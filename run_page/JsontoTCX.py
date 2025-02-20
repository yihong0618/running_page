import os
import json
import time
import xml.etree.ElementTree as ET
from utils import adjust_time_to_utc, adjust_timestamp_to_utc, to_date
from datetime import datetime, timedelta
from xml.dom import minidom
from tzlocal import get_localzone
import numpy as np
import random


# Forerunner 945?
CONNECT_API_PART_NUMBER = "006-D2449-00"

# getting content root directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)

RUNDATA_FOLDER=os.path.join(parent, "RUN_DATA")


codoon_folder = os.path.join(RUNDATA_FOLDER, 'Codoon')
codoon_tcx_folder = os.path.join(RUNDATA_FOLDER, 'Codoon_TCX')
codoon_done_folder = os.path.join(RUNDATA_FOLDER, 'Codoon_Done')
codoon_fail_folder = os.path.join(RUNDATA_FOLDER, 'Codoon_Fail')


        
# TCX和Codoon运动类型的映射关系
TCX_TYPE_DICT = {
    0: "Hiking",
    1: "Running",
    2: "Biking",
    5:  "Hiking",
}
#每条运动类型包含的数据
FitType = np.dtype(
    {
        "names": [
            "time",
            "bpm",
            "lati",
            "longi",
            "elevation",
            "distance",
            "speed",
            "cadence",
            "watts",
        ],  # unix timestamp, heart bpm, LatitudeDegrees, LongitudeDegrees, elevation
        "formats": ["i", "S4", "S32", "S32", "S8", "S32", "S32", "S8", "S8"],
    }
)




def formated_input(    run_data, run_data_label, tcx_label):  
    # load run_data from run_data_label, parse to tcx_label, return xml node
    fit_data = str(run_data[run_data_label])
    chile_node = ET.Element(tcx_label)
    chile_node.text = fit_data
    return chile_node

def set_array(fit_array, array_time, array_bpm, array_lati, array_longi, elevation,distance,speed,cadence,watts):
  
    fit_data = np.array(
        (array_time, array_bpm, array_lati, array_longi, elevation,distance,speed,cadence,watts), dtype=FitType
    )
    if fit_array is None:
        fit_array = np.array([fit_data], dtype=FitType)
    else:
        fit_array = np.append(fit_array, fit_data)
    return fit_array
    
 
            
def tcx_output(fit_array, run_data,filename):
    """
    If you want to make a more detailed tcx file, please refer to oppo_sync.py
    """
    # route ID
    # fit_id = str(run_data["id"])
    # local time
    fit_start_time_local = run_data["start_time"]
    # zulu time
    utc = adjust_time_to_utc(to_date(fit_start_time_local), str(get_localzone()))
    fit_start_time = utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Root node
    training_center_database = ET.Element(
        "TrainingCenterDatabase",
        {
            "xmlns": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
            "xmlns:ns5": "http://www.garmin.com/xmlschemas/ActivityGoals/v1",
            "xmlns:ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
            "xmlns:ns2": "http://www.garmin.com/xmlschemas/UserProfile/v2",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:ns4": "http://www.garmin.com/xmlschemas/ProfileExtension/v1",
            "xsi:schemaLocation": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd",
        },
    )
    # xml tree
    ET.ElementTree(training_center_database)
    # Activities
    activities = ET.Element("Activities")
    training_center_database.append(activities)
    # sport type
    sports_type = TCX_TYPE_DICT.get(run_data["sports_type"])
    # activity
    activity = ET.Element("Activity", {"Sport": sports_type})
    activities.append(activity)
    
    
    #   Id
    activity_id = ET.Element("Id")
    activity_id.text = fit_start_time  # Codoon use start_time as ID
    activity.append(activity_id)
    #   Creator
    activity_creator = ET.Element("Creator", {"xsi:type": "Device_t"})
    activity.append(activity_creator)
    #       Name
    activity_creator_name = ET.Element("Name")
    activity_creator_name.text = "Codoon"
    activity_creator.append(activity_creator_name)
    activity_creator_product = ET.Element("ProductID")
    activity_creator_product.text = "3441"
    activity_creator.append(activity_creator_product)
    #   Lap
    activity_lap = ET.Element("Lap", {"StartTime": fit_start_time})
    activity.append(activity_lap)
    #       TotalTimeSeconds
    activity_lap.append(formated_input(run_data, "total_time", "TotalTimeSeconds"))
    #       DistanceMeters
    activity_lap.append(formated_input(run_data, "total_length", "DistanceMeters"))
      #       MaximumSpeed
    maximum_speed = ET.Element("MaximumSpeed")
    maximum_speed.text = str(run_data["MaxToPreviousSpeed"]*1000/3600) #  km/h  to m/s
    activity_lap.append(maximum_speed)

    #       Calories
    calories = ET.Element("Calories")
    calories.text = str(int(run_data["total_calories"]))
    activity_lap.append(calories)
    
    # activity_lap.append(formated_input(run_data, "total_calories", "Calories"))
    
    #average heartratebpm
    average_heartratebpm = ET.Element("AverageHeartRateBpm")
    average_heartratebpm_value = ET.Element("Value")
     #maximum heartratebpm
    maximum_heartratebpm = ET.Element("MaximumHeartRateBpm")
    maximum_heartratebpm_value = ET.Element("Value")
    if "hrdevice"  in run_data:
        average_heartratebpm_value.text = str(run_data["hrdevice"]["heart_ext"]["avg"])
        maximum_heartratebpm_value.text = str(run_data["hrdevice"]["heart_ext"]["max"])
    else:
        average_heartratebpm_value.text = str("150")
        maximum_heartratebpm_value.text= str("160")
        
    
    average_heartratebpm.append(average_heartratebpm_value)
    activity_lap.append(average_heartratebpm)
    
   
    
    maximum_heartratebpm.append(maximum_heartratebpm_value)
    activity_lap.append(maximum_heartratebpm)
    
    #Intensity
    intensity = ET.Element("Intensity")
    intensity.text = str("Active")
    activity_lap.append(intensity)

    # TriggerMethod
    trigger_method = ET.Element("TriggerMethod")
    trigger_method.text = str("Manual")
    activity_lap.append(trigger_method)
    
    #Extensions
    extensions = ET.Element("Extensions")
    activity_lap.append(extensions)
    #   TPX
    lx = ET.Element("ns3:LX")
    extensions.append(lx)
    #     RunSpeed
    avg_speed = ET.Element("ns3:AvgSpeed")
    avg_speed.text = str(run_data["AverageSpeed"]*1000/3600) #  km/h  to m/s
    lx.append(avg_speed)

    #       AverageRunCadence
    average_run_cadence = ET.Element("ns3:AvgRunCadence")
    if "average_step_cadence"  in run_data:
        average_run_cadence.text = str(int(run_data["average_step_cadence"]/2))
    else:
        average_run_cadence.text = str("90") #perhaps need divide by 2
    lx.append(average_run_cadence)
    #maximum run cadence
    maximum_run_cadence = ET.Element("ns3:MaxRunCadence")
    if "max_step_cadence" in run_data:
        maximum_run_cadence.text = str(int(run_data["max_step_cadence"])/2)
    else:
        maximum_run_cadence.text  = str("95")
    lx.append(maximum_run_cadence)
    
    if fit_array is not None:
    # Track
        track = ET.Element("Track")
        activity_lap.append(track)
        for i in fit_array:
            tp = ET.Element("Trackpoint")
            track.append(tp)
            # Time
            time_stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime(i["time"]))
            time_label = ET.Element("Time")
            time_label.text = time_stamp
            tp.append(time_label)
            # HeartRateBpm
            # None was converted to bytes by np.dtype, becoming a string "None" after decode...-_-
            # as well as LatitudeDegrees and LongitudeDegrees below
            if not bytes.decode(i["bpm"]) == "None":
                bpm = ET.Element("HeartRateBpm")
                bpm_value = ET.Element("Value")
                bpm.append(bpm_value)
                bpm_value.text = bytes.decode(i["bpm"])
                tp.append(bpm)
            # Position
            if not bytes.decode(i["lati"]) == "None":
                position = ET.Element("Position")
                tp.append(position)
                #   LatitudeDegrees
                lati = ET.Element("LatitudeDegrees")
                lati.text = bytes.decode(i["lati"])
                position.append(lati)
                #   LongitudeDegrees
                longi = ET.Element("LongitudeDegrees")
                longi.text = bytes.decode(i["longi"])
                position.append(longi)
                #  AltitudeMeters
                altitude_meters = ET.Element("AltitudeMeters")
                altitude_meters.text = bytes.decode(i["elevation"])
                tp.append(altitude_meters)
            if not bytes.decode(i["distance"]) == "None":
                distance_meters = ET.Element("DistanceMeters")
                distance_meters.text = bytes.decode(i["distance"])
                tp.append(distance_meters)
            # add extensions  
            if  (not bytes.decode(i["speed"]) == "None") or (not bytes.decode(i["cadence"]) == "None") or (not bytes.decode(i["watts"]) == "None"):
                extensions = ET.Element("Extensions")
                tp.append(extensions)
                tpx = ET.Element("ns3:TPX")
                extensions.append(tpx)
                if not bytes.decode(i["speed"]) == "None":
                    speed = ET.Element("ns3:Speed")
                    speed.text = bytes.decode(i["speed"])
                    tpx.append(speed)
                    
                if not bytes.decode(i["cadence"]) == "None":
                    cadence = ET.Element("ns3:RunCadence")
                    cadence.text = bytes.decode(i["cadence"])
                    tpx.append(cadence)
                if not bytes.decode(i["watts"]) == "None":
                    power = ET.Element("ns3:Watts")
                    power.text = bytes.decode(i["watts"])
                    tpx.append(power)
                        
    # Author
    author = ET.Element("Author", {"xsi:type": "Application_t"})
    training_center_database.append(author)
    author_name = ET.Element("Name")
    author_name.text = "Connect Api"
    author.append(author_name)
    author_lang = ET.Element("LangID")
    author_lang.text = "en"
    author.append(author_lang)
    author_part = ET.Element("PartNumber")
    author_part.text = CONNECT_API_PART_NUMBER
    author.append(author_part)
    
    #  生成TCX文件
    start_time = run_data.get('start_time', '')
    in_room = run_data.get('is_in_room', 1)
    if in_room:
        Roomtype = "InRoom"
    else:
        Roomtype = "OutDoor"
    datastr=""
    if fit_array is  None:
        datastr="_NoData"
                
                # 构造新的文件名
    # new_filename = f"{sports_type}_{Roomtype}_{start_time}.json".replace(':', '')
    # 构造新的文件名
    tcx_filename = f"{sports_type}_{Roomtype}_{start_time}{datastr}.tcx".replace(':', '')
    tcx_file_path = os.path.join(codoon_tcx_folder, tcx_filename)
    
    # tree = ET.ElementTree(training_center_database)
    # tree.write(tcx_file_path, encoding='utf-8', xml_declaration=True)

   
    xml_str = minidom.parseString(ET.tostring(training_center_database)).toprettyxml()
    with open(tcx_file_path, "w") as f:
        f.write(str(xml_str))



def tcx_job(run_data,filename):
    # fit struct array
    fit_array = None

    # raw data
    own_heart_rate = None
    own_points = None
    own_steps=None
    steps_per_minute = {}
    default_cadence = 90
    if "average_step_cadence" in run_data:
        default_cadence = int(run_data["average_step_cadence"]/2)
    if "heart_rate" in run_data:
        own_heart_rate = run_data["heart_rate"]  # bpm key-value
    if "points" in run_data:
        own_points = run_data["points"]  # track points
    if "user_steps_list_perm" in run_data:
        own_steps = run_data["user_steps_list_perm"]  # steps key-value
    
    # get single bpm
    if own_steps is not None:
        for stepinfo in own_steps:
            time_str = stepinfo[0]
            steps = int(stepinfo[1])
            # 将时间字符串转换为 datetime 对象
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            # 提取分钟信息作为键
            key = dt.strftime("%Y-%m-%d %H:%M")
            steps = int(steps/2)
            steps_per_minute[key] = steps
            
            
    if own_heart_rate is not None:
        heartcount = len(own_heart_rate)-1 # 数据长度
        if heartcount==0:
            heartcount=1
        i=0
        avgdistance=run_data["total_length"]/heartcount #平均每次的距离
        distance=0
        speed=0
        pretime=0
        watts=0
        # pretime=own_heart_rate[0][0]
        for single_time, single_bpm in own_heart_rate.items():
            single_time_utc = adjust_timestamp_to_utc(single_time, str(get_localzone()))
            # set bpm data
            step_time=datetime.fromtimestamp(int(single_time)).strftime("%Y-%m-%d %H:%M")
            cadence = default_cadence
            
            # speed=run_data["AverageSpeed"]*1000/3600 #计算平均速度
            if own_steps is not None:
                # 找到与当前时间最接近的步频数据
                
                if step_time in steps_per_minute:
                    # 如果找到对应的步频，则赋值
                    cadence = steps_per_minute[step_time]
            # fit_array = set_array(fit_array, single_time_utc, single_bpm, None, None, None, None, None, None, None)
            
            if own_points is not None and len(own_points)>0: #有轨迹，则只添加步频
                fit_array = set_array(fit_array, single_time_utc, single_bpm, None, None, None, None, None, cadence, None)
            else:
                pointdistance=round(avgdistance*random.uniform(0.95,1.05),4) #计算每次的距离
                if pretime!=0:
                    speed=round(pointdistance/(int(single_time)-int(pretime)),3) #计算速度
                    watts=int(float(speed)*55*9.8*0.2) #计算功率
                fit_array = set_array(fit_array, single_time_utc, single_bpm, None, None, None, None, speed, cadence, watts)
                
                distance+=pointdistance #计算截止到当前时间的总距离
                i+=1
                if i==heartcount:
                    distance=run_data["total_length"] #计算截止到当前时间的总距离
                
                pretime=int(single_time) #上一次的时间   
             
    # get single track point
    if own_points is not None:
        for point in own_points:
            repeat_flag = False
            # TODO add elevation information
            time_stamp_local = point.get("time_stamp")
            latitude = point.get("latitude")
            longitude = point.get("longitude")
            elevation = point.get("elevation")
            speed=point.get("topreviousspeed")
            distance=point.get("tostartdistance") #这里看deepseek解释说要选截止起点总距离
            cadence = default_cadence
            if run_data["sports_type"] == 2:
               F_rolling=3.14
               F_air=0.245*(float(speed))**2
               watts=int((F_rolling+F_air)*float(speed)) #计算功率 
            else:
                C = 0.2  # 水平阻力系数（建议范围0.1-0.3）
                watts=int(float(speed)*55*9.8*C) #计算功率
            
            # move to UTC
            utc = adjust_time_to_utc(to_date(time_stamp_local), str(get_localzone()))
            time_stamp = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            # to time array
            time_array = time.strptime(time_stamp, "%Y-%m-%dT%H:%M:%SZ")
            # to unix timestamp
            unix_time = int(time.mktime(time_array))
            
            #如果有步频数据就加上步频
            if own_steps is not None:
                # 找到与当前时间最接近的步频数据
                dt = to_date(time_stamp_local)
                # 提取分钟信息作为键
                key = dt.strftime("%Y-%m-%d %H:%M")
                if key in steps_per_minute:
                    # 如果找到对应的步频，则赋值
                    cadence = steps_per_minute[key]
                
            
            # set GPS data
            # if the track point which has the same time has been added
            if fit_array is None:
                fit_array = set_array(
                    fit_array, unix_time, None, latitude, longitude, elevation,distance,speed,cadence,watts
                )
            else:
                for i in fit_array:
                    if i["time"] == unix_time:
                        i["lati"] = latitude
                        i["longi"] = longitude
                        i["elevation"] = elevation
                        i["distance"] = distance
                        i["speed"] = speed
                        i["cadence"] = cadence
                        i["watts"] = watts
                        repeat_flag = True  # unix_time repeated
                        break
                if not repeat_flag:
                    fit_array = set_array(
                        fit_array, unix_time, None, latitude, longitude, elevation,distance,speed,cadence,watts
                    )

    # if fit_array is not None:
        # order array
        fit_array = np.sort(fit_array, order="time")
        # write to TCX file
    try:
        tcx_output(fit_array, run_data,filename)
        return True
    except Exception as e:
        
        print(f"处理 {filename} 失败: {e}")
        return False
    # else:
    #     print(f"No data in {filename} " )
    #     return True

def rename_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            json_file_path = os.path.join(folder_path, filename)
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 提取start_time字段
            start_time = data.get('start_time', '')
            sports_type = TCX_TYPE_DICT.get(data["sports_type"])
            
            # 构造新的文件名
            new_filename = f"{start_time}_{sports_type}.json".replace(':', '')
            # 构造新的文件路径
            new_file_path = os.path.join(folder_path, new_filename)

            # 重命名文件
            os.rename(json_file_path, new_file_path)
            print(f"重命名 {filename} 为 {new_filename}")
            
            
if __name__ == "__main__":
# 遍历Codoon文件夹下的所有JSON文件
    # 创建必要的文件夹
    for folder in [codoon_tcx_folder, codoon_done_folder, codoon_fail_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    for filename in os.listdir(codoon_folder):
        if filename.endswith('.json'):
            json_file_path = os.path.join(codoon_folder, filename)
        
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            result=tcx_job(data["data"],filename)
            # 处理JSON数据  
            if len(data["data"])>0:
                start_time = data["data"].get('start_time', '')
                sports_type = TCX_TYPE_DICT.get(data["data"]["sports_type"])
                in_room = data["data"].get('is_in_room', 1)
                if in_room:
                    Roomtype = "InRoom"
                else:
                    Roomtype = "OutDoor"
                
                # 构造新的文件名
                new_filename = f"{sports_type}_{Roomtype}_{start_time}.json".replace(':', '')
            
            
            else:
                new_filename = filename
            # 构造新的文件路径
            

        
            if result:
            # 将处理成功的JSON文件移动到Codoon_Done文件夹
            
                done_file_path = os.path.join(codoon_done_folder, new_filename)
                if not os.path.exists(done_file_path):
                    os.rename(json_file_path, done_file_path)
                print(f"成功处理 {filename}")
            else:
                # 将处理失败的JSON文件移动到Codoon_Fail文件夹
                fail_file_path = os.path.join(codoon_folder, new_filename)
                os.rename(json_file_path, fail_file_path)
                