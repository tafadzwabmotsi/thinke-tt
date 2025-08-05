import csv
from typing import Dict, List

from lib.grade import EceswaGrade
from lib.paths import StudentCSVPaths
from lib.typing.domain.student import Student

# data/students/student_data_reader.py
class StudentDataReader:
    def __init__(self, grade: str):
        self._grade = grade
        self._paths = StudentCSVPaths()

    def get_students_by_grade(self) -> List[Student]:
        """
        Retrieve all students for the given grade.

        Args:
            grade (EceswaGrade): The grade to filter students by.

        Returns:
            List[Student]: A list of fully populated Student objects.
        """
        students: List[Student] = []
        matching_infos = []

        # Read student_info.csv and collect matching students
        with self._paths.info_file.open("r", newline='') as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 3:
                    try:
                        student_id = int(row[0])
                        name = row[1].strip()
                        student_grade = row[2].strip()
                        if student_grade == self._grade:
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
                        student_id = int(row[0])
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
                        student_id = int(row[0])
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

    def get_assigned_schedules(self) -> List[Dict[str, str]]:
        rows = []
        if self._paths.assigned_schedules_file.exists():
            with self._paths.assigned_schedules_file.open(mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    rows.append(row)
        return rows
