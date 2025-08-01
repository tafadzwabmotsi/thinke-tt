
from typing import Any, Dict

from lib.utils import LibUtils

class WhatsAppMessenger:
    """
    Uses pywhatkit to send the day's scheduled past paper exam 
    to the given student
    """
    
    def __init__(self, schedule: Dict[str, Any]):
        self._schedule = schedule
    
    def send_msg(self) -> None:
        schedule = self._schedule
        
        phone = self._format_phone(schedule.get("phone"))
        name = schedule.get("name")
        day = schedule.get("day")
        attachments = schedule.get("attachments")

        if not phone or not attachments:
            print("Missing phone number or attachments.")
            return
    
        for attachment in attachments:
            message = self._build_attachment_message(day, attachment)
            print(f"\n◉ Sending exam preparation work [{LibUtils.get_human_readable_date(day)}] - {name}\n")

            try:
                # pywhatkit.sendwhatmsg_instantly(phone, message.strip(), wait_time=10, tab_close=True)
                print(message)
            except Exception as e:  
                print("Failed to send message:", str(e))
                
    def _format_phone(self, phone: int | str) -> str:
        """
        Ensures the phone is in international format (e.g. '+26812345678')
        """
        return str(phone) if str(phone).startswith('+') else f"+{str(phone)}"
    
    def _build_attachment_message(self, day: str, attachment: Dict[str, Any]) -> str:
        lines = [f"*{day}*\n"] if day else []

        for k in ["subject", "paper", "insert", "session", "code", "time_allowed"]:
            v = attachment.get(k)
            if v:
                lines.append(f"_{v}_")

    
        lines.append(f"\n📎 {attachment.get("url")}")

        return f'{"\n".join(lines)}\n'

    
        