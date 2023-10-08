import sqlite3

try:
    import pandas as pd
except:
    raise Exception("please install pandas run: pip3 install pandas")
from math import floor

data = sqlite3.connect("run_page/data.db")
df = pd.read_sql_query("SELECT * FROM activities", data)


def apply_duration_time(d):
    try:
        return d.split()[1].split(".")[0]
    except:
        return ""


# we do not need polyline in csv
df = df.drop("summary_polyline", axis=1)
df["elapsed_time"] = df["elapsed_time"].apply(apply_duration_time)
df["moving_time"] = df["moving_time"].apply(apply_duration_time)


def format_pace(d):
    if not d:
        return "0"
    pace = (1000.0 / 60.0) * (1.0 / d)
    minutes = floor(pace)
    seconds = floor((pace - minutes) * 60.0)
    return f"{minutes}''{seconds}"


df["average_speed"] = df["average_speed"].apply(format_pace)
df = df.sort_values(by=["start_date"])

df.to_csv("data.csv")
