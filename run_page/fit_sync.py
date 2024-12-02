"""
If you do not want bind any account
Only the gpx files in GPX_OUT sync
"""

from config import JSON_FILE, SQL_FILE, FIT_FOLDER

from utils import make_activities_file

if __name__ == "__main__":
    print("only sync fit files in FIT_OUT")
    make_activities_file(SQL_FILE, FIT_FOLDER, JSON_FILE, "fit")
