# STANDARD LIBRARY IMPORTS
import signal

# UTIL IMPORTS
from utils.colors import bcolors

# Define the timeout handler
def timeout_handler(signum: int, frame: any) -> None:
    """
    Handle the timeout signal.

    Args:
        signum (int): Signal number.
        frame (frame): Current stack frame.
    
    Returns:
        None
    """
    raise TimeoutError("Function call timed out")

# Function to apply the timeout
def run_with_timeout(func: callable, *args: any, timeout_duration: int = 30, **kwargs: any) -> any:
    """
    Call a function with a timeout.

    Args:
        func (callable): Function to call.
        *args: Positional arguments for the function.
        timeout_duration (int): Timeout duration in seconds.
        **kwargs: Keyword arguments for the function.

    Returns:
        Any: Result of the function call.
    """
    # Set the signal handler
    signal.signal(signal.SIGALRM, timeout_handler)
    # Set the alarm
    signal.alarm(timeout_duration)
    try:
        # Call the function
        result = func(*args, **kwargs)
    finally:
        # Cancel the alarm
        signal.alarm(0)
    return result