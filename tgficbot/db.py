import sqlite3
import os
from telethon.tl import types
from tgficbot import states

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
        content TEXT NOT NULL
    );
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        state INTEGER NOT NULL,
        selected_id INTEGER
    );
""")
# A junction table to handle many-to-many relationship between channels and admins
cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels_admins (
        channel_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL
    );
""")


def save_user(user: types.User):
    cursor.execute(
        'INSERT OR REPLACE INTO users (user_id, username, state) VALUES (?, ?, ?)',
        (user.id, user.username, states.Empty))


def get_user_state(user: types.User):
    cursor.execute('SELECT state FROM users WHERE user_id = ?', (user.id, ))
    fetched = cursor.fetchone()
    return None if fetched is None else states.State(fetched[0])


def set_user_state(user: types.User, state: states.State):
    cursor.execute('UPDATE users SET state = ? WHERE user_id = ?',
                   (state.numerator, user.id))
    conn.commit()


def clear_user_state(user: types.User):
    set_user_state(user, state=states.Empty)


def check_channel_saved(channel: types.Channel):
    cursor.execute('SELECT * FROM channels WHERE channel_id = ?',
                   (channel.id, ))
    if cursor.fetchone() is not None:
        return True
    return False


def save_channel(channel: types.Channel):
    cursor.execute(
        'INSERT INTO channels (channel_id, username, title) VALUES (?, ?, ?)',
        (channel.id, channel.username, channel.title))


def save_channel_admin_relation(channel_id: int, admin: types.User):
    if admin.bot:
        return
    cursor.execute(
        'INSERT INTO channels_admins (channel_id, user_id) VALUES (?, ?)',
        (channel_id, admin.id))


def _sqlresult2id(result):
    return result[0]


def get_user_owned_channels(user: types.User):
    cursor.execute('SELECT channel_id FROM channels_admins WHERE user_id = ?',
                   (user.id, ))
    sqlresult = cursor.fetchall()
    return [x[0] for x in sqlresult]


def get_channel_admins(channel_id: types.Channel):
    cursor.execute('SELECT user_id FROM channels_admins WHERE channel_id = ?',
                   (channel_id, ))
    sqlresult = cursor.fetchall()
    return map(_sqlresult2id, sqlresult)


def get_channel_title(channel_id: int):
    cursor.execute('SELECT title FROM channels WHERE channel_id = ?',
                   (channel_id, ))
    return cursor.fetchone()[0]


def save_message(message: types.Message):
    if not isinstance(message, types.Message):
        return
    if (message.message is None) or (len(message.message) == 0):
        return
    cursor.execute(
        'INSERT INTO messages (message_id, channel_id, content) VALUES (?, ?, ?)',
        (message.id, message.to_id.channel_id, message.message))


def find_in_messages(channel_id: int, pattern: str):
    cursor.execute(
        'SELECT message_id, content FROM messages WHERE channel_id = ?',
        (channel_id, ))
    messages = cursor.fetchall()

    def filter_none(m):
        if m[1] is None:
            return False
        return True

    messages = filter(filter_none, messages)
    matched_messages = [m for m in messages if m[1].find(pattern) != -1]
    message_ids = [m[0] for m in matched_messages]
    return message_ids


def set_user_selected(user_id: int, channel_id: int):
    cursor.execute('UPDATE users SET selected_id=? WHERE user_id=?',
                   (channel_id, user_id))
    conn.commit()


def get_user_selected(user_id: int):
    cursor.execute('SELECT selected_id FROM users WHERE user_id=?',
                   (user_id, ))
    return cursor.fetchone()[0]
