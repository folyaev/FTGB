import os
import logging
from typing import List
from config import config

def load_phrases(filename: str) -> List[str]:
    if not os.path.exists(filename):
        logging.warning(f"File {filename} not found. Using default phrases.")
    else:
        with open(filename, "r") as file:
            phrases = [line.strip() for line in file.readlines()]
        if phrases:
            return phrases

    # Fallback to default phrases
    return [
        "apple", "banana", "cherry", "pineapple", "grape",
        "I love programming", "Chatbot is fun", "Python is great"
    ]

phrases = load_phrases(config["phrases_file"])