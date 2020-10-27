import argparse
import os
import time
from subprocess import call

from config import GPX_FOLDER, JSON_FILE, SQL_FILE
from utils import make_activities_file

runstastic_command_str = "runtastic -e {email} -p {password} -o {output} -t {last_time}"


def run_sync_command(email, password, output=GPX_FOLDER, last_time=0):
    try:
        call(
            runstastic_command_str.format(
                email=email, password=password, output=output, last_time=str(last_time)
            ).split()
        )
    except:
        pass


def get_last_time():
    try:
        file_names = os.listdir(GPX_FOLDER)
        last_time = max(int(i.split(".")[0]) for i in file_names if not i.startswith("."))
    except:
        last_time = 0
    return last_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="email of runstastic")
    parser.add_argument("password", help="password of runstastic")
    options = parser.parse_args()
    last_time = get_last_time()
    run_sync_command(options.email, options.password, last_time=last_time)
    # for gpx generation change sleep time here
    time.sleep(2)

    make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE)
