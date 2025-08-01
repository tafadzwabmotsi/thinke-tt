from enum import Enum
import os
import re
from typing import Dict

import fitz
from extractor.utils import PastPaperExtractorUtils as Utils


class PastPaperExtractor:
    """
    Class that extracts info from PDF past papers
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans a string extracted from a PDF by removing non-printable characters 
        and normalizing whitespace.

        This method is especially useful for preparing text extracted from 
        scanned or OCR-processed PDFs to ensure consistency in matching and 
        string comparison. It removes characters such as backspaces or form feeds, 
        and converts all consecutive whitespace characters (spaces, tabs, etc.) 
        into a single space.

        Args:
            text (str): The raw string to clean.

        Returns:
            str: The cleaned string with non-printable characters removed and
                consistent whitespace formatting.
        """
        if not text:
            return ''
        text = re.sub(r'[^\x20-\x7E]', '', text)  # Remove non-printables
        text = re.sub(r'\s+', ' ', text)          # Normalize spaces
        return text.strip()

    @staticmethod
    def extract_igcse_past_paper_metadata(pdf_path: str, subjects_enum: Enum) -> Dict[str, str]:
        """
        Extracts metadata from the cover page of a Cambridge IGCSE past paper PDF.

        The metadata fields include:
            - subject: Identified from known local subject names in the given enum.
            - paper: e.g., "Paper 1", "Paper 2 Extended", etc.
            - insert: Set if the paper contains the word "INSERT".
            - session: The examination date, e.g., "June 2022".
            - code: The paper code, e.g., "0450/12".
            - time_allowed: e.g., "1 hour 30 minutes".

        This method processes only the first page of the PDF and uses both pattern
        matching and string normalization to extract these fields.

        Args:
            pdf_path (str): The full path to the IGCSE past paper PDF file.
            subjects_enum (Enum): An enumeration of subjects with a `local_name` attribute
                                used to identify the subject from the text.

        Returns:
            Dict[str, str]: A dictionary with the extracted metadata. If extraction fails,
                            fields may be returned as empty strings.
        """
        extracted_metadata: Dict[str, str] = {
            'subject': '',
            'paper': '',
            'insert': '',
            'session': '',
            'code': '',
            'time_allowed': '',
        }

        if not os.path.exists(pdf_path):
            print(f"Error: PDF file not found at '{pdf_path}'")
            return extracted_metadata

        try:
            doc = fitz.open(pdf_path)
            if not doc.page_count:
                print(f"Warning: PDF '{pdf_path}' has no pages.")
                return extracted_metadata

            text = doc[0].get_text("text")
            lines = [PastPaperExtractor.clean_text(line) for line in text.split("\n") if line.strip()]
            normalized_lines = [line.lower() for line in lines]

            # Subject detection
            if not extracted_metadata['subject']:
                for subject_enum in subjects_enum:
                    subject_name = PastPaperExtractor.clean_text(subject_enum.value.local_name).lower()
                    if subject_name in normalized_lines:
                        extracted_metadata['subject'] = Utils.clean_part(subject_enum.value.local_name)
                        break

            # Patterns
            code_pattern = re.compile(r'\b(?:\d{3,4}/\d{2,3}|\d{3})\b')
            paper_pattern = re.compile(r'Paper\s+\d+.*', re.IGNORECASE)
            insert_pattern = re.compile(r'^INSERT$', re.IGNORECASE)
            session_pattern = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)(?:/[A-Za-z]+)?\s+\d{4}', re.IGNORECASE)
            time_allowed_pattern = re.compile(r'(\d+\s+(?:minutes?|hour(?:s)?)(?:\s+\d+\s+minutes?)?)', re.IGNORECASE)

            for line in lines:
                if not extracted_metadata['paper']:
                    match = paper_pattern.search(line)
                    if match:
                        extracted_metadata['paper'] = Utils.clean_part(PastPaperExtractor.clean_text(match.group(0)))

                if not extracted_metadata['insert']:
                    match = insert_pattern.search(line)
                    if match:
                        extracted_metadata['insert'] = Utils.clean_part(PastPaperExtractor.clean_text(match.group(0).title()))

                if not extracted_metadata['session']:
                    match = session_pattern.search(line)
                    if match:
                        extracted_metadata['session'] = Utils.clean_part(PastPaperExtractor.clean_text(match.group(0)))

                if not extracted_metadata['code']:
                    match = code_pattern.search(line)
                    if match:
                        extracted_metadata['code'] = Utils.clean_part(PastPaperExtractor.clean_text(match.group(0)))

                if not extracted_metadata['time_allowed']:
                    match = time_allowed_pattern.search(line)
                    if match:
                        extracted_metadata['time_allowed'] = Utils.clean_part(PastPaperExtractor.clean_text(match.group(0)))

        except fitz.EmptyFileError:
            print(f"Error: PDF '{pdf_path}' is an empty file.")
        except Exception as e:
            print(f"An error occurred while processing '{pdf_path}': {e}")
        finally:
            doc.close()

        return extracted_metadata

    @staticmethod
    def extract_eceswa_past_paper_metadata(pdf_path: str, subjects_enum: Enum) -> Dict[str, str]:
        """
        Extracts metadata from the cover page of an ECESWA past paper PDF.

        Extracted metadata includes:
            - subject: inferred from known subject names (passed as an Enum)
            - paper: title of the paper, e.g., "Paper 2 Geographical Skills"
            - session: e.g., "October/November 2023"
            - code: paper code, e.g., "6890/02"
            - time_allowed: e.g., "2 hours"

        Args:
            pdf_path (str): Path to the ECESWA past paper PDF.
            subjects_enum (Enum): Enum class containing possible subject names.

        Returns:
            Dict[str, str]: Metadata dictionary with keys: subject, paper, session, code, time_allowed.
        """
        extracted_metadata: Dict[str, str] = {
            'subject': '',
            'paper': '',
            'insert': '',
            'session': '',
            'code': '',
            'time_allowed': '',
        }

        if not os.path.exists(pdf_path):
            print(f"Error: PDF file not found at '{pdf_path}'")
            return extracted_metadata

        try:
            doc = fitz.open(pdf_path)
            if not doc.page_count:
                print(f"Warning: PDF '{pdf_path}' has no pages.")
                return extracted_metadata
            
            text = doc[0].get_text("text")
            lines = [PastPaperExtractor.clean_text(line) for line in text.split("\n") if line.strip()]      
            
            # Patterns
            code_pattern = re.compile(r'\b\d{3,4}/\d{2}\b')
            paper_pattern = re.compile(r'Paper\s+\d+.*', re.IGNORECASE)
            session_pattern = re.compile(
                r'(January|February|March|April|May|June|July|August|September|October|November|December)(?:/[A-Za-z]+)?\s+\d{4}',
                re.IGNORECASE
            )
            time_allowed_pattern = re.compile(
                r'\d+\s+(?:minutes?|hours?)(?:\s+\d+\s+minutes?)?', re.IGNORECASE
            )

            for line in lines:
                cleaned_line = PastPaperExtractor.clean_text(line)

                # Subject + Code detection
                if not extracted_metadata['subject'] or not extracted_metadata['code']:
                    for subject_enum in subjects_enum:
                        subject_value = subject_enum.value.strip().lower()
                        cleaned_line_lower = cleaned_line.strip().lower()
                        if subject_value == cleaned_line_lower:
                            extracted_metadata['subject'] = Utils.clean_part(subject_enum.value)
                            code_match = code_pattern.search(cleaned_line)
                            if code_match:
                                extracted_metadata['code'] = Utils.clean_part(code_match.group(0))
                            break

                # Paper detection
                if not extracted_metadata['paper']:
                    paper_match = paper_pattern.search(cleaned_line)
                    if paper_match:
                        extracted_metadata['paper'] = Utils.clean_part(paper_match.group(0).strip())

                # Session detection (independent)
                if not extracted_metadata['session']:
                    session_match = session_pattern.search(cleaned_line)
                    if session_match:
                        extracted_metadata['session'] = Utils.clean_part(session_match.group(0).strip())

                # Time allowed detection (independent)
                if not extracted_metadata['time_allowed']:
                    time_match = time_allowed_pattern.search(cleaned_line)
                    if time_match:
                        extracted_metadata['time_allowed'] = Utils.clean_part(time_match.group(0).strip())

                # Fallback code detection (in case it's on a separate line)
                if not extracted_metadata['code']:
                    code_match = code_pattern.search(cleaned_line)
                    if code_match:
                        extracted_metadata['code'] = Utils.clean_part(code_match.group(0).strip())

        except fitz.EmptyFileError:
            print(f"Error: PDF '{pdf_path}' is an empty file.")
        except Exception as e:
            print(f"An error occurred while processing '{pdf_path}': {e}")
        finally:
            doc.close()

        return extracted_metadata
    