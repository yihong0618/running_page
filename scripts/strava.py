from datetime import datetime, timedelta
import time
import logging
import json
from json.decoder import JSONDecodeError
import os
import os.path
from xml.etree import ElementTree
import argparse
import gpxpy.gpx

from stravalib.client import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("strava")

GET_DIR = "activities"
GPX_FOLDER = os.path.join(os.getcwd(), "GPX_OUT")


def make_client(client_id, client_secret, refresh_token):
    client = Client()

    refresh_response = client.refresh_access_token(
        client_id=client_id, client_secret=client_secret, refresh_token=refresh_token
    )
    client.access_token = refresh_response["access_token"]
    return client


def get_last_time(client):
    """
    if there is no activities cause exception return 0
    """
    try:
        activate = next(client.get_activities(limit=3))
        # add 30 minutes to make sure after the end of this activate
        end_date = activate.start_date + activate.elapsed_time + timedelta(minutes=30)
        return int(datetime.timestamp(end_date) * 1000)
    except:
        return 0


def get_to_generate_files(last_time):
    file_names = os.listdir(GET_DIR)
    return [GET_DIR + "/" + i for i in file_names if int(i.split(".")[0]) > last_time]


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
    """
    Saves the GPX data to a file on disk
    Args:
        gpx_data: the GPX XML doc
        activity_id: the name of the file
    """

    file_path = os.path.join(GPX_FOLDER, activity_id + ".gpx")
    with open(file_path, "w") as f:
        f.write(gpx_data)


def upload_gpx(file_name):
    with open(file_name, "rb") as f:
        r = client.upload_activity(activity_file=f, data_type="gpx")
        print(r)


def make_new_gpxs(files):
    # TODO refactor maybe we do not need to upload
    if not files:
        return
    if not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)
    for file in files:
        with open(file, "r") as f:
            try:
                json_data = json.loads(f.read())
            except JSONDecodeError:
                pass
        # ALL save name using utc if you want local please offset
        gpx_name = str(datetime.utcfromtimestamp(int(json_data["start_epoch_ms"]) / 1000).strftime('%Y-%m-%d %H-%M-%S'))
        parsed_data = parse_activity_data(json_data)
        if parsed_data:
            save_gpx(parsed_data, gpx_name)
    gpx_files = sorted(os.listdir(GPX_FOLDER))
    # get new, TODO: not mind the delete stai
    gpx_files = gpx_files[-len(files):]
    for f in gpx_files:
        upload_gpx(GPX_FOLDER + "/" + f)
        upload_gpx(os.path.join(GPX_FOLDER, f))
        logger.info(f +" uploaded")


if __name__ == "__main__":
    # TODO try to support delete
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", help="strava client id")
    parser.add_argument("client_secret", help="strava client secret")
    parser.add_argument("refresh_token", help="strava refresh token")
    options = parser.parse_args()
    try:
        client = make_client(
            options.client_id, options.client_secret, options.refresh_token
        )
    except:
        print("try again login strava")
        time.sleep(10)
        client = make_client(
            options.client_id, options.client_secret, options.refresh_token
        )
    last_time = get_last_time(client)
    # change here to manual
    files = get_to_generate_files(last_time)
    make_new_gpxs(files)
