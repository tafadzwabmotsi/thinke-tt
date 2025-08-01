
from enum import Enum

class PapaCambridgeIgcseSubject(Enum):
    """
    List the most common subjects offered by the Cambridge 
    IGCSE exam council that students take
    """
    MATHEMATICS = "Mathematics"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"
    ENGLISH = "English"
    LITERATURE = "Literature"
    HISTORY = "History"
    GEOGRAPHY = "Geography"
    BUSINESS_STUDIES = "Business Studies"
    DESIGN_AND_TECHNOLOGY = "Design and Technology"
    RELIGIOUS_STUDIES = "Religious Studies"
    ACCOUNTING = "Accounting"
    AGRICULTURE = "Agriculture"
    COMPUTER_SCIENCE = "Computer Science"
    ECONOMICS = "Economics"
    FOOD_AND_NUTRITION = "Food and Nutrition"
    PHYSICAL_SCIENCE = "Physical Science"
    WORLD_LITERATURE = "World Literature"

class SaveMyExamsIgcseSubject:
    def __init__(self, site_name: str, local_name: str):
        """
        Constructs of a save igcse subject.
        
        Args:
            site_name (str): The subject's name on the website.
            local_name (str): The subject's name on local disk
        """
        self.site_name = site_name
        self.local_name = local_name

    def __str__(self):
        return f"{self.site_name} ({self.local_name})"
    
class SaveMyExamsIgcseSubjects(Enum):
    """
    All IGCSE subjects listed by savemyexams.com 
    """
    ACCOUNTING = SaveMyExamsIgcseSubject("Accounting", "Accounting")
    ADDITIONAL_MATHS = SaveMyExamsIgcseSubject("Additional Maths", "Additional Mathematics")
    BIOLOGY = SaveMyExamsIgcseSubject("Biology", "Biology")
    BUSINESS = SaveMyExamsIgcseSubject("Business", "Business Studies")
    CHEMISTRY = SaveMyExamsIgcseSubject("Chemistry", "Chemistry") 
    COMPUTER_SCIENCE = SaveMyExamsIgcseSubject("Computer Science", "Computer Science")
    ECONOMICS = SaveMyExamsIgcseSubject("Economics", "Economics") 
    ENGLISH_LANGUAGE = SaveMyExamsIgcseSubject("English Language", "English Language") 
    ENGLISH_LITERATURE = SaveMyExamsIgcseSubject("English Literature", "Literature in English") 
    GEOGRAPHY = SaveMyExamsIgcseSubject("Geography", "Geography") 
    HISTORY = SaveMyExamsIgcseSubject("History", "History") 
    ICT = SaveMyExamsIgcseSubject("ICT", "ICT") 
    INTERNATIONAL_MATHS_CORE = SaveMyExamsIgcseSubject("International Maths: Core", "Mathematics") 
    INTERNATIONAL_MATHS_EXTENDED = SaveMyExamsIgcseSubject("International Maths: Extended", "Mathematics") 
    MATHS_CORE = SaveMyExamsIgcseSubject("Maths: Core", "Mathematics") 
    MATHS_EXTENDED = SaveMyExamsIgcseSubject("Maths: Extended", "Mathematics") 
    PHYSICS = SaveMyExamsIgcseSubject("Physics", "Physics") 
    RELIGIOUS_STUDIES = SaveMyExamsIgcseSubject("Religious Studies", "Religious Education")
    
class EceswaJcSubject(Enum):
    """
    List JC subjects offered by the Eceswa
    """
    ADD_MATHS = "Additional Mathematics"
    AGRICULTURE = "Agriculture"
    BOOKKEEPING = "Bookkeeping and Accounts"
    BUSINESS_STUDIES = "Business Studies"
    CONSUMER_SCIENCE = "Consumer Science"
    DESIGN_AND_TECHNOLOGY = "Design and Technology"
    DEVELOPMENT_STUDIES = "Development Studies"
    ENGLISH = "English Language"
    ENGLISH_LITERATURE = "English Literature"
    FRENCH = "French"
    GEOGRAPHY = "Geography"
    HISTORY = "History"
    MATHEMATICS = "Mathematics"
    RELIGIOUS_EDUCATION = "Religious Education"
    SCIENCE = "Science"
    SISWATI = "SiSwati"

class EceswaEgcseSubject(Enum):
    """
    Lists EGCSE subjects provided by Eceswa
    """
    ACCOUNTING = "Accounting"
    AGRICULTURE = "Agriculture"
    BIOLOGY = "Biology"
    BUSINESS_STUDIES = "Business Studies"
    DESIGN_AND_TECHNOLOGY = "Design and Technology"
    ECONOMICS = "Economics"
    ENGLISH = "English Language"
    FASHION_AND_FABRICS = "Fashion and Fabrics"
    FIRST_SISWATI = "First Language SiSwati"
    FOOD_AND_NUTRITION = "Food and Nutrition"
    GEOGRAPHY = "Geography"
    HISTORY = "History"
    LITERATURE = "Literature in English"
    MATHEMATICS = "Mathematics"
    PHYSICAL_SCIENCE = "Physical Science"
    RELIGIOUS_EDUCATION = "Religious Education"
    SECOND_SISWATI = "Siswati as a Second Language"
    
class EceswaEpcSubject(Enum):
    """
    Lists EGCSE subjects provided by Eceswa
    """
    ENGLISH = "English Language"
    MATHEMATICS = "Mathematics"
    SISWATI = "Siswati"
    FRENCH = "French"
    SCIENCE = "Science"
    SOCIAL_STUDIES = "Social Studies"
    AGRICULTURE = "Agriculture"
    CONSUMER_SCIENCE = "Consumer Science"
    RELIGIOUS_EDUCATION = "Religious Education"
    PRACTICAL_ARTS_AND_TECHNOLOGY = "Practical Arts and Technology"
    EXPRESSIVE_ARTS = "Expressive Arts"
    HEALTH_AND_PHYSICAL_EDUCATION = "Health and Physical Education"
    ICT = "ICT"
    
EceswaSubject = EceswaEgcseSubject | EceswaJcSubject
Subject = EceswaSubject | SaveMyExamsIgcseSubject
SeniorHighSchoolSubject = EceswaEgcseSubject | SaveMyExamsIgcseSubject