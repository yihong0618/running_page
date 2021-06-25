import os
from collections import namedtuple
from re import M

import yaml

GET_DIR = "activities"
OUTPUT_DIR = "activities"
GPX_FOLDER = os.path.join(os.getcwd(), "GPX_OUT")
SQL_FILE = "scripts/data.db"
JSON_FILE = "src/static/activities.json"

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
STRAVA_GARMIN_TYPE_DICT = {
    "Hike": "hiking",
    "Run": "running",
    "EBikeRide": "cycling",
    "Walk": "walking",
    "Swim": "swimming",
}
