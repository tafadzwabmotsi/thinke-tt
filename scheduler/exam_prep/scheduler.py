from enum import Enum, auto
from itertools import cycle
import os
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path, PurePosixPath
from collections import defaultdict
from urllib.parse import urlparse

from data.schedules.exam_schedule_data_reader import ExamSchedulerDataReader
from data.students.student_data_writer import StudentDataWriter
from lib.constants import BASE_DIR
from lib.exam_council import ExamCouncil
from lib.grade import EceswaGrade, CambridgeGrade
from lib.subject import EceswaJcSubject
from lib.typing.data.schedule import DayOfWeek, ScheduleInputData
from lib.typing.domain.schedule import DailySchedule, DownloadedPastPaperMetadata, ExamSchedule, MonthlySchedule, SchedulePaper, ScheduledPastPaperMetadata, PastPaperMetadata, StudentInfo
from lib.typing.domain.student import Student, StudentRecord
from lib.utils import LibUtils


from datetime import datetime, timedelta
from typing import Dict, List, Any

from lib.typing.data.schedule import ScheduleInputData
from data.students.student_data_reader import StudentDataReader
from data.subjects.past_paper_metadata_reader import PastPaperMetadataReader

class ExamScheduler:
    """
    Generates and manages a personalized exam preparation schedule for a student.

    This class is responsible for:
    - Determining which exam papers to assign to a student for each study day.
    - Ensuring that no duplicate papers are assigned.
    - Respecting prioritized exam councils per subject.
    - Handling fallback logic when papers for a preferred council are exhausted.
    - Caching metadata for efficient lookups.
    - Verifying if a student has a complete schedule.
    """

    def __init__(self, student: Student):
        """
        Initialize the ExamScheduler.
        """
        self._student = student
        
        # Readers
        self._student_reader = StudentDataReader()
        self._schedule_reader = ExamSchedulerDataReader(EceswaGrade[self._student.grade])
        
        self._input_data = self._schedule_reader.get_schedule_input_data()
       
        self._past_paper_readers = {
                grade.value: PastPaperMetadataReader(grade.value) 
                for grade in list(list(EceswaGrade) + list(CambridgeGrade))
        }
        
        # Derived data: subjects + prioritized councils
        self._student_subjects_with_councils = [
            {
                'subject': council.subject,
                'councils': [ExamCouncil.from_value(c) for c in council.councils]
            }
            for council in self._input_data.prioritized_councils
            if council.subject in self._student.subjects
        ]

        # Paper tracking
        self._assigned_paper_urls = self._load_assigned_paper_urls()
   
        # Cached past papers per subject
        self._subject_paper_cache = self._cache_all_subject_papers()
    
    def _get_scheduled_records(self) -> list[ScheduledPastPaperMetadata]:
        """
        Get all scheduled exam records for the current student,
        sorted by date in ascending order (oldest first).

        Returns:
            list[ScheduledPastPaperMetadata]: Sorted scheduled records.
        """
        records = [
            record 
            for record in self._student_reader.get_exam_schedules_by_id(self._student.id)
            if record.url
        ]

        return sorted(
            records,
            key=lambda r: datetime.strptime(r.date, "%d-%m-%y")
        )
    
    def get_scheduled_records_by_day(self, day: str) -> list[ScheduledPastPaperMetadata]:
        return [
            record 
            for record in self._get_scheduled_records()
            if record.date == day
        ]
    
    def _generate_monthly_schedules(self) -> list[Dict]:
        """
        Generate a list of monthly blocks containing valid study days.

        Returns:
            List[Dict]: A list of dictionaries where each contains a year, month name, and
                        a list of valid study days formatted as 'dd-mm-yy'.
        """
        
        start_date = datetime.strptime(self._input_data.start_date, "%d-%m-%y")
        end_date = datetime.strptime(self._input_data.end_date, "%d-%m-%y")

        delta = timedelta(days=1)
        current = start_date
        monthly_schedules: Dict[str, Dict] = {}

        while current <= end_date:
            weekday_name = current.strftime('%A')
            if weekday_name not in self._input_data.excluded_days:
                year = current.year
                month_name = current.strftime('%B')
                day_formatted = current.strftime('%d-%m-%y')

                key = f"{year}-{month_name}"
                if key not in monthly_schedules:
                    monthly_schedules[key] = {
                        'year': year,
                        'month': month_name,
                        'days': []
                    }

                monthly_schedules[key]['days'].append(day_formatted)

            current += delta

        return list(monthly_schedules.values())

    def _load_assigned_paper_urls(self) -> set[str]:
        """
        Load previously assigned past paper URLs for the student.

        Returns:
            set[str]: A set of URLs that have already been assigned to avoid duplication.
        """
  
        return { record.url for record in self._get_scheduled_records() }

    def _get_subject_papers(self, subject: str) -> List[PastPaperMetadata]:
        """
        Retrieve all past papers for a given subject from the local cache.

        Args:
            subject (str): Subject to fetch papers for.

        Returns:
            List[PastPaperMetadata]: List of metadata objects for the subject.
        """
        
        return self._subject_paper_cache.get(subject, [])

    def _cache_all_subject_papers(self) -> Dict[str, Dict[str, List[PastPaperMetadata]]]:
        """
        Load and cache all past papers for the student's subjects across all available readers.

        Returns:
            Dict[str, Dict[str, List[PastPaperMetadata]]]: Nested dictionary of cached papers
            by subject and grade.
        """
        
        cache: Dict[str, Dict[str, List[PastPaperMetadata]]] = {}
        for subject in self._student.subjects:
            cache[subject] = {}
            for grade_key, reader in self._past_paper_readers.items():
                papers = reader.get_subject_metadata(subject)
                if papers:
                    cache[subject][grade_key] = papers
        return cache

    def _get_next_cambridge_igcse_unassigned_paper(
        self,
        subject: str,
    ) -> list[PastPaperMetadata]:
        """
        Return the next unassigned Cambridge IGCSE paper group for a subject.

        Papers are grouped by grade, subject, year, session, and filename stem to ensure
        related documents (e.g., QP and IN) are assigned together.

        Args:
            subject (str): The subject to fetch papers for.

        Returns:
            List[PastPaperMetadata]: A list of unassigned papers in the next group, or empty if none are found.
        """
        
        grade = CambridgeGrade.IGCSE.value
        all_papers = self._subject_paper_cache.get(subject, {}).get(grade, [])
        grouped_papers = defaultdict(list)

        def extract_group_key(paper: PastPaperMetadata) -> Optional[str]:
            try:
                filename = PurePosixPath(paper.url).name
                normalized = re.sub(r'_(qp|in)_', '_', filename)
                return f"{paper.grade}::{paper.subject}::{paper.year}::{paper.session}::{normalized}"
            except Exception:
                return []

        # Group papers by metadata + normalized filename stem
        for paper in all_papers:
            key = extract_group_key(paper)
            if key:
                grouped_papers[key].append(
                    PastPaperMetadata(
                        grade=paper.grade,
                        subject=paper.subject,
                        year=paper.year,
                        session=paper.session,
                        url=paper.url,
                        paper=LibUtils.extract_paper_label(paper.url)
                    )
                )

        for paper_group in grouped_papers.values():
            if all(p.url not in self._assigned_paper_urls for p in paper_group):
                for p in paper_group:
                    self._assigned_paper_urls.add(p.url)
                return paper_group 

        return []
    
    def _get_next_eceswa_unassigned_paper(self, subject: str, grade: str) -> list[PastPaperMetadata]:
        """
        Return the next unassigned ECESWA paper group for the given subject and grade.

        Groups papers by year, session, and paper number. Prioritizes latest year and lowest paper number.

        Args:
            subject (str): Subject to find papers for.
            grade (str): Grade (e.g., JC or EGCSE).

        Returns:
            list[PastPaperMetadata]: A list of unassigned papers or [].
        """
        
        def extract_paper_number(url: str) -> Optional[int]:
            """
            Extracts the paper number from the filename in the URL.
            Returns an integer (e.g., 1, 2) or None if not found.
            """
            match = re.search(r"Paper\s*(\d+)", url, re.IGNORECASE)
            if match:
                return int(match.group(1))
            return None
        
        subject_papers = self._subject_paper_cache.get(subject, {}).get(grade, [])
        grouped: Dict[tuple[int, str, Optional[int]], list[PastPaperMetadata]] = defaultdict(list)

        # Group by (year, session, paper_number)
        for paper in subject_papers:
            paper_number = extract_paper_number(paper.url)
            group_key = (paper.year, paper.session, paper_number)
            grouped[group_key].append(
                PastPaperMetadata(
                    grade=paper.grade,
                    subject=paper.subject,
                    year=paper.year,
                    session=paper.session,
                    url=paper.url,
                    paper=LibUtils.extract_paper_label(paper.url)
                )
            )

        # Sort groups by year descending, then paper number ascending
        sorted_groups = sorted(grouped.items(), key=lambda x: (-x[0][0], x[0][2] or 0))

        for (_, _, _), papers in sorted_groups:
            if all(p.url not in self._assigned_paper_urls for p in papers):
                for p in papers:
                    self._assigned_paper_urls.add(p.url)
                return papers

        return []

    def _get_next_eceswa_egcse_unassigned_paper(self, subject: str) -> list[PastPaperMetadata]:
        """
        Get the next unassigned ECESWA EGCSE paper group for the subject.

        Args:
            subject (str): Subject to assign.

        Returns:
            List[PastPaperMetadata]: Unassigned paper group or empty list.
        """
        return self._get_next_eceswa_with_reset(subject, EceswaGrade.EGCSE.value)

    def _get_next_eceswa_jc_unassigned_paper(self, subject: str) -> list[PastPaperMetadata]:
        """
        Get the next unassigned ECESWA JC paper group for the subject.

        Args:
            subject (str): Subject to assign.

        Returns:
            List[PastPaperMetadata]: Unassigned paper group or empty list.
        """
        
        return self._get_next_eceswa_with_reset(subject, EceswaGrade.JC.value)

    def _get_all_days(self) -> set[str]:
        """
        Get all valid schedule days within the configured range, respecting excluded days.

        Returns:
            set[str]: Set of valid study day strings in 'dd-mm-yy' format.
        """
        return {
            day
            for month_block in self._generate_monthly_schedules()
            for day in month_block["days"]
        }
        
    def _get_next_eceswa_with_reset(self, subject: str, grade: str) -> list[PastPaperMetadata]:
        """
        Get the next ECESWA unassigned paper group for the given subject and grade.
        Resets ECESWA assigned papers if exhausted.

        Args:
            subject (str): Subject to fetch papers for.
            grade (str): ECESWA grade (e.g., JC or EGCSE).

        Returns:
            list[PastPaperMetadata]: The next unassigned paper group.
        """
        
        def reset_eceswa_assigned_urls(grade: str):
            """
            Reset assigned paper URLs for ECESWA papers of a given grade.

            Args:
                grade (str): The ECESWA grade (e.g., JC or EGCSE).
            """
            eceswa_urls = {
                paper.url
                for subject, grades in self._subject_paper_cache.items()
                for g, papers in grades.items()
                if g == grade
                for paper in papers
            }
            self._assigned_paper_urls -= eceswa_urls
        
        papers = self._get_next_eceswa_unassigned_paper(subject, grade)
        if not papers:
            # Check if all ECESWA papers for this grade are already assigned
            all_papers = [
                p for g, papers in self._subject_paper_cache.get(subject, {}).items()
                if g == grade for p in papers
            ]
            all_urls = {p.url for p in all_papers}
            if all_urls.issubset(self._assigned_paper_urls):
                reset_eceswa_assigned_urls(grade)
                papers = self._get_next_eceswa_unassigned_paper(subject, grade)
        return papers
    
    def get_new_scheduled_papers_for_student(self) -> list[ScheduledPastPaperMetadata]:
        """
        Generate a strict one-subject-per-day exam preparation schedule for the student.

        Rules:
            - Subjects are scheduled in a fixed, round-robin order.
            - For each subject, councils are also scheduled in round-robin order.
            - If the chosen council has no papers left, the next council for that subject is tried.
            - A subject is always assigned for a given day, even if no papers are available.
            - No paper URL is assigned more than once across the schedule.

        Returns:
            list[ScheduledPastPaperMetadata]:
                List of scheduled papers (or empty placeholders) for each study day.
        """

        def get_papers_for_subject(subject: str, councils: list[ExamCouncil]) -> list[PastPaperMetadata]:
            """
            Get the next available paper(s) for a subject, rotating through councils.

            Logic:
                - Start with the current council index for this subject.
                - If that council has no unassigned papers, try the next council, and so on.
                - If no council has any unassigned papers, return an empty list.
                - Update the council index to the one after the council from which papers were assigned.

            Args:
                subject (str): The subject to assign.
                councils (list[ExamCouncil]): Councils to rotate through.

            Returns:
                list[PastPaperMetadata]: The next unassigned paper group, or [] if none remain.
            """
            start_index = council_indices[subject] % len(councils)

            for i in range(len(councils)):
                council = councils[(start_index + i) % len(councils)]

                if council == ExamCouncil.CAMBRIDGE:
                    papers = self._get_next_cambridge_igcse_unassigned_paper(subject)
                elif self._student.grade == EceswaGrade.EGCSE.value:
                    papers = self._get_next_eceswa_egcse_unassigned_paper(subject)
                else:
                    papers = self._get_next_eceswa_jc_unassigned_paper(subject)

                if papers:
                    council_indices[subject] = (start_index + i + 1) % len(councils)
                    return papers

            # No papers left for any council
            council_indices[subject] = (council_indices[subject] + 1) % len(councils)
            return []

        # All valid schedule days (already excludes weekends and configured off-days)
        all_days = sorted(
            self._get_all_days(),
            key=lambda d: datetime.strptime(d, "%d-%m-%y")
        )

        # Fixed order list of subjects
        subjects_order = [
            s_w_c["subject"]
            for s_w_c in self._student_subjects_with_councils
        ]

        # Map each subject to its available councils
        councils_map = {
            s_w_c["subject"]: s_w_c["councils"]
            for s_w_c in self._student_subjects_with_councils
        }

        # Track which council index to use next for each subject
        council_indices = {subject: 0 for subject in subjects_order}

        assigned_rows = []
        subject_index = 0

        for day in all_days:
            subject = subjects_order[subject_index % len(subjects_order)]
            councils = councils_map[subject]

            # Get papers for this subject, trying multiple councils if needed
            papers = get_papers_for_subject(subject, councils)

            # Add assigned papers (if any)
            for p in papers:
                assigned_rows.append(ScheduledPastPaperMetadata(
                    student_id=self._student.id,
                    date=day,
                    grade=p.grade,
                    subject=p.subject,
                    year=p.year,
                    session=p.session,
                    url=p.url,
                    paper=p.paper
                ))

            # If no papers, still log the empty subject assignment
            if not papers:
                assigned_rows.append(ScheduledPastPaperMetadata(
                    student_id=self._student.id,
                    date=day,
                    grade="",
                    subject=subject,
                    year=0,
                    session="",
                    url="",
                    paper=""
                ))

            subject_index += 1  # Move to the next subject for the next day

        return assigned_rows



    def has_complete_schedule(self) -> bool:
        """
        Check if the student has a complete schedule assigned.

        A complete schedule means that every valid schedule day has at least one paper assigned.

        Returns:
            bool: True if complete, False otherwise.
        """
        
        expected_days = self._get_all_days()
        assigned_days = {record.date for record in self._get_scheduled_records()}
        
        if not assigned_days:
            return False
        
        return assigned_days.issubset(expected_days)
    
    def schedule_written_to_database(self) -> bool:
        """
        Checks if the exam schedule is written to database.
        """
      
        all_downloaded_past_papers_urls = [
            record.url 
            for record in self._schedule_reader.get_downloaded_paper_metadata_records()
        ]
        
        all_scheduled_papers_urls = [record.url for record in self._get_scheduled_records()]
        
        return set(all_scheduled_papers_urls).issubset(set(all_downloaded_past_papers_urls))
    
    def papers_exist_in_src_dir(self) -> bool:
        """
        Check if the all the assigned past papers have been downloaded 
        onto disk
        """
        return all([
            paper.src_path.exists()
            for monthly_schedule in self.get_schedule().monthly_schedules
            for daily_schedule in monthly_schedule.daily_schedules 
            for paper in daily_schedule.papers
        ])
        
    def schedule_pdf_generated(self) -> bool:
        path = self.get_schedule().generated_pdf_path
        return Path(path).with_suffix('.pdf').resolve().exists()
    
    def schedule_copied_to_output_dir(self) -> bool:
        
        schedule_base_path = self.get_schedule().base_path / self._student.name
        copied_papers_paths = list(schedule_base_path.rglob("*.pdf"))
        
        
        scheduled_papers_paths = [
            paper.dest_path
            for ms in self.get_schedule().monthly_schedules
            for ds in ms.daily_schedules
            for paper in ds.papers
        ]
        
        return set(scheduled_papers_paths).issubset(set(copied_papers_paths))
    
    def get_exam_schedule_papers(self) -> list[SchedulePaper]:
        return [
            paper 
            for ms in self.get_schedule().monthly_schedules
            for ds in ms.daily_schedules
            for paper in ds.papers
        ]
    
    def get_schedule(self) -> ExamSchedule:
    
        
        # Base path for destination to which the past paper will be copied
        base_path = BASE_DIR / "Output" / self._student.grade
        generated_pdf_path = BASE_DIR / "Output" / "pdf" / f'{self._student.name} - Exam Preparation Schedule'
        
        # Group by year -> month -> date -> subject
        grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
        
        for r in self._get_scheduled_records():
            year, month = LibUtils.get_date_parts(r.date)
            
            filename = os.path.basename(urlparse(r.url).path)
            
            src_path = BASE_DIR / "Resources" / r.grade / r.subject / r.year / r.session / filename
            dest_path = base_path / self._student.name / year / month / r.date / r.subject / filename
        
            # Append the schedule paper object to the grouping
            if r.url:
                grouped[year][month][r.date][r.subject].append(SchedulePaper(
                    paper_metadata=DownloadedPastPaperMetadata(
                        grade=r.grade,
                        subject=r.subject,
                        year=r.year,
                        session=r.session,
                        url=r.url,
                        path=src_path,
                    ),
                    src_path=src_path,
                    dest_path=dest_path
                ))
        
        # Now build the ExamSchedule data structure
        monthly_schedules = []
        for year, months in sorted(grouped.items()):
            for month, dates in sorted(months.items()):
                daily_schedules = []
                for date, subjects in sorted(dates.items()):
                    for subject, papers in sorted(subjects.items()):
                        daily_schedule = DailySchedule(
                            day=date,
                            subject=subject,
                            papers=papers
                        )
                        daily_schedules.append(daily_schedule)
                        
                monthly_schedule = MonthlySchedule(
                    year=year,
                    month=month,
                    daily_schedules=daily_schedules
                )
                monthly_schedules.append(monthly_schedule)
        
        return ExamSchedule(
            student_info=StudentInfo(
                id=self._student.id,
                name=self._student.name,
                grade=self._student.grade
            ),
            base_path=base_path,
            generated_pdf_path=generated_pdf_path,
            monthly_schedules=monthly_schedules
        )
            