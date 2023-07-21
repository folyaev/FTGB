# message_handling.py

from typing import Optional
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext

def send_or_edit_message(update: Update, context: CallbackContext, chat_id: int, message_id: int, new_text: str, keyboard: InlineKeyboardMarkup, parse_mode: Optional[str] = None):
    """
    Send a new message or edit an existing one.

    :param update: The Update object provided by the python-telegram-bot library.
    :param context: The CallbackContext provided by the python-telegram-bot library.
    :param chat_id: The ID of the chat where the message should be sent or edited.
    :param message_id: The ID of the message to edit. If this is None, a new message will be sent.
    :param new_text: The new text for the message.
    :param keyboard: The keyboard markup for the message.
    """
    if message_id is None:
        # If there's no message_id, send a new message
        message = update.effective_message.reply_text(new_text, reply_markup=keyboard, parse_mode=parse_mode)
        return message.message_id
    else:
        # If there's a message_id, edit the existing message
        context.bot.edit_message_text(new_text, chat_id, message_id, reply_markup=keyboard, parse_mode=parse_mode)
        return message_id