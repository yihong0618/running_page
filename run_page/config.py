import os
from collections import namedtuple
import yaml

# getting content root directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)

OUTPUT_DIR = os.path.join(parent, "activities")
GPX_FOLDER = os.path.join(parent, "GPX_OUT")
TCX_FOLDER = os.path.join(parent, "TCX_OUT")
FIT_FOLDER = os.path.join(parent, "FIT_OUT")
ENDOMONDO_FILE_DIR = os.path.join(parent, "Workouts")
FOLDER_DICT = {
    "gpx": GPX_FOLDER,
    "tcx": TCX_FOLDER,
    "fit": FIT_FOLDER,
}
SQL_FILE = os.path.join(parent, "run_page", "data.db")
JSON_FILE = os.path.join(parent, "src", "static", "activities.json")
SYNCED_FILE = os.path.join(parent, "imported.json")

# TODO: Move into nike_sync
BASE_URL = "https://api.nike.com/sport/v3/me"
TOKEN_REFRESH_URL = "https://unite.nike.com/tokenRefresh"
NIKE_CLIENT_ID = "HlHa2Cje3ctlaOqnxvgZXNaAs7T9nAuH"
BASE_TIMEZONE = "Asia/Shanghai"


start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")

try:
    with open("config.yaml") as f:
        _config = yaml.safe_load(f)
except:
    _config = {}


def config(*keys):
    def safeget(dct, *keys):
        for key in keys:
            try:
                dct = dct[key]
            except KeyError:
                return None
        return dct

    return safeget(_config, *keys)


# add more type here
TYPE_DICT = {
    "running": "Run",
    "RUN": "Run",
    "Run": "Run",
    "track_running": "Run",
    "trail_running": "Trail Running",
    "cycling": "Ride",
    "CYCLING": "Ride",
    "Ride": "Ride",
    "road_biking": "Ride",
    "VirtualRide": "VirtualRide",
    "indoor_cycling": "Indoor Ride",
    "walking": "Hike",
    "hiking": "Hike",
    "Walk": "Hike",
    "Hike": "Hike",
    "Swim": "Swim",
    "rowing": "Rowing",
    "RoadTrip": "RoadTrip",
    "flight": "Flight",
    "kayaking": "Kayaking",
    "Snowboard": "Snowboard",
    "resort_skiing_snowboarding_ws": "Ski",  # garmin
    "AlpineSki": "Ski",  # strava
    "Ski": "Ski",
}

MAPPING_TYPE = [
    "Hike",
    "Ride",
    "VirtualRide",
    "Rowing",
    "Run",
    "Trail Running",
    "Swim",
    "RoadTrip",
    "Kayaking",
    "Snowboard",
    "Ski",
]

STRAVA_GARMIN_TYPE_DICT = {
    "Hike": "hiking",
    "Run": "running",
    "EBikeRide": "cycling",
    "VirtualRide": "VirtualRide",
    "Walk": "walking",
    "Swim": "swimming",
}
