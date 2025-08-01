from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class StudentCSVPaths:
    """Centralized file paths for storing student-related data."""
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
