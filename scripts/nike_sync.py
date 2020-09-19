import json
import datetime
import logging
import os.path
import sys
import argparse
import time

import httpx

BASE_URL = "https://api.nike.com/sport/v3/me"
TOKEN_REFRESH_URL = "https://unite.nike.com/tokenRefresh"
OUTPUT_DIR = "activities"
NIKE_CLIENT_ID = "HlHa2Cje3ctlaOqnxvgZXNaAs7T9nAuH"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nike_sync")


class Nike:
    def __init__(self, refresh_token):
        self.client = httpx.Client()

        response = self.client.post(
            TOKEN_REFRESH_URL,
            json={
                "refresh_token": refresh_token,
                "client_id": NIKE_CLIENT_ID,
                "grant_type": "refresh_token",
            },
            timeout=60
        )
        response.raise_for_status()

        access_token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

    def get_activities_since_timestamp(self, timestamp):
        return self.request("activities/after_time", timestamp)

    def get_activities_since_id(self, activity_id):
        try:
            return self.request("activities/after_id", activity_id)
        except:
            print("retry")
            time.sleep(3)
            return self.request("activities/after_id", activity_id)

    def get_activity(self, activity_id):
        try:
            return self.request("activity", f"{activity_id}?metrics=ALL")
        except:
            print("retry")
            time.sleep(3)
            return self.request("activity", f"{activity_id}?metrics=ALL")

    def request(self, resource, selector):
        url = f"{BASE_URL}/{resource}/{selector}"
        logger.info(f"GET: {url}")
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()


def run(refresh_token):
    nike = Nike(refresh_token)
    last_id = get_last_id()

    logger.info(f"Running from ID {last_id}")

    while True:
        if last_id is not None:
            data = nike.get_activities_since_id(last_id)
        else:
            data = nike.get_activities_since_timestamp(0)

        last_id = data["paging"].get("after_id")
        activities = data["activities"]

        logger.info(f"Found {len(activities)} new activities")

        for activity in activities:
            full_activity = nike.get_activity(activity["id"])
            save_activity(full_activity)

        if last_id is None or not activities:
            logger.info(f"Found no new activities, finishing")
            return


def save_activity(activity):
    activity_id = activity["id"]
    activity_time = activity["end_epoch_ms"]
    print(activity_time)
    logger.info(f"Saving activity {activity_id}")
    path = os.path.join(OUTPUT_DIR, f"{activity_time}.json")
    try:
        with open(path, "w") as f:
            json.dump(sanitise_json(activity), f, indent=4)
    except Exception:
        os.unlink(path)
        raise


def get_last_id():
    try:
        file_names = os.listdir(OUTPUT_DIR)
        file_names.sort()
        file_name = file_names[-1]
        with open(os.path.join(OUTPUT_DIR, file_name)) as f:
            data = json.load(f)
        logger.info(f"Last update from {data['id']}")
        return data["id"]
    # easy solution when error happens no last id
    except:
        return None


def sanitise_json(d):
    """
    Gatsby's JSON loading for GraphQL queries doesn't support "." characters in
    names, which Nike uses a lot for reverse-domain notation.

    We recursively transform all dict keys to use underscores instead.
    """

    def _transform_key(key):
        return key.replace(".", "_")

    if isinstance(d, dict):
        return {_transform_key(k): sanitise_json(v) for k, v in d.items()}

    if isinstance(d, (tuple, list)):
        return [sanitise_json(x) for x in d]

    return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("refresh_token", help="API access token for nike.com")
    options = parser.parse_args()
    run(options.refresh_token)
