from collections import defaultdict
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from typing import List, Literal, Optional, Dict, Tuple, Union

# Assuming lib.grade and lib.subject are available in your environment
from downloader.scraper_tools.criterion import PaperCount
from downloader.scraper_tools.utils import ScraperToolsUtils
from lib.grade import CambridgeGrade
from lib.subject import SaveMyExamsSubject, SaveMyExamsSubjectDefinition, SaveMyExamsSubjectDefinition
from lib.typing.data.downloader import DownloadLinks
    

class SaveMyExamsScraper:
    """
    This class encapsulates the logic to scrap `www.savemyexams.com`
    with the goal of compiling all the downloadable links of the past papers
    required by the user.

    Given the grade, subject title, and years; it returns a list of absolute
    urls that point to all the found question papers.
    """

    BASE_URL = 'https://www.savemyexams.com'
    DOWNLOAD_BASE_URL = 'https://pastpapers.co'

    def __init__(self):
        """
        Initializes the SaveMyExams scraper with a requests session
        and sets default headers to mimic a web browser.
        """
        self.session = requests.Session()

        # Set a User-Agent header to make requests appear from a common browser.
        # This helps avoid some basic bot detection.
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': self.BASE_URL,
            'DNT': '1',  # Do Not Track
            'Upgrade-Insecure-Requests': '1',
        })
 
        # Cache for soup objects (for _get_soup calls)
        self._soup_cache: Dict[str, BeautifulSoup] = {}
        
        # Cache for specific subject past papers URLs after they are resolved (grade, subject) -> URL
        self._past_papers_url_cache: Dict[tuple[CambridgeGrade, SaveMyExamsSubject], Optional[str]] = {}


    def _get_soup(self, url: str, use_cache: bool = True) -> Optional[BeautifulSoup]:
        """
        Helper method to fetch the content of a given URL and parse it with BeautifulSoup.

        Args:
            url: The URL to fetch.
            use_cache: If True, tries to retrieve from cache or store in cache.

        Returns:
            A BeautifulSoup object if the request is successful, otherwise None.
        """
        if use_cache and url in self._soup_cache:
            return self._soup_cache[url]

        try:
            response = self.session.get(url, timeout=15)  # Set a timeout for the request
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            soup = BeautifulSoup(response.text, 'html5lib')
            if use_cache:
                self._soup_cache[url] = soup
            return soup

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
        
    def _get_subject_past_papers_url(
        self, 
        grade: CambridgeGrade, 
        subject: SaveMyExamsSubject
    ) -> Optional[str]:
            """
            Navigates to the grade's main page (e.g., /igcse/), finds the specific subject's
            section, and then extracts the absolute URL to its "Past Papers" resource.
            Caches the found URL for efficiency.

            Args:
                grade (SaveMyExamsGrade): The grade level (e.g., IGCSE, A_LEVEL).
                subject (SaveMyExamsSubject): The subject enum whose past papers URL is to be found.

            Returns:
                Optional[str]: The absolute URL to the subject's past papers page for the given grade,
                            or None if the subject or its past papers link cannot be found.
            """
            # Check cache first
            cache_key = (grade, subject)
            if cache_key in self._past_papers_url_cache:
                return self._past_papers_url_cache[cache_key]
            
            
            
            grade_page_url = urljoin(self.BASE_URL, f'/{grade.value.lower()}/')
          
            
            soup = self._get_soup(grade_page_url)
            if not soup:
                print(f"Failed to retrieve the grade page from {grade_page_url}.")
                return None
            
            # Find the main container div that holds all subject sections
            main_container = soup.find('main', class_='py-5')
            if not main_container:
                print(f"Could not find the main subjects container on the {grade.value} page.")
                return None

            # Iterate through each subject block
            # The structure is: div.Wrapper_wrapper__GnBU0.border.rounded.mb-3 -> h3.Subjects_subject__t5OCh
            subject_blocks = main_container.find_all('div', class_='Wrapper_wrapper__GnBU0 border rounded mb-3')

            for block in subject_blocks:
                subject_heading = block.find('h3', class_='Subjects_subject__t5OCh')
                if subject_heading and subject_heading.get_text(strip=True) == subject.value.site_name:
                    # Found the correct subject block. Now look for the "Past Papers" link within it.
                    
                    # The structure for resource links is:
                    # div.Wrapper_wrapper__GnBU0.Subjects_links___N7A9 (or similar parent)
                    # -> a.ResourceLink_link__DBka0
                    #    -> span.ResourceLink_text__36e8q (with text "Past Papers")
                  
                    # Refined search: find the <a> tag whose child span has the text "Past Papers"
                    found_link = None
                    for a_tag in block.find_all('a', class_='ResourceLink_link__DBka0'):
                        span_text_element = a_tag.find('span', class_='ResourceLink_text__36e8q')
                        href = a_tag.get('href')
                        if span_text_element and "Past Papers".lower() in span_text_element.get_text(strip=True).lower() and href:
                            # Add an additional check to ensure href contains grade.value for robustness
                            if grade.value.lower() in href.lower():
                                found_link = a_tag
                                break
                    
                    if found_link:
                        href = found_link.get('href')
                        past_papers_url = urljoin(self.BASE_URL, href)
                        self._past_papers_url_cache[cache_key] = past_papers_url
                        return past_papers_url
                    else:
                        print(f"Past Papers link for '{subject.value.site_name}' not found within its block for {grade.value}.")
                        self._past_papers_url_cache[cache_key] = None
                        return None
            
            print(f"Subject '{subject.value.site_name}' not found under grade '{grade.value}' on {grade_page_url}.")
            self._past_papers_url_cache[cache_key] = None # Cache None to avoid re-attempting
            return None
    
    def _extract_pdf_links_from_table(
        self,
        grade: CambridgeGrade,
        subject: SaveMyExamsSubject,
        limit: Optional[int] = None,
        group_by: Literal["path", "csv"] = "path"
    ) -> Dict[str, List[str]]:
        """
        Internal method to scrape and extract PDF URLs from SaveMyExams past paper table.

        Args:
            grade: Grade enum (e.g., SaveMyExamsGrade.IGCSE).
            subject: Subject enum.
            limit: Max number of papers to fetch. None means unlimited.
            group_by: "path" = use backslash paths as keys, "csv" = comma-separated keys.

        Returns:
            Dictionary of paper URLs grouped by session.
        """
        past_papers_page_url = self._get_subject_past_papers_url(grade, subject)
        if not past_papers_page_url:
            print(f"Could not find past papers URL for {grade.value} {subject.value.site_name}.")
            return {}

        soup = self._get_soup(past_papers_page_url)
        if not soup:
            print(f"Failed to retrieve past papers page from {past_papers_page_url}.")
            return {}

        table = soup.find('table', class_='PastPapersTable_table__NXbSW')
        if not table:
            print(f"Could not find the past papers table on {past_papers_page_url}.")
            return {}

        tbody = table.find('tbody')
        if not tbody:
            print(f"Could not find tbody within the past papers table.")
            return {}

        rows = tbody.find_all("tr")
        session_dict = {}
        year_regex = ScraperToolsUtils.get_year_regex()
        month_regex = ScraperToolsUtils.get_month_regex()

        for row in rows:
            # Extract session year and month
            session_year = None
            session_month = None
            a_tags = row.find_all("a", attrs={"data-type": "Past Paper"})

            for a in a_tags:
                text = a.get_text(strip=True)
                year_match = year_regex.search(text)
                month_match = month_regex.search(text)
                if year_match and month_match:
                    session_year = int(year_match.group())
                    session_month = month_match.group().capitalize()
                    break

            if not (session_year and session_month):
                continue

            # Collect all PDF links
            urls = []
            for a in a_tags:
                href = a.get("href", "")
                if not href.endswith(".pdf"):
                    continue
                if not any(key in href.lower() for key in ["_qp_", "_in_"]):
                    continue

                if "view.php" in href:
                    resolved = ScraperToolsUtils.resolve_redirected_pdf_url(
                        view_php_url=href,
                        base_url=self.DOWNLOAD_BASE_URL
                    )
                    if resolved:
                        urls.append(resolved)
                else:
                    urls.append(href)

            if not urls:
                continue

            key = (session_year, session_month)
            if key not in session_dict:
                session_dict[key] = []
            session_dict[key].extend(urls)

        # Sort sessions by recency
        sorted_sessions = sorted(
            session_dict.items(),
            key=lambda item: (item[0][0], ScraperToolsUtils.get_month_num(item[0][1])),
            reverse=True
        )

        result = {}
        total = 0

        for (year, month), urls in sorted_sessions:
            group_key = (
                f"{grade.value}\\{subject.value.local_name}\\{year}\\{month}"
                if group_by == "path"
                else f"{grade.value},{subject.value.local_name},{year},{month}"
            )

            result[group_key] = urls
            total += len(urls)

            if limit is not None and total >= limit:
                break

        return result

    
    def get_pdf_download_urls(
        self,
        grade: CambridgeGrade,
        subject: SaveMyExamsSubject,
        paper_count: PaperCount
    ) -> DownloadLinks:
        return self._extract_pdf_links_from_table(
            grade=grade,
            subject=subject,
            limit=paper_count.value,
            group_by="path"
        )

    def get_pdf_save_urls(
        self,
        grade: CambridgeGrade,
        subject: SaveMyExamsSubject
    ) -> DownloadLinks:
        return self._extract_pdf_links_from_table(
            grade=grade,
            subject=subject,
            limit=None,      
            group_by="csv"   
        )
