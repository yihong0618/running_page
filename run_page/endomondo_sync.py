"""
need to download the files from endomondo
and store it in Workouts dir in running_page
"""

import json
import os
from collections import namedtuple
from datetime import datetime, timedelta

import polyline
from config import BASE_TIMEZONE, ENDOMONDO_FILE_DIR, JSON_FILE, SQL_FILE
from generator import Generator

from utils import adjust_time

# Activity type mapping from Endomondo to Strava-compatible types
ENDOMONDO_TO_STRAVA_TYPE = {
    "running": "Run",
    "cycling": "Ride",
    "walking": "Walk",
    "hiking": "Hike",
    "mountain_biking": "Ride",
    "skating": "IceSkate",
    "skiing": "AlpineSki",
    "swimming": "Swim",
    "other": "Run",  # Default to Run for unknown types
}

start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")


def _make_heart_rate(en_dict):
    """
    Extract average heart rate from Endomondo data.

    Looks for heart rate data in:
    1. Summary data (heart_rate_avg, avg_heart_rate, average_heart_rate)
    2. Points data (heart_rate values in track points)

    :param en_dict: Endomondo activity dictionary
    :return: Average heart rate as integer, or None if not available
    """
    # Try to get heart rate from summary data first
    heart_rate = (
        en_dict.get("heart_rate_avg")
        or en_dict.get("avg_heart_rate")
        or en_dict.get("average_heart_rate")
        or en_dict.get("heart_rate")
    )

    if heart_rate is not None:
        try:
            heart_rate = int(heart_rate)
            # Validate heart rate is in reasonable range (30-220 bpm)
            if 30 <= heart_rate <= 220:
                return heart_rate
        except (ValueError, TypeError):
            pass

    # If not in summary, try to calculate from points data
    points = en_dict.get("points", [])
    heart_rates = []

    for point in points:
        if isinstance(point, dict):
            # Check if point has heart rate directly
            hr = point.get("heart_rate") or point.get("hr")
            if hr is not None:
                try:
                    hr_value = int(hr)
                    if 30 <= hr_value <= 220:
                        heart_rates.append(hr_value)
                except (ValueError, TypeError):
                    continue
        elif isinstance(point, list):
            # Handle nested structure
            for attr in point:
                if isinstance(attr, dict):
                    hr = attr.get("heart_rate") or attr.get("hr")
                    if hr is not None:
                        try:
                            hr_value = int(hr)
                            if 30 <= hr_value <= 220:
                                heart_rates.append(hr_value)
                        except (ValueError, TypeError):
                            continue

    # Calculate average if we have heart rate data
    if heart_rates:
        return int(sum(heart_rates) / len(heart_rates))

    return None


def _make_endomondo_id(file_name):
    endomondo_id = file_name.split(os.sep)[-1].split(".")[0]
    endomondo_id = endomondo_id.replace(" ", "").replace("_", "").replace("-", "")
    return endomondo_id


def _get_activity_type(en_dict):
    """
    Extract activity type from Endomondo data and map to Strava-compatible type.

    :param en_dict: Endomondo activity dictionary
    :return: Tuple of (type, subtype) as strings
    """
    # Try various possible keys for sport/activity type
    sport_type = (
        en_dict.get("sport")
        or en_dict.get("sport_type")
        or en_dict.get("activity_type")
        or en_dict.get("type")
        or "running"  # Default to running
    )

    # Normalize to lowercase for mapping
    if isinstance(sport_type, str):
        sport_type = sport_type.lower().replace(" ", "_")

    # Map to Strava-compatible type
    mapped_type = ENDOMONDO_TO_STRAVA_TYPE.get(sport_type, "Run")

    return mapped_type, mapped_type


def _extract_location_points(points):
    """
    Extract all location points from Endomondo points data.

    Handles various data structures:
    - Points as list of dicts with location data
    - Points as list of lists with nested location data
    - Direct location coordinates

    :param points: Points data from Endomondo
    :return: List of [latitude, longitude] pairs
    """
    location_points = []

    if not points:
        return location_points

    for point in points:
        if isinstance(point, dict):
            # Direct location in point dict
            if "location" in point:
                loc = point["location"]
                if isinstance(loc, list) and len(loc) >= 2:
                    # Handle [lat, lon] format
                    if isinstance(loc[0], (int, float)) and isinstance(
                        loc[1], (int, float)
                    ):
                        location_points.append([float(loc[0]), float(loc[1])])
                    # Handle nested dict format
                    elif isinstance(loc[0], dict) and isinstance(loc[1], dict):
                        lat = loc[0].get("latitude") or loc[0].get("lat")
                        lon = loc[1].get("longitude") or loc[1].get("lon")
                        if lat is not None and lon is not None:
                            location_points.append([float(lat), float(lon)])
            # Check for lat/lon directly
            elif "latitude" in point and "longitude" in point:
                location_points.append(
                    [float(point["latitude"]), float(point["longitude"])]
                )
            elif "lat" in point and "lon" in point:
                location_points.append([float(point["lat"]), float(point["lon"])])
        elif isinstance(point, list):
            # Handle nested list structure
            for attr in point:
                if isinstance(attr, dict):
                    if "location" in attr:
                        loc = attr["location"]
                        if isinstance(loc, list) and len(loc) >= 2:
                            if isinstance(loc[0], dict) and isinstance(loc[1], dict):
                                lat = loc[0].get("latitude") or loc[0].get("lat")
                                lon = loc[1].get("longitude") or loc[1].get("lon")
                                if lat is not None and lon is not None:
                                    location_points.append([float(lat), float(lon)])
                            elif isinstance(loc[0], (int, float)) and isinstance(
                                loc[1], (int, float)
                            ):
                                location_points.append([float(loc[0]), float(loc[1])])
                    elif "latitude" in attr and "longitude" in attr:
                        location_points.append(
                            [float(attr["latitude"]), float(attr["longitude"])]
                        )

    return location_points


def parse_run_endomondo_to_nametuple(en_dict):
    """
    Parse Endomondo activity data to namedtuple format.

    :param en_dict: Endomondo activity dictionary
    :return: Namedtuple with activity data
    """
    points = en_dict.get("points", [])
    location_points = _extract_location_points(points)

    polyline_str = polyline.encode(location_points) if location_points else ""
    start_latlng = start_point(*location_points[0]) if location_points else None

    # Parse dates
    start_date_str = en_dict.get("start_time") or en_dict.get("startTime")
    end_date_str = en_dict.get("end_time") or en_dict.get("endTime")

    if not start_date_str or not end_date_str:
        raise ValueError("Missing start_time or end_time in Endomondo data")

    # Handle different date formats
    date_formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ]

    start_date = None
    end_date = None

    for fmt in date_formats:
        try:
            start_date = datetime.strptime(start_date_str, fmt)
            end_date = datetime.strptime(end_date_str, fmt)
            break
        except (ValueError, TypeError):
            continue

    if start_date is None or end_date is None:
        raise ValueError(f"Unable to parse dates: {start_date_str}, {end_date_str}")

    start_date_local = adjust_time(start_date, BASE_TIMEZONE)
    end_date_local = adjust_time(end_date, BASE_TIMEZONE)

    # Extract heart rate
    heart_rate = _make_heart_rate(en_dict)

    # Get activity type
    activity_type, subtype = _get_activity_type(en_dict)

    # Calculate distance and duration
    distance_km = en_dict.get("distance_km") or en_dict.get("distanceKm") or 0
    duration_s = (
        en_dict.get("duration_s")
        or en_dict.get("durationS")
        or en_dict.get("duration")
        or 1
    )

    # Calculate average speed (m/s)
    average_speed = (distance_km * 1000) / duration_s if duration_s > 0 else 0

    # Get elevation gain if available
    elevation_gain = (
        en_dict.get("elevation_gain")
        or en_dict.get("elevationGain")
        or en_dict.get("total_elevation_gain")
        or None
    )
    if elevation_gain is not None:
        try:
            elevation_gain = float(elevation_gain)
        except (ValueError, TypeError):
            elevation_gain = None

    # Get location country if available
    location_country = (
        en_dict.get("location_country")
        or en_dict.get("locationCountry")
        or en_dict.get("country")
        or ""
    )

    # Create activity name
    activity_name = f"{activity_type} from endomondo"
    if en_dict.get("name"):
        activity_name = en_dict.get("name")

    d = {
        "id": en_dict.get("id"),
        "name": activity_name,
        "type": activity_type,
        "subtype": subtype,
        "start_date": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
        "end": datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S"),
        "start_date_local": datetime.strftime(start_date_local, "%Y-%m-%d %H:%M:%S"),
        "end_local": datetime.strftime(end_date_local, "%Y-%m-%d %H:%M:%S"),
        "length": distance_km * 1000,
        "average_heartrate": int(heart_rate) if heart_rate else None,
        "map": run_map(polyline_str),
        "start_latlng": start_latlng,
        "distance": distance_km * 1000,
        "moving_time": timedelta(seconds=duration_s),
        "elapsed_time": timedelta(seconds=duration_s),
        "average_speed": average_speed,
        "elevation_gain": elevation_gain,
        "location_country": location_country,
    }
    return namedtuple("x", d.keys())(*d.values())


def parse_one_endomondo_json(json_file_name):
    """
    Parse a single Endomondo JSON file.

    :param json_file_name: Path to the Endomondo JSON file
    :return: Dictionary with parsed Endomondo activity data
    """
    try:
        with open(json_file_name, encoding="utf-8") as f:
            content = json.loads(f.read())
    except (json.JSONDecodeError, IOError) as e:
        raise ValueError(f"Error reading JSON file {json_file_name}: {e}")

    d = {}
    # use file name as id
    endomondo_id = _make_endomondo_id(json_file_name)
    print(f"Processing Endomondo activity: {endomondo_id}")

    if not endomondo_id:
        raise ValueError(f"No endomondo id generated from filename: {json_file_name}")

    d["id"] = endomondo_id

    # endomondo list -> dict
    # Handle both list and dict formats
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict):
                d.update(**c)
    elif isinstance(content, dict):
        d.update(**content)

    return d


def get_all_en_endomondo_json_file(file_dir=ENDOMONDO_FILE_DIR):
    dirs = os.listdir(file_dir)
    json_files = [os.path.join(file_dir, i) for i in dirs if i.endswith(".json")]
    return json_files


def run_enomondo_sync():
    """
    Main function to sync all Endomondo activities.

    Reads all JSON files from the Workouts directory, parses them,
    and syncs to the database.
    """
    generator = Generator(SQL_FILE)
    old_tracks_ids = generator.get_old_tracks_ids()
    json_files_list = get_all_en_endomondo_json_file()

    if not json_files_list:
        raise FileNotFoundError(
            f"No JSON files found in {ENDOMONDO_FILE_DIR}. "
            "Please ensure Endomondo export files are placed in the Workouts directory."
        )

    tracks = []
    skipped_count = 0
    error_count = 0

    for json_file in json_files_list:
        try:
            endomondo_id = _make_endomondo_id(json_file)
            if endomondo_id in old_tracks_ids:
                skipped_count += 1
                continue

            en_dict = parse_one_endomondo_json(json_file)
            track = parse_run_endomondo_to_nametuple(en_dict)
            tracks.append(track)
        except Exception as e:
            error_count += 1
            print(f"Error processing {json_file}: {e}")
            continue

    print(
        f"Processed {len(tracks)} activities, skipped {skipped_count}, errors {error_count}"
    )

    if tracks:
        generator.sync_from_app(tracks)
        activities_list = generator.load()
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(activities_list, f, indent=2, ensure_ascii=False)
        print(f"Successfully synced {len(tracks)} Endomondo activities")
    else:
        print("No new activities to sync")


if __name__ == "__main__":
    run_enomondo_sync()
