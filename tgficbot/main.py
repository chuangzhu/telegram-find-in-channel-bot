from telethon import TelegramClient
from telethon.events import NewMessage, CallbackQuery, StopPropagation, register, unregister
from telethon.tl import types, functions
from telethon.tl.custom import Button
import os
import configparser
import logging
from tgficbot import db, states
from tgficbot.states import onstate

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


@bot.on(NewMessage(pattern='/init'))
@onstate(states.Empty)
async def init_channel(event):
    await event.respond('''To initialize your channel, do the following:

1. Add this bot to your channel as an admin;
2. Forward any message of the channel to me.''')
    user = await event.get_chat()
    db.set_user_state(user, states.AddingAChannel)


@bot.on(NewMessage())
@onstate(states.AddingAChannel)
async def on_initializing_forward(event: NewMessage.Event):
    user = await event.get_chat()

    if event.message.message == '/cancel':
        await event.respond('Aborted.')
        db.clear_user_state(user)
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
    channel = await bot.get_input_entity(event.message.fwd_from.channel_id)
    full_channel = await bot(
        functions.channels.GetFullChannelRequest(channel=channel))
    if db.check_channel_saved(full_channel):
        await event.respond('Channel already initialized. Abort.')
        db.clear_user_state(user)
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
    db.clear_user_state(user)


# @bot.on(NewMessage(pattern='/find'))
# async def find(event):
#     args = event.raw_text.split()
#     if len(args) == 1:
#         await event.respond('Usage: `/find channel_name pattern`')
#         return

#     channel_name = args[1]
#     pattern = ' '.join(args[2:])
#     if event.is_private:
#         channel = await bot.get_input_entity(channel_name)
#         found_message_ids = db.find_in_messages(channel.channel_id, pattern)
#         for message_id in found_message_ids:
#             await event.respond(f'https://t.me/{channel_name}/{message_id}')


@bot.on(NewMessage(pattern='/find'))
@onstate(states.Empty)
async def select_channel(event: NewMessage.Event):
    if not event.is_private:
        await event.respond('This command can only be used in private chat.')
        return

    user = await event.get_chat()
    user_owned_channel_ids = db.get_user_owned_channel(user)

    def channel_id2button(channel_id):
        channel_title = db.get_channel_title(channel_id)
        return Button.inline(channel_title, data=channel_id)

    buttons = list(map(channel_id2button, user_owned_channel_ids))
    await event.respond('Select a channel to search:', buttons=buttons)
    db.set_user_state(user, states.SelectingAChannel)


@bot.on(CallbackQuery())
@onstate(states.SelectingAChannel)
async def callback_query(event: CallbackQuery.Event):
    user = await event.get_chat()
    channel_id = int(event.data)
    channel_title = db.get_channel_title(channel_id)
    db.set_user_state(user, states.FindingInAChannel)
    db.set_user_selected(user.id, channel_id)
    await event.respond(
        'Now type in what you want to find in **{}**, or /quit to quit.'.
        format(channel_title))


@bot.on(NewMessage())
@onstate(states.FindingInAChannel)
async def find_in_a_channel(event: NewMessage.Event):
    user = await event.get_chat()
    channel_id = db.get_user_selected(user.id)
    pattern = event.raw_text

    if pattern == '/quit':
        db.set_user_state(user, states.Empty)
        db.set_user_selected(user.id, None)
        await event.respond('Quitted searching.')
        return

    found_message_ids = db.find_in_messages(channel_id, pattern)
    if len(found_message_ids) == 0:
        await event.respond('No results.')
        return
    for message_id in found_message_ids:
        await bot.forward_messages(user, message_id, channel_id)


@bot.on(NewMessage())
async def new_message(event: NewMessage.Event):
    if event.is_channel:
        db.save_message(event.message)


bot.run_until_disconnected()
