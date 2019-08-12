from telethon import TelegramClient, events
from telethon.tl import types, functions
import os
import configparser
import logging

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
    chat = await event.get_chat()
    if isinstance(chat, types.User):
        for text in args[1:]:
            await event.respond(text)
    elif isinstance(chat, types.Channel):
        for text in args[2:]:
            await event.respond(text)


@bot.on(events.NewMessage(pattern='/get'))
async def get_history(event):
    channel = await bot.get_input_entity('genelocated')
    full_channel = await bot(functions.channels.GetFullChannelRequest(channel=channel))
    for i in range(full_channel.full_chat.read_inbox_max_id):
        message = await bot.get_messages(channel, ids=i)
        print(message)


bot.run_until_disconnected()