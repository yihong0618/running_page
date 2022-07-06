import argparse
import asyncio
from datetime import datetime, timedelta
from io import BytesIO
from xml.etree import ElementTree

import gpxpy
import gpxpy.gpx
from config import STRAVA_GARMIN_TYPE_DICT
from garmin_sync import Garmin
from rich import print
from strava_sync import run_strava_sync

from utils import make_strava_client

""""
TODO..................not finish yet

"""


def generate_strava_run_points(start_time, strava_streams):
    """
    strava return same len data list
    """
    if not (strava_streams.get("time") and strava_streams.get("latlng")):
        return None
    points_dict_list = []
    time_list = strava_streams["time"].data
    time_list = [start_time + timedelta(seconds=int(i)) for i in time_list]
    latlng_list = strava_streams["latlng"].data

    for i, j in zip(time_list, latlng_list):
        points_dict_list.append(
            {
                "latitude": j[0],
                "longitude": j[1],
                "time": i,
            }
        )
    # add heart rate
    if strava_streams.get("heartrate"):
        heartrate_list = strava_streams.get("heartrate").data
        for index, h in enumerate(heartrate_list):
            points_dict_list[index]["heart_rate"] = h
    # add altitude
    if strava_streams.get("altitude"):
        heartrate_list = strava_streams.get("altitude").data
        for index, h in enumerate(heartrate_list):
            points_dict_list[index]["elevation"] = h
    return points_dict_list


def make_gpx_from_points(title, points_dict_list):
    gpx = gpxpy.gpx.GPX()
    gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = title
    gpx_track.type = "Run"
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    for p in points_dict_list:
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


async def upload_to_activities(garmin_client):
    last_activity = await garmin_client.get_activities(0, 1)
    print(last_activity)
    files_list = []
    await garmin_client.upload_activities(files_list)
    return files_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("garmin_email", nargs="?", help="email of garmin")
    parser.add_argument("garmin_password", nargs="?", help="password of garmin")
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin accout is cn",
    )
    options = parser.parse_args()
    garmin_auth_domain = "CN" if options.is_cn else ""

    garmin_client = Garmin(
        options.garmin_email, options.garmin_password, garmin_auth_domain
    )
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(upload_to_activities(garmin_client))
    loop.run_until_complete(future)
