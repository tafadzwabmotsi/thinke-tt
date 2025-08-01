import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any

from lib.exam_council import ExamCouncil
from lib.grade import EceswaGrade
from lib.typing.data.schedule import DayOfWeek
from lib.typing.domain.student import Student, StudentRecord
from lib.utils import LibUtils
from scheduler.exam_prep.utils import ExamSchedulerUtils


class ExamScheduler:
    """
    A class to generate and manage exam preparation schedules for students.

    Once initialized with the student information, subjects, exam preferences, and scheduling
    details, the class generates a day-by-day schedule for practicing past exam papers.

    Args:
        student_data: (Dict[str, Any]) The object that carries student data
        read_base_path (str): Root directory where past paper resources are stored.
        write_base_path (str): Root directory where generated schedules will be saved.
    """

    def __init__(
        self,
        student: Student,
        start_date: str,
        end_date: str,
        excluded_days: List[DayOfWeek]
    ):
        self._student = student
        self._start_date = start_date
        self._end_date = end_date
        self._excluded_days = excluded_days
        
        print(student)
        
        self._read_base_path = None # TODO: Incorporate a way to internalize file paths

        self._exam_schedule: Dict[str, Any] = {}

    def _generate_monthly_schedules(self) -> List[Dict]:
        """Generate valid monthly schedule blocks between start and end dates, excluding specified weekdays."""
        start_date = datetime.strptime(self._start_date, "%d-%m-%y")
        end_date = datetime.strptime(self._end_date, "%d-%m-%y")

        delta = timedelta(days=1)
        current = start_date
        monthly_schedules: Dict[str, Dict] = {}

        while current <= end_date:
            weekday_name = current.strftime('%A')
            if weekday_name not in self._excluded_days:
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
