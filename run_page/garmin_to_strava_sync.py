"""
new garmin ids to strava;
not the same logic as nike_to_strava_sync
"""

import argparse
import asyncio
import os
import sys
import time

from config import FOLDER_DICT, STRAVA_GARMIN_TYPE_DICT
from garmin_sync import download_new_activities, get_downloaded_ids
from strava_sync import run_strava_sync
from utils import make_strava_client, upload_file_to_strava

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("strava_client_id", help="strava client id")
    parser.add_argument("strava_client_secret", help="strava client secret")
    parser.add_argument("strava_refresh_token", help="strava refresh token")
    parser.add_argument(
        "secret_string", nargs="?", help="secret_string fro get_garmin_secret.py"
    )
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin accout is cn",
    )
    parser.add_argument(
        "--tcx",
        dest="download_file_type",
        action="store_const",
        const="tcx",
        default="gpx",
        help="to download personal documents or ebook",
    )
    options = parser.parse_args()
    strava_client = make_strava_client(
        options.strava_client_id,
        options.strava_client_secret,
        options.strava_refresh_token,
    )
    secret_string = options.secret_string
    garmin_auth_domain = "CN" if options.is_cn else ""
    email = options.secret_string
    file_type = options.download_file_type
    is_only_running = False
    if secret_string is None:
        print("Missing argument nor valid configuration file")
        sys.exit(1)
    folder = FOLDER_DICT.get(file_type, "gpx")
    downloaded_ids = get_downloaded_ids(folder)

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        download_new_activities(
            secret_string,
            garmin_auth_domain,
            downloaded_ids,
            is_only_running,
            folder,
            file_type,
        )
    )
    loop.run_until_complete(future)
    new_ids, id2title = future.result()
    print(f"To upload to strava {len(new_ids)} files")
    index = 1
    for i in new_ids:
        f = os.path.join(folder, f"{i}.{file_type}")
        upload_file_to_strava(strava_client, f, file_type, False)
        if index % 10 == 0:
            print("For the rate limit will sleep 10s")
            time.sleep(10)
        index += 1
        time.sleep(1)

    # Run the strava sync
    run_strava_sync(
        options.strava_client_id,
        options.strava_client_secret,
        options.strava_refresh_token,
    )
