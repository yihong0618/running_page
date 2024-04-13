import argparse
import base64
import json
import os
from sre_constants import SUCCESS
import time
import zlib
from collections import namedtuple
from datetime import datetime, timedelta

import eviltransform
import gpxpy
import polyline
import requests
from config import GPX_FOLDER, JSON_FILE, SQL_FILE, run_map, start_point
from Crypto.Cipher import AES
from generator import Generator
from utils import adjust_time
import xml.etree.ElementTree as ET
from config import OUTPUT_DIR
from stravalib.exc import ActivityUploadFailed, RateLimitTimeout
from utils import make_strava_client, upload_file_to_strava
from keep_sync import (
    TIMESTAMP_THRESHOLD_IN_DECISECOND,
    TRANS_GCJ02_TO_WGS84,
    login,
    decode_runmap_data,
    find_nearest_hr,
)

"""
Only provide the ability to sync data from keep's multiple sport types to strava's corresponding sport types to help those who use multiple devices like me, the web page presentation still uses Strava (or refer to nike_to_strava_sync.py to modify it to suit you).
My own best practices:
1. running/hiking/Cycling (Huawei/OPPO) -> Keep
2. Keep -> Strava (add this scripts to run_data_sync.yml)
3. Road Cycling(Garmin) -> Strava.
4. running_page(Strava)


    """
KEEP_DATA_TYPE_API = ["running", "hiking", "cycling"]
KEEP2STRAVA = {
    "outdoorWalking": "Walk",
    "outdoorRunning": "Run",
    "outdoorCycling": "Ride",
    "indoorRunning": "VirtualRun",
}

# need to test
LOGIN_API = "https://api.gotokeep.com/v1.1/users/login"
RUN_DATA_API = "https://api.gotokeep.com/pd/v3/stats/detail?dateUnit=all&type={data_type_api}&lastDate={last_date}"
RUN_LOG_API = "https://api.gotokeep.com/pd/v3/{data_type_api}log/{run_id}"


def get_to_download_runs_ids(session, headers, data_type_api):
    last_date = 0
    result = []

    while 1:
        r = session.get(
            RUN_DATA_API.format(data_type_api=data_type_api, last_date=last_date),
            headers=headers,
        )
        if r.ok:
            run_logs = r.json()["data"]["records"]

            for i in run_logs:
                logs = [j["stats"] for j in i["logs"]]
                result.extend(k["id"] for k in logs if not k["isDoubtful"])
            last_date = r.json()["data"]["lastTimestamp"]
            since_time = datetime.utcfromtimestamp(last_date / 1000)
            print(f"pares keep ids data since {since_time}")
            time.sleep(1)  # spider rule
            if not last_date:
                break
    return result


def get_single_run_data(session, headers, run_id, data_type_api):
    r = session.get(
        RUN_LOG_API.format(data_type_api=data_type_api, run_id=run_id), headers=headers
    )
    if r.ok:
        return r.json()


def download_keep_gpx(gpx_data, keep_id):
    try:
        print(f"downloading keep_id {str(keep_id)} gpx")
        file_path = os.path.join(GPX_FOLDER, str(keep_id) + ".gpx")
        with open(file_path, "w") as fb:
            fb.write(gpx_data)
        return file_path
    except:
        print(f"wrong id {keep_id}")
        pass


def parse_points_to_gpx(run_points_data, start_time, type):
    """
    Convert run points data to GPX format.

    Args:
        run_id (str): The ID of the run.
        run_points_data (list of dict): A list of run data points.
        start_time (int): The start time for adjusting timestamps. Note that the unit of the start_time is millsecond

    Returns:
        gpx_data (str): GPX data in string format.
    """
    points_dict_list = []
    # early timestamp fields in keep's data stands for delta time, but in newly data timestamp field stands for exactly time,
    # so it does'nt need to plus extra start_time
    if run_points_data[0]["timestamp"] > TIMESTAMP_THRESHOLD_IN_DECISECOND:
        start_time = 0

    for point in run_points_data:
        points_dict = {
            "latitude": point["latitude"],
            "longitude": point["longitude"],
            "time": datetime.utcfromtimestamp(
                (point["timestamp"] * 100 + start_time)
                / 1000  # note that the timestamp of a point is decisecond(分秒)
            ),
            "elevation": point.get("verticalAccuracy"),
            "hr": point.get("hr"),
        }
        points_dict_list.append(points_dict)
    gpx = gpxpy.gpx.GPX()
    gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = "gpx from keep"
    gpx_track.type = type
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    for p in points_dict_list:
        point = gpxpy.gpx.GPXTrackPoint(
            latitude=p["latitude"],
            longitude=p["longitude"],
            time=p["time"],
            elevation=p.get("elevation"),
        )
        if p.get("hr") is not None:
            gpx_extension_hr = ET.fromstring(
                f"""<gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
                    <gpxtpx:hr>{p["hr"]}</gpxtpx:hr>
                    </gpxtpx:TrackPointExtension>
                    """
            )
            point.extensions.append(gpx_extension_hr)
        gpx_segment.points.append(point)
    return gpx.to_xml()


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
                tracks.append(track)
            except Exception as e:
                print(f"Something wrong paring keep id {run}" + str(e))
    return tracks


def parse_raw_data_to_nametuple(run_data, old_gpx_ids, session, with_download_gpx=True):
    run_data = run_data["data"]
    run_points_data = []

    # 5898009e387e28303988f3b7_9223370441312156007_rn middle
    keep_id = run_data["id"].split("_")[1]

    start_time = run_data["startTime"]
    avg_heart_rate = None
    decoded_hr_data = []
    if run_data["heartRate"]:
        avg_heart_rate = run_data["heartRate"].get("averageHeartRate", None)
        heart_rate_data = run_data["heartRate"].get("heartRates", None)
        if heart_rate_data is not None:
            decoded_hr_data = decode_runmap_data(heart_rate_data)
        # fix #66
        if avg_heart_rate and avg_heart_rate < 0:
            avg_heart_rate = None

    file_path = None
    if run_data["geoPoints"]:
        run_points_data = decode_runmap_data(run_data["geoPoints"], True)
        run_points_data_gpx = run_points_data
        if TRANS_GCJ02_TO_WGS84:
            run_points_data = [
                list(eviltransform.gcj2wgs(p["latitude"], p["longitude"]))
                for p in run_points_data
            ]
            for i, p in enumerate(run_points_data_gpx):
                p["latitude"] = run_points_data[i][0]
                p["longitude"] = run_points_data[i][1]

        for p in run_points_data_gpx:
            p_hr = find_nearest_hr(decoded_hr_data, int(p["timestamp"]), start_time)
            if p_hr:
                p["hr"] = p_hr
        if with_download_gpx:
            if str(keep_id) not in old_gpx_ids and run_data["dataType"].startswith(
                "outdoor"
            ):
                gpx_data = parse_points_to_gpx(
                    run_points_data_gpx, start_time, KEEP2STRAVA[run_data["dataType"]]
                )
                file_path = download_keep_gpx(gpx_data, str(keep_id))
    else:
        print(f"ID {keep_id} no gps data")
    polyline_str = polyline.encode(run_points_data) if run_points_data else ""
    start_latlng = start_point(*run_points_data[0]) if run_points_data else None
    start_date = datetime.utcfromtimestamp(start_time / 1000)
    tz_name = run_data.get("timezone", "")
    start_date_local = adjust_time(start_date, tz_name)
    end = datetime.utcfromtimestamp(run_data["endTime"] / 1000)
    end_local = adjust_time(end, tz_name)
    if not run_data["duration"]:
        print(f"ID {keep_id} has no total time just ignore please check")
        return
    d = {
        "id": int(keep_id),
        "name": f"{KEEP2STRAVA[run_data['dataType']]} from keep",
        # future to support others workout now only for run
        "type": f"{KEEP2STRAVA[(run_data['dataType'])]}",
        "start_date": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
        "end": datetime.strftime(end, "%Y-%m-%d %H:%M:%S"),
        "start_date_local": datetime.strftime(start_date_local, "%Y-%m-%d %H:%M:%S"),
        "end_local": datetime.strftime(end_local, "%Y-%m-%d %H:%M:%S"),
        "length": run_data["distance"],
        "average_heartrate": int(avg_heart_rate) if avg_heart_rate else None,
        "map": run_map(polyline_str),
        "start_latlng": start_latlng,
        "distance": run_data["distance"],
        "moving_time": timedelta(seconds=run_data["duration"]),
        "elapsed_time": timedelta(
            seconds=int((run_data["endTime"] - run_data["startTime"]) / 1000)
        ),
        "average_speed": run_data["distance"] / run_data["duration"],
        "location_country": str(run_data.get("region", "")),
        "source": "Keep",
        "gpx_file_path": file_path,
    }
    return namedtuple("x", d.keys())(*d.values())


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
    new_tracks = run_keep_sync(options.phone_number, options.password)

    # to strava.
    print("Need to load all gpx files maybe take some time")
    last_time = 0
    client = make_strava_client(
        options.client_id, options.client_secret, options.strava_refresh_token
    )

    index = 1
    print(f"{len(new_tracks)} gpx files is going to upload")
    uploaded_file_paths = []
    for track in new_tracks:
        if track.gpx_file_path is not None:
            print(track.gpx_file_path)
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
