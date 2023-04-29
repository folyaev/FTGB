import csv
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CallbackContext, InlineQueryHandler
from user_data import read_user_data

phrase_hash_to_phrase = {}

def handle_inline_query(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query

    if not query:
        return

    data = read_user_data()
    matching_data = [row for row in data if row["current_phrase"].lower() == query.lower()]

    if matching_data:
        results = [
            InlineQueryResultArticle(
                id=str(i),
                title=f"{example['user_message']}",
                input_message_content=InputTextMessageContent(f"{example['user_message']}"),
                description="Выбрать рифму",
            )
            for i, example in enumerate(matching_data)
        ]
    else:
        phrase_hash = hashlib.sha1(query.encode()).hexdigest()
        context.bot_data[phrase_hash] = query
        
        results = [
            InlineQueryResultArticle(
                id="0",
                title=f"На «{query}» рифм нет",
                input_message_content=InputTextMessageContent(f"На «{query}» рифм нет, добавить в базу?"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Добавить в базу", callback_data=f"add_phrase:{phrase_hash}")]
                ]),
                description="Добавить в базу",
            )
        ]

    update.inline_query.answer(results)
