
import textwrap
from typing import Any, Dict, List, Optional

from lib.exam_council import ExamCouncil
from lib.grade import CambridgeGrade, EceswaGrade
from lib.symbols import Symbols
from lib.typing.domain.schedule import MsgRecord, ScheduledPastPaperMetadata
from lib.typing.domain.student import Student, StudentRecord
from lib.utils import LibUtils

class Messenger:
    """
    Uses pywhatkit to send the day's scheduled past paper exam 
    to the given student
    """
    
    def __init__(self, student: Student, past_paper: ScheduledPastPaperMetadata):
        
        self._student = student
        self._past_paper = past_paper
        
    
    def send_whatsapp_msg(self) -> Optional[MsgRecord]:
        p = self._past_paper
        
        day =  LibUtils.get_human_readable_date(p.date)
        exam_council = self._get_exam_council()
        subject = f'{p.subject} {p.paper}'
        session = f'{p.session} {p.year}'
        url = p.url
        
        phone = self._get_formatted_phone()
        
        msg = textwrap.dedent(f"""\
            *{day}*

            _{exam_council}_
            _{subject}_
            _{session}_

            {Symbols.attachment} {url}
            """
        )
     
        try:
            print(self._student.name)
            print(msg)
            # pywhatkit.sendwhatmsg_instantly(phone, message.strip(), wait_time=10, tab_close=True)
            return MsgRecord(
                student_id=self._student.id,
                date=LibUtils.get_machine_readable_date(day),
                exam_council=exam_council,
                subject=subject,
                session=session,
                attached_url=url
            )
        except Exception as e:  
            print("Failed to send message:", str(e))
            return None
                
    def _get_formatted_phone(self) -> str:
        """
        Ensures the phone is in international format (e.g. '+26812345678')
        """
        phone = self._student.phone
        
        return phone if phone.startswith('+') else f"+268{phone}"
    
    def _get_exam_council(self) -> str:
        if self._past_paper.grade == CambridgeGrade.IGCSE.value:
            return ExamCouncil.CAMBRIDGE.value
        else:
            return ExamCouncil.ECESWA.value
    
        