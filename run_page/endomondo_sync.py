"""
need to download the files from endomondo
and store it in Workous dir in running_page
"""

import json
import os
from collections import namedtuple
from datetime import datetime, timedelta

import polyline
from config import BASE_TIMEZONE, ENDOMONDO_FILE_DIR, JSON_FILE, SQL_FILE
from generator import Generator

from utils import adjust_time

# TODO Same as keep_sync maybe refactor
start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")


def _make_heart_rate(en_dict):
    """
    #TODO
    """
    return None


def _make_endomondo_id(file_name):
    endomondo_id = file_name.split(os.sep)[-1].split(".")[0]
    endomondo_id = endomondo_id.replace(" ", "").replace("_", "").replace("-", "")
    return endomondo_id


def parse_run_endomondo_to_nametuple(en_dict):
    points = en_dict.get("points", [])
    location_points = []
    for p in points:
        for attr in p:
            if attr.get("location"):
                # WTF TODO? maybe more points?
                lat, lon = attr.get("location")[0]
                location_points.append([lat.get("latitude"), lon.get("longitude")])
    polyline_str = polyline.encode(location_points) if location_points else ""
    start_latlng = start_point(*location_points[0]) if location_points else None
    start_date = en_dict.get("start_time")
    start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
    end_date = en_dict.get("end_time")
    end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S.%f")
    start_date_local = adjust_time(start_date, BASE_TIMEZONE)
    end_date_local = adjust_time(end_date, BASE_TIMEZONE)
    heart_rate = _make_heart_rate(en_dict)
    d = {
        "id": en_dict.get("id"),
        "name": "run from endomondo",
        "type": "Run",  # TODO others
        "subtype": "Run",  # TODO others
        "start_date": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
        "end": datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S"),
        "start_date_local": datetime.strftime(start_date_local, "%Y-%m-%d %H:%M:%S"),
        "end_local": datetime.strftime(end_date_local, "%Y-%m-%d %H:%M:%S"),
        "length": en_dict.get("distance_km", 0) * 1000,
        "average_heartrate": int(heart_rate) if heart_rate else None,
        "map": run_map(polyline_str),
        "start_latlng": start_latlng,
        "distance": en_dict.get("distance_km", 0) * 1000,
        "moving_time": timedelta(seconds=en_dict.get("duration_s", 0)),
        "elapsed_time": timedelta(seconds=en_dict.get("duration_s", 0)),
        "average_speed": en_dict.get("distance_km", 0)
        / en_dict.get("duration_s", 1)
        * 1000,
        "elevation_gain": None,
        "location_country": "",
    }
    return namedtuple("x", d.keys())(*d.values())


def parse_one_endomondo_json(json_file_name):
    with open(json_file_name) as f:
        content = json.loads(f.read())
    d = {}
    # use file name as id
    endomondo_id = _make_endomondo_id(json_file_name)
    print(endomondo_id)
    if not endomondo_id:
        raise Exception("No endomondo id generated in {}".format(json_file_name))
    d["id"] = endomondo_id
    # endomondo list -> dict
    for c in content:
        d.update(**c)
    return d


def get_all_en_endomondo_json_file(file_dir=ENDOMONDO_FILE_DIR):
    dirs = os.listdir(file_dir)
    json_files = [os.path.join(file_dir, i) for i in dirs if i.endswith(".json")]
    return json_files


def run_enomondo_sync():
    generator = Generator(SQL_FILE)
    old_tracks_ids = generator.get_old_tracks_ids()
    json_files_list = get_all_en_endomondo_json_file()
    if not json_files_list:
        raise Exception("No json files found in {}".format(ENDOMONDO_FILE_DIR))
    tracks = []
    for i in json_files_list:
        if _make_endomondo_id(i) in old_tracks_ids:
            continue
        en_dict = parse_one_endomondo_json(i)
        track = parse_run_endomondo_to_nametuple(en_dict)
        tracks.append(track)
    generator.sync_from_app(tracks)
    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f, indent=0)


if __name__ == "__main__":
    run_enomondo_sync()
