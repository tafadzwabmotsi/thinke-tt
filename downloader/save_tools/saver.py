

import requests

from data.past_papers.save_metadata import SaveMetadata
from downloader.scraper_tools.eceswa import EceswaScraper
from downloader.scraper_tools.papacambridge import PapaCambridgeScraper
from downloader.scraper_tools.save_my_exams import SaveMyExamsScraper
from lib.grade import CambridgeGrade, EceswaGrade
from lib.subject import EceswaEgcseSubject, EceswaJcSubject, SaveMyExamsIgcseSubjects
from lib.utils import LibUtils


class PastPaperSaver:
    """
    Gathers past paper urls and saves them in .csv files grouping them by in folders 
    grade, subject, year, session, url
    """
    
    def __init__(self):
        self._eceswa_scraper = EceswaScraper()
        self._papa_cambridge_scraper = PapaCambridgeScraper()
        self._save_my_exams_scraper = SaveMyExamsScraper()

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        })
  

    def save(self):
        """
        Iterate over each ECESWA grade and retrieve PDF URLs for all associated subjects
        using the appropriate scraper, then save them to CSV.

        - Skips EPC grade.
        - Uses `SaveMyExamsScraper` for IGCSE subjects.
        - Uses `EceswaScraper` for JC and EGCSE subjects.
        - Displays a spinner to indicate progress for each grade.

        Returns:
            None
        """
        for grade in list(list(EceswaGrade) + list (CambridgeGrade)):
            with LibUtils.spinner(
                start_text=f"Saving URLs - {grade.value}",
                success_text=f"Successfully saved all URLs - {grade.value}"
            ):
                if grade == CambridgeGrade.IGCSE:
                    subject_enum = SaveMyExamsIgcseSubjects
                    scraper = self._save_my_exams_scraper
                elif grade in (EceswaGrade.JC, EceswaGrade.EGCSE):
                    subject_enum = EceswaJcSubject if grade == EceswaGrade.JC else EceswaEgcseSubject
                    scraper = self._eceswa_scraper
                else:
                    raise ValueError(f"Unsupported grade: {grade}")

                for subject in subject_enum:
                    urls = scraper.get_pdf_save_urls(grade, subject)
                    SaveMetadata(urls).save()



                        
                    
                        