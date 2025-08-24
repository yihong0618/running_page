import argparse
import json
import os
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import gpxpy
import polyline
import requests
from config import GPX_FOLDER, JSON_FILE, SQL_FILE, run_map, start_point
from generator import Generator
from xml.etree import ElementTree
from utils import adjust_time_to_utc

# need to test
ACTIVITY_LIST_API = "https://open.tulipsport.com/api/v1/feeds4likes?start_time={start_time}&end_time={end_time}"
ACTIVITY_DETAIL_API = (
    "https://open.tulipsport.com/api/v1/feeddetail?activity_id={activity_id}"
)
TULIPSPORT_FAKE_ID_PREFIX = "666"

TIMEZONE_OFFSET = "+08:00"
TIMEZONE_NAME = "Asia/Shanghai"
DEFAULT_TIMEZONE = timezone(timedelta(hours=8), TIMEZONE_NAME)


def get_all_activity_summaries(session, headers, start_time=None):
    if start_time is None:
        start_time = datetime.fromisoformat("2015-01-01T00:00:00+08:00")
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = datetime.now(tz=DEFAULT_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    result = []
    r = session.get(
        ACTIVITY_LIST_API.format(
            start_time=quote(start_time_str), end_time=quote(end_time_str)
        ),
        headers=headers,
    )
    if r.ok:
        data = r.json()
        if data["code"] == 0:
            summary_list = data["msg"]
            for summary in summary_list:
                if summary["activity_type"] != "run":
                    continue
                start_date_local = datetime.fromisoformat(
                    summary["start_date_local"] + TIMEZONE_OFFSET
                )
                start_date = adjust_time_to_utc(start_date_local, TIMEZONE_NAME)
                moving_time = timedelta(seconds=int(summary["moving_time"]))
                distance = float(summary["activity_distance"]) * 1000
                result.append(
                    {
                        "id": build_tulipsport_int_activity_id(summary),
                        "aid": summary["activity_id"],
                        "name": "run from tulipsport by " + summary["device"],
                        "distance": distance,
                        "moving_time": moving_time,
                        "elapsed_time": moving_time,
                        "type": "Run",
                        "subtype": "Run",
                        "start_date": start_date,
                        "start_date_local": start_date_local,
                        "end_date": start_date + moving_time,
                        "end_date_local": start_date_local + moving_time,
                        "average_heartrate": None,
                        "average_speed": distance / int(summary["moving_time"]),
                        "summary_polyline": "",
                        "outdoor": summary["location"] != ",,",
                    }
                )
    return result


def get_activity_detail(session, headers, activity_id):
    r = session.get(
        ACTIVITY_DETAIL_API.format(activity_id=activity_id), headers=headers
    )
    if r.ok:
        return r.json()


def merge_summary_and_detail_to_nametuple(summary, detail):
    id = int(summary["id"])
    name = summary["name"]
    type = summary["type"]
    start_date = datetime.strftime(summary["start_date"], "%Y-%m-%d %H:%M:%S")
    start_date_local = datetime.strftime(
        summary["start_date_local"], "%Y-%m-%d %H:%M:%S"
    )
    # end_date = datetime.strftime(summary["end_date"], "%Y-%m-%d %H:%M:%S")
    # end_date_local = datetime.strftime(summary["end_date_local"], "%Y-%m-%d %H:%M:%S")
    average_heartrate = int(detail["avg_hr"])
    elevation_gain = None
    map = run_map("")
    start_latlng = None
    distance = summary["distance"]
    moving_time = summary["moving_time"]
    elapsed_time = summary["elapsed_time"]
    average_speed = summary["average_speed"]
    location_country = ""

    # 详情接口具体的内容参考文档链接：https://open.tulipsport.com/document
    # map_data_list 的结构为 [ [latitude, longitude, elevation, section, distance, hr, time, cadence], ... ]
    point_list = detail["map_data_list"]
    point_list_length = len(point_list)
    if point_list_length and summary["outdoor"]:
        first_point = point_list[0]
        start_latlng = start_point(float(first_point[0]), float(first_point[1]))
        if point_list_length > 1:
            last_point = point_list[-1]
            elapsed_time = datetime.fromisoformat(
                last_point[6]
            ) - datetime.fromisoformat(first_point[6])
            latlng_list = [[float(point[0]), float(point[1])] for point in point_list]
            map = run_map(polyline.encode(latlng_list))

            altitude_list = [point[2] for point in detail["map_data_list"]]
            elevation_gain = compute_elevation_gain(altitude_list)

    activity_db_instance = {
        "id": id,
        "name": name,
        "type": type,
        "start_date": start_date,
        "start_date_local": start_date_local,
        "average_heartrate": average_heartrate,
        "map": map,
        "start_latlng": start_latlng,
        "distance": distance,
        "moving_time": moving_time,
        "elapsed_time": elapsed_time,
        "average_speed": average_speed,
        "elevation_gain": elevation_gain,
        "location_country": location_country,
    }
    return namedtuple("activity_db_instance", activity_db_instance.keys())(
        *activity_db_instance.values()
    )


def compute_elevation_gain(altitudes):
    total_gain = 0
    for i in range(1, len(altitudes)):
        if altitudes[i] > altitudes[i - 1]:
            total_gain += altitudes[i] - altitudes[i - 1]
    return total_gain


def find_last_tulipsport_start_time(track_ids):
    start_time = None
    tulipsport_ids = [
        id for id in track_ids if str(id).startswith(TULIPSPORT_FAKE_ID_PREFIX)
    ]
    if tulipsport_ids:
        tulipsport_ids.sort()
        # 从模拟的构造 ID（特殊前缀 (666) + 活动开始时间的 timestamp + 活动距离 (单位：米，支持单次活动最大距离为 999,999 米)）中读取时间信息
        start_time = datetime.fromtimestamp(
            int(str(tulipsport_ids[-1])[3:-6]), DEFAULT_TIMEZONE
        )
    return start_time


def get_new_activities(token, old_tracks_ids, with_gpx=False):
    s = requests.Session()
    headers = {"Authorization": token}
    activity_summary_list = get_all_activity_summaries(
        s, headers, find_last_tulipsport_start_time(old_tracks_ids)
    )
    activity_summary_list = [
        activity
        for activity in activity_summary_list
        if activity["id"] not in old_tracks_ids
    ]
    print(f"{len(activity_summary_list)} new activities to generate")
    tracks = []
    if with_gpx and not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)
    old_gpx_ids = os.listdir(GPX_FOLDER)
    old_gpx_ids = [i.split(".")[0] for i in old_gpx_ids if not i.startswith(".")]
    for activity_summary in activity_summary_list:
        activity_id = activity_summary["aid"]
        print(f"parsing activity id {activity_id}")
        try:
            activity_detail = get_activity_detail(s, headers, activity_id)
            track = merge_summary_and_detail_to_nametuple(
                activity_summary, activity_detail
            )
            tracks.append(track)
            if with_gpx and activity_summary["id"] not in old_gpx_ids:
                save_activity_gpx(activity_summary, activity_detail, track)
        except Exception as e:
            print(f"Something wrong parsing tulipsport id {activity_id} " + str(e))
    return tracks


def save_activity_gpx(summary, detail, track):
    if not summary["outdoor"]:
        return
    gpx = gpxpy.gpx.GPX()
    gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = track.name
    gpx.tracks.append(gpx_track)

    # 详情接口具体的内容参考文档链接：https://open.tulipsport.com/document
    # map_data_list 的结构为 [ [latitude, longitude, elevation, section, distance, hr, time, cadence], ... ]
    point_list = detail["map_data_list"]
    last_section = ""
    avg_hr = int(detail["avg_hr"]) if detail.__contains__("avg_hr") else 0
    avg_cadence = (
        int(detail["avg_cadence"]) if detail.__contains__("avg_cadence") else 0
    )
    for point in point_list:
        cur_section = point[3]
        if last_section != cur_section:
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)
            last_section = cur_section
        gpx_point = gpxpy.gpx.GPXTrackPoint(
            latitude=float(point[0]),
            longitude=float(point[1]),
            elevation=float(point[2]),
            time=adjust_time_to_utc(
                datetime.fromisoformat(point[6] + TIMEZONE_OFFSET), TIMEZONE_NAME
            ),
        )
        if avg_hr > 0 or avg_cadence > 0:
            extension_list = []
            if avg_hr > 0:
                extension_list.append(f"<gpxtpx:hr>{int(point[5])}</gpxtpx:hr>")
            if avg_cadence > 0:
                extension_list.append(f"<gpxtpx:cad>{int(point[7])}</gpxtpx:cad>")
            gpx_extension = ElementTree.fromstring(
                f"""<gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">{"".join(extension_list)}</gpxtpx:TrackPointExtension>"""
            )
            gpx_point.extensions.append(gpx_extension)

        gpx_segment.points.append(gpx_point)

    activity_id = summary["id"]
    try:
        print(f"saving tulipsport activity {str(activity_id)} gpx")
        file_path = os.path.join(GPX_FOLDER, str(activity_id) + ".gpx")
        with open(file_path, "w") as fb:
            fb.write(gpx.to_xml())
    except Exception as e:
        print(f"saving tulipsport activity {activity_id} gpx occurs errors: {str(e)}")
        pass


# 郁金香运动的活动 ID 采用 UUID 模式，而 DB 主键使用 long 类型，无法有效存储，所以采用构造个人唯一的活动 ID
# 模拟构造 ID = 特殊前缀 + 活动开始时间的 timestamp + 活动距离（单位：米）
def build_tulipsport_int_activity_id(activity):
    timestamp_str = str(
        int(datetime.fromisoformat(activity["start_date_local"] + "+08:00").timestamp())
    )
    distance_str = f'{int(float(activity["activity_distance"]) * 1000):0>6}'
    return TULIPSPORT_FAKE_ID_PREFIX + timestamp_str + distance_str


def sync_tulipsport_activites(token, with_gpx=False):
    generator = Generator(SQL_FILE)
    old_tracks_ids = generator.get_old_tracks_ids()
    new_tracks = get_new_activities(token, old_tracks_ids, with_gpx)
    generator.sync_from_app(new_tracks)

    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("token", help="TulipSport Open Platform's accessToken")
    parser.add_argument(
        "--with-gpx",
        dest="with_gpx",
        action="store_true",
        help="get all data save to gpx",
    )
    options = parser.parse_args()
    sync_tulipsport_activites(options.token, options.with_gpx)
