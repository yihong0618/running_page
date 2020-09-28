#!/usr/bin/env python3

import datetime
import time
import json
import os
import argparse

from generator import Generator

JSON_FILE = "src/static/activities.js"
SQL_FILE = "scripts/data.db"
GPX_DIR = "GPX_OUT"


def run(client_id, client_secret, refresh_token):
    generator = Generator(SQL_FILE)
    # if you want to update data change False to True
    generator.sync_from_gpx(GPX_DIR, False)
    # generator.sync()
    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:

        f.write("const activities = ")
        json.dump(activities_list, f, indent=2)
        f.write(";\n")
        f.write("\n")
        f.write("export {activities};\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", help="strava client id")
    parser.add_argument("client_secret", help="strava client secret")
    parser.add_argument("refresh_token", help="strava refresh token")
    options = parser.parse_args()
    # maybe upload not done just tricky
    # time.sleep(10)
    run(options.client_id, options.client_secret, options.refresh_token)
