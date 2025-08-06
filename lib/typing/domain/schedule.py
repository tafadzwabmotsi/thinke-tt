from dataclasses import dataclass


@dataclass
class PastPaperMetadata:
    grade: str
    subject: str
    year: int
    url: str
    session: str
    paper: str

@dataclass
class ScheduledPastPaperMetadata(PastPaperMetadata):
    student_id: str
    date: str
    