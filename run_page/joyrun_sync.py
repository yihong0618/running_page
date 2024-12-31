# some code from https://github.com/fieryd/PKURunningHelper great thanks
import argparse
import json
import os
import subprocess
import sys
import time
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from hashlib import md5
from urllib.parse import quote

import gpxpy
import polyline
import requests
from config import BASE_TIMEZONE, GPX_FOLDER, JSON_FILE, SQL_FILE, run_map, start_point
from generator import Generator

from utils import adjust_time

get_md5_data = lambda data: md5(str(data).encode("utf-8")).hexdigest().upper()


def download_joyrun_gpx(gpx_data, joyrun_id):
    try:
        print(f"downloading joyrun_id {str(joyrun_id)} gpx")
        file_path = os.path.join(GPX_FOLDER, str(joyrun_id) + ".gpx")
        with open(file_path, "w") as fb:
            fb.write(gpx_data)
    except:
        print(f"wrong id {joyrun_id}")
        pass


class JoyrunAuth:
    def __init__(self, uid=0, sid=""):
        self.params = {}
        self.uid = uid
        self.sid = sid

    def reload(self, params={}, uid=0, sid=""):
        self.params = params
        if uid and sid:
            self.uid = uid
            self.sid = sid
        return self

    @classmethod
    def __get_signature(cls, params, uid, sid, salt):
        if not uid:  # uid == 0 or ''
            uid = sid = ""
        pre_string = "{params_string}{salt}{uid}{sid}".format(
            params_string="".join(
                "".join((k, str(v))) for k, v in sorted(params.items())
            ),
            salt=salt,
            uid=str(uid),
            sid=sid,
        )
        return get_md5_data(pre_string)

    @classmethod
    def get_signature_v1(cls, params, uid=0, sid=""):
        return cls.__get_signature(params, uid, sid, "1fd6e28fd158406995f77727b35bf20a")

    @classmethod
    def get_signature_v2(cls, params, uid=0, sid=""):
        return cls.__get_signature(params, uid, sid, "0C077B1E70F5FDDE6F497C1315687F9C")

    def __call__(self, r):
        params = self.params.copy()
        params["timestamp"] = int(time.time())

        signV1 = self.get_signature_v1(params, self.uid, self.sid)
        signV2 = self.get_signature_v2(params, self.uid, self.sid)

        r.headers["_sign"] = signV2

        if r.method == "GET":
            r.prepare_url(
                r.url, params={"signature": signV1, "timestamp": params["timestamp"]}
            )
        elif r.method == "POST":
            params["signature"] = signV1
            r.prepare_body(data=params, files=None)
        return r


class Joyrun:
    base_url = "https://api.thejoyrun.com"

    def __init__(self, user_name="", identifying_code="", uid=0, sid=""):
        self.user_name = user_name
        # from sms
        self.identifying_code = identifying_code
        self.uid = uid
        self.sid = sid

        self.session = requests.Session()

        self.session.headers.update(self.base_headers)
        self.session.headers.update(self.device_info_headers)

        self.auth = JoyrunAuth(self.uid, self.sid)
        if self.uid and self.sid:
            self.__update_loginInfo()

    @classmethod
    def from_uid_sid(cls, uid, sid):
        return cls(uid=uid, sid=sid)

    @property
    def base_headers(self):
        return {
            "Accept-Language": "en_US",
            "User-Agent": "okhttp/3.10.0",
            "Host": "api.thejoyrun.com",
            "Connection": "Keep-Alive",
        }

    @property
    def device_info_headers(self):
        return {
            "MODELTYPE": "Xiaomi MI 5",
            "SYSVERSION": "8.0.0",
            "APPVERSION": "4.2.0",
        }

    def __update_loginInfo(self):
        self.auth.reload(uid=self.uid, sid=self.sid)
        loginCookie = "sid=%s&uid=%s" % (self.sid, self.uid)
        self.session.headers.update({"ypcookie": loginCookie})
        self.session.cookies.clear()
        self.session.cookies.set("ypcookie", quote(loginCookie).lower())
        self.session.headers.update(
            self.device_info_headers
        )  # 更新设备信息中的 uid 字段

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
        if login_data["ret"] != "0":
            raise Exception(f'{login_data["ret"]}: {login_data["msg"]}')
        self.sid = login_data["data"]["sid"]
        self.uid = login_data["data"]["user"]["uid"]
        print(f"your uid and sid are {str(self.uid)} {str(self.sid)}")
        self.__update_loginInfo()

    def get_runs_records_ids(self):
        payload = {
            "year": 0,  # as of the "year". when set to 2023, it means fetch records during currentYear ~ 2023. set to 0 means fetch all.
        }
        r = self.session.post(
            f"{self.base_url}/userRunList.aspx",
            data=payload,
            auth=self.auth.reload(payload),
        )
        if not r.ok:
            raise Exception("get runs records error")
        return [i["fid"] for i in r.json()["datas"]]

    @staticmethod
    def parse_content_to_ponits(content):
        if not content:
            return []
        try:
            # eval is bad but easy maybe change it later
            # TODO fix this
            # just an easy way to fix joyrun issue, need to refactor this shit
            # -[34132812,-118126177]- contains `-` so I just fix it by replace
            try:
                points = eval(content.replace("]-[", "],["))
            except Exception as e:
                print(str(e))
                print(f"Points: {str(points)} can not eval")
            points = [[p[0] / 1000000, p[1] / 1000000] for p in points]
        except Exception as e:
            print(str(e))
            points = []
        return points

    @staticmethod
    def parse_points_to_gpx(
        run_points_data, start_time, end_time, pause_list, interval=5
    ):
        """
        parse run_data content to gpx object
        TODO for now kind of same as `keep` maybe refactor later

        :param run_points_data: [[latitude, longitude],...]
        :param pause_list:      [[interval_index, pause_seconds],...]
        :param interval:        time interval between each point, in seconds
        """

        # format data
        segment_list = []
        points_dict_list = []
        current_time = start_time

        for index, point in enumerate(run_points_data[:-1]):
            points_dict = {
                "latitude": point[0],
                "longitude": point[1],
                "time": datetime.fromtimestamp(current_time, tz=timezone.utc),
            }
            points_dict_list.append(points_dict)

            current_time += interval
            if pause_list and int(pause_list[0][0]) - 1 == index:
                segment_list.append(points_dict_list[:])
                points_dict_list.clear()
                current_time += int(pause_list[0][1])
                pause_list.pop(0)

        points_dict_list.append(
            {
                "latitude": run_points_data[-1][0],
                "longitude": run_points_data[-1][1],
                "time": datetime.fromtimestamp(end_time, tz=timezone.utc),
            }
        )
        segment_list.append(points_dict_list)

        # gpx part
        gpx = gpxpy.gpx.GPX()
        gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = "gpx from joyrun"
        gpx.tracks.append(gpx_track)

        # add segment list to our GPX track:
        for point_list in segment_list:
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)
            for p in point_list:
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
        pause_list = run_data["pause"]
        run_points_data = self.parse_content_to_ponits(run_data["content"])
        if with_gpx:
            # pass the track no points
            if run_points_data:
                gpx_data = self.parse_points_to_gpx(
                    run_points_data, start_time, end_time, pause_list
                )
                download_joyrun_gpx(gpx_data, str(joyrun_id))
        try:
            heart_rate_list = (
                eval(run_data["heartrate"]) if run_data["heartrate"] else None
            )
        except:
            print(f"Heart Rate: can not eval for {str(heart_rate_list)}")
        heart_rate = None
        if heart_rate_list:
            heart_rate = int(sum(heart_rate_list) / len(heart_rate_list))
            # fix #66
            if heart_rate < 0:
                heart_rate = None

        polyline_str = polyline.encode(run_points_data) if run_points_data else ""
        start_latlng = start_point(*run_points_data[0]) if run_points_data else None
        start_date = datetime.fromtimestamp(start_time, tz=timezone.utc)
        start_date_local = adjust_time(start_date, BASE_TIMEZONE)
        end = datetime.fromtimestamp(end_time, tz=timezone.utc)
        # only for China now
        end_local = adjust_time(end, BASE_TIMEZONE)
        location_country = None
        # joyrun location is kind of fucking strange, you can comments this two lines to make a better location
        if run_data["city"] or run_data["province"]:
            location_country = str(run_data["city"]) + ":" + str(run_data["province"])
        d = {
            "id": int(joyrun_id),
            "name": "run from joyrun",
            # future to support others workout now only for run
            "type": "Run",
            "subtype": "Run",
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
        }
        return namedtuple("x", d.keys())(*d.values())

    def get_all_joyrun_tracks(self, old_tracks_ids, with_gpx=False, threshold=10):
        run_ids = self.get_runs_records_ids()
        old_tracks_ids = [int(i) for i in old_tracks_ids if i.isdigit()]

        old_gpx_ids = os.listdir(GPX_FOLDER)
        old_gpx_ids = [i.split(".")[0] for i in old_gpx_ids if not i.startswith(".")]
        new_run_ids = list(set(run_ids) - set(old_tracks_ids))
        tracks = []
        seen_runs = {}  # Dictionary to keep track of unique runs with start time as key
        for i in new_run_ids:
            run_data = self.get_single_run_record(i)
            start_time = datetime.fromtimestamp(run_data["runrecord"]["starttime"])
            distance = run_data["runrecord"]["meter"]

            is_duplicate = False
            for seen_start in list(seen_runs.keys()):
                if abs((start_time - seen_start).total_seconds()) <= threshold:
                    if distance > seen_runs[seen_start]["distance"]:
                        seen_runs[seen_start] = {
                            "run_data": run_data,
                            "distance": distance,
                        }
                    is_duplicate = True
                    break
            if not is_duplicate:
                seen_runs[start_time] = {"run_data": run_data, "distance": distance}
            for run in seen_runs.values():
                track = self.parse_raw_data_to_nametuple(
                    run["run_data"], old_gpx_ids, with_gpx
                )
                tracks.append(track)
        return tracks


def _generate_svg_profile(athlete, min_grid_distance):
    # To generate svg for 'Total' in the left-up map
    if not athlete:
        # Skip to avoid override
        print("Skipping gen_svg. Fill your name with --athlete if you don't want skip")
        return
    print(
        f"Running scripts for [Make svg GitHub profile] with athlete={athlete} min_grid_distance={min_grid_distance}"
    )
    cmd_args_list = [
        [
            sys.executable,
            "run_page/gen_svg.py",
            "--from-db",
            "--title",
            f"{athlete} Running",
            "--type",
            "github",
            "--athlete",
            athlete,
            "--special-distance",
            "10",
            "--special-distance2",
            "20",
            "--special-color",
            "yellow",
            "--special-color2",
            "red",
            "--output",
            "assets/github.svg",
            "--use-localtime",
            "--min-distance",
            "0.5",
        ],
        [
            sys.executable,
            "run_page/gen_svg.py",
            "--from-db",
            "--title",
            f"Over {min_grid_distance} Running",
            "--type",
            "grid",
            "--athlete",
            athlete,
            "--special-distance",
            "20",
            "--special-distance2",
            "40",
            "--special-color",
            "yellow",
            "--special-color2",
            "red",
            "--output",
            "assets/grid.svg",
            "--use-localtime",
            "--min-distance",
            str(min_grid_distance),
        ],
        [
            sys.executable,
            "run_page/gen_svg.py",
            "--from-db",
            "--type",
            "circular",
            "--use-localtime",
        ],
    ]
    for cmd_args in cmd_args_list:
        subprocess.run(cmd_args, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phone_number_or_uid", help="joyrun phone number or uid")
    parser.add_argument(
        "identifying_code_or_sid", help="joyrun identifying_code from sms or sid"
    )
    parser.add_argument(
        "--athlete",
        dest="athlete",
        help="athlete, keep same with {env.ATHLETE}",
    )
    parser.add_argument(
        "--min_grid_distance",
        dest="min_grid_distance",
        help="min_grid_distance, keep same with {env.MIN_GRID_DISTANCE}",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--with-gpx",
        dest="with_gpx",
        action="store_true",
        help="get all joyrun data to gpx and download",
    )
    parser.add_argument(
        "--from-uid-sid",
        dest="from_uid_sid",
        action="store_true",
        help="from uid and sid for download datas",
    )
    parser.add_argument(
        "--threshold",
        dest="threshold",
        help="threshold in seconds to consider runs as duplicates",
        type=int,
        default=10,
    )
    options = parser.parse_args()
    if options.from_uid_sid:
        j = Joyrun.from_uid_sid(
            uid=str(options.phone_number_or_uid),
            sid=str(options.identifying_code_or_sid),
        )
    else:
        j = Joyrun(
            user_name=str(options.phone_number_or_uid),
            identifying_code=str(options.identifying_code_or_sid),
        )
        j.login_by_phone()

    generator = Generator(SQL_FILE)
    old_tracks_ids = generator.get_old_tracks_ids()
    tracks = j.get_all_joyrun_tracks(
        old_tracks_ids, options.with_gpx, options.threshold
    )
    generator.sync_from_app(tracks)
    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f)

    print("Data export to DB done")
    _generate_svg_profile(options.athlete, options.min_grid_distance)
