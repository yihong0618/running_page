import requests
import base64
import zipfile
import zlib
import json
from pprint import pprint

from requests.sessions import session


""" test run id
5f0b0558650b9c74c049e911_9223370434084248807_rn
5f0b0558650b9c74c049e911_9223370434180463807_rn
5f0b0558650b9c74c049e911_9223370434256157807_rn
5f0b0558650b9c74c049e911_9223370434348312807_rn
5f0b0558650b9c74c049e911_9223370434608873807_rn
"""

# need to test
LOGIN_API = "https://api.gotokeep.com/v1.1/users/login"
RUN_DATA_API = "https://api.gotokeep.com/pd/v3/stats/detail?dateUnit=all&type=running"
RUN_LOG_API = "https://api.gotokeep.com/pd/v3/runninglog/{run_id}"

def login(session, mobile, passowrd):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
    data =  {"mobile": mobile, "password": passowrd}
    r = s.post(LOGIN_API, headers=headers, data=data)
    if r.ok:
        token = r.json()["data"]["token"]
        headers["Authorization"] = f"Bearer {token}"
        return session, headers


def get_to_download_runs_ids(session, headers):
    r = session.get(RUN_DATA_API, headers=headers)
    if r.ok:
        run_logs = r.json()["data"]["records"]
        return [i["logs"][0]["stats"]["id"] for i in run_logs]


def get_single_run_data(session, headers, run_id):
    r = session.get(RUN_LOG_API.format(run_id=run_id), headers=headers)
    if r.ok:
        return r.json()


def parse_raw_run_data(run_data):
    raw_data_url = run_data["data"]["rawDataURL"]
    raw_data_url = "http://www.baidu.com"
    start_time = run_data["data"]["startTime"]
    print(start_time)
    print(raw_data_url)
    r = req_proxy.generate_proxied_request(raw_data_url)
    try:
        return r.text
    except:
        pass
    # string strart with `H4sIAAAAAAAA`
    # run_points_data = zlib.decompress(base64.b64decode(r.text), 16+zlib.MAX_WBITS)
    # run_points_data = json.loads(run_points_data)
    # print(run_points_data[0])
    


if __name__ == "__main__":
    s = requests.Session()
    s.verify = False
    s, headers = login(s, "", "")
    runs = get_to_download_runs_ids(s, headers)
    for i in range(len(runs)):
        run_data = get_single_run_data(s, headers, runs[i])
        print(parse_raw_run_data(run_data))
