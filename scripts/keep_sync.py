import requests
import base64
import zipfile
import json


# string strart with `H4sIAAAAAAAA`

# need to test
RUN_DATA_API = "https://api.gotokeep.com/pd/v3/stats/detail?dateUnit=all&type=running"
RUN_LOG_API = "https://api.gotokeep.com/pd/v3/runninglog/{run_id}"

data = {"mobile": "", "password": ""}
login = "https://api.gotokeep.com/v1.1/users/login"

headers =  {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
s = requests.Session()

r = s.post(login, headers=headers, data=data)

token = r.json()["data"]["token"]

headers["Authorization"] = f"Bearer {token}"

