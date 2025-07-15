import argparse
import asyncio
import hashlib
import os
import time

import aiofiles
import httpx

from config import JSON_FILE, SQL_FILE, FOLDER_DICT
from utils import make_activities_file

COROS_URL_DICT = {
    "LOGIN_URL": "https://teamcnapi.coros.com/account/login",
    "DOWNLOAD_URL": "https://teamcnapi.coros.com/activity/detail/download",
    "ACTIVITY_LIST": "https://teamcnapi.coros.com/activity/query",
}

COROS_TYPE_DICT = {
    "gpx": 1,
    "fit": 4,
    "tcx": 3,
}


TIME_OUT = httpx.Timeout(240.0, connect=360.0)


class Coros:
    def __init__(self, account, password, is_only_running=False):
        self.account = account
        self.password = password
        self.headers = None
        self.req = None

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
            access_token = resp_json.get("data", {}).get("accessToken")
            if not access_token:
                raise Exception(
                    "============Login failed! please check your account and password==========="
                )
            self.headers = {
                "accesstoken": access_token,
                "cookie": f"CPL-coros-region=2; CPL-coros-token={access_token}",
            }
            self.is_only_running = is_only_running
            self.req = httpx.AsyncClient(timeout=TIME_OUT, headers=self.headers)
        await client.aclose()

    async def init(self):
        await self.login()

    async def fetch_activity_ids_types(self, only_run):
        page_number = 1
        all_activities_ids_types = []

        mode_list_str = "100,101,102,103" if only_run else ""
        while True:
            url = f"{COROS_URL_DICT.get('ACTIVITY_LIST')}?&modeList={mode_list_str}&pageNumber={page_number}&size=20"
            response = await self.req.get(url)
            data = response.json()
            activities = data.get("data", {}).get("dataList", None)
            if not activities:
                break
            for activity in activities:
                label_id = activity["labelId"]
                sport_type = activity["sportType"]
                if label_id is None:
                    continue
                all_activities_ids_types.append([label_id, sport_type])

            page_number += 1

        return all_activities_ids_types

    async def download_activity(self, label_id, sport_type, file_type):
        if sport_type == 101 and file_type == "gpx":
            print(
                f"Sport type {sport_type} is not supported in {file_type} file. The activity will be ignored"
            )
            return None, None
        download_folder = FOLDER_DICT[file_type]
        download_url = (
            f"{COROS_URL_DICT.get('DOWNLOAD_URL')}?labelId={label_id}&sportType={sport_type}"
            f"&fileType={COROS_TYPE_DICT[file_type]}"
        )
        file_url = None
        fname = ""
        file_path = ""
        try:
            response = await self.req.post(download_url)
            resp_json = response.json()
            file_url = resp_json.get("data", {}).get("fileUrl")
            if not file_url:
                print(f"No file URL found for label_id {label_id}")
                return None, None

            fname = os.path.basename(file_url)
            file_path = os.path.join(download_folder, fname)

            async with self.req.stream("GET", file_url) as response:
                response.raise_for_status()
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
            return label_id, fname
        except httpx.HTTPStatusError as exc:
            print(
                f"Failed to download {file_url} with status code {response.status_code}: {exc}"
            )
        except Exception as exc:
            print(f"Error occurred while downloading {file_url}: {exc}")
        if file_path and os.path.exists(file_path):
            print(f"Delete the corrupted fit file: {fname}")
            os.remove(file_path)

        return None, None


def get_downloaded_ids(folder):
    return [i.split(".")[0] for i in os.listdir(folder) if not i.startswith(".")]


async def download_and_generate(account, password, only_run, file_type):
    folder = FOLDER_DICT[file_type]
    downloaded_ids = get_downloaded_ids(folder)
    coros = Coros(account, password)
    await coros.init()
    activity_infos = await coros.fetch_activity_ids_types(only_run=only_run)
    activity_ids = [i[0] for i in activity_infos]
    activity_types = [i[1] for i in activity_infos]
    activity_id_type_dict = dict(zip(activity_ids, activity_types))
    print("activity_ids: ", len(activity_ids))
    print("downloaded_ids: ", len(downloaded_ids))
    to_generate_coros_ids = list(set(activity_ids) - set(downloaded_ids))
    print("to_generate_activity_ids: ", len(to_generate_coros_ids))

    start_time = time.time()
    await gather_with_concurrency(
        10,
        [
            coros.download_activity(
                label_id, activity_id_type_dict[label_id], file_type
            )
            for label_id in to_generate_coros_ids
        ],
    )
    print(f"Download finished. Elapsed {time.time()-start_time} seconds")
    await coros.req.aclose()
    make_activities_file(SQL_FILE, folder, JSON_FILE, file_type)


async def gather_with_concurrency(n, tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("account", nargs="?", help="input coros account")

    parser.add_argument("password", nargs="?", help="input coros password")

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
        default="fit",
        help="to download personal documents or ebook",
    )
    parser.add_argument(
        "--gpx",
        dest="download_file_type",
        action="store_const",
        const="gpx",
        default="fit",
        help="to download personal documents or ebook",
    )
    options = parser.parse_args()

    account = options.account
    password = options.password
    is_only_running = options.only_run
    file_type = options.download_file_type
    file_type = file_type if file_type in ["gpx", "tcx", "fit"] else "fit"
    encrypted_pwd = hashlib.md5(password.encode()).hexdigest()

    asyncio.run(
        download_and_generate(account, encrypted_pwd, is_only_running, file_type)
    )
