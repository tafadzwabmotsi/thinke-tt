from collections import defaultdict
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Any, Literal, Optional
from enum import Enum

from downloader.scraper_tools.criterion import PaperCount
from lib.grade import EceswaGrade
from lib.subject import EceswaSubject
from lib.typing.data.downloader import DownloadLinks


class EceswaScraper:
    """
    This class encapsulates the logic to scrap `https://www.examscouncil.org.sz/`
    with the goal of compiling all the downloadable links of the past papers from
    Eswatini Council required by the user.

    Given the `grade`(e.g `EGCSE`), subject title, and years; it returns a list of absolute
    urls that point to all the found question papers.
    """

    BASE_URL = "https://www.examscouncil.org.sz/"
    PROGRAMMES_PAGE_URL = urljoin(BASE_URL, "index.php")

    def __init__(self):
        """
        Initializes the EceswaScraper with a requests session
        and sets default headers to mimic a web browser.
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        })

    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Helper method to fetch the content of a given URL and parse it with BeautifulSoup.

        Args:
            url: The URL to fetch.

        Returns:
            A BeautifulSoup object if the request is successful, otherwise None.
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _get_absolute_url(self, relative_path: str) -> str:
        """Constructs an absolute URL from a relative path using the BASE_URL."""
        return urljoin(self.BASE_URL, relative_path)

    def _get_subject_urls(self, grade: EceswaGrade) -> Dict[str, str]:
        """
        Retrieves a dictionary of subject names and their corresponding absolute URLs
        for a given grade.

        This method navigates to the main page, parses the HTML, finds the section
        corresponding to the specified grade by checking its header, and extracts
        all subject links within it.

        Args:
            grade (Grade): The enum representing the desired grade (e.g., Grade.EGCSE).

        Returns:
            Dict[str, str]: A dictionary where keys are subject names (e.g., "Mathematics (6880)")
                            and values are their absolute URLs. Returns an empty dictionary
                            if the grade or its subjects are not found.
        """
        soup = self._get_soup(self.PROGRAMMES_PAGE_URL)
        if not soup:
            print(f"Could not fetch the programmes page from {self.PROGRAMMES_PAGE_URL}. Cannot get subject URLs.")
            return {}

        subject_links: Dict[str, str] = {}
        target_grade_value = grade.value
      

        programmes_container = soup.find('div', class_='container-fluid pl-5 pr-5')
        if not programmes_container:
            print("Programmes container (div.container-fluid.pl-5.pr-5) not found on the page.")
            return {}

        grade_columns = programmes_container.find_all('div', class_='col-sm-3')

        for col in grade_columns:
            # Find the strong tag which contains the full grade name 
            # (e.g., "Eswatini General Certificate of Secondary Education (EGCSE)")
            grade_title_strong_tag = col.find('h6', class_='border')
            if grade_title_strong_tag:
                grade_title_strong_tag = grade_title_strong_tag.find('strong')

            if grade_title_strong_tag:
                html_grade_name = grade_title_strong_tag.get_text(strip=True)

                # Check if the desired grade's enum value is part of the HTML grade name
                # This makes it flexible for full names like "Eswatini General Certificate
                # of Secondary Education (EGCSE)"
                if target_grade_value in html_grade_name:
                    # Found the correct grade column, now extract its subjects
                    subject_anchor_tags = col.find_all('a', class_='dropdown-item')
                    for anchor in subject_anchor_tags:
                        subject_name = anchor.get_text(strip=True)
                        relative_url = anchor.get('href')

                        if subject_name and relative_url:
                            absolute_url = self._get_absolute_url(relative_url)
                            subject_links[subject_name] = absolute_url
                    break # Stop searching after finding and processing the desired grade

        return subject_links
    
    def _extract_pdf_links_grouped_by_year(
        self,
        grade: EceswaGrade,
        subject: EceswaSubject,
        limit: Optional[int] = None,
        group_by: Literal["path", "csv"] = "path"
    ) -> Dict[str, List[str]]:
        """
        Core logic that navigates to the subject page and extracts PDF links.

        Args:
            grade (EceswaGrade): Grade level (e.g., JC, EGCSE).
            subject (EceswaSubject): Subject to look for (e.g., ENGLISH).
            limit (Optional[int]): Max number of papers to include. If None, includes all.
            group_by (str): "path" for backslash paths, "csv" for comma-separated keys.

        Returns:
            Dict[str, List[str]]: Keys are either path-style or csv-style, values are lists of URLs.
        """
        grade_subject_urls = self._get_subject_urls(grade)
        if not grade_subject_urls:
            print(f"No subjects found for grade {grade.value}.")
            return {}

        # Find matching subject URL
        target_subject_url = next(
            (url for name, url in grade_subject_urls.items()
            if subject.value.lower() in name.lower()), None
        )
        if not target_subject_url:
            print(f"Subject '{subject.value}' not found for grade '{grade.value}'.")
            return {}

        subject_soup = self._get_soup(target_subject_url)
        if not subject_soup:
            print(f"Failed to fetch subject page: {target_subject_url}")
            return {}

        past_papers_section = subject_soup.find('section', id='tab3', class_='tab-content')
        if not past_papers_section:
            print(f"Past papers section not found on: {target_subject_url}")
            return {}

        anchors = past_papers_section.find_all(
            'a',
            href=lambda h: h and (h.lower().endswith('.pdf')) # or h.lower().endswith('.mp3'))
        )

        year_pattern = re.compile(r'(20(?:[0-2]\d|30))')
        links_by_group: Dict[str, List[str]] = defaultdict(list)
        added = 0
        current_year = None

        for anchor in anchors:
            href = anchor.get('href')
            absolute_url = self._get_absolute_url(href)
            match = year_pattern.search(absolute_url)

            if not match:
                continue

            year = match.group(1)
            if group_by == "path":
                key = f"{grade.value}\\{subject.value}\\{year}"
            else:
                key = f"{grade.value},{subject.value},{year}"

            if limit is not None and added >= limit and current_year != year:
                break

            if current_year != year:
                current_year = year

            links_by_group[key].append(absolute_url)
            added += 1

        return dict(links_by_group)

    def get_pdf_download_urls(
        self,
        grade: EceswaGrade,
        subject: EceswaSubject,
        paper_count: PaperCount
    ) -> DownloadLinks:
        """
        Returns download links grouped by year in path format.
        """
        return self._extract_pdf_links_grouped_by_year(
            grade=grade,
            subject=subject,
            limit=paper_count.value,
            group_by="path"
        )
        
    def get_pdf_save_urls(self, grade: EceswaGrade, subject: EceswaSubject) -> Dict[str, List[str]]:
        """
        Returns all downloadable links grouped by CSV-compatible keys (grade,subject,year).
        No paper limit is enforced.
        """
        return self._extract_pdf_links_grouped_by_year(
            grade=grade,
            subject=subject,
            limit=None,
            group_by="csv"
        )


