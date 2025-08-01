import os
from pathlib import Path
from typing import List
import requests
from urllib.parse import urlparse
import time
from tqdm import tqdm

from downloader.scraper_tools.save_my_exams import SaveMyExamsScraper
from lib.grade import Grade
from lib.subject import EceswaSubject, PapaCambridgeIgcseSubject, Subject
from lib.utils import LibUtils

from .utils import download_file, get_urls_for_nonexistent_files
from ..scraper_tools.criterion import PaperCount
from ..scraper_tools.eceswa import EceswaScraper

from ..scraper_tools.papacambridge import PapaCambridgeScraper

from concurrent.futures import ThreadPoolExecutor, as_completed

class PastPaperDownloader:
    """
    This class encapsulates the logic to download past papers from
    different exam councils and saving them to disk.
    """

    def __init__(self):
        self._eceswa_scraper = EceswaScraper()
        self._papa_cambridge_scraper = PapaCambridgeScraper()
        self._save_my_exams_scraper = SaveMyExamsScraper()

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        })

    def download(
        self,
        grade: Grade,
        subject: Subject,
        paper_count: PaperCount,
        download_path: str
    ) -> None:
        """
        Downloads PDF past papers for a specified grade and subject, and saves them
        to the provided download path. 

        The method performs the following:
        - Fetches download URLs for the subject and grade.
        - Skips files that already exist.
        - Downloads missing files concurrently using a thread pool.
        - Displays a progress bar using `tqdm`.
        - Adds a small delay between downloads to reduce server strain.

        Args:
            grade (Grade): The academic grade
            subject (Subject): The subject to download past papers for.
            paper_count (PaperCount): The number of papers to download, used to limit scraping.
            download_path (str): The root directory where the downloaded files will be saved.

        Returns:
            None: This method performs downloads and saves files but returns nothing.
    """
        if isinstance(subject, EceswaSubject):
            urls = self._eceswa_scraper.get_pdf_download_urls(grade, subject, paper_count)
        elif isinstance(subject, PapaCambridgeIgcseSubject):
            urls = self._papa_cambridge_scraper.get_pdf_download_urls(grade, subject, paper_count)
        else:
            urls = self._save_my_exams_scraper.get_pdf_download_urls(grade, subject, paper_count)
      
        download_tasks = []

        for relative_path, pdf_urls in urls.items():
            save_folder = os.path.join(download_path, relative_path)
            
            try:
                os.makedirs(save_folder, exist_ok=True)
            except OSError as e:
                print(f"Error creating download folder {save_folder}: {e}")
                return

            for pdf_url in pdf_urls:
                filename = os.path.basename(urlparse(pdf_url).path)
                full_save_path = os.path.join(save_folder, filename)
           
                if not os.path.exists(full_save_path):
                    download_tasks.append((pdf_url, full_save_path))
    
        if not download_tasks:
            return
    
        # Wrap the download function to include tqdm and sleep
        def task_wrapper(url: str, path: str) -> tuple[str, bool]:
            success = download_file(self.session, url, path)
            time.sleep(0.5)
            return (os.path.basename(path), success)

        # Use tqdm to track progress
        with ThreadPoolExecutor(max_workers=6) as executor, tqdm(total=len(download_tasks), desc=f"Downloading {grade.value} - {subject.value} papers", unit="file") as progress:
            future_to_task = {
                executor.submit(task_wrapper, url, path): (url, path)
                for url, path in download_tasks
            }

            for future in as_completed(future_to_task):
                filename, success = future.result()
                path = future_to_task[future][1]

                progress.update(1)