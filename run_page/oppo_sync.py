import argparse
import hashlib
import json
import os
import time
import xml.etree.ElementTree as ET
from collections import namedtuple
from datetime import datetime, timedelta
from xml.dom import minidom

import gpxpy
import polyline
import requests
from tzlocal import get_localzone

from config import (
    GPX_FOLDER,
    JSON_FILE,
    SQL_FILE,
    run_map,
    start_point,
    TCX_FOLDER,
    UTC_TIMEZONE,
)
from generator import Generator
from utils import adjust_time

TOKEN_REFRESH_URL = "https://sport.health.heytapmobi.com/open/v1/oauth/token"
OPPO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Query brief version of sports records
# The query range cannot exceed one month!
"""
Return value is like:
[
    {
       "dataType": 2,//运动数类型 1=健身类 2=其他运动类
       "startTime": 1630323565000, //开始时间 单位毫秒
       "endTime": 1630337130000,//结束时间 单位毫秒
       "sportMode": 10,//运动模式 室内跑 详情见文档附录
       "otherSportData": {
           "avgHeartRate": 153,//平均心率 单位：count/min
           "avgPace": 585,//平均配速 单位s/km
           "avgStepRate": 115,//平均步频 单位step/min
           "bestStepRate": 135,//最佳步频 单位step/min
           "bestPace": 572,//最佳配速 单位s/km
           "totalCalories": 2176000,//总消耗 单位卡
           "totalDistance": 23175,//总距离 单位米
           "totalSteps": 26062,//总步数
           "totalTime": 13562000,//总时长，单位:毫秒
           "totalClimb": 100//累计爬升高度，单位:米
       },
    },
    {
       "dataType": 1,//运动数类型 1=健身类 2=其他运动类
       "startTime": 1630293981497 //开始时间 单位毫秒
       "endTime": 1630294218127,//结束时间 单位毫秒
       "sportMode": 9,//运动模式 健身 详情见文档附录
       "fitnessData": {
           "avgHeartRate": 90,//平均心率 单位：count/min
           "courseName": "零基础减脂碎片练习",//课程名称
           "finishNumber": 1,//课程完成次数
           "trainedCalorie": 13554,//训练消耗的卡路里，单位:卡
           "trainedDuration": 176000//实际训练时间，单位:ms
       },
    }
]
"""
BRIEF_SPORT_DATA_API = "https://sport.health.heytapmobi.com/open/v1/data/sport/record?startTimeMillis={start_time}&endTimeMillis={end_time}"

# Query detailed sports records
# The query range cannot exceed one day!
DETAILED_SPORT_DATA_API = "https://sport.health.heytapmobi.com/open/v2/data/sport/record?startTimeMillis={start_time}&endTimeMillis={end_time}"

TIMESTAMP_THRESHOLD_IN_MILLISECOND = 5000

# If your points need trans from gcj02 to wgs84 coordinate which use by Mapbox
TRANS_GCJ02_TO_WGS84 = True

# May be Forerunner 945?
CONNECT_API_PART_NUMBER = "006-D2449-00"

AVAILABLE_OUTDOOR_SPORT_MODE = [
    1,  # WALK
    2,  # RUN
    3,  # RIDE
    13,  # OUTDOOR_PHYSICAL_RUN
    15,  # OUTDOOR_5KM_RELAX_RUN
    17,  # OUTDOOR_FAT_REDUCE_RUN
    22,  # MARATHON
    36,  # MOUNTAIN_CLIMBING
    37,  # CROSS_COUNTRY
]

AVAILABLE_INDOOR_SPORT_MODE = [
    10,  # INDOOR_RUN
    14,  # INDOOR_PHYSICAL_RUN
    16,  # INDOOR_5KM_RELAX_RUN
    18,  # INDOOR_FAT_REDUCE_RUN
    19,  # INDOOR_FITNESS_WALK
    21,  # TREADMILL_RUN
]


def get_access_token(session, client_id, client_secret, refresh_token):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "refreshToken": refresh_token,
        "grantType": "refreshToken",
    }
    r = session.post(TOKEN_REFRESH_URL, headers=headers, json=data)
    if r.ok:
        token = r.json()["body"]["accessToken"]
        headers["access-token"] = token
        return session, headers


def get_to_download_runs_ranges(session, sync_months, headers, start_timestamp):
    result = []
    current_time = datetime.now()
    start_datatime = datetime.fromtimestamp(start_timestamp / 1000)

    if start_datatime < current_time + timedelta(days=-30 * sync_months):
        """retrieve the data of last 6 months."""
        while sync_months >= 0:
            temp_end = int(current_time.timestamp() * 1000)
            current_time = current_time + timedelta(days=-30)
            temp_start = int(current_time.timestamp() * 1000)
            sync_months = sync_months - 1
            result.extend(
                parse_brief_sport_data(session, headers, temp_start, temp_end)
            )
    else:
        while start_datatime < current_time:
            temp_start = int(start_datatime.timestamp() * 1000)
            start_datatime = start_datatime + timedelta(days=30)
            temp_end = int(start_datatime.timestamp() * 1000)
            result.extend(
                parse_brief_sport_data(session, headers, temp_start, temp_end)
            )
    return result


def parse_brief_sport_data(session, headers, temp_start, temp_end):
    result = []
    r = session.get(
        BRIEF_SPORT_DATA_API.format(end_time=temp_end, start_time=temp_start),
        headers=headers,
    )
    if r.ok:
        sport_logs = r.json()["body"]
        for i in sport_logs:
            if (
                i["sportMode"] in AVAILABLE_INDOOR_SPORT_MODE
                or i["sportMode"] in AVAILABLE_OUTDOOR_SPORT_MODE
            ):
                result.append((i["startTime"], i["endTime"]))
                print(f"sync record: start_time: " + str(i["startTime"]))
        time.sleep(1)  # spider rule
    return result


def get_single_run_data(session, headers, start, end):
    r = session.get(
        DETAILED_SPORT_DATA_API.format(end_time=end, start_time=start), headers=headers
    )
    if r.ok:
        return r.json()


def parse_raw_data_to_name_tuple(sport_data, with_gpx, with_tcx):
    sport_data = sport_data["body"][0]
    m = hashlib.md5()
    m.update(str.encode(str(sport_data)))
    oppo_id_str = str(int(m.hexdigest(), 16))[0:16]
    oppo_id = int(oppo_id_str)

    sport_data["id"] = oppo_id
    start_time = sport_data["startTime"]
    other_data = sport_data["otherSportData"]
    avg_heart_rate = None
    elevation_gain = None
    if other_data:
        avg_heart_rate = other_data.get("avgHeartRate", None)
        # fix #66
        if avg_heart_rate and avg_heart_rate < 0:
            avg_heart_rate = None

        # if TRANS_GCJ02_TO_WGS84:
        #     run_points_data = [
        #         list(eviltransform.gcj2wgs(p["latitude"], p["longitude"]))
        #         for p in run_points_data
        #     ]
        #     for i, p in enumerate(run_points_data_gpx):
        #         p["latitude"] = run_points_data[i][0]
        #         p["longitude"] = run_points_data[i][1]

        point_dict = prepare_track_points(sport_data, with_gpx)

        gpx_data = parse_points_to_gpx(sport_data, point_dict)
        elevation_gain = gpx_data.get_uphill_downhill().uphill
        if with_gpx is True:
            download_keep_gpx(gpx_data.to_xml(), str(oppo_id))
        if with_tcx is True:
            parse_points_to_tcx(sport_data, point_dict)

    else:
        print(f"ID {oppo_id} no gps data")

    gps_data = [
        (item["latitude"], item["longitude"]) for item in other_data["gpsPoint"]
    ]
    polyline_str = polyline.encode(gps_data) if gps_data else ""
    start_latlng = start_point(*gps_data[0]) if gps_data else None
    start_date = datetime.utcfromtimestamp(start_time / 1000)
    start_date_local = adjust_time(start_date, str(get_localzone()))
    end = datetime.utcfromtimestamp(sport_data["endTime"] / 1000)
    end_local = adjust_time(end, str(get_localzone()))
    location_country = None
    if not other_data["totalTime"]:
        print(f"ID {oppo_id} has no total time just ignore please check")
        return
    d = {
        "id": int(oppo_id),
        "name": "activity from oppo",
        # future to support others workout now only for run
        "type": map_oppo_fit_type_to_strava_activity_type(sport_data["sportMode"]),
        "start_date": datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S"),
        "end": datetime.strftime(end, "%Y-%m-%d %H:%M:%S"),
        "start_date_local": datetime.strftime(start_date_local, "%Y-%m-%d %H:%M:%S"),
        "end_local": datetime.strftime(end_local, "%Y-%m-%d %H:%M:%S"),
        "length": other_data["totalDistance"],
        "average_heartrate": int(avg_heart_rate) if avg_heart_rate else None,
        "map": run_map(polyline_str),
        "start_latlng": start_latlng,
        "distance": other_data["totalDistance"],
        "moving_time": timedelta(seconds=other_data["totalTime"]),
        "elapsed_time": timedelta(
            seconds=int((sport_data["endTime"] - sport_data["startTime"]) / 1000)
        ),
        "average_speed": other_data["totalDistance"] / other_data["totalTime"] * 1000,
        "elevation_gain": elevation_gain,
        "location_country": location_country,
        "source": sport_data["deviceName"],
    }
    return namedtuple("x", d.keys())(*d.values())


def get_all_oppo_tracks(
    client_id,
    client_secret,
    refresh_token,
    sync_months,
    last_track_date,
    with_download_gpx,
    with_download_tcx,
):
    if with_download_gpx and not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)
    s = requests.Session()
    s, headers = get_access_token(s, client_id, client_secret, refresh_token)

    last_timestamp = (
        0
        if (last_track_date == 0)
        else int(
            datetime.timestamp(datetime.strptime(last_track_date, "%Y-%m-%d %H:%M:%S"))
            * 1000
        )
    )

    runs = get_to_download_runs_ranges(s, sync_months, headers, last_timestamp + 1000)
    print(f"{len(runs)} new oppo runs to generate")
    tracks = []
    for start, end in runs:
        print(f"parsing oppo id {str(start)}-{str(end)}")
        try:
            run_data = get_single_run_data(s, headers, start, end)
            track = parse_raw_data_to_name_tuple(
                run_data, with_download_gpx, with_download_tcx
            )
            tracks.append(track)
        except Exception as e:
            print(f"Something wrong paring keep id {str(start)}-{str(end)}" + str(e))
    return tracks


def switch(v):
    yield lambda *c: v in c


def map_oppo_fit_type_to_gpx_type(oppo_type):
    for case in switch(oppo_type):
        if case(1):  # WALK
            return "Walking"
        if case(2, 13, 15, 17, 22, 10, 14, 16, 18, 21, 37):
            # RUN |
            # OUTDOOR_PHYSICAL_RUN |
            # OUTDOOR_5KM_RELAX_RUN |
            # OUTDOOR_FAT_REDUCE_RUN |
            # MARATHON
            # INDOOR_RUN, etc.
            # CROSS_COUNTRY
            return "Running"
        if case(19):  # MOUNTAIN_CLIMBING
            return "Hiking"
        if case(3):  # Ride
            return "Biking"


def map_oppo_fit_type_to_strava_activity_type(oppo_type):
    """
    Note: should consider the supported strava activity type:
    Link: https://developers.strava.com/docs/reference/#api-models-ActivityType
    """
    for case in switch(oppo_type):
        if case(1):  # WALK
            return "Walk"
        if case(2, 13, 15, 17, 22, 10, 14, 16, 18, 21, 37):
            # RUN |
            # OUTDOOR_PHYSICAL_RUN |
            # OUTDOOR_5KM_RELAX_RUN |
            # OUTDOOR_FAT_REDUCE_RUN |
            # MARATHON
            # INDOOR_RUN, etc.
            # CROSS_COUNTRY
            return "Run"
        if case(19):  # MOUNTAIN_CLIMBING
            return "Hike"
        if case(3):  # Ride
            return "Ride"


def parse_points_to_gpx(sport_data, points_dict_list):
    gpx = gpxpy.gpx.GPX()
    gpx.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = f"""gpx from {sport_data["deviceName"]}"""
    gpx_track.type = map_oppo_fit_type_to_gpx_type(sport_data["sportMode"])
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    for p in points_dict_list:
        point = gpxpy.gpx.GPXTrackPoint(
            latitude=p["latitude"],
            longitude=p["longitude"],
            time=p["time"],
            elevation=p.get("elevation"),
        )
        hr = p.get("hr")
        cad = p.get("cad")
        if hr is not None or cad is not None:
            hr_str = f"""<gpxtpx:hr>{hr}</gpxtpx:hr>""" if hr is not None else ""
            cad_str = (
                f"""<gpxtpx:cad>{p["cad"]}</gpxtpx:cad>""" if cad is not None else ""
            )
            gpx_extension = ET.fromstring(
                f"""<gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
                    {hr_str}
                    {cad_str}
                    </gpxtpx:TrackPointExtension>
                    """
            )
            point.extensions.append(gpx_extension)
        gpx_segment.points.append(point)
    return gpx


def download_keep_gpx(gpx_data, keep_id):
    try:
        print(f"downloading keep_id {str(keep_id)} gpx")
        file_path = os.path.join(GPX_FOLDER, str(keep_id) + ".gpx")
        with open(file_path, "w") as fb:
            fb.write(gpx_data)
    except:
        print(f"wrong id {keep_id}")
        pass


def prepare_track_points(sport_data, with_gpx):
    """
    Convert run points data to GPX format.

    Args:
        sport_data (map of dict): A map of run data points.
        with_gpx (boolean): export to gpx file or not.

    Returns:
        points_dict_list (list): data with need to parse.
    """
    other_data = sport_data["otherSportData"]
    decoded_hr_data = other_data.get("heartRate", None)
    points_dict_list = []

    if other_data.get("gpsPoint"):
        timestamp_list = [item["timestamp"] for item in decoded_hr_data]
        other_data = sport_data["otherSportData"]
        value_size = len(other_data.get("gpsPoint", None))

        for i in range(value_size):
            temp_timestamp = other_data.get("gpsPoint")[i]["timestamp"]
            j = timestamp_list.index(temp_timestamp)

            points_dict = {
                "latitude": other_data.get("gpsPoint")[i]["latitude"],
                "longitude": other_data.get("gpsPoint")[i]["longitude"],
                "time": datetime.utcfromtimestamp(temp_timestamp / 1000),
                "hr": other_data.get("heartRate")[j]["value"],
            }
            points_dict_list.append(get_value(j, points_dict, other_data))
    elif with_gpx is False:
        value_size = len(other_data.get("heartRate", None))

        for i in range(value_size):
            temp_timestamp = other_data.get("heartRate")[i]["timestamp"]
            temp_date = datetime.utcfromtimestamp(temp_timestamp / 1000)
            points_dict = {
                "time": temp_date,
                "hr": other_data.get("heartRate")[i]["value"],
            }
            points_dict_list.append(get_value(i, points_dict, other_data))

    return points_dict_list


def get_value(index, points_dict, other_data):
    if other_data.get("pace"):
        pace = other_data.get("pace")[index]["value"]
        points_dict["speed"] = 0 if pace == 0 else 1000 / pace
    if other_data.get("frequency"):
        points_dict["cad"] = other_data.get("frequency")[index]["value"]
    if other_data.get("distance"):
        points_dict["distance"] = other_data.get("distance")[index]["value"]
    if other_data.get("elevation"):
        points_dict["elevation"] = other_data.get("elevation")[index]["value"]
    return points_dict


def parse_points_to_tcx(sport_data, points_dict_list):
    # route ID
    fit_id = str(sport_data["id"])
    # local time
    start_time = sport_data["startTime"]
    start_date = datetime.utcfromtimestamp(start_time / 1000)
    fit_start_time = datetime.strftime(
        adjust_time(start_date, UTC_TIMEZONE), "%Y-%m-%dT%H:%M:%SZ"
    )

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
    sports_type = map_oppo_fit_type_to_gpx_type(sport_data["sportMode"])
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
    activity_creator_name.text = sport_data["deviceName"]
    activity_creator.append(activity_creator_name)
    activity_creator_product = ET.Element("ProductID")
    activity_creator_product.text = "3441"
    activity_creator.append(activity_creator_product)

    """
    first, find distance split index
    """
    lap_split_indexes = [0]
    points_dict_list_chunks = []

    for idx, item in enumerate(points_dict_list):
        size = len(lap_split_indexes)
        if sports_type == "Running":
            target_distance = 1000 * size
        elif sports_type == "Biking":
            target_distance = 5000 * size
        else:
            break

        if idx + 1 != len(points_dict_list):
            if (
                item["distance"]
                < target_distance
                <= points_dict_list[idx + 1]["distance"]
            ):
                lap_split_indexes.append(idx)

    if len(lap_split_indexes) == 1:
        points_dict_list_chunks = [points_dict_list]
    else:
        for idx, item in enumerate(lap_split_indexes):
            if idx + 1 == len(lap_split_indexes):
                points_dict_list_chunks.append(
                    points_dict_list[item : len(points_dict_list) - 1]
                )
            else:
                points_dict_list_chunks.append(
                    points_dict_list[item : lap_split_indexes[idx + 1]]
                )

    current_distance = 0
    current_time = start_date

    for item in points_dict_list_chunks:
        #   Lap
        lap_start_time = datetime.strftime(
            adjust_time(item[0]["time"], UTC_TIMEZONE), "%Y-%m-%dT%H:%M:%SZ"
        )
        activity_lap = ET.Element("Lap", {"StartTime": lap_start_time})
        activity.append(activity_lap)

        #       DistanceMeters
        total_distance_node = ET.Element("DistanceMeters")
        total_distance_node.text = str(item[-1]["distance"] - current_distance)
        current_distance = item[-1]["distance"]
        activity_lap.append(total_distance_node)
        #       TotalTimeSeconds
        chile_node = ET.Element("TotalTimeSeconds")
        chile_node.text = str((item[-1]["time"] - current_time).total_seconds())
        current_time = item[-1]["time"]
        activity_lap.append(chile_node)
        #       MaximumSpeed
        chile_node = ET.Element("MaximumSpeed")
        chile_node.text = str(max(node["speed"] for node in item))
        activity_lap.append(chile_node)
        # #       Calories
        # chile_node = ET.Element("Calories")
        # chile_node.text = str(int(other_data["totalCalories"] / 1000))
        # activity_lap.append(chile_node)
        #       AverageHeartRateBpm
        # bpm = ET.Element("AverageHeartRateBpm")
        # bpm_value = ET.Element("Value")
        # bpm.append(bpm_value)
        # bpm_value.text = str(other_data["avgHeartRate"])
        # heartrate_list = [item["value"] for item in other_data["heartRate"]]
        # bpm_value.text = str(round(statistics.mean(heartrate_list)))
        # activity_lap.append(bpm)
        # #       MaximumHeartRateBpm
        # bpm = ET.Element("MaximumHeartRateBpm")
        # bpm_value = ET.Element("Value")
        # bpm.append(bpm_value)
        # bpm_value.text = str(max(node["hr"] for node in item))
        # activity_lap.append(bpm)

        # Track
        track = ET.Element("Track")
        activity_lap.append(track)

        for p in item:
            tp = ET.Element("Trackpoint")
            track.append(tp)
            # Time
            time_stamp = datetime.strftime(
                adjust_time(p["time"], UTC_TIMEZONE), "%Y-%m-%dT%H:%M:%SZ"
            )
            time_label = ET.Element("Time")
            time_label.text = time_stamp

            tp.append(time_label)
            if sports_type == "Biking" and p.get("cad"):
                cadence_label = ET.Element("Cadence")
                cadence_label.text = str(p["cad"])
                tp.append(cadence_label)
            if p.get("distance"):
                distance_label = ET.Element("DistanceMeters")
                distance_label.text = str(p["distance"])
                tp.append(distance_label)
            # HeartRateBpm
            # None was converted to bytes by np.dtype, becoming a string "None" after decode...-_-
            # as well as LatitudeDegrees and LongitudeDegrees below
            if p.get("hr"):
                bpm = ET.Element("HeartRateBpm")
                bpm_value = ET.Element("Value")
                bpm.append(bpm_value)
                bpm_value.text = str(p["hr"])
                tp.append(bpm)
            #  AltitudeMeters
            if p.get("elevation"):
                altitude_meters = ET.Element("AltitudeMeters")
                altitude_meters.text = str(p["elevation"] / 10)
                tp.append(altitude_meters)
            if p.get("latitude"):
                position = ET.Element("Position")
                tp.append(position)
                #   LatitudeDegrees
                lati = ET.Element("LatitudeDegrees")
                lati.text = str(p["latitude"])
                position.append(lati)
                #   LongitudeDegrees
                longi = ET.Element("LongitudeDegrees")
                longi.text = str(p["longitude"])
                position.append(longi)
            # Extensions
            if p.get("speed") is not None or (
                p.get("cad") is not None and sports_type == "Running"
            ):
                extensions = ET.Element("Extensions")
                tp.append(extensions)
                tpx = ET.Element("ns3:TPX")
                extensions.append(tpx)
                #   LatitudeDegrees
                #   LatitudeDegrees
                if p.get("speed") is not None:
                    speed = ET.Element("ns3:Speed")
                    speed.text = str(p["speed"])
                    tpx.append(speed)
                if p.get("cad") is not None and sports_type == "Running":
                    cad = ET.Element("ns3:RunCadence")
                    cad.text = str(round(p["cad"] / 2))
                    tpx.append(cad)
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
    xml_str = minidom.parseString(ET.tostring(training_center_database)).toprettyxml()
    with open(TCX_FOLDER + "/" + fit_id + ".tcx", "w") as f:
        f.write(str(xml_str))


def formated_input(
    run_data, run_data_label, tcx_label
):  # load run_data from run_data_label, parse to tcx_label, return xml node
    fit_data = str(run_data[run_data_label])
    chile_node = ET.Element(tcx_label)
    chile_node.text = fit_data
    return chile_node


def run_oppo_sync(
    client_id,
    client_secret,
    refresh_token,
    sync_months=6,
    with_download_gpx=False,
    with_download_tcx=True,
):
    generator = Generator(SQL_FILE)
    old_tracks_dates = generator.get_old_tracks_dates()
    new_tracks = get_all_oppo_tracks(
        client_id,
        client_secret,
        refresh_token,
        sync_months,
        old_tracks_dates[0] if old_tracks_dates else 0,
        with_download_gpx,
        with_download_tcx,
    )
    generator.sync_from_app(new_tracks)

    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f, indent=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", help="oppo heytap fit client id")
    parser.add_argument("client_secret", help="oppo heytap fit client secret")
    parser.add_argument("refresh_token", help="oppo heytap fit refresh token")
    parser.add_argument(
        "--with-gpx",
        dest="with_gpx",
        action="store_true",
        help="get all oppo fit data to gpx and download",
    )
    parser.add_argument(
        "--with-tcx",
        dest="with_tcx",
        action="store_true",
        help="get all oppo fit data to tcx and download",
    )
    parser.add_argument(
        "-m" "--months",
        type=int,
        default=6,
        dest="sync_months",
        help="oppo has limited the data retrieve, so the default months we can sync is 6.",
    )
    options = parser.parse_args()
    run_oppo_sync(
        options.client_id,
        options.client_secret,
        options.refresh_token,
        options.sync_months,
        options.with_gpx,
        options.with_tcx,
    )
