import argparse
import json
import logging
import os.path
import time
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

import gpxpy.gpx
import httpx
from config import (
    BASE_TIMEZONE,
    GPX_FOLDER,
    JSON_FILE,
    OUTPUT_DIR,
    SQL_FILE,
    run_map,
)
from generator import Generator
from utils import adjust_time, make_activities_file

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nike_sync")

BASE_URL = "https://api.nike.com/plus/v3"
TOKEN_REFRESH_URL = "https://api.nike.com/idn/shim/oauth/2.0/token"


class Nike:
    def __init__(self, access_token):
        self.client = httpx.Client()

        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

    def get_activities_before_id(self, activity_id):
        if not activity_id:
            activity_id = "*"
        try:
            return self.request(
                f"activities/before_id/v3/{activity_id}?limit=30&types=run%2Cjogging&include_deleted=false"
            )
        except Exception as e:
            print(f"Error getting activities before id {activity_id}: {e}")
            time.sleep(3)
            return self.request(
                f"activities/before_id/v3/{activity_id}?limit=30&types=run%2Cjogging&include_deleted=false"
            )

    def get_activity(self, activity_id):
        try:
            return self.request(f"activity/{activity_id}?metrics=ALL")
        except Exception as e:
            logger.warning(f"Error getting activity {activity_id}: {e}, retrying...")
            time.sleep(3)
            return self.request(f"activity/{activity_id}?metrics=ALL")

    def request(self, resource):
        url = f"{BASE_URL}/{resource}"
        logger.info(f"GET: {url}")
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()


def run(refresh_token, is_continue_sync=False):
    nike = Nike(refresh_token)
    if is_continue_sync:
        last_id_local = get_last_before_id()
        print(f"Will continue sync before Running from ID {last_id_local}")
    else:
        last_id_local = None
    before_id = None
    while True:
        data = nike.get_activities_before_id(before_id)
        activities = data["activities"]
        activities_ids = [i["id"] for i in activities]
        is_sync_done = False
        if last_id_local in activities_ids:
            index = activities_ids.index(last_id_local)
            activities = activities[:index]
            is_sync_done = True

        before_id = data["paging"].get("before_id")

        logger.info(f"Found {len(activities)} new activities")

        for activity in activities:
            # ignore NTC record
            app_id = activity["app_id"]
            activity_id = activity["id"]
            if (
                app_id == "com.nike.ntc.brand.ios"
                or app_id == "com.nike.ntc.brand.droid"
            ):
                logger.info(f"Ignore NTC record {activity_id}")
                continue

            full_activity = nike.get_activity(activity_id)
            save_activity(full_activity)

        if is_sync_done or before_id is None or not activities:
            logger.info("Found no new activities, finishing")
            return


def save_activity(activity):
    activity_id = activity["id"]
    activity_time = activity["end_epoch_ms"]
    print(activity_time)
    logger.info(f"Saving activity {activity_id}")
    path = os.path.join(OUTPUT_DIR, f"{activity_time}.json")
    try:
        with open(path, "w") as f:
            json.dump(activity, f, indent=4)
    except Exception:
        os.unlink(path)
        raise


def get_last_before_id():
    try:
        file_names = os.listdir(OUTPUT_DIR)
        file_names = [i for i in file_names if not i.startswith(".")]
        file_names.sort()
        file_name = file_names[-1]
        with open(os.path.join(OUTPUT_DIR, file_name)) as f:
            data = json.load(f)
        logger.info(f"Last update from {data['id']}")
        return data["id"]
    # easy solution when error happens no last id
    except Exception as e:
        print(f"Error getting last before id: {e}")
        return None


def get_to_generate_files():
    file_names = os.listdir(GPX_FOLDER)
    try:
        # error when mixed keep & nike gpx files
        # since keep has gpx files like 9223370434827882207.gpx
        # so we need to check gpx file name ensure it is a valid timestamp
        timestamps = []
        for i in file_names:
            if i.startswith("."):
                continue
            t = int(i.split(".")[0])
            # the follow 7226553600000 representing the timestamp(with millisecond)
            # for "Tue Jan 01 2199 00:00:00 GMT+0800 (CST)"
            if t > 0 and t < 7226553600000:
                timestamps.append(t)
            else:
                logger.info(f"Invalid timestamp: {t}")

        if len(timestamps) > 0:
            last_time = max(timestamps)
        else:
            last_time = 0
    except Exception as e:
        print(f"Error getting last time: {e}")
        last_time = 0
    return [
        OUTPUT_DIR + "/" + i
        for i in os.listdir(OUTPUT_DIR)
        if not i.startswith(".") and int(i.split(".")[0]) > last_time
    ]


def generate_gpx(title, latitude_data, longitude_data, elevation_data, heart_rate_data):
    """
    Parses the latitude, longitude and elevation data to generate a GPX document
    Args:
        title: the title of the GPX document
        latitude_data: A list of dictionaries containing latitude data
        longitude_data: A list of dictionaries containing longitude data
        elevation_data: A list of dictionaries containing elevation data
    Returns:
        gpx: The GPX XML document
    """

    gpx = gpxpy.gpx.GPX()
    gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = title
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    points_dict_list = []

    def update_points(points, update_data, update_name):
        """
        Update the points dict list so that can easy create GPXTrackPoint
        Args:
            points: basic points list
            update_data: attr to update points which is a list
            update_name: attr name
        Returns:
            None (just update the points list)
        """
        counter = 0
        for p in points:
            while p["start_time"] >= update_data[counter]["end_epoch_ms"]:
                if counter == len(update_data) - 1:
                    break
                p[update_name] = update_data[counter]["value"]
                counter += 1

    for lat, lon in zip(latitude_data, longitude_data):
        if lat["start_epoch_ms"] != lon["start_epoch_ms"]:
            raise Exception("\tThe latitude and longitude data is out of order")

        points_dict_list.append(
            {
                "latitude": lat["value"],
                "longitude": lon["value"],
                "start_time": lat["start_epoch_ms"],
                "time": datetime.fromtimestamp(
                    lat["start_epoch_ms"] / 1000, tz=timezone.utc
                ),
            }
        )

    if elevation_data:
        update_points(points_dict_list, elevation_data, "elevation")
    if heart_rate_data:
        update_points(points_dict_list, heart_rate_data, "heart_rate")

    for p in points_dict_list:
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

    return gpx.to_xml()


def parse_activity_data(activity):
    """
    Parses a NRC activity and returns GPX XML
    Args:
        activity: a json document for a NRC activity
    Returns:
        gpx: the GPX XML doc for the input activity
    """

    lat_index = None
    lon_index = None
    elevation_index = None
    heart_rate_index = None
    if not activity.get("metrics"):
        print(f"The activity {activity['id']} doesn't contain metrics information")
        return
    for i, metric in enumerate(activity["metrics"]):
        if metric["type"] == "latitude":
            lat_index = i
        if metric["type"] == "longitude":
            lon_index = i
        if metric["type"] == "elevation":
            elevation_index = i
        if metric["type"] == "heart_rate":
            heart_rate_index = i

    if not any([lat_index, lon_index]):
        return None

    latitude_data = activity["metrics"][lat_index]["values"]
    longitude_data = activity["metrics"][lon_index]["values"]
    elevation_data = None
    heart_rate_data = None
    if elevation_index:
        elevation_data = activity["metrics"][elevation_index]["values"]
    if heart_rate_index:
        heart_rate_data = activity["metrics"][heart_rate_index]["values"]

    title = activity["tags"].get("com.nike.name")

    gpx_doc = generate_gpx(
        title, latitude_data, longitude_data, elevation_data, heart_rate_data
    )
    return gpx_doc


def save_gpx(gpx_data, activity_id):
    file_path = os.path.join(GPX_FOLDER, activity_id + ".gpx")
    with open(file_path, "w") as f:
        f.write(gpx_data)


def parse_no_gpx_data(activity):
    if not activity.get("metrics"):
        print(f"The activity {activity['id']} doesn't contain metrics information")
        return
    average_heartrate = None
    summary_info = activity.get("summaries")
    distance = 0

    for s in summary_info:
        if s.get("metric") == "distance":
            distance = s.get("value", 0) * 1000
        if s.get("metric") == "heart_rate":
            average_heartrate = s.get("value", None)
    # maybe training that no distance
    if not distance:
        return
    start_stamp = activity["start_epoch_ms"] / 1000
    end_stamp = activity["end_epoch_ms"] / 1000
    moving_time = timedelta(seconds=int(end_stamp - start_stamp))
    elapsed_time = timedelta(seconds=int(activity["active_duration_ms"] / 1000))

    nike_id = activity["end_epoch_ms"]
    start_date = datetime.fromtimestamp(
        activity["start_epoch_ms"] / 1000, tz=timezone.utc
    )
    start_date_local = adjust_time(start_date, BASE_TIMEZONE)
    end_date = datetime.fromtimestamp(activity["end_epoch_ms"] / 1000, tz=timezone.utc)
    end_date_local = adjust_time(end_date, BASE_TIMEZONE)
    d = {
        "id": int(nike_id),
        "name": "run from nike",
        "type": "Run",
        "subtype": "Run",
        "start_date": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
        "end": datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S"),
        "start_date_local": datetime.strftime(start_date_local, "%Y-%m-%d %H:%M:%S"),
        "end_local": datetime.strftime(end_date_local, "%Y-%m-%d %H:%M:%S"),
        "length": distance,
        "average_heartrate": average_heartrate,
        "map": run_map(""),
        "start_latlng": None,
        "distance": distance,
        "moving_time": moving_time,
        "elapsed_time": elapsed_time,
        "average_speed": distance / int(activity["active_duration_ms"] / 1000),
        "elevation_gain": 0,
        "location_country": "",
    }
    return namedtuple("x", d.keys())(*d.values())


def make_new_gpxs(files):
    # TODO refactor maybe we do not need to upload
    if not files:
        print("no files")
        return
    if not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)
    gpx_files = []
    tracks_list = []
    for file in files:
        with open(file, "r") as f:
            try:
                json_data = json.loads(f.read())
            except Exception as e:
                print(f"Error reading JSON file {file}: {e}")
                continue
        # ALL save name using utc if you want local please offset
        activity_name = str(json_data["end_epoch_ms"])
        parsed_data = parse_activity_data(json_data)
        if parsed_data:
            gpx_files.append(os.path.join(GPX_FOLDER, str(activity_name) + ".gpx"))
            save_gpx(parsed_data, activity_name)
        else:
            try:
                track = parse_no_gpx_data(json_data)
                if track:
                    tracks_list.append(track)
            # just ignore some unexpected run
            except Exception as e:
                print(str(e))
                continue
    if tracks_list:
        generator = Generator(SQL_FILE)
        generator.sync_from_app(tracks_list)
    return gpx_files


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    parser = argparse.ArgumentParser()
    parser.add_argument("refresh_token", help="API refresh access token for nike.com")
    parser.add_argument(
        "--continue-sync",
        dest="continue_sync",
        action="store_true",
        help="Continue syncing from the last activity",
    )
    options = parser.parse_args()
    run(options.refresh_token, options.continue_sync)

    time.sleep(2)
    files = get_to_generate_files()
    make_new_gpxs(files)
    # waiting for gpx
    time.sleep(2)
    make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE)
