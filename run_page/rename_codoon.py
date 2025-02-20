import os
import json
import time
import xml.etree.ElementTree as ET
from utils import adjust_time_to_utc, adjust_timestamp_to_utc, to_date
from datetime import datetime, timedelta
from xml.dom import minidom
from tzlocal import get_localzone
import numpy as np


# Forerunner 945?
CONNECT_API_PART_NUMBER = "006-D2449-00"

# getting content root directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)

RUNDATA_FOLDER=os.path.join(parent, "RUN_DATA")


codoon_folder = os.path.join(RUNDATA_FOLDER, 'Tmp')
codoon_tcx_folder = os.path.join(RUNDATA_FOLDER, 'Codoon_TCX')
codoon_done_folder = os.path.join(RUNDATA_FOLDER, 'Codoon_Done')
codoon_fail_folder = os.path.join(RUNDATA_FOLDER, 'Codoon_Fail')

# TCX和Codoon运动类型的映射关系
TCX_TYPE_DICT = {
    0: "Hiking",
    1: "Running",
    2: "Biking",
    5: "Hiking",
}

def rename_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            json_file_path = os.path.join(folder_path, filename)
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if len(data["data"])>0:
            # 提取start_time字段
                start_time = data["data"].get('start_time', '')
                sports_type = TCX_TYPE_DICT.get(data["data"]["sports_type"])
                in_room = data["data"].get('is_in_room', 1)
                if in_room:
                    Roomtype = "InRoom"
                else:
                    Roomtype = "OutDoor"
                
                # 构造新的文件名
                new_filename = f"{sports_type}_{Roomtype}_{start_time}.json".replace(':', '')
                # 构造新的文件路径
                new_file_path = os.path.join(folder_path, new_filename)

                # 重命名文件
                os.rename(json_file_path, new_file_path)
                print(f"重命名 {filename} 为 {new_filename}")
                
if __name__=="__main__":
    rename_files_in_folder(codoon_folder)