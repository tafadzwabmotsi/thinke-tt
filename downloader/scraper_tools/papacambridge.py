import os
import re
from collections import defaultdict
from typing import List, Dict, Literal, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from downloader.scraper_tools.criterion import FilteringCriterion, PaperCount
from downloader.scraper_tools.types import SessionEntry, Year
from downloader.scraper_tools.utils import ScraperToolsUtils
from lib.grade import EceswaGrade
from lib.session import Session
from lib.subject import PapaCambridgeIgcseSubject
from lib.typing.data.downloader import DownloadLinks

# Define types common to this class
SubjectUrls = Dict[str, str]

# Regular expressions common to this class
month_pattern = (
            r'(?:January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|'
            r'July|Jul|August|Aug|September|Sep|October|Oct|November|Nov|December|Dec)'
)

def get_subject_code(instance: str) -> Optional[str]:
    """
    Extracts the 4-digit code and optional region suffix from a string.

    Examples:
        "Mathematics - 0444 - US" → "0444_US"
        "German-7159-UK" → "7159_UK"
        "Mathematics - 0580" → "0580"

    Args:
        instance (str): Input string containing the subject name and code.

    Returns:
        Optional[str]: Extracted code with optional suffix (joined by underscore), or `None` if not found.
    """
    match = re.search(r'(\d{4})(?:\s*-\s*([A-Za-z]+))?', instance)
    if match:
        code = match.group(1)
        suffix = match.group(2)
        return f"{code}_{suffix.upper()}" if suffix else code
    return None

class PapaCambridgeScraper:
    BASE_URL = "https://pastpapers.papacambridge.com/"

    def __init__(self):
        """
        Initializes a new instance of the PapaCambridgeScraper.

        Sets up an HTTP session with appropriate headers to mimic a browser and initializes
        internal caches to improve scraping performance by avoiding redundant network requests.
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        })
        self._soup_cache: Dict[str, Optional[BeautifulSoup]] = {}
        self._grade_url_cache: Dict[str, Optional[str]] = {}
        self._subject_urls_cache: Dict[str, Dict[str, str]] = {}
        self._year_session_urls_cache: Dict[str, List[SessionEntry]] = {}

        self._year_session_regex = re.compile(
            rf'^\d{{4}}(?:[\s\-]+{month_pattern}){{1,2}}$',
            re.IGNORECASE
        )

    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetches and parses the HTML content of a URL into a BeautifulSoup object, with caching.

        If the HTML content for the specified URL has already been fetched previously,
        the cached version is returned. Otherwise, the URL is requested, parsed using BeautifulSoup,
        and stored in the cache for future access.

        Args:
            url (str): The web address to fetch and parse.

        Returns:
            Optional[BeautifulSoup]: A BeautifulSoup object representing the parsed HTML content
                                     if the request is successful; otherwise, None.
        """
        if url in self._soup_cache:
            return self._soup_cache[url]

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            self._soup_cache[url] = soup
            return soup
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            self._soup_cache[url] = None
            return None

    def _get_grade_url(self, grade: EceswaGrade) -> Optional[str]:
        """
        Retrieves and caches the URL corresponding to the given academic grade (e.g., IGCSE, A Level).

        This method scrapes the main navigation menu of the PapaCambridge homepage to locate
        the specific link that leads to the page for the given grade. The result is cached
        to avoid redundant network calls on subsequent invocations.

        Args:
            grade (Grade): The academic grade enum representing levels such as IGCSE,
                           O Level, AS & A Level, etc.

        Returns:
            Optional[str]: The absolute URL of the grade page if found; otherwise, None.
        """
        grade_key = grade.value.lower()
        if grade_key in self._grade_url_cache:
            return self._grade_url_cache[grade_key]

        soup = self._get_soup(self.BASE_URL)
        if not soup:
            return None

        grade_menu_ul = soup.find('ul', class_='kt-right-submenu__nav')
        if not grade_menu_ul:
            return None

        for li in grade_menu_ul.find_all('li', class_='kt-menu__item'):
            a_tag = li.find('a', class_='kt-menu__link')
            if a_tag and 'href' in a_tag.attrs:
                span_text = a_tag.find('span', class_='kt-menu__link-text')
                if span_text:
                    link_text = span_text.get_text().strip().lower()
                    if grade_key == link_text or grade_key in link_text:
                        full_url = urljoin(self.BASE_URL, a_tag['href'])
                        self._grade_url_cache[grade_key] = full_url
                        return full_url

        self._grade_url_cache[grade_key] = None
        return None

    def _filter_subject_urls(self, subject_urls: SubjectUrls, criterion: FilteringCriterion) -> SubjectUrls:
        """
        Filters subject URLs by identifying which URLs contain enough recent session folders to meet the criterion.

        Args:
            subject_urls (SubjectUrls): The subject URLs to filter.
            criterion (FilteringCriterion): The criterion to filter subjects by.

        Returns:
            SubjectUrls: The filtered subject URLs.
        """
        min_required_sessions = criterion.value

        month_order = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
            'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
        }

        def session_sort_key(session_str: str) -> tuple:
            parts = session_str.replace('-', ' ').split()
            try:
                year = int(parts[0])
                month = ScraperToolsUtils.get_full_month_name(parts[-1])
                return year, month_order.get(month, 0)
            except (ValueError, TypeError):
                return 0, 0

        def analyze_subject(subject_label: str, url: str) -> Optional[tuple]:
            soup = self._get_soup(url)
            if not soup:
                return None

            main_div = soup.find('div', class_='files-list-main')
            if not main_div:
                return None

            valid_sessions = [
                span.get_text(strip=True)
                for span in main_div.find_all('span', class_='wraptext')
                if self._year_session_regex.match(span.get_text(strip=True))
            ]

            if not valid_sessions:
                return None

            latest = max(valid_sessions, key=session_sort_key)
            return subject_label, url, latest, len(valid_sessions)

        selected: SubjectUrls = {}
        accumulated = 0
        results = []

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(analyze_subject, lbl, url): lbl for lbl, url in subject_urls.items()}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        results.sort(key=lambda x: session_sort_key(x[2]), reverse=True)

        for label, url, _, count in results:
            selected[label] = url
            accumulated += count
            if accumulated >= min_required_sessions:
                break

        return selected

    def _get_subject_urls(
            self,
            grade: EceswaGrade,
            subject: PapaCambridgeIgcseSubject,
            criterion: FilteringCriterion
    ) -> SubjectUrls:
        """
        Retrieves and caches the URLs of all subject folders matching a given subject for a specific grade.

        This method parses the page corresponding to the given grade, searches for folder links
        whose labels loosely match the provided subject name, and returns a dictionary mapping
        the full folder labels (e.g., "Mathematics - 0580") to their corresponding URLs.

        Args:
            grade (Grade): The academic grade (e.g., Grade.IGCSE, Grade.ALEVEL).
            subject (PapaCambridgeIgcseSubject): The subject to match against folder labels
                (e.g., IgcseSubject.MATHEMATICS, IgcseSubject.PHYSICS).
            criterion (FilteringCriterion): The subject selection criterion.

        Returns:
            SubjectUrls: A mapping from full folder label (subject name with code) to the folder URL.
                            If no folders are found or scraping fails, returns an empty dictionary.
        """
        key = f"{grade.value}|{subject.value}".lower()
        if key in self._subject_urls_cache:
            return self._subject_urls_cache[key]

        subject_value_lower = subject.value.lower().strip()
        grade_url = self._get_grade_url(grade)

        if not grade_url:
            return {}

        soup = self._get_soup(grade_url)
        if not soup:
            return {}

        found_subject_urls: Dict[str, str] = {}
        files_list_main_div = soup.find('div', class_='files-list-main')
        if not files_list_main_div:
            return {}

        subject_folder_items = files_list_main_div.find_all('div', class_='kt-widget4__item item-folder-type')
        for item_div in subject_folder_items:
            a_tag = item_div.find('a', class_='kt-widget4__title')
            if a_tag and 'href' in a_tag.attrs:
                span_text_tag = a_tag.find('span', class_='wraptext')
                if span_text_tag:
                    link_subject_full = span_text_tag.get_text().strip()
                    link_subject_lower = link_subject_full.lower()
                    if subject_value_lower in link_subject_lower:
                        full_url = urljoin(self.BASE_URL, a_tag['href'])

                        found_subject_urls[link_subject_full] = full_url

        self._subject_urls_cache[key] = found_subject_urls

        return self._filter_subject_urls(subject_urls=found_subject_urls, criterion=criterion)

    def _get_session_entries(
            self,
            grade: EceswaGrade,
            subject: PapaCambridgeIgcseSubject,
            criterion: FilteringCriterion
    ) -> List[SessionEntry]:
        """
        Retrieves a flat list of session entries for a given grade and subject using
        the filtering criterion to limit redundant scraping.

        Args:
            grade (Grade): The educational grade (e.g., Grade.IGCSE).
            subject (PapaCambridgeIgcseSubject): The subject of interest (e.g., IgcseSubject.MATHEMATICS).
            criterion (FilteringCriterion): The filter determining how many latest sessions to consider.

        Returns:
            List[SessionEntry]: A flat list of session entries, one for each matched year/session folder.
        """
        cache_key = f"{grade.value}|{subject.value}".lower()
        if cache_key in self._year_session_urls_cache:
            return self._year_session_urls_cache[cache_key]

        subject_urls = self._get_subject_urls(grade, subject, criterion)
        if not subject_urls:
            return []

        subject_name = subject.value
        entries: List[SessionEntry] = []

        def extract_entries(subject_label: str, subject_url: str) -> List[SessionEntry]:
            subject_code = get_subject_code(subject_label)
            if not subject_code:
                return []

            soup = self._get_soup(subject_url)
            if not soup:
                return []

            main_div = soup.find('div', class_='files-list-main')
            if not main_div:
                return []

            session_entries: List[SessionEntry] = []
            for item_div in main_div.find_all('div', class_='kt-widget4__item item-folder-type'):
                a_tag = item_div.find('a', class_='kt-widget4__title')
                if not (a_tag and 'href' in a_tag.attrs):
                    continue

                span = a_tag.find('span', class_='wraptext')
                if not span:
                    continue

                folder_name = span.get_text(strip=True)
                if not self._year_session_regex.match(folder_name):
                    continue

                parts = folder_name.replace('-', ' ').split()
                if len(parts) < 2:
                    continue

                year_str, month_str = parts[0], parts[-1]
                session_name = ScraperToolsUtils.get_full_month_name(month_str)
                if not session_name:
                    continue

                session_entries.append(SessionEntry(
                    subject=subject_name,
                    code=subject_code,
                    year=year_str,
                    session=session_name,
                    url=urljoin(self.BASE_URL, a_tag['href'])
                ))

            return session_entries

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(extract_entries, label, url) for label, url in subject_urls.items()]
            for future in as_completed(futures):
                entries.extend(future.result())

        self._year_session_urls_cache[cache_key] = entries
        return entries

    def _extract_pdf_links_from_sessions(
        self,
        grade: EceswaGrade,
        subject: PapaCambridgeIgcseSubject,
        limit: Optional[int] = None,
        group_by: Literal["path", "csv"] = "path"
    ) -> Dict[str, List[str]]:
        """
        Shared logic to extract PDF links from session entries.

        Args:
            grade (EceswaGrade): Grade level (e.g., IGCSE).
            subject (PapaCambridgeIgcseSubject): Subject name.
            limit (Optional[int]): Max number of papers to retrieve. If None, get all.
            group_by (str): "path" for backslash paths, "csv" for comma-separated keys.

        Returns:
            Dict[str, List[str]]: Keys are group labels, values are lists of URLs.
        """
        # Always use FilteringCriterion.LATEST_16 for all-inclusive scraping
        criterion = FilteringCriterion.LATEST_16

        session_entries = self._get_session_entries(
            grade=grade,
            subject=subject,
            criterion=criterion
        )

        links_by_group = defaultdict(list)
        added = 0

        for subj, code, year, session, url in session_entries:
            group_key = (
                f"{grade.value}\\{subj}\\{year}\\{session}" if group_by == "path"
                else f"{grade.value},{subj},{year},{session}"
            )

            soup = self._get_soup(url)
            if not soup:
                continue

            files_div = soup.find('div', class_='files-list-main')
            if not files_div:
                continue

            for item in files_div.find_all('div', class_='kt-widget4__item'):
                anchor = item.find(
                    'a', class_='badge badge-info',
                    attrs={'download': ''},
                    href=lambda h: h and "download_file.php?files=" in h
                )
                if anchor and 'href' in anchor.attrs:
                    parsed = urlparse(anchor['href'])
                    query = parse_qs(parsed.query)
                    files_param = query.get('files', [])
                    if not files_param:
                        continue

                    direct_url = files_param[0]
                    filename = os.path.basename(urlparse(direct_url).path).lower()

                    # Only accept relevant paper types
                    if any(marker in filename for marker in ['_qp_', '_in_', '_sf_']):
                        links_by_group[group_key].append(direct_url)
                        added += 1
                        if limit and added >= limit:
                            return dict(links_by_group)

        return dict(links_by_group)
    
    def get_pdf_download_urls(
        self,
        grade: EceswaGrade,
        subject: PapaCambridgeIgcseSubject,
        paper_count: PaperCount
    ) -> DownloadLinks:
        return self._extract_pdf_links_from_sessions(
            grade=grade,
            subject=subject,
            limit=paper_count.value,
            group_by="path"
        )

    def get_pdf_save_urls(
        self,
        grade: EceswaGrade,
        subject: PapaCambridgeIgcseSubject
    ) -> Dict[str, List[str]]:
        return self._extract_pdf_links_from_sessions(
            grade=grade,
            subject=subject,
            limit=None, 
            group_by="csv"
        )
