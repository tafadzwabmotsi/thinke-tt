
import asyncio
import os
import time
from typing import Dict, List
from daily_schedule.messenger import Messenger
from data.schedules.exam_schedule_data_reader import ExamSchedulerDataReader
from data.schedules.exam_schedule_data_writer import ExamSchedulerDataWriter
from data.students.student_data_reader import StudentDataReader
from data.students.student_data_writer import StudentDataWriter
from downloader.download_tools.downloader import PastPaperDownloader
from downloader.save_tools.saver import PastPaperSaver
from downloader.scraper_tools.criterion import PaperCount
from lib.colors import Colors 
from lib.constants import BASE_DIR
from lib.grade import EceswaGrade, Grade
from lib.subject import Subject
from lib.symbols import Symbols
from lib.typing.data.schedule import ScheduleInputData
from lib.typing.domain.student import Student, StudentRecord
from lib.utils import LibUtils
from scheduler.exam_prep.schedule_generator import ScheduleGenerator
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
                    start_text=f"Saving exam schedule input data - {grade.value}",
                    success_text=f"Successfully saved exam schedule input data - {grade.value}"
                ):
                    ExamSchedulerDataWriter(input_data, grade).write_schedule_input_data()
                    time.sleep(0.5)
            
        asyncio.run(async_read_and_write_helper())         
    
    @staticmethod
    def download_past_papers(grade: Grade, subject: Subject, paper_count: PaperCount):
        PastPaperDownloader().download(
            grade=grade,
            subject=subject,
            paper_count=paper_count,
            download_path=os.path.join(BASE_DIR, 'Resources')
        )
    
    @staticmethod
    def generate_exam_preparation_schedules():
        
        def create_schedule_helper(scheduler: ExamScheduler, student: Student) -> None:
            # Create schedule if not already created                
            if not scheduler.has_complete_schedule():  
                scheduled_papers = scheduler.get_new_scheduled_papers_for_student()
                
                with LibUtils.spinner(
                        start_text=f"Writing schedule to database - {student.name}",
                        success_text=f"Successfully written schedule to database - {student.name}"
                    ):
                    for schedule_paper in scheduled_papers:
                        student_writer.write_exam_schedule_record(schedule_paper)
                            
        def download_papers_write_metadata_helper(grade: EceswaGrade, scheduler: ExamScheduler, student: Student) -> None:
            schedule_writer = ExamSchedulerDataWriter(grade)
            if not scheduler.schedule_written_to_database() or not scheduler.papers_exist_in_src_dir(): 
                with LibUtils.progress_bar(
                    tasks=scheduler.get_exam_schedule_papers(),
                    desc_text=f"{Symbols.arrow} Downloading missing papers - {student.name}",
                    unit="file"
                ) as progress:
                    for p in progress:  
                        if PastPaperDownloader().download_pure(p.paper_metadata.url, p.src_path):
                            schedule_writer.write_downloaded_paper_metadata_record(p.paper_metadata)
                            time.sleep(0.2) 
                                
        def copy_schedule_helper(scheduler: ExamScheduler, student: Student, generator: ScheduleGenerator) -> None:
            if not scheduler.schedule_copied_to_output_dir() and scheduler.papers_exist_in_src_dir(): 
                with LibUtils.spinner(
                    start_text=f"Copying schedule to output directory - {student.name}",
                    success_text=f"Successfully copied schedule - {student.name}"
                ):    
                    generator.save_schedule_to_disk()
        
        def generate_pdf(scheduler: ExamScheduler, student: Student, generator: ScheduleGenerator) -> None:
            if not scheduler.schedule_pdf_generated():
                with LibUtils.spinner(
                    start_text=f"Generating PDF file for schedule - {student.name}",
                    success_text=f"Successfully generated PDF file - {student.name}"
                ):
                    generator.generate_pdf_schedule()
                    time.sleep(0.5)
                
        for grade in EceswaGrade:
            students = StudentDataReader().get_students_by_grade(grade)
            
            if not students:
                print(f"{Symbols.arrow} No {grade.value} students were found in the database")
                continue
                
            student_writer = StudentDataWriter()
            
            for student in students:
                scheduler = ExamScheduler(student)
           
                create_schedule_helper(scheduler, student)
                download_papers_write_metadata_helper(grade, scheduler, student)
                
                generator = ScheduleGenerator(scheduler.get_schedule())
                copy_schedule_helper(scheduler, student, generator)
                generate_pdf(scheduler, student, generator)
        
    @staticmethod
    def send_schedules():
        
        for grade in EceswaGrade:
            reader = StudentDataReader()
            writer = StudentDataWriter()
            
            students = reader.get_students_by_grade(grade)
        
            for student in students:
                day = '12-08-25'
                id = student.id
                
                schedule_records = ExamScheduler(student).get_scheduled_records_by_day(day)
                readable_day = LibUtils.get_human_readable_date(day)
                
                # if reader.msgs_for_id_and_day_exist(id, day):
                #     print(f"{Colors.GREEN} {Symbols.circle} Schedule [{readable_day}] already sent - {student.name} {Colors.RESET}")
                #     continue
                
                
                for past_paper in schedule_records:  
                    if not past_paper:
                        continue
                    
                    messenger = Messenger(student=student, past_paper=past_paper)
                    msg = messenger.send_whatsapp_msg()
                    
                    if msg:
                        pass
            
                
                # with LibUtils.spinner(
                #         start_text=f"Sending schedule [{readable_day}] - {student.name}",
                #         success_text=f"Successfully sent schedule [{readable_day}] - {student.name}"
                #     ):  
                #     for past_paper in schedule_records:  
                #         if not past_paper:
                #             continue
                       
                #         messenger = Messenger(student=student, past_paper=past_paper)
                #         msg = messenger.send_whatsapp_msg()
                        
                #         if msg:
                #             pass
                #             # print(msg)
                #             # print()
                #             # writer.write_msg_record(msg)
                        
                #         time.sleep(1)