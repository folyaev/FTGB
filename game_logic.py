import random
from typing import List
from config import config
from phrases import phrases

class GameState:
    def __init__(self):
        self.phrases = phrases

    def __str__(self) -> str:
        return f"GameState(phrases={self.phrases})"

    def get_random_phrase(self) -> str:
        return random.choice(self.phrases)

game_state = GameState()
