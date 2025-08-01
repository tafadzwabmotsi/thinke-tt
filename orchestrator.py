
import asyncio
import os
import time
from typing import List
from constants import BASE_PATH
from daily_schedule.schedule import Schedule
from data.students.student_data import StudentData
from data.students.student_data_reader import StudentDataReader
from data.students.student_data_writer import StudentDataWriter
from downloader.download_tools.downloader import PastPaperDownloader
from downloader.save_tools.saver import PastPaperSaver
from downloader.scraper_tools.criterion import PaperCount
from lib.colors import Colors 
from lib.grade import EceswaGrade, Grade
from lib.subject import EceswaEgcseSubject, Subject
from daily_schedule.messenger import WhatsAppMessenger
from lib.symbols import Symbols
from lib.typing.domain.student import StudentRecord
from lib.utils import LibUtils
from scheduler.exam_prep.assigner import ExamAssigner
from scheduler.exam_prep.scheduler import ExamScheduler
from ui.exam_scheduler_ui import ExamSchedulerUI
from ui.student_data_reader_ui import StudentDataReaderUI


# Global objects
students_data = StudentData(
    in_data_filename='tt_students_data.ods',
    out_data_filename='tt_daily_schedules_data.ods'
).get_students_data()

class Orchestrator:
    """
    Orchestrates the application's functionality.
    """
    
    @staticmethod
    def save_metadata():
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
                    StudentDataWriter(record).write_record()
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
        async def get_exam_schedule_input():
            
            # for grade in list(EceswaGrade):
            #     schedule_input_data = await ExamSchedulerUI(grade).run_async()
                
            #     print(schedule_input_data)    
            schedule_input_data = await ExamSchedulerUI(EceswaGrade.JC).run_async()
            print(schedule_input_data)
            
        asyncio.run(get_exam_schedule_input())
        
        
        return
        
        
        
        if students:
            for student in students: 
                scheduler = ExamScheduler(
                    student=student,
                    start_date='03-06-25',
                    end_date='30-09-25',
                    excluded_days=["Friday", "Saturday"]
                )
                
                # print(scheduler._generate_monthly_schedules())
                
                # exam_schedule = scheduler.generate_exam_schedule()
                
                # print(exam_schedule)
                print()
                print()
            
                # ExamAssigner(scheduler.generate_exam_schedule()).generate_pdf_schedule()
        
    @staticmethod
    def send_schedules():
        
        for student in students_data:  
            schedule = Schedule(student_data=student).generate_schedule_to_send()
            
            if not schedule:
                continue
            
            messenger = WhatsAppMessenger(schedule=schedule)
            messenger.send_msg()
            # schedule.assign_schedule()         
    