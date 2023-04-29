import json
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load config
def load_config(filename: str) -> dict:
    with open(filename, "r") as file:
        config = json.load(file)
    return config

config = load_config("config.json")
