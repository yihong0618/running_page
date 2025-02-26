import argparse
import garth

import argparse
import asyncio
import os
from datetime import datetime
from tcxreader.tcxreader import TCXReader
from config import TCX_FOLDER
from garmin_sync import Garmin
import xml.etree.ElementTree as ET
import json

#生成Garmin的secret_string
def get_garmin_secret(email, password):
    parser = argparse.ArgumentParser()
    parser.add_argument("email", nargs="?", help="email of garmin")
    parser.add_argument("password", nargs="?", help="password of garmin")
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin accout is cn",
    )
    options = parser.parse_args()
    if options.is_cn:
        garth.configure(domain="garmin.cn")
    garth.login(options.email, options.password)
    secret_string = garth.client.dumps()
    return secret_string




# def get_to_generate_files(last_time):
#     """
#     return to one sorted list for next time upload
#     """
#     file_names = os.listdir(TCX_FOLDER)
#     tcx = TCXReader()
#     tcx_files = [
#         (
#             tcx.read(os.path.join(TCX_FOLDER, i), only_gps=False),
#             os.path.join(TCX_FOLDER, i),
#         )
#         for i in file_names
#         if i.endswith(".tcx")
#     ]
#     tcx_files_dict = {
#         int(i[0].trackpoints[0].time.timestamp()): i[1]
#         for i in tcx_files
#         if len(i[0].trackpoints) > 0
#         and int(i[0].trackpoints[0].time.timestamp()) > last_time
#     }

#     dict(sorted(tcx_files_dict.items()))

#     return tcx_files_dict.values()

def read_last_time(file_path):
    """读取last_time配置文件"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            last_time_str = data.get('last_time', '2025-02-01T00:00:00Z')
            
            
            last_dt = datetime.strptime(last_time_str, "%Y-%m-%dT%H:%M:%SZ")
            
            return last_dt
    except (FileNotFoundError, json.JSONDecodeError):
        return datetime(2025, 2, 1, 0, 0, 0)

def write_last_time(file_path, last_time_str):
    """写入新的时间配置"""
    data = {
        
        'last_time': last_time_str

    }
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"写入时间文件失败: {e}")


def get_to_generate_files(last_time):
    # TCX_FOLDER = "/path/to/tcx/files"  # 替换为实际路径

    
    tcx_files_dict = {}
    Json_file=os.path.join(TCX_FOLDER, "Last_date.json")
    if last_time==0:
        last_time = read_last_time(Json_file)
    # 遍历所有tcx文件
    for file_name in os.listdir(TCX_FOLDER):
        if file_name.endswith(".tcx"):
            file_path = os.path.join(TCX_FOLDER, file_name)
            tcx_date = ET.parse(file_path).getroot()[0][0][0]
            
            # 提取所有符合条件的Activity
           
            try:
                activity_dt = datetime.strptime(tcx_date.text.strip(), '%Y-%m-%dT%H:%M:%SZ')
                if activity_dt> last_time:
                    # activity_timestamp = int(activity_dt.timestamp())
                    tcx_files_dict[file_path] = tcx_date.text.strip()
            except:
                continue  # 忽略格式错误的Id
            
    if tcx_files_dict:
        new_date = max(tcx_files_dict.values())
        # new_date = max(tcx_files_dict, key=lambda k: tcx_files_dict[k][1]) if tcx_files_dict else None
        write_last_time(Json_file,new_date)
    else:
    # 这里添加"不处理"的逻辑，例如：
        pass  # 或者设置默认值       
    
    
    # 返回排序后的结果
    return dict(sorted(tcx_files_dict.items()))
    


async def upload_tcx_files_to_garmin(options):
    print("Need to load all tcx files maybe take some time")
    garmin_auth_domain = "CN" if options.is_cn else ""
    if options.is_cn:
        garth.configure(domain="garmin.cn")
    garth.login(options.email, options.password)
    secret_string = garth.client.dumps()
    garmin_client = Garmin(secret_string, garmin_auth_domain)

    last_time = 0
    if not options.all:
        print("upload new tcx to Garmin")
        last_activity = await garmin_client.get_activities(0, 1)
        if not last_activity:
            print("no garmin activity")
        else:
            after_datetime_str = last_activity[0]["startTimeGMT"]
            after_datetime = datetime.strptime(after_datetime_str, "%Y-%m-%d %H:%M:%S")
            last_time = datetime.timestamp(after_datetime)
    else:
        print("Need to load all tcx files maybe take some time")
    to_upload_dict = get_to_generate_files(last_time)

    await garmin_client.upload_activities_files(to_upload_dict)


if __name__ == "__main__":
    if not os.path.exists(TCX_FOLDER):
        os.mkdir(TCX_FOLDER)
    parser = argparse.ArgumentParser()
    parser.add_argument("email", nargs="?", help="email of garmin")
    parser.add_argument("password", nargs="?", help="password of garmin")
    parser.add_argument(
        "--all",
        dest="all",
        action="store_true",
        help="if upload to strava all without check last time",
    )
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin account is cn",
    )
    
    # parser = argparse.ArgumentParser()
    # parser.add_argument("email", nargs="?", help="email of garmin")
    # parser.add_argument("password", nargs="?", help="password of garmin")
   
    options = parser.parse_args()
    
    
    
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(upload_tcx_files_to_garmin(parser.parse_args()))
    loop.run_until_complete(future)

