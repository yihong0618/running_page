"""
Python 3 API wrapper for Garmin Connect to get your statistics.
Copy most code from https://github.com/cyberjunky/python-garminconnect
"""

import argparse
import asyncio
import logging
import os
import sys
import time
import traceback
import zipfile
from io import BytesIO

import aiofiles
import cloudscraper
import garth
import httpx
from config import FIT_FOLDER, GPX_FOLDER, JSON_FILE, SQL_FILE, config
from garmin_device_adaptor import wrap_device_info
from garmin_sync import Garmin, get_downloaded_ids
from garmin_sync import (
    download_new_activities,
    gather_with_concurrency,
    get_activities_name,
)
from synced_data_file_logger import (
    load_synced_activity_list,
    save_synced_activity_list,
    load_fit_name_mapping,
    save_fit_name_mapping,
)
from utils import make_activities_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cn_secret_string", nargs="?", help="secret_string fro get_garmin_secret.py"
    )
    parser.add_argument(
        "global_secret_string", nargs="?", help="secret_string fro get_garmin_secret.py"
    )
    parser.add_argument(
        "--only-run",
        dest="only_run",
        action="store_true",
        help="if is only for running",
    )

    options = parser.parse_args()
    secret_string_cn = options.cn_secret_string
    secret_string_global = options.global_secret_string
    auth_domain = "CN"
    is_only_running = options.only_run
    if secret_string_cn is None or secret_string_global is None:
        print("Missing argument nor valid configuration file")
        sys.exit(1)

    # Step 1:
    # Sync all activities from Garmin CN to Garmin Global in FIT format
    # If the activity is manually imported with a GPX, the GPX file will be synced

    # load synced activity list
    synced_activity = load_synced_activity_list()

    folder = FIT_FOLDER
    # make gpx or tcx dir
    if not os.path.exists(folder):
        os.mkdir(folder)

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        download_new_activities(
            secret_string_cn,
            auth_domain,
            synced_activity,
            is_only_running,
            folder,
            "fit",
        )
    )
    loop.run_until_complete(future)
    new_ids = future.result()

    # Step 2:
    # activity name not included in fit file
    # manually fetch activity name, save to file for later use
    old_name_mapping = load_fit_name_mapping()
    new_ids = new_ids - old_name_mapping.keys()
    if new_ids:
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(
            get_activities_name(secret_string_cn, auth_domain, new_ids)
        )
        loop.run_until_complete(future)
        names_mapping = future.result()
        names_mapping.update(old_name_mapping)
        save_fit_name_mapping(names_mapping)

    to_upload_files = []
    for i in new_ids:
        if os.path.exists(os.path.join(FIT_FOLDER, f"{i}.fit")):
            # upload fit files
            to_upload_files.append(os.path.join(FIT_FOLDER, f"{i}.fit"))
        elif os.path.exists(os.path.join(GPX_FOLDER, f"{i}.gpx")):
            # upload gpx files which are manually uploaded to garmin connect
            to_upload_files.append(os.path.join(GPX_FOLDER, f"{i}.gpx"))

    print("Files to sync:" + " ".join(to_upload_files))
    garmin_global_client = Garmin(
        secret_string_global,
        config("sync", "garmin", "authentication_domain"),
        is_only_running,
    )
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        garmin_global_client.upload_activities_files(to_upload_files)
    )
    loop.run_until_complete(future)

    # Save synced activity list for speeding up
    synced_activity.extend(new_ids)
    save_synced_activity_list(synced_activity)

    # Step 3:
    # Generate track from fit/gpx file
    make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE, file_suffix="gpx")
    make_activities_file(SQL_FILE, FIT_FOLDER, JSON_FILE, file_suffix="fit")
