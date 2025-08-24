import os
import sys
import argparse
import requests
from config import (
    GPX_FOLDER,
    TCX_FOLDER,
    FIT_FOLDER,
)

BASE_URL = "https://prod.zh.igpsport.com/service/"
LOGIN_URL = BASE_URL + "auth/account/login"
ACTIVITY_URL = BASE_URL + "web-gateway/web-analyze/activity/"
QUERY_URL = ACTIVITY_URL + "queryMyActivity"
DOWNLOAD_URL = ACTIVITY_URL + "getDownloadUrl/"


class IGPSPORT:
    def __init__(self, username, password, token):
        self.username = username
        self.password = password
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": "Bearer " + token})

    def login(self):
        if not self.username or not self.password:
            raise Exception("username or password is empty")
        req = {
            "appId": "igpsport-web",
            "username": self.username,
            "password": self.password,
        }
        rsp = self.session.post(LOGIN_URL, json=req)
        if not rsp.ok:
            raise Exception(rsp.reason)
        ret = rsp.json()
        access_token = ret.get("data", {}).get("access_token", "")
        if not access_token:
            raise Exception("AccessToken nil")
        self.token = access_token
        self.session.headers.update({"Authorization": "Bearer " + access_token})

    def get_activity_list(self, page_no, ext):
        if page_no < 1:
            raise Exception("pageNo must be greater than 0")
        params = {"pageNo": str(page_no), "pageSize": "20", "sort": "1"}
        if ext == "fit":
            params["reqType"] = "0"
        elif ext == "gpx":
            params["reqType"] = "1"
        elif ext == "tcx":
            params["reqType"] = "2"
        else:
            params["reqType"] = "2"
        rsp = self.session.get(QUERY_URL, params=params)
        if not rsp.ok:
            raise Exception(rsp.reason)
        return rsp.json()

    def get_activity_download_url(self, ride_id):
        if not ride_id:
            raise Exception("rideId is empty")
        rsp = self.session.get(DOWNLOAD_URL + str(ride_id))
        if not rsp.ok:
            raise Exception(rsp.reason)
        ret = rsp.json()
        return ret.get("data", "")

    def download_file(self, url, file_name, ext):
        if not url or not file_name:
            raise Exception("url or fileName is empty")
        print("downloading igpsport", file_name, ext)
        folder = TCX_FOLDER
        if ext == "fit":
            folder = FIT_FOLDER
        elif ext == "gpx":
            folder = GPX_FOLDER
        elif ext == "tcx":
            folder = TCX_FOLDER
        else:
            folder = TCX_FOLDER
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"{file_name}.{ext}")
        rsp = requests.get(url)
        if not rsp.ok:
            raise Exception(rsp.reason)
        with open(file_path, "wb") as f:
            f.write(rsp.content)

    def download_type(self, ext):
        if not self.token:
            self.login()
        page = 1
        while True:
            rsp = self.get_activity_list(page, ext)
            rows = rsp.get("data", {}).get("rows", [])
            for row in rows:
                ride_id = row.get("rideId")
                url = self.get_activity_download_url(ride_id)
                self.download_file(url, str(ride_id), ext)
            total_page = rsp.get("data", {}).get("totalPage", 1)
            page += 1
            if page > total_page:
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="igpsport phone number")
    parser.add_argument("password", help="igpsport password")
    parser.add_argument(
        "--token", default="", help="from authorization token for download data"
    )
    parser.add_argument(
        "--with-gpx",
        action="store_true",
        help="get all igpsport data to gpx and download",
    )
    parser.add_argument(
        "--with-tcx",
        action="store_true",
        help="get all igpsport data to tcx and download",
    )
    parser.add_argument(
        "--with-fit",
        action="store_true",
        help="get all igpsport data to fit and download",
    )
    args = parser.parse_args()

    # 如果用户没有指定任何下载类型，只下载 tcx
    if not args.with_gpx and not args.with_tcx and not args.with_fit:
        args.with_tcx = True

    igpsport = IGPSPORT(args.username, args.password, args.token)

    errs = []
    if args.with_fit:
        try:
            igpsport.download_type("fit")
        except Exception as e:
            errs.append(f"fit: {e}")
    if args.with_gpx:
        try:
            igpsport.download_type("gpx")
        except Exception as e:
            errs.append(f"gpx: {e}")
    if args.with_tcx:
        print("type empty or tcx unsupportted yet")
        parser.print_usage()
        sys.exit(1)

    if errs:
        for e in errs:
            print("error:", e, file=sys.stderr)
        sys.exit(2)

    print("done")
