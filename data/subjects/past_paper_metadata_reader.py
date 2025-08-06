

import csv
from typing import Dict, List
from lib.paths import PastPaperCSVPaths
from lib.typing.domain.schedule import PastPaperMetadata


# data/subjects/past_paper_metadata_reader.py
class PastPaperMetadataReader:
    def __init__(self, grade: str):
        self._paths = PastPaperCSVPaths(grade)
    
    def get_subject_metadata(self, subject: str) -> List[PastPaperMetadata]:
        metadata = []
        subject_file = self._paths.subject_file(subject)

        if subject_file.exists():
            with subject_file.open(mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        paper = PastPaperMetadata(
                            grade=row['grade'].strip(),
                            subject=row['subject'].strip(),
                            year=int(row['year'].strip()),
                            session=row['session'].strip(),
                            url=row['url'].strip(),
                            paper=""
                        )
                        metadata.append(paper)
                    except KeyError:
                        continue
                    except ValueError:
                        continue

        return metadata