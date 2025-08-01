import os
import re
from typing import List
import requests
from urllib.parse import urlparse # Import urlparse to extract filename from URL


def clean_folder_name(name: str) -> str:
    """
    Cleans a string to be suitable for a filesystem folder name.
    Replaces invalid characters and normalizes spaces/hyphens to underscores.
    """
    # Replace characters not allowed in Windows filenames (and /) with an underscore.
    # Note: \ is a path separator and will be handled by os.path.join later,
    # so we primarily clean characters that are invalid *within* a segment.
    # For simplicity, we are cleaning a broad set here.
    cleaned_name = re.sub(r'[<>:"|?*]', '_', name)
    cleaned_name = re.sub(r'[/\\-]', '_', cleaned_name) # Explicitly replace path separators and hyphens

    # Replace multiple spaces with a single underscore, and strip leading/trailing underscores
    cleaned_name = re.sub(r'\s+', '_', cleaned_name).strip('_')
    
    return cleaned_name

def download_file(session: requests.Session, url: str, save_path: str) -> bool:
    """
    Downloads a single PDF file from the given URL and saves it to the specified path.

    Args:
        session: The requests.Session object to use for downloading.
        url: The absolute URL of the PDF file to download.
        save_path: The full local path (including filename) where the PDF should be saved.

    Returns:
        True if the download was successful, False otherwise.
    """

    # Do not re-download files that already exist
    if os.path.exists(save_path):
        # print(f"File already exists, skipping download: {os.path.basename(save_path)}")
        return True
    
    try:
        # Use stream=True to handle potentially large files efficiently
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status() 

        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False
    except IOError as e:
        print(f"Error saving file to {save_path}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during download of {url}: {e}")
        return False

def get_urls_for_nonexistent_files(pdf_urls: List[str], current_download_dir: str) -> List[str]:
    """
    Filters a list of PDF URLs, returning only those for which the corresponding
    file does not already exist in the specified local download directory.
    This helps in resuming downloads and avoiding redundant checks/downloads.

    Args:
        pdf_urls (List[str]): A list of absolute URLs to PDF files.
        current_download_dir (str): The absolute path to the local directory
                                    where the PDF files are expected to be saved.

    Returns:
        List[str]: A new list containing only the URLs of PDF files that
                   do not yet exist in the `current_download_dir`.
    """
    urls: List[str] = []
    
    for pdf_url in pdf_urls:
        # Extract the intended filename from the PDF URL
        filename = os.path.basename(urlparse(pdf_url).path)
        
        # Construct the full expected path for the file on disk
        full_save_path = os.path.join(current_download_dir, filename)

        # Check if the file does NOT exist at the calculated path
        if not os.path.exists(full_save_path):
            urls.append(pdf_url)
        
        else:
            # print(f"File already exists. Skipping {pdf_url}.")
            continue
    
    return urls
