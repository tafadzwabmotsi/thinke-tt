from enum import Enum


class PapaCambridgeGrade(Enum):
    """
    Lists grades from cambridge
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
    Defines all the possible grades from cambridge
    """
    IGCSE = "IGCSE"
    O_LEVEL = "O-Level"
 
Grade =  EceswaGrade | CambridgeGrade

    