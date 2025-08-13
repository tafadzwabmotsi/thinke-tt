import csv
from dataclasses import asdict
import os


from data.students.student_data import StudentData
from lib.grade import EceswaGrade
from lib.typing.domain.schedule import ScheduledPastPaperMetadata
from lib.typing.domain.student import Student


class StudentDataReader(StudentData):
    def __init__(self):
        super().__init__()

    def get_students_by_grade(self, grade: EceswaGrade) -> list[Student]:
        """
        Retrieve all students for the given grade.

        Args:
            grade (EceswaGrade): The grade to filter students by.

        Returns:
            List[Student]: A list of fully populated Student objects.
        """
        students: list[Student] = []
        matching_infos = []

        # Read student_info.csv and collect matching students
        with self._paths.info_file.open("r", newline='') as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 3:
                    try:
                        student_id = row[0]
                        name = row[1].strip()
                        student_grade = row[2].strip()
                        if student_grade == grade.value:
                            matching_infos.append((student_id, name, student_grade))
                    except ValueError:
                        continue

        # Nothing found for this grade — return early
        if not matching_infos:
            return []

        # Load only relevant contacts
        contact_map = {}
        with self._paths.contacts_file.open("r", newline='') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    try:
                        student_id = row[0]
                        if student_id in {info[0] for info in matching_infos}:
                            contact_map[student_id] = row[1].strip()
                    except ValueError:
                        continue

        # Load only relevant subjects
        subjects_map = {}
        with self._paths.subjects_file.open("r", newline='') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    try:
                        student_id = row[0]
                        if student_id in {info[0] for info in matching_infos}:
                            subjects_map[student_id] = [s.strip() for s in row[1:] if s.strip()]
                    except ValueError:
                        continue

        # Build Student objects
        for student_id, name, student_grade in matching_infos:
            phone = contact_map.get(student_id, "")
            subjects = subjects_map.get(student_id, [])
            students.append(Student(
                id=student_id,
                name=name,
                phone=phone,
                grade=student_grade,
                subjects=subjects
            ))

        return students
    
    def exam_schedule_record_exists(self, record: ScheduledPastPaperMetadata) -> bool:
        path = self._paths.assigned_schedules_file
        if not path.exists():
            return False

        record_dict = {key: asdict(record)[key] for key in self._exam_schedule_record_fieldnames}

        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if all(str(row[key]).strip() == str(record_dict[key]).strip() for key in self._exam_schedule_record_fieldnames):
                    return True

        return False

    def get_exam_schedules_by_id(self, id: str) -> list[ScheduledPastPaperMetadata]:
        """
        Returns all scheduled exam records for the given student ID.
        """
        matching_records = []
        path = self._paths.assigned_schedules_file

        if path.exists():
            with path.open(mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file, fieldnames=self._exam_schedule_record_fieldnames)
                next(reader, None)

                for row in reader:
                    if row.get("student_id", "").strip() == id.strip():
                        try:
                            record = ScheduledPastPaperMetadata(
                                student_id=row["student_id"],
                                date=row["date"],
                                grade=row["grade"],
                                subject=row["subject"],
                                year=row["year"],
                                session=row["session"],
                                url=row["url"],
                                paper=row["paper"]
                            )
                            matching_records.append(record)
                        except Exception as e:
                            print(f"[StudentDataReader] Skipping row due to error: {e}")

        return matching_records

    def get_exam_schedules_by_id_and_day(self, student_id: str, day: str) -> list[ScheduledPastPaperMetadata]:
        records = []

        file_path = self._paths.assigned_schedules_file
        if not file_path.exists():
            return records

        with file_path.open(mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["student_id"] == str(student_id) and row["date"] == day:
                    try:
                        records.append(ScheduledPastPaperMetadata(
                            student_id=row["student_id"],
                            date=row["date"],
                            grade=row["grade"],
                            subject=row["subject"],
                            year=row["year"],
                            session=row["session"],
                            url=row["url"],
                            paper=row["paper"]
                        ))
                    except Exception as e:
                        print(f"[StudentDataReader] Skipping invalid row: {row} — {e}")
                        continue

        return records

    def msgs_for_id_and_day_exist(self, student_id: str, day: str) -> bool:
        file_path = self._paths.sent_msgs_file

        if not os.path.exists(file_path):
            return False 

        with open(file_path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['student_id'] == student_id and row['date'] == day:
                    return True  

        return False 
            