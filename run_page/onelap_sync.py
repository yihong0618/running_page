# some code from
# https://github.com/DreamMryang/synchronizeTheRecordingOfOnelapToGiant.git
# https://github.com/moruoxian/SyncOnelapToXoss.git
# great thanks

import os
import uuid
import hashlib
import time
import argparse
import requests
from config import FIT_FOLDER

SIGNIN_URL = "https://www.onelap.cn/api/login"
ACTIVITY_URL = "https://u.onelap.cn/analysis/list"


class Onelap:
    def __init__(self, account, password):
        self.account = account
        self.password = password

    def login(self):
        nonce = uuid.uuid4().hex[:16]
        timestamp = str(int(time.time()))
        sign = hashlib.md5(
            f"account={self.account}&nonce={nonce}&***".encode()
        ).hexdigest()
        headers = {"nonce": nonce, "timestamp": timestamp, "sign": sign}

        try:
            login_response = requests.post(
                SIGNIN_URL,
                json={
                    "account": self.account,
                    "password": hashlib.md5(self.password.encode()).hexdigest(),
                },
                headers=headers,
            )
            login_response.raise_for_status()
            login_response = login_response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP POST request failed: {e}")

        data = login_response.get("data", [])
        if not data:
            raise RuntimeError(login_response.get("error"))

        return data[0]

    def get_activities(self):
        login_data = self.login()
        token = login_data.get("token")
        refresh_token = login_data.get("refresh_token")
        userinfo = login_data.get("userinfo", {})
        uid = userinfo.get("uid")

        cookies = f"ouid={uid}; XSRF-TOKEN={token}; OTOKEN={refresh_token}"
        headers = {
            "Cookie": cookies,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }

        try:
            activities_response = requests.get(ACTIVITY_URL, headers=headers)
            activities_response.raise_for_status()
            activities_response = activities_response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP GET request failed: {e}")

        activities = activities_response.get("data", [])
        if not activities:
            raise RuntimeError("no data returned.")

        return activities

    def download_onelap_data(self):
        activities = self.get_activities()
        os.makedirs(FIT_FOLDER, exist_ok=True)
        for activity in activities:
            file_key = activity.get("fileKey")
            download_url = activity.get("durl")
            if file_key and download_url:
                response = requests.get(download_url)
                if response.status_code == 200:
                    file_path = os.path.join(FIT_FOLDER, file_key)
                    with open(file_path, "wb") as file:
                        file.write(response.content)
                    print(f"download {file_key}")
                else:
                    print(f"Failed to download {file_key}: {response.status_code}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("account", help="Onelap account")
    parser.add_argument("password", help="Onelap password")
    parser.add_argument(
        "--with-fit",
        dest="with_fit",
        action="store_true",
        help="get all Onelap data to fit and download",
    )
    options = parser.parse_args()

    onelap = Onelap(options.account, options.password)
    onelap.download_onelap_data()
