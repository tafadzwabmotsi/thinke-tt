
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

class SaveMyExamsSubjectDefinition:
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
    
class SaveMyExamsIgcseSubject(Enum):
    """
    All IGCSE subjects listed by savemyexams.com 
    """
    ACCOUNTING = SaveMyExamsSubjectDefinition("Accounting", "Accounting")
    ADDITIONAL_MATHS = SaveMyExamsSubjectDefinition("Additional Maths", "Additional Mathematics")
    BIOLOGY = SaveMyExamsSubjectDefinition("Biology", "Biology")
    BUSINESS = SaveMyExamsSubjectDefinition("Business", "Business Studies")
    CHEMISTRY = SaveMyExamsSubjectDefinition("Chemistry", "Chemistry") 
    COMPUTER_SCIENCE = SaveMyExamsSubjectDefinition("Computer Science", "Computer Science")
    
    ECONOMICS = SaveMyExamsSubjectDefinition("Economics", "Economics") 
    ENGLISH_LANGUAGE = SaveMyExamsSubjectDefinition("English Language", "English Language") 
    ENGLISH_LITERATURE = SaveMyExamsSubjectDefinition("English Literature", "Literature in English") 
    GEOGRAPHY = SaveMyExamsSubjectDefinition("Geography", "Geography") 
    HISTORY = SaveMyExamsSubjectDefinition("History", "History") 
    ICT = SaveMyExamsSubjectDefinition("ICT", "ICT") 
    INTERNATIONAL_MATHS_CORE = SaveMyExamsSubjectDefinition("International Maths: Core", "Mathematics") 
    INTERNATIONAL_MATHS_EXTENDED = SaveMyExamsSubjectDefinition("International Maths: Extended", "Mathematics") 
    MATHS_CORE = SaveMyExamsSubjectDefinition("Maths: Core", "Mathematics") 
    MATHS_EXTENDED = SaveMyExamsSubjectDefinition("Maths: Extended", "Mathematics") 
    PHYSICS = SaveMyExamsSubjectDefinition("Physics", "Physics") 
    RELIGIOUS_STUDIES = SaveMyExamsSubjectDefinition("Religious Studies", "Religious Education")
    
class SaveMyExamsOLevelSubject(Enum):
    """
    All O Level subjects listed by savemyexams.com 
    """    
    ADD_MATHS = SaveMyExamsSubjectDefinition("Additional Maths", "Additional Mathematics")
    BIOLOGY = SaveMyExamsSubjectDefinition("Biology", "Biology")
    BUSINESS_STUDIES = SaveMyExamsSubjectDefinition("Business Studies", "Business Studies")
    CHEMISTRY = SaveMyExamsSubjectDefinition("Chemistry", "Chemistry") 
    COMPUTER_SCIENCE = SaveMyExamsSubjectDefinition("Computer Science", "Computer Science")
    ECONOMICS = SaveMyExamsSubjectDefinition("Economics", "Economics") 
    GEOGRAPHY = SaveMyExamsSubjectDefinition("Geography", "Geography") 
    HISTORY = SaveMyExamsSubjectDefinition("History", "History") 
    MATHS = SaveMyExamsSubjectDefinition("Maths", "Mathematics")
    PHYSICS = SaveMyExamsSubjectDefinition("Physics", "Physics") 

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
    
SaveMyExamsSubject = SaveMyExamsIgcseSubject | SaveMyExamsOLevelSubject
EceswaSubject = EceswaEgcseSubject | EceswaJcSubject
Subject = EceswaSubject | SaveMyExamsSubjectDefinition
SeniorHighSchoolSubject = EceswaEgcseSubject | SaveMyExamsSubjectDefinition