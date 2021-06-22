#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime

import pytz
from generator import Generator


def adjust_time(time, tz_name):
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    return time + tc_offset


def make_activities_file(sql_file, gpx_dir, json_file):
    generator = Generator(sql_file)
    generator.sync_from_gpx(gpx_dir)
    activities_list = generator.load()
    with open(json_file, "w") as f:
        json.dump(activities_list, f)
