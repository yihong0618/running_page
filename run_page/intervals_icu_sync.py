import argparse
import gzip
import os
import time
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth

from config import JSON_FILE, SQL_FILE, FOLDER_DICT
from utils import make_activities_file

BASE_URL = "https://intervals.icu/api/v1"
RUNNING_TYPES = ["Run", "VirtualRun", "TrailRun"]


class IntervalsICU:
    def __init__(self, athlete_id, api_key):
        self.athlete_id = athlete_id
        self.api_key = api_key
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth("API_KEY", api_key)
        self.session.headers["Accept"] = "application/json"

    def get_activities(self, oldest, newest):
        url = (
            f"{BASE_URL}/athlete/{self.athlete_id}/activities"
            f"?oldest={oldest}&newest={newest}"
        )
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def download_activity_file(self, activity_id, file_type, output_folder):
        url = f"{BASE_URL}/activity/{activity_id}/file"
        numeric_id = str(activity_id).lstrip("i")
        output_path = os.path.join(output_folder, f"{numeric_id}.{file_type}")

        try:
            response = self.session.get(url)
            response.raise_for_status()
            content = response.content
            # Decompress only if gzip-compressed (magic bytes: 1f 8b)
            if content[:2] == bytes([0x1f, 0x8b]):
                content = gzip.decompress(content)

            with open(output_path, "wb") as f:
                f.write(content)

            return output_path
        except Exception:
            return None


def get_downloaded_ids(folder):
    return [i.split(".")[0] for i in os.listdir(folder) if not i.startswith(".")]


def run():
    parser = argparse.ArgumentParser(
        description="Sync running activities from Intervals.icu"
    )
    parser.add_argument("athlete_id", help="Intervals.icu athlete ID")
    parser.add_argument("api_key", help="Intervals.icu API key")
    parser.add_argument(
        "--start-date",
        default="2015-01-01",
        help="Oldest date to sync (YYYY-MM-DD, default: 2015-01-01)",
    )
    parser.add_argument(
        "--all",
        dest="sync_all",
        action="store_true",
        help="Sync all activity types, not just running",
    )
    options = parser.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    client = IntervalsICU(options.athlete_id, options.api_key)
    activities = client.get_activities(oldest=options.start_date, newest=today)

    if not options.sync_all:
        activities = [
            activity for activity in activities if activity.get("type") in RUNNING_TYPES
        ]

    # Only activities with a declared file type and supported folder mapping
    candidates = []
    for activity in activities:
        file_type = activity.get("file_type")
        if not file_type:
            continue
        file_type = str(file_type).lower()
        if file_type not in FOLDER_DICT:
            continue
        candidates.append((activity, file_type))

    downloaded_count = 0
    used_file_types = set()
    total = len(candidates)

    for n, (activity, file_type) in enumerate(candidates, start=1):
        output_folder = FOLDER_DICT[file_type]
        numeric_id = str(activity["id"]).lstrip("i")
        output_path = os.path.join(output_folder, f"{numeric_id}.{file_type}")

        if os.path.exists(output_path):
            continue

        activity_id = activity["id"]
        print(f"Downloading activity {activity_id} ({n}/{total})...")

        try:
            saved_path = client.download_activity_file(
                activity_id, file_type, output_folder
            )
            if saved_path:
                downloaded_count += 1
                used_file_types.add(file_type)
            else:
                print(
                    f"Warning: Failed to download activity {activity_id}: unknown error"
                )
        except Exception as e:
            print(f"Warning: Failed to download activity {activity_id}: {e}")

        time.sleep(1)

    for file_type in used_file_types:
        make_activities_file(
            SQL_FILE, FOLDER_DICT[file_type], JSON_FILE, file_suffix=file_type
        )

    print(f"Done. Downloaded {downloaded_count} new activities.")


if __name__ == "__main__":
    run()
