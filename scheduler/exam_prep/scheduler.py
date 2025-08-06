from enum import Enum, auto
from itertools import cycle
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import PurePosixPath
from collections import defaultdict

from data.students.student_data_writer import StudentDataWriter
from lib.exam_council import ExamCouncil
from lib.grade import EceswaGrade, CambridgeGrade
from lib.typing.data.schedule import DayOfWeek, ScheduleInputData
from lib.typing.domain.schedule import ScheduledPastPaperMetadata, PastPaperMetadata
from lib.typing.domain.student import Student, StudentRecord
from lib.utils import LibUtils
from scheduler.exam_prep.utils import ExamSchedulerUtils as Utils


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

    def __init__(
        self, 
        student: Student, 
        input_data: ScheduleInputData,
        student_data_reader,
        past_paper_readers
        ):
        """
        Initialize the ExamScheduler.

        Args:
            student (Student): The student to generate the schedule for.
            input_data (ScheduleInputData): The input configuration including dates, subjects, and exclusions.
            student_data_reader (StudentDataReader): Reader for retrieving stored schedule data.
            past_paper_readers (Dict[str, PastPaperMetadataReader]): Readers for accessing past paper metadata per grade.
        """
        
        self._student = student
        self._input_data = input_data

        self._exam_schedule: Dict[str, Any] = {}

        # Readers
        self._student_reader: StudentDataReader = student_data_reader
       
        self._past_paper_readers: Dict[str, PastPaperMetadataReader] = past_paper_readers
        
        # Derived data: subjects + prioritized councils
        self._student_subjects_with_councils: List[Dict[str, Any]] = [
            {
                'subject': council.subject,
                'councils': [ExamCouncil.from_value(c) for c in council.councils]
            }
            for council in self._input_data.prioritized_councils
            if council.subject in self._student.subjects
        ]

        # Paper tracking
        self._assigned_paper_urls: set[str] = self._load_assigned_paper_urls()
   
        # Cached past papers per subject
        self._subject_paper_cache: Dict[str, Dict[str, List[PastPaperMetadata]]] = self._cache_all_subject_papers()
    
    def _generate_monthly_schedules(self) -> List[Dict]:
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
        
        rows = self._student_reader.get_all_exam_schedule_records_by_student_id(self._student.id)
        return {
            row.url
            for row in rows
        }

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
    ) -> List[PastPaperMetadata]:
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
                        paper=Utils.extract_cambridge_paper_label(paper.url)
                    )
                )

        for paper_group in grouped_papers.values():
            if all(p.url not in self._assigned_paper_urls for p in paper_group):
                for p in paper_group:
                    self._assigned_paper_urls.add(p.url)
                return paper_group 

        return []
    
    def _get_next_eceswa_unassigned_paper(self, subject: str, grade: str) -> Optional[List[PastPaperMetadata]]:
        """
        Return the next unassigned ECESWA paper group for the given subject and grade.

        Groups papers by year, session, and paper number. Prioritizes latest year and lowest paper number.

        Args:
            subject (str): Subject to find papers for.
            grade (str): Grade (e.g., JC or EGCSE).

        Returns:
            Optional[List[PastPaperMetadata]]: A list of unassigned papers or None.
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
        grouped: Dict[tuple[int, str, Optional[int]], List[PastPaperMetadata]] = defaultdict(list)

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
                    paper=Utils.extract_eceswa_paper_label(paper.url)
                )
            )

        # Sort groups by year descending, then paper number ascending
        sorted_groups = sorted(grouped.items(), key=lambda x: (-x[0][0], x[0][2] or 0))

        for (_, _, _), papers in sorted_groups:
            if all(p.url not in self._assigned_paper_urls for p in papers):
                return papers

        return None

    def _get_next_eceswa_egcse_unassigned_paper(self, subject: str) -> List[PastPaperMetadata]:
        """
        Get the next unassigned ECESWA EGCSE paper group for the subject.

        Args:
            subject (str): Subject to assign.

        Returns:
            List[PastPaperMetadata]: Unassigned paper group or empty list.
        """
        return self._get_next_eceswa_unassigned_paper(subject, EceswaGrade.EGCSE.value)

    def _get_next_eceswa_jc_unassigned_paper(self, subject: str) -> List[PastPaperMetadata]:
        """
        Get the next unassigned ECESWA JC paper group for the subject.

        Args:
            subject (str): Subject to assign.

        Returns:
            List[PastPaperMetadata]: Unassigned paper group or empty list.
        """
        
        return self._get_next_eceswa_unassigned_paper(subject, EceswaGrade.JC.value)

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
    
    def get_scheduled_papers_for_student(self) -> List[ScheduledPastPaperMetadata]:
        """
        Generate a complete schedule of exam papers for the student.

        Cycles through each subject and its prioritized councils, ensuring no paper is repeated
        and fallback strategies are used if preferred councils are exhausted.

        Returns:
            List[ScheduledPastPaperMetadata]: List of scheduled papers with student and date info.
        """
        
        def get_fallback_papers(
            subject: str,
            council: ExamCouncil,
            councils: List[ExamCouncil]
        ) -> List[PastPaperMetadata]:
            """
            Return the next set of unassigned papers based on council and fallback strategy.
            Prioritizes ECESWA for EGCSE students, but falls back to CAMBRIDGE if needed.
            """
            papers = []

            if council == ExamCouncil.CAMBRIDGE:
                papers = self._get_next_cambridge_igcse_unassigned_paper(subject)

            elif self._student.grade == EceswaGrade.EGCSE.value:
                # First try ECESWA
                papers = self._get_next_eceswa_egcse_unassigned_paper(subject)

                # Fallback to CAMBRIDGE if ECESWA papers are exhausted
                if not papers and ExamCouncil.CAMBRIDGE in councils:
                    papers = self._get_next_cambridge_igcse_unassigned_paper(subject)

            else:
                # For JC students (only ECESWA)
                papers = self._get_next_eceswa_jc_unassigned_paper(subject)

            return papers

        all_days = self._get_all_days()

        assigned_rows: List[ScheduledPastPaperMetadata] = []
        
        subjects_cycle = cycle(self._student_subjects_with_councils)
        subject_assignments: Dict[str, int] = {
            s_w_c['subject']: 0 
            for s_w_c in self._student_subjects_with_councils
        }

        for day in all_days:
            for _ in range(len(self._student_subjects_with_councils)):
                subject_entry = next(subjects_cycle)
                subject = subject_entry["subject"]
                councils = subject_entry["councils"]
                
                council = councils[subject_assignments[subject] % len(councils)]

                papers = get_fallback_papers(subject, council, councils)
                
                if papers:
                    for p in papers:
                        self._assigned_paper_urls.add(p.url)
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
                    subject_assignments[subject] += 1
                    
                    # move to the next day after a successful assignment
                    break 
        
        return assigned_rows

    def student_has_complete_schedule(self) -> bool:
        """
        Check if the student has a complete schedule assigned.

        A complete schedule means that every valid schedule day has at least one paper assigned.

        Returns:
            bool: True if complete, False otherwise.
        """
        
        expected_days = self._get_all_days()
        
        assigned_records = self._student_reader.get_all_exam_schedule_records_by_student_id(self._student.id)
        assigned_days = {record.date for record in assigned_records}

        return expected_days == assigned_days
    