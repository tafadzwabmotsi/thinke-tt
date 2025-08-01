from collections import OrderedDict
from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pyexcel_ods3 import get_data, save_data

from extractor.past_paper_extractor import PastPaperExtractor
from extractor.utils import PastPaperExtractorUtils
from lib.exam_council import ExamCouncil
from lib.grade import EceswaGrade
from lib.subject import EceswaEgcseSubject, EceswaEpcSubject, EceswaJcSubject, SaveMyExamsIgcseSubjects
from lib.utils import LibUtils


class Schedule:
    """
    A class that generates student daily schedule that will be sent to students
    """
    
    def __init__(self, student_data: Dict[str, Any]):
        self._student_data = student_data
        self._today = datetime.today()
    
    def generate_schedule_to_send(self):
        student = self._student_data
        
        id = student['id']
        name = student['name']
        grade = student['grade']
        phone = student['phone']
        subjects = student['subjects']
        
        scheduled_papers = self._get_papers_to_send()
       
        
        if not scheduled_papers:
            print(f"◉ No scheduled papers on {LibUtils.get_human_readable_date(self._today.strftime('%d-%m-%y'))} - {name}")
            return {}
        
        day = scheduled_papers['day']
        papers = scheduled_papers['papers']
        exam_council = scheduled_papers['exam_council']
        
        # Construct a msg object
        msg = {}
        if not day in student['daily_schedules']:
            attachments = []
            for paper in papers:
                for file in paper['files']:
                    
                    path = file['path']
                    url = file['url']
                    
                    metadata = self._get_past_past_metadata(
                        exam_council=exam_council, 
                        pdf_file_path=path,
                        grade=EceswaGrade(grade)
                    )
                    
                    # Populate the msg object
                    if metadata:
                        attachments.append({
                            'url': url, **{
                            k: PastPaperExtractorUtils.restore_part(v)
                                for k, v in {**metadata}.items()
                            }
                        })
                    else:
                        attachments.append({
                            'subject': paper['subject'], 
                            'url': url
                        })  
            msg['name'] = name
            msg['phone'] = phone
            msg['day'] = day
            msg['attachments'] = attachments
            
        return msg

    def assign_schedule(self) -> None:
        """
        Assigns a schedule to a student for a given day without wiping other sheets.
        """

        day = self._today.strftime('%d-%m-%y')
        student_id = self._student_data['id']
        
        # Load the entire spreadsheet first
        full_data = get_data(self._data_file_path)

        # Get the schedule data or initialize it
        schedules = full_data.get(self.DAILY_SCHEDULES, [])
        found = False

        for row in schedules:
            if row and row[0] == student_id:
                found = True
                if day not in row:
                    row.append(day)
                break

        if not found:
            schedules.append([student_id, day])

        # Update only the DAILY_SCHEDULES sheet in the full data
        full_data[self.DAILY_SCHEDULES] = schedules

        # Save everything back to preserve all sheets
        save_data(self._data_file_path, full_data)

    def _get_papers_to_send(self) -> Optional[Dict]:
        """
        Returns today's scheduled PDF papers for a given student, along with their metadata.

        Assumes each subject folder contains exactly one exam council subfolder, and PDFs
        are stored within or under that exam council folder. Also assumes the same exam
        council is used for all subjects that day.

        The returned dictionary includes:
            - name: The full name of the student
            - grade: The academic level of the student
            - day: Today's date in "dd-mm-yy" format
            - exam_council: Name of the exam council used
            - papers: A list of dictionaries, each like:
                {
                    "subject": <subject name>,
                    "files": [<full path to PDF 1>, <PDF 2>, ...]
                }

        Args:
            student_grade (str): The academic level of the student.
            student_name (str): The full name of the student.

        Returns:
            Optional[Dict]: The structured scheduled data, or None if no PDFs found.
        """
        today = self._today
        year_str = str(today.year)
        month_str = today.strftime('%B')
        day_str = today.strftime('%d-%m-%y')

        student_path = os.path.join(
            self._student_data['base_path'],
            year_str,
            month_str,
            day_str
        )

        if not os.path.exists(student_path):
            return None
        
        papers = []
        exam_council = None
      
        for subject_name in os.listdir(student_path):
            subject_path = os.path.join(student_path, subject_name)
            if not os.path.isdir(subject_path):
                continue

            # Expect exactly one exam council folder
            sub_folders = [f for f in os.listdir(subject_path)
                        if os.path.isdir(os.path.join(subject_path, f))]
            if len(sub_folders) != 1:
                continue

            current_exam_council = sub_folders[0]
            if exam_council is None:
                exam_council = current_exam_council
            elif exam_council != current_exam_council:
                # Optional: Raise or skip if inconsistent council across subjects
                continue  # or raise ValueError("Inconsistent exam council across subjects.")

            exam_council_path = os.path.join(subject_path, current_exam_council)

            # Recursively gather all the paths and urls of PDF from the .csv file
            pdf_paths_urls = [
                LibUtils.get_paths_urls_from_csv(csv_file=os.path.join(root, file))
                for root, _, files in os.walk(exam_council_path)
                for file in files if file.lower().endswith('.csv')
            ]

            if pdf_paths_urls:
                papers.append({
                    "subject": subject_name,
                    "files": pdf_paths_urls
                })
        if not papers:
            return None

        return {
            "day": day_str,
            "exam_council": ExamCouncil(exam_council.upper()),
            "papers": papers
        }

    def _get_past_past_metadata(self, pdf_file_path: str, exam_council: ExamCouncil, grade: EceswaGrade) -> Dict[str, str]:
        if not Path(pdf_file_path).with_suffix('.pdf').resolve().exists():
            print("✗ Paper's metadata not extracted - Path not found")
            return
        
        match exam_council:
            case ExamCouncil.CAMBRIDGE:
                return PastPaperExtractor.extract_igcse_past_paper_metadata(
                    pdf_path=pdf_file_path,
                    subjects_enum=SaveMyExamsIgcseSubjects
                ) 
            case ExamCouncil.ECESWA:
                subjects_enum = EceswaEgcseSubject
                match grade:
                    case EceswaGrade.EGCSE:
                        subjects_enum = EceswaEgcseSubject
                    case EceswaGrade.JC:
                        subjects_enum = EceswaJcSubject
                    case EceswaGrade.EPC:
                        subjects_enum = EceswaEpcSubject
                return PastPaperExtractor.extract_eceswa_past_paper_metadata(
                    pdf_path=pdf_file_path,
                    subjects_enum=subjects_enum
                )
            