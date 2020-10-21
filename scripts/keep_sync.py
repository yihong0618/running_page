import argparse
import base64
import json
import os
import zlib
from collections import namedtuple
from datetime import datetime

import gpxpy
import polyline
import pytz
import requests
from requests.sessions import session

from config import (GPX_FOLDER, JSON_FILE, NIKE_CLIENT_ID, OUTPUT_DIR,
                    SQL_FILE, TOKEN_REFRESH_URL)
from generator import Generator

start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")

# need to test
LOGIN_API = "https://api.gotokeep.com/v1.1/users/login"
RUN_DATA_API = "https://api.gotokeep.com/pd/v3/stats/detail?dateUnit=all&type=running"
RUN_LOG_API = "https://api.gotokeep.com/pd/v3/runninglog/{run_id}"


def login(session, mobile, passowrd):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
    data =  {"mobile": mobile, "password": passowrd}
    r = session.post(LOGIN_API, headers=headers, data=data)
    if r.ok:
        token = r.json()["data"]["token"]
        headers["Authorization"] = f"Bearer {token}"
        return session, headers


def get_to_download_runs_ids(session, headers):
    r = session.get(RUN_DATA_API, headers=headers)
    if r.ok:
        run_logs = r.json()["data"]["records"]
        return [i["logs"][0]["stats"]["id"] for i in run_logs]


def get_single_run_data(session, headers, run_id):
    r = session.get(RUN_LOG_API.format(run_id=run_id), headers=headers)
    if r.ok:
        return r.json()


def decode_runmap_data(text):
    run_points_data = zlib.decompress(base64.b64decode(text), 16+zlib.MAX_WBITS)
    run_points_data = json.loads(run_points_data)
    run_points_data = [[p["latitude"], p["longitude"]] for p in run_points_data]
    return run_points_data


def adjust_time(time, tz_name):
    tz = pytz.timezone(tz_name)
    time_local = time.astimezone(tz)
    return time_local
    

def parse_raw_data_to_nametuple(run_data):
    run_data = run_data["data"]
    run_points_data = []
    if run_data.get("vendor").get("genre", "") == "KeepApp":
        raw_data_url = run_data.get("rawDataURL")
        r = requests.get(raw_data_url)
        # string strart with `H4sIAAAAAAAA`
        run_points_data = decode_runmap_data(r.text)
    heart_rate = run_data["heartRate"].get("averageHeartRate", None)
    polyline_str = polyline.encode(run_points_data) if run_points_data else ""
    start_latlng = start_point(*run_points_data[0]) if run_points_data else None
    start_date = datetime.utcfromtimestamp(run_data["startTime"] / 1000)
    tz_name = run_data.get("timezone", "")
    start_date_local = adjust_time(start_date, tz_name)
    end = datetime.utcfromtimestamp(run_data["endTime"] / 1000)
    end_local = adjust_time(end, tz_name)
    # 5898009e387e28303988f3b7_9223370441312156007_rn middle
    keep_id = run_data["id"].split("_")[1]

    d = {
        "id": int(keep_id),
        "name": "run from keep",
        # future to support others workout now only for run 
        "type": "Run",
        "start_date": start_date,
        "end": end,
        "start_date_local": start_date_local,
        "end_local": end_local,
        "length": run_data["distance"],
        "average_heartrate": int(heart_rate) if heart_rate else None,
        "map": run_map(polyline_str),
        "start_latlng": start_latlng,
        "distance": run_data["distance"],
        "moving_time": run_data["duration"],
        "elapsed_time": run_data["duration"],
        "average_speed": run_data["distance"] / run_data["duration"],
    }
    return namedtuple("x", d.keys())(*d.values())


def get_all_keep_tracks(email, password):
    s = requests.Session()
    s, headers = login(s, email, password)
    runs = get_to_download_runs_ids(s, headers)
    tracks = []
    for run in runs:
        run_data = get_single_run_data(s, headers, run)
        print(f"parsing keep id {run}")
        track = parse_raw_data_to_nametuple(run_data)
        tracks.append(track)
    return tracks


def run_keep_sync(email, password):
    tracks =  get_all_keep_tracks(email, password)
    generator = Generator(SQL_FILE)
    # if you want to refresh data change False to True
    generator.sync_from_keep(tracks)

    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:

        f.write("const activities = ")
        json.dump(activities_list, f, indent=2)
        f.write(";\n")
        f.write("\n")
        f.write("export {activities};\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="keep login email")
    parser.add_argument("password", help="keep login password")
    options = parser.parse_args()
    run_keep_sync(options.email, options.password)
