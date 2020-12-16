import argparse
import asyncio
import base64
import datetime
import json
import os
import struct
import time
from hashlib import sha1
from xml.etree import ElementTree

import gpxpy.gpx
import httpx

from config import GPX_FOLDER, JSON_FILE, SQL_FILE
from utils import make_activities_file

GPX_FILE_DIR = "GPX_OUT"

# (timestamp: int64, longitude: float32, latitude: float32, Elevation: float32,
# unknown: int16, SpeedKPH: float32, elapsed: int32, Distance: int32,
# ElevationGain": int16, ElevationLoss: int16)
UNPACK_GPS_CODE = ">q3fhfi4h"
# (timestamp: int64, heart_rate: uint8, unknown: uint8, elapsed: int32, Distance: int32)
UNPACK_HEARTRATE_CODE = ">q2B2i"

SECRET_DICT = {
    "APP_SECRET": "T68bA6dHk2ayW1Y39BQdEnUmGqM8Zq1SFZ3kNas3KYDjp471dJNXLcoYWsDBd1mH",
    "APP_KEY": "com.runtastic.android",
    "sessionCookie": "_runtastic_appws_session",
}

HEADERS = {
    "X-App-Version": "6.9.2",
    "X-App-Key": "com.runtastic.android",
    "X-Auth-Token": "",
    "Content-Type": "application/json",
    "X-Date": "",
}


BASE_URL = "https://appws.runtastic.com"
SYNC_URL = "/webapps/services/runsessions/v3/sync"

# For timeout Exception change here
TIME_OUT = httpx.Timeout(240.0, connect=360.0)

rids = []

# utils
def try_to_parse_time(from_time):
    # if not a format timestamp return 0
    if from_time.isdigit():
        if len(from_time) == 10:
            return str(int(from_time) * 1000)
        elif len(from_time) == 13:
            return from_time
        else:
            return "0"
    try:
        from_time = time.mktime(
            datetime.datetime.strptime(from_time, "%Y-%m-%d").timetuple()
        )
        return str(int(from_time) * 1000)
    except:
        return "0"


def make_auth_token(appKey, appSecret, str_now):
    s = f"--{appKey}--{appSecret}--{str_now}--"
    auth_token = sha1(s.encode("utf-8")).hexdigest()
    return auth_token


def make_request_header(header):
    str_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    auth_token = make_auth_token(
        SECRET_DICT["APP_KEY"], SECRET_DICT["APP_SECRET"], str_now
    )
    header["X-Date"] = str_now
    header["X-Auth-Token"] = auth_token
    return header


async def _login(email, password):
    headers = make_request_header(HEADERS)
    async with httpx.AsyncClient(timeout=TIME_OUT) as client:
        r = await client.post(
            BASE_URL + "/webapps/services/auth/login",
            headers=headers,
            data=json.dumps(
                {
                    "email": email,
                    "additionalAttributes": ["accessToken"],
                    "password": password,
                }
            ),
        )
    if r.status_code != 200:
        raise Exception("Please make sure your email or password are correct")
    HEADERS["Authorization"] = "Bearer " + r.json()["accessToken"]


def get_buf(trace):
    trace_list = trace.split("\\n")
    buf = base64.b64decode(trace_list[0])
    # first four bytes is length points
    point_length = int(struct.unpack(">i", buf[:4])[0])
    window_length = int((len(buf) - 4) / point_length)
    buf = buf[4:]
    return point_length, window_length, buf


def decode_gps_trace(trace):
    point_length, window_length, buf = get_buf(trace)
    points = []
    for i in range(point_length):
        points.append(
            struct.unpack(
                UNPACK_GPS_CODE, buf[i * window_length : (i + 1) * window_length]
            )
        )
    # to gpx format
    points_dict_list = [
        {
            "latitude": p[2],
            "longitude": p[1],
            "start_time": p[0],
            "elevation": p[3],
            "time": datetime.datetime.utcfromtimestamp(p[0] / 1000),
        }
        for p in points
    ]
    return points_dict_list


def decode_heart_rate_trace(trace):
    point_length, window_length, buf = get_buf(trace)
    points = []
    for i in range(point_length):
        points.append(
            struct.unpack(
                UNPACK_HEARTRATE_CODE, buf[i * window_length : (i + 1) * window_length]
            )
        )
    # to heart rate format
    points_dict_list = [
        {
            "start_time": p[0],
            "heart_rate": p[1],
        }
        for p in points
        if int(p[1]) != 0
    ]
    return points_dict_list


def update_gpx_points(gpx_points, heart_rate_points):
    counter = 0
    # make heart rate data in gpx
    for p in gpx_points:
        while p["start_time"] >= heart_rate_points[counter]["start_time"]:
            if counter == len(heart_rate_points) - 1:
                break
            p["heart_rate"] = heart_rate_points[counter]["heart_rate"]
            counter += 1


def gen_gpx(gpx_points):
    gpx = gpxpy.gpx.GPX()
    gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    file_name = gpx_points[0].get("start_time")

    for p in gpx_points:
        # delete useless attr
        del p["start_time"]
        if p.get("heart_rate") is None:
            point = gpxpy.gpx.GPXTrackPoint(**p)
        else:
            heart_rate_num = p.pop("heart_rate")
            point = gpxpy.gpx.GPXTrackPoint(**p)
            gpx_extension_hr = ElementTree.fromstring(
                f"""<gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
                <gpxtpx:hr>{heart_rate_num}</gpxtpx:hr>
                </gpxtpx:TrackPointExtension>
            """
            )
            point.extensions.append(gpx_extension_hr)
        gpx_segment.points.append(point)
    return gpx.to_xml(), file_name


async def get_and_save_one_activate(rid, asyncio_semaphore, output=GPX_FILE_DIR):
    async with asyncio_semaphore:
        data = json.dumps(
            {
                "includeGpsTrace": {"include": True, "version": "1"},
                "includeHeartRateTrace": {"include": True, "version": "1"},
                "includeHeartRateZones": True,
            }
        )
        try:
            async with httpx.AsyncClient(timeout=TIME_OUT) as client:
                r = await client.post(
                    BASE_URL
                    + "/webapps/services/runsessions/v2/{}/details".format(rid),
                    headers=HEADERS,
                    data=data,
                )
        except:
            await asyncio.sleep(2)
            print("retry")
            try:
                async with httpx.AsyncClient(timeout=TIME_OUT) as client:
                    r = await client.post(
                        BASE_URL
                        + "/webapps/services/runsessions/v2/{}/details".format(rid),
                        headers=HEADERS,
                        data=data,
                    )
            except:
                print(f"fail parse {rid} gpx please try again")
                return

        run_session = r.json()["runSessions"]
        gps_trace = run_session.get("gpsData", {}).get("trace", "")
        # remove session that add manually
        if not gps_trace:
            return
        heart_rate_trace = run_session.get("heartRateData", {}).get("trace", "")
        gpx_points = decode_gps_trace(gps_trace)
        if heart_rate_trace:
            heart_rate_points = decode_heart_rate_trace(heart_rate_trace)
            # just update
            if heart_rate_points:
                update_gpx_points(gpx_points, heart_rate_points)

        gpx_data, file_name = gen_gpx(gpx_points)
        # use start time as gpx name
        file_name = str(file_name) + ".gpx"
        file_path = os.path.join(output, file_name)
        with open(file_path, "w") as f:
            print(f"Saving gpx file name {file_name}")
            f.write(gpx_data)


async def get_to_sync_sessions(from_time):
    start = try_to_parse_time(from_time)
    sync_data = {
        "syncedUntil": start,
        "perPage": "100",
    }
    async with httpx.AsyncClient(timeout=TIME_OUT) as client:
        r = await client.post(
            BASE_URL + SYNC_URL, data=json.dumps(sync_data), headers=HEADERS
        )
    sessions_data = r.json()

    for session in sessions_data.get("sessions", []):
        # comment by yihong0618 this is for only run type sportTypeId in [1, 14] are running for now
        # sportTypeId in [3, 4, 15, 22] are Biking
        # sportTypeId in [18] are Swimming
        # sportTypeId in [2, 7, 19] are Walking
        # this may be refine when issue #54 resolved
        # if you want to diy please change here
        if session.get("deletedAt") or session.get("sportTypeId") not in ["1", "14"]:
            continue
        rids.append(session.get("id"))
    date = datetime.datetime.utcfromtimestamp(int(sessions_data["syncedUntil"]) / 1000)
    print(f"Parse sessions rids since {str(date)[:10]} data")
    if sessions_data["moreItemsAvailable"] == "true":
        return await get_to_sync_sessions(sessions_data["syncedUntil"])
    return rids


async def run(email, password, from_time, output=GPX_FILE_DIR):
    # chunk async tasks for every 50
    asyncio_semaphore = asyncio.BoundedSemaphore(50)
    await _login(email, password)
    rids = await get_to_sync_sessions(from_time)
    tasks = [
        asyncio.ensure_future(get_and_save_one_activate(rid, asyncio_semaphore, output))
        for rid in rids
    ]
    return await asyncio.gather(*tasks)


def main():

    # cli args
    ap = argparse.ArgumentParser(description="Get your runtastic GPX data")
    ap.add_argument("-e", "--email", help="Your runtastic email or user name")
    ap.add_argument("-p", "--password", help="Your runtastic password")
    ap.add_argument(
        "-t", "--from-time", help="from time", default="0", dest="from_time"
    )
    ap.add_argument(
        "-o", "--out-dir", help="output dir", default=GPX_FILE_DIR, dest="out_dir"
    )
    args = ap.parse_args()
    email = args.email
    password = args.password
    from_time = args.from_time
    output = args.out_dir
    # make output dir
    if not os.path.exists(output):
        os.mkdir(output)
    if not email:
        raise Exception("you must enter your email")
    if not password:
        raise Exception("you must enter your password")

    start = time.time()
    print("Start to save gpx in GPX_OUT please wait")
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(email, password, from_time, output))
    loop.run_until_complete(future)
    print(f"save to gpx cost {time.time() - start} seconds")


def get_last_time():
    try:
        file_names = os.listdir(GPX_FOLDER)
        last_time = max(
            int(i.split(".")[0]) for i in file_names if not i.startswith(".")
        )
    except:
        last_time = 0
    return last_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="email of runstastic")
    parser.add_argument("password", help="password of runstastic")
    options = parser.parse_args()
    last_time = get_last_time()

    # make output dir
    if not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)
    if not options.email:
        raise Exception("you must enter your email")
    if not options.password:
        raise Exception("you must enter your password")

    start = time.time()
    print("Start to save gpx in GPX_OUT please wait")
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        run(options.email, options.password, str(last_time), GPX_FOLDER)
    )
    loop.run_until_complete(future)
    print(f"save to gpx cost {time.time() - start} seconds")

    # for gpx generation change sleep time here
    time.sleep(2)
    make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE)
