import argparse
import os
import time

from config import TCX_FOLDER
from strava_sync import run_strava_sync
from stravalib.exc import RateLimitTimeout, ActivityUploadFailed, RateLimitExceeded
from tcxparser import TCXParser

from utils import make_strava_client, get_strava_last_time, upload_file_to_strava


def get_to_generate_files(last_time):
    """
    reuturn to values one dict for upload
    and one sorted list for next time upload
    """
    file_names = os.listdir(TCX_FOLDER)
    tcx_files = [
        (TCXParser(os.path.join(TCX_FOLDER, i)), os.path.join(TCX_FOLDER, i))
        for i in file_names
        if i.endswith(".tcx")
    ]
    tcx_files_dict = {
        int(i[0].time_objects()[0].timestamp()): i[1]
        for i in tcx_files
        if len(i[0].time_objects()) > 0
        and int(i[0].time_objects()[0].timestamp()) > last_time
    }

    return sorted(list(tcx_files_dict.keys())), tcx_files_dict


if __name__ == "__main__":
    if not os.path.exists(TCX_FOLDER):
        os.mkdir(TCX_FOLDER)
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", help="strava client id")
    parser.add_argument("client_secret", help="strava client secret")
    parser.add_argument("strava_refresh_token", help="strava refresh token")
    options = parser.parse_args()
    # upload new tcx to strava
    print("Need to load all tcx files maybe take some time")
    client = make_strava_client(
        options.client_id, options.client_secret, options.strava_refresh_token
    )
    parser.add_argument(
        "--all",
        dest="all",
        action="store_true",
        help="if upload to strava all without check last time",
    )
    last_time = 0
    if not options.all:
        last_time = get_strava_last_time(client, is_milliseconds=False)
    to_upload_time_list, to_upload_dict = get_to_generate_files(last_time)
    index = 1
    for i in to_upload_time_list:
        tcx_file = to_upload_dict.get(i)
        try:
            upload_file_to_strava(client, tcx_file, "tcx")
        except RateLimitTimeout as e:
            timeout = e.timeout
            print(f"Strava API Rate Limit Timeout. Retry in {timeout} seconds")
            print()
            time.sleep(timeout)
            # try previous again
            upload_file_to_strava(client, tcx_file, "tcx")

        except ActivityUploadFailed as e:
            print(f"Upload faild error {str(e)}")
        # spider rule
        time.sleep(1)

    time.sleep(10)
    run_strava_sync(
        options.client_id, options.client_secret, options.strava_refresh_token
    )
