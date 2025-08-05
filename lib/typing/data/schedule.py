from dataclasses import dataclass
from enum import Enum
from typing import List

class DayOfWeek(Enum):
    SUNDAY = "Sunday"
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"

@dataclass
class PrioritizedCouncil:
    subject: str
    councils: List[str]

@dataclass
class ScheduleInputData:
    start_date: str
    end_date: str
    excluded_days: List[DayOfWeek]
    prioritized_councils: List[PrioritizedCouncil]
    

@dataclass
class ScheduleOutputData:
    student_id: str
    day: str
    subject: str
    council: str
    session: str
    paper_title: str
    paper_code: str
    paper_type: str
    time_allowed: str
    paper_url: str