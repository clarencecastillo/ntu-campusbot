import json
import os

SAVE_FILE_NAME = "save_data.json"
LOG_TAG = "commons"

def set_data(key, value):
    save_data = get_data()
    with open(SAVE_FILE_NAME, 'w') as save_file:
        save_data[key] = value
        json.dump(save_data, save_file)

def get_data(key = None):
    with open(SAVE_FILE_NAME, 'r') as save_file:
        save_data = json.load(save_file)
        return (save_data if not key else save_data[key])

def log(tag, message):
    print("<" + tag.upper() + ">", message)
