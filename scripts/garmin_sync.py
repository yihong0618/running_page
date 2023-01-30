"""
Python 3 API wrapper for Garmin Connect to get your statistics.
Copy most code from https://github.com/cyberjunky/python-garminconnect
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
import traceback

import aiofiles
import cloudscraper
import httpx
from config import JSON_FILE, SQL_FILE, FOLDER_DICT, config
from io import BytesIO
from tenacity import retry, stop_after_attempt, wait_fixed

from utils import make_activities_file

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

TIME_OUT = httpx.Timeout(240.0, connect=360.0)
GARMIN_COM_URL_DICT = {
    "BASE_URL": "https://connect.garmin.com",
    "SSO_URL_ORIGIN": "https://sso.garmin.com",
    "SSO_URL": "https://sso.garmin.com/sso",
    # "MODERN_URL": "https://connect.garmin.com/modern",
    "MODERN_URL": "https://connect.garmin.com",
    "SIGNIN_URL": "https://sso.garmin.com/sso/signin",
    "CSS_URL": "https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css",
    "UPLOAD_URL": "https://connect.garmin.com/modern/proxy/upload-service/upload/.gpx",
    "ACTIVITY_URL": "https://connect.garmin.com/proxy/activity-service/activity/{activity_id}",
}

GARMIN_CN_URL_DICT = {
    "BASE_URL": "https://connect.garmin.cn",
    "SSO_URL_ORIGIN": "https://sso.garmin.com",
    "SSO_URL": "https://sso.garmin.cn/sso",
    # "MODERN_URL": "https://connect.garmin.cn/modern",
    "MODERN_URL": "https://connect.garmin.cn",
    "SIGNIN_URL": "https://sso.garmin.cn/sso/signin",
    "CSS_URL": "https://static.garmincdn.cn/cn.garmin.connect/ui/css/gauth-custom-v1.2-min.css",
    "UPLOAD_URL": "https://connect.garmin.cn/modern/proxy/upload-service/upload/.gpx",
    "ACTIVITY_URL": "https://connect.garmin.cn/proxy/activity-service/activity/{activity_id}",
}


class Garmin:
    def __init__(self, email, password, auth_domain, is_only_running=False):
        """
        Init module
        """
        self.email = email
        self.password = password
        self.req = httpx.AsyncClient(timeout=TIME_OUT)
        self.cf_req = cloudscraper.CloudScraper()
        self.URL_DICT = (
            GARMIN_CN_URL_DICT
            if auth_domain and str(auth_domain).upper() == "CN"
            else GARMIN_COM_URL_DICT
        )
        self.modern_url = self.URL_DICT.get("MODERN_URL")

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "origin": self.URL_DICT.get("SSO_URL_ORIGIN"),
            "nk": "NT",
        }
        self.is_only_running = is_only_running
        self.upload_url = self.URL_DICT.get("UPLOAD_URL")
        self.activity_url = self.URL_DICT.get("ACTIVITY_URL")
        self.is_login = False

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(30))
    def login(self):
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
            self.cf_req.get(
                self.URL_DICT.get("SIGNIN_URL"), headers=self.headers, params=params
            )
            response = self.cf_req.post(
                self.URL_DICT.get("SIGNIN_URL"),
                headers=self.headers,
                params=params,
                data=data,
            )
        except Exception as err:
            raise GarminConnectConnectionError("Error connecting") from err
        response_url = re.search(r'"(https:[^"]+?ticket=[^"]+)"', response.text)

        if not response_url:
            raise GarminConnectAuthenticationError("Authentication error")

        response_url = re.sub(r"\\", "", response_url.group(1))
        try:
            response = self.cf_req.get(response_url)
            self.req.cookies = self.cf_req.cookies
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")
            response.raise_for_status()
            self.is_login = True
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
                self.login()
                await self.fetch_data(url, retrying=True)

    async def get_activities(self, start, limit):
        """
        Fetch available activities
        """
        if not self.is_login:
            self.login()
        url = f"{self.modern_url}/proxy/activitylist-service/activities/search/activities?start={start}&limit={limit}"
        if self.is_only_running:
            url = url + "&activityType=running"
        return await self.fetch_data(url)

    async def download_activity(self, activity_id, file_type="gpx"):
        url = f"{self.modern_url}/proxy/download-service/export/{file_type}/activity/{activity_id}"
        logger.info(f"Download activity from {url}")
        response = await self.req.get(url, headers=self.headers)
        response.raise_for_status()
        return response.read()

    async def upload_activities(self, files):
        if not self.is_login:
            self.login()
        for file, garmin_type in files:
            files = {"data": ("file.gpx", file)}
            try:
                res = await self.req.post(
                    self.upload_url, files=files, headers={"nk": "NT"}
                )
            except Exception as e:
                print(str(e))
                # just pass for now
                continue
            try:
                resp = res.json()["detailedImportResult"]
            except Exception as e:
                print(e)
                raise Exception("failed to upload")
            # change the type
            if resp["successes"]:
                activity_id = resp["successes"][0]["internalId"]
                print(f"id {activity_id} uploaded...")
                data = {"activityTypeDTO": {"typeKey": garmin_type}}
                encoding_headers = {"Content-Type": "application/json; charset=UTF-8"}
                r = await self.req.put(
                    self.activity_url.format(activity_id=activity_id),
                    data=json.dumps(data),
                    headers=encoding_headers,
                )
                r.raise_for_status()
        await self.req.aclose()

    async def upload_activities_original(self, datas):
        print("start upload activities to garmin!!!")
        if not self.is_login:
            self.login()
        for data in datas:
            print(data.filename)
            with open(data.filename, "wb") as f:
                for chunk in data.content:
                    f.write(chunk)
            f = open(data.filename, "rb")
            files = {"data": (data.filename, BytesIO(f.read()))}

            try:
                res = await self.req.post(
                    self.upload_url, files=files, headers={"nk": "NT"}
                )
                os.remove(data.filename)
                f.close()
            except Exception as e:
                print(str(e))
                # just pass for now
                continue
            try:
                resp = res.json()["detailedImportResult"]
                print("garmin upload success: ", resp)
            except Exception as e:
                print("garmin upload failed: ", e)
        await self.req.aclose()


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


async def download_garmin_data(client, activity_id, file_type="gpx"):
    folder = FOLDER_DICT.get(file_type, "gpx")
    try:
        file_data = await client.download_activity(activity_id, file_type=file_type)
        file_path = os.path.join(folder, f"{activity_id}.{file_type}")
        async with aiofiles.open(file_path, "wb") as fb:
            await fb.write(file_data)
    except:
        print(f"Failed to download activity {activity_id}: ")
        traceback.print_exc()


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


def get_downloaded_ids(folder):
    return [i.split(".")[0] for i in os.listdir(folder) if not i.startswith(".")]


async def download_new_activities(
    email, password, auth_domain, downloaded_ids, is_only_running, folder, file_type
):
    client = Garmin(email, password, auth_domain, is_only_running)
    client.login()
    # because I don't find a para for after time, so I use garmin-id as filename
    # to find new run to generage
    activity_ids = await get_activity_id_list(client)
    to_generate_garmin_ids = list(set(activity_ids) - set(downloaded_ids))
    print(f"{len(to_generate_garmin_ids)} new activities to be downloaded")

    start_time = time.time()
    await gather_with_concurrency(
        10,
        [
            download_garmin_data(client, id, file_type=file_type)
            for id in to_generate_garmin_ids
        ],
    )
    print(f"Download finished. Elapsed {time.time()-start_time} seconds")

    await client.req.aclose()
    return to_generate_garmin_ids


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email", nargs="?", help="email of garmin")
    parser.add_argument("password", nargs="?", help="password of garmin")
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin accout is cn",
    )
    parser.add_argument(
        "--only-run",
        dest="only_run",
        action="store_true",
        help="if is only for running",
    )
    parser.add_argument(
        "--tcx",
        dest="download_file_type",
        action="store_const",
        const="tcx",
        default="gpx",
        help="to download personal documents or ebook",
    )
    options = parser.parse_args()
    email = options.email or config("sync", "garmin", "email")
    password = options.password or config("sync", "garmin", "password")
    auth_domain = (
        "CN" if options.is_cn else config("sync", "garmin", "authentication_domain")
    )
    file_type = options.download_file_type
    is_only_running = options.only_run
    if email == None or password == None:
        print("Missing argument nor valid configuration file")
        sys.exit(1)
    folder = FOLDER_DICT.get(file_type, "gpx")
    # make gpx or tcx dir
    if not os.path.exists(folder):
        os.mkdir(folder)
    downloaded_ids = get_downloaded_ids(folder)

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        download_new_activities(
            email,
            password,
            auth_domain,
            downloaded_ids,
            is_only_running,
            folder,
            file_type,
        )
    )
    loop.run_until_complete(future)
    make_activities_file(SQL_FILE, folder, JSON_FILE, file_suffix=file_type)
