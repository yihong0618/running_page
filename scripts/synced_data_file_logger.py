import os
from config import SYNCED_FILE_NAME
import json


def save_synced_data_file_list(data_dir: str, file_list: list):
    data_dir = os.path.abspath(data_dir)
    synced_json_file = os.path.join(data_dir, SYNCED_FILE_NAME)

    old_list = load_synced_file_list(data_dir)

    with open(synced_json_file, "w") as f:
        file_list.extend(old_list)

        json.dump(file_list, f)


def load_synced_file_list(data_dir: str):
    data_dir = os.path.abspath(data_dir)
    synced_json_file = os.path.join(data_dir, SYNCED_FILE_NAME)

    if os.path.exists(synced_json_file):
        with open(synced_json_file, "r") as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"json load {synced_json_file} \nerror {e}")
                pass

    return []
