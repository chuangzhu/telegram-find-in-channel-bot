from telethon import TelegramClient
from telethon.events import NewMessage, CallbackQuery, MessageEdited
from telethon.events import StopPropagation
from telethon.tl import types, functions
from telethon.tl.custom import Button
from telethon.errors.rpcerrorlist import ChannelPrivateError

import os
import signal
from pathlib import Path
import logging
import asyncio
import argparse
import configparser

from . import states
from .db import Database
from . import i18n

argp = argparse.ArgumentParser(description='Start Telegram FindInChannelBot.')
argp.add_argument('--config',
                  type=str,
                  default=os.path.expanduser('~/.config/tgficbot.cfg'),
                  help='specify config file')
argp.add_argument('--dbpath',
                  type=str,
                  default=os.path.expanduser('~/.cache/'),
                  help='specify directory to store databases')
args = argp.parse_args()

db = Database(Path(args.dbpath) / 'tgficbot.db')
onstate = states.StateHandler(db)
withi18n = i18n.I18nHandler(db)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

config = configparser.ConfigParser()
config.read(args.config)

bot = TelegramClient(
    str(Path(args.dbpath) / 'bot.session'), config['api']['id'],
    config['api']['hash']).start(bot_token=config['bot']['token'])


@bot.on(NewMessage(pattern='/start'))
@withi18n
async def start_command_handler(event: NewMessage.Event, strings):
    if not event.is_private:
        return
    await event.respond(strings.greeting)
    chat = await event.get_chat()
    db.save_user(chat)
    db.conn.commit()
    raise StopPropagation


@bot.on(NewMessage(pattern='/add'))
@onstate(states.Empty)
@withi18n
async def add_command_handler(event, strings):
    await event.respond(strings.add_guide)
    user = await event.get_chat()
    db.set_user_state(user, states.AddingAChannel)


@bot.on(NewMessage(pattern='/cancel'))
@withi18n
async def cancel_command_handler(event: NewMessage.Event, strings):
    user = await event.get_chat()
    current_state = db.get_user_state(user)
    if current_state == states.Empty:
        return
    db.clear_user_state(user)
    db.set_user_selected(user.id, None)
    await event.respond(strings.cancel)


@bot.on(NewMessage())
@onstate(states.AddingAChannel)
@withi18n
async def adding_forward_handler(event: NewMessage.Event, strings):
    user = await event.get_chat()

    if event.message.fwd_from is None:
        await event.respond(strings.add_not_forward)
        return
    if event.message.fwd_from.channel_id is None:
        await event.respond(strings.add_forward_not_channel)
        return

    await event.respond(strings.add_getting_infos)
    try:
        channel = await bot.get_entity(event.message.fwd_from.channel_id)
    except ChannelPrivateError:
        await event.respond(strings.add_1st_step_not_complete)
        return

    if channel.admin_rights is None:
        await event.respond(strings.add_1st_step_not_complete)
        return
    if db.check_channel_saved(channel):
        await event.respond(strings.add_already_added)
        db.clear_user_state(user)
        return

    db.save_channel(channel)
    async for admin in bot.iter_participants(
            channel, filter=types.ChannelParticipantsAdmins):
        db.save_channel_admin_relation(channel.id, admin)

    full_channel = await bot(
        functions.channels.GetFullChannelRequest(channel=channel))
    await event.respond(strings.add_obtain_msg)
    for i in range(full_channel.full_chat.read_inbox_max_id):
        message = await bot.get_messages(channel, ids=i)
        db.save_message(message)

    db.conn.commit()
    await event.respond(strings.add_finished)
    db.clear_user_state(user)


@bot.on(NewMessage(pattern='/find'))
@onstate(states.Empty)
@withi18n
async def find_command_handler(event: NewMessage.Event, strings):
    if not event.is_private:
        await event.respond(strings.private_only)
        return

    user = await event.get_chat()
    user_owned_channel_ids = db.get_user_owned_channels(user)

    if len(user_owned_channel_ids) == 0:
        await event.respond(strings.find_no_owned_channel)
        return

    def channel_id2button(channel_id):
        channel_title = db.get_channel_title(channel_id)
        return Button.inline(channel_title, data=channel_id)

    buttons = list(map(channel_id2button, user_owned_channel_ids))
    await event.respond(strings.find_select, buttons=buttons)
    db.set_user_state(user, states.SelectingAChannelToFind)


@bot.on(CallbackQuery())
@onstate(states.SelectingAChannelToFind)
@withi18n
async def select_channel_to_find_handler(event: CallbackQuery.Event, strings):
    user = await event.get_chat()
    channel_id = int(event.data)

    if user.id not in db.get_channel_admins(channel_id):
        await event.respond(strings.find_access_failed)
        db.clear_user_state(user)
        return

    channel_title = db.get_channel_title(channel_id)
    db.set_user_state(user, states.FindingInAChannel)
    db.set_user_selected(user.id, channel_id)
    await event.respond(strings.find_lets_find.format(channel_title))


@bot.on(NewMessage())
@onstate(states.FindingInAChannel)
@withi18n
async def finding_handler(event: NewMessage.Event, strings):
    user = await event.get_chat()
    channel_id = db.get_user_selected(user.id)
    pattern = event.raw_text

    found_message_ids = db.find_in_messages(channel_id, pattern)
    if len(found_message_ids) == 0:
        await event.respond(strings.find_no_result)
        return
    for message_id in found_message_ids:
        await bot.forward_messages(user, message_id, channel_id)


@bot.on(NewMessage())
async def channel_newmessage_handler(event: NewMessage.Event):
    """Continuously listen to channel updates, save new messages"""
    if event.is_channel:
        db.save_message(event.message)


@bot.on(MessageEdited())
async def channel_messageedited_handler(event: MessageEdited.Event):
    if event.is_channel:
        db.update_message(event.message)


@bot.on(NewMessage(pattern='/lang'))
@onstate(states.Empty)
@withi18n
async def lang_command_handler(event: NewMessage.Event, strings):
    user = await event.get_chat()
    buttons = [[Button.inline(strings.lang_follow_telegram, data='follow')]]
    for i in range(0, len(i18n.languages), 3):
        buttons.append([
            Button.inline(i18n.languages[langcode], data=langcode)
            for langcode in list(i18n.languages.keys())[i:i + 3]
        ])
    db.set_user_state(user, states.SettingLang)
    await event.respond(strings.lang_select_lang, buttons=buttons)


@bot.on(CallbackQuery())
@onstate(states.SettingLang)
async def setting_lang_handler(event: CallbackQuery.Event):
    user = await event.get_chat()
    langcode = event.data.decode()
    if (langcode not in i18n.languages) and (langcode != 'follow'):
        await event.respond('Unsupported language selected.')
        return
    db.set_user_lang(user.id, langcode)
    db.clear_user_state(user)

    async def respond(event, strings):
        await event.respond(strings.greeting)

    await withi18n(respond)(event)


def sigterm_handler(num, frame):
    db.conn.commit()
    os.sys.exit(130)


def main():
    # Save database when being killed
    signal.signal(signal.SIGTERM, sigterm_handler)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(bot.disconnected)
    except KeyboardInterrupt:
        db.conn.commit()


if __name__ == '__main__':
    main()
