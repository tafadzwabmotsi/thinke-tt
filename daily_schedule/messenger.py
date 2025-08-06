
import textwrap
from typing import Any, Dict, List

from lib.exam_council import ExamCouncil
from lib.grade import CambridgeGrade, EceswaGrade
from lib.symbols import Symbols
from lib.typing.domain.schedule import ScheduledPastPaperMetadata
from lib.typing.domain.student import Student, StudentRecord
from lib.utils import LibUtils

class WhatsAppMessenger:
    """
    Uses pywhatkit to send the day's scheduled past paper exam 
    to the given student
    """
    
    def __init__(self, phone: str, past_paper: ScheduledPastPaperMetadata):
        
        self._phone = phone
        self._past_paper = past_paper
        
    
    def send_msg(self) -> None:
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
            # pywhatkit.sendwhatmsg_instantly(phone, message.strip(), wait_time=10, tab_close=True)
            return msg
        except Exception as e:  
            print("Failed to send message:", str(e))
                
    def _get_formatted_phone(self) -> str:
        """
        Ensures the phone is in international format (e.g. '+26812345678')
        """
        return self._phone if self._phone.startswith('+') else f"+{self._phone}"
    
    def _get_exam_council(self) -> str:
        if self._past_paper.grade == CambridgeGrade.IGCSE.value:
            return ExamCouncil.CAMBRIDGE.value
        else:
            return ExamCouncil.ECESWA.value
    
        