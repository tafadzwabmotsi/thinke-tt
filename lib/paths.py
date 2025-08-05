from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class StudentCSVPaths:
    base_dir: Path = Path.cwd() / "database" / "students"

    @property
    def info_file(self) -> Path:
        return self.base_dir / "student_info.csv"

    @property
    def subjects_file(self) -> Path:
        return self.base_dir / "student_subjects.csv"

    @property
    def contacts_file(self) -> Path:
        return self.base_dir / "student_contacts.csv"

    @property
    def assigned_schedules_file(self) -> Path:
        return self.base_dir / "assigned_schedules.csv"

@dataclass
class ExamScheduleCSVPaths:
    """
    Centralized paths for storing exam schedule input data
    """
    def __init__(self, grade: str):
        self.grade = grade.lower()
        self.base_dir: Path = Path.cwd() / "database" / "exam_preparation" / self.grade
    
    @property
    def dates_file(self) -> Path:
        return self.base_dir / "dates.csv"
    
    @property
    def excluded_days_file(self) -> Path:
        return self.base_dir / "excluded_days.csv"
    
    @property
    def prioritized_councils_file(self) -> Path:
        return self.base_dir / "prioritized_councils.csv"
    
    
@dataclass
class PastPaperCSVPaths:
    def __init__(self, grade: str):
        self.grade = grade.lower()
        self.base_dir: Path = Path.cwd() / "database" / "subjects" / self.grade

    def subject_file(self, subject: str) -> Path:
        return self.base_dir / f"{subject}.csv"
        