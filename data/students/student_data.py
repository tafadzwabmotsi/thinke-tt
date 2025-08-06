
from lib.paths import StudentCSVPaths

class StudentData:
    def __init__(self):
        self._paths = StudentCSVPaths()
        self._exam_schedule_record_fieldnames = ["student_id", "date", "grade", "subject", "paper", "year", "session", "url"]
