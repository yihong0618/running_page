import json
import time
from datetime import datetime

import pytz

import gpxpy
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np

try:
    from rich import print
except:
    pass
from generator import Generator
from stravalib.client import Client
from stravalib.exc import RateLimitExceeded
from collections import namedtuple

Metadata = namedtuple("Metadata", ("name", "type", "desc", "link"))


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
            print("Error: Can not execute strptime")
            pass

    raise ValueError(f"cannot parse timestamp {ts} into date with fmts: {ts_fmts}")


def make_activities_file(sql_file, data_dir, json_file, file_suffix="gpx"):
    generator = Generator(sql_file)
    generator.sync_from_data_dir(data_dir, file_suffix=file_suffix)
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
            print()
            print(f"Strava API Rate Limit Exceeded. Retry after {timeout} seconds")
            print()
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


def parse_df_points_to_gpx(
    metadata,
    df_points,
    col_lat="latitude",
    col_long="longitude",
    col_time="time",
    col_ele="elevation",
    col_hr="hr",
):
    """
    Convert a pandas dataframe to gpx
    Parameters:
        metadata(Metadata): metadata of the gpx track
        df_points (pd.DataFrame): pandas dataframe containing at minimum lat,long,time info of points
    """
    gpx = gpxpy.gpx.GPX()
    gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # support multi tracks in the future
    gpx.tracks[0].name = metadata.name
    gpx.tracks[0].type = metadata.type
    gpx.tracks[0].description = metadata.desc
    gpx.tracks[0].link = metadata.link

    for idx in df_points.index:
        track_point = gpxpy.gpx.GPXTrackPoint(
            latitude=df_points.loc[idx, col_lat],
            longitude=df_points.loc[idx, col_long],
            time=pd.Timestamp(df_points.loc[idx, col_time]),
            elevation=df_points.loc[idx, col_ele] if col_ele else None,
        )

        # gpx extensions
        if df_points.loc[idx, col_hr] and not np.isnan(df_points.loc[idx, col_hr]):
            hr = int(df_points.loc[idx, col_hr])
            gpx_extension_hr = ET.fromstring(
                f"""<gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
                <gpxtpx:hr>{hr}</gpxtpx:hr>
                </gpxtpx:TrackPointExtension>
                """
            )
            track_point.extensions.append(gpx_extension_hr)
        gpx_segment.points.append(track_point)
    return gpx.to_xml()
