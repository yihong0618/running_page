import argparse
import json
import os
import time
from collections import namedtuple
from config import GPX_FOLDER
from config import OUTPUT_DIR
from stravalib.exc import ActivityUploadFailed, RateLimitTimeout
from utils import make_strava_client, upload_file_to_strava
from keep_sync import KEEP_SPORT_TYPES, get_all_keep_tracks
from strava_sync import run_strava_sync

"""
Only provide the ability to sync data from Keep's multiple sport types to Strava's corresponding sport types to help those who use multiple devices like me, the web page presentation still uses Strava (or refer to nike_to_strava_sync.py to modify it to suit you).
My own best practices:
1. running/hiking/Cycling (Huawei/OPPO) -> Keep
2. Keep -> Strava (add this scripts to run_data_sync.yml)
3. Road Cycling(Garmin) -> Strava.
4. running_page(Strava)

"""
KEEP2STRAVA_BK_PATH = os.path.join(OUTPUT_DIR, "keep2strava.json")


def run_keep_sync(email, password, keep_sports_data_api, with_download_gpx=False):
    if not os.path.exists(KEEP2STRAVA_BK_PATH):
        file = open(KEEP2STRAVA_BK_PATH, "w")
        file.close()
        content = []
    else:
        with open(KEEP2STRAVA_BK_PATH) as f:
            try:
                content = json.loads(f.read())
            except:
                content = []
    old_tracks_ids = [str(a["run_id"]) for a in content]
    _new_tracks = get_all_keep_tracks(
        email, password, old_tracks_ids, keep_sports_data_api, True
    )
    new_tracks = []
    for track in _new_tracks:
        # By default only outdoor sports have latlng as well as GPX.
        if track.start_latlng is not None:
            file_path = namedtuple("x", "gpx_file_path")(
                os.path.join(GPX_FOLDER, str(track.id) + ".gpx")
            )
        else:
            file_path = namedtuple("x", "gpx_file_path")(None)
        track = namedtuple("y", track._fields + file_path._fields)(*(track + file_path))
        new_tracks.append(track)

    return new_tracks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phone_number", help="keep login phone number")
    parser.add_argument("password", help="keep login password")
    parser.add_argument("client_id", help="strava client id")
    parser.add_argument("client_secret", help="strava client secret")
    parser.add_argument("strava_refresh_token", help="strava refresh token")
    parser.add_argument(
        "--sync-types",
        dest="sync_types",
        nargs="+",
        default=["running"],
        help="sync sport types from keep, default is running, you can choose from running, hiking, cycling",
    )

    options = parser.parse_args()
    for _tpye in options.sync_types:
        assert (
            _tpye in KEEP_SPORT_TYPES
        ), f"{_tpye} are not supported type, please make sure that the type entered in the {KEEP_SPORT_TYPES}"
    new_tracks = run_keep_sync(
        options.phone_number, options.password, options.sync_types, True
    )

    # to strava.
    print("Need to load all gpx files maybe take some time")
    last_time = 0
    client = make_strava_client(
        options.client_id, options.client_secret, options.strava_refresh_token
    )

    index = 1
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

    # This file is used to record which logs have been uploaded to strava
    # to avoid intrusion into the data.db resulting in double counting of data.
    with open(KEEP2STRAVA_BK_PATH, "r") as f:
        try:
            content = json.loads(f.read())
        except:
            content = []

    # Extend and Save the successfully uploaded log to the backup file.
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
    with open(KEEP2STRAVA_BK_PATH, "w") as f:
        json.dump(content, f, indent=0)

    # del the uploaded GPX file.
    for track in uploaded_file_paths:
        if track.gpx_file_path is not None:
            os.remove(track.gpx_file_path)
        else:
            continue

    run_strava_sync(
        options.client_id, options.client_secret, options.strava_refresh_token
    )
