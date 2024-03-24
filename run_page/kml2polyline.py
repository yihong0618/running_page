import json
from datetime import datetime, timedelta

import eviltransform
import polyline
from config import JSON_FILE, SQL_FILE
from fastkml import kml
from generator import Generator
from gpxtrackposter.track import Track, start_point

# set to False if your trip is not in china mainland
IN_CHINA = True


def get_points_from_kml(k: kml):
    points = []
    document = list(k.features())[0]
    for folder in list(document.features()):
        if folder.geometry.geom_type == "LineString":
            points.extend(folder.geometry.coords)
    return [(p[1], p[0]) for p in points]


def load_kml_file(k: kml):
    file = "run_page/import.kml"
    try:
        with open(file, "rb") as f:
            kml_string = f.read()
            # Read in the KML string
            k.from_string(kml_string)
    except Exception as err:
        print(err)
        raise "kml file not exist. please place import.kml into script/ folder"

        exit(1)


def load_kml_data(track, k):
    track.moving_dict = {
        "distance": distance * 1000,
        "moving_time": timedelta(seconds=days * hours_per_day * 60 * 60),
        "elapsed_time": timedelta(seconds=days * 24 * 60 * 60),
    }
    track.run_id = int(datetime.timestamp(track.start_time) * 1000)
    track.start_time_local, track.end_time_local = track.start_time, track.end_time
    track.moving_dict["average_speed"] = track.moving_dict["distance"] / (
        days * hours_per_day * 60 * 60
    )
    polyline_container = get_points_from_kml(k)
    if IN_CHINA:
        # convert WGS-84 to GCJ-02
        polyline_container = [
            eviltransform.gcj2wgs(p[0], p[1]) for p in polyline_container
        ]

    track.start_latlng = start_point(polyline_container[0][0], polyline_container[0][1])
    track.polyline_str = polyline.encode(polyline_container)
    return track


if __name__ == "__main__":
    track = Track()
    # TODO modify here
    # trip name
    track.name = "2020-10 Tibet Road Trip"
    # start/end time Year-Month-Day-Hour-Minute
    track.start_time = datetime(2020, 9, 29, 10, 0)
    track.end_time = datetime(2020, 10, 10, 18, 0)
    # total distance
    distance = 4000  # KM
    # total days
    days = 12
    # average daily distacnce
    hours_per_day = 6
    track.type = "RoadTrip"
    track.source = "Google Maps"

    k = kml.KML()
    load_kml_file(k)
    load_kml_data(track, k)

    # save
    generator = Generator(SQL_FILE)
    generator.sync_from_kml_track(track)
    activities_list = generator.loadForMapping()
    with open(JSON_FILE, "w") as json_file:
        json.dump(activities_list, json_file, indent=0)
