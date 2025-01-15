import argparse
import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import namedtuple
from datetime import datetime, timedelta
from xml.dom import minidom

import eviltransform
import gpxpy
import numpy as np
import polyline
import requests
from config import (
    BASE_TIMEZONE,
    GPX_FOLDER,
    JSON_FILE,
    SQL_FILE,
    TCX_FOLDER,
    run_map,
    start_point,
)

#根据data.db生成json文件,Json文件影响页面的展示

from generator import Generator
from tzlocal import get_localzone
from utils import adjust_time_to_utc, adjust_timestamp_to_utc, to_date
#def test():
if __name__ == "__main__":
    generator = Generator(SQL_FILE)
    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f, indent=0)