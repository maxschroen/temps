import pathlib
import os

VERSION_NUMBER = "0.0.1"

RES_PATH = os.path.join(f"{pathlib.Path(__file__).parent.parent.resolve()}", "res")
DB_FILE_NAME = "temps.duckdb"
USER_CONFIG_FILE_NAME = "user_config.json"
LOG_PATH = os.path.join(f"{pathlib.Path(__file__).parent.parent.resolve()}", "logs")
OUT_PATH = os.path.join(f"{pathlib.Path(__file__).parent.parent.resolve()}", "out")
GOLD_TABLE_SCHEMA = [('uuid', 'VARCHAR', 'NO', 'PRI', None, None), ('date', 'DATE', 'NO', 'UNI', None, None), ('day_of_week', 'VARCHAR', 'NO', None, None, None), ('event_type', 'VARCHAR', 'NO', None, None, None), ('clock_in', 'VARCHAR', 'YES', None, None, None), ('clock_out', 'VARCHAR', 'YES', None, None, None), ('break_time_minutes', 'INTEGER', 'YES', None, None, None), ('expected_total_minutes', 'INTEGER', 'YES', None, None, None), ('expected_total_minutes_work_default', 'INTEGER', 'YES', None, None, None), ('actual_total_minutes', 'INTEGER', 'YES', None, None, None), ('day_balance_minutes', 'INTEGER', 'YES', None, None, None), ('created_at', 'TIMESTAMP', 'NO', None, None, None), ('updated_at', 'TIMESTAMP', 'NO', None, None, None)]