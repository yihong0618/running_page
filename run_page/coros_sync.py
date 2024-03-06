import argparse
import asyncio
import hashlib
import logging
import os

import aiohttp

from config import JSON_FILE, SQL_FILE, FIT_FOLDER
from utils import make_activities_file

logger = logging.getLogger(__name__)

COROS_URL_DICT = {
    "LOGIN_URL": "https://teamcnapi.coros.com/account/login",
    "DOWNLOAD_URL": "https://teamcnapi.coros.com/activity/detail/download",
    "ACTIVITY_LIST": "https://teamcnapi.coros.com/activity/query?&modeList=100,102,103",  # 100: 跑步，101: 跑步机, 102: 运动场, 103: 越野
}


class Coros:
    def __init__(self, headers, access_token):
        headers.update(
            {
                "accesstoken": access_token,
                "cookie": f"CPL-coros-region=2; CPL-coros-token={access_token}",
            }
        )

        self.headers = headers

    @staticmethod
    async def login(account, password):
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
        data = {"account": account, "accountType": 2, "pwd": password}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                resp_json = await response.json()
                access_token = resp_json["data"]["accessToken"]
                return Coros(headers, access_token)

    async def fetch_activity_ids(self, session):
        page_number = 1
        all_activities_ids = []

        while True:
            url = f"{COROS_URL_DICT.get('ACTIVITY_LIST')}&pageNumber={page_number}&size=20"
            headers = self.headers

            async with session.get(url, headers=headers) as response:
                data = await response.json()
                activities = data.get("data", {}).get("dataList", None)
                if not activities:
                    break  # 如果当前页面没有活动，结束循环
                for activity in activities:
                    label_id = activity["labelId"]
                    all_activities_ids.append(label_id)

                page_number += 1  # 准备获取下一个页面的数据

        return all_activities_ids

    async def download_activity(self, session, label_id):
        download_folder = FIT_FOLDER
        download_url = f"{COROS_URL_DICT.get('DOWNLOAD_URL')}?labelId={label_id}&sportType=100&fileType=4"
        headers = self.headers
        async with session.post(download_url, headers=headers) as response:
            resp_json = await response.json()
            file_url = resp_json["data"]["fileUrl"]
            fname = os.path.basename(file_url)
            async with session.get(file_url) as res:
                if res.status == 200:
                    file_path = os.path.join(download_folder, fname)
                    with open(file_path, "wb") as f:
                        while True:
                            chunk = await res.content.read(4096)
                            if not chunk:
                                break
                            f.write(chunk)
                    return label_id, fname
        return None, None


def get_downloaded_ids(folder):
    return [i.split(".")[0] for i in os.listdir(folder) if not i.startswith(".")]


async def download_and_generate(account, password):
    folder = FIT_FOLDER
    downloaded_ids = get_downloaded_ids(folder)
    client = await Coros.login(account, password)

    async with aiohttp.ClientSession() as session:
        activity_ids = await client.fetch_activity_ids(session)
        #  目前个别的 label id 和下载的id可能不一致 导致每次都会下载新的
        print("activity_ids:", len(activity_ids))
        print("downloaded_ids:", len(downloaded_ids))
        # diff downloaded label id,
        to_generate_coros_ids = list(set(activity_ids) - set(downloaded_ids))
        print("to_generate_activity_ids: ", len(to_generate_coros_ids))
        tasks = []
        for label_id in to_generate_coros_ids:
            task = client.download_activity(session, label_id)
            tasks.append(task)
        # 等待所有下载任务完成
        await asyncio.gather(*tasks)
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
