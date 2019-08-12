import sqlite3
import os

dbpath = os.path.expanduser('~/.cache/tgficbot.db')

conn = sqlite3.connect(dbpath)
cursor = conn.cursor()

cursor.execute(
    "CREATE TABLE IF NOT EXISTS channels (id INTERGER PRIMARY KEY, name varchar(101));"
)
