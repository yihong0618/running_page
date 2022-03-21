from config import GPX_FOLDER, JSON_FILE, SQL_FILE, config

from utils import make_activities_file_only

if __name__ == "__main__":
    make_activities_file_only(SQL_FILE, GPX_FOLDER, JSON_FILE)
