import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import gpxpy
import pytz

try:
    from rich import print
except Exception:
    pass
from generator import Generator
from stravalib.client import Client
from stravalib.exc import RateLimitExceeded


def adjust_time(time, tz_name):
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    return time + tc_offset


def adjust_time_to_utc(time, tz_name):
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    return time - tc_offset


def adjust_timestamp_to_utc(timestamp, tz_name):
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    delta = int(tc_offset.total_seconds())
    return int(timestamp) - delta


def to_date(ts):
    # TODO use https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat
    # once we decide to move on to python v3.7+
    ts_fmts = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]

    for ts_fmt in ts_fmts:
        try:
            # performance with using exceptions
            # shouldn't be an issue since it's an offline cmdline tool
            return datetime.strptime(ts, ts_fmt)
        except ValueError:
            pass

    raise ValueError(f"cannot parse timestamp {ts} into date with fmts: {ts_fmts}")


def make_activities_file(
    sql_file, data_dir, json_file, file_suffix="gpx", activity_title_dict={}
):
    generator = Generator(sql_file)
    generator.sync_from_data_dir(
        data_dir, file_suffix=file_suffix, activity_title_dict=activity_title_dict
    )
    activities_list = generator.load()
    with open(json_file, "w") as f:
        json.dump(activities_list, f)


def make_strava_client(client_id, client_secret, refresh_token):
    client = Client()

    refresh_response = client.refresh_access_token(
        client_id=client_id, client_secret=client_secret, refresh_token=refresh_token
    )
    client.access_token = refresh_response["access_token"]
    return client


def get_strava_last_time(client, is_milliseconds=True):
    """
    if there is no activities cause exception return 0
    """
    try:
        activity = None
        activities = client.get_activities(limit=10)
        activities = list(activities)
        activities.sort(key=lambda x: x.start_date, reverse=True)
        # for else in python if you don't know please google it.
        for a in activities:
            if a.type == "Run":
                activity = a
                break
        else:
            return 0
        end_date = activity.start_date + activity.elapsed_time
        last_time = int(datetime.timestamp(end_date))
        if is_milliseconds:
            last_time = last_time * 1000
        return last_time
    except Exception as e:
        print(f"Something wrong to get last time err: {str(e)}")
        return 0


def upload_file_to_strava(client, file_name, data_type, force_to_run=True):
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
            if force_to_run:
                r = client.upload_activity(
                    activity_file=f, data_type=data_type, activity_type="run"
                )
            else:
                r = client.upload_activity(activity_file=f, data_type=data_type)
        print(
            f"Uploading {data_type} file: {file_name} to strava, upload_id: {r.upload_id}."
        )


def create_tcx_root():
    """
    Create the root TCX TrainingCenterDatabase element with standard namespaces.

    Returns:
        ET.Element: The root TrainingCenterDatabase element
    """
    return ET.Element(
        "TrainingCenterDatabase",
        {
            "xmlns": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
            "xmlns:ns5": "http://www.garmin.com/xmlschemas/ActivityGoals/v1",
            "xmlns:ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
            "xmlns:ns2": "http://www.garmin.com/xmlschemas/UserProfile/v2",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:ns4": "http://www.garmin.com/xmlschemas/ProfileExtension/v1",
            "xsi:schemaLocation": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd",
        },
    )


def add_tcx_author(root, part_number="000-00000-00"):
    """
    Add Author element to TCX root with standard Connect API information.

    Args:
        root: The root TrainingCenterDatabase element
        part_number: The device part number (default: "000-00000-00")
    """
    author = ET.Element("Author", {"xsi:type": "Application_t"})
    root.append(author)

    author_name = ET.Element("Name")
    author_name.text = "Connect Api"
    author.append(author_name)

    author_lang = ET.Element("LangID")
    author_lang.text = "en"
    author.append(author_lang)

    author_part = ET.Element("PartNumber")
    author_part.text = part_number
    author.append(author_part)


def create_gpx_track_segment(points_dict_list):
    """
    Create a GPX track segment from a list of point dictionaries.

    Args:
        points_dict_list: List of dictionaries with keys: latitude, longitude, time, elevation (optional), hr (optional), cad (optional)

    Returns:
        gpxpy.gpx.GPXTrackSegment: The created track segment
    """
    gpx_segment = gpxpy.gpx.GPXTrackSegment()

    for p in points_dict_list:
        point = gpxpy.gpx.GPXTrackPoint(
            latitude=p["latitude"],
            longitude=p["longitude"],
            time=p["time"],
            elevation=p.get("elevation"),
        )

        # Add heart rate and/or cadence extension if available
        hr = p.get("hr")
        cad = p.get("cad")
        if hr is not None or cad is not None:
            hr_str = f"<gpxtpx:hr>{hr}</gpxtpx:hr>" if hr is not None else ""
            cad_str = f"<gpxtpx:cad>{cad}</gpxtpx:cad>" if cad is not None else ""
            gpx_extension = ET.fromstring(
                f"""<gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
                    {hr_str}
                    {cad_str}
                    </gpxtpx:TrackPointExtension>
                    """
            )
            point.extensions.append(gpx_extension)

        gpx_segment.points.append(point)

    return gpx_segment


def add_argparse_arguments(parser, args_config):
    """
    Add common arguments to an ArgumentParser based on configuration.

    Args:
        parser: argparse.ArgumentParser instance
        args_config: Dictionary with argument names as keys and configuration as values
                     Example: {"is_cn": True, "only_run": True, "tcx": True, "all": True}

    Returns:
        argparse.ArgumentParser: The parser with added arguments
    """
    if args_config.get("is_cn"):
        parser.add_argument(
            "--is-cn",
            dest="is_cn",
            action="store_true",
            help="if garmin account is cn",
        )

    if args_config.get("only_run"):
        parser.add_argument(
            "--only-run",
            dest="only_run",
            action="store_true",
            help="if is only for running",
        )

    if args_config.get("tcx"):
        parser.add_argument(
            "--tcx",
            dest="download_file_type",
            action="store_const",
            const="tcx",
            default="gpx",
            help="to download personal documents or ebook",
        )

    if args_config.get("fit"):
        parser.add_argument(
            "--fit",
            dest="download_file_type",
            action="store_const",
            const="fit",
            help="download as fit file format",
        )

    if args_config.get("all"):
        parser.add_argument(
            "--all",
            dest="all",
            action="store_true",
            help="if upload to strava all without check last time",
        )

    return parser
