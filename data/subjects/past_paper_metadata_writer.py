import csv
import os
from typing import List
from lib.typing.data.downloader import DownloadLinks


class PaperPaperMetadataWriter:
    """
    Handles the storage of subject-specific download metadata into structured CSV files.

    Each subject is grouped under its grade and saved in a dedicated CSV file located in:
    ./database/subjects/<grade>/<subject>.csv

    Files are created if they do not exist, including dynamic headers based on the metadata provided.
    Duplicate entries are avoided based on exact row matching.
    
    Args:
        urls (DownloadLinks): A dictionary where each key is a comma-separated string
            representing metadata (e.g., "IGCSE,Mathematics,2023,November"), and each value
            is a list of associated download URLs.
    """

    def __init__(self, urls: DownloadLinks):
        self._urls = urls

    def write(self):
        """
        Saves download URLs into CSV files organized by grade and subject.

        Each CSV file includes the following columns:
            - grade
            - subject
            - year
            - session (optional)
            - url

        Notes:
            - CSV headers are written if the file is new or empty.
            - Existing rows are preserved, and duplicates are not re-added.
            - Malformed keys (fewer than 3 parts) are skipped.
        """
        base_dir = os.path.join(os.getcwd(), "database", "subjects")

        for key, url_list in self._urls.items():
            parts = key.split(",")
            if len(parts) < 3:
                print(f"Skipping malformed key: {key}")
                continue

            grade = parts[0].strip().lower()
            subject = parts[1].strip().lower()

            subject_dir = os.path.join(base_dir, grade)
            os.makedirs(subject_dir, exist_ok=True)

            csv_path = os.path.join(subject_dir, f"{subject}.csv")

            # Build header dynamically based on parts length
            header = ["grade", "subject", "year"]
            if len(parts) > 3:
                header.append("session")
            header.append("url")

            # Ensure file exists and has a header
            self._ensure_csv_with_header(csv_path, header)

            # Load existing rows to avoid duplicates
            existing_rows = set()
            with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    existing_rows.add(tuple(row))

            # Append new rows if not duplicates
            with open(csv_path, mode="a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)

                for url in url_list:
                    row = parts + [url]
                    row_tuple = tuple(row)

                    if row_tuple not in existing_rows:
                        writer.writerow(row)
                        existing_rows.add(row_tuple)

    def _ensure_csv_with_header(self, path: str, header: List[str]):
        """
        Ensures that the given CSV file exists and starts with the correct header.

        Args:
            path (str): The full path to the CSV file.
            header (List[str]): The header row to write if the file is new or empty.
        """
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            with open(path, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
