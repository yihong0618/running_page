import argparse
import asyncio
from datetime import datetime

from garmin_sync import Garmin
from strava_sync import run_strava_sync
from stravaweblib import DataFormat, WebClient
from utils import make_strava_client


async def upload_to_activities(
    garmin_client, strava_client, strava_web_client, format, use_fake_garmin_device
):
    last_activity = await garmin_client.get_activities(0, 1)
    if not last_activity:
        print("no garmin activity")
        filters = {}
    else:
        # is this startTimeGMT must have ?
        after_datetime_str = last_activity[0]["startTimeGMT"]
        after_datetime = datetime.strptime(after_datetime_str, "%Y-%m-%d %H:%M:%S")
        print("garmin last activity date: ", after_datetime)
        filters = {"after": after_datetime}
    strava_activities = list(strava_client.get_activities(**filters))
    files_list = []
    print("strava activities size: ", len(strava_activities))
    if not strava_activities:
        print("no strava activity")
        return files_list

    # strava rate limit
    for i in sorted(strava_activities, key=lambda i: int(i.id)):
        try:
            data = strava_web_client.get_activity_data(i.id, fmt=format)
            files_list.append(data)
        except Exception as ex:
            print("get strava data error: ", ex)
    await garmin_client.upload_activities_original_from_strava(
        files_list, use_fake_garmin_device
    )
    return files_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("strava_client_id", help="strava client id")
    parser.add_argument("strava_client_secret", help="strava client secret")
    parser.add_argument("strava_refresh_token", help="strava refresh token")
    parser.add_argument(
        "secret_string", nargs="?", help="secret_string fro get_garmin_secret.py"
    )
    parser.add_argument("strava_email", nargs="?", help="email of strava")
    parser.add_argument("strava_password", nargs="?", help="password of strava")
    parser.add_argument("strava_jwt", nargs="?", help="jwt token of strava")
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin account is cn",
    )
    parser.add_argument(
        "--use_fake_garmin_device",
        action="store_true",
        default=False,
        help="whether to use a faked Garmin device",
    )
    options = parser.parse_args()
    strava_client = make_strava_client(
        options.strava_client_id,
        options.strava_client_secret,
        options.strava_refresh_token,
    )
    if options.strava_jwt:
        strava_web_client = WebClient(
            access_token=strava_client.access_token,
            jwt=options.strava_jwt,
        )
    elif options.strava_email and options.strava_password:
        strava_web_client = WebClient(
            access_token=strava_client.access_token,
            email=options.strava_email,
            password=options.strava_password,
        )

    garmin_auth_domain = "CN" if options.is_cn else ""

    try:
        garmin_client = Garmin(options.secret_string, garmin_auth_domain)
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(
            upload_to_activities(
                garmin_client,
                strava_client,
                strava_web_client,
                DataFormat.ORIGINAL,
                options.use_fake_garmin_device,
            )
        )
        loop.run_until_complete(future)
    except Exception as err:
        print(err)

    # Run the strava sync
    run_strava_sync(
        options.strava_client_id,
        options.strava_client_secret,
        options.strava_refresh_token,
    )
