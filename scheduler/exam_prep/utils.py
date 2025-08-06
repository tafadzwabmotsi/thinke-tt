from pathlib import PurePosixPath
import re
from typing import Any, Dict, Optional

import fitz

from lib.exam_council import ExamCouncil
from lib.grade import EceswaGrade
from lib.subject import EceswaEgcseSubject, EceswaJcSubject


class ExamSchedulerUtils:
    """
    Utility class for exam scheduling logic, including subject-to-exam-council mappings
    and filename parsing for sorting past papers by year and session.

    This class provides static methods used during exam schedule generation to:
    - Retrieve prioritized and fallback exam councils based on grade and subject.
    - Parse past paper filenames to extract year and session information for sorting purposes.
    """
    
    @staticmethod
    def extract_cambridge_paper_label(url: str) -> str:
        filename = PurePosixPath(url).name
        match_paper = re.search(r'_qp_(\d{2})\.pdf', filename)
        match_insert = re.search(r'_in_(\d{2})\.pdf', filename)
        if match_paper:
            return f"Paper {int(match_paper.group(1)[0])}"
        
        if match_insert:
            return f"Paper {int(match_insert.group(1)[0])} - Insert"
        return "Paper No: Undefined"

    @staticmethod
    def extract_eceswa_paper_label(url: str) -> str:
        match = re.search(r'Paper\s*(\d+)', url, re.IGNORECASE)
        if match:
            return f"Paper {int(match.group(1))}"
        return "Paper No: Undefined"