# -*- coding: utf-8 -*-
"""
Python 3 API wrapper for Garmin Connect to get your statistics.
Copy most code from https://github.com/cyberjunky/python-garminconnect
"""
import argparse
import json
import logging
import os
import time
import re
from threading import Thread
from enum import Enum, auto

import requests

from config import GPX_FOLDER, JSON_FILE, SQL_FILE
from utils import make_activities_file

GARMIN_COM_URL_DICT = {
    "BASE_URL": "https://connect.garmin.com",
    "SSO_URL_ORIGIN": "https://sso.garmin.com",
    "SSO_URL": "https://sso.garmin.com/sso",
    "MODERN_URL": "https://connect.garmin.com/modern",
    "SIGNIN_URL": "https://sso.garmin.com/sso/signin",
    "CSS_URL": "https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css"
}


GARMIN_CN_URL_DICT = {
    "BASE_URL": 'https://connect.garmin.cn',
    "SSO_URL_ORIGIN": "https://sso.garmin.com",
    "SSO_URL": 'https://sso.garmin.cn/sso',
    "MODERN_URL": 'https://connect.garmin.cn/modern',
    "SIGNIN_URL": 'https://sso.garmin.cn/sso/signin',
    "CSS_URL": "https://static.garmincdn.cn/cn.garmin.connect/ui/css/gauth-custom-v1.2-min.css",
}

class Garmin:

    def __init__(self, email, password, is_CN=True):
        """
        Init module
        """
        self.email = email
        self.password = password
        self.req = requests.session()
        self.logger = logging.getLogger(__name__)
        self.display_name = ""
        self.full_name = ""
        self.unit_system = ""
        self.URL_DICT = GARMIN_CN_URL_DICT if is_CN else GARMIN_COM_URL_DICT
        MODERN_URL = self.URL_DICT.get("MODERN_URL")
        self.url_user_summary = MODERN_URL + '/proxy/usersummary-service/usersummary/daily/'
        self.url_user_summary_chart = MODERN_URL + '/proxy/wellness-service/wellness/dailySummaryChart/'
        self.url_heartrates = MODERN_URL + '/proxy/wellness-service/wellness/dailyHeartRate/'
        self.url_activities = MODERN_URL + '/proxy/activitylist-service/activities/search/activities'
        self.url_exercise_sets = MODERN_URL + '/proxy/activity-service/activity/'
        self.url_tcx_download = MODERN_URL + "/proxy/download-service/export/tcx/activity/"
        self.url_gpx_download = MODERN_URL + "/proxy/download-service/export/gpx/activity/"
        self.url_fit_download = MODERN_URL + "/proxy/download-service/files/activity/"
        self.url_csv_download = MODERN_URL + "/proxy/download-service/export/csv/activity/"
        self.url_device_list = MODERN_URL + '/proxy/device-service/deviceregistration/devices'
        self.url_device_settings = MODERN_URL + '/proxy/device-service/deviceservice/device-info/settings/'

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
            'origin': self.URL_DICT.get("SSO_URL_ORIGIN")
        }


    def login(self):
        """
        Login to portal
        """
        params = {
            'webhost': self.URL_DICT.get("BASE_URL"),
            'service': self.URL_DICT.get("MODERN_URL"),
            'source': self.URL_DICT.get("SIGNIN_URL"),
            'redirectAfterAccountLoginUrl': self.URL_DICT.get("MODERN_URL"),
            'redirectAfterAccountCreationUrl': self.URL_DICT.get("MODERN_URL"),
            'gauthHost': self.URL_DICT.get("SSO_URL"),
            'locale': 'en_US',
            'id': 'gauth-widget',
            'cssUrl': self.URL_DICT.get("CSS_URL"),
            'clientId': 'GarminConnect',
            'rememberMeShown': 'true',
            'rememberMeChecked': 'false',
            'createAccountShown': 'true',
            'openCreateAccount': 'false',
            'usernameShown': 'false',
            'displayNameShown': 'false',
            'consumeServiceTicket': 'false',
            'initialFocus': 'true',
            'embedWidget': 'false',
            'generateExtraServiceTicket': 'false'
        }

        data = {
            'username': self.email,
            'password': self.password,
            'embed': 'true',
            'lt': 'e1s1',
            '_eventId': 'submit',
            'displayNameRequired': 'false'
        }

        try:
            response = self.req.post(self.URL_DICT.get("SIGNIN_URL"), headers=self.headers, params=params, data=data)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")

            response.raise_for_status()
            self.logger.debug("Login response code %s", response.status_code)
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting") from err

        self.logger.debug("Response is %s", response.text)
        response_url = re.search(r'"(https:[^"]+?ticket=[^"]+)"', response.text)

        if not response_url:
            raise GarminConnectAuthenticationError("Authentication error")

        response_url = re.sub(r'\\', '', response_url.group(1))
        self.logger.debug("Fetching profile info using found response url")
        try:
            response = self.req.get(response_url)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")

            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting") from err

        self.user_prefs = self.parse_json(response.text, 'VIEWER_USERPREFERENCES')
        self.unit_system = self.user_prefs['measurementSystem']

        self.social_profile = self.parse_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.display_name = self.social_profile['displayName']
        self.full_name = self.social_profile['fullName']

    def parse_json(self, html, key):
        """
        Find and return json data
        """
        found = re.search(key + r" = JSON.parse\(\"(.*)\"\);", html, re.M)
        if found:
            text = found.group(1).replace('\\"', '"')
            return json.loads(text)


    def fetch_data(self, url):
        """
        Fetch and return data
        """
        try:
            response = self.req.get(url, headers=self.headers)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")

            self.logger.debug("Fetch response code %s", response.status_code)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            self.logger.debug("Exception occurred during data retrieval - perhaps session expired - trying relogin: %s" % err)
            self.login()
            try:
                response = self.req.get(url, headers=self.headers)
                if response.status_code == 429:
                    raise GarminConnectTooManyRequestsError("Too many requests")

                self.logger.debug("Fetch response code %s", response.status_code)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.logger.debug("Exception occurred during data retrieval, relogin without effect: %s" % err)
                raise GarminConnectConnectionError("Error connecting") from err

        resp_json = response.json()
        self.logger.debug("Fetch response json %s", resp_json)
        return resp_json


    def get_full_name(self):
        """
        Return full name
        """
        return self.full_name


    def get_unit_system(self):
        """
        Return unit system
        """
        return self.unit_system


    def get_stats_and_body(self, cdate):
        """
        Return activity data and body composition
        """
        return ({**self.get_stats(cdate), **self.get_body_composition(cdate)['totalAverage']})


    def get_stats(self, cdate):   # cDate = 'YYY-mm-dd'
        """
        Fetch available activity data
        """
        summaryurl = self.url_user_summary + self.display_name + '?' + 'calendarDate=' + cdate
        self.logger.debug("Fetching statistics %s", summaryurl)
        try:
            response = self.req.get(summaryurl, headers=self.headers)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")

            self.logger.debug("Statistics response code %s", response.status_code)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting") from err

        resp_json = response.json()
        if resp_json['privacyProtected'] is True:
            self.logger.debug("Session expired - trying relogin")
            self.login()
            try:
                response = self.req.get(summaryurl, headers=self.headers)
                if response.status_code == 429:
                    raise GarminConnectTooManyRequestsError("Too many requests")

                self.logger.debug("Statistics response code %s", response.status_code)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.logger.debug("Exception occurred during statistics retrieval, relogin without effect: %s" % err)
                raise GarminConnectConnectionError("Error connecting") from err
            else:
                resp_json = response.json()
        return resp_json

    def get_activities(self, start, limit):
        """
        Fetch available activities
        """
        activitiesurl = self.url_activities + '?start=' + str(start) + '&limit=' + str(limit)
        return self.fetch_data(activitiesurl)

    def get_excercise_sets(self, activity_id):
        activity_id = str(activity_id)
        exercisesetsurl = f"{self.url_exercise_sets}{activity_id}/exerciseSets"
        self.logger.debug(f"Fetching exercise sets for activity_id {activity_id}")

        return self.fetch_data(exercisesetsurl)

    class ActivityDownloadFormat(Enum):
        ORIGINAL = auto()
        TCX = auto()
        GPX = auto()
        CSV = auto()

    def download_activity(self, activity_id, dl_fmt=ActivityDownloadFormat.TCX):
        """
        Downloads activity in requested format and returns the raw bytes. For
        "Original" will return the zip file content, up to user to extract it.
        "CSV" will return a csv of the splits.
        """
        activity_id = str(activity_id)
        urls = {
            Garmin.ActivityDownloadFormat.ORIGINAL: f"{self.url_fit_download}{activity_id}",
            Garmin.ActivityDownloadFormat.TCX: f"{self.url_tcx_download}{activity_id}",
            Garmin.ActivityDownloadFormat.GPX: f"{self.url_gpx_download}{activity_id}",
            Garmin.ActivityDownloadFormat.CSV: f"{self.url_csv_download}{activity_id}",
        }
        if dl_fmt not in urls:
            raise ValueError(f"Unexpected value {dl_fmt} for dl_fmt")
        url = urls[dl_fmt]

        self.logger.debug(f"Downloading from {url}")
        try:
            response = self.req.get(url, headers=self.headers)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting")
        return response.content


class GarminConnectConnectionError(Exception):
    """Raised when communication ended in error."""

    def __init__(self, status):
        """Initialize."""
        super(GarminConnectConnectionError, self).__init__(status)
        self.status = status


class GarminConnectTooManyRequestsError(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, status):
        """Initialize."""
        super(GarminConnectTooManyRequestsError, self).__init__(status)
        self.status = status


class GarminConnectAuthenticationError(Exception):
    """Raised when login returns wrong result."""

    def __init__(self, status):
        """Initialize."""
        super(GarminConnectAuthenticationError, self).__init__(status)
        self.status = status


def download_garmin_gpx(client, activity_id):
    try:
        gpx_data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat.GPX)
        output_file = f"{GPX_FOLDER}/{str(activity_id)}.gpx"
        with open(output_file, "wb") as fb:
            fb.write(gpx_data)
    except:
        print(f"wrong id {activity_id}")
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="email of garmin")
    parser.add_argument("password", help="password of garmin")
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin accout is com",
    )
    options = parser.parse_args()
    client = Garmin(options.email, options.password,  options.is_cn)
    client.login()
    limit, start = 100, 0
    count = 0
    # because I don't find a para for after time, so I use garmin-id as filename
    # to find new run to generage
    old_garmin_ids = os.listdir(GPX_FOLDER)
    old_garmin_ids = [i.split(".")[0] for i in old_garmin_ids]
    api_garmin_ids = []
    while True:
        activities = client.get_activities(start, limit)
        for a in activities:
            if a.get("activityId") is None:
                print("Skipping activity without id")
                continue
            api_garmin_ids.append(str(a.get("activityId")))
        activities_count = len(activities)
        count += activities_count
        print(f"parsing from {start} to {count}")
        start += 100
        # tricky break
        if activities_count != limit:
            break

    to_generate_garmin_ids = list(set(api_garmin_ids) - set(old_garmin_ids))
    print(f"{len(to_generate_garmin_ids)} new runs to generate")
    start_time = time.time()
    threads = []
    for i in to_generate_garmin_ids:
        t = Thread(target=download_garmin_gpx, args=(client, i))
        threads.append(t)
        t.start()
    for thread in threads:
        thread.join()
    print(f"cost {time.time()-start_time} s for gpx")
    time.sleep(60) # waiting
    make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE)
