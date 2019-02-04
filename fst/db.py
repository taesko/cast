import sqlite3
import os

from fst.trace import trace
from fst.config import CONFIG

# TODO load dynamically and guess current app
DB_PATH = CONFIG['fstctl']['db_path']

exists = os.path.exists(DB_PATH)
conn = sqlite3.connect(DB_PATH)
conn.set_trace_callback(trace)
conn.row_factory = sqlite3.Row
trace("Database path is: %s", DB_PATH)
if not exists:
    trace("Database does not exist. Creating...")
    cursor = conn.cursor()
    with open("db/schema.sql") as f:
        cursor.executescript(f.read())


def connect(path):
    return conn
