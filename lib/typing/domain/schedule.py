from dataclasses import dataclass
from pathlib import Path

@dataclass
class PastPaperMetadata:
    grade: str
    subject: str
    year: str
    url: str
    session: str
    paper: str

@dataclass
class ScheduledPastPaperMetadata(PastPaperMetadata):
    student_id: str
    date: str
    
@dataclass
class MsgRecord:
    student_id: str
    date: str
    exam_council: str
    subject: str
    session: str
    attached_url: str 

@dataclass
class StudentInfo:
    id: str
    name: str
    grade: str

@dataclass
class DownloadedPastPaperMetadata:
    grade: str
    subject: str
    year: str
    session: str
    url: str
    path: Path
    
@dataclass
class SchedulePaper:
    paper_metadata: DownloadedPastPaperMetadata
    src_path: Path
    dest_path: Path

@dataclass
class DailySchedule:
    day: str
    subject: str
    papers: list[SchedulePaper]
    
@dataclass
class MonthlySchedule:
    year: str
    month: str
    daily_schedules: list[DailySchedule]

@dataclass
class ExamSchedule:
    student_info: StudentInfo
    base_path: Path
    generated_pdf_path: Path
    monthly_schedules: list[MonthlySchedule]