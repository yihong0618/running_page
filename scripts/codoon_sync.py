# some code from https://github.com/iascchen/VisHealth great thanks
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import time
from collections import namedtuple
from datetime import datetime, timedelta
from urllib.parse import quote

import gpxpy
import polyline
import pytz
import requests
import hashlib
import hmac
import base64

from config import GPX_FOLDER, JSON_FILE, SQL_FILE
from generator import Generator

start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")

davinci = "0"
did = "24-00000000-03e1-7dd7-0033-c5870033c588"
key = bytes("ecc140ad6e1e12f7d972af04add2c7ee", 'UTF-8')
user_agent = "CodoonSport(8.9.0 1170;Android 7;Sony XZ1)"


# now its the same like keep_sync but we want the code can run in single file
# by copy so maybe refactor later
def adjust_time(time, tz_name):
    tc_offset = datetime.now(pytz.timezone(tz_name)).utcoffset()
    return time + tc_offset

# decrypt from libencrypt.so Java_com_codoon_jni_JNIUtils_encryptHttpSignature
def make_digest(message):
    message = bytes(message, 'UTF-8')

    digester = hmac.new(key, message, hashlib.sha1)
    signature1 = digester.digest()

    signature2 = base64.urlsafe_b64encode(signature1)

    return str(signature2, 'UTF-8')


def download_joyrun_gpx(gpx_data, joyrun_id):
    try:
        print(f"downloading joyrun_id {str(joyrun_id)} gpx")
        file_path = os.path.join(GPX_FOLDER, str(joyrun_id) + ".gpx")
        with open(file_path, "w") as fb:
            fb.write(gpx_data)
    except:
        print(f"wrong id {joyrun_id}")
        pass


class CodoonAuth:
    def __init__(self, token=""):
        self.params = {}
        self.token = token

    def reload(self, params={}, token=""):
        self.params = params
        if token:
            self.token = token
        return self

    @classmethod
    def __get_signature(cls, token="", path="", body="", query="", timestamp=""):
        pre_string = "Authorization=Bearer {token}&Davinci={davinci}&Did={did}&Timestamp={timestamp}|path={path}|body={body}|{query}".format(
            token=token,
            davinci=davinci,
            did=did,
            path=path,
            body=json.dumps(body),
            query=query,
            timestamp=str(timestamp),
        )
        print("pre_string " + pre_string)
        return make_digest(pre_string).replace('-', '+').replace('_', '/')


    def __call__(self, r):
        params = self.params.copy()
        timestamp = int(time.time())

        sign = self.__get_signature(self.token, r.path_url, self.params, timestamp=timestamp)

        r.headers["timestamp"] = timestamp
        r.headers["authorization"] = "Bearer " + self.token
        r.headers["signature"] = sign
        if r.method == "GET":
            r.prepare_url(
                r.url, params={"signature": sign, "timestamp": params["timestamp"]}
            )
        elif r.method == "POST":
            r.body = json.dumps(params)
            r.headers["content-type"] = 'application/json; charset=utf-8'
        return r


class Codoon:

    base_url = "https://api.codoon.com"

    def __init__(self, mobile="", password="", token="", userId=""):
        self.mobile = mobile
        self.password = password
        self.token = token
        self.userId = userId

        self.session = requests.Session()

        self.session.headers.update(self.base_headers)
        self.session.headers.update(self.device_info_headers)

        self.auth = CodoonAuth(self.token)

    @classmethod
    def from_auth_token(cls, token, userId):
        return cls(token=token, userId=userId)

    @property
    def base_headers(self):
        return {
            "accept-encoding": "gzip",
            # "host": "api.codoon.com",
            # "cache-control": "max-age=0",
        }

    @property
    def device_info_headers(self):
        return {
            "user-agent": user_agent,
            "did": did,
            "davinci": davinci,
        }

    def login_by_phone(self):
        params = {
            "phoneNumber": self.user_name,
            "identifyingCode": self.identifying_code,
        }
        r = self.session.get(
            f"{self.base_url}//user/login/phonecode",
            params=params,
            auth=self.auth.reload(params),
        )
        login_data = r.json()
        # self.sid = login_data["data"]["sid"]
        # self.uid = login_data["data"]["user"]["uid"]
        # print(f"your uid and sid are {str(self.uid)} {str(self.sid)}")

    def get_runs_records_ids(self, userId="", page=1):
        payload = {
            # "limit": 500,
            # "page": page,
            "log_id": 205420830,
            "user_id": userId
        }
        r = self.session.post(
            # f"{self.base_url}/api/get_old_route_log",
            f"{self.base_url}/api/get_new_route_log",
            data=payload,
            auth=self.auth.reload(payload),
        )
        print(r)
        print(r.headers)
        print("json: " + str(r.json()))
        if not r.ok:
            raise Exception("get runs records error")
        return [i["fid"] for i in r.json()["datas"]]

    @staticmethod
    def parse_content_to_ponits(content):
        if not content:
            return []
        try:
            # eval is bad but easy maybe change it later
            points = eval(content.replace("-", ","))
            points = [[p[0] / 1000000, p[1] / 1000000] for p in points]
        except Exception as e:
            print(str(e))
            points = []
        return points

    @staticmethod
    def parse_points_to_gpx(run_points_data, start_time, end_time, interval=5):
        # TODO for now kind of same as `keep` maybe refactor later
        points_dict_list = []
        i = 0
        for point in run_points_data[:-1]:
            points_dict = {
                "latitude": point[0],
                "longitude": point[1],
                "time": datetime.utcfromtimestamp(start_time + interval * i),
            }
            i += 1
            points_dict_list.append(points_dict)
        points_dict_list.append(
            {
                "latitude": run_points_data[-1][0],
                "longitude": run_points_data[-1][1],
                "time": datetime.utcfromtimestamp(end_time),
            }
        )
        gpx = gpxpy.gpx.GPX()
        gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = "gpx from keep"
        gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        for p in points_dict_list:
            point = gpxpy.gpx.GPXTrackPoint(**p)
            gpx_segment.points.append(point)

        return gpx.to_xml()

    def get_single_run_record(self, fid):
        payload = {
            "fid": fid,
            "wgs": 1,
        }
        r = self.session.post(
            f"{self.base_url}/Run/GetInfo.aspx",
            data=payload,
            auth=self.auth.reload(payload),
        )
        data = r.json()
        return data

    def parse_raw_data_to_nametuple(self, run_data, old_gpx_ids, with_gpx=False):
        run_data = run_data["runrecord"]
        joyrun_id = run_data["fid"]

        start_time = run_data["starttime"]
        end_time = run_data["endtime"]
        run_points_data = self.parse_content_to_ponits(run_data["content"])
        if with_gpx:
            # pass the track no points
            if run_points_data:
                gpx_data = self.parse_points_to_gpx(
                    run_points_data, start_time, end_time
                )
                download_joyrun_gpx(gpx_data, str(joyrun_id))
        heart_rate_list = eval(run_data["heartrate"]) if run_data["heartrate"] else None
        heart_rate = None
        if heart_rate_list:
            heart_rate = int(sum(heart_rate_list) / len(heart_rate_list))
            # fix #66
            if heart_rate < 0:
                heart_rate = None

        polyline_str = polyline.encode(run_points_data) if run_points_data else ""
        start_latlng = start_point(*run_points_data[0]) if run_points_data else None
        start_date = datetime.utcfromtimestamp(start_time)
        start_date_local = adjust_time(start_date, "Asia/Shanghai")
        end = datetime.utcfromtimestamp(end_time)
        # only for China now
        end_local = adjust_time(end, "Asia/Shanghai")
        location_country = None
        # joyrun location is kind of fucking strage, so I decide not use it, if you want use it, uncomment this two lines
        # if run_data["city"] or run_data["province"]:
        #     location_country = str(run_data["city"]) + " " + str(run_data["province"])
        d = {
            "id": int(joyrun_id),
            "name": "run from joyrun",
            # future to support others workout now only for run
            "type": "Run",
            "start_date": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
            "end": datetime.strftime(end, "%Y-%m-%d %H:%M:%S"),
            "start_date_local": datetime.strftime(
                start_date_local, "%Y-%m-%d %H:%M:%S"
            ),
            "end_local": datetime.strftime(end_local, "%Y-%m-%d %H:%M:%S"),
            "length": run_data["meter"],
            "average_heartrate": heart_rate,
            "map": run_map(polyline_str),
            "start_latlng": start_latlng,
            "distance": run_data["meter"],
            "moving_time": timedelta(seconds=run_data["second"]),
            "elapsed_time": timedelta(
                seconds=int((run_data["endtime"] - run_data["starttime"]))
            ),
            "average_speed": run_data["meter"] / run_data["second"],
            "location_country": location_country,
            "source": "Joyrun",
        }
        return namedtuple("x", d.keys())(*d.values())

    def get_old_tracks(self, old_tracks_ids, with_gpx=False):
        run_ids = self.get_runs_records_ids(self.userId, 1)
        old_tracks_ids = [int(i) for i in old_tracks_ids if i.isdigit()]

        old_gpx_ids = os.listdir(GPX_FOLDER)
        old_gpx_ids = [i.split(".")[0] for i in old_gpx_ids if not i.startswith(".")]
        new_run_ids = list(set(run_ids) - set(old_tracks_ids))
        tracks = []
        for i in new_run_ids:
            run_data = self.get_single_run_record(i)
            track = self.parse_raw_data_to_nametuple(run_data, old_gpx_ids, with_gpx)
            tracks.append(track)
        return tracks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mobile_or_token", help="codoon phone number or token")
    parser.add_argument("password_or_userId", help="codoon password or userId")
    parser.add_argument(
        "--with-gpx",
        dest="with_gpx",
        action="store_true",
        help="get all keep data to gpx and download",
    )
    parser.add_argument(
        "--from-auth-token",
        dest="from_auth_token",
        action="store_true",
        help="from authorization token for download data",
    )
    options = parser.parse_args()
    if options.from_auth_token:
        j = Codoon.from_auth_token(
            token=str(options.mobile_or_token),
            userId=str(options.password_or_userId),
        )
    else:
        j = Codoon(
            mobile=str(options.mobile_or_token),
            password=str(options.password_or_userId),
        )
        j.login_by_phone()

    generator = Generator(SQL_FILE)
    old_tracks_ids = generator.get_old_tracks_ids()
    tracks = j.get_old_tracks(old_tracks_ids, options.with_gpx)
    # generator.sync_from_app(tracks)
    # activities_list = generator.load()
    # with open(JSON_FILE, "w") as f:
    #     json.dump(activities_list, f)