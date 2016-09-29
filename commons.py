'''
This file contains the common methods shared between all other components. Uses
standard setter/getter to access shared data storage.
'''

import json
import os

SAVE_FILE_NAME = "save_data.json"
LOG_TAG = "commons"

def set_data(key, value):

    '''
    Adds specified key to the save file with the given value, or update that
    key's value if it already exists.

    @param key: unique key to store the value with
    @param value: the value you want to store in the storage
    '''

    save_data = get_data()
    with open(SAVE_FILE_NAME, 'w') as save_file:
        save_data[key] = value
        json.dump(save_data, save_file)

def get_data(key = None):

    '''
    Returns the entire shared data as a dictionary. Pass a key parameter to
    return only that particular value.

    @param key: optional key to extract a specific value
    '''

    with open(SAVE_FILE_NAME, 'r') as save_file:
        save_data = json.load(save_file)
        return (save_data if not key else save_data[key])

def log(tag, message):

    '''
    Standardised logging including tags.

    @param tag: tag which describes the scope of where the log is called
    @param message: the message to be logged
    '''

    print("<" + tag.upper() + ">", message)
