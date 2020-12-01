import argparse
import json
import logging
import os.path
import time
from datetime import datetime
from xml.etree import ElementTree

import gpxpy.gpx
import httpx

from config import (
    BASE_URL,
    GPX_FOLDER,
    JSON_FILE,
    NIKE_CLIENT_ID,
    OUTPUT_DIR,
    SQL_FILE,
    TOKEN_REFRESH_URL,
)
from utils import make_activities_file

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nike_sync")


class Nike:
    def __init__(self, refresh_token):
        self.client = httpx.Client()

        response = self.client.post(
            TOKEN_REFRESH_URL,
            json={
                "refresh_token": refresh_token,
                "client_id": NIKE_CLIENT_ID,
                "grant_type": "refresh_token",
            },
            timeout=60,
        )
        response.raise_for_status()

        access_token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

    def get_activities_since_timestamp(self, timestamp):
        return self.request("activities/after_time", timestamp)

    def get_activities_since_id(self, activity_id):
        try:
            return self.request("activities/after_id", activity_id)
        except:
            print("retry")
            time.sleep(3)
            return self.request("activities/after_id", activity_id)

    def get_activity(self, activity_id):
        try:
            return self.request("activity", f"{activity_id}?metrics=ALL")
        except:
            print("retry")
            time.sleep(3)
            return self.request("activity", f"{activity_id}?metrics=ALL")

    def request(self, resource, selector):
        url = f"{BASE_URL}/{resource}/{selector}"
        logger.info(f"GET: {url}")
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()


def run(refresh_token):
    nike = Nike(refresh_token)
    last_id = get_last_id()

    logger.info(f"Running from ID {last_id}")

    while True:
        if last_id is not None:
            data = nike.get_activities_since_id(last_id)
        else:
            data = nike.get_activities_since_timestamp(0)

        last_id = data["paging"].get("after_id")
        activities = data["activities"]

        logger.info(f"Found {len(activities)} new activities")

        for activity in activities:
            full_activity = nike.get_activity(activity["id"])
            save_activity(full_activity)

        if last_id is None or not activities:
            logger.info(f"Found no new activities, finishing")
            return


def save_activity(activity):
    activity_id = activity["id"]
    activity_time = activity["end_epoch_ms"]
    print(activity_time)
    logger.info(f"Saving activity {activity_id}")
    path = os.path.join(OUTPUT_DIR, f"{activity_time}.json")
    try:
        with open(path, "w") as f:
            json.dump(sanitise_json(activity), f, indent=4)
    except Exception:
        os.unlink(path)
        raise


def get_last_id():
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
    except:
        return None


def sanitise_json(d):
    """
    Gatsby's JSON loading for GraphQL queries doesn't support "." characters in
    names, which Nike uses a lot for reverse-domain notation.

    We recursively transform all dict keys to use underscores instead.
    """

    def _transform_key(key):
        return key.replace(".", "_")

    if isinstance(d, dict):
        return {_transform_key(k): sanitise_json(v) for k, v in d.items()}

    if isinstance(d, (tuple, list)):
        return [sanitise_json(x) for x in d]

    return d


def get_to_generate_files():
    file_names = os.listdir(GPX_FOLDER)
    try:
        last_time = max(
            int(i.split(".")[0]) for i in file_names if not i.startswith(".")
        )
    except:
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
        title: the title of the GXP document
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
            raise Exception(f"\tThe latitude and longitude data is out of order")

        points_dict_list.append(
            {
                "latitude": lat["value"],
                "longitude": lon["value"],
                "start_time": lat["start_epoch_ms"],
                "time": datetime.utcfromtimestamp(lat["start_epoch_ms"] / 1000),
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
    ascent_index = None
    heart_rate_index = None
    if not activity.get("metrics"):
        print(f"The activity {activity['id']} doesn't contain metrics information")
        return
    for i, metric in enumerate(activity["metrics"]):
        if metric["type"] == "latitude":
            lat_index = i
        if metric["type"] == "longitude":
            lon_index = i
        if metric["type"] == "ascent":
            ascent_index = i
        if metric["type"] == "heart_rate":
            heart_rate_index = i

    if not any([lat_index, lon_index]):
        return None

    latitude_data = activity["metrics"][lat_index]["values"]
    longitude_data = activity["metrics"][lon_index]["values"]
    elevation_data = None
    heart_rate_data = None
    if ascent_index:
        elevation_data = activity["metrics"][ascent_index]["values"]
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


def make_new_gpxs(files):
    # TODO refactor maybe we do not need to upload
    if not files:
        print("no files")
        return
    if not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)
    gpx_files = []
    for file in files:
        with open(file, "r") as f:
            try:
                json_data = json.loads(f.read())
            except:
                return
        # ALL save name using utc if you want local please offset
        gpx_name = str(json_data["end_epoch_ms"])
        gpx_files.append(os.path.join(GPX_FOLDER, str(gpx_name) + ".gpx"))
        parsed_data = parse_activity_data(json_data)
        if parsed_data:
            save_gpx(parsed_data, gpx_name)
    return gpx_files


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    parser = argparse.ArgumentParser()
    parser.add_argument("refresh_token", help="API refresh access token for nike.com")
    options = parser.parse_args()
    run(options.refresh_token)

    time.sleep(2)
    files = get_to_generate_files()
    make_new_gpxs(files)
    # waiting for gpx
    time.sleep(2)
    make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE)
