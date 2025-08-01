from collections import OrderedDict, defaultdict
import os
from pathlib import Path
from pyexcel_ods3 import get_data, save_data

from constants import BASE_PATH
from lib.exam_council import ExamCouncil
from lib.grade import EceswaGrade
from lib.subject import EceswaEgcseSubject as EgcseSubject, EceswaJcSubject as JcSubject

class StudentData:
    
    # Sheet names
    STUDENTS = 'students'
    SUBJECTS = 'subjects'
    GRADES = 'grades'
    EGCSE_SUBJECTS = 'egcse_subjects'
    EPC_SUBJECTS = 'epc_subjects'
    JC_SUBJECTS = 'jc_subjects'
    DAILY_SCHEDULES = 'daily_schedules'
    EXAM_COUNCILS = 'exam_councils'
    EGCSE_SUBJECTS_PRIORITIZED_EXAM_COUNCILS = 'egcse_subjects_prioritized_exam_councils'
    EGCSE_SUBJECTS_FALLBACK_EXAM_COUNCIL = 'egcse_subjects_fallback_exam_council'
    JC_SUBJECTS_PRIORITIZED_EXAM_COUNCILS = 'jc_subjects_prioritized_exam_councils'
    JC_SUBJECTS_FALLBACK_EXAM_COUNCIL = 'jc_subjects_fallback_exam_council'
    DATES_RANGE = 'dates_range'
    EXCLUDED_DAYS = 'excluded_days'

    def __init__(self,  in_data_filename: str, out_data_filename: str):
       
        self._in_data_file_path = os.path.join(
            BASE_PATH,
            'Input',
            in_data_filename
        )
        self._out_data_file_path = os.path.join(
            BASE_PATH,
            'Input',
            out_data_filename
        )
        
        
        # If out data file is not there, then create it, initializing it 
        # the daily schedules data object to an empty dict
        if not Path(self._out_data_file_path).exists():
            save_data(self._out_data_file_path, OrderedDict({self.DAILY_SCHEDULES: []}))
            
        # Otherwise read in the daily schedules
        self._students_daily_schedules_data = {
            sheet: [row for row in rows if any(cell for cell in row)]
            for sheet, rows in get_data(self._out_data_file_path).items()
        }
        
        # Initialize students data
        self._students_data = {
            sheet: [row for row in rows if any(cell for cell in row)]
            for sheet, rows in get_data(self._in_data_file_path).items()
        }
    
    def get_out_data_file_path(self) -> str:
        return self._out_data_file_path
    
    def get_students_daily_schedules(self):
        print(self._students_daily_schedules_data)
            
    def get_students_data(self):
        
        data = self._students_data | self._students_daily_schedules_data
        
        # Build student base records from the main `students` sheet
        students = {
            row[0]: {
                "id": row[0],
                "name": row[1],
                "phone": row[2],
                "grade": EceswaGrade(row[3])
            }
            for row in data.get(self.STUDENTS, []) if row and isinstance(row[0], int)
        }

        # Iterate through other sheets and enrich student data
        for sheet_name, rows in data.items():
            if sheet_name in {self.STUDENTS}:
                continue

            for row in rows:
                if not row or not isinstance(row[0], int):
                    continue
                student_id, *values = row
                if student_id not in students:
                    continue
                student = students[student_id]

                if sheet_name == self.DATES_RANGE:
                    student['start_date'] = values[0] if len(values) > 0 else ''
                    student['end_date'] = values[1] if len(values) > 1 else ''
                    
                elif sheet_name == self.SUBJECTS:
                    # Normalize and enrich subject objects
                    raw_subjects = values
                    student_grade = student["grade"]
                    subject_meta = self._normalize_subject_metadata(data, student_grade)
                    enriched_subjects = []
                    for s in raw_subjects:
                        meta = subject_meta.get(s, {})
                        enriched_subjects.append({
                            'title': EgcseSubject(s) if student_grade == EceswaGrade.EGCSE else JcSubject(s),
                            'prioritized_exam_councils': meta.get('prioritized_exam_councils', []),
                            'fallback_exam_council': meta.get('fallback_exam_council', '')
                        })
                    student['subjects'] = enriched_subjects
                else:
                    # For all other sheets, just attach them as list of values
                    student[sheet_name] = values
                student['out_data'] = {
                    'path': self._out_data_file_path,
                    'sheet_name': self.DAILY_SCHEDULES
                }
                student['base_path'] = os.path.join(
                    BASE_PATH,
                    'Output',
                    student['grade'].value,
                    student['name']
                )
            
        # Return cleaned/enriched values
        return list(students.values())

    def _normalize_subject_metadata(self, data, grade: EceswaGrade):
        """
        Builds a mapping:
            subject title -> {
                prioritized_exam_councils: [...],
                fallback_exam_council: ...
            }
        """
        grade_key = grade.value.strip().lower()
        prioritized_key = f"{grade_key}_subjects_prioritized_exam_councils"
        fallback_key = f"{grade_key}_subjects_fallback_exam_council"

        prioritized = defaultdict(list)
        fallback = {}

        # Process prioritized
        for row in data.get(prioritized_key, []):
            if row and isinstance(row[0], str):
                subject = row[0].strip()
                councils = [ExamCouncil(c.strip()) for c in row[1:] if isinstance(c, str)]
                prioritized[subject] = councils

        # Process fallback
        for row in data.get(fallback_key, []):
            if row and isinstance(row[0], str):
                subject = row[0].strip()
                if len(row) > 1 and isinstance(row[1], str):
                    fallback[subject] = ExamCouncil(row[1].strip())

        # Combine
        subject_metadata = {}
        all_subjects = set(prioritized.keys()) | set(fallback.keys())
        for subject in all_subjects:
            subject_metadata[subject] = {
                'prioritized_exam_councils': prioritized.get(subject, []),
                'fallback_exam_council': fallback.get(subject, '')
            }

        return subject_metadata

    