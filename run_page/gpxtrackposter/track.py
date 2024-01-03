"""Create and maintain info about a given activity track (corresponding to one GPX file)."""
# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
# 2019-now yihong0618 Florian Pigorsch & Contributors. All rights reserved.
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import datetime
import os
from collections import namedtuple

import gpxpy as mod_gpxpy
import lxml
import polyline
import s2sphere as s2
from fit_tool.fit_file import FitFile
from fit_tool.profile.messages.activity_message import ActivityMessage
from fit_tool.profile.messages.device_info_message import DeviceInfoMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.messages.software_message import SoftwareMessage
from fit_tool.profile.profile_type import Sport
from polyline_processor import filter_out
from rich import print
from tcxreader.tcxreader import TCXReader

from .exceptions import TrackLoadError
from .utils import parse_datetime_to_local

start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")

IGNORE_BEFORE_SAVING = os.getenv("IGNORE_BEFORE_SAVING", False)


class Track:
    def __init__(self):
        self.file_names = []
        self.polylines = []
        self.polyline_str = ""
        self.start_time = None
        self.end_time = None
        self.start_time_local = None
        self.end_time_local = None
        self.length = 0
        self.special = False
        self.average_heartrate = None
        self.moving_dict = {}
        self.run_id = 0
        self.start_latlng = []
        self.type = "Run"

    def load_gpx(self, file_name):
        """
        TODO refactor with load_tcx to one function
        """
        try:
            self.file_names = [os.path.basename(file_name)]
            # Handle empty gpx files
            # (for example, treadmill runs pulled via garmin-connect-export)
            if os.path.getsize(file_name) == 0:
                raise TrackLoadError("Empty GPX file")
            with open(file_name, "r", encoding="utf-8", errors="ignore") as file:
                self._load_gpx_data(mod_gpxpy.parse(file))
        except Exception as e:
            print(
                f"Something went wrong when loading GPX. for file {self.file_names[0]}, we just ignore this file and continue"
            )
            print(str(e))
            pass

    def load_tcx(self, file_name):
        try:
            self.file_names = [os.path.basename(file_name)]
            # Handle empty tcx files
            # (for example, treadmill runs pulled via garmin-connect-export)
            tcx = TCXReader()
            if os.path.getsize(file_name) == 0:
                raise TrackLoadError("Empty TCX file")
            self._load_tcx_data(tcx.read(file_name), file_name=file_name)
        except Exception as e:
            print(
                f"Something went wrong when loading TCX. for file {self.file_names[0]}, we just ignore this file and continue"
            )
            print(str(e))

    def load_fit(self, file_name):
        try:
            self.file_names = [os.path.basename(file_name)]
            # Handle empty fit files
            # (for example, treadmill runs pulled via garmin-connect-export)
            if os.path.getsize(file_name) == 0:
                raise TrackLoadError("Empty FIT file")

            fit = FitFile.from_file(file_name)
            self._load_fit_data(fit)
        except Exception as e:
            print(
                f"Something went wrong when loading FIT. for file {self.file_names[0]}, we just ignore this file and continue"
            )
            print(str(e))

    def load_from_db(self, activity):
        # use strava as file name
        self.file_names = [str(activity.run_id)]
        start_time = datetime.datetime.strptime(
            activity.start_date_local, "%Y-%m-%d %H:%M:%S"
        )
        self.start_time_local = start_time
        self.end_time = start_time + activity.elapsed_time
        self.length = float(activity.distance)
        if IGNORE_BEFORE_SAVING:
            summary_polyline = filter_out(activity.summary_polyline)
        else:
            summary_polyline = activity.summary_polyline
        polyline_data = polyline.decode(summary_polyline) if summary_polyline else []
        self.polylines = [[s2.LatLng.from_degrees(p[0], p[1]) for p in polyline_data]]
        self.run_id = activity.run_id

    def bbox(self):
        """Compute the smallest rectangle that contains the entire track (border box)."""
        bbox = s2.LatLngRect()
        for line in self.polylines:
            for latlng in line:
                bbox = bbox.union(s2.LatLngRect.from_point(latlng.normalized()))
        return bbox

    @staticmethod
    def __make_run_id(time_stamp):
        return int(datetime.datetime.timestamp(time_stamp) * 1000)

    def _load_tcx_data(self, tcx, file_name):
        self.length = float(tcx.distance)
        time_values = [i.time for i in tcx.trackpoints]
        if not time_values:
            raise TrackLoadError("Track is empty.")

        self.start_time, self.end_time = time_values[0], time_values[-1]
        moving_time = int(self.end_time.timestamp() - self.start_time.timestamp())
        self.run_id = self.__make_run_id(self.start_time)
        self.average_heartrate = tcx.hr_avg
        polyline_container = []
        position_values = [(i.latitude, i.longitude) for i in tcx.trackpoints]
        if not position_values and int(self.length) == 0:
            raise Exception(
                f"This {file_name} TCX file do not contain distance and position values we ignore it"
            )
        if position_values:
            line = [s2.LatLng.from_degrees(p[0], p[1]) for p in position_values]
            self.polylines.append(line)
            polyline_container.extend([[p[0], p[1]] for p in position_values])
            self.polyline_container = polyline_container
            self.start_time_local, self.end_time_local = parse_datetime_to_local(
                self.start_time, self.end_time, polyline_container[0]
            )
            # get start point
            try:
                self.start_latlng = start_point(*polyline_container[0])
            except:
                pass
            self.polyline_str = polyline.encode(polyline_container)
        self.moving_dict = {
            "distance": self.length,
            "moving_time": datetime.timedelta(seconds=moving_time),
            "elapsed_time": datetime.timedelta(
                seconds=moving_time
            ),  # FIXME for now make it same as moving time
            "average_speed": self.length / moving_time if moving_time else 0,
        }

    def _load_gpx_data(self, gpx):
        self.start_time, self.end_time = gpx.get_time_bounds()
        # use timestamp as id
        self.run_id = self.__make_run_id(self.start_time)
        if self.start_time is None:
            raise TrackLoadError("Track has no start time.")
        if self.end_time is None:
            raise TrackLoadError("Track has no end time.")
        self.length = gpx.length_2d()
        if self.length == 0:
            raise TrackLoadError("Track is empty.")
        gpx.simplify()
        polyline_container = []
        heart_rate_list = []
        for t in gpx.tracks:
            for s in t.segments:
                try:
                    extensions = [
                        {
                            lxml.etree.QName(child).localname: child.text
                            for child in p.extensions[0]
                        }
                        for p in s.points
                        if p.extensions
                    ]
                    heart_rate_list.extend(
                        [
                            int(p["hr"]) if p.__contains__("hr") else None
                            for p in extensions
                            if extensions
                        ]
                    )
                    heart_rate_list = list(filter(None, heart_rate_list))
                except:
                    pass
                line = [
                    s2.LatLng.from_degrees(p.latitude, p.longitude) for p in s.points
                ]
                self.polylines.append(line)
                polyline_container.extend([[p.latitude, p.longitude] for p in s.points])
                self.polyline_container = polyline_container
        # get start point
        try:
            self.start_latlng = start_point(*polyline_container[0])
        except:
            pass
        self.start_time_local, self.end_time_local = parse_datetime_to_local(
            self.start_time, self.end_time, polyline_container[0]
        )
        self.polyline_str = polyline.encode(polyline_container)
        self.average_heartrate = (
            sum(heart_rate_list) / len(heart_rate_list) if heart_rate_list else None
        )
        self.moving_dict = self._get_moving_data(gpx)

    def _load_fit_data(self, fit: FitFile):
        _polylines = []
        self.polyline_container = []

        for record in fit.records:
            message = record.message

            if isinstance(message, RecordMessage):
                if message.position_lat and message.position_long:
                    _polylines.append(
                        s2.LatLng.from_degrees(
                            message.position_lat, message.position_long
                        )
                    )
                    self.polyline_container.append(
                        [message.position_lat, message.position_long]
                    )
            elif isinstance(message, SessionMessage):
                self.start_time = datetime.datetime.utcfromtimestamp(
                    message.start_time / 1000
                )
                self.run_id = message.start_time
                self.end_time = datetime.datetime.utcfromtimestamp(
                    (message.start_time + message.total_elapsed_time * 1000) / 1000
                )
                self.length = message.total_distance
                self.average_heartrate = (
                    message.avg_heart_rate if message.avg_heart_rate != 0 else None
                )
                self.type = Sport(message.sport).name.lower()

                # moving_dict
                self.moving_dict["distance"] = message.total_distance
                self.moving_dict["moving_time"] = datetime.timedelta(
                    seconds=message.total_moving_time
                    if message.total_moving_time
                    else message.total_timer_time
                )
                self.moving_dict["elapsed_time"] = datetime.timedelta(
                    seconds=message.total_elapsed_time
                )
                self.moving_dict["average_speed"] = (
                    message.enhanced_avg_speed
                    if message.enhanced_avg_speed
                    else message.avg_speed
                )

        self.start_time_local, self.end_time_local = parse_datetime_to_local(
            self.start_time, self.end_time, self.polyline_container[0]
        )
        self.start_latlng = start_point(*self.polyline_container[0])
        self.polylines.append(_polylines)
        self.polyline_str = polyline.encode(self.polyline_container)

    def append(self, other):
        """Append other track to self."""
        self.end_time = other.end_time
        self.length += other.length
        # TODO maybe a better way
        try:
            self.moving_dict["distance"] += other.moving_dict["distance"]
            self.moving_dict["moving_time"] += other.moving_dict["moving_time"]
            self.moving_dict["elapsed_time"] += other.moving_dict["elapsed_time"]
            self.polyline_container.extend(other.polyline_container)
            self.polyline_str = polyline.encode(self.polyline_container)
            self.moving_dict["average_speed"] = (
                self.moving_dict["distance"]
                / self.moving_dict["moving_time"].total_seconds()
            )
            self.file_names.extend(other.file_names)
            self.special = self.special or other.special
        except:
            print(
                f"something wrong append this {self.end_time},in files {str(self.file_names)}"
            )
            pass

    @staticmethod
    def _get_moving_data(gpx):
        moving_data = gpx.get_moving_data()
        return {
            "distance": moving_data.moving_distance,
            "moving_time": datetime.timedelta(seconds=moving_data.moving_time),
            "elapsed_time": datetime.timedelta(
                seconds=(moving_data.moving_time + moving_data.stopped_time)
            ),
            "average_speed": moving_data.moving_distance / moving_data.moving_time
            if moving_data.moving_time
            else 0,
        }

    def to_namedtuple(self):
        d = {
            "id": self.run_id,
            "name": "run from gpx",  # maybe change later
            "type": "Run",  # Run for now only support run for now maybe change later
            "start_date": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "start_date_local": self.start_time_local.strftime("%Y-%m-%d %H:%M:%S"),
            "end_local": self.end_time_local.strftime("%Y-%m-%d %H:%M:%S"),
            "length": self.length,
            "average_heartrate": int(self.average_heartrate)
            if self.average_heartrate
            else None,
            "map": run_map(self.polyline_str),
            "start_latlng": self.start_latlng,
        }
        d.update(self.moving_dict)
        # return a nametuple that can use . to get attr
        return namedtuple("x", d.keys())(*d.values())
