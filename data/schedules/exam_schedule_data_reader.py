import csv
import os
from pathlib import Path
from typing import Optional

from lib.typing.data.schedule import ScheduleInputData, PrioritizedCouncil
from lib.paths import ExamScheduleCSVPaths
from lib.typing.domain.schedule import DownloadedPastPaperMetadata
from lib.utils import LibUtils
from lib.grade import EceswaGrade


class ExamSchedulerDataReader:
    """
    Reads structured exam preparation data from CSV files and reconstructs a ScheduleInputData object.
    """

    def __init__(self, grade: EceswaGrade):
        self.grade = grade.value.lower()
        self._paths = ExamScheduleCSVPaths(grade=self.grade)

    def get_schedule_input_data(self) -> Optional[ScheduleInputData]:
        """Reads exam schedule data from CSV files and returns a structured ScheduleInputData object."""
        
        def read_dates() -> tuple[str, str]:
            """Reads and returns human-readable start and end dates."""
            with self._paths.dates_file.open(mode="r", newline="") as file:
                reader = csv.reader(file)
                headers = next(reader)  # Skip header
                row = next(reader)
                return row[0], row[1]

        def read_excluded_days() -> list[str]:
            """Reads excluded days from CSV."""
            with self._paths.excluded_days_file.open(mode="r", newline="") as file:
                reader = csv.reader(file)
                rows = list(reader)
                return rows[0] if rows else []

        def read_prioritized_councils() -> list[PrioritizedCouncil]:
            """Reads prioritized councils from CSV."""
            prioritized: list[PrioritizedCouncil] = []

            with self._paths.prioritized_councils_file.open(mode="r", newline="") as file:
                reader = csv.reader(file)
                for row in reader:
                    subject = row[0]
                    councils = row[1:] if len(row) > 1 else []
                    prioritized.append(PrioritizedCouncil(subject=subject, councils=councils))

            return prioritized
    
        try:
            start_date, end_date = read_dates()
            excluded_days = read_excluded_days()
            prioritized_councils = read_prioritized_councils()

            return ScheduleInputData(
                start_date=start_date,
                end_date=end_date,
                excluded_days=excluded_days,
                prioritized_councils=prioritized_councils
            )
        except FileNotFoundError:
            # One or more required files not found
            return None
    
    def get_downloaded_paper_metadata_records(self) -> list[DownloadedPastPaperMetadata]:
        file_path = self._paths.downloaded_past_papers_file

        if not os.path.exists(file_path):
            return [] 

        records = []
        
        with open(file_path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not any(row.values()):
                    continue
                records.append(DownloadedPastPaperMetadata(**row))

        return records
