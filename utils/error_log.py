# STANDARD LIBRARY IMPORTS
import os
import logging
from datetime import datetime
import pathlib

# UTIL IMPORTS
from utils.colors import bcolors
from utils.config import LOG_PATH

def log_error_to_file(error_message: str) -> None:
    """
    Logs an error message to a file with a timestamp.

    The log file is created in the 'logs' directory with the naming format
    'error_{timestamp}.log'. If the 'logs' directory does not exist, it
    will be created.

    Parameters:
    error_message (str): The error message to log.

    Returns:
    None
    """
    try:
        os.makedirs(LOG_PATH, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = f"{LOG_PATH}/error_{timestamp}.log"
        logging.basicConfig(filename=log_file_path, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.error(error_message)
    except OSError as e:
        print(bcolors.FAIL + f"\n✗ Failed to create log directory or file." + bcolors.ENDC)
    except Exception as e:
        print(bcolors.FAIL + f"\n✗ An unexpected error occurred while logging." + bcolors.ENDC)