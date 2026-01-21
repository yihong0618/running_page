import json
import time
from datetime import datetime
from typing import Dict, Optional

import pytz

try:
    from rich import print
except Exception:
    pass
from generator import Generator
from stravalib.client import Client
from stravalib.exc import RateLimitExceeded


def adjust_time(time: datetime, tz_name: str) -> datetime:
    """
    Adjust a datetime object by adding the timezone offset.
    
    Args:
        time: The datetime object to adjust
        tz_name: The timezone name (e.g., 'Asia/Shanghai')
        
    Returns:
        Adjusted datetime object
    """
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    return time + tc_offset


def adjust_time_to_utc(time: datetime, tz_name: str) -> datetime:
    """
    Convert a datetime object to UTC by subtracting the timezone offset.
    
    Args:
        time: The datetime object to convert
        tz_name: The timezone name (e.g., 'Asia/Shanghai')
        
    Returns:
        UTC datetime object
    """
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    return time - tc_offset


def adjust_timestamp_to_utc(timestamp: int, tz_name: str) -> int:
    """
    Convert a timestamp to UTC by subtracting the timezone offset.
    
    Args:
        timestamp: The timestamp to convert
        tz_name: The timezone name (e.g., 'Asia/Shanghai')
        
    Returns:
        UTC timestamp
    """
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    delta = int(tc_offset.total_seconds())
    return int(timestamp) - delta


def to_date(ts: str) -> datetime:
    """
    Parse ISO format timestamp string to datetime object.
    Uses datetime.fromisoformat() for standard ISO format strings.
    Falls back to strptime for non-standard formats.
    
    Args:
        ts: ISO format timestamp string
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValueError: If the timestamp cannot be parsed
    """
    # Try fromisoformat first (Python 3.7+)
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        # Fallback to strptime for non-standard formats
        ts_fmts = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]
        for ts_fmt in ts_fmts:
            try:
                return datetime.strptime(ts, ts_fmt)
            except ValueError:
                pass
        raise ValueError(f"cannot parse timestamp {ts} into date")


def make_activities_file(
    sql_file: str,
    data_dir: str,
    json_file: str,
    file_suffix: str = "gpx",
    activity_title_dict: Optional[Dict] = None,
) -> None:
    """
    Generate activities JSON file from SQL database and data directory.
    
    Args:
        sql_file: Path to SQLite database file
        data_dir: Directory containing activity files (GPX, FIT, etc.)
        json_file: Output JSON file path
        file_suffix: File extension to process (default: "gpx")
        activity_title_dict: Optional dictionary mapping activity IDs to titles
    """
    if activity_title_dict is None:
        activity_title_dict = {}
    generator = Generator(sql_file)
    generator.sync_from_data_dir(
        data_dir, file_suffix=file_suffix, activity_title_dict=activity_title_dict
    )
    activities_list = generator.load()
    with open(json_file, "w") as f:
        json.dump(activities_list, f)


def make_strava_client(client_id: str, client_secret: str, refresh_token: str) -> Client:
    """
    Create and authenticate a Strava API client.
    
    Args:
        client_id: Strava application client ID
        client_secret: Strava application client secret
        refresh_token: Strava refresh token
        
    Returns:
        Authenticated Strava client instance
    """
    client = Client()

    refresh_response = client.refresh_access_token(
        client_id=client_id, client_secret=client_secret, refresh_token=refresh_token
    )
    client.access_token = refresh_response["access_token"]
    return client


def get_strava_last_time(client: Client, is_milliseconds: bool = True) -> int:
    """
    Get the timestamp of the end time of the most recent running activity.
    
    Args:
        client: Authenticated Strava client instance
        is_milliseconds: If True, return timestamp in milliseconds; otherwise in seconds
        
    Returns:
        Timestamp of the end time of the most recent run, or 0 if no runs found or error occurs
    """
    try:
        activity = None
        activities = client.get_activities(limit=10)
        activities = list(activities)
        activities.sort(key=lambda x: x.start_date, reverse=True)
        # Find the most recent Run activity
        for a in activities:
            if a.type == "Run":
                activity = a
                break
        else:
            # No Run activities found in the recent activities
            return 0
        end_date = activity.start_date + activity.elapsed_time
        last_time = int(datetime.timestamp(end_date))
        if is_milliseconds:
            last_time = last_time * 1000
        return last_time
    except Exception as e:
        print(f"Error retrieving last Strava activity time: {str(e)}")
        return 0


def upload_file_to_strava(
    client: Client, file_name: str, data_type: str, force_to_run: bool = True
) -> None:
    """
    Upload an activity file to Strava.
    
    Args:
        client: Authenticated Strava client instance
        file_name: Path to the activity file to upload
        data_type: File type (e.g., 'gpx', 'tcx', 'fit')
        force_to_run: If True, force activity type to 'run'
        
    Note:
        Automatically handles rate limiting by retrying after the specified timeout.
    """
    with open(file_name, "rb") as f:
        try:
            if force_to_run:
                r = client.upload_activity(
                    activity_file=f, data_type=data_type, activity_type="run"
                )
            else:
                r = client.upload_activity(activity_file=f, data_type=data_type)

        except RateLimitExceeded as e:
            timeout = e.timeout
            print(f"Strava API Rate Limit Exceeded. Retry after {timeout} seconds")
            time.sleep(timeout)
            # Reset file pointer to beginning for retry
            f.seek(0)
            if force_to_run:
                r = client.upload_activity(
                    activity_file=f, data_type=data_type, activity_type="run"
                )
            else:
                r = client.upload_activity(activity_file=f, data_type=data_type)
        print(
            f"Uploading {data_type} file: {file_name} to strava, upload_id: {r.upload_id}."
        )
