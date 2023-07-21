# random_phrase.py

import random

def generate_random_phrase(phrases, used_phrases):
    """
    Generate a random phrase that hasn't been used yet.

    :param phrases: A list of all possible phrases.
    :param used_phrases: A list of phrases that have been used.
    :return: A new phrase that hasn't been used yet.
    """
    available_phrases = [phrase for phrase in phrases if phrase not in used_phrases]

    # If there are no available phrases, reset the used phrases
    if not available_phrases:
        used_phrases = []
        available_phrases = phrases

    # Choose a random phrase from the available ones
    random_phrase = random.choice(available_phrases)

    return random_phrase