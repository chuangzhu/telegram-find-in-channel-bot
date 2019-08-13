import sqlite3
import os
from telethon.tl import types

dbpath = os.path.expanduser('~/.cache/tgficbot.db')

conn = sqlite3.connect(dbpath)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        channel_id INTEGER PRIMARY KEY NOT NULL,
        username TEXT,
        title TEXT NOT NULL
    );
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL,
        content TEXT
    );
""")


def check_channel_exist(full_channel: types.ChannelFull):
    channel = full_channel.chats[0]
    cursor.execute('SELECT * FROM channels WHERE channel_id = ?',
                   (channel.id, ))
    if cursor.fetchone() is not None:
        return


def save_channel(full_channel: types.ChannelFull):
    channel = full_channel.chats[0]
    cursor.execute(
        'INSERT INTO channels (channel_id, username, title) VALUES (?, ?, ?)',
        (channel.id, channel.username, channel.title))


def save_message(message: types.Message):
    if not isinstance(message, types.Message):
        return
    if message.message is None:
        return
    cursor.execute(
        'INSERT INTO messages (message_id, channel_id, content) VALUES (?, ?, ?)',
        (message.id, message.to_id.channel_id, message.message))


def find_in_messages(channel_id: int, pattern: str):
    cursor.execute('SELECT * FROM messages WHERE channel_id = ?',
                   (channel_id, ))
    messages = cursor.fetchall()
    def filter_none(m):
        if m[3] is None:
            return False
        return True
    messages = filter(filter_none, messages)
    matched_messages = [m for m in messages if m[3].find(pattern) != -1]
    message_ids = [m[1] for m in matched_messages]
    return message_ids

