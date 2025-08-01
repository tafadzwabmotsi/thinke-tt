from enum import Enum


class PapaCambridgeGrade(Enum):
    """
    Lists grades from papacambridge.com
    """
    IGCSE = "IGCSE"
    # Could have more grades distinct from SaveMyExamsGrade 


class EceswaGrade(Enum):
    """
    Lists grades from eceswa
    """
    EGCSE = "EGCSE"
    JC = "JC"

class CambridgeGrade(Enum):
    """
    Defines all the possible grades from savemyexams.com
    """
    IGCSE = "IGCSE"
    # Could have more grade distinct from PapaCambridgeGrade
 
Grade =  EceswaGrade | CambridgeGrade

    