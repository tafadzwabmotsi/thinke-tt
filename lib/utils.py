from datetime import date, datetime, timedelta
        
from contextlib import contextmanager
from typing import Literal
from halo import Halo

class LibUtils:
    """
    A class that defines static library utility methods
    """

    @staticmethod
    def get_human_readable_date(date_str: str) -> str:
        """
        Converts a date string from 'dd-mm-yy' format to a more human-readable form like '22 July 2025'.

        Args:
            date_str (str): The date string in 'dd-mm-yy' format.

        Returns:
            str: A human-readable version of the date, e.g. '22 July 2025'.
        """
        try:
            dt = datetime.strptime(date_str, "%d-%m-%y")
            return dt.strftime("%d %B %Y")
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Expected 'dd-mm-yy'.")

    @contextmanager
    def spinner(
        start_text: str, 
        success_text: str = None, 
        fail_text: str = None, 
        frames_type: Literal["loading", "sending"] = "loading"
    ):
        """
        A context manager that wraps a block with a Halo spinner.
        
        Args:
            start_text (str): Spinner text shown during processing.
            success_text (str, optional): Message shown on success.
            fail_text (str, optional): Message shown on failure.
        """
        spinner = Halo(
            text=start_text,
            color="yellow",
            text_color="yellow",
            spinner={
                'interval': 100,
                'frames': [
                    r'[\]', r'[_]', r'[/]'
                ] if frames_type == "loading" else [
                    r'[=>]', r'[==>]', r'[===>]' 
                ]
             }
        )

        try:
            spinner.start()
            yield
            spinner.color = "green"
            spinner.text_color = "green"
            spinner.succeed(success_text or f"{start_text} - done")
        except Exception as e:
            spinner.color = "red"
            spinner.text_color = "red"
            spinner.fail(fail_text or f"{start_text} - failed")
            raise  # re-raise so upstream can catch
        finally:
            spinner.stop()
      
    @staticmethod
    def get_todays_date() -> str:
        """
        Returns today's date formatted as a string in the format 'DD-MM-YY'.

        Returns:
            str: Today's date, e.g. '30-07-25'.
        """
        return date.today().strftime("%d-%m-%y")

    @staticmethod
    def get_next_months_date() -> str:
        """
        Returns the date 30 days from today, formatted as 'DD-MM-YY'.

        This function internally uses `get_todays_date()` to get today's date
        and adds 30 days to compute the next month's date.

        Returns:
            str: A date string 30 days from today, in the format 'DD-MM-YY'.
        """
        start_date = LibUtils.get_todays_date()
        return (datetime.strptime(start_date, "%d-%m-%y") + timedelta(days=30)).strftime("%d-%m-%y")