import calendar
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path, PurePosixPath
import re
import requests        
        
from contextlib import contextmanager
import os
import shutil
from typing import Any, Generator, Iterable, Literal
from halo import Halo
from tqdm import tqdm

class LibUtils:
    """
    A class that defines static library utility methods
    """
    @staticmethod
    def extract_paper_label(url: str) -> str:
        filename = PurePosixPath(url).name
        
        # Cambridge scenario
        match_cambridge_paper = re.search(r'_qp_(\d{2})\.pdf', filename)
        match_cambridge_insert = re.search(r'_in_(\d{2})\.pdf', filename)
        if match_cambridge_paper:
            return f"Paper {int(match_cambridge_paper.group(1)[0])}"
        
        if match_cambridge_insert:
            return f"Paper {int(match_cambridge_insert.group(1)[0])} - Insert"
 
        # Eceswa scenario
        match_eceswa_paper = re.search(r'Paper\s*(\d+)', url, re.IGNORECASE)
        if match_eceswa_paper:
            return f"Paper {int(match_eceswa_paper.group(1))}"
        
        return "Paper No: Undefined"
    
    @staticmethod
    def copy_file(src: Path, dst: Path):
        """
        Copy a file from src to dst if it doesn't already exist.
        """
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"Error copying file {src} to {dst}: {e}")
    
    @staticmethod            
    def format_date_with_weekday(date_str: str) -> str:
            """Format 'DD-MM-YY' to 'DD-MM-YY (Weekday)'"""
            date_obj = datetime.strptime(date_str, "%d-%m-%y")
            return date_obj.strftime("%d-%m-%y (%a)")
    
    @staticmethod
    def get_human_readable_date(date_str: str) -> str:
        """
        Converts a date string from 'dd-mm-yy' format to a more human-readable form like '22 July 2025'.

        Args:
            date_str (str): The date string in 'dd-mm-yy' format.

        Returns:
            str: A human-readable version of the date, e.g. '22 July 2025'.
        """
        try:
            dt = datetime.strptime(date_str, "%d-%m-%y")
            return dt.strftime("%d %B %Y")
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Expected 'dd-mm-yy'.")

    @staticmethod
    def get_machine_readable_date(date_str: str) -> str:
        """
        Converts a human-readable date string like '22 July 2025' into 'dd-mm-yy' format.

        Args:
            date_str (str): The date string in 'dd Month yyyy' format.

        Returns:
            str: A machine-readable date string in 'dd-mm-yy' format.
        """
        try:
            dt = datetime.strptime(date_str, "%d %B %Y")
            return dt.strftime("%d-%m-%y")
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Expected 'dd Month yyyy'.")
    
    @staticmethod
    @contextmanager
    def spinner(
        start_text: str, 
        success_text: str = None, 
        fail_text: str = None, 
        frames_type: Literal["loading", "sending"] = "loading"
    ):
        """
        A context manager that wraps a block with a Halo spinner.
        
        Args:
            start_text (str): Spinner text shown during processing.
            success_text (str, optional): Message shown on success.
            fail_text (str, optional): Message shown on failure.
        """
        spinner = Halo(
            text=start_text,
            color="yellow",
            text_color="yellow",
            spinner={
                'interval': 100,
                'frames': [
                    r'[\]', r'[_]', r'[/]'
                ] if frames_type == "loading" else [
                    r'[=>]', r'[==>]', r'[===>]' 
                ]
             }
        )

        try:
            spinner.start()
            yield
            spinner.color = "green"
            spinner.text_color = "green"
            spinner.succeed(success_text or f"{start_text} - done")
        except Exception as e:
            spinner.color = "red"
            spinner.text_color = "red"
            spinner.fail(fail_text or f"{start_text} - failed")
            raise  # re-raise so upstream can catch
        finally:
            spinner.stop()
            
    @staticmethod
    @contextmanager
    def progress_bar(
        tasks: Iterable[Any], 
        desc_text: str = "", 
        unit: Literal["task", "file"] = "task"
    ) -> Generator[Iterable[Any], None, None]:
        """
        Context manager that runs tasks in parallel and yields completed items
        while automatically updating a tqdm progress bar.

        Args:
            tasks: Iterable of items to process.
            desc_text: Description text for the progress bar.
            unit: Unit name shown in the tqdm bar.
        """
        
        tasks = list(tasks) 

        with tqdm(total=len(tasks), desc=desc_text, unit=unit) as bar:
            with ThreadPoolExecutor(max_workers=6) as executor:
                # Submit each task to the executor but don't process it yet
                futures = {executor.submit(lambda x: x, t): t for t in tasks}

                def completed_task_generator():
                    for future in as_completed(futures):
                        bar.update(1)
                        yield futures[future] 

                yield completed_task_generator()
      
    @staticmethod
    def get_todays_date() -> str:
        """
        Returns today's date formatted as a string in the format 'DD-MM-YY'.

        Returns:
            str: Today's date, e.g. '30-07-25'.
        """
        return date.today().strftime("%d-%m-%y")

    @staticmethod
    def get_next_months_date() -> str:
        """
        Returns the date 30 days from today, formatted as 'DD-MM-YY'.

        This function internally uses `get_todays_date()` to get today's date
        and adds 30 days to compute the next month's date.

        Returns:
            str: A date string 30 days from today, in the format 'DD-MM-YY'.
        """
        start_date = LibUtils.get_todays_date()
        return (datetime.strptime(start_date, "%d-%m-%y") + timedelta(days=30)).strftime("%d-%m-%y")
    
    def get_date_parts(date_str: str) -> tuple[str, str]:
        # Parse string "dd-mm-yy" into datetime object
        dt = datetime.strptime(date_str, "%d-%m-%y")
        return str(dt.year), calendar.month_name[dt.month]

    @staticmethod
    def clean_folder_name(name: str) -> str:
        """
        Cleans a string to be suitable for a filesystem folder name.
        Replaces invalid characters and normalizes spaces/hyphens to underscores.
        """
        # Replace characters not allowed in Windows filenames (and /) with an underscore.
        # Note: \ is a path separator and will be handled by os.path.join later,
        # so we primarily clean characters that are invalid *within* a segment.
        # For simplicity, we are cleaning a broad set here.
        cleaned_name = re.sub(r'[<>:"|?*]', '_', name)
        cleaned_name = re.sub(r'[/\\-]', '_', cleaned_name) # Explicitly replace path separators and hyphens

        # Replace multiple spaces with a single underscore, and strip leading/trailing underscores
        cleaned_name = re.sub(r'\s+', '_', cleaned_name).strip('_')
        
        return cleaned_name

    @staticmethod
    def download_file(session: requests.Session, url: str, save_path: str) -> bool:
        """
        Downloads a single PDF file from the given URL and saves it to the specified path.

        Args:
            session: The requests.Session object to use for downloading.
            url: The absolute URL of the PDF file to download.
            save_path: The full local path (including filename) where the PDF should be saved.

        Returns:
            True if the download was successful, False otherwise.
        """

        # Do not re-download files that already exist
        if os.path.exists(save_path):
            # print(f"File already exists, skipping download: {os.path.basename(save_path)}")
            return True
        
        try:
            # Use stream=True to handle potentially large files efficiently
            response = session.get(url, stream=True, timeout=30)
            response.raise_for_status() 

            # Ensure the parent directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True

        except requests.exceptions.RequestException as e:
            # print(f"Error downloading {url}: {e}")
            return False
        except IOError as e:
            # print(f"Error saving file to {save_path}: {e}")
            return False
        except Exception as e:
            # print(f"An unexpected error occurred during download of {url}: {e}")
            return False
