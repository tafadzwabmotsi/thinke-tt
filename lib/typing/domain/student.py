
from dataclasses import dataclass
from typing import List


@dataclass
class StudentRecord:
    name: str
    phone: str
    grade: str
    subjects: List[str]

@dataclass
class Student(StudentRecord):
    id: int
