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
from scheduler.exam_prep.utils import ExamSchedulerUtils


from datetime import datetime, timedelta
from typing import Dict, List, Any

from lib.typing.data.schedule import ScheduleInputData
from data.students.student_data_reader import StudentDataReader
from data.subjects.past_paper_metadata_reader import PastPaperMetadataReader

class ExamScheduler:
    """
    A class to generate and manage exam preparation schedules for a given student.
    """

    def __init__(
        self, 
        student: Student, 
        input_data: ScheduleInputData,
        student_data_reader,
        past_paper_readers
        ):
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
                'councils': [ExamCouncil[c] for c in council.councils]
            }
            for council in self._input_data.prioritized_councils
            if council.subject in self._student.subjects
        ]

        # Paper tracking
        self._assigned_paper_urls: set[str] = self._load_assigned_paper_urls()

        # Cached past papers per subject
        self._subject_paper_cache: Dict[str, Dict[str, List[PastPaperMetadata]]] = self._cache_all_subject_papers()
        
        # paper = self._get_next_cambridge_igcse_unassigned_paper('English Language', ExamCouncil.CAMBRIDGE)
        
        # print(paper)    
        
        # print(self._subject_paper_cache.get('English Language').get('EGCSE'))
    
    def _generate_monthly_schedules(self) -> List[Dict]:
        """Generate valid monthly schedule blocks between start and end dates, 
           excluding specified weekdays.
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
        """Load previously assigned past paper URLs to avoid reassignment."""
        rows = self._student_reader.get_assigned_schedules()
        return {
            row['url']
            for row in rows
            if row.get('url')
        }

    def _get_subject_papers(self, subject: str) -> List[PastPaperMetadata]:
        """Retrieve all papers (as PastPaper objects) for a subject, from cache."""
        return self._subject_paper_cache.get(subject, [])

    def _cache_all_subject_papers(self) -> Dict[str, Dict[str, List[PastPaperMetadata]]]:
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
        Return the next unassigned IGCSE paper group (e.g., QP + IN) for the given subject.
        A group is a set of papers sharing grade, subject, year, session, and filename stem.
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
                grouped_papers[key].append(paper)

        for paper_group in grouped_papers.values():
            if all(p.url not in self._assigned_paper_urls for p in paper_group):
                for p in paper_group:
                    self._assigned_paper_urls.add(p.url)
                return paper_group 

        return []
    
    def _get_next_eceswa_unassigned_paper(self, subject: str, grade: str) -> Optional[List[PastPaperMetadata]]:
        """
        Return the next unassigned ECESWA paper group (Question/Insert), grouped by paper number.
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
            grouped[group_key].append(paper)

        # Sort groups by year descending, then paper number ascending
        sorted_groups = sorted(grouped.items(), key=lambda x: (-x[0][0], x[0][2] or 0))

        for (_, _, _), papers in sorted_groups:
            if all(p.url not in self._assigned_paper_urls for p in papers):
                return papers

        return None

    def _get_next_eceswa_egcse_unassigned_paper(self, subject: str) -> List[PastPaperMetadata]:
        return self._get_next_eceswa_unassigned_paper(subject, EceswaGrade.EGCSE.value)

    def _get_next_eceswa_jc_unassigned_paper(self, subject: str) -> List[PastPaperMetadata]:
        return self._get_next_eceswa_unassigned_paper(subject, EceswaGrade.JC.value)

    def get_scheduled_papers_for_student(self) -> List[ScheduledPastPaperMetadata]:
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

        all_days = [
            day
            for month_block in self._generate_monthly_schedules()
            for day in month_block["days"]
        ]

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
                    for paper in papers:
                        self._assigned_paper_urls.add(paper.url)
                        assigned_rows.append(ScheduledPastPaperMetadata(
                            student_id=self._student.id,
                            date=day,
                            grade=paper.grade,
                            subject=paper.subject,
                            year=paper.year,
                            session=paper.session,
                            url=paper.url
                        ))
                    subject_assignments[subject] += 1
                    
                    # move to the next day after a successful assignment
                    break 
        
        return assigned_rows

    def _assign_exam_council(
        self,
        subject_config: Dict[str, Any],
        papers_cache: Dict[str, List[List[str]]],
        subject_group_indices: Dict[str, int],
        subject_council_indices: Dict[str, int],
    ):
        
        student_grade = self._student['grade']
        
        subject_title = subject_config["title"]
        prioritized_councils = subject_config["prioritized_exam_councils"]
        fallback_council = subject_config.get("fallback_exam_council", None)
        tried = 0
        num_councils = len(prioritized_councils)
        start_index = subject_council_indices[subject_title]

        while tried < num_councils:
            council = prioritized_councils[(start_index + tried) % num_councils]

            grade_folder = (
                EceswaGrade.IGCSE.value if council.name == ExamCouncil.CAMBRIDGE.value
                else student_grade.value
            )
            subject_path = os.path.join(self._read_base_path, grade_folder, subject_title.value)
            
            print(grade_folder, subject_title.value)

            if subject_path not in papers_cache:
                papers_cache[subject_path] = self._get_past_papers(subject_path)
                subject_group_indices[subject_path] = 0

            group_index = subject_group_indices[subject_path]
            all_groups = papers_cache[subject_path]

            if group_index < len(all_groups):
                subject_group_indices[subject_path] += 1
                return all_groups[group_index], council

            tried += 1

        # Fallback attempt
        if fallback_council:
            grade_folder = (
                EceswaGrade.IGCSE.value if fallback_council.name == ExamCouncil.CAMBRIDGE.value
                else student_grade.value
            )
            fallback_path = os.path.join(self._read_base_path, grade_folder, subject_title.value)

            if fallback_path not in papers_cache:
                papers_cache[fallback_path] = self._get_past_papers(fallback_path)
                subject_group_indices[fallback_path] = 0

            group_index = subject_group_indices[fallback_path]
            fallback_groups = papers_cache[fallback_path]

            if group_index < len(fallback_groups):
                subject_group_indices[fallback_path] += 1
                return fallback_groups[group_index], fallback_council

        return [], prioritized_councils[start_index]

    
    def generate_exam_schedule(self) -> Dict[str, Any]:
        
        student_name = self._student['name']
        student_grade = self._student['grade']
        subjects = self._student['subjects']
        
        monthly_schedules = self._generate_monthly_schedules()
        exam_schedule: List[Dict[str, Any]] = []

        papers_cache: Dict[str, List[List[str]]] = {}
        subject_group_indices: Dict[str, int] = {}
        subject_index = 0
        
        subject_council_indices = {subj["title"]: 0 for subj in subjects}
        for month_schedule in monthly_schedules:
            daily_schedules = []

            for day in month_schedule["days"]:
                subject_config = subjects[subject_index]
                subject_title = subject_config["title"]

                papers, selected_council = self._assign_exam_council(
                    subject_config=subject_config,
                    papers_cache=papers_cache,
                    subject_group_indices=subject_group_indices,
                    subject_council_indices=subject_council_indices
                )

                subject_council_indices[subject_title] = (
                    subject_council_indices[subject_title] + 1
                ) % len(subject_config["prioritized_exam_councils"])

                daily_schedules.append({
                    "day": day,
                    "subject": subject_title.value,
                    "papers": papers,
                    "exam_council": selected_council.value
                })

                subject_index = (subject_index + 1) % len(subjects)
                
            exam_schedule.append({
                "year": month_schedule["year"],
                "month": month_schedule["month"],
                "daily_schedules": daily_schedules
            })
        
        self._exam_schedule['student_info'] = {
                    'name': student_name,
                    'grade': student_grade.value,
                    'base_path':self._student['base_path'],
            }
        self._exam_schedule['exam_schedule'] = exam_schedule    

        return self._exam_schedule

    def _get_past_papers(self, subject_path: str) -> List[List[Dict[str, str]]]:
        """Scan and group past paper files by year and paper number, sorted for scheduling."""

        igcse_grouped = defaultdict(list)
        eceswa_grouped = defaultdict(list)

        def extract_igcse_metadata(file_path: str):
            try:
                parts = file_path.split(os.sep)
                year = int(parts[-3])
                session = parts[-2]
                match = re.search(r'(?:qp|in)_(\d{2})', os.path.basename(file_path).lower())
                paper_no = int(match.group(1)) if match else -1
               
                return (year, session, paper_no)
            except Exception:
                return None

        def extract_egcse_metadata(file_path: str):
            if not ExamSchedulerUtils().is_eceswa_question_paper(file_path):
                return None
            
            try:
                parts = file_path.split(os.sep)
                year = int(parts[-2])
                match = re.search(r'Paper\s+(\d{1,2})', os.path.basename(file_path), re.IGNORECASE)
                paper_no = int(match.group(1)) if match else -1
                
                return (year, paper_no)
            except Exception:
                return None

        for root, _, files in os.walk(subject_path):
           
            csv_files = [
                os.path.join(root, f) for f in files if files and f.lower().endswith(".csv")
            ]
            
            paths_urls = LibUtils.get_paths_urls_from_csv(csv_file=csv_files[0]) if csv_files else {}
                        
            for file in files:
                
                full_path = os.path.join(root, file)
                
                if not file.lower().endswith(".pdf"):
                    continue
                    
                if EceswaGrade.IGCSE.value in subject_path:
                    key = extract_igcse_metadata(full_path)
                    if key and paths_urls:
                        if paths_urls.get('path') == full_path:
                            igcse_grouped[key].append(paths_urls)
                else:
                    key = extract_egcse_metadata(full_path)
                    if key and paths_urls:
                        if paths_urls.get('path') == full_path:
                            eceswa_grouped[key].append(paths_urls)

        final_result = []

        if EceswaGrade.IGCSE.value in subject_path:
            sorted_keys = sorted(igcse_grouped.keys(), key=lambda x: (-x[0], x[1], x[2]))
            for key in sorted_keys:
                final_result.append(sorted(igcse_grouped[key]))
        else:
            sorted_keys = sorted(eceswa_grouped.keys(), key=lambda x: (-x[0], x[1]))
            for key in sorted_keys:
                final_result.append(sorted(eceswa_grouped[key]))

        return final_result
