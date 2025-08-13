import csv
from dataclasses import asdict
import os
from lib.grade import EceswaGrade
from lib.paths import ExamScheduleCSVPaths
from lib.typing.data.schedule import ScheduleInputData
from lib.typing.domain.schedule import DownloadedPastPaperMetadata


class ExamSchedulerDataWriter:
    """
    Writes structured exam preparation schedule data to CSV files:
    - dates.csv: stores start and end dates
    - excluded_days.csv: stores a list of excluded days
    - prioritized_councils.csv: stores subject-to-council mappings
    """

    def __init__(self, grade: EceswaGrade):
        self._paths = ExamScheduleCSVPaths(grade=grade.value)
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Ensure the base directory exists before writing any files."""
        self._paths.base_dir.mkdir(parents=True, exist_ok=True)

    def write_schedule_input_data(self, input_data: ScheduleInputData,):
        """Main method to write all data to their respective CSV files."""
        
        def write_dates():
            """Write the start and end dates in dd-mm-yy format to dates.csv."""
            with self._paths.dates_file.open(mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["start_date", "end_date"])
                writer.writerow([input_data.start_date, input_data.end_date])

        def write_excluded_days():
            """Write excluded days (e.g., Sunday, Monday) to excluded_days.csv."""
            with self._paths.excluded_days_file.open(mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(input_data.excluded_days)

        def write_prioritized_councils():
            """
            Write each subject and its associated councils to prioritized_councils.csv.
            Each row is structured as:
            subject, council_1, council_2, ..., council_n
            """
            with self._paths.prioritized_councils_file.open(mode="w", newline="") as file:
                writer = csv.writer(file)
                for prioritized in input_data.prioritized_councils:
                    writer.writerow([prioritized.subject] + prioritized.councils)
                
        write_dates()
        write_excluded_days()
        write_prioritized_councils()
    
    def write_downloaded_paper_metadata_record(self, record: DownloadedPastPaperMetadata) -> bool:
        file_path = self._paths.downloaded_past_papers_file
        headers = list(DownloadedPastPaperMetadata.__annotations__.keys())
        record_dict = asdict(record)

        # Ensure the file exists with headers
        file_exists = os.path.exists(file_path)
        if not file_exists:
            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

        # Check if record already exists
        with open(file_path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if all(row[key] == record_dict[key] for key in headers):
                    return False 

        # Write the new record
        with open(file_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writerow(record_dict)

        return True
