import re

class PastPaperExtractorUtils:
    """
    Defines utility methods commonly to refactor filenames
    """

    @staticmethod
    def clean_part(name: str) -> str | None:
        """
        Cleans a string to be suitable for a filesystem folder name.

        It replaces characters that are strictly illegal in Windows filenames,
        removes parentheses, condenses multiple spaces to a single space, strips leading/trailing
        spaces, and replaces embedded path separators ('/' or '\') with underscores.
        Hyphens are preserved.

        Args:
            name (str): The original string (e.g., student name, subject name, date string).

        Returns:
            str | None: The cleaned string, suitable for use as a folder or filename segment,
                        or None if the string becomes empty after cleaning.
        """
        cleaned = name
        cleaned = re.sub(r'[<>:"|?*]', '_', cleaned)
        cleaned = re.sub(r'[()]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'[/\\]', '_', cleaned)

        return cleaned if cleaned else None

    @staticmethod
    def restore_part(name: str) -> str:
        """
        Restores a cleaned string by replacing underscores with forward slashes.

        Args:
            name (str): The cleaned string.

        Returns:
            str: The restored string with underscores replaced by '/'.
        """
        return name.replace('_', '/')
