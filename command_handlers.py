from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from user_data import save_user_data, read_user_data, generate_leaderboard
from utils import check_message_length, is_valid_response, get_word_frequencies

def settings_command(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": True, "shuffle_interval": 10, "additional_challenge": False})

    keyboard = [
        [
            InlineKeyboardButton("Подсказки: " + ("✅" if settings_data["hint"] else "⬜️"), callback_data="toggle_hint")
        ],
        [
            InlineKeyboardButton("Сменить фразу: " + ("✅" if settings_data["change_phrase"] else "⬜️"), callback_data="toggle_change_phrase")
        ],
        [
            InlineKeyboardButton("Таймер: " + ("✅" if settings_data["shuffle"] else "⬜️"), callback_data="toggle_shuffle")
        ],
        [
            InlineKeyboardButton("Additional Challenge: " + ("✅" if settings_data["additional_challenge"] else "⬜️"), callback_data="toggle_additional_challenge")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Настройки:", reply_markup=reply_markup)



def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "При игре в чате – отвечай реплаем\n\n"
        "Это игра для рифм гурмана:\n"
        "Получаешь слово – срифмовать надо!\n"
        "Оступишься раз и всё – конец раунда\n"
        "Удачи там!"
    )
    keyboard = [
        [InlineKeyboardButton("🚀 Полетели", callback_data="start_game")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(help_text, reply_markup=reply_markup)

def leaderboard_command(update: Update, context: CallbackContext) -> None:
    data = read_user_data()
    leaderboard_text = generate_leaderboard(data)

    keyboard = [
        [InlineKeyboardButton("😎 Сделать лучше", callback_data="start_game")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(leaderboard_text, reply_markup=reply_markup)

def add_phrase_command(update: Update, context: CallbackContext) -> None:
    new_phrases = update.message.text.split(' ', 1)  # Split the command from the arguments
    if len(new_phrases) < 2:
        update.message.reply_text("Введите фразу после команды /add_phrase.")
        return
    new_phrases = new_phrases[1]  # Get the phrases part

    with open("phrases.txt", "a", encoding="utf-8") as file:
        phrases = new_phrases.split(',')
        for phrase in phrases:
            file.write(phrase.strip() + '\n')  # Add a newline character at the end of each phrase

    update.message.reply_text(f"Добавлено!")


def timer_command(update: Update, context: CallbackContext) -> None:
    try:
        # Extracting the argument from command
        input_seconds = int(context.args[0])
        if input_seconds <= 10:
            update.message.reply_text("Please enter a number greater than 10.")
        else:
            # Fetch the settings data
            settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": True, "shuffle_interval": 10})
            # Update the interval
            settings_data["shuffle_interval"] = input_seconds
            context.chat_data["settings"] = settings_data
            update.message.reply_text(f"Shuffle interval updated to {input_seconds} seconds.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /timer <seconds>")

def unknown_command(update: Update, context: CallbackContext) -> None:
    """Send a message to the user when an unknown command is received."""
    update.message.reply_text("Чё?")