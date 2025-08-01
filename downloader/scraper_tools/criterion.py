from enum import Enum


class FilteringCriterion(Enum):
    """
    Provides several criteria for filtering the subject urls.
    These criteria help slice the amount network bandwidth by
    selecting precisely the number the latest sessions from
    which the past papers satisfy the user's needs.
    """
    LATEST_4 = 4
    LATEST_7 = 7
    LATEST_10 = 10
    LATEST_13 = 13
    LATEST_16 = 16


class PaperCount(Enum):
    """
    Provides several criteria for the number of past
    papers that will be downloaded.
    """
    LATEST_5 = 5
    LATEST_10 = 10
    LATEST_20 = 20
    LATEST_30 = 30
    LATEST_40 = 40
    LATEST_50 = 50
  
