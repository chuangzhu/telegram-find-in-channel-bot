from telethon import TelegramClient
from telethon.events import NewMessage, StopPropagation, register, unregister
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


@bot.on(NewMessage(pattern='/start'))
async def start(event: NewMessage.Event):
    if event.is_private:
        await event.respond('Hi!')
        chat = await event.get_chat()
        db.save_user(chat)
        db.conn.commit()
        raise StopPropagation


@bot.on(NewMessage(pattern='/find'))
async def find(event):
    args = event.raw_text.split()
    if len(args) == 1:
        await event.respond('Usage: `/find channel_name pattern`')
        return

    channel_name = args[1]
    pattern = ' '.join(args[2:])
    chat = await event.get_chat()
    if isinstance(chat, types.User):
        channel = await bot.get_input_entity(channel_name)
        found_message_ids = db.find_in_messages(channel.channel_id, pattern)
        for message_id in found_message_ids:
            await event.respond(f'https://t.me/{channel_name}/{message_id}')


@bot.on(NewMessage(pattern='/init'))
async def init_channel(event):
    await event.respond('''To initialize your channel, do the following:

1. Add this bot to your channel as an admin;
2. Forward any message of the channel to me.''')
    user = await event.get_chat()
    Initializer(user)


class Initializer:
    """We need to add a event handler to bot, and remove it after it finished.
    To make it easier, let's pack it into a class.
    """

    def __init__(self, user: types.User):
        self.user = user
        self.handler = self.new_handler(user)
        bot.add_event_handler(self.handler)

    def new_handler(self, user: types.User):
        async def on_forward_func(event):
            if event.message.message == '/cancel':
                await event.respond('Aborted.')
                self.remove_handler()
                return
            if event.message.fwd_from is None:
                await event.respond(
                    'Please forward any message from your channel to me, or /cancel to abort.'
                )
                return
            if event.message.fwd_from.channel_id is None:
                await event.respond('Please forward from a channel.')
                return

            await event.respond('Getting channel infos...')
            channel = await bot.get_input_entity(
                event.message.fwd_from.channel_id)
            full_channel = await bot(
                functions.channels.GetFullChannelRequest(channel=channel))
            if db.check_channel_saved(full_channel):
                await event.respond('Channel already initialized. Abort.')
                self.remove_handler()
                return
            db.save_channel(full_channel)

            async for admin in bot.iter_participants(
                    channel, filter=types.ChannelParticipantsAdmins):
                db.save_channel_admin_relation(channel.channel_id, admin)

            await event.respond('Obtaining previous messages...')
            for i in range(full_channel.full_chat.read_inbox_max_id):
                message = await bot.get_messages(channel, ids=i)
                db.save_message(message)

            db.conn.commit()
            await event.respond('Initialize finished.')
            self.remove_handler()

        # Register the handler
        return register(event=NewMessage(from_users=user))(on_forward_func)

    def remove_handler(self):
        unregister(self.handler)
        bot.remove_event_handler(self.handler)


@bot.on(NewMessage())
async def new_message(event: NewMessage.Event):
    if event.is_channel:
        db.save_message(event.message)


# @bot.on(NewMessage())
# async def peek_message(event: NewMessage.Event):
#     print(event.message)

# @bot.on(NewMessage(pattern='/select'))
# async def select_channel(event: NewMessage.Event):
#     if not event.is_private:
#         await event.respond('This command can only be used in private chat.')
#         return

#     chat = await event.get_chat()
#     db.save_selected(chat.id, )

bot.run_until_disconnected()