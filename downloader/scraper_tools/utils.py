
import calendar
from datetime import datetime
import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

import requests

class ScraperToolsUtils:
    """
    Defines static methods that can be used as utilities in scraper tools.
    """
    @staticmethod
    def get_year_regex():
        """
        Returns a compiled regex pattern that matches years from 2000 to 2030.
        """
        return re.compile(r'\b(20[0-2][0-9]|2030)\b')

    @staticmethod
    def get_month_regex():
        """
        Returns a compiled regex pattern that matches both full and abbreviated month names.
        Matches are case-insensitive.
        """
        return re.compile(
            r'(?:January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|'
            r'July|Jul|August|Aug|September|Sep|October|Oct|November|Nov|December|Dec)',
            re.IGNORECASE
        )
        
    
    @staticmethod
    def get_full_month_name(month_input: str) -> Optional[str]:
        """
        Converts a month input (either abbreviation or full name) to a standardized full month name.

        Args:
            month_input (str): The month name string (e.g., 'nov', 'march', 'JUN').

        Returns:
            Optional[str]: The capitalized full month name (e.g., 'November', 'March', 'June'),
                            or None if the input does not match a known month.
        """
        month_map = {
            "jan": "January", "january": "January",
            "feb": "February", "february": "February",
            "mar": "March", "march": "March",
            "apr": "April", "april": "April",
            "may": "May",
            "jun": "June", "june": "June",
            "jul": "July", "july": "July",
            "aug": "August", "august": "August",
            "sep": "September", "september": "September",
            "oct": "October", "october": "October",
            "nov": "November", "november": "November",
            "dec": "December", "december": "December"
        }
        return month_map.get(month_input.lower())

    @staticmethod
    def get_month_num(month_str: str) -> int:
        """
        Maps a three-character month abbreviation or full month name to its numerical representation (1-12)
        for sorting purposes.
        """
        month_to_num = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
        month_to_num.update({abbr.lower(): i for i, abbr in enumerate(calendar.month_abbr) if abbr})
        
        return month_to_num.get(month_str.lower(), 0)
    
    def get_session_years() -> dict[int, int]:
        """
        Returns a dictionary where keys are the past 25 years (excluding the current year),
        and values are their distance from the current year.

        Example (if current year is 2025):
        {
            2024: 1,
            2023: 2,
            ...
            2000: 25
        }
        """ 
        return {datetime.now().year - i: i for i in range(1, 27)}
    
    def get_session_months() -> dict[str, int]:
        """
        Returns a dictionary mapping full month names to their numerical order (1-based),
        skipping empty strings (like the first element in calendar.month_name).

        Example:
        {
            'January': 1,
            'February': 2,
            ...
            'December': 12
        }
        """
        return {month: i for i, month in enumerate(calendar.month_name) if month}
    
    @staticmethod
    def resolve_redirected_pdf_url(view_php_url: str, base_url: str) -> Optional[str]:
        """
        Resolves a 'view.php' style URL to the direct .pdf file path without making a request.
        
        Args:
            view_php_url (str): The full URL pointing to the 'view.php?id=...' pattern.
            base_url (str): The base URL from which PDF files will be downloaded.
            
        Returns:
            Optional[str]: The resolved absolute .pdf URL, or None if it cannot be resolved.
        """
        try:
            parsed = urlparse(view_php_url)
            query = parse_qs(parsed.query)
            path = query.get("id", [None])[0]
            
            if path and path.lower().endswith(".pdf"):
                return f"{base_url}/{path.lstrip('/')}"
            return None
        except Exception:
            return None



