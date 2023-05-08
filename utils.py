from user_data import read_user_data

def check_message_length(message_text: str, current_phrase: str) -> bool:
    return len(message_text) == len(current_phrase)

def jaccard_similarity(set1: set, set2: set) -> float:
    intersection_size = len(set1.intersection(set2))
    union_size = len(set1.union(set2))
    return intersection_size / union_size

def is_valid_response(user_message: str, current_phrase: str) -> bool:
    if len(user_message) < len(current_phrase):
        return False

    phrase_chars = set(current_phrase)
    if not phrase_chars:
        return False

    matching_chars = sum(1 for char in phrase_chars if char in user_message)
    matching_percentage = (matching_chars / len(phrase_chars)) * 100

    return matching_percentage >= 50

def get_word_frequencies() -> dict:
    data = read_user_data()
    word_frequencies = {}

    for row in data:
        current_phrase = row["current_phrase"]
        if current_phrase not in word_frequencies:
            word_frequencies[current_phrase] = 0
        word_frequencies[current_phrase] += 1

    return word_frequencies
