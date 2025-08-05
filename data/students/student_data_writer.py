import csv
from dataclasses import asdict
from pathlib import Path
from typing import List

from lib.paths import StudentCSVPaths
from lib.typing.domain.schedule import ScheduledPastPaperMetadata
from lib.typing.domain.student import StudentRecord

class StudentDataWriter:
    """
    Handles the storage of student records into structured CSV files.
    """

    def __init__(self):
        """
        Initialize the writer with a student record.
       
        """
        self._paths = StudentCSVPaths()

    def write_student_record(self, record: StudentRecord) -> bool:
        """
        Write the student record to the appropriate CSV files.

        Returns:
            bool: True if the record was saved successfully, False otherwise.
        """
        
        def ensure_file(path: Path):
            """
            Ensure that a file exists at the specified path with appropriate headers.

            Args:
                path (Path): The file path to check or create.
            """
            if not path.exists() or path.stat().st_size == 0:
                with path.open("w", newline='') as f:
                    writer = csv.writer(f)
                    if path == self._paths.info_file:
                        writer.writerow(["id", "name", "grade"])
                    elif path == self._paths.subjects_file:
                        # Use generic headers for subjects, or generate based on actual subjects
                        headers = ["id"] + [f"subject{i+1}" for i in range(len(record.subjects))]
                        writer.writerow(headers)
                    elif path == self._paths.contacts_file:
                        writer.writerow(["id", "phone"])

        def get_or_create_student_info(info_file: Path) -> int:
            """
            Retrieve the student's ID from the info file or create a new entry.

            Args:
                info_file (Path): Path to student_info.csv.

            Returns:
                int: The unique ID of the student.
            """
            student_id = None
            rows = []

            with info_file.open("r", newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    rows.append(row)
                    if (
                        len(row) >= 3 and
                        row[1].strip() == record.name.strip() and
                        row[2].strip() == record.grade
                    ):
                        student_id = int(row[0])
                        break

            if student_id is None:
                student_id = len(rows) + 1  # row count without header = current max ID
                with info_file.open("a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        student_id,
                        record.name.strip(),
                        record.grade
                    ])

            return student_id

        def write_subjects_if_missing(subjects_file: Path, student_id: int):
            """
            Write the student's subjects to the subjects file if not already recorded.

            Args:
                subjects_file (Path): Path to student_subjects.csv.
                student_id (int): ID associated with the student.
            """
            with subjects_file.open("r", newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if row and int(row[0]) == student_id:
                        return  # already exists

            with subjects_file.open("a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([student_id] + record.subjects)

        def write_contact_if_missing(contacts_file: Path, student_id: int):
            """
            Write the student's phone number to the contacts file if not already recorded.

            Args:
                contacts_file (Path): Path to student_contacts.csv.
                student_id (int): ID associated with the student.
            """
            with contacts_file.open("r", newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if row and int(row[0]) == student_id:
                        return  # already exists

            with contacts_file.open("a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([student_id, record.phone.strip()])
        
        try:
            self._paths.base_dir.mkdir(parents=True, exist_ok=True)

            ensure_file(self._paths.info_file)
            ensure_file(self._paths.subjects_file)
            ensure_file(self._paths.contacts_file)

            student_id = get_or_create_student_info(self._paths.info_file)
            write_subjects_if_missing(self._paths.subjects_file, student_id)
            write_contact_if_missing(self._paths.contacts_file, student_id)

            return True

        except Exception as err:
            print(f"[StudentDataWriter] Error saving student record: {err}")
            return False

    def write_exam_schedule_record(self, record: ScheduledPastPaperMetadata) -> bool:
        
        fieldnames = ["student_id", "date", "grade", "subject", "year", "session", "url"]
        
        def ensure_file(path: Path):
            if not path.exists() or path.stat().st_size == 0:
                with path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames)
                    writer.writeheader()
    
        file_path = self._paths.assigned_schedules_file

        try:
            ensure_file(file_path)
            with file_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames)
                writer.writerow({key: asdict(record)[key] for key in fieldnames})
            return True
        except Exception as e:
            print(f"Failed to write schedule record: {e}")
            return False
