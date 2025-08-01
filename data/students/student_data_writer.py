import csv
from pathlib import Path

from lib.paths import StudentCSVPaths
from lib.typing.domain.student import StudentRecord

class StudentDataWriter:
    """
    Handles the storage of student records into structured CSV files.

    This class uses a StudentRecord object and writes the data into:
    - student_info.csv (core identity info)
    - student_subjects.csv (linked subjects)
    - student_contacts.csv (linked phone number)

    It ensures referential integrity by always referencing the ID from student_info.csv
    as the single source of truth.
    """

    def __init__(self, record: StudentRecord):
        """
        Initialize the writer with a student record.

        Args:
            record (StudentRecord): The structured student data to save.
        """
        self._record = record
        self._paths = StudentCSVPaths()

    def write_record(self) -> bool:
        """
        Write the student record to the appropriate CSV files.

        Returns:
            bool: True if the record was saved successfully, False otherwise.
        """
        try:
            self._paths.base_dir.mkdir(parents=True, exist_ok=True)

            self._ensure_file(self._paths.info_file)
            self._ensure_file(self._paths.subjects_file)
            self._ensure_file(self._paths.contacts_file)

            student_id = self._get_or_create_student_info(self._paths.info_file)
            self._write_subjects_if_missing(self._paths.subjects_file, student_id)
            self._write_contact_if_missing(self._paths.contacts_file, student_id)

            return True

        except Exception as err:
            print(f"[StudentDataWriter] Error saving student record: {err}")
            return False

    def _ensure_file(self, path: Path):
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
                    headers = ["id"] + [f"subject{i+1}" for i in range(len(self._record.subjects))]
                    writer.writerow(headers)
                elif path == self._paths.contacts_file:
                    writer.writerow(["id", "phone"])

    def _get_or_create_student_info(self, info_file: Path) -> int:
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
                    row[1].strip() == self._record.name.strip() and
                    row[2].strip() == self._record.grade
                ):
                    student_id = int(row[0])
                    break

        if student_id is None:
            student_id = len(rows) + 1  # row count without header = current max ID
            with info_file.open("a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    student_id,
                    self._record.name.strip(),
                    self._record.grade
                ])

        return student_id

    def _write_subjects_if_missing(self, subjects_file: Path, student_id: int):
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
            writer.writerow([student_id] + self._record.subjects)

    def _write_contact_if_missing(self, contacts_file: Path, student_id: int):
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
            writer.writerow([
                student_id,
                self._record.phone.strip()
            ])
