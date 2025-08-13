from typing import Optional
from google.adk.tools.base_toolset import BaseToolset

class GreetingTools:
    
    def __init__(self):
        pass
     
    def say_hello(name: Optional[str] = None) -> str:
        """Provides a simple greeting. If a name is provided, it will be used.

        Args:
            name (str, optional): The name of the person to greet. Defaults to a generic greeting if not provided.

        Returns:
            str: A friendly greeting message.
        """
        if name:
            greeting = f"Hello, {name}!"
            print(f"--- Tool: say_hello called with name: {name} ---")
        else:
            greeting = "Hello there!" # Default greeting if name is None or not explicitly passed
            print(f"--- Tool: say_hello called without a specific name (name_arg_value: {name}) ---")
        return greeting

