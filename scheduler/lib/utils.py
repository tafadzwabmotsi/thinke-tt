import re

def clean_folder_name(name: str) -> str:
    """
    Cleans a string to be suitable for a filesystem folder name.
    
    It replaces characters that are strictly illegal in Windows filenames,
    condenses multiple spaces to a single space, strips leading/trailing
    spaces, and replaces embedded path separators ('/' or '\') with underscores.
    Hyphens are preserved.

    Args:
        name (str): The original string (e.g., student name, subject name, date string).

    Returns:
        str: The cleaned string, suitable for use as a folder or filename segment.
    """
    # 1. Replace characters strictly illegal in Windows filenames (excluding path separators / \ and hyphen -)
    #    Illegal chars for Windows filenames: < > : " | ? *
    cleaned_name = re.sub(r'[<>:"|?*]', '_', name)

    # 2. Condense any sequences of whitespace (spaces, tabs, newlines) into a single space.
    #    Then, strip any leading or trailing spaces. This preserves single spaces between words.
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()

    # 3. Replace any embedded path separators ('/' or '\') with an underscore.
    #    This prevents unintended subdirectories if a name contains these characters.
    #    Hyphens are explicitly excluded from this replacement.
    cleaned_name = re.sub(r'[/\\]', '_', cleaned_name)
    
    # Ensure the name is not empty after cleaning; provide a fallback if needed
    if not cleaned_name:
        return "untitled"
        
    return cleaned_name