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
from config import FOLDER_DICT, JSON_FILE, SQL_FILE, config
from garmin_device_adaptor import wrap_device_info
from garmin_sync import Garmin, get_downloaded_ids
from garmin_sync import download_new_activities


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
    # auth_domain = (
    #     "CN" if options.is_cn else config("sync", "garmin", "authentication_domain")
    # )
    auth_domain = "CN"
    is_only_running = options.only_run
    if secret_string_cn is None or secret_string_global is None:
        print("Missing argument nor valid configuration file")
        sys.exit(1)
    folder = FOLDER_DICT.get("fit")
    # make gpx or tcx dir
    if not os.path.exists(folder):
        os.mkdir(folder)
    downloaded_ids = get_downloaded_ids(folder)
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        download_new_activities(
            secret_string_cn,
            auth_domain,
            downloaded_ids,
            is_only_running,
            folder,
            "fit",
        )
    )
    loop.run_until_complete(future)
    new_ids = future.result()
    to_upload_files = [
        os.path.join(folder, f"{i}.fit")
        for i in new_ids
        if os.path.exists(os.path.join(folder, f"{i}.fit"))
    ]
    print("Files to sync:" + " ".join(to_upload_files))
    garmin_global_client = Garmin(
        secret_string_global,
        config("sync", "garmin", "authentication_domain"),
        is_only_running,
    )
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        garmin_global_client.upload_activities_files(to_upload_files, False)
    )
    loop.run_until_complete(future)
