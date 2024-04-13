import argparse
import json
import os
from sre_constants import SUCCESS
import time
from collections import namedtuple
import requests
from config import GPX_FOLDER
from Crypto.Cipher import AES
from config import OUTPUT_DIR
from stravalib.exc import ActivityUploadFailed, RateLimitTimeout
from utils import make_strava_client, upload_file_to_strava
from keep_sync import (
    login,
    get_all_keep_tracks,
    KEEP_DATA_TYPE_API,
    parse_raw_data_to_nametuple,
    get_to_download_runs_ids,
    get_single_run_data,
)

"""
Only provide the ability to sync data from Keep's multiple sport types to Strava's corresponding sport types to help those who use multiple devices like me, the web page presentation still uses Strava (or refer to nike_to_strava_sync.py to modify it to suit you).
My own best practices:
1. running/hiking/Cycling (Huawei/OPPO) -> Keep
2. Keep -> Strava (add this scripts to run_data_sync.yml)
3. Road Cycling(Garmin) -> Strava.
4. running_page(Strava)

"""


def get_all_keep_tracks(email, password, old_tracks_ids, with_download_gpx=True):
    if with_download_gpx and not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)
    s = requests.Session()
    s, headers = login(s, email, password)
    tracks = []
    for api in KEEP_DATA_TYPE_API:
        runs = get_to_download_runs_ids(s, headers, api)
        runs = [run for run in runs if run.split("_")[1] not in old_tracks_ids]
        print(f"{len(runs)} new keep {api} data to generate")
        old_gpx_ids = os.listdir(GPX_FOLDER)
        old_gpx_ids = [i.split(".")[0] for i in old_gpx_ids if not i.startswith(".")]
        for run in runs:
            print(f"parsing keep id {run}")
            try:
                run_data = get_single_run_data(s, headers, run, api)
                track = parse_raw_data_to_nametuple(
                    run_data, old_gpx_ids, s, with_download_gpx
                )
                # By default only outdoor sports have latlng as well as GPX.
                if track.start_latlng is not None:
                    file_path = namedtuple("x", "gpx_file_path")(
                        os.path.join(GPX_FOLDER, str(track.id) + ".gpx")
                    )
                else:
                    file_path = namedtuple("x", "gpx_file_path")(None)
                track = namedtuple("y", track._fields + file_path._fields)(
                    *(track + file_path)
                )
                tracks.append(track)
            except Exception as e:
                print(f"Something wrong paring keep id {run}" + str(e))
    return tracks


def run_keep_sync(email, password, with_download_gpx=True):
    keep2strava_bk_path = os.path.join(OUTPUT_DIR, "keep2strava.json")
    if not os.path.exists(keep2strava_bk_path):
        file = open(keep2strava_bk_path, "w")
        file.close()
        content = []
    else:
        with open(keep2strava_bk_path) as f:
            try:
                content = json.loads(f.read())
            except:
                content = []
    old_tracks_ids = [str(a["run_id"]) for a in content]
    new_tracks = get_all_keep_tracks(email, password, old_tracks_ids, with_download_gpx)

    return new_tracks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phone_number", help="keep login phone number")
    parser.add_argument("password", help="keep login password")
    parser.add_argument("client_id", help="strava client id")
    parser.add_argument("client_secret", help="strava client secret")
    parser.add_argument("strava_refresh_token", help="strava refresh token")

    options = parser.parse_args()
    new_tracks = run_keep_sync(options.phone_number, options.password, True)

    # to strava.
    print("Need to load all gpx files maybe take some time")
    last_time = 0
    client = make_strava_client(
        options.client_id, options.client_secret, options.strava_refresh_token
    )

    index = 1
    print(f"{len(new_tracks)} gpx files is going to upload")
    print(f"Up to {len(new_tracks)} files are waiting to be uploaded")
    uploaded_file_paths = []
    for track in new_tracks:
        if track.gpx_file_path is not None:
            try:
                upload_file_to_strava(client, track.gpx_file_path, "gpx", False)
                uploaded_file_paths.append(track)
            except RateLimitTimeout as e:
                timeout = e.timeout
                print(f"Strava API Rate Limit Timeout. Retry in {timeout} seconds\n")
                time.sleep(timeout)
                # try previous again
                upload_file_to_strava(client, track.gpx_file_path, "gpx", False)
                uploaded_file_paths.append(track)
            except ActivityUploadFailed as e:
                print(f"Upload faild error {str(e)}")
            # spider rule
            time.sleep(1)
        else:
            # for no gps data, like indoorRunning.
            uploaded_file_paths.append(track)
    time.sleep(10)

    keep2strava_bk_path = os.path.join(OUTPUT_DIR, "keep2strava.json")
    with open(keep2strava_bk_path, "r") as f:
        try:
            content = json.loads(f.read())
        except:
            content = []
    content.extend(
        [
            dict(
                run_id=track.id,
                name=track.name,
                type=track.type,
                gpx_file_path=track.gpx_file_path,
            )
            for track in uploaded_file_paths
        ]
    )
    with open(keep2strava_bk_path, "w") as f:
        json.dump(content, f, indent=0)

    # del gpx
    for track in new_tracks:
        if track.gpx_file_path is not None:
            os.remove(track.gpx_file_path)
        else:
            continue
