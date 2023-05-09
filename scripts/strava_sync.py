import argparse
import csv
import json

from config import JSON_FILE, SQL_FILE, CSV_FILE
from generator import Generator


def run_strava_sync(client_id, client_secret, refresh_token):
    generator = Generator(SQL_FILE)
    generator.set_strava_config(client_id, client_secret, refresh_token)
    # if you want to refresh data change False to True
    generator.sync(True)

    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f)

    run_data = [
        [
            d["start_date_local"],
            d["name"],
            d["distance"],
            d["moving_time"],
            d["location_country"],
        ]
        for d in activities_list
    ]

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(run_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", help="strava client id")
    parser.add_argument("client_secret", help="strava client secret")
    parser.add_argument("refresh_token", help="strava refresh token")
    options = parser.parse_args()
    run_strava_sync(options.client_id, options.client_secret, options.refresh_token)
