from telethon import TelegramClient
from telethon.events import NewMessage, CallbackQuery, StopPropagation
from telethon.tl import types, functions
from telethon.tl.custom import Button
import os
import configparser
import logging
from tgficbot import db, states
from tgficbot.states import onstate
from tgficbot import strings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

config = configparser.ConfigParser()
config.read(os.path.expanduser('~/.config/tgficbot.cfg'))

bot = TelegramClient(
    'bot', config['api']['id'],
    config['api']['hash']).start(bot_token=config['bot']['token'])


@bot.on(NewMessage(pattern='/start'))
async def start_command_handler(event: NewMessage.Event):
    if event.is_private:
        await event.respond(strings.greeting)
        chat = await event.get_chat()
        db.save_user(chat)
        db.conn.commit()
        raise StopPropagation


@bot.on(NewMessage(pattern='/add'))
@onstate(states.Empty)
async def add_command_handler(event):
    await event.respond(strings.add_guide)
    user = await event.get_chat()
    db.set_user_state(user, states.AddingAChannel)


@bot.on(NewMessage(pattern='/cancel'))
async def cancel_command_handler(event: NewMessage.Event):
    user = await event.get_chat()
    current_state = db.get_user_state(user)
    if current_state == states.Empty:
        return
    db.clear_user_state(user)
    db.set_user_selected(user.id, None)
    await event.respond(strings.cancel)


@bot.on(NewMessage())
@onstate(states.AddingAChannel)
async def adding_forward_handler(event: NewMessage.Event):
    user = await event.get_chat()

    if event.message.fwd_from is None:
        await event.respond(strings.add_not_forward)
        return
    if event.message.fwd_from.channel_id is None:
        await event.respond(strings.add_forward_not_channel)
        return

    await event.respond(strings.add_getting_infos)
    channel = await bot.get_entity(event.message.fwd_from.channel_id)

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
async def find_command_handler(event: NewMessage.Event):
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
async def select_channel_to_find_handler(event: CallbackQuery.Event):
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
async def finding_handler(event: NewMessage.Event):
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
    if event.is_channel:
        db.save_message(event.message)


def main():
    bot.run_until_disconnected()


if __name__ == '__main__':
    main()
