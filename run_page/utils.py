import json
import time
from datetime import datetime

import pytz

try:
    from rich import print
except Exception:
    pass
from generator import Generator
from stravalib.client import Client
from stravalib.exc import RateLimitExceeded


def adjust_time(time, tz_name):
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    return time + tc_offset


def adjust_time_to_utc(time, tz_name):
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    return time - tc_offset


def adjust_timestamp_to_utc(timestamp, tz_name):
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    delta = int(tc_offset.total_seconds())
    return int(timestamp) - delta


def to_date(ts):
    """
    Parse ISO format timestamp string to datetime object.
    Uses datetime.fromisoformat() for standard ISO format strings.
    Falls back to strptime for non-standard formats.
    """
    # Try fromisoformat first (Python 3.7+)
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        # Fallback to strptime for non-standard formats
        ts_fmts = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]
        for ts_fmt in ts_fmts:
            try:
                return datetime.strptime(ts, ts_fmt)
            except ValueError:
                pass
        raise ValueError(f"cannot parse timestamp {ts} into date")


def make_activities_file(
    sql_file, data_dir, json_file, file_suffix="gpx", activity_title_dict={}
):
    generator = Generator(sql_file)
    generator.sync_from_data_dir(
        data_dir, file_suffix=file_suffix, activity_title_dict=activity_title_dict
    )
    activities_list = generator.load()
    with open(json_file, "w") as f:
        json.dump(activities_list, f)


def make_strava_client(client_id, client_secret, refresh_token):
    client = Client()

    refresh_response = client.refresh_access_token(
        client_id=client_id, client_secret=client_secret, refresh_token=refresh_token
    )
    client.access_token = refresh_response["access_token"]
    return client


def get_strava_last_time(client, is_milliseconds=True):
    """
    if there is no activities cause exception return 0
    """
    try:
        activity = None
        activities = client.get_activities(limit=10)
        activities = list(activities)
        activities.sort(key=lambda x: x.start_date, reverse=True)
        # for else in python if you don't know please google it.
        for a in activities:
            if a.type == "Run":
                activity = a
                break
        else:
            return 0
        end_date = activity.start_date + activity.elapsed_time
        last_time = int(datetime.timestamp(end_date))
        if is_milliseconds:
            last_time = last_time * 1000
        return last_time
    except Exception as e:
        print(f"Something wrong to get last time err: {str(e)}")
        return 0


def upload_file_to_strava(client, file_name, data_type, force_to_run=True):
    with open(file_name, "rb") as f:
        try:
            if force_to_run:
                r = client.upload_activity(
                    activity_file=f, data_type=data_type, activity_type="run"
                )
            else:
                r = client.upload_activity(activity_file=f, data_type=data_type)

        except RateLimitExceeded as e:
            timeout = e.timeout
            print(f"Strava API Rate Limit Exceeded. Retry after {timeout} seconds")
            time.sleep(timeout)
            if force_to_run:
                r = client.upload_activity(
                    activity_file=f, data_type=data_type, activity_type="run"
                )
            else:
                r = client.upload_activity(activity_file=f, data_type=data_type)
        print(
            f"Uploading {data_type} file: {file_name} to strava, upload_id: {r.upload_id}."
        )
