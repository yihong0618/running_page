import argparse
import os
import time

import gpxpy as mod_gpxpy
from config import GPX_FOLDER
from strava_sync import run_strava_sync
from stravalib.exc import ActivityUploadFailed, RateLimitTimeout
from utils import get_strava_last_time, make_strava_client, upload_file_to_strava


def get_to_generate_files(last_time):
    """
    reuturn to values one dict for upload
    and one sorted list for next time upload
    """
    file_names = os.listdir(GPX_FOLDER)
    gpx_files = []
    for f in file_names:
        if f.endswith(".gpx"):
            file_path = os.path.join(GPX_FOLDER, f)
            with open(file_path, "rb") as r:
                try:
                    gpx = mod_gpxpy.parse(r)
                except Exception as e:
                    print(f"Something is wring with {file_path} err: {str(e)}")
                    continue
                # if gpx file has no start time we ignore it.
                if gpx.get_time_bounds()[0]:
                    gpx_files.append((gpx, file_path))
    gpx_files_dict = {
        int(i[0].get_time_bounds()[0].timestamp()): i[1]
        for i in gpx_files
        if int(i[0].get_time_bounds()[0].timestamp()) > last_time
    }
    return sorted(list(gpx_files_dict.keys())), gpx_files_dict


if __name__ == "__main__":
    if not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", help="strava client id")
    parser.add_argument("client_secret", help="strava client secret")
    parser.add_argument("strava_refresh_token", help="strava refresh token")
    parser.add_argument(
        "--all",
        dest="all",
        action="store_true",
        help="if upload to strava all without check last time",
    )
    options = parser.parse_args()
    # upload new tcx to strava
    print("Need to load all gpx files maybe take some time")
    last_time = 0
    client = make_strava_client(
        options.client_id, options.client_secret, options.strava_refresh_token
    )
    if not options.all:
        last_time = get_strava_last_time(client, is_milliseconds=False)
    to_upload_time_list, to_upload_dict = get_to_generate_files(last_time)
    index = 1
    print(f"{len(to_upload_time_list)} gpx files is going to upload")
    for i in to_upload_time_list:
        gpx_file = to_upload_dict.get(i)
        try:
            upload_file_to_strava(client, gpx_file, "gpx")
        except RateLimitTimeout as e:
            timeout = e.timeout
            print(f"Strava API Rate Limit Timeout. Retry in {timeout} seconds\n")
            time.sleep(timeout)
            # try previous again
            upload_file_to_strava(client, gpx_file, "gpx")

        except ActivityUploadFailed as e:
            print(f"Upload faild error {str(e)}")
        # spider rule
        time.sleep(1)

    time.sleep(10)
    run_strava_sync(
        options.client_id, options.client_secret, options.strava_refresh_token
    )
