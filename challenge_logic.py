# challenge_logic.py

import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from callback_actions import CallbackActions, AdditionalChallengeStatus

def handle_additional_challenge(update: Update, context: CallbackContext, chat_id: int):
    """
    Handle the additional challenge.

    :param update: The Update object provided by the python-telegram-bot library.
    :param context: The CallbackContext provided by the python-telegram-bot library.
    :param chat_id: The ID of the chat where the additional challenge should be sent.
    """
    # Check if the additional challenge setting is enabled
    settings_data = context.chat_data.get("settings", {"additional_challenge": False})
    if not settings_data.get("additional_challenge", False):
        return

    # Read the list of challenges from a file
    with open("challenges.txt", "r", encoding="utf-8") as file:
        challenges = [line.strip() for line in file.readlines()]

    # Choose a random challenge
    random_challenge = random.choice(challenges)

    # Create a keyboard markup with a button to accept the challenge
    accept_challenge_button = InlineKeyboardButton("Accept ⬜️", callback_data="accept_challenge")
    challenge_markup = InlineKeyboardMarkup([[accept_challenge_button]])

    # Send the challenge message
    sent_message = context.bot.send_message(chat_id, f"<i>{random_challenge}</i>", parse_mode="HTML", reply_markup=challenge_markup)

    # Set the status of the additional challenge to SENT
    context.chat_data["additional_challenge_status"] = AdditionalChallengeStatus.SENT.value