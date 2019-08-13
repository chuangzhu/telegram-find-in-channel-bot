from telethon import TelegramClient, events
from telethon.tl import types, functions
import os
import configparser
import logging
from tgficbot import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

config = configparser.ConfigParser()
config.read(os.path.expanduser('~/.config/tgficbot.cfg'))

bot = TelegramClient(
    'bot', config['api']['id'],
    config['api']['hash']).start(bot_token=config['bot']['token'])


@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Hi!')
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='/find'))
async def find(event):
    args = event.raw_text.split()
    if len(args) == 1:
        await event.respond('Usage: `/find channel_name pattern`')

    channel_name = args[1]
    pattern = ' '.join(args[2:])
    chat = await event.get_chat()
    if isinstance(chat, types.User):
        channel = await bot.get_input_entity(channel_name)
        found_message_ids = db.find_in_messages(channel.channel_id, pattern)
        for message_id in found_message_ids:
            await event.respond(f'https://t.me/{channel_name}/{message_id}')


@bot.on(events.NewMessage(pattern='/init'))
async def get_history(event):
    args = event.raw_text.split()
    if len(args) != 2:
        await event.respond('Usage: `/init channel_name`')
        return

    channel_name = args[1]
    channel = await bot.get_input_entity(channel_name)
    full_channel = await bot(
        functions.channels.GetFullChannelRequest(channel=channel))
    db.save_channel(full_channel)
    for i in range(full_channel.full_chat.read_inbox_max_id):
        message = await bot.get_messages(channel, ids=i)
        db.save_message(message)
        db.conn.commit()


bot.run_until_disconnected()