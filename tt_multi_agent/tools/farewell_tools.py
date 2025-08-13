from typing import Optional

from google.adk.tools.base_toolset import BaseToolset


class FarewellTools:
    
    def __init__(self):
        pass

    def say_goodbye(self) -> str:
        """Provides a simple farewell message to conclude the conversation."""
        print(f"--- Tool: say_goodbye called ---")
        return "Goodbye! Have a great day."