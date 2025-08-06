import csv
from dataclasses import asdict
from pathlib import Path
import uuid

from data.students.student_data import StudentData
from data.students.student_data_reader import StudentDataReader
from lib.typing.domain.schedule import ScheduledPastPaperMetadata
from lib.typing.domain.student import StudentRecord

class StudentDataWriter(StudentData):
    """
    Handles the storage of student records into structured CSV files.
    """

    def __init__(self):
        super().__init__()
        self._reader = StudentDataReader()

    def write_student_record(self, record: StudentRecord) -> bool:
        """
        Write the student record to the appropriate CSV files.

        Returns:
            bool: True if the record was saved successfully, False otherwise.
        """

        def ensure_file(path: Path):
            """Ensure file exists with proper headers."""
            if not path.exists() or path.stat().st_size == 0:
                with path.open("w", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if path == self._paths.info_file:
                        writer.writerow(["id", "name", "grade"])
                    elif path == self._paths.subjects_file:
                        headers = ["id"] + [f"subject{i+1}" for i in range(len(record.subjects))]
                        writer.writerow(headers)
                    elif path == self._paths.contacts_file:
                        writer.writerow(["id", "phone"])

        def get_or_create_student_info(info_file: Path) -> str:
            """
            Retrieve or create student ID based on name + grade match.

            Returns:
                str: UUID string as the student ID.
            """
            student_id = None

            with info_file.open("r", newline='', encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    if (
                        len(row) >= 3 and
                        row[1].strip() == record.name.strip() and
                        row[2].strip() == record.grade
                    ):
                        student_id = row[0]  # ID is already a string
                        break

            if student_id is None:
                student_id = str(uuid.uuid4())
                with info_file.open("a", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        student_id,
                        record.name.strip(),
                        record.grade
                    ])

            return student_id

        def write_subjects_if_missing(subjects_file: Path, student_id: str):
            """Write subjects only if not already present."""
            with subjects_file.open("r", newline='', encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and row[0] == student_id:
                        return

            with subjects_file.open("a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([student_id] + record.subjects)

        def write_contact_if_missing(contacts_file: Path, student_id: str):
            """Write contact if not already present."""
            with contacts_file.open("r", newline='', encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and row[0] == student_id:
                        return

            with contacts_file.open("a", newline='', encoding="utf-8") as f:
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
        fieldnames = self._exam_schedule_record_fieldnames

        def ensure_file(path: Path):
            if not path.exists() or path.stat().st_size == 0:
                with path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

        file_path = self._paths.assigned_schedules_file

        try:
            ensure_file(file_path)
            new_row = {key: asdict(record)[key] for key in fieldnames}
        
            if self._reader.exam_schedule_record_exists(record):
                return False

            # Append new row
            with file_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(new_row)

            return True

        except Exception as e:
            print(f"Failed to write schedule record: {e}")
            return False

