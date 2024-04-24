import argparse
import asyncio
import os
from datetime import datetime

from tcxreader.tcxreader import TCXReader

from config import TCX_FOLDER
from garmin_sync import Garmin


def get_to_generate_files(last_time):
    """
    return to one sorted list for next time upload
    """
    file_names = os.listdir(TCX_FOLDER)
    tcx = TCXReader()
    tcx_files = [
        (
            tcx.read(os.path.join(TCX_FOLDER, i), only_gps=False),
            os.path.join(TCX_FOLDER, i),
        )
        for i in file_names
        if i.endswith(".tcx")
    ]
    tcx_files_dict = {
        int(i[0].trackpoints[0].time.timestamp()): i[1]
        for i in tcx_files
        if len(i[0].trackpoints) > 0
        and int(i[0].trackpoints[0].time.timestamp()) > last_time
    }

    dict(sorted(tcx_files_dict.items()))

    return tcx_files_dict.values()


async def upload_tcx_files_to_garmin(options):
    print("Need to load all tcx files maybe take some time")
    garmin_auth_domain = "CN" if options.is_cn else ""
    garmin_client = Garmin(options.secret_string, garmin_auth_domain)

    last_time = 0
    if not options.all:
        print("upload new tcx to Garmin")
        last_activity = await garmin_client.get_activities(0, 1)
        if not last_activity:
            print("no garmin activity")
        else:
            after_datetime_str = last_activity[0]["startTimeGMT"]
            after_datetime = datetime.strptime(after_datetime_str, "%Y-%m-%d %H:%M:%S")
            last_time = datetime.timestamp(after_datetime)
    else:
        print("Need to load all tcx files maybe take some time")
    to_upload_dict = get_to_generate_files(last_time)

    await garmin_client.upload_activities_files(to_upload_dict)


if __name__ == "__main__":
    if not os.path.exists(TCX_FOLDER):
        os.mkdir(TCX_FOLDER)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "secret_string", nargs="?", help="secret_string fro get_garmin_secret.py"
    )
    parser.add_argument(
        "--all",
        dest="all",
        action="store_true",
        help="if upload to strava all without check last time",
    )
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin account is cn",
    )
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(upload_tcx_files_to_garmin(parser.parse_args()))
    loop.run_until_complete(future)
