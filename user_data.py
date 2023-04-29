import csv
from typing import List, Dict

phrase_hash_to_phrase = {}

def save_user_data(username: str, current_phrase: str, user_message: str, score: int) -> None:
    with open("user_data.csv", mode="a", newline="", encoding="utf-8") as file:
        fieldnames = ["username", "current_phrase", "user_message", "score"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Uncomment the following line to write the header only once when the file is empty.
        # if file.tell() == 0:
        #     writer.writeheader()

        writer.writerow({
            "username": username,
            "current_phrase": current_phrase,
            "user_message": user_message,
            "score": score
        })


def read_user_data() -> list:
    data = []

    with open("user_data.csv", mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 4:
                username, current_phrase, user_message, score = row
                data.append({"username": username, "current_phrase": current_phrase, "user_message": user_message, "score": score})

    return data


def generate_leaderboard(data: list) -> str:
    scores = {}

    for row in data:
        username = row["username"]
        score = int(row["score"])

        if username not in scores or scores[username] < score:
            scores[username] = score

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]

    leaderboard_text = "🏆 Чемпионы 🏆\n"
    for i, (username, score) in enumerate(sorted_scores, start=1):
        leaderboard_text += f"{i}. {username} - {score}\n"

    return leaderboard_text
