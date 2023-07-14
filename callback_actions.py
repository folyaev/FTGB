from enum import Enum

class CallbackActions(Enum):
    START_GAME = "start_game"

class AdditionalChallengeStatus(Enum):
    NONE = 0
    SENT = 1
    ACCEPTED = 2