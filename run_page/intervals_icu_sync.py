import argparse
import gzip
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import eviltransform
import gpxpy
import requests
from requests.auth import HTTPBasicAuth

from config import JSON_FILE, SQL_FILE, FOLDER_DICT
from utils import make_activities_file

BASE_URL = "https://intervals.icu/api/v1"
RUNNING_TYPES = ["Run", "VirtualRun", "TrailRun"]
TCX_NAMESPACE = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"


class IntervalsICU:
    def __init__(self, athlete_id, api_key):
        self.athlete_id = athlete_id
        self.api_key = api_key
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth("API_KEY", api_key)
        self.session.headers["Accept"] = "application/json"

    def get_activities(self, oldest, newest):
        url = (
            f"{BASE_URL}/athlete/{self.athlete_id}/activities"
            f"?oldest={oldest}&newest={newest}"
        )
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def download_activity_file(self, activity_id, file_type, output_folder):
        url = f"{BASE_URL}/activity/{activity_id}/file"
        numeric_id = str(activity_id).lstrip("i")
        output_path = os.path.join(output_folder, f"{numeric_id}.{file_type}")

        try:
            response = self.session.get(url)
            response.raise_for_status()
            content = response.content
            # Decompress only if gzip-compressed (magic bytes: 1f 8b)
            if content[:2] == bytes([0x1F, 0x8B]):
                content = gzip.decompress(content)

            with open(output_path, "wb") as f:
                f.write(content)

            return output_path
        except Exception:
            return None


def get_downloaded_ids(folder):
    return [i.split(".")[0] for i in os.listdir(folder) if not i.startswith(".")]


def correct_gpx_gcj02(file_path):
    """Convert GCJ-02 coordinates to WGS-84 in a GPX file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            gpx = gpxpy.parse(f)

        count = 0
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    wgs_lat, wgs_lng = eviltransform.gcj2wgs_exact(
                        point.latitude, point.longitude
                    )
                    point.latitude = wgs_lat
                    point.longitude = wgs_lng
                    count += 1

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(gpx.to_xml())

        print(f"  GCJ-02 → WGS-84: corrected {count} points in {file_path}")
    except Exception as e:
        print(f"  Warning: Failed to correct GCJ-02 coordinates in {file_path}: {e}")


def correct_tcx_gcj02(file_path):
    """Convert GCJ-02 coordinates to WGS-84 in a TCX file."""
    try:
        ET.register_namespace("", TCX_NAMESPACE)

        tree = ET.parse(file_path)
        root = tree.getroot()
        ns = TCX_NAMESPACE

        count = 0
        for position in root.iter(f"{{{ns}}}Position"):
            lat_el = position.find(f"{{{ns}}}LatitudeDegrees")
            lng_el = position.find(f"{{{ns}}}LongitudeDegrees")
            if lat_el is None or lng_el is None:
                continue
            lat = float(lat_el.text)
            lng = float(lng_el.text)
            wgs_lat, wgs_lng = eviltransform.gcj2wgs_exact(lat, lng)
            lat_el.text = str(wgs_lat)
            lng_el.text = str(wgs_lng)
            count += 1

        tree.write(file_path, xml_declaration=True, encoding="UTF-8")
        print(f"  GCJ-02 → WGS-84: corrected {count} positions in {file_path}")
    except Exception as e:
        print(f"  Warning: Failed to correct GCJ-02 coordinates in {file_path}: {e}")


def correct_fit_gcj02(file_path):
    """Convert GCJ-02 coordinates to WGS-84 in a FIT file."""
    try:
        from fit_tool.fit_file import FitFile
        from fit_tool.profile.messages.record_message import RecordMessage

        fit = FitFile.from_file(file_path)
        count = 0
        for record in fit.records:
            msg = record.message
            if isinstance(msg, RecordMessage):
                if msg.position_lat is not None and msg.position_long is not None:
                    wgs_lat, wgs_lng = eviltransform.gcj2wgs_exact(
                        msg.position_lat, msg.position_long
                    )
                    msg.position_lat = wgs_lat
                    msg.position_long = wgs_lng
                    count += 1
        fit.crc = None  # Reset CRC so it recalculates on write
        fit.to_file(file_path)
        print(f"  GCJ-02 → WGS-84: corrected {count} records in {file_path}")
    except Exception as e:
        print(f"  Warning: Failed to correct GCJ-02 coordinates in {file_path}: {e}")


def correct_file_gcj02(file_path, file_type):
    """Apply GCJ-02 to WGS-84 coordinate correction based on file type."""
    if file_type == "gpx":
        correct_gpx_gcj02(file_path)
    elif file_type == "tcx":
        correct_tcx_gcj02(file_path)
    elif file_type == "fit":
        correct_fit_gcj02(file_path)


def run():
    parser = argparse.ArgumentParser(
        description="Sync running activities from Intervals.icu"
    )
    parser.add_argument("athlete_id", help="Intervals.icu athlete ID")
    parser.add_argument("api_key", help="Intervals.icu API key")
    parser.add_argument(
        "--start-date",
        default="2015-01-01",
        help="Oldest date to sync (YYYY-MM-DD, default: 2015-01-01)",
    )
    parser.add_argument(
        "--all",
        dest="sync_all",
        action="store_true",
        help="Sync all activity types, not just running",
    )
    parser.add_argument(
        "--gcj02",
        action="store_true",
        help="Convert GCJ-02 coordinates to WGS-84 in downloaded files",
    )
    options = parser.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    client = IntervalsICU(options.athlete_id, options.api_key)
    activities = client.get_activities(oldest=options.start_date, newest=today)

    if not options.sync_all:
        activities = [
            activity for activity in activities if activity.get("type") in RUNNING_TYPES
        ]

    # Only activities with a declared file type and supported folder mapping
    candidates = []
    activity_title_dict = {}
    for activity in activities:
        file_type = activity.get("file_type")
        if not file_type:
            continue
        file_type = str(file_type).lower()
        if file_type not in FOLDER_DICT:
            continue
        candidates.append((activity, file_type))
        # Build title dict keyed by numeric ID (matching downloaded filename)
        numeric_id = str(activity["id"]).lstrip("i")
        if activity.get("name"):
            activity_title_dict[numeric_id] = activity["name"]

    downloaded_count = 0
    used_file_types = set()
    all_file_types = {ft for _, ft in candidates}
    total = len(candidates)

    for n, (activity, file_type) in enumerate(candidates, start=1):
        output_folder = FOLDER_DICT[file_type]
        numeric_id = str(activity["id"]).lstrip("i")
        output_path = os.path.join(output_folder, f"{numeric_id}.{file_type}")

        if os.path.exists(output_path):
            continue

        activity_id = activity["id"]
        print(f"Downloading activity {activity_id} ({n}/{total})...")

        try:
            saved_path = client.download_activity_file(
                activity_id, file_type, output_folder
            )
            if saved_path:
                downloaded_count += 1
                used_file_types.add(file_type)
                if options.gcj02:
                    correct_file_gcj02(saved_path, file_type)
            else:
                print(
                    f"Warning: Failed to download activity {activity_id}: unknown error"
                )
        except Exception as e:
            print(f"Warning: Failed to download activity {activity_id}: {e}")

        time.sleep(1)

    for file_type in all_file_types:
        make_activities_file(
            SQL_FILE,
            FOLDER_DICT[file_type],
            JSON_FILE,
            file_suffix=file_type,
            activity_title_dict=activity_title_dict,
        )

    print(f"Done. Downloaded {downloaded_count} new activities.")


if __name__ == "__main__":
    run()
