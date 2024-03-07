import argparse
import asyncio
import hashlib
import logging
import os
import time

import aiofiles
import httpx

from config import JSON_FILE, SQL_FILE, FIT_FOLDER
from utils import make_activities_file

logging.getLogger("asyncio").setLevel(logging.ERROR)  # 只显示错误级别的日志

COROS_URL_DICT = {
    "LOGIN_URL": "https://teamcnapi.coros.com/account/login",
    "DOWNLOAD_URL": "https://teamcnapi.coros.com/activity/detail/download",
    "ACTIVITY_LIST": "https://teamcnapi.coros.com/activity/query?&modeList=100,102,103",  # 100: 跑步，101: 跑步机, 102: 运动场, 103: 越野
}

TIME_OUT = httpx.Timeout(240.0, connect=360.0)

class Coros:
    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.headers = None
        self.req = None  # 这里先不初始化 httpx.AsyncClient，等登录后再初始化

    async def login(self):
        url = COROS_URL_DICT.get("LOGIN_URL")
        headers = {
            "authority": "teamcnapi.coros.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json;charset=UTF-8",
            "dnt": "1",
            "origin": "https://t.coros.com",
            "referer": "https://t.coros.com/",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        data = {"account": self.account, "accountType": 2, "pwd": self.password}
        async with httpx.AsyncClient(timeout=TIME_OUT) as client:
            response = await client.post(url, json=data, headers=headers)
            resp_json = response.json()
            access_token = resp_json["data"]["accessToken"]
            self.headers = {
                "accesstoken": access_token,
                "cookie": f"CPL-coros-region=2; CPL-coros-token={access_token}",
            }
            self.req = httpx.AsyncClient(timeout=TIME_OUT, headers=self.headers)
        await client.aclose()

    async def init(self):
        await self.login()

    async def fetch_activity_ids(self):
        page_number = 1
        all_activities_ids = []

        while True:
            url = f"{COROS_URL_DICT.get('ACTIVITY_LIST')}&pageNumber={page_number}&size=20"
            response = await self.req.get(url)
            data = response.json()
            activities = data.get("data", {}).get("dataList", None)
            if not activities:
                break  # 如果当前页面没有活动，结束循环
            for activity in activities:
                label_id = activity["labelId"]
                all_activities_ids.append(label_id)

            page_number += 1  # 准备获取下一个页面的数据

        return all_activities_ids

    async def download_activity(self, label_id):
        download_folder = FIT_FOLDER
        download_url = f"{COROS_URL_DICT.get('DOWNLOAD_URL')}?labelId={label_id}&sportType=100&fileType=4"
        response = await self.req.post(download_url)
        time.sleep(1)  # 避免请求过快，本地可注释
        resp_json = response.json()
        file_url = resp_json["data"]["fileUrl"]
        fname = os.path.basename(file_url)
        file_path = os.path.join(download_folder, fname)

        try:
            async with self.req.stream("GET", file_url) as response:
                response.raise_for_status()
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
        except httpx.HTTPStatusError as exc:
            print(
                f"Failed to download {file_url} with status code {response.status_code}: {exc}"
            )
            return None, None
        except Exception as exc:
            print(f"Error occurred while downloading {file_url}: {exc}")
            return None, None

        return label_id, fname


def get_downloaded_ids(folder):
    return [i.split(".")[0] for i in os.listdir(folder) if not i.startswith(".")]


async def download_and_generate(account, password):
    folder = FIT_FOLDER
    downloaded_ids = get_downloaded_ids(folder)
    coros = Coros(account, password)
    await coros.init()

    activity_ids = await coros.fetch_activity_ids()
    print("activity_ids: ", len(activity_ids))
    print("downloaded_ids: ", len(downloaded_ids))
    to_generate_coros_ids = list(set(activity_ids) - set(downloaded_ids))
    print("to_generate_activity_ids: ", len(to_generate_coros_ids))

    async def download_task(label_id):
        return await coros.download_activity(label_id)

    tasks = [download_task(label_id) for label_id in to_generate_coros_ids]
    await asyncio.gather(*tasks)
    await coros.req.aclose()
    # 处理图片
    make_activities_file(SQL_FILE, FIT_FOLDER, JSON_FILE, "fit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("account", nargs="?", help="input coros account")

    parser.add_argument("password", nargs="?", help="input coros  password")
    options = parser.parse_args()

    account = options.account
    password = options.password
    encrypted_pwd = hashlib.md5(password.encode()).hexdigest()

    asyncio.run(download_and_generate(account, encrypted_pwd))
