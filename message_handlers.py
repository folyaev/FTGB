from typing import Dict, Optional, List

from enum import Enum
import csv
import hashlib
import logging
import random
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from telegram import Message, MessageEntity, ParseMode

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram.ext import InlineQueryHandler, JobQueue

from telegram.error import BadRequest

from config import config

from game_logic import CallbackActions, game_state, start_game, start_game_callback, change_phrase_callback, add_phrase_callback, show_example_callback, back_to_main_callback, button_callback, handle_message, game_over_message
from phrases import phrases
from user_data import save_user_data, read_user_data, generate_leaderboard, phrase_hash_to_phrase
from utils import check_message_length, is_valid_response, get_word_frequencies
from command_handlers import help_command, leaderboard_command, add_phrase_command, settings_command, timer_command, unknown_command
from inline_handlers import handle_inline_query
from keyboard_handlers import get_start_game_markup, build_keyboard, settings_callback, timer_settings_callback, back_to_settings

from apscheduler.schedulers.background import BackgroundScheduler

def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors caused by updates."""
    logging.error(f"Update {update} caused error: {context.error}")

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

def message_handler(update: Update, context: CallbackContext) -> None:
    if context.chat_data.get("awaiting_interval", False):
        try:
            new_interval = max(10, int(update.message.text)) # ensure minimum 10 seconds
            settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": False, "shuffle_interval": 10})
            settings_data["shuffle_interval"] = new_interval
            context.chat_data["settings"] = settings_data
            context.chat_data["awaiting_interval"] = False
            update.message.reply_text(f"New interval set to {new_interval} seconds")
        except ValueError:
            update.message.reply_text("Please enter a valid number")

scheduler = BackgroundScheduler()

def write_valid_answer(username, current_phrase, user_message):
    with open("user_data.csv", "a", encoding="utf-8", newline="") as csvfile:
        fieldnames = ["username", "current_phrase", "user_message"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writerow({"username": username, "current_phrase": current_phrase, "user_message": user_message})

def setup_dispatcher(dispatcher, bot_user_id):
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, handle_message))
    dispatcher.add_handler(CallbackQueryHandler(start_game_callback, pattern=f"^{CallbackActions.START_GAME.value}$"))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(CommandHandler("settings", settings_command))
    dispatcher.add_handler(CallbackQueryHandler(settings_callback, pattern="^toggle_"))
    dispatcher.add_handler(CommandHandler("leaderboard", leaderboard_command))
    dispatcher.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard$"))
    dispatcher.add_handler(CallbackQueryHandler(show_example_callback, pattern="^show_example:"))
    dispatcher.add_handler(CommandHandler("timer", timer_command))
    dispatcher.add_handler(CallbackQueryHandler(timer_settings_callback, pattern='^timer_settings$'))
    dispatcher.add_handler(CallbackQueryHandler(back_to_settings, pattern='^back_to_settings$'))
    dispatcher.add_handler(InlineQueryHandler(handle_inline_query))
    dispatcher.add_handler(CallbackQueryHandler(back_to_main_callback, pattern="^back_to_main:"))
    dispatcher.add_handler(CallbackQueryHandler(add_phrase_callback, pattern="^add_phrase:"))
    dispatcher.add_handler(CallbackQueryHandler(change_phrase_callback, pattern="^change_phrase$"))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))
    dispatcher.add_handler(CommandHandler("add_phrase", add_phrase_command))  # Make sure this line is before the unknown_command MessageHandler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))  # Move this line to the end of setup_dispatcher
    