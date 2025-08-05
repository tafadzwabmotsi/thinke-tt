import csv
from lib.grade import EceswaGrade
from lib.paths import ExamScheduleCSVPaths
from lib.typing.data.schedule import ScheduleInputData


class ExamSchedulerDataWriter:
    """
    Writes structured exam preparation schedule data to CSV files:
    - dates.csv: stores start and end dates
    - excluded_days.csv: stores a list of excluded days
    - prioritized_councils.csv: stores subject-to-council mappings
    """

    def __init__(self, input_data: ScheduleInputData, grade: EceswaGrade):
        self._input_data = input_data
        self._paths = ExamScheduleCSVPaths(grade=grade.value)
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Ensure the base directory exists before writing any files."""
        self._paths.base_dir.mkdir(parents=True, exist_ok=True)

    def write(self):
        """Main method to write all data to their respective CSV files."""
        self._write_dates()
        self._write_excluded_days()
        self._write_prioritized_councils()

    def _write_dates(self):
        """Write the start and end dates in dd-mm-yy format to dates.csv."""
        with self._paths.dates_file.open(mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["start_date", "end_date"])
            writer.writerow([self._input_data.start_date, self._input_data.end_date])

    def _write_excluded_days(self):
        """Write excluded days (e.g., Sunday, Monday) to excluded_days.csv."""
        with self._paths.excluded_days_file.open(mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(self._input_data.excluded_days)

    def _write_prioritized_councils(self):
        """
        Write each subject and its associated councils to prioritized_councils.csv.
        Each row is structured as:
        subject, council_1, council_2, ..., council_n
        """
        with self._paths.prioritized_councils_file.open(mode="w", newline="") as file:
            writer = csv.writer(file)
            for prioritized in self._input_data.prioritized_councils:
                writer.writerow([prioritized.subject] + prioritized.councils)
