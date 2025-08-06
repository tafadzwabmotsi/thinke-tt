
from enum import Enum


class ExamCouncil(Enum):
    """
    Defines the exam council from which the past papers 
    will be taken.
    """
    ECESWA = "Examinations Councils of Eswatini"
    CAMBRIDGE = "Cambridge Assessment International Education"
    
    @classmethod
    def from_value(cls, value: str):
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching ExamCouncil for value: {value}")