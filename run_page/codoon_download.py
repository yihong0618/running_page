import argparse
import base64
from datetime import datetime
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import requests
import re
from config import (
    JSON_FILE,
    SQL_FILE,
    RUNDATA_FOLDER,
)
from generator import Generator
# device info
user_agent = "CodoonSport(8.9.0 1170;Android 7;Sony XZ1)"
did = "24-00000000-03e1-7dd7-0033-c5870033c588"
# May be Forerunner 945?
CONNECT_API_PART_NUMBER = "006-D2449-00"

# fixed params
base_url = "https://api.codoon.com"
davinci = "0"
basic_auth = "MDk5Y2NlMjhjMDVmNmMzOWFkNWUwNGU1MWVkNjA3MDQ6YzM5ZDNmYmVhMWU4NWJlY2VlNDFjMTk5N2FjZjBlMzY="
client_id = "099cce28c05f6c39ad5e04e51ed60704"


# decrypt from libencrypt.so Java_com_codoon_jni_JNIUtils_encryptHttpSignature
# sha1 -> base64
def make_signature(message):
    key = bytes("ecc140ad6e1e12f7d972af04add2c7ee", "UTF-8")
    message = bytes(message, "UTF-8")
    digester = hmac.new(key, message, hashlib.sha1)
    signature1 = digester.digest()
    signature2 = base64.b64encode(signature1)
    return str(signature2, "UTF-8")


def device_info_headers():
    return {
        "accept-encoding": "gzip",
        "user-agent": user_agent,
        "did": did,
        "davinci": davinci,
    }

def maxdate():
        
        codoon_done_folder = os.path.join(RUNDATA_FOLDER, 'Codoon_Done')
        pattern = r'(\d{4}-\d{2}-\d{2}T\d{6})'
        datetime_list = []

        # 遍历文件夹中的所有.json文件
        for filename in os.listdir(codoon_done_folder):
            if filename.endswith('.json'):
                # 使用正则表达式提取日期时间部分
                match = re.search(pattern, filename)
                if match:
                    dt_str = match.group(1)
                    # 转换为datetime对象
                    dt = datetime.strptime(dt_str, '%Y-%m-%dT%H%M%S')
                    datetime_list.append(dt)

        if datetime_list:
            max_dt = max(datetime_list)
        else:
            max_dt = datetime(2025, 1, 1, 0, 0, 0)
        
        return max_dt
       
          
class CodoonAuth:
    def __init__(self, refresh_token=None):
        self.params = {}
        self.refresh_token = refresh_token
        self.token = ""

        if refresh_token:
            session = requests.Session()
            session.headers.update(device_info_headers())
            query = f"client_id={client_id}&grant_type=refresh_token&refresh_token={refresh_token}&scope=user%2Csports"
            r = session.post(
                f"{base_url}/token?" + query,
                data=query,
                auth=self.reload(query),
            )
            if not r.ok:
                print(r.json())
                raise Exception("refresh_token expired")

            self.token = r.json()["access_token"]

    def reload(self, params={}, token=""):
        self.params = params
        if token:
            self.token = token
        return self

    @classmethod
    def __get_signature(cls, token="", path="", body=None, timestamp=""):
        arr = path.split("?")
        path = arr[0]
        query = arr[1] if len(arr) > 1 else ""
        body_str = body if body else ""
        if body is not None and not isinstance(body, str):
            body_str = json.dumps(body)
        if query != "":
            query = urllib.parse.unquote(query)

        pre_string = f"Authorization={token}&Davinci={davinci}&Did={did}&Timestamp={str(timestamp)}|path={path}|body={body_str}|{query}"
        return make_signature(pre_string)

    def __call__(self, r):
        params = self.params
        body = params
        if not isinstance(self.params, str):
            params = self.params.copy()
            body = json.dumps(params)

        sign = ""
        if r.method == "GET":
            timestamp = 0
            r.headers["authorization"] = "Basic " + basic_auth
            r.headers["timestamp"] = timestamp
            sign = self.__get_signature(
                r.headers["authorization"], r.path_url, timestamp=timestamp
            )
        elif r.method == "POST":
            timestamp = int(time.time())
            r.headers["timestamp"] = timestamp
            if "refresh_token" in params:
                r.headers["authorization"] = "Basic " + basic_auth
                r.headers["content-type"] = (
                    "application/x-www-form-urlencode; charset=utf-8"
                )
            else:
                r.headers["authorization"] = "Bearer " + self.token
                r.headers["content-type"] = "application/json; charset=utf-8"
            sign = self.__get_signature(
                r.headers["authorization"], r.path_url, body=body, timestamp=timestamp
            )
            r.body = body

        r.headers["signature"] = sign
        return r


class Codoon:
    def __init__(self, mobile="", password="", refresh_token=None, user_id=""):
        self.mobile = mobile
        self.password = password
        self.refresh_token = refresh_token
        self.user_id = user_id

        self.session = requests.Session()

        self.session.headers.update(device_info_headers())

        self.auth = CodoonAuth(self.refresh_token)
        self.auth.token = self.auth.token

    @classmethod
    def from_auth_token(cls, refresh_token, user_id):
        return cls(refresh_token=refresh_token, user_id=user_id)

    def login_by_phone(self):
        params = {
            "client_id": client_id,
            "email": self.mobile,
            "grant_type": "password",
            "password": self.password,
            "scope": "user",
        }
        r = self.session.get(
            f"{base_url}/token",
            params=params,
            auth=self.auth.reload(params),
        )
        login_data = r.json()
        if login_data.__contains__("status") and login_data["status"] == "Error":
            raise Exception(login_data["description"])
        self.refresh_token = login_data["refresh_token"]
        self.token = login_data["access_token"]
        self.user_id = login_data["user_id"]
        self.auth.reload(token=self.token)
        print(
            f"your refresh_token and user_id are {str(self.refresh_token)} {str(self.user_id)}"
        )
        
    
            

    def get_runs_records(self, page=1):
        payload = {"limit": 500, "page": page, "user_id": self.user_id}
        r = self.session.post(
            f"{base_url}/api/get_old_route_log",
            data=payload,
            auth=self.auth.reload(payload),
        )
        if not r.ok:
            print(r.json())
            raise Exception("get runs records error")

        runs = r.json()["data"]["log_list"]
        
        target_date = maxdate()
        
        runs = [run for run in runs if datetime.strptime(run["start_time"], '%Y-%m-%d %H:%M:%S') >=target_date]
        print(f"{len(runs)} runs to parse")
        if r.json()["data"]["has_more"]:
            return runs + self.get_runs_records(page + 1)
        return runs



    def get_single_run_record(self, route_id):
        print(f"Get single run for codoon id {route_id}")
        payload = {
            "route_id": route_id,
        }
        r = self.session.post(
            f"{base_url}/api/get_single_log",
            data=payload,
            auth=self.auth.reload(payload),
        )
        if not r.ok:
            print(r)
            raise Exception("get runs records error")
        data = r.json()
        file_path = os.path.join(RUNDATA_FOLDER, f"{route_id}.json")
         # 将数据写入 JSON 文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            # print(f"Data saved to {file_path}")
        except Exception as e:
            print(f"Error saving data to {file_path}: {e}")
        
        return data



    def get_tracks(self):
        run_records = self.get_runs_records()


        for i in run_records:
            run_data = self.get_single_run_record(i["route_id"])
            


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mobile_or_token", help="codoon phone number or refresh token")
    parser.add_argument("password_or_user_id", help="codoon password or user_id")
    
    options = parser.parse_args()

    app = Codoon(
        mobile=str(options.mobile_or_token),
        password=str(options.password_or_user_id),
    )
    app.login_by_phone()
    tracks = app.get_tracks()
    


  