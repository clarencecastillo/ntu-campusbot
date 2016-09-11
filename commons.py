import json
import os

FILE_NAME = "subscribers.json"

def init():
    global subscribers
    subscribers = load_subscribers() if os.path.isfile(FILE_NAME) else []

def new_subscriber(id, name):
    subscribers.append(id)
    print("New subscriber:", name)
    save_subscribers(subscribers)

def remove_subscriber(id, name):
    subscribers.remove(id)
    print("Removed subscriber:", name)
    save_subscribers(subscribers)

def save_subscribers(subscribers_list):
    with open(FILE_NAME, 'w') as subcribers_list_file:
        save_data = {'subscribers' : subscribers_list}
        json.dump(save_data, subcribers_list_file)

def load_subscribers():
    with open(FILE_NAME) as subcribers_list_file:
        load_data = json.load(subcribers_list_file)['subscribers']
        print("Loaded", len(load_data), "subscribers!")
        return load_data
