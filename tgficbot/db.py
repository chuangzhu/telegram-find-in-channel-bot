import sqlite3
import os
import re
from telethon.tl import types
from typing import List
from . import states


def first_fetchall(sqlresult: List[tuple]):
    return [x[0] for x in sqlresult]


class Database:
    def __init__(self, dbpath):
        conn = sqlite3.connect(dbpath)
        conn.create_function('REGEXP', 2,
                             lambda p, s: re.search(p, s) is not None)
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
                selected_id INTEGER,
                latest_search TEXT,
                lang TEXT DEFAULT follow NOT NULL
            );
        """)
        # A junction table to handle many-to-many relationship between channels and admins
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels_admins (
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL
            );
        """)
        try:
            cursor.execute('SELECT lang FROM users')
        except sqlite3.OperationalError:
            cursor.execute(
                'ALTER TABLE users ADD lang TEXT DEFAULT follow NOT NULL')
        try:
            cursor.execute('SELECT latest_search FROM users')
        except sqlite3.OperationalError:
            cursor.execute('ALTER TABLE users ADD latest_search TEXT')
        self.conn = conn
        self.cursor = cursor

    def save_user(self, user: types.User):
        self.cursor.execute(
            'INSERT OR IGNORE INTO users (user_id, username, state) VALUES (?, ?, ?)',
            (user.id, user.username, states.Empty))
        self.clear_user_state(user)

    def get_user_state(self, user: types.User):
        self.cursor.execute('SELECT state FROM users WHERE user_id = ?',
                            (user.id, ))
        fetched = self.cursor.fetchone()
        return None if fetched is None else states.State(fetched[0])

    def set_user_state(self, user: types.User, state: states.State):
        self.cursor.execute('UPDATE users SET state = ? WHERE user_id = ?',
                            (state.numerator, user.id))
        self.conn.commit()

    def clear_user_state(self, user: types.User):
        self.set_user_state(user, state=states.Empty)

    def check_channel_saved(self, channel: types.Channel):
        self.cursor.execute('SELECT * FROM channels WHERE channel_id = ?',
                            (channel.id, ))
        return self.cursor.fetchone() is not None

    def save_channel(self, channel: types.Channel):
        self.cursor.execute(
            'INSERT INTO channels (channel_id, username, title) VALUES (?, ?, ?)',
            (channel.id, channel.username, channel.title))

    def save_channel_admin_relation(self, channel_id: int, admin: types.User):
        if admin.bot:
            return
        self.cursor.execute(
            'INSERT INTO channels_admins (channel_id, user_id) VALUES (?, ?)',
            (channel_id, admin.id))

    def get_user_owned_channels(self, user: types.User) -> List[int]:
        self.cursor.execute(
            'SELECT channel_id FROM channels_admins WHERE user_id = ?',
            (user.id, ))
        sqlresult = self.cursor.fetchall()
        return first_fetchall(sqlresult)

    def get_channel_admins(self, channel_id: int):
        self.cursor.execute(
            'SELECT user_id FROM channels_admins WHERE channel_id = ?',
            (channel_id, ))
        sqlresult = self.cursor.fetchall()
        # Return ids only
        return first_fetchall(sqlresult)

    def is_channel_admins(self, user: types.User, channel_id: int) -> bool:
        return user.id in self.get_channel_admins(channel_id)

    def get_channel_title(self, channel_id: int):
        self.cursor.execute('SELECT title FROM channels WHERE channel_id = ?',
                            (channel_id, ))
        return self.cursor.fetchone()[0]

    def get_channel_name(self, channel_id: int):
        self.cursor.execute(
            'SELECT username FROM channels WHERE channel_id = ?',
            (channel_id, ))
        return self.cursor.fetchone()[0]

    def match_user_owned_channels_with_pattern(self, user: types.User,
                                               pattern: str) -> List[int]:
        sqlquery = """
            SELECT channel_id FROM channels
            WHERE channel_id IN (
                SELECT channel_id FROM channels_admins WHERE user_id = ?
            ) AND {0} LIKE ?
            ORDER BY {0}
        """
        # Find in channels names, then channel titles. The priority matters.
        self.cursor.execute(sqlquery.format('username'),
                            (user.id, f'%{pattern}%'))
        matched_ids = first_fetchall(self.cursor.fetchall())
        self.cursor.execute(sqlquery.format('title'),
                            (user.id, f'%{pattern}%'))
        matched_ids += first_fetchall(self.cursor.fetchall())
        # Remove duplicates
        matched_ids = list(dict.fromkeys(matched_ids))
        return matched_ids

    def get_channel_id_from_name(self, user: types.User,
                                 channel_name: str) -> int:
        self.cursor.execute(
            """
            SELECT channel_id FROM channels
            WHERE channel_id IN (
                SELECT channel_id FROM channels_admins WHERE user_id = ?
            ) AND username = ?
        """, (user.id, channel_name))
        sqlresult = self.cursor.fetchone()
        return sqlresult and sqlresult[0]

    def save_message(self, message: types.Message):
        if not isinstance(message, types.Message):
            return
        if (message.message is None) or (len(message.message) == 0):
            return
        self.cursor.execute(
            'INSERT INTO messages (message_id, channel_id, content) VALUES (?, ?, ?)',
            (message.id, message.to_id.channel_id, message.message))

    def update_message(self, message: types.Message):
        self.cursor.execute(
            'SELECT rowid FROM messages WHERE message_id=? AND channel_id=?',
            (message.id, message.to_id.channel_id))
        sqlresult = self.cursor.fetchone()
        if sqlresult is None:
            self.cursor.execute(
                'INSERT INTO messages (message_id, channel_id, content) VALUES (?, ?, ?)',
                (message.id, message.to_id.channel_id, message.message))
        else:
            self.cursor.execute('UPDATE messages SET content=? WHERE rowid=?',
                                (message.message, sqlresult[0]))

    def find_in_messages(self, channel_id: int, pattern: str):
        self.cursor.execute(
            'SELECT message_id FROM messages WHERE channel_id = ? AND content LIKE ?',
            (channel_id, f'%{pattern}%'))
        messages = self.cursor.fetchall()
        message_ids = first_fetchall(messages)
        return message_ids

    def find_in_messages_glob(self, channel_id: int, pattern: str):
        self.cursor.execute(
            'SELECT message_id FROM messages WHERE channel_id = ? AND content GLOB ?',
            (channel_id, f'*{pattern}*'))
        messages = self.cursor.fetchall()
        message_ids = first_fetchall(messages)
        return message_ids

    def find_in_messages_regexp(self, channel_id: int, pattern: str):
        self.cursor.execute(
            'SELECT message_id FROM messages WHERE channel_id = ? AND content REGEXP ?',
            (channel_id, pattern))
        messages = self.cursor.fetchall()
        message_ids = first_fetchall(messages)
        return message_ids

    def set_user_selected(self, user_id: int, channel_id: int):
        self.cursor.execute('UPDATE users SET selected_id=? WHERE user_id=?',
                            (channel_id, user_id))
        self.conn.commit()

    def get_user_selected(self, user_id: int):
        self.cursor.execute('SELECT selected_id FROM users WHERE user_id=?',
                            (user_id, ))
        return self.cursor.fetchone()[0]

    def set_user_lang(self, user_id: int, langcode: str):
        self.cursor.execute('UPDATE users SET lang=? WHERE user_id=?',
                            (langcode, user_id))

    def get_user_lang(self, user_id: int):
        self.cursor.execute('SELECT lang FROM users WHERE user_id=?',
                            (user_id, ))
        return self.cursor.fetchone()[0]

    def get_latest_search(self, user_id: int):
        self.cursor.execute('SELECT latest_search FROM users WHERE user_id=?',
                            (user_id, ))
        return self.cursor.fetchone()[0]

    def set_latest_search(self, user_id: int, latest_search: str):
        self.cursor.execute('UPDATE users SET latest_search=? WHERE user_id=?',
                            (latest_search, user_id))

    def clear_latest_search(self, user_id: int):
        self.set_latest_search(user_id, None)
