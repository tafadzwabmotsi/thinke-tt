import os
from dotenv import load_dotenv
from data.students.student_data_reader import StudentDataReader
from lib.grade import EceswaGrade
from lib.subject import EceswaJcSubject
from orchestrator import Orchestrator
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from pydantic import BaseModel
import asyncio

from scheduler.exam_prep.scheduler import ExamScheduler

# Load environment variables from .env
load_dotenv()


# Set LiteLLM's key for Gemini


if __name__ == "__main__":

    # for paper in schedule:
        
    
    # papers = scheduler._get_next_eceswa_unassigned_paper(subject, grade.value)
    
    # print("---- Papers ----")
    # print(papers)
    # print("---------------")
    # print()
    
    
    # print("---- Assigned Papers ----")
    # assigned_papers = scheduler._load_assigned_paper_urls()
    # for p in assigned_papers:
    #     if subject in p:
    #         print(p)
    
    
    _ = Orchestrator()
    # _.save_metadata()
    # _.read_and_write_students_records()
    # _.read_and_write_schedule_input_data()
    _.generate_exam_preparation_schedules()
    # _.send_schedules()        


   
    
    
    
    
    



    