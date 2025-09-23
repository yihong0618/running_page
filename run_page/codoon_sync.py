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
from datetime import datetime, timedelta, timezone
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
from generator import Generator
from tzlocal import get_localzone
from utils import adjust_time_to_utc, adjust_timestamp_to_utc, to_date

# struct body
FitType = np.dtype(
    {
        "names": [
            "time",
            "bpm",
            "step",
            "lati",
            "longi",
            "elevation",
        ],  # unix timestamp, heart bpm, step, LatitudeDegrees, LongitudeDegrees, elevation
        "formats": ["i", "S4", "S4", "S32", "S32", "S8"],
    }
)

# device info
user_agent = "CodoonSport(8.9.0 1170;Android 7;Sony XZ1)"
did = "24-ffffffff-faac-3052-0033-c5870033c587"
# May be Forerunner 945?
CONNECT_API_PART_NUMBER = "006-D2449-00"

# fixed params
base_url = "https://api.codoon.com"
davinci = "0"
basic_auth = "MDk5Y2NlMjhjMDVmNmMzOWFkNWUwNGU1MWVkNjA3MDQ6YzM5ZDNmYmVhMWU4NWJlY2VlNDFjMTk5N2FjZjBlMzY="
client_id = "099cce28c05f6c39ad5e04e51ed60704"

# for multi sports
TYPE_DICT = {
    0: "Hike",
    1: "Run",
    2: "Ride",
}

# for tcx type
TCX_TYPE_DICT = {
    0: "Hiking",
    1: "Running",
    2: "Biking",
}

# only for running sports, if you want others, please change the True to False
IS_ONLY_RUN = False

# If your points need trans from gcj02 to wgs84 coordinate which use by Mapbox
TRANS_GCJ02_TO_WGS84 = False
# trans the coordinate data until the TRANS_END_DATE, work with TRANS_GCJ02_TO_WGS84 = True
TRANS_END_DATE = "2014-03-24"


# decrypt from libencrypt.so Java_com_codoon_jni_JNIUtils_encryptHttpSignature
# sha1 -> base64
def make_signature(message):
    key = bytes("ecc140ad6e1e12f7d972af04add2c7ee", "UTF-8")
    message = bytes(message, "UTF-8")
    digester = hmac.new(key, message, hashlib.sha1)
    signature1 = digester.digest()
    signature2 = base64.b64encode(signature1)
    return str(signature2, "UTF-8")


def device_info_headers():
    return {
        "accept-encoding": "gzip",
        "user-agent": user_agent,
        "did": did,
        "davinci": davinci,
    }


def download_codoon_gpx(gpx_data, log_id):
    try:
        print(f"downloading codoon {str(log_id)} gpx")
        file_path = os.path.join(GPX_FOLDER, str(log_id) + ".gpx")
        with open(file_path, "w") as fb:
            fb.write(gpx_data)
    except Exception as e:
        print(f"wrong id {log_id} error {str(e)}")
        pass


def formated_input(
    run_data, run_data_label, tcx_label
):  # load run_data from run_data_label, parse to tcx_label, return xml node
    fit_data = str(run_data[run_data_label])
    chile_node = ET.Element(tcx_label)
    chile_node.text = fit_data
    return chile_node


def tcx_output(fit_array, run_data):
    """
    If you want to make a more detailed tcx file, please refer to oppo_sync.py
    """
    # route ID
    fit_id = str(run_data["id"])
    # local time
    fit_start_time_local = run_data["start_time"]
    # zulu time
    utc = adjust_time_to_utc(to_date(fit_start_time_local), str(get_localzone()))
    fit_start_time = utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Root node
    training_center_database = ET.Element(
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
    # xml tree
    ET.ElementTree(training_center_database)
    # Activities
    activities = ET.Element("Activities")
    training_center_database.append(activities)
    # sport type
    sports_type = TCX_TYPE_DICT.get(run_data["sports_type"])
    # activity
    activity = ET.Element("Activity", {"Sport": sports_type})
    activities.append(activity)
    #   Id
    activity_id = ET.Element("Id")
    activity_id.text = fit_start_time  # Codoon use start_time as ID
    activity.append(activity_id)
    #   Creator
    activity_creator = ET.Element("Creator", {"xsi:type": "Device_t"})
    activity.append(activity_creator)
    #       Name
    activity_creator_name = ET.Element("Name")
    activity_creator_name.text = "Codoon"
    activity_creator.append(activity_creator_name)
    activity_creator_product = ET.Element("ProductID")
    activity_creator_product.text = "3441"
    activity_creator.append(activity_creator_product)
    #   Lap
    activity_lap = ET.Element("Lap", {"StartTime": fit_start_time})
    activity.append(activity_lap)
    #       TotalTimeSeconds
    activity_lap.append(formated_input(run_data, "total_time", "TotalTimeSeconds"))
    #       DistanceMeters
    activity_lap.append(formated_input(run_data, "total_length", "DistanceMeters"))
    #       Calories
    if "total_calories" in run_data:
        activity_lap.append(formated_input(run_data, "total_calories", "Calories"))
    #       AverageCadence
    if "average_step_cadence" in run_data:
        activity_lap.append(
            formated_input(run_data, "average_step_cadence", "AverageCadence")
        )
    #       MaximumCadence
    if "max_step_cadence" in run_data:
        activity_lap.append(
            formated_input(run_data, "max_step_cadence", "MaximumCadence")
        )

    # Track
    track = ET.Element("Track")
    activity_lap.append(track)
    for i in fit_array:
        tp = ET.Element("Trackpoint")
        track.append(tp)
        # Time
        time_stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime(i["time"]))
        time_label = ET.Element("Time")
        time_label.text = time_stamp
        tp.append(time_label)
        # HeartRateBpm
        # None was converted to bytes by np.dtype, becoming a string "None" after decode...-_-
        # as well as LatitudeDegrees and LongitudeDegrees below
        if not bytes.decode(i["bpm"]) == "None":
            bpm = ET.Element("HeartRateBpm")
            bpm_value = ET.Element("Value")
            bpm.append(bpm_value)
            bpm_value.text = bytes.decode(i["bpm"])
            tp.append(bpm)
        # Cadence
        # The unit is step-per-minute in Garmin
        # but is stride-per-minute in Strava, Coros, and RQrun
        if not bytes.decode(i["step"]) == "None":
            step = ET.Element("Cadence")
            step.text = bytes.decode(i["step"])
            tp.append(step)
        # Position
        if not bytes.decode(i["lati"]) == "None":
            position = ET.Element("Position")
            tp.append(position)
            #   LatitudeDegrees
            lati = ET.Element("LatitudeDegrees")
            lati.text = bytes.decode(i["lati"])
            position.append(lati)
            #   LongitudeDegrees
            longi = ET.Element("LongitudeDegrees")
            longi.text = bytes.decode(i["longi"])
            position.append(longi)
            #  AltitudeMeters
            altitude_meters = ET.Element("AltitudeMeters")
            altitude_meters.text = bytes.decode(i["elevation"])
            tp.append(altitude_meters)
    # Author
    author = ET.Element("Author", {"xsi:type": "Application_t"})
    training_center_database.append(author)
    author_name = ET.Element("Name")
    author_name.text = "Connect Api"
    author.append(author_name)
    author_lang = ET.Element("LangID")
    author_lang.text = "en"
    author.append(author_lang)
    author_part = ET.Element("PartNumber")
    author_part.text = CONNECT_API_PART_NUMBER
    author.append(author_part)
    # write to TCX file
    try:
        xml_str = minidom.parseString(
            ET.tostring(training_center_database)
        ).toprettyxml()
        with open(TCX_FOLDER + "/" + fit_id + ".tcx", "w") as f:
            f.write(str(xml_str))
    except Exception as e:
        print(f"empty database error {str(e)}")
        pass


def tcx_job(run_data):
    # fit struct array
    fit_array = None
    fit_list = []
    fit_hrs = {}
    fit_steps = {}

    # raw data
    own_heart_rate = None
    own_points = None
    own_steps = None
    if "heart_rate" in run_data:
        own_heart_rate = run_data["heart_rate"]  # bpm key-value
    if "user_steps_list_perm" in run_data:
        own_steps = run_data["user_steps_list_perm"]  # step key-value
    if "points" in run_data:
        own_points = run_data["points"]  # track points

    # get single bpm
    if own_heart_rate is not None:
        for single_time, single_bpm in own_heart_rate.items():
            single_time = adjust_timestamp_to_utc(single_time, str(get_localzone()))
            fit_hrs[single_time] = single_bpm

    # get single step
    if own_steps is not None:
        for own_step in own_steps:
            [single_time, single_step] = own_step[0:2]
            # firstly, convert 2025-09-16 20:08:00 to 2025-09-16T20:08:00
            single_time = single_time.replace(" ", "T")
            # move to UTC
            utc = adjust_time_to_utc(to_date(single_time), str(get_localzone()))
            time_stamp = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            # to time array
            time_array = time.strptime(time_stamp, "%Y-%m-%dT%H:%M:%SZ")
            # to unix timestamp
            unix_time = int(time.mktime(time_array))
            fit_steps[unix_time] = int(single_step)

    # get single track point
    if len(own_points) > 0:
        for point in own_points:
            time_stamp = point.get("time_stamp")
            latitude = point.get("latitude")
            longitude = point.get("longitude")
            elevation = point.get("elevation")

            # move to UTC
            utc = adjust_time_to_utc(to_date(time_stamp), str(get_localzone()))
            time_stamp = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            # to time array
            time_array = time.strptime(time_stamp, "%Y-%m-%dT%H:%M:%SZ")
            # to unix timestamp
            unix_time = int(time.mktime(time_array))

            # get heart rate at unix_time
            hr = fit_hrs.get(unix_time, None)

            # get steps per minute at unix_time
            step = fit_steps.get(unix_time, None)

            fit_list.append((unix_time, hr, step, latitude, longitude, elevation))
    elif fit_hrs:
        # not trackpoints but heart rates
        print(
            "No track points, but heart rates, might have steps " + str(run_data["id"])
        )
        for unix_time, hr in fit_hrs.items():
            # get heart rate at unix_time
            step = fit_steps.get(unix_time, None)
            fit_list.append((unix_time, hr, step, None, None, None))
    elif fit_steps:
        # not trackpoints but steps
        print("No track points, only steps " + str(run_data["id"]))
        for unix_time, step in fit_steps.items():
            fit_list.append((unix_time, None, step, None, None, None))

    if fit_list:
        # track points
        fit_array = np.array(fit_list, dtype=FitType)
        # order array
        fit_array = np.sort(fit_array, order="time")
        # write to TCX file
        tcx_output(fit_array, run_data)
    else:
        print("No data in " + str(run_data["id"]))


class CodoonAuth:
    def __init__(self, refresh_token=None):
        self.params = {}
        self.refresh_token = refresh_token
        self.token = ""

        if refresh_token:
            session = requests.Session()
            session.headers.update(device_info_headers())
            query = f"client_id={client_id}&grant_type=refresh_token&refresh_token={refresh_token}&scope=user%2Csports"
            r = session.post(
                f"{base_url}/token?" + query,
                data=query,
                auth=self.reload(query),
            )
            if not r.ok:
                print(r.json())
                raise Exception("refresh_token expired")

            self.token = r.json()["access_token"]

    def reload(self, params={}, token=""):
        self.params = params
        if token:
            self.token = token
        return self

    @classmethod
    def __get_signature(cls, token="", path="", body=None, timestamp=""):
        arr = path.split("?")
        path = arr[0]
        query = arr[1] if len(arr) > 1 else ""
        body_str = body if body else ""
        if body is not None and not isinstance(body, str):
            body_str = json.dumps(body)
        if query != "":
            query = urllib.parse.unquote(query)

        pre_string = f"Authorization={token}&Davinci={davinci}&Did={did}&Timestamp={str(timestamp)}|path={path}|body={body_str}|{query}"
        return make_signature(pre_string)

    def __call__(self, r):
        params = self.params
        body = params
        if not isinstance(self.params, str):
            params = self.params.copy()
            body = json.dumps(params)

        sign = ""
        if r.method == "GET":
            timestamp = 0
            r.headers["authorization"] = "Basic " + basic_auth
            r.headers["timestamp"] = timestamp
            sign = self.__get_signature(
                r.headers["authorization"], r.path_url, timestamp=timestamp
            )
        elif r.method == "POST":
            timestamp = int(time.time())
            r.headers["timestamp"] = timestamp
            if "refresh_token" in params:
                r.headers["authorization"] = "Basic " + basic_auth
                r.headers["content-type"] = (
                    "application/x-www-form-urlencode; charset=utf-8"
                )
            else:
                r.headers["authorization"] = "Bearer " + self.token
                r.headers["content-type"] = "application/json; charset=utf-8"
            sign = self.__get_signature(
                r.headers["authorization"], r.path_url, body=body, timestamp=timestamp
            )
            r.body = body

        r.headers["signature"] = sign
        return r


class Codoon:
    def __init__(self, mobile="", password="", refresh_token=None, user_id=""):
        self.mobile = mobile
        self.password = password
        self.refresh_token = refresh_token
        self.user_id = user_id

        self.session = requests.Session()

        self.session.headers.update(device_info_headers())

        self.auth = CodoonAuth(self.refresh_token)
        self.auth.token = self.auth.token

    @classmethod
    def from_auth_token(cls, refresh_token, user_id):
        return cls(refresh_token=refresh_token, user_id=user_id)

    def login_by_phone(self):
        params = {
            "client_id": client_id,
            "email": self.mobile,
            "grant_type": "password",
            "password": self.password,
            "scope": "user",
        }
        r = self.session.get(
            f"{base_url}/token",
            params=params,
            auth=self.auth.reload(params),
        )
        login_data = r.json()
        if login_data.__contains__("status") and login_data["status"] == "Error":
            raise Exception(login_data["description"])
        self.refresh_token = login_data["refresh_token"]
        self.token = login_data["access_token"]
        self.user_id = login_data["user_id"]
        self.auth.reload(token=self.token)
        print(
            f"your refresh_token and user_id are {str(self.refresh_token)} {str(self.user_id)}"
        )

    def get_runs_records(self, page=1):
        payload = {"limit": 500, "page": page, "user_id": self.user_id}
        r = self.session.post(
            f"{base_url}/api/get_old_route_log",
            data=payload,
            auth=self.auth.reload(payload),
        )
        if not r.ok:
            print(r.json())
            raise Exception("get runs records error")

        runs = r.json()["data"]["log_list"]
        if IS_ONLY_RUN:
            runs = [run for run in runs if run["sports_type"] == 1]
        print(f"{len(runs)} runs to parse")
        if r.json()["data"]["has_more"]:
            return runs + self.get_runs_records(page + 1)
        return runs

    @staticmethod
    def parse_latlng(points):
        if not points:
            return []
        try:
            points = [[p["latitude"], p["longitude"]] for p in points]
        except Exception as e:
            print(str(e))
            points = []
        return points

    def parse_points_to_gpx(self, run_points_data):
        # TODO for now kind of same as `keep` maybe refactor later
        points_dict_list = []
        for point in run_points_data[:-1]:
            points_dict = {
                "latitude": point["latitude"],
                "longitude": point["longitude"],
                "elevation": point["elevation"],
                "time": adjust_time_to_utc(
                    to_date(point["time_stamp"]), BASE_TIMEZONE
                ).replace(tzinfo=timezone.utc),
            }
            points_dict_list.append(points_dict)
        gpx = gpxpy.gpx.GPX()
        gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = "gpx from codoon"
        gpx_track.type = "Run"
        gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        for p in points_dict_list:
            point = gpxpy.gpx.GPXTrackPoint(**p)
            gpx_segment.points.append(point)
        return gpx

    def get_single_run_record(self, route_id):
        print(f"Get single run for codoon id {route_id}")
        payload = {
            "route_id": route_id,
        }
        r = self.session.post(
            f"{base_url}/api/get_single_log",
            data=payload,
            auth=self.auth.reload(payload),
        )
        if not r.ok:
            print(r)
            raise Exception("get runs records error")
        data = r.json()
        return data

    @staticmethod
    def _gt(dt_str):
        dt, _, _ = dt_str.partition(".")
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")

    def parse_raw_data_to_namedtuple(
        self, run_data, old_gpx_ids, with_gpx=False, with_tcx=False
    ):
        run_data = run_data["data"]
        log_id = run_data["id"]

        if with_tcx:
            tcx_job(run_data)  # TCX part

        start_time = run_data.get("start_time")
        if not start_time:
            return
        end_time = run_data["end_time"]
        run_points_data = run_data["points"] if "points" in run_data else None

        latlng_data = self.parse_latlng(run_points_data)
        if TRANS_GCJ02_TO_WGS84:
            trans_end_date = time.strptime(TRANS_END_DATE, "%Y-%m-%d")
            start_date = time.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
            if trans_end_date > start_date:
                latlng_data = [
                    list(eviltransform.gcj2wgs(p[0], p[1])) for p in latlng_data
                ]
            if run_points_data:
                for i, p in enumerate(run_points_data):
                    p["latitude"] = latlng_data[i][0]
                    p["longitude"] = latlng_data[i][1]

        elevation_gain = None
        if run_points_data:
            gpx_data = self.parse_points_to_gpx(run_points_data)
            elevation_gain = gpx_data.get_uphill_downhill().uphill
            if with_gpx:
                # pass the track no points
                if str(log_id) not in old_gpx_ids:
                    download_codoon_gpx(gpx_data.to_xml(), str(log_id))
        heart_rate_dict = run_data.get("heart_rate")
        heart_rate = None
        if heart_rate_dict:
            heart_rate = sum(heart_rate_dict.values()) / len(heart_rate_dict)

        polyline_str = polyline.encode(latlng_data) if latlng_data else ""
        start_latlng = start_point(*latlng_data[0]) if latlng_data else None
        start_date = self._gt(start_time)
        end_date = self._gt(end_time)
        location_country = None
        sport_type = run_data["sports_type"]
        # only support run now, if you want all type comments these two lines
        if IS_ONLY_RUN and sport_type != 1:
            return
        cast_type = TYPE_DICT[sport_type] if sport_type in TYPE_DICT else sport_type
        if not run_data["total_time"]:
            print(f"ID {log_id} has no total time just ignore please check")
            return
        d = {
            "id": log_id,
            "name": str(cast_type) + " from codoon",
            "type": cast_type,
            "subtype": cast_type,
            "start_date": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
            "end": datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S"),
            "start_date_local": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
            "end_local": datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S"),
            "length": run_data["total_length"],
            "average_heartrate": heart_rate,
            "map": run_map(polyline_str),
            "start_latlng": start_latlng,
            "distance": run_data["total_length"],
            "moving_time": timedelta(seconds=run_data["total_time"]),
            "elapsed_time": timedelta(
                seconds=int((end_date.timestamp() - start_date.timestamp()))
            ),
            "average_speed": run_data["total_length"] / run_data["total_time"],
            "elevation_gain": elevation_gain,
            "location_country": location_country,
            "source": "Codoon",
        }
        return namedtuple("x", d.keys())(*d.values())

    def get_old_tracks(self, old_ids, with_gpx=False, with_tcx=False):
        run_records = self.get_runs_records()

        old_gpx_ids = os.listdir(GPX_FOLDER)
        old_gpx_ids = [i.split(".")[0] for i in old_gpx_ids if not i.startswith(".")]
        new_run_routes = [i for i in run_records if str(i["log_id"]) not in old_ids]
        tracks = []
        for i in new_run_routes:
            run_data = self.get_single_run_record(i["route_id"])
            run_data["data"]["id"] = i["log_id"]
            track = self.parse_raw_data_to_namedtuple(
                run_data, old_gpx_ids, with_gpx, with_tcx
            )
            if track:
                tracks.append(track)
        return tracks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mobile_or_token", help="codoon phone number or refresh token")
    parser.add_argument("password_or_user_id", help="codoon password or user_id")
    parser.add_argument(
        "--with-gpx",
        dest="with_gpx",
        action="store_true",
        help="get all keep data to gpx and download",
    )
    parser.add_argument(
        "--with-tcx",
        dest="with_tcx",
        action="store_true",
        help="get all keep data to tcx and download",
    )
    parser.add_argument(
        "--from-auth-token",
        dest="from_refresh_token",
        action="store_true",
        help="from authorization token for download data",
    )
    options = parser.parse_args()
    if options.from_refresh_token:
        j = Codoon.from_auth_token(
            refresh_token=str(options.mobile_or_token),
            user_id=str(options.password_or_user_id),
        )
    else:
        j = Codoon(
            mobile=str(options.mobile_or_token),
            password=str(options.password_or_user_id),
        )
        j.login_by_phone()

    generator = Generator(SQL_FILE)
    old_tracks_ids = generator.get_old_tracks_ids()
    tracks = j.get_old_tracks(old_tracks_ids, options.with_gpx, options.with_tcx)

    generator.sync_from_app(tracks)
    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f, indent=0)
