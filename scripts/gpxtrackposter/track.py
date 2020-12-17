"""Create and maintain info about a given activity track (corresponding to one GPX file)."""
# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import datetime
import gpxpy as mod_gpxpy
import json
import os
import s2sphere as s2
from .exceptions import TrackLoadError
from .utils import parse_datetime_to_local
import polyline
from collections import namedtuple

start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")


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

    def load_gpx(self, file_name):
        try:
            self.file_names = [os.path.basename(file_name)]
            # Handle empty gpx files
            # (for example, treadmill runs pulled via garmin-connect-export)
            if os.path.getsize(file_name) == 0:
                raise TrackLoadError("Empty GPX file")
            with open(file_name, "r") as file:
                self._load_gpx_data(mod_gpxpy.parse(file))
        except:
            print(
                f"Something went wrong when loading GPX. for file {self.file_names[0]}"
            )
            pass

    def load_from_db(self, activate):
        # use strava as file name
        self.file_names = [str(activate.run_id)]
        start_time = datetime.datetime.strptime(
            activate.start_date_local, "%Y-%m-%d %H:%M:%S"
        )
        self.start_time_local = start_time
        self.end_time = start_time + activate.elapsed_time
        self.length = float(activate.distance)
        summary_polyline = activate.summary_polyline
        polyline_data = polyline.decode(summary_polyline) if summary_polyline else []
        self.polylines = [[s2.LatLng.from_degrees(p[0], p[1]) for p in polyline_data]]

    def bbox(self):
        """Compute the smallest rectangle that contains the entire track (border box)."""
        bbox = s2.LatLngRect()
        for line in self.polylines:
            for latlng in line:
                bbox = bbox.union(s2.LatLngRect.from_point(latlng.normalized()))
        return bbox

    def _load_gpx_data(self, gpx):
        self.start_time, self.end_time = gpx.get_time_bounds()
        # use timestamp as id
        self.run_id = int(datetime.datetime.timestamp(self.start_time) * 1000)
        self.start_time_local, self.end_time_local = parse_datetime_to_local(
            self.start_time, self.end_time, gpx
        )
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
                    heart_rate_list.extend(
                        [
                            int(p.extensions[0].getchildren()[0].text)
                            for p in s.points
                            if p.extensions
                        ]
                    )
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
        self.polyline_str = polyline.encode(polyline_container)
        self.average_heartrate = (
            sum(heart_rate_list) / len(heart_rate_list) if heart_rate_list else None
        )
        self.moving_dict = self._get_moving_data(gpx)

    def append(self, other):
        """Append other track to self."""
        self.end_time = other.end_time
        self.length += other.length
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

    def load_cache(self, cache_file_name):
        try:
            with open(cache_file_name) as data_file:
                data = json.load(data_file)
                self.start_time = datetime.datetime.strptime(
                    data["start"], "%Y-%m-%d %H:%M:%S"
                )
                self.end_time = datetime.datetime.strptime(
                    data["end"], "%Y-%m-%d %H:%M:%S"
                )
                self.start_time_local = datetime.datetime.strptime(
                    data["start_local"], "%Y-%m-%d %H:%M:%S"
                )
                self.end_time_local = datetime.datetime.strptime(
                    data["end_local"], "%Y-%m-%d %H:%M:%S"
                )
                self.length = float(data["length"])
                self.polylines = []
                for data_line in data["segments"]:
                    self.polylines.append(
                        [
                            s2.LatLng.from_degrees(float(d["lat"]), float(d["lng"]))
                            for d in data_line
                        ]
                    )
        except Exception as e:
            raise TrackLoadError("Failed to load track data from cache.") from e

    def store_cache(self, cache_file_name):
        """Cache the current track"""
        dir_name = os.path.dirname(cache_file_name)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        with open(cache_file_name, "w") as json_file:
            lines_data = []
            for line in self.polylines:
                lines_data.append(
                    [
                        {"lat": latlng.lat().degrees, "lng": latlng.lng().degrees}
                        for latlng in line
                    ]
                )
            json.dump(
                {
                    "start": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "start_local": self.start_time_local.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_local": self.end_time_local.strftime("%Y-%m-%d %H:%M:%S"),
                    "length": self.length,
                    "segments": lines_data,
                },
                json_file,
            )

    @staticmethod
    def _get_moving_data(gpx):
        moving_data = gpx.get_moving_data()
        return {
            "distance": moving_data.moving_distance,
            "moving_time": datetime.timedelta(seconds=moving_data.moving_time),
            "elapsed_time": datetime.timedelta(
                seconds=(moving_data.moving_time + moving_data.stopped_time)
            ),
            "average_speed": moving_data.moving_distance / moving_data.moving_time,
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
