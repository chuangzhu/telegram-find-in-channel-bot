from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import sys

token = sys.argv[1]

updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text='Hello!')


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


def text(update, context):
    if update.channel_post is not None:
        context.bot.send_message(chat_id=update.channel_post.chat_id,
                                 text=update.channel_post.text)
    else:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=update.message.text)


text_handler = MessageHandler(Filters.text, text)
dispatcher.add_handler(text_handler)


def unknown_command(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Sorry, I didn't understand that command.")


unknown_command_handler = MessageHandler(Filters.command, unknown_command)
dispatcher.add_handler(unknown_command_handler)

updater.start_polling()