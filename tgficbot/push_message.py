#!/usr/bin/env python3

import telethon
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import BadRequestError, rpc_errors_dict
from pathlib import Path
import os
import argparse
import configparser
from .db import Database

argp = argparse.ArgumentParser(description='Push notifications.')
argp.add_argument('content', type=str, help='content to push')
argp.add_argument('--config',
                  type=str,
                  default=os.path.expanduser('~/.config/tgficbot.cfg'),
                  help='specify config file')
argp.add_argument('--dbpath',
                  type=str,
                  default=os.path.expanduser('~/.cache/'),
                  help='specify directory to store databases')
args = argp.parse_args()

config = configparser.ConfigParser()
config.read(args.config)

db = Database(Path(args.dbpath) / 'tgficbot.db')

session_db = str(Path(args.dbpath) / 'bot.session')
api_id = config['api']['id']
api_hash = config['api']['hash']

with TelegramClient(session_db, api_id, api_hash) as client:
    client.start(bot_token=config['bot']['token'])
    db.cursor.execute('SELECT user_id FROM users')
    fetched = db.cursor.fetchall()
    for user in fetched:
        try:
            client.send_message(user[0], args.content)
        except BadRequestError as e:
            print(f'{user[0]} {str(e)}', file=os.sys.stderr)
