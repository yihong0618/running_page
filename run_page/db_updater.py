from generator.db import init_db, Activity
from config import SQL_FILE
import sqlalchemy
from sqlalchemy import text
from config import GPX_FOLDER, JSON_FILE
from utils import make_activities_file


def add_column_elevation_gain(session):
    # check if column elevation_gain is already added
    # if not add it to the db
    try:
        session.query(Activity).first()
        print("column elevation_gain already added, skipping")
    except sqlalchemy.exc.OperationalError:
        sql_statement = 'alter TABLE "activities" add column elevation_gain Float after average_heartrate'
        session.execute(text(sql_statement))
        print("column elevation_gain added successfully")


if __name__ == "__main__":
    session = init_db(SQL_FILE)
    add_column_elevation_gain(session)
    # regenerate activities
    make_activities_file(SQL_FILE, GPX_FOLDER, JSON_FILE)
