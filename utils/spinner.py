# STANDARD LIBRARY IMPORTS
import time
import threading
import sys

# UTIL IMPORTS
from utils.colors import bcolors

def loading_spinner(loading_text: str, success_text: str, failure_text: str) -> None:
    """
    Display loading spinner with text.

    Args:
    text (str): Text to display with loading spinner.
    
    Returns:
    None
    """
    # Define loading spinner animation
    animation = "◢◣◤◥"
    idx = 0
    # Get current thread
    t = threading.current_thread()
    # Show animation while attribute is set
    while getattr(t, "is_loading", True):
        # print(f"{animation[idx % len(animation)]} {loading_text}...", end="\r")
        print(f"\r{animation[idx % len(animation)]} {loading_text}...", end='', flush=True)
        idx += 1
        time.sleep(0.1)
    # Print success or failure text based on success status attribute
    if getattr(t, "finished_successfully", True):
        print(f"\r{bcolors.OKGREEN}✔ {success_text}{bcolors.ENDC}", end='', flush=True)
    else:
        print(f"\r{bcolors.FAIL}✗ {failure_text}{bcolors.ENDC}", end='', flush=True)
    
def spawn_loading_spinner_thread(loading_text: str, success_text: str, failure_text: str) -> threading.Thread:
    """
    Spawns a new thread for the loading spinner.

    Args:
    loading_text (str): Text to display with loading spinner.
    success_text (str): Text to display upon successful completion.
    failure_text (str): Text to display upon failure.

    Returns:
    thread (threading.Thread): Thread object for loading spinner.
    """
    thread = None
    try:
        # Spawn thread with target function and arguments
        thread = threading.Thread(target=loading_spinner, args=(loading_text, success_text, failure_text))
        # Set thread as daemon to allow for KeyboardInterrupt to stop thread
        thread.daemon = True                                                                                       
        # Set thread loading status to True to start animation  
        thread.is_loading = True                                                                             
        # Set thread success status initial value
        thread.finished_successfully = False                                                               
        # Start thread   
        thread.start()                                                                                                           
    except KeyboardInterrupt:
        pass
    return thread

def terminate_loading_spinner_thread(thread: threading.Thread, terminate_success: bool ) -> None:
    """
    Terminates the loading spinner thread and sets success status.

    Args:
    thread (threading.Thread): Thread object for loading spinner.
    terminate_success (bool): True if successful, False if failed.

    Returns:
    None
    """
    try:
        # Set thread loading status attribute to stop animation
        thread.is_loading = False
        # Set thread success status for conditional print of failure text                            
        thread.finished_successfully = terminate_success
        # Join thread back to main thread / end thread     
        thread.join()                                           
    except KeyboardInterrupt: 
        pass