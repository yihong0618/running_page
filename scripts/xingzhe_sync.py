#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import os
from base64 import b64encode
from datetime import datetime

import aiofiles
import bs4
import gpxpy as mod_gpxpy
import requests
from config import GPX_FOLDER, JSON_FILE, SQL_FILE
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from generator import Generator

from utils import make_activities_file

startYear = 2012

# device info
XINGZHE_URL_DICT = {
    "BASE_URL": "https://www.imxingzhe.com/user/login",
    "ACTIVITY_LIST_URL": "https://www.imxingzhe.com/api/v4/user_month_info/?",
    "DOWNLOAD_GPX_URL": "https://www.imxingzhe.com/xing",
    "SSO_URL_ORIGIN": "https://www.imxingzhe.com/portal/",
}

TYPE_DICT = {
    0: "Drive",
    1: "Hike",
    2: "Run",
    3: "Ride",
    8: "Indoor Cycling",
}


def encrypt_password(public_key, password, salt):
    enc = PKCS1_v1_5.new(RSA.importKey(public_key))
    message = f"{password};{salt}".encode("utf8")
    ciphertext = enc.encrypt(message)
    return b64encode(ciphertext).decode("utf8")


def device_info_headers():
    return {
        "Connection": "keep-alive",
        "Accept": "application/json, text/javascript, */*;",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://www.imxingzhe.com",
        "Referer": "https://www.imxingzhe.com/user/login",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }


class Xingzhe:
    def __init__(self, mobile=None, password="", session_id=None, user_id=""):
        self.mobile = mobile
        self.password = password
        self.session_id = session_id
        self.user_id = user_id

        self.session = requests.Session()
        self.session.headers.update(device_info_headers())
        if session_id:
            self.session.headers.update({"Cookie": f"sessionid={session_id}"})

    def login_by_password(self):
        params = {}
        r = self.session.get(
            f"{XINGZHE_URL_DICT['BASE_URL']}",
            params=params,
        )
        rd = r.cookies["rd"]
        soup = bs4.BeautifulSoup(r.content, "html.parser")
        pubkey = soup.find(attrs={"id": "pubkey"}).text

        params = {
            "account": self.mobile,
            "password": encrypt_password(pubkey, self.password, rd),
            "source": "web",
        }
        r = self.session.post(
            f"{XINGZHE_URL_DICT['BASE_URL']}",
            json=params,
        )
        login_data = r.json()
        if not r.ok:
            print(r.json())
            raise Exception("Login Fail " + login_data["error_message"])

        self.session_id = r.cookies["sessionid"]
        self.user_id = login_data["data"]["userid"]
        print(
            f"your refresh_token and user_id are {str(self.session_id)} {str(self.user_id)}"
        )

    def get_activities_by_month(self, year, month):
        url = f"{XINGZHE_URL_DICT['ACTIVITY_LIST_URL']}user_id={self.user_id}&year={year}&month={month}"

        response = self.session.get(url)
        json = response.json()
        if json is not None and json["data"] is not None and len(json["data"]):
            return json["data"]["wo_info"]
        return []

    def get_old_tracks(self):
        results = []
        now_date = datetime.now()
        for year in range(now_date.year - startYear):
            for m in range(12):
                activities = self.get_activities_by_month(
                    year=year + startYear, month=m + 1
                )
                if len(activities) == 0:
                    pass
                ids = [
                    {"id": i["id"], "type": TYPE_DICT[i["sport"]]} for i in activities
                ]
                results = results + ids
        for m in range(now_date.month):
            activities = self.get_activities_by_month(year=now_date.year, month=m + 1)
            if len(activities) == 0:
                pass
            ids = [{"id": i["id"], "type": TYPE_DICT[i["sport"]]} for i in activities]
            results = results + ids
        return results

    def download_gpx(self, activity_id):
        url = f"{XINGZHE_URL_DICT['DOWNLOAD_GPX_URL']}/{activity_id}/gpx/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.content

    async def download_xingzhe_gpx(self, track):
        try:
            file_path = os.path.join(GPX_FOLDER, f"{track['id']}.gpx")
            if os.path.exists(file_path):
                print(f"activity {str(track['id'])}: downloaded already")
                pass
            gpx_data = self.download_gpx(track["id"])
            gpx = mod_gpxpy.parse(gpx_data.decode("utf8"))
            tracks = gpx.tracks
            tracks[0].source = "xingzhe"
            tracks[0].type = track["type"]
            tracks[0].number = track["id"]
            async with aiofiles.open(file_path, "wb") as fb:
                await fb.write(gpx.to_xml(version="1.1").encode("utf8"))
        except Exception as err:
            print(f"Failed to download activity {track}: " + str(err))
            pass


async def gather_with_concurrency(n, tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mobile_or_token", help="Xingzhe phone number or session_id")
    parser.add_argument("password_or_user_id", help="Xinzhe password or user_id")
    parser.add_argument(
        "--with-gpx",
        dest="with_gpx",
        action="store_true",
        help="get all data to gpx and download",
    )
    parser.add_argument(
        "--from-auth-token",
        dest="from_session_id",
        action="store_true",
        help="from authorization token for download data",
    )
    options = parser.parse_args()
    if options.from_session_id:
        x = Xingzhe(
            session_id=str(options.mobile_or_token),
            user_id=str(options.password_or_user_id),
        )
    else:
        x = Xingzhe(
            mobile=str(options.mobile_or_token),
            password=str(options.password_or_user_id),
        )
        x.login_by_password()

    generator = Generator(SQL_FILE)
    old_tracks_ids = generator.get_old_tracks_ids()
    tracks = x.get_old_tracks()
    new_tracks = [i for i in tracks if str(i["id"]) not in old_tracks_ids]

    print(f"{len(new_tracks)} new activities to be downloaded")

    async def download_new_activities():
        await gather_with_concurrency(
            3, [x.download_xingzhe_gpx(track) for track in new_tracks]
        )

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(download_new_activities())
    loop.run_until_complete(future)

    make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE)
