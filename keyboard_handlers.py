from typing import Dict, Optional
from enum import Enum
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import CallbackContext
from config import config
from callback_actions import CallbackActions

def get_start_game_markup():
    buttons = [
        [InlineKeyboardButton("🦅 Вперёд!", callback_data=CallbackActions.START_GAME.value)],
        [InlineKeyboardButton("🏆 Чемпионы", callback_data="leaderboard")]
    ]
    return InlineKeyboardMarkup(buttons)

def build_keyboard(reply_markup: Optional[InlineKeyboardMarkup], shuffle_button_text: str, shuffle_button_callback_data: str, settings_data: Dict[str, bool], current_phrase: str) -> InlineKeyboardMarkup:
    if not reply_markup:
        keyboard = [[]]

        if settings_data["hint"]:
            keyboard[0].append(InlineKeyboardButton("🔥", callback_data=f"show_example:{current_phrase}"))

        if settings_data["change_phrase"]:
            keyboard[0].append(InlineKeyboardButton("🔄", callback_data="change_phrase"))

        if settings_data["shuffle"] and shuffle_button_text:
            keyboard[0].append(InlineKeyboardButton(shuffle_button_text, callback_data=shuffle_button_callback_data))

        return InlineKeyboardMarkup(keyboard)

    new_buttons = []
    for row in reply_markup.inline_keyboard:
        new_row = []
        for button in row:
            if button.callback_data in ["shuffle", "stop_shuffle"]:
                if shuffle_button_text:
                    new_row.append(InlineKeyboardButton(shuffle_button_text, callback_data=shuffle_button_callback_data))
            else:
                new_row.append(button)
        new_buttons.append(new_row)

    return InlineKeyboardMarkup(new_buttons)

def settings_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data

    settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": True, "shuffle_interval": 10, "additional_challenge": False})

    if data.startswith("toggle_"):
        setting_key = data[7:]
        settings_data[setting_key] = not settings_data.get(setting_key, False)
        context.chat_data["settings"] = settings_data

    # Fetch the latest settings data here.
    settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": True, "shuffle_interval": 10, "additional_challenge": False})

    # Modify the text of the shuffle button based on its status
    shuffle_text = "Таймер: ✅" if settings_data.get("shuffle", False) else "Таймер: ⬜️"

    additional_challenge_text = "Additional Challenge: ✅" if settings_data.get("additional_challenge", False) else "Additional Challenge: ⬜️"
    
    keyboard = [
        [
            InlineKeyboardButton("Подсказки: " + ("✅" if settings_data.get("hint", False) else "⬜️"), callback_data="toggle_hint")
        ],
        [
            InlineKeyboardButton("Сменить фразу: " + ("✅" if settings_data.get("change_phrase", False) else "⬜️"), callback_data="toggle_change_phrase")
        ],
        [
            InlineKeyboardButton(shuffle_text, callback_data="toggle_shuffle")
        ],
        [
            InlineKeyboardButton(additional_challenge_text, callback_data="toggle_additional_challenge")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("Настройки:", reply_markup=reply_markup)

def timer_settings_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": False, "shuffle_interval": 10})
    
    keyboard = [
        [
             InlineKeyboardButton("Настроить таймер: " + str(settings_data["shuffle_interval"]) + " секунд", callback_data="change_interval")
        ],
        [
            InlineKeyboardButton("Back to settings", callback_data="back_to_settings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("Настройки Таймера:", reply_markup=reply_markup)

def back_to_settings(update: Update, context: CallbackContext) -> None:
    settings_callback(update, context)
