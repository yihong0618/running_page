#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import time
from collections import namedtuple
from datetime import datetime, timedelta

import gpxpy
import polyline
import requests
import hashlib
import hmac
import base64
import urllib.parse

from config import GPX_FOLDER, JSON_FILE, SQL_FILE
from generator import Generator

start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")

base_url = "https://api.codoon.com"
davinci = "0"
did = "24-00000000-03e1-7dd7-0033-c5870033c588"
user_agent = "CodoonSport(8.9.0 1170;Android 7;Sony XZ1)"
basic_auth = 'MDk5Y2NlMjhjMDVmNmMzOWFkNWUwNGU1MWVkNjA3MDQ6YzM5ZDNmYmVhMWU4NWJlY2VlNDFjMTk5N2FjZjBlMzY='
client_id = '099cce28c05f6c39ad5e04e51ed60704'


TYPE_DICT = {
    0: "Hike",
    1: "Run",
    2: "Ride",
}


# decrypt from libencrypt.so Java_com_codoon_jni_JNIUtils_encryptHttpSignature
# sha1 -> base64
def make_signature(message):
    key = bytes("ecc140ad6e1e12f7d972af04add2c7ee", 'UTF-8')
    message = bytes(message, 'UTF-8')
    digester = hmac.new(key, message, hashlib.sha1)
    signature1 = digester.digest()
    signature2 = base64.b64encode(signature1)
    return str(signature2, 'UTF-8')


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
    except:
        print(f"wrong id {log_id}")
        pass


class CodoonAuth:
    def __init__(self, refresh_token=None):
        self.params = {}
        self.refresh_token = refresh_token
        self.token = ""

        if refresh_token:
            session = requests.Session()
            session.headers.update(device_info_headers())
            query = "client_id={client_id}&grant_type=refresh_token&refresh_token={refresh_token}&scope=user%2Csports".format(
                client_id=client_id,
                refresh_token=refresh_token,
            )
            r = session.post(
                f"{base_url}/token?"+query,
                data=query,
                auth=self.reload(query),
            )
            if not r.ok:
                print(r)
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
        body_str = body if body else ''
        if body is not None and not isinstance(body, str):
            body_str = json.dumps(body)
        if query != "":
            query = urllib.parse.unquote(query)

        pre_string = "Authorization={token}&Davinci={davinci}&Did={did}&Timestamp={timestamp}|path={path}|body={body}|{query}".format(
            token=token,
            davinci=davinci,
            did=did,
            path=path,
            body=body_str,
            query=query,
            timestamp=str(timestamp),
        )
        # print("pre_string " + pre_string)
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
            sign = self.__get_signature(r.headers["authorization"], r.path_url, timestamp=timestamp)
        elif r.method == "POST":
            timestamp = int(time.time())
            r.headers["timestamp"] = timestamp
            if "refresh_token" in params:
                r.headers["authorization"] = "Basic " + basic_auth
                r.headers["content-type"] = 'application/x-www-form-urlencode; charset=utf-8'
            else:
                r.headers["authorization"] = "Bearer " + self.token
                r.headers["content-type"] = 'application/json; charset=utf-8'
            sign = self.__get_signature(r.headers["authorization"], r.path_url, body=body, timestamp=timestamp)
            r.body = body

        # print('sign= ', sign)
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
        print(r.json())
        login_data = r.json()
        self.refresh_token = login_data["refresh_token"]
        self.token = login_data["access_token"]
        self.user_id = login_data["user_id"]
        self.auth.reload(token=self.token)
        print(f"your refresh_token and user_id are {str(self.refresh_token)} {str(self.user_id)}")

    def get_runs_records(self, page=1):
        payload = {
            "limit": 500,
            "page": page,
            "user_id": self.user_id
        }
        r = self.session.post(
            f"{base_url}/api/get_old_route_log",
            data=payload,
            auth=self.auth.reload(payload),
        )
        if not r.ok:
            print(r)
            print(r.json())
            raise Exception("get runs records error")

        # print(r.json())
        runs = r.json()["data"]["log_list"]
        if r.json()["data"]["has_more"] == "true":
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

    @staticmethod
    def parse_points_to_gpx(run_points_data, start_time, end_time, interval=5):
        # TODO for now kind of same as `keep` maybe refactor later
        points_dict_list = []
        i = 0
        start_timestamp = datetime.fromisoformat(start_time).timestamp()
        end_timestamp = datetime.fromisoformat(end_time).timestamp()
        for point in run_points_data[:-1]:
            points_dict = {
                "latitude": point["latitude"],
                "longitude": point["longitude"],
                "elevation": point["elevation"],
                "time": datetime.utcfromtimestamp(start_timestamp + interval * i),
            }
            i += 1
            points_dict_list.append(points_dict)
        points_dict_list.append(
            {
                "latitude": run_points_data[-1]["latitude"],
                "longitude": run_points_data[-1]["longitude"],
                "elevation": run_points_data[-1]["elevation"],
                "time": datetime.utcfromtimestamp(end_timestamp),
            }
        )
        gpx = gpxpy.gpx.GPX()
        gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = "gpx from codoon"
        gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        for p in points_dict_list:
            point = gpxpy.gpx.GPXTrackPoint(**p)
            gpx_segment.points.append(point)

        return gpx.to_xml()

    def get_single_run_record(self, route_id):
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
            print(r.json())
            raise Exception("get runs records error")
        data = r.json()
        # print(json.dumps(data))
        return data

    def parse_raw_data_to_namedtuple(self, run_data, old_gpx_ids, with_gpx=False):
        run_data = run_data["data"]
        # print(run_data)
        log_id = run_data["id"]

        start_time = run_data["start_time"]
        end_time = run_data["end_time"]
        run_points_data = run_data["points"] if "points" in run_data else None

        latlng_data = self.parse_latlng(run_points_data)
        if with_gpx:
            # pass the track no points
            if str(log_id) not in old_gpx_ids and run_points_data:
                gpx_data = self.parse_points_to_gpx(
                    run_points_data, start_time, end_time
                )
                download_codoon_gpx(gpx_data, str(log_id))
        heart_rate = None

        polyline_str = polyline.encode(latlng_data) if latlng_data else ""
        start_latlng = start_point(*latlng_data[0]) if latlng_data else None
        start_date = datetime.fromisoformat(start_time)
        end_date = datetime.fromisoformat(end_time)
        location_country = None
        sport_type = run_data["sports_type"]
        cast_type = TYPE_DICT[sport_type] if sport_type in TYPE_DICT else sport_type
        d = {
            "id": log_id,
            "name": str(cast_type) + " from codoon",
            "type": cast_type,
            "start_date": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
            "end": datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S"),
            "start_date_local": datetime.strftime(
                start_date, "%Y-%m-%d %H:%M:%S"
            ),
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
            "location_country": location_country,
            "source": "Codoon",
        }
        return namedtuple("x", d.keys())(*d.values())

    def get_old_tracks(self, old_ids, with_gpx=False):
        run_records = self.get_runs_records()

        old_gpx_ids = os.listdir(GPX_FOLDER)
        old_gpx_ids = [i.split(".")[0] for i in old_gpx_ids if not i.startswith(".")]
        new_run_routes = [i for i in run_records if str(i["log_id"]) not in old_ids]
        tracks = []
        for i in new_run_routes:
            run_data = self.get_single_run_record(i["route_id"])
            run_data["data"]["id"] = i["log_id"]
            track = self.parse_raw_data_to_namedtuple(run_data, old_gpx_ids, with_gpx)
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
    tracks = j.get_old_tracks(old_tracks_ids, options.with_gpx)

    generator.sync_from_app(tracks)
    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f, indent=2)
