import argparse
import os
import time
from datetime import datetime

from config import TCX_FOLDER
from rich import print
from strava_sync import run_strava_sync
from tcxparser import TCXParser

from utils import make_strava_client


def get_last_time(client):
    """
    if there is no activities cause exception return 0
    """
    try:
        activity = None
        activities = client.get_activities(limit=10)
        # for else in python if you don't know please google it.
        for a in activities:
            if a.type == "Run":
                activity = a
                break
        else:
            return 0
        end_date = activity.start_date + activity.elapsed_time
        return int(datetime.timestamp(end_date))
    except Exception as e:
        print(f"Something wrong to get last time err: {str(e)}")
        return 0


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
        if int(i[0].time_objects()[0].timestamp()) > last_time
    }

    return sorted(list(tcx_files_dict.keys())), tcx_files_dict


def upload_tcx(client, file_name):
    with open(file_name, "rb") as f:
        r = client.upload_activity(activity_file=f, data_type="tcx")
        try:
            r.wait()
            print(file_name)
            print("===== waiting for upload ====")
            print(r.status, f"strava id: {r.activity_id}")
        except Exception as e:
            print(str(e))


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
    last_time = get_last_time(client)
    to_upload_time_list, to_upload_dict = get_to_generate_files(last_time)
    for i in to_upload_time_list:
        tcx_file = to_upload_dict.get(i)
        upload_tcx(client, tcx_file)

    time.sleep(10)
    run_strava_sync(
        options.client_id, options.client_secret, options.strava_refresh_token
    )
