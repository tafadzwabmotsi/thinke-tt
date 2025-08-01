from enum import Enum, auto

class SchedulingCriterion(Enum):
        """
        Defines distinct criteria flags for scheduling.
        Each member is a unique constant.
        """

        """
        Criterion depicts a bottle. Increment the number 
        of exams written per day by one.

        Visual example:

                #    Month 1 - Write 1 exam per day
                ##    Month 2 - Write 2 exams per day
                ###    Month 3 - Write 3 exams per day
                ####   Month 4 - Write 4 exams per day
        """
        # BOTTLE = auto()

        """
        Criterion depicts a ballon. The most outer pair 
        of months will have the number of exams written 
        per day.

        Visual example:

                #    Month 1 - Write 1 exam per day
                ##    Month 2 - Write 2 exams per day
                ###    Month 3 - Write 3 exams per day
                ##     Month 4 - Write 2 exams per day
                #      Month 5 - Write 1 exam per day
        """
        # BALLOON = auto()


        """
        Criterion depicts a zip. If the number month(in the 
        list of dates) is odd, then 1 exam is written 
        per day. But 2 if it's even.

        Visual example:

                #    Month 1 - Write 1 exam per day
                ##    Month 2 - Write 2 exams per day
                #    Month 3 - Write 1 exam per day
                ##    Month 4 - Write 2 exams per day
                #    Month 5 - Write 1 exam per day
        """
        # ZIP = auto()

        """
        Criterion depicts a straight line. A maximum of 
        one exam is written on each day for any month.

        Visual example:

                #    Month 1 - Write 1 exam per day
                #    Month 2 - Write 1 exam per day
                #    Month 3 - Write 1 exam per day
                #    Month 4 - Write 1 exam per day
                #    Month 5 - Write 1 exam per day
        """
        LINE = auto()
    

class AssignmentCriterion(Enum):
        """
        Defines the past paper assignment criteria
        """

        # Latest past papers are assigned first.
        LATEST = auto()

        # Oldest past papers are assigned first.
        OLDEST = auto()

        # One latest past paper is assigned, then oldest, 
        # then latest, and so on. 
        ZIG_ZAG = auto()