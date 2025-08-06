import csv
from pathlib import Path
from typing import Optional

from lib.typing.data.schedule import ScheduleInputData, PrioritizedCouncil
from lib.paths import ExamScheduleCSVPaths
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
        try:
            start_date, end_date = self._read_dates()
            excluded_days = self._read_excluded_days()
            prioritized_councils = self._read_prioritized_councils()

            return ScheduleInputData(
                start_date=start_date,
                end_date=end_date,
                excluded_days=excluded_days,
                prioritized_councils=prioritized_councils
            )
        except FileNotFoundError:
            # One or more required files not found
            return None

    def _read_dates(self) -> tuple[str, str]:
        """Reads and returns human-readable start and end dates."""
        with self._paths.dates_file.open(mode="r", newline="") as file:
            reader = csv.reader(file)
            headers = next(reader)  # Skip header
            row = next(reader)
            return row[0], row[1]

    def _read_excluded_days(self) -> list[str]:
        """Reads excluded days from CSV."""
        with self._paths.excluded_days_file.open(mode="r", newline="") as file:
            reader = csv.reader(file)
            rows = list(reader)
            return rows[0] if rows else []

    def _read_prioritized_councils(self) -> list[PrioritizedCouncil]:
        """Reads prioritized councils from CSV."""
        prioritized: list[PrioritizedCouncil] = []

        with self._paths.prioritized_councils_file.open(mode="r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                subject = row[0]
                councils = row[1:] if len(row) > 1 else []
                prioritized.append(PrioritizedCouncil(subject=subject, councils=councils))

        return prioritized
