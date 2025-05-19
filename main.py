#!/usr/local/Caskroom/miniforge/base/envs/temps/bin/python
# STANDARD LIBRARY IMPORTS
import sys
import os
import traceback
import json
import string
import uuid
from datetime import datetime
from datetime import timedelta

# THIRD PARTY IMPORTS
import pandas as pd
import duckdb as ddb
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

# UTIL IMPORTS
from utils.colors import bcolors
from utils.config import VERSION_NUMBER, RES_PATH, DB_FILE_NAME, USER_CONFIG_FILE_NAME, OUT_PATH, GOLD_TABLE_SCHEMA
from utils.error_log import log_error_to_file, LOG_PATH
from utils.spinner import spawn_loading_spinner_thread, terminate_loading_spinner_thread

# GLOBAL VARS
_threads = []
_config = {}

def clear_terminal() -> None:
    """
    Clears the terminal screen.

    Args:
        None
    
    Returns:
        None
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def print_title() -> None:
    """
    Prints title.

    Args:
        None
    
    Returns:
        None
    """
    print(f"{bcolors.HEADER}{bcolors.BOLD}{bcolors.UNDERLINE}⏱ temps - Simple Time Tracking CLI (v{VERSION_NUMBER}){bcolors.ENDC}\n")

def terminate_threads(threads: list = []) -> None:
    """
    Terminates all threads in the list.

    Args:
        threads (list): List of threads to terminate.

    Returns:
        None
    """
    if len(threads) > 0:
        for thread in threads:
            terminate_loading_spinner_thread(thread, False)

def graceful_exit(success: bool) -> None:
    """
    Prints exit message and terminates script execution.

    Args:
        success (bool): Whether the script executed successfully or not.
    
    Returns:
        None
    """
    if not success:
        print(f"\n{bcolors.WARNING}→ Exiting...{bcolors.ENDC}")
    sys.exit()

def prompt_continue() -> None:
    """
    Prompts the user to continue.

    Args:
        None
    
    Returns:
        None
    """
    input(f"{bcolors.OKCYAN}\nPress ENTER to continue...{bcolors.ENDC}")

def get_db_connection() -> ddb.DuckDBPyConnection:
    """
    Returns a connection to the DuckDB database.

    Args:
        None
    
    Returns:
        ddb.DuckDBPyConnection: Connection to the DuckDB database.
    """
    return ddb.connect(os.path.join(RES_PATH, DB_FILE_NAME))

def save_config(config: dict) -> None:
    """
    Saves the user configuration to a json file.

    Args:
        config (dict): User configuration to save.
    
    Returns:
        None
    """
    try:
        with open(os.path.join(RES_PATH, USER_CONFIG_FILE_NAME), "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        raise e

def convert_minutes(minutes):
    """
    Converts minutes to a human-readable format of years, months, weeks, days, hours, and minutes.

    Args:
        minutes (int): Number of minutes to convert.
    
    Returns:
        str: Human-readable format of the number of minutes.
    """
    return f"{minutes // 525600}y {(minutes % 525600) // 43800}m {((minutes % 525600) % 43800) // 10080}w {(((minutes % 525600) % 43800) % 10080) // 1440}d {((((minutes % 525600) % 43800) % 10080) % 1440) // 60}h {((((minutes % 525600) % 43800) % 10080) % 1440) % 60}min"


def prompt(input_type: str, *args, **kwargs) -> str:
    """
    Prompts the user for input.

    Args:
        input_type (str): Type of input to prompt for.
        *args: Additional arguments to pass to the input function.
        **kwargs: Additional keyword arguments to pass to the input function.

    Returns:
        str: Choice / input returned by prompt.    
    """
    MANDATORY_MSG = "This field is required!"
    try:
        answer = None
        match input_type:
            case "text":
                answer = inquirer.text(
                    amark = "✔", 
                    mandatory_message = MANDATORY_MSG,
                    **kwargs
                ).execute()
            case "number":
                answer = inquirer.number(
                    amark = "✔", 
                    mandatory_message = MANDATORY_MSG,
                    **kwargs
                ).execute()
            case "number":
                answer = inquirer.number(
                    amark = "✔",
                    mandatory_message = MANDATORY_MSG,
                    **kwargs
                ).execute()
            case "confirm":
                answer = inquirer.confirm(
                    amark = "✔",
                    mandatory_message = MANDATORY_MSG,
                    **kwargs
                ).execute()
            case "select":
                answer = inquirer.select(
                    amark = "✔",
                    mandatory_message = MANDATORY_MSG,
                    **kwargs
                ).execute()
            case "checkbox":
                answer = inquirer.checkbox(
                    amark = "✔",
                    mandatory_message = MANDATORY_MSG,
                    **kwargs
                ).execute()
            case "fuzzy":
                answer = inquirer.fuzzy(
                    amark = "✔",
                    mandatory_message = MANDATORY_MSG,
                    **kwargs
                ).execute()
            case _:
                pass
        if answer is None:
            raise KeyboardInterrupt
        return answer
    except KeyboardInterrupt as e:
        raise e
    except Exception as e:
        print(f"\n{bcolors.FAIL}✗ An error occured during prompting for user input.{bcolors.ENDC}")
        raise e

def show_entry(entry: dict) -> None:
    """
    Shows the details of an entry.

    Args:
        entry (dict): Entry to show.
    
    Returns:
        None
    """
    try:
        print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ VIEW ENTRY{bcolors.ENDC}\n")
        print(f"{bcolors.ORANGE}‣ Date:            {bcolors.ENDC}{entry['day_of_week']}, {entry['date'].strftime('%d %B %Y')}")
        print(f"{bcolors.ORANGE}‣ Type:            {bcolors.ENDC}{entry['event_type']}")
        if entry["event_type"] == "Work":
            print(f"{bcolors.ORANGE}‣ Time Overview:   {bcolors.ENDC}{entry['clock_in']} → {entry['clock_out']} (incl. {entry['break_time_minutes']}min break)")
            print(f"{bcolors.ORANGE}‣ Time Worked:     {bcolors.ENDC}{entry['actual_total_minutes'] // 60}h {entry['actual_total_minutes'] % 60}min / {entry['expected_total_minutes'] // 60}h {entry['expected_total_minutes'] % 60}min ({(entry['actual_total_minutes']/entry['expected_total_minutes']*100):.0f}%)")
        if entry["event_type"] in ["Work", "Overtime Compensation"]:
            print(f"{bcolors.ORANGE}‣ Balance:         {bcolors.ENDC}{bcolors.OKGREEN + '+' if entry['day_balance_minutes'] > 0 else bcolors.FAIL if entry['day_balance_minutes'] < 0 else None}{entry['day_balance_minutes']}min{bcolors.ENDC}")
        print()
    except Exception as e:
        raise e

def show_config() -> None:
    """
    Shows the user configuration.

    Args:
        None
    
    Returns:
        None
    """
    try:
        print(f"{bcolors.ORANGE}‣ Name:            {bcolors.ENDC}{_config['name']}")
        print(f"{bcolors.ORANGE}‣ Start Date:      {bcolors.ENDC}{_config['start_date']}")
        print(f"{bcolors.ORANGE}‣ Weekly Work:     {bcolors.ENDC}{(_config['weekly_work_minutes'] // 60):.0f}h {(_config['weekly_work_minutes'] % 60):.0f}min")
        print(f"{bcolors.ORANGE}‣ Work Days:       {bcolors.ENDC}{', '.join(_config['work_days'])}")
        print(f"{bcolors.ORANGE}‣ Daily Break:     {bcolors.ENDC}{_config['daily_break_minutes']}min")
        print()
    except Exception as e:
        raise e

def create_config(default: dict = None) -> dict:
    """
    Creates a new user configuration.

    Args:
        None

    Returns:
        dict: User configuration.
    """
    config = {}
    config["name"] = prompt(
        input_type = "text",
        message = "Enter your name: ",
        default = default["name"] if default else "",
        mandatory = True,
        wrap_lines = True,
        validate = lambda text: len(text) > 0 and len(text) < 50 and all(character in string.ascii_letters + string.digits + string.punctuation + ' ' for character in text),
        invalid_message = "Name must be between 1 and 50 characters and can only consist of alphanumerics, spaces, and punctuation.",
    )
    config["start_date"] = prompt(
        input_type = "text",
        message = "Enter the start date (YYYY-MM-DD): ",
        default = default["start_date"] if default else "",
        mandatory = True,
        wrap_lines = True,
        validate = lambda text: len(text) == 10 and datetime.strptime(text, "%Y-%m-%d"),
        invalid_message = "Start date must be in format YYYY-MM-DD.",
    )
    config["weekly_work_minutes"] = prompt(
        input_type = "text",
        message = "Enter the number of expected weekly work hours: ",
        default = (f"{int(default['weekly_work_minutes'] / 60)}" if (default["weekly_work_minutes"] / 60).is_integer() else f"{default['weekly_work_minutes'] / 60:.1f}") if default else "",
        mandatory = True,
        wrap_lines = True,
        validate = lambda number: float(number) > 0 and float(number) < 168,
        invalid_message = "Start date must be in format YYYY-MM-DD.",
        filter = lambda number: float(number) * 60
    )
    config["work_days"] = prompt(
        input_type = "select",
        message = "Select your work days: ",
        choices = [
            Choice("Monday", enabled=True if default and "Monday" in default["work_days"] else False),
            Choice("Tuesday", enabled=True if default and "Tuesday" in default["work_days"] else False),
            Choice("Wednesday", enabled=True if default and "Wednesday" in default["work_days"] else False),
            Choice("Thursday", enabled=True if default and "Thursday" in default["work_days"] else False),
            Choice("Friday", enabled=True if default and "Friday" in default["work_days"] else False),
            Choice("Saturday", enabled=True if default and "Saturday" in default["work_days"] else False),
            Choice("Sunday", enabled=True if default and "Sunday" in default["work_days"] else False)
        ],
        default = default["work_days"] if default else "",
        mandatory = True,
        wrap_lines = True,
        multiselect = True,
        validate = lambda choices: len(choices) > 0,
        invalid_message = "At least one work day must be selected.",
        show_cursor = False,
        border = True
    )
    config["daily_break_minutes"] = prompt(
        input_type = "number",
        message = "Enter the number of daily break minutes: ",
        default = default["daily_break_minutes"] if default else 0,
        mandatory = True,
        wrap_lines = True,
        validate = lambda number: int(number) >= 0 and int(number) < config["weekly_work_minutes"] / len(config["work_days"]),
        invalid_message = f"Daily break minutes must be between 0 and {round(1440 - (config["weekly_work_minutes"] / len(config["work_days"])))}.",
        filter = lambda number: int(number)
    )
    config["expected_daily_total_minutes"] = config["weekly_work_minutes"] / len(config["work_days"]) + config["daily_break_minutes"]
    return config

def load_validate_config() -> None:
    """
    Loads and validates the user configuration.

    Args:
        None

    Returns:
        None
    """
    try:
        thread_init_config = spawn_loading_spinner_thread(f"Loading & validating user configuration", f"Successfully loaded & validated user configuration.\n", f"Failed to load & validate user configuration.")
        _threads.append(thread_init_config)
        # Load config into global variable to make it accessible across entire script
        global _config
        _config = json.load(open(os.path.join(RES_PATH, USER_CONFIG_FILE_NAME), "r"))
        # Validate config
        # Check if all required fields are present in the config
        if not all(key in _config for key in ["name", "start_date", "weekly_work_minutes", "work_days", "daily_break_minutes"]):
            raise ValueError("User config file is missing required fields. Please delete the config file and re-launch the program.")
        terminate_loading_spinner_thread(thread_init_config, True)
    except Exception as e:
        raise e

def initialize() -> None:
    """
    Initializes the database, creates the necessary tables, loads and validates the user config, creates folder structure.

    Args:
        None
    
    Returns:
        None
    """
    try:
        # FOLDER STRUCTURE --- --- --- --- ---
        # Create the necessary directories if they don't exist
        thread_init_folders = spawn_loading_spinner_thread(f"Creating folder structure", f"Successfully created folder structure.\n", f"Failed to create folder structure.")
        _threads.append(thread_init_folders)
        os.makedirs(RES_PATH, exist_ok=True)
        os.makedirs(OUT_PATH, exist_ok=True)
        terminate_loading_spinner_thread(thread_init_folders, True)
        # DATABASE --- --- --- --- ---
        thread_init_database = spawn_loading_spinner_thread(f"Validating database", f"Successfully validated database.\n", f"Failed to validate database.")
        _threads.append(thread_init_database)
        # Create a connection to the DuckDB database
        connection = get_db_connection()
        # Create the 'times' table if it doesn't exist
        result = connection.execute("SHOW ALL TABLES;").fetchall()
        table_exists = len(result) > 0
        if not table_exists:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS times (
                    uuid VARCHAR NOT NULL PRIMARY KEY,
                    date DATE NOT NULL UNIQUE,
                    day_of_week VARCHAR NOT NULL,
                    event_type VARCHAR NOT NULL,
                    clock_in VARCHAR,
                    clock_out VARCHAR,
                    break_time_minutes INT,
                    expected_total_minutes INT,
                    expected_total_minutes_work_default INT, 
                    actual_total_minutes INT,
                    day_balance_minutes INT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                );
            """)
        # Check if the table schema matches the expected schema
        table_schema = connection.execute("DESCRIBE times;").fetchall()
        # When table schema is not matched, export all data as backup and advise to delete the database file
        if table_schema != GOLD_TABLE_SCHEMA:
            df = connection.execute("SELECT * FROM times;").fetchdf()
            df.to_excel(os.path.join(OUT_PATH, "backup.xlsx"), index=False)
            raise ValueError("Table schema does not match the expected schema. Delete the database file and re-lauch the program. This will delete all your entries.")
        # Close the connection
        connection.close()
        terminate_loading_spinner_thread(thread_init_database, True)
        # USER CONFIG --- --- --- --- ---
        # Check if user config file exists
        config = {}
        config_exists = os.path.exists(os.path.join(RES_PATH, USER_CONFIG_FILE_NAME))
        # Prompt for config creation if it doesn't exist
        if not config_exists:
            print(f"{bcolors.WARNING}→ User config file not found. Creating new config..{bcolors.ENDC}")
            config = create_config()
            # Write config to json file
            save_config(config)
            print(f"{bcolors.OKGREEN}✔ Successfully created user configuration.{bcolors.ENDC}")
        # Read, validate & apply config
        load_validate_config()
        prompt_continue()
    except Exception as e:
        raise e

def get_existing_entries() -> any:
    """
    Returns all existing entries from the database.

    Args:
        None
    
    Returns:
        any: All existing entries from the database.
    """
    try:
        # Print loading spinner
        thread_get_existing_entries = spawn_loading_spinner_thread(f"Loading existing entries", f"Successfully loaded existing entries.\n", f"Failed to load existing entries.")
        _threads.append(thread_get_existing_entries)
        # Create a connection to the DuckDB database
        connection = get_db_connection()
        # Get all existing entries
        existing_entries = connection.execute("SELECT * FROM times;").df()
        # Close the connection
        connection.close()
        # Terminate loading spinner
        terminate_loading_spinner_thread(thread_get_existing_entries, True)
        return existing_entries
    except Exception as e:
        raise e

def add_entry() -> None:
    """
    Adds a new entry to the database.

    Args:
        None
    
    Returns:
        None
    """
    try:
        should_exit = False
        while not should_exit:
            # Print header
            clear_terminal()
            print_title()
            print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ ADD NEW ENTRY{bcolors.ENDC}\n")
            # Get all existing entries
            existing_entries = get_existing_entries()
            # Get all existing dates from database entries formatted as YYYY-MM-DD
            existing_dates = [date.strftime("%Y-%m-%d") for date in existing_entries["date"].tolist()]
            # Get all valid dates from start date to today, excluding existing dates
            valid_dates = sorted([
                date.strftime("%Y-%m-%d") for date in (
                    datetime.strptime(_config["start_date"], "%Y-%m-%d") + timedelta(days=i) for i in range((datetime.now() - datetime.strptime(_config["start_date"], "%Y-%m-%d")).days + 1)
                )
                if date.strftime("%A") in _config["work_days"] and date.strftime("%Y-%m-%d") not in set(existing_dates)
            ], reverse=True)
            # No dates available -> entries are up-to-date, nothing to do
            if len(valid_dates) == 0:
                print(f"{bcolors.OKGREEN}✔ Entries are up-to-date. There are currently no missing entries.{bcolors.ENDC}")
                should_exit = True
                prompt_continue()
                continue
            # Prompts for entry details below
            date = prompt(
                input_type = "fuzzy",
                message = "Select an entry date:",
                choices =  [
                    Choice(date) for date in valid_dates
                ],
                default = valid_dates[0] if len(valid_dates) > 0 else "",
                mandatory = True,
                wrap_lines = True,
                validate = lambda text: len(text) == 10 and datetime.strptime(text, "%Y-%m-%d"),
                invalid_message = "Start date must be in format YYYY-MM-DD.",
                border = True,
                cycle = True
            )
            day_of_week = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
            event_type = prompt(
                input_type = "select",
                message = "Select an event type:",
                choices = [
                    "Work",
                    "Vacation",
                    "Public / Company Holiday",
                    "Sick Leave",
                    "Overtime Compensation",
                ],
                default = "Work",
                mandatory = True,
                wrap_lines = True,
                show_cursor = False,
                border = True
            )
            # Set default values
            clock_in = None
            clock_out = None
            actual_total_minutes = None
            balance = None 
            expected_total_minutes = 0
            # Overtime compensation specifics
            if event_type == "Overtime Compensation":
                expected_total_minutes = _config["expected_daily_total_minutes"]
                balance = -_config["expected_daily_total_minutes"]
            # Work specifics
            if event_type == "Work":
                clock_in = prompt(
                    input_type = "text",
                    message = "Enter clock in time (HH:MM): ",
                    mandatory = True,
                    wrap_lines = True,
                    validate = lambda text: len(text) == 5 and datetime.strptime(text, "%H:%M") >= datetime.strptime("00:00", "%H:%M") and datetime.strptime(text, "%H:%M") <= datetime.strptime("23:59", "%H:%M"),
                    invalid_message = "Clock in time must be in format HH:MM, between 00:00 and 23:59.",
                )
                clock_out = prompt(
                    input_type = "text",
                    message = "Enter clock out time (HH:MM): ",
                    mandatory = True,
                    wrap_lines = True,
                    validate = lambda text: len(text) == 5 and datetime.strptime(text, "%H:%M") > datetime.strptime(clock_in, "%H:%M") and datetime.strptime(text, "%H:%M") >= datetime.strptime("00:00", "%H:%M") and datetime.strptime(text, "%H:%M") <= datetime.strptime("23:59", "%H:%M"),
                    invalid_message = "Clock out time must be in format HH:MM, between 00:00 and 23:59, and after clock in time.",
                )
                expected_total_minutes = _config["expected_daily_total_minutes"]
                # Get difference between clock in and clock out
                clock_in_time = datetime.strptime(clock_in, "%H:%M")
                clock_out_time = datetime.strptime(clock_out, "%H:%M")
                actual_total_minutes = (clock_out_time.hour * 60 + clock_out_time.minute) - (clock_in_time.hour * 60 + clock_in_time.minute)
                # Calculate balance
                balance = actual_total_minutes - expected_total_minutes
            # Write entry to database
            thread_add_entry = spawn_loading_spinner_thread(f"Adding new entry", f"Successfully added new entry.\n", f"Failed to add new entry.")
            _threads.append(thread_add_entry)
            # Create a connection to the DuckDB database
            connection = get_db_connection()
            # Insert the new entry into the database
            query = """
                INSERT INTO times (uuid, date, day_of_week, event_type, clock_in, clock_out, break_time_minutes, expected_total_minutes, expected_total_minutes_work_default, actual_total_minutes, day_balance_minutes, created_at, updated_at)
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
            """
            connection.execute(query,
                [
                    str(uuid.uuid4()),
                    date,
                    day_of_week,
                    event_type,
                    clock_in,
                    clock_out,
                    int(_config["daily_break_minutes"]),
                    int(expected_total_minutes),
                    int(_config["expected_daily_total_minutes"]),
                    int(actual_total_minutes),
                    int(balance)
                ]
            )
            # Close the connection
            connection.close()
            terminate_loading_spinner_thread(thread_add_entry, True)
            print()
            # Prompt for another entry
            should_exit = not prompt(
                input_type = "confirm",
                message = f"Do you want to add another entry?",
                default = False,
                mandatory = True,
                wrap_lines = True
            )
    except Exception as e:
        raise e
    
def edit_entry() -> None:
    """
    Edits an existing entry in the database.

    Args:
        None
    
    Returns:
        None
    """
    try:
        should_exit = False
        while not should_exit:
            # Print header
            clear_terminal()
            print_title()
            print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ EDIT ENTRY{bcolors.ENDC}\n")
            # Get all existing entries
            existing_entries = get_existing_entries()
            # Get all existing dates from database entries formatted as YYYY-MM-DD
            existing_dates = sorted([date.strftime("%Y-%m-%d") for date in existing_entries["date"].tolist()], reverse=True)
            # No dates available -> nothing to edit
            if len(existing_dates) == 0:
                print(f"{bcolors.WARNING}→ No entries available for editing. Most likely no entries have been made yet, once entries exist, they will be shown here.{bcolors.ENDC}")
                should_exit = True
                prompt_continue()
                continue
            # Prompt for date selection from list of entries
            date = prompt(
                input_type = "fuzzy",
                message = "Select an entry:",
                choices =  [
                    Choice(date) for date in existing_dates
                ],
                default = existing_dates[0] if len(existing_dates) > 0 else "",
                mandatory = True,
                wrap_lines = True,
                validate = lambda text: len(text) == 10 and datetime.strptime(text, "%Y-%m-%d"),
                invalid_message = "Start date must be in format YYYY-MM-DD.",
                border = True,
                cycle = True
            )
            # Get selected entry by date
            entry = existing_entries[existing_entries["date"] == date].iloc[0]
            # Print entry details
            clear_terminal()
            print_title()
            show_entry(entry)
            # Prompt for confirmation to edit entry
            confirmed_edit = prompt(
                input_type = "confirm",
                message = f"Are you sure you want to edit this entry?",
                mandatory = True,
                wrap_lines = True
            )
            if confirmed_edit:
                clear_terminal()
                print_title()
                print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ EDIT ENTRY{bcolors.ENDC}\n")
                event_type = prompt(
                    input_type = "select",
                    message = "Select an event type:",
                    choices = [
                        "Work",
                        "Vacation",
                        "Public / Company Holiday",
                        "Sick Leave",
                        "Overtime Compensation",
                    ],
                    default = "Work",
                    instruction = f"(Current value: {entry['event_type']})",
                    mandatory = True,
                    wrap_lines = True,
                    show_cursor = False,
                    border = True
                )
                # Set default values
                clock_in = None
                clock_out = None
                actual_total_minutes = None
                balance = None 
                expected_total_minutes = 0
                # Overtime compensation specifics
                if event_type == "Overtime Compensation":
                    balance = -entry["expected_total_minutes_work_default"]
                    expected_total_minutes = entry["expected_total_minutes_work_default"]
                # Work specifics
                if event_type == "Work":
                    clock_in = prompt(
                        input_type = "text",
                        message = "Enter clock in time (HH:MM): ",
                        default = entry["clock_in"],
                        mandatory = True,
                        wrap_lines = True,
                        validate = lambda text: len(text) == 5 and datetime.strptime(text, "%H:%M") >= datetime.strptime("00:00", "%H:%M") and datetime.strptime(text, "%H:%M") <= datetime.strptime("23:59", "%H:%M"),
                        invalid_message = "Clock in time must be in format HH:MM, between 00:00 and 23:59.",
                    )
                    clock_out = prompt(
                        input_type = "text",
                        message = "Enter clock out time (HH:MM): ",
                        default = entry["clock_out"],
                        mandatory = True,
                        wrap_lines = True,
                        validate = lambda text: len(text) == 5 and datetime.strptime(text, "%H:%M") > datetime.strptime(clock_in, "%H:%M") and datetime.strptime(text, "%H:%M") >= datetime.strptime("00:00", "%H:%M") and datetime.strptime(text, "%H:%M") <= datetime.strptime("23:59", "%H:%M"),
                        invalid_message = "Clock out time must be in format HH:MM, between 00:00 and 23:59, and after clock in time.",
                    )
                    expected_total_minutes = entry["expected_total_minutes_work_default"]
                    # Get difference between clock in and clock out
                    clock_in_time = datetime.strptime(clock_in, "%H:%M")
                    clock_out_time = datetime.strptime(clock_out, "%H:%M")
                    actual_total_minutes = (clock_out_time.hour * 60 + clock_out_time.minute) - (clock_in_time.hour * 60 + clock_in_time.minute)
                    # Calculate balance
                    balance = actual_total_minutes - entry["expected_total_minutes"]
                # Update entry in database
                thread_edit_entry = spawn_loading_spinner_thread(f"Updating entry", f"Successfully updated entry.\n", f"Failed to update entry.")
                connection = get_db_connection()
                query = """
                    UPDATE times
                    SET 
                        event_type = ?,
                        clock_in = ?,
                        clock_out = ?,
                        expected_total_minutes = ?,
                        actual_total_minutes = ?,
                        day_balance_minutes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE date = ?;
                """
                connection.execute(query, 
                    [
                        event_type,
                        clock_in,
                        clock_out,
                        int(expected_total_minutes),
                        int(actual_total_minutes),
                        int(balance),
                        date
                    ]
                )
                # Close the connection
                connection.close()
                terminate_loading_spinner_thread(thread_edit_entry, True)
                print()
                # prompt for another entry               
                should_exit = not prompt(
                    input_type = "confirm",
                    message = f"Do you want to edit another entry?",
                    default = False,
                    mandatory = True,
                    wrap_lines = True
                )
    except Exception as e:
        raise e

def view_entry() -> None:
    """
    Views an existing entry in the database.

    Args:
        None
    
    Returns:
        None
    """
    try:
        # Print title
        clear_terminal()
        print_title()
        print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ VIEW ENTRY{bcolors.ENDC}\n")
        # Get all existing entries
        existing_entries = get_existing_entries()
        should_exit = False
        while not should_exit:
            # Print header
            clear_terminal()
            print_title()
            print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ VIEW ENTRY{bcolors.ENDC}\n")
            # Get all existing dates
            existing_dates = sorted([date.strftime("%Y-%m-%d") for date in existing_entries["date"].tolist()], reverse=True)
            # No dates available -> nothing to view
            if len(existing_dates) == 0:
                print(f"{bcolors.WARNING}→ No entries available for viewing. Most likely no entries have been made yet, once entries exist, they will be shown here.{bcolors.ENDC}")
                should_exit = True
                prompt_continue()
                continue
            # Prompt for date selection from entries
            date = prompt(
                input_type = "fuzzy",
                message = "Select an entry:",
                choices =  [
                    Choice(date) for date in existing_dates
                ],
                default = existing_dates[0],
                mandatory = True,
                wrap_lines = True,
                validate = lambda text: len(text) == 10 and datetime.strptime(text, "%Y-%m-%d"),
                invalid_message = "Start date must be in format YYYY-MM-DD.",
                border = True,
                cycle = True
            )
            # Get entry by date
            entry = existing_entries[existing_entries["date"] == date].iloc[0]
            # Print entry details
            clear_terminal()
            print_title()
            show_entry(entry)
            # Prompt for confirmation to view another entry
            should_exit = not prompt(
                input_type = "confirm",
                message = f"Do you want to view another entry?",
                default = False,
                mandatory = True,
                wrap_lines = True
            )
    except Exception as e:
        raise e
    
def show_stats() -> None:
    """
    Shows statistics of the existing entries in the database.
    
    Args:
        None
    
    Returns:
        None
        
    """
    try:
        # Print header
        clear_terminal()
        print_title()
        print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ SHOW STATS{bcolors.ENDC}\n")
        # Get all existing entries
        existing_entries = get_existing_entries()
        # Get all existing dates formatted as YYYY-MM-DD from existing entries
        existing_dates = sorted([date.strftime("%Y-%m-%d") for date in existing_entries["date"].tolist()], reverse=True)
        # Get missing dates, i.e. dates between start date and today that are not in the database
        missing_entries = [
            date.strftime("%Y-%m-%d") for date in (
                datetime.strptime(_config["start_date"], "%Y-%m-%d") + timedelta(days=i) for i in range((datetime.now() - datetime.strptime(_config["start_date"], "%Y-%m-%d")).days + 1)
            )
            if date.strftime("%A") in _config["work_days"] and date.strftime("%Y-%m-%d") not in set(existing_dates)
        ]
        # Entries by category
        entries_by_category_work = len(existing_entries[existing_entries["event_type"] == "Work"])
        entries_by_category_work_percentage = round(entries_by_category_work / len(existing_entries) * 100)
        entries_by_category_vacation = len(existing_entries[existing_entries["event_type"] == "Vacation"])
        entries_by_category_vacation_percentage = round(entries_by_category_vacation / len(existing_entries) * 100)
        entries_by_category_public_holiday = len(existing_entries[existing_entries["event_type"] == "Public / Company Holiday"])
        entries_by_category_public_holiday_percentage = round(entries_by_category_public_holiday / len(existing_entries) * 100)
        entries_by_category_sick_leave = len(existing_entries[existing_entries["event_type"] == "Sick Leave"])
        entries_by_category_sick_leave_percentage = round(entries_by_category_sick_leave / len(existing_entries) * 100)
        entries_by_category_overtime_compensation = len(existing_entries[existing_entries["event_type"] == "Overtime Compensation"])
        entries_by_category_overtime_compensation_percentage = round(entries_by_category_overtime_compensation / len(existing_entries) * 100)
        # Total balance 
        total_balance = existing_entries['day_balance_minutes'].sum()
        # Total times
        total_time_worked = existing_entries['actual_total_minutes'].sum()
        total_time_expected = existing_entries['expected_total_minutes'].sum()
        # Print statistics
        print()
        print(f"{bcolors.ORANGE}‣ User:                  {bcolors.ENDC}{bcolors.OKCYAN}{_config['name']}{bcolors.ENDC}")
        print(" ------------------------" + "-" * len(_config['name']))
        print(f"{bcolors.ORANGE}‣ Total Entries:         {bcolors.ENDC}{bcolors.OKGREEN if len(missing_entries) == 0 else bcolors.ORANGE}{len(existing_entries)}{bcolors.ENDC} since {bcolors.WARNING}{_config['start_date']}{bcolors.ENDC}")
        print(f"{bcolors.ORANGE}‣ Missing Entries:       {bcolors.ENDC}{bcolors.FAIL if len(missing_entries) != 0 else ""}{len(missing_entries)}{bcolors.ENDC}")
        print(f"{bcolors.ORANGE}‣ Entries by Category    {bcolors.ENDC}")
        print(f"{bcolors.ORANGE}   - Work:               {bcolors.ENDC}{entries_by_category_work} ({entries_by_category_work_percentage}%)")
        print(f"{bcolors.ORANGE}   - Vacation:           {bcolors.ENDC}{entries_by_category_vacation} ({entries_by_category_vacation_percentage}%)")
        print(f"{bcolors.ORANGE}   - Public Holiday:     {bcolors.ENDC}{entries_by_category_public_holiday} ({entries_by_category_public_holiday_percentage}%)")
        print(f"{bcolors.ORANGE}   - Sick Leave:         {bcolors.ENDC}{entries_by_category_sick_leave} ({entries_by_category_sick_leave_percentage}%)")
        print(f"{bcolors.ORANGE}   - Overtime Comp.:     {bcolors.ENDC}{entries_by_category_overtime_compensation} ({entries_by_category_overtime_compensation_percentage}%)")
        print(" ------------------------" + "-" * len(_config['name']))
        print(f"{bcolors.ORANGE}‣ Total Balance:         {bcolors.ENDC}{bcolors.OKGREEN if total_balance >= 0 else bcolors.FAIL}{total_balance // 60}h {total_balance % 60}min")
        print(f"{bcolors.ORANGE}‣ Total Time Worked:     {bcolors.ENDC}{convert_minutes(total_time_worked)}")
        print(f"{bcolors.ORANGE}‣ Total Time Expected:   {bcolors.ENDC}{convert_minutes(total_time_expected)}")
        # Prompt for showing missing entries, if any are available
        if len(missing_entries) > 0:
            print()
            show_missing_dates = prompt(
                input_type = "confirm",
                message = f"Show missing entries ({len(missing_entries)})?",
                default = False,
                mandatory = True,
                wrap_lines = True
            )
            if show_missing_dates:
                print(f"{bcolors.ORANGE}‣ Missing Entries: {bcolors.ENDC}")
                for date in missing_entries:
                    print(f"   - {date}")
        prompt_continue()
    except Exception as e:
        raise e
    
def edit_config() -> None:
    """
    Edits the user configuration.

    Args:
        None
    
    Returns:
        None
    """
    try:
        # Print header
        clear_terminal()
        print_title()
        print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ EDIT CONFIG{bcolors.ENDC}\n")
        # Show existing config
        show_config()
        # Prompt for confirmation to edit config
        confirmed_edit = prompt(
            input_type = "confirm",
            message = f"Do you want to edit this configuration?",
            mandatory = True,
            wrap_lines = True
        )
        if confirmed_edit:
            # Print header
            clear_terminal()
            print_title()
            print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ EDIT CONFIG{bcolors.ENDC}\n")
            # Edit config with default values
            config = create_config(_config)
            # Write config to json file
            save_config(config)
            print(f"{bcolors.OKGREEN}✔ Successfully updated user configuration.{bcolors.ENDC}")
            # Load and validate config
            load_validate_config()
            prompt_continue()
    except Exception as e:
        raise e

def export_stats() -> None:
    """
    Exports the statistics to a file.

    Args:
        None
    
    Returns:
        None
    """
    try:
        # Print header
        clear_terminal()
        print_title()
        print(f"{bcolors.OKCYAN}{bcolors.UNDERLINE}→ EXPORT STATS{bcolors.ENDC}\n")
        thread_export_stats = spawn_loading_spinner_thread(f"Exporting stats", f"Successfully exported stats.\n", f"Failed to export stats.")
        _threads.append(thread_export_stats)
        # Get all existing entries
        existing_entries = get_existing_entries()
        # Get all existing dates formatted as YYYY-MM-DD from existing entries
        existing_dates = sorted([date.strftime("%Y-%m-%d") for date in existing_entries["date"].tolist()], reverse=True)
        # Get missing dates between start date and today that are not in the database
        missing_entries = [
            date.strftime("%Y-%m-%d") for date in (
                datetime.strptime(_config["start_date"], "%Y-%m-%d") + timedelta(days=i) for i in range((datetime.now() - datetime.strptime(_config["start_date"], "%Y-%m-%d")).days + 1)
            )
            if date.strftime("%A") in _config["work_days"] and date.strftime("%Y-%m-%d") not in set(existing_dates)
        ]
        # Prepare data for export
        # Entries --- --- --- --- ---
        existing_entries['date'].apply(lambda x: x.strftime("%Y-%m-%d"))
        existing_entries = existing_entries.sort_values(by=['date'], ascending=True)
        existing_entries = existing_entries.drop(columns=['uuid', 'day_of_week', 'expected_total_minutes_work_default', 'created_at', 'updated_at'])
        existing_entries = existing_entries.rename(columns={
            'date': 'Date',
            'event_type': 'Event Type',
            'clock_in': 'Clock In',
            'clock_out': 'Clock Out',
            'break_time_minutes': 'Break Time (minutes)',
            'expected_total_minutes': 'Expected Total (minutes)',
            'actual_total_minutes': 'Actual Total (minutes)',
            'day_balance_minutes': 'Balance (minutes)'
        })
        # Summary --- --- --- --- ---
        total_balance = existing_entries['Balance (minutes)'].sum()
        summary = pd.DataFrame({
            'Name': [_config['name']],
            'Start Date': [_config['start_date']],
            'Work Days': [", ".join(_config['work_days'])],
            'Weekly Work (hours)': [_config['weekly_work_minutes'] / 60],
            'Daily Break (minutes)': [_config['daily_break_minutes']],
            'Total Entries': [len(existing_entries)],
            'Missing Entries': [len(missing_entries)],
            'Total Balance (hours)': [f"{total_balance // 60}h {total_balance % 60}min"],
            'Timesheet Generated': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        summary = summary.transpose()
        # Export to Excel
        with pd.ExcelWriter(os.path.join(OUT_PATH, f"timesheet_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.xlsx"), engine='openpyxl') as writer:
            summary.to_excel(writer, sheet_name='Summary', header=False, index=True)
            existing_entries.to_excel(writer, sheet_name='Entries', index=False)
        terminate_loading_spinner_thread(thread_export_stats, True)
        prompt_continue()
    except Exception as e:
        raise e

def main_menu_loop() -> None:
    """
    Trigger main menu loop.
    Displays the main menu and handles user input and branches into the appropriate functions.

    Args:
        None
    
    Returns:
        None
    """
    try:
        should_exit = False
        while not should_exit:
            clear_terminal()
            print_title()
            selection = prompt (
                input_type = "select",
                message = "Select an option:",
                choices = [
                    Choice("ENTRY_NEW", name="Entry - New"),
                    Choice("ENTRY_EDIT", name="Entry - Edit"),
                    Choice("ENTRY_VIEW", name="Entry - View" ),
                    Separator(),
                    Choice("STATS_SHOW", name="Stats - Show"),
                    Choice("STATS_EXPORT", name="Stats - Export"),
                    Separator(),
                    Choice("CONFIG_EDIT", name="Config - Edit"),
                    Separator(),
                    # Choice("DANGER", name="DANGER ZONE"),
                    # Separator(),
                    Choice(f"EXIT", name="Exit")
                ],
                mandatory = True,
                wrap_lines = True,
                show_cursor = False,
                border = True,
            )
            match selection:
                case "ENTRY_NEW":
                    add_entry()
                case "ENTRY_EDIT":
                    edit_entry()
                case "ENTRY_VIEW":
                    view_entry()
                case "STATS_SHOW":
                    show_stats()
                case "STATS_EXPORT":
                    export_stats()
                case "CONFIG_EDIT":
                    edit_config()
                # @TODO: Implement DANGER ZONE (db imports, exports, deletes, etc.)
                # case "DANGER":
                #     clear_terminal()
                #     print_title()
                #     print(f"{bcolors.WARNING}→ COMING SOON...{bcolors.ENDC}")
                #     prompt_continue()
                case "EXIT":
                    should_exit = True
                case _:
                    print(f"{bcolors.FAIL}✗ Invalid selection.{bcolors.ENDC}")
        return should_exit
    except Exception as e:
        raise e

if __name__ == "__main__":
    try:
        # CLEAR TERMINAL
        clear_terminal()
        # PRINT TITLE
        print_title()
        # INITIALIZE DATABASE & CONFIGURATION
        initialize()
        # PRINT MAIN MENU
        main_menu_loop()
    # Catch CTRL + C and exit gracefully
    except KeyboardInterrupt:
        terminate_threads(_threads)
        graceful_exit(success=False)
    # Catch all other exceptions
    except Exception as e:
        terminate_threads(_threads)
        print(f"{bcolors.FAIL}\n✗ Check {LOG_PATH} for additional details.{bcolors.ENDC}")
        log_error_to_file(traceback.format_exc())
        graceful_exit(success=False)
    # EXIT APPLICATION
    finally:
        graceful_exit(success=True)