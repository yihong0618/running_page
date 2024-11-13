import os
from config import SYNCED_FILE, SYNCED_ACTIVITY_FILE
import json


def save_synced_data_file_list(file_list: list):
    old_list = load_synced_file_list()

    with open(SYNCED_FILE, "w") as f:
        file_list.extend(old_list)

        json.dump(file_list, f)


def save_synced_activity_list(activity_list: list):
    with open(SYNCED_ACTIVITY_FILE, "w") as f:
        json.dump(activity_list, f)


def load_synced_file_list():
    if os.path.exists(SYNCED_FILE):
        with open(SYNCED_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"json load {SYNCED_FILE} \nerror {e}")
                pass

    return []
