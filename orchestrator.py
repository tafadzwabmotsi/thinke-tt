
import asyncio
import os
import time
from typing import Dict, List
from constants import BASE_PATH
from daily_schedule.messenger import WhatsAppMessenger
from data.schedules.exam_schedule_data_reader import ExamSchedulerDataReader
from data.schedules.exam_schedule_data_writer import ExamSchedulerDataWriter
from data.students.student_data_reader import StudentDataReader
from data.students.student_data_writer import StudentDataWriter
from data.subjects.past_paper_metadata_reader import PastPaperMetadataReader
from downloader.download_tools.downloader import PastPaperDownloader
from downloader.save_tools.saver import PastPaperSaver
from downloader.scraper_tools.criterion import PaperCount
from lib.colors import Colors 
from lib.exam_council import ExamCouncil
from lib.grade import CambridgeGrade, EceswaGrade, Grade
from lib.subject import Subject
from lib.symbols import Symbols
from lib.typing.data.schedule import ScheduleInputData
from lib.typing.domain.student import StudentRecord
from lib.utils import LibUtils
from scheduler.exam_prep.scheduler import ExamScheduler
from ui.exam_scheduler_ui import ExamSchedulerUI
from ui.student_data_reader_ui import StudentDataReaderUI


# Global objects

class Orchestrator:
    """
    Orchestrates the application's functionality.
    """
    
    @staticmethod
    def save_metadata():
        # TODO: Check if past paper metadata already exists and skill the process if for
        PastPaperSaver().save()
    
    @staticmethod
    def read_and_write_students_records():
        async def async_read_and_write_helper():
            student_records: List[StudentRecord] = []
            student_count = input(f"{Colors.GREEN} {Symbols.arrow} How many students do you want to add?: {Colors.RESET}")
            
            # Read student records
            for _ in range(int(student_count)):
                reader = StudentDataReaderUI()
                await reader.run_async()
                
                if reader.student_record:
                    student_records.append(reader.student_record)
            
            # Write student records
            for record in student_records:
                with LibUtils.spinner(
                    start_text=f"Saving record - {record.name}",
                    success_text=f"Successfully saved record - {record.name}"
                ):
                    StudentDataWriter().write_student_record(record)
                    time.sleep(0.5)
                    
        asyncio.run(async_read_and_write_helper())
    
    @staticmethod
    def read_and_write_schedule_input_data():
        async def async_read_and_write_helper():
            
            schedule_input_data: Dict[EceswaGrade, ScheduleInputData] = {}
            
            for grade in list(EceswaGrade):
                result = await ExamSchedulerUI(grade).run_async()
                
                if result:
                    schedule_input_data[grade] = result
            
            for grade, input_data in schedule_input_data.items():
                with LibUtils.spinner(
                    start_text=f"Saving exam preparation schedule input data - {grade.value}",
                    success_text=f"Successfully saved exam preparation schedule input data - {grade.value}"
                ):
                    ExamSchedulerDataWriter(input_data, grade).write()
                    time.sleep(0.5)
            
        asyncio.run(async_read_and_write_helper())         
    
    @staticmethod
    def download_past_papers(grade: Grade, subject: Subject, paper_count: PaperCount):
        downloader = PastPaperDownloader()
        downloader.download(
            grade=grade,
            subject=subject,
            paper_count=paper_count,
            download_path=os.path.join(BASE_PATH, 'Resources')
        )
    
    @staticmethod
    def generate_exam_preparation_schedules():
        
        for grade in EceswaGrade:
            students = StudentDataReader().get_all_students_by_grade(grade)
            writer = StudentDataWriter()
            input_data = ExamSchedulerDataReader(grade).get_schedule_input_data()
            student_data_reader = StudentDataReader()
            past_paper_readers = {
                grade.value: PastPaperMetadataReader(grade.value) 
                for grade in list(list(EceswaGrade) + list(CambridgeGrade))
            }
            
            for student in students:
                scheduler = ExamScheduler(
                        student=student, 
                        input_data=input_data,
                        student_data_reader=student_data_reader,
                        past_paper_readers=past_paper_readers
                    )

                if scheduler.student_has_complete_schedule():
                  print(f"{Colors.GREEN} {Symbols.circle} Exam preparation schedule already assigned - {student.name} {Colors.RESET}")
                  
                else:
                    scheduled_papers = scheduler.get_scheduled_papers_for_student()
                    with LibUtils.spinner(
                            start_text=f"Saving exam preparation schedule - {student.name}",
                            success_text=f"Successfully saved exam preparation schedule - {student.name}"
                        ):
                        for schedule_paper in scheduled_papers:
                            writer.write_exam_schedule_record(schedule_paper)
                    time.sleep(1)
        
    @staticmethod
    def send_schedules():
        
        for grade in EceswaGrade:
            reader = StudentDataReader()
            writer = StudentDataWriter()
            
            students = reader.get_all_students_by_grade(grade)
        
        
            for student in students:  
                schedule_records = reader.get_exam_schedule_records_by_student_id_and_day(
                    student.id,
                    '06-08-25'
                )
                
                for past_paper in schedule_records:  
                    if not past_paper:
                        continue
                    
                    msg = WhatsAppMessenger(phone=student.phone, past_paper=past_paper).send_msg()
                    print(msg)
                    time.sleep(1)