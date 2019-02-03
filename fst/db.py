import sqlite3
import os

from fst.trace import trace

HOME_DIR = os.environ.get("HOME")
if HOME_DIR == "/":
    HOME_DIR = "/var/"
    DB_PATH = os.path.join(HOME_DIR, "fst.db")
else:
    DB_PATH = os.path.join(HOME_DIR, ".fst.db")

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
