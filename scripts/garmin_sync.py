# -*- coding: utf-8 -*-
"""
Python 3 API wrapper for Garmin Connect to get your statistics.
Copy most code from https://github.com/cyberjunky/python-garminconnect
"""

import argparse
import logging
import os
import time
import re
import sys
import traceback
import asyncio
import httpx
import aiofiles

from config import GPX_FOLDER, JSON_FILE, SQL_FILE, config
from utils import make_activities_file

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


TIME_OUT = httpx.Timeout(240.0, connect=360.0)
GARMIN_COM_URL_DICT = {
    "BASE_URL": "https://connect.garmin.com",
    "SSO_URL_ORIGIN": "https://sso.garmin.com",
    "SSO_URL": "https://sso.garmin.com/sso",
    "MODERN_URL": "https://connect.garmin.com/modern",
    "SIGNIN_URL": "https://sso.garmin.com/sso/signin",
    "CSS_URL": "https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css",
}

GARMIN_CN_URL_DICT = {
    "BASE_URL": "https://connect.garmin.cn",
    "SSO_URL_ORIGIN": "https://sso.garmin.com",
    "SSO_URL": "https://sso.garmin.cn/sso",
    "MODERN_URL": "https://connect.garmin.cn/modern",
    "SIGNIN_URL": "https://sso.garmin.cn/sso/signin",
    "CSS_URL": "https://static.garmincdn.cn/cn.garmin.connect/ui/css/gauth-custom-v1.2-min.css",
}


class Garmin:
    def __init__(self, email, password, auth_domain):
        """
        Init module
        """
        self.email = email
        self.password = password
        self.req = httpx.AsyncClient(timeout=TIME_OUT)
        self.URL_DICT = (
            GARMIN_CN_URL_DICT
            if auth_domain and str(auth_domain).upper() == "CN"
            else GARMIN_COM_URL_DICT
        )
        self.modern_url = self.URL_DICT.get("MODERN_URL")

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "origin": self.URL_DICT.get("SSO_URL_ORIGIN"),
        }

    async def login(self):
        """
        Login to portal
        """
        params = {
            "webhost": self.URL_DICT.get("BASE_URL"),
            "service": self.modern_url,
            "source": self.URL_DICT.get("SIGNIN_URL"),
            "redirectAfterAccountLoginUrl": self.modern_url,
            "redirectAfterAccountCreationUrl": self.modern_url,
            "gauthHost": self.URL_DICT.get("SSO_URL"),
            "locale": "en_US",
            "id": "gauth-widget",
            "cssUrl": self.URL_DICT.get("CSS_URL"),
            "clientId": "GarminConnect",
            "rememberMeShown": "true",
            "rememberMeChecked": "false",
            "createAccountShown": "true",
            "openCreateAccount": "false",
            "usernameShown": "false",
            "displayNameShown": "false",
            "consumeServiceTicket": "false",
            "initialFocus": "true",
            "embedWidget": "false",
            "generateExtraServiceTicket": "false",
        }

        data = {
            "username": self.email,
            "password": self.password,
            "embed": "true",
            "lt": "e1s1",
            "_eventId": "submit",
            "displayNameRequired": "false",
        }

        try:
            response = await self.req.post(
                self.URL_DICT.get("SIGNIN_URL"),
                headers=self.headers,
                params=params,
                data=data,
            )
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")
            response.raise_for_status()
            logger.debug("Login response code %s", response.status_code)
            text = response.text
        except Exception as err:
            raise GarminConnectConnectionError("Error connecting") from err

        # logger.debug("Response is %s", text)
        response_url = re.search(r'"(https:[^"]+?ticket=[^"]+)"', text)

        if not response_url:
            raise GarminConnectAuthenticationError("Authentication error")

        response_url = re.sub(r"\\", "", response_url.group(1))
        try:
            response = await self.req.get(response_url)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")
            response.raise_for_status()
        except Exception as err:
            raise GarminConnectConnectionError("Error connecting") from err

    async def fetch_data(self, url, retrying=False):
        """
        Fetch and return data
        """
        try:
            response = await self.req.get(url, headers=self.headers)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")
            logger.debug(f"fetch_data got response code {response.status_code}")
            response.raise_for_status()
            return response.json()
        except Exception as err:
            if retrying:
                logger.debug(
                    "Exception occurred during data retrieval, relogin without effect: %s"
                    % err
                )
                raise GarminConnectConnectionError("Error connecting") from err
            else:
                logger.debug(
                    "Exception occurred during data retrieval - perhaps session expired - trying relogin: %s"
                    % err
                )
                await self.login()
                await self.fetch_data(url, retrying=True)

    async def get_activities(self, start, limit):
        """
        Fetch available activities
        """
        url = f"{self.modern_url}/proxy/activitylist-service/activities/search/activities?start={start}&limit={limit}"
        return await self.fetch_data(url)

    async def download_activity(self, activity_id):
        url = f"{self.modern_url}/proxy/download-service/export/gpx/activity/{activity_id}"
        logger.info(f"Download activity from {url}")
        response = await self.req.get(url, headers=self.headers)
        response.raise_for_status()
        return response.read()


class GarminConnectHttpError(Exception):
    def __init__(self, status):
        super(GarminConnectHttpError, self).__init__(status)
        self.status = status


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


async def download_garmin_gpx(client, activity_id):
    try:
        gpx_data = await client.download_activity(activity_id)
        file_path = os.path.join(GPX_FOLDER, f"{activity_id}.gpx")
        async with aiofiles.open(file_path, "wb") as fb:
            await fb.write(gpx_data)
    except:
        print(f"Failed to download activity {activity_id}: ")
        traceback.print_exc()
        pass


async def get_activity_id_list(client, start=0):
    activities = await client.get_activities(start, 100)
    if len(activities) > 0:
        ids = list(map(lambda a: str(a.get("activityId", "")), activities))
        print(f"Syncing Activity IDs")
        return ids + await get_activity_id_list(client, start + 100)
    else:
        return []


async def gather_with_concurrency(n, tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email", nargs="?", help="email of garmin")
    parser.add_argument("password", nargs="?", help="password of garmin")
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin accout is com",
    )
    options = parser.parse_args()
    email = options.email or config("sync", "garmin", "email")
    password = options.password or config("sync", "garmin", "password")
    auth_domain = (
        "CN" if options.is_cn else config("sync", "garmin", "authentication_domain")
    )
    if email == None or password == None:
        print("Missing argument nor valid configuration file")
        sys.exit(1)

    # make gpx dir
    if not os.path.exists(GPX_FOLDER):
        os.mkdir(GPX_FOLDER)

    async def download_new_activities():
        client = Garmin(email, password, auth_domain)
        await client.login()

        # because I don't find a para for after time, so I use garmin-id as filename
        # to find new run to generage
        downloaded_ids = [
            i.split(".")[0] for i in os.listdir(GPX_FOLDER) if not i.startswith(".")
        ]
        activity_ids = await get_activity_id_list(client)
        to_generate_garmin_ids = list(set(activity_ids) - set(downloaded_ids))
        print(f"{len(to_generate_garmin_ids)} new activities to be downloaded")

        start_time = time.time()
        await gather_with_concurrency(
            10, [download_garmin_gpx(client, id) for id in to_generate_garmin_ids]
        )
        print(f"Download finished. Elapsed {time.time()-start_time} seconds")
        make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE)

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(download_new_activities())
    loop.run_until_complete(future)
