from typing import Dict, Optional, List
from telegram import Message, MessageEntity, ReplyMarkup

import random
import logging
from telegram import Update, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import telegram
from telegram.ext import CallbackContext
from telegram.error import BadRequest
from config import config
from phrases import phrases
from utils import read_user_data, check_message_length, is_valid_response, get_word_frequencies
from user_data import save_user_data
from keyboard_handlers import get_start_game_markup, build_keyboard
from callback_actions import CallbackActions, AdditionalChallengeStatus
from random_phrase import generate_random_phrase
from message_handling import send_or_edit_message
from challenge_logic import handle_additional_challenge

class GameState:
    def __init__(self):
        self.phrases = phrases

    def __str__(self) -> str:
        return f"GameState(phrases={self.phrases})"

    def get_random_phrase(self) -> str:
        return random.choice(self.phrases)

game_state = GameState()

def handle_callback_and_send_phrase(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    send_random_phrase(context.user_data, context=context, update=update, query=query)

def start_game(update: Update, context: CallbackContext) -> None:
    handle_callback_and_send_phrase(update, context)

def start_game_callback(update: Update, context: CallbackContext) -> None:
    print("start_game_callback called")
    handle_callback_and_send_phrase(update, context)

def change_phrase_callback(update: Update, context: CallbackContext) -> None:
    handle_callback_and_send_phrase(update, context)

def send_random_phrase(user_data: Dict, context: CallbackContext, update: Optional[Update] = None, query: Optional[CallbackQuery] = None, chat_id: Optional[int] = None, start_timer: Optional[int] = None, message: Optional[Message] = None) -> None:
    """
    Send a random phrase to the chat.

    :param user_data: The user's data.
    :param context: The CallbackContext provided by the python-telegram-bot library.
    :param update: The Update object provided by the python-telegram-bot library.
    :param query: The CallbackQuery object provided by the python-telegram-bot library.
    :param chat_id: The ID of the chat where the random phrase should be sent.
    :param start_timer: The number of seconds to start a timer for changing the phrase.
    :param message: The Message object provided by the python-telegram-bot library.
    """
    print("send_random_phrase called")
    user_data["game_over"] = False
    user_data["additional_challenge_status"] = AdditionalChallengeStatus.NONE.value
    settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": True, "shuffle_interval": 10})

    with open("phrases.txt", "r", encoding="utf-8") as file:
        phrases = [line.strip() for line in file.readlines()]

    used_phrases = user_data.get("used_phrases", [])
    user_data["used_phrases"] = used_phrases

    available_phrases = [phrase for phrase in phrases if phrase not in used_phrases]

    if not available_phrases:
        context.user_data["used_phrases"] = []
        available_phrases = phrases

    word_frequencies = get_word_frequencies()
    sorted_phrases = sorted(available_phrases, key=lambda phrase: word_frequencies.get(phrase.lower(), 0))

    # Stop the shuffle if it's active
    if "shuffle_job" in context.chat_data:
        context.chat_data["shuffle_job"].schedule_removal()
        context.chat_data.pop("shuffle_job", None)
        user_data["shuffle_active"] = False

    random_phrase = generate_random_phrase(phrases, used_phrases)

    # Add this block of code
    if query:
        current_text = query.message.text.strip()
        while current_text == random_phrase:
            random_phrase = random.choice(sorted_phrases[:1000])
    else:
        current_text = ""
    # End of the added block

    user_data["used_phrases"].append(random_phrase)
    user_data["shuffle_active"] = False
    user_data["current_phrase"] = random_phrase
    user_data["shown_examples"] = []

    # If shuffle is active, use "Stop Shuffle" button text and "stop_shuffle" callback data, otherwise use "Shuffle" button text and "shuffle" callback data
    shuffle_button_text = "⏹️" if user_data.get("shuffle_active", False) else "▶️"
    shuffle_button_callback_data = "stop_shuffle" if user_data.get("shuffle_active", False) else "shuffle"

    # Build the message reply_markup
    reply_markup = build_keyboard(reply_markup=None, shuffle_button_text=shuffle_button_text, shuffle_button_callback_data=shuffle_button_callback_data, settings_data=settings_data, current_phrase=random_phrase)

    if query:
        reply_markup_without_shuffle = build_keyboard(reply_markup=None, shuffle_button_text=None, shuffle_button_callback_data=None, settings_data=settings_data, current_phrase=random_phrase)
    phrases = get_phrases()
    
    if update:
        user_data = user_data
    else:
        user_data = user_data

        
    if not chat_id and message:
        chat_id = message.chat_id

    if start_timer:
        context.job_queue.run_once(change_phrase_with_timer, start_timer, context={"chat_id": chat_id, "message_id": message.message_id, "timer": start_timer})  # Pass the message_id here

    if query:
        print("query is not None")
        chat_id = query.message.chat_id
    elif update:
        chat_id = update.message.chat_id
    elif message:
        chat_id = message.chat_id
    else:
    # If no query, update or message was passed, raise an exception or handle the situation in a suitable way.
        raise ValueError("chat_id could not be determined because no query, update or message was provided.")
    
    if query:
        message_id = send_or_edit_message(update, context, chat_id, query.message.message_id, f"<b>{random_phrase}</b>", reply_markup, parse_mode='HTML')
    else:
        message_id = send_or_edit_message(update, context, chat_id, None, f"<b>{random_phrase}</b>", reply_markup, parse_mode='HTML')

    # Handle the additional challenge
    handle_additional_challenge(update, context, chat_id)
    
    print(f"New random phrase: {random_phrase}")  # Debugging print

def get_phrases() -> List[str]:
    with open("phrases.txt", "r", encoding="utf-8") as file:
        phrases = [line.strip() for line in file.readlines()]
    return phrases

def message_entities_to_html(message: Message) -> str:
    formatted_message = message.text
    offset_correction = 0

    for entity in reversed(message.entities):
        start_pos = entity.offset + offset_correction
        end_pos = start_pos + entity.length
        tag = None

        if entity.type == MessageEntity.BOLD:
            tag = 'b'
        elif entity.type == MessageEntity.ITALIC:
            tag = 'i'
        elif entity.type == MessageEntity.UNDERLINE:
            tag = 'u'
        elif entity.type == MessageEntity.STRIKETHROUGH:
            tag = 's'
        elif entity.type == MessageEntity.CODE:
            tag = 'code'

        if tag:
            formatted_message = f"{formatted_message[:start_pos]}<{tag}>{formatted_message[start_pos:end_pos]}</{tag}>{formatted_message[end_pos:]}"
            offset_correction += 2 * (len(tag) + 2)

    return formatted_message

def add_phrase_callback(update: Update, context: CallbackContext) -> None:
    phrase_hash = update.callback_query.data.split(":")[1]
    new_phrase = context.bot_data.get(phrase_hash, "")

    if not new_phrase:
        update.callback_query.answer(text="Произошла ошибка. Попробуйте еще раз.")
        return

    with open("phrases.txt", "a", encoding="utf-8") as file:
        file.write(new_phrase + '\n')  # Add the new phrase to the file

    del context.bot_data[phrase_hash]

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=f"«{new_phrase}» добавлено в базу и скоро будет доступно!", reply_markup=None)

def show_example_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    # Extract the current phrase from the callback data
    current_phrase = query.data.split(":", 1)[1]

    data = read_user_data()

    # Filter the data to only include rows that match the current phrase
    matching_data = [row for row in data if row["current_phrase"] == current_phrase]

    # Define the reply_markup variable with the same keyboard as in the send_random_phrase function
    keyboard = [
        [
            InlineKeyboardButton("Ещё", callback_data=f"show_example:{current_phrase}"),
            InlineKeyboardButton("Назад", callback_data=f"back_to_main:{current_phrase}"),
        ],
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

def back_to_main_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    current_phrase = query.data.split(":", 1)[1]
    settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": True, "shuffle_interval": 10})
    reply_markup = build_keyboard(reply_markup=None, shuffle_button_text="▶️", shuffle_button_callback_data="shuffle", settings_data=settings_data, current_phrase=current_phrase)

    try:
        query.edit_message_text(f"<b>{current_phrase}</b>", parse_mode="HTML", reply_markup=reply_markup)
    except Exception as e:
        print(f"Error occurred while editing the message: {e}")

def change_phrase_with_timer(context: CallbackContext) -> None:
    """
    Change the phrase after a certain interval.

    :param context: The CallbackContext provided by the python-telegram-bot library.
    """
    job_context = context.job.context
    chat_id = job_context["chat_id"]
    message_id = job_context["message_id"]
    user_id = job_context["user_id"]
    chat_data = job_context["chat_data"]
    user_data = job_context["user_data"]

    settings_data = chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": True, "shuffle_interval": 10})
    current_phrase = user_data["current_phrase"]

    used_phrases = set(user_data.get("used_phrases", []))
    all_phrases = set(get_phrases())
    available_phrases = all_phrases - used_phrases

    if not available_phrases:
        available_phrases = all_phrases
        used_phrases.clear()

    new_phrase = random.choice(list(available_phrases))

    # Ensure the new_phrase is different from the current_phrase
    while new_phrase == current_phrase:
        new_phrase = random.choice(list(available_phrases))

    # Update the shuffle button text and callback_data based on shuffle_active status
    shuffle_active = user_data.get("shuffle_active", False)
    shuffle_button_text = "⏹️" if shuffle_active else "▶️"
    shuffle_button_callback_data = "stop_shuffle" if shuffle_active else "shuffle"

    new_reply_markup = build_keyboard(reply_markup=None, shuffle_button_text=shuffle_button_text, shuffle_button_callback_data=shuffle_button_callback_data, settings_data=settings_data, current_phrase=new_phrase)

    try:
        user_data["current_phrase"] = new_phrase
        # Wrap new_phrase in HTML bold tags
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"<b>{new_phrase}</b>", reply_markup=new_reply_markup, parse_mode="HTML")
    except BadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Update {job_context} caused error: {e}")

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data
    chat_id = query.message.chat_id

    settings_data = context.chat_data.get("settings", {"hint": True, "change_phrase": True, "shuffle": True, "shuffle_interval": 10})

    if data == "start_game":
        send_random_phrase(context.user_data, context=context, update=update, query=query)

    elif data in ["shuffle", "stop_shuffle"]:
        print("Shuffle button pressed")
        shuffle_active = context.user_data.get("shuffle_active", False)

        current_phrase = context.user_data["current_phrase"]

        if not shuffle_active:
            print("Starting shuffle")
            context.user_data["shuffle_active"] = True
            user_id = update.effective_user.id
            # Add a default value for `interval` in case "shuffle_interval" doesn't exist in the settings data
            interval = context.chat_data.get("settings", {}).get("shuffle_interval", 30)
            job = context.job_queue.run_repeating(change_phrase_with_timer, interval=interval, first=0, context={"chat_id": chat_id, "message_id": query.message.message_id, "user_id": user_id, "chat_data": context.chat_data.copy(), "user_data": context.user_data})
            context.chat_data["shuffle_job"] = job
            query.edit_message_reply_markup(reply_markup=build_keyboard(query.message.reply_markup, shuffle_button_text="⏹️", shuffle_button_callback_data="stop_shuffle", settings_data=settings_data, current_phrase=current_phrase))

        else:
            print("Stopping shuffle")
            context.user_data["shuffle_active"] = False
            job = context.chat_data.pop("shuffle_job", None)
            if job:
                job.schedule_removal()
            query.edit_message_reply_markup(reply_markup=build_keyboard(query.message.reply_markup, shuffle_button_text="▶️", shuffle_button_callback_data="shuffle", settings_data=settings_data, current_phrase=current_phrase))


    elif data.startswith("show_example"):
        phrase = data.split(":")[1]
        show_example_callback(update, context, phrase)

    elif data == "change_phrase":
        send_random_phrase(context.user_data, query=query)

    elif data == "accept_challenge":
        # Change the status of the additional challenge to "Accepted"
        context.chat_data["additional_challenge_status"] = AdditionalChallengeStatus.ACCEPTED.value
        # Store the message ID of the accepted challenge
        context.chat_data["accepted_challenge_id"] = update.callback_query.message.message_id
        # Edit the button text to "Accepted ✅"
        accepted_challenge_button = InlineKeyboardButton("Accepted ✅", callback_data="accepted_challenge")
        accepted_challenge_markup = InlineKeyboardMarkup([[accepted_challenge_button]])
        update.callback_query.edit_message_reply_markup(reply_markup=accepted_challenge_markup)
        print(f"Accepted challenge with message ID {update.callback_query.message.message_id}.")
        print(f"additional_challenge_status set to: {context.chat_data['additional_challenge_status']}")
        print(f"accepted_challenge_id set to: {context.chat_data['accepted_challenge_id']}")

def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    current_phrase = context.user_data.get("current_phrase", "")
    username = update.message.from_user.first_name

    # Check if the message is a reply and in a group chat
    if update.message.chat.type in ["group", "supergroup"]:
        if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != context.bot.id:
            return
    elif update.message.chat.type != "private":
        return

    formatted_message_text = message_entities_to_html(update.message)

    accepted_challenge_info = (context.chat_data.get("additional_challenge_status", AdditionalChallengeStatus.NONE.value),
                           context.chat_data.get("accepted_challenge_id"))


    # Debugging information
    print(f"handle_message called with user message: {message_text}")
    print(f"Current phrase: {current_phrase}")
    print(f"additional_challenge_status before check: {context.chat_data.get('additional_challenge_status', AdditionalChallengeStatus.NONE.value)}")
    print(f"accepted_challenge_id before check: {context.chat_data.get('accepted_challenge_id')}")


    if is_valid_response(message_text, current_phrase):
        score = context.user_data.get("score", 0) + 1
        print(f"About to add regular point. Current score: {score-1}.")

    # Check if the user has accepted an additional challenge
        if accepted_challenge_info == (AdditionalChallengeStatus.ACCEPTED.value, update.message.reply_to_message.message_id):
            print("Inside condition block: accepted_challenge_info =", accepted_challenge_info)
            score += 1
            print("Additional challenge point added. Score is now {}.".format(score))

    # Reset the challenge status and ID, regardless of whether the user got an additional point
        context.user_data["additional_challenge_status"] = AdditionalChallengeStatus.NONE.value
        context.user_data["accepted_challenge_id"] = None

        print("After condition check: accepted_challenge_info =", accepted_challenge_info)

        context.user_data["score"] = score
        save_user_data(username, current_phrase, message_text, score)  # Save the score after adjusting for the additional challenge
        print("Regular point added. Score is now {}.".format(score))

        if "shuffle_job" in context.chat_data:
            context.chat_data["shuffle_job"].schedule_removal()
            context.chat_data.pop("shuffle_job", None)
            context.user_data["shuffle_active"] = False

    # Call the send_random_phrase function when a valid answer is detected
        send_random_phrase(context.user_data, context=context, update=update)

    # Remove all inline buttons from the message after a valid answer
        if update.message.reply_to_message.reply_markup:
            context.bot.edit_message_reply_markup(chat_id=update.effective_chat.id, message_id=update.message.reply_to_message.message_id, reply_markup=None)

        print(f"Checking for accepted challenge. Current status: {context.user_data.get('additional_challenge_status', AdditionalChallengeStatus.NONE.value)}, expected status: {AdditionalChallengeStatus.ACCEPTED.value}")
        print(f"Checking for accepted challenge. Reply message ID: {update.message.reply_to_message.message_id}, accepted challenge ID: {context.user_data.get('accepted_challenge_id')}")

    elif check_message_length(message_text, current_phrase):
        print("User typed the same word.")
        send_or_edit_message(update, context, update.effective_chat.id, None, "Хорошая попытка, но нет.", None)

    else:
        print("Invalid response.")
        game_over_message(update, context)

    if context.chat_data.get("additional_challenge_status", AdditionalChallengeStatus.NONE.value) == AdditionalChallengeStatus.SENT.value and update.message.reply_to_message.text == "Here is your additional challenge! Reply to this message for extra points.":
        score += 1
        context.user_data["additional_challenge_status"] = AdditionalChallengeStatus.ACCEPTED.value

    # Edit the message to indicate that the challenge was accepted
        try:
            context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                text=f"{update.message.text}\n\nChallenge accepted!",
                parse_mode="HTML",
                reply_markup=ReplyMarkup
        )
        except telegram.error.BadRequest as e:
            if str(e) != "Message is not modified":
                print(f"Error occurred while sending the message text: {e}")

def game_over_message(update: Update, context: CallbackContext) -> None:
    score = context.user_data.get("score", 0)
    first_name = update.message.from_user.first_name
    context.user_data["score"] = 0
    game_over_text = f"{first_name}, ты сделал всё, что мог!\nТвой счёт: {score}"
    keyboard = [
        [InlineKeyboardButton("Сделать лучше 😎", callback_data="start_game")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Stop shuffle if it's active
    if context.user_data.get("shuffle_active", False):
        context.user_data["shuffle_active"] = False
        job = context.chat_data.pop("shuffle_job", None)
        if job:
            job.schedule_removal()

    # Check if the game over message has already been sent
    if "game_over_sent" not in context.user_data or not context.user_data["game_over_sent"]:
        context.user_data["game_over_sent"] = True
        update.message.reply_text(game_over_text, reply_markup=reply_markup)