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
    def get_subject_exam_councils(grade: str, subject: str) -> Optional[Dict[str, Any]]:
        """
        Returns metadata for a specific subject under a given grade, including the
        prioritized and fallback exam councils.

        Args:
            grade (str): The grade level, e.g., "JC" or "EGCSE".
            subject (str): The subject name or code (as a string) for the given grade.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with:
                - 'title': The enum subject object.
                - 'prioritized_exam_councils': A list of exam councils (by priority).
                - 'fallback_exam_council': The default exam council if others are unavailable.
            Returns None if the subject or grade is not found.
        """
        
        data = {
            EceswaGrade.JC: {
                EceswaJcSubject.ADD_MATHS.value.strip().lower(): {
                    'title': EceswaJcSubject.ADD_MATHS,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.AGRICULTURE.value.strip().lower(): {
                    'title': EceswaJcSubject.AGRICULTURE,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.BOOKKEEPING.value.strip().lower(): {
                    'title': EceswaJcSubject.BOOKKEEPING,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.BUSINESS_STUDIES.value.strip().lower(): {
                    'title': EceswaJcSubject.BUSINESS_STUDIES,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.CONSUMER_SCIENCE.value.strip().lower(): {
                    'title': EceswaJcSubject.CONSUMER_SCIENCE,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.DESIGN_AND_TECHNOLOGY.value.strip().lower(): {
                    'title': EceswaJcSubject.DESIGN_AND_TECHNOLOGY,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.DEVELOPMENT_STUDIES.value.strip().lower(): {
                    'title': EceswaJcSubject.DEVELOPMENT_STUDIES,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.ENGLISH.value.strip().lower(): {
                    'title': EceswaJcSubject.ENGLISH,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.ENGLISH_LITERATURE.value.strip().lower(): {
                    'title': EceswaJcSubject.ENGLISH_LITERATURE,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.FRENCH.value.strip().lower(): {
                    'title': EceswaJcSubject.FRENCH,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.GEOGRAPHY.value.strip().lower(): {
                    'title': EceswaJcSubject.GEOGRAPHY,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.HISTORY.value.strip().lower(): {
                    'title': EceswaJcSubject.HISTORY,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.MATHEMATICS.value.strip().lower(): {
                    'title': EceswaJcSubject.MATHEMATICS,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.RELIGIOUS_EDUCATION.value.strip().lower(): {
                    'title': EceswaJcSubject.RELIGIOUS_EDUCATION,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.SCIENCE.value.strip().lower(): {
                    'title': EceswaJcSubject.SCIENCE,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaJcSubject.SISWATI.value.strip().lower(): {
                    'title': EceswaJcSubject.SISWATI,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
            },
            EceswaGrade.EGCSE: {
                EceswaEgcseSubject.ACCOUNTING.value.strip().lower(): {
                    'title': EceswaEgcseSubject.ACCOUNTING,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.AGRICULTURE.value.strip().lower(): {
                    'title': EceswaEgcseSubject.AGRICULTURE,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.BIOLOGY.value.strip().lower(): {
                    'title': EceswaEgcseSubject.BIOLOGY,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.BUSINESS_STUDIES.value.strip().lower(): {
                    'title': EceswaEgcseSubject.BUSINESS_STUDIES,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.DESIGN_AND_TECHNOLOGY.value.strip().lower(): {
                    'title': EceswaEgcseSubject.DESIGN_AND_TECHNOLOGY,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.ECONOMICS.value.strip().lower(): {
                    'title': EceswaEgcseSubject.ECONOMICS,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.ENGLISH.value.strip().lower(): {
                    'title': EceswaEgcseSubject.ENGLISH,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.FASHION_AND_FABRICS.value.strip().lower(): {
                    'title': EceswaEgcseSubject.FASHION_AND_FABRICS,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaEgcseSubject.FIRST_SISWATI.value.strip().lower(): {
                    'title': EceswaEgcseSubject.FIRST_SISWATI,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
                EceswaEgcseSubject.FOOD_AND_NUTRITION.value.strip().lower(): {
                    'title': EceswaEgcseSubject.FOOD_AND_NUTRITION,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.GEOGRAPHY.value.strip().lower(): {
                    'title': EceswaEgcseSubject.GEOGRAPHY,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.HISTORY.value.strip().lower(): {
                    'title': EceswaEgcseSubject.HISTORY,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.LITERATURE.value.strip().lower(): {
                    'title': EceswaEgcseSubject.LITERATURE,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.MATHEMATICS.value.strip().lower(): {
                    'title': EceswaEgcseSubject.MATHEMATICS,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.PHYSICAL_SCIENCE.value.strip().lower(): {
                    'title': EceswaEgcseSubject.PHYSICAL_SCIENCE,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.RELIGIOUS_EDUCATION.value.strip().lower(): {
                    'title': EceswaEgcseSubject.RELIGIOUS_EDUCATION,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA, ExamCouncil.CAMBRIDGE],
                    'fallback_exam_council': ExamCouncil.CAMBRIDGE
                },
                EceswaEgcseSubject.SECOND_SISWATI.value.strip().lower(): {
                    'title': EceswaEgcseSubject.SECOND_SISWATI,
                    'prioritized_exam_councils': [ExamCouncil.ECESWA],
                    'fallback_exam_council': ExamCouncil.ECESWA
                },
            }
        }

        return data.get(EceswaGrade(grade), {}).get(subject.strip().lower())

    @staticmethod
    def parse_filename_for_sorting(filename: str) -> Optional[Dict[str, Any]]:
        """
        Parses a past paper filename to extract the exam year and session,
        which can be used to sort papers chronologically and by session priority.

        Example filename format:
            'Mathematics-Paper_1_Core-May_June_2019-0980_12-1_hour.pdf'

        Args:
            filename (str): The filename of the exam paper.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with:
                - 'year' (int): The year of the exam (e.g., 2019).
                - 'session_sort_key' (int): A numeric value for sorting session priority.
                  Higher values represent later sessions (e.g., October/November > May/June).
            Returns None if the filename doesn't match the expected format.
        """
        
        pattern = re.compile(r'([A-Za-z]+)_([A-Za-z]+)_(\d{4})-.*\.pdf$', re.IGNORECASE)
        session_sort_map = {
            ('october', 'november'): 2,
            ('may', 'june'): 1,
        }

        match = pattern.search(filename)
        if not match:
            return None

        month1, month2, year_str = match.groups()
        try:
            year = int(year_str)
            session_key = session_sort_map.get((month1.lower(), month2.lower()), 0)
            return {'year': year, 'session_sort_key': session_key}
        except (ValueError, TypeError):
            return None
    
    @staticmethod    
    def is_eceswa_question_paper(file_path: str) -> bool:
        """
        Checks if a given ECESWA PDF is a question paper based on the presence of mandatory
        uppercase markers like CANDIDATE, NAME, CENTRE, NUMBER in the first page.

        Args:
            file_path (str): Full path to the PDF file.

        Returns:
            bool: True if it is a question paper; False if it's likely examiner notes or admin content.
        """
        required_keywords = {"CANDIDATE", "NAME", "CENTRE", "NUMBER"}

        try:
            with fitz.open(file_path) as doc:
                if doc.page_count == 0:
                    return False
                text = doc[0].get_text("text")
                lines = [line.strip().upper() for line in text.split("\n") if line.strip()]
                line_set = set(lines)
                return required_keywords.issubset(line_set)
        except Exception as e:
            return False
