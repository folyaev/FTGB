import csv
import hashlib
import logging
import random
import time
from enum import Enum
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram.ext import InlineQueryHandler

from config import config
from game_logic import game_state
from phrases import phrases
from user_data import save_user_data, read_user_data, generate_leaderboard, phrase_hash_to_phrase
from utils import check_message_length, is_valid_response, get_word_frequencies
from command_handlers import help_command, leaderboard_command, add_phrase_command, unknown_command
from inline_handlers import handle_inline_query

class CallbackActions(Enum):
    START_GAME = "start_game"

def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors caused by updates."""
    logging.error(f"Update {update} caused error: {context.error}")

def start_game(update: Update, context: CallbackContext) -> None:
    send_random_phrase(update, context)

def get_start_game_markup():
    buttons = [
        [InlineKeyboardButton("🦅 Вперёд!", callback_data=CallbackActions.START_GAME.value)],
        [InlineKeyboardButton("🏆 Чемпионы", callback_data="leaderboard")]
    ]
    return InlineKeyboardMarkup(buttons)

def start(update, context):
    welcome_text = get_welcome_text()
    reply_markup = get_start_game_markup()
    update.message.reply_text(welcome_text, reply_markup=reply_markup)

def get_welcome_text() -> str:
    """Return the welcome text for the game."""
    return (
        f"Йау! Это бот Фоляйф!\n"
        f"Значит время играть.\n"
        f"Я выдаю тебе слова –\n"
        f"Надо их срифмовать!\n"
    )

def start_game_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    send_random_phrase(query, context)

def leaderboard_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = read_user_data()
    leaderboard_text = generate_leaderboard(data)

    keyboard = [
        [InlineKeyboardButton("Сделать лучше 😎", callback_data="start_game")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(leaderboard_text, reply_markup=reply_markup)

def send_random_phrase(update: Update, context: CallbackContext, query: Optional[CallbackQuery] = None) -> None:
    with open("phrases.txt", "r", encoding="utf-8") as file:
        phrases = [line.strip() for line in file.readlines()]

    # Check if there are used_phrases in the context, create an empty list if not
    used_phrases = context.user_data.get("used_phrases", [])
    context.user_data["used_phrases"] = used_phrases

    # Filter out used phrases from the phrases list
    available_phrases = [phrase for phrase in phrases if phrase not in used_phrases]

    # If there are no more available phrases, reset the used_phrases list
    if not available_phrases:
        context.user_data["used_phrases"] = []
        available_phrases = phrases

    word_frequencies = get_word_frequencies()
    sorted_phrases = sorted(available_phrases, key=lambda phrase: word_frequencies.get(phrase.lower(), 0))

    # Choose a random phrase from the least frequent ones (up to 1000)
    random_phrase = random.choice(sorted_phrases[:1000])

    # Add the chosen phrase to the used_phrases list
    context.user_data["used_phrases"].append(random_phrase)

    context.user_data["current_phrase"] = random_phrase
    context.user_data["shown_examples"] = []

    keyboard = [
        [InlineKeyboardButton("Подсказка 🔥", callback_data="show_example")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        message = query.message
    else:
        message = update.message

    message.reply_text(f"<b>{random_phrase}</b>", parse_mode="HTML", reply_markup=reply_markup)


def add_phrase_callback(update: Update, context: CallbackContext) -> None:
    phrase_hash = update.callback_query.data.split(":")[1]
    new_phrase = context.bot_data.get(phrase_hash, "")

    if not new_phrase:
        update.callback_query.answer(text="Произошла ошибка. Попробуйте еще раз.")
        return

    del context.bot_data[phrase_hash]


    update.callback_query.answer()
    update.callback_query.edit_message_text(text=f"«{new_phrase}» добавлено в базу и скоро будет доступно!", reply_markup=None)

def show_example_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    current_phrase = context.user_data.get("current_phrase", "")
    data = read_user_data()

    # Filter the data to only include rows that match the current phrase
    matching_data = [row for row in data if row["current_phrase"] == current_phrase]

    # Define the reply_markup variable with the same keyboard as in the send_random_phrase function
    keyboard = [
        [InlineKeyboardButton("Подсказка 🔥", callback_data="show_example")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not matching_data:
        query.edit_message_text(f"Чёт никто ничего не придумал на {current_phrase}!")
    else:
        shown_examples = context.user_data.get("shown_examples", [])

        if len(shown_examples) == len(matching_data):
            shown_examples = []  # Reset the shown examples list

        new_example = random.choice(matching_data)
        while len(shown_examples) < len(matching_data) and new_example in shown_examples:
            new_example = random.choice(matching_data)

        shown_examples.append(new_example)
        context.user_data["shown_examples"] = shown_examples

        example_text = new_example["user_message"]

        if query.message.text != f"{example_text}":
            try:
                query.edit_message_text(f"{example_text}", reply_markup=reply_markup)
            except Exception as e:
                print(f"Error occurred while editing the message: {e}")

def handle_message(update: Update, context: CallbackContext, bot_user_id: int) -> None:
    message_text = update.message.text
    current_phrase = context.user_data.get("current_phrase", "")
    username = update.message.from_user.first_name

    # Check if the message is a reply and in a group chat
    if update.message.chat.type in ["group", "supergroup"]:
        if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != bot_user_id:
            return
    elif update.message.chat.type != "private":
        return

    if check_message_length(message_text, current_phrase):
        update.message.reply_text("Хорошая попытка, но нет.")
    elif is_valid_response(message_text, current_phrase):
        score = context.user_data.get("score", 0) + 1
        save_user_data(username, current_phrase, message_text, score)
        context.user_data["score"] = score
        send_random_phrase(update, context)
    else:
        game_over_message(update, context)

    if update.message.chat.type in ["group", "supergroup"]:
        if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != bot_user_id:
            return

def game_over_message(update: Update, context: CallbackContext) -> None:
    score = context.user_data.get("score", 0)
    first_name = update.message.from_user.first_name
    context.user_data["score"] = 0
    game_over_text = f"{first_name}, ты сделал всё, что мог!\nТвой счёт: {score}"
    keyboard = [
        [InlineKeyboardButton("🔁 Заново", callback_data="start_game")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if the game over message has already been sent
    if "game_over_sent" not in context.user_data or not context.user_data["game_over_sent"]:
        context.user_data["game_over_sent"] = True
        update.message.reply_text(game_over_text, reply_markup=reply_markup)

def setup_dispatcher(dispatcher, bot_user_id):
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, lambda update, context: handle_message(update, context, bot_user_id)))
    dispatcher.add_handler(CallbackQueryHandler(start_game_callback, pattern=f"^{CallbackActions.START_GAME.value}$"))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(CommandHandler("leaderboard", leaderboard_command))
    dispatcher.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard$"))
    dispatcher.add_handler(CallbackQueryHandler(show_example_callback, pattern="^show_example$"))
    dispatcher.add_handler(InlineQueryHandler(handle_inline_query))
    dispatcher.add_handler(CallbackQueryHandler(add_phrase_callback, pattern="^add_phrase:"))
    dispatcher.add_handler(CommandHandler("add_phrase", add_phrase_command))  # Make sure this line is before the unknown_command MessageHandler
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))  # Move this line to the end of setup_dispatcher