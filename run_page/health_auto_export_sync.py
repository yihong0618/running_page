"""Import Health Auto Export Workouts JSON v2 into running_page."""

import argparse
import hashlib
import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import polyline
from config import JSON_FILE, SQL_FILE
from generator import IGNORE_BEFORE_SAVING, Generator
from generator.db import Activity
from polyline_processor import filter_out
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select

# Store ownership separately so existing Activity rows and public JSON need no
# schema changes. An occupied ID without matching ownership is a collision.
workout_ids = Table(
    "health_auto_export_workout_ids",
    MetaData(),
    Column("external_id", String, primary_key=True),
    Column("run_id", Integer, nullable=False, unique=True),
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
RUN_TYPES = {"Running", "Outdoor Run", "Indoor Run", "跑步", "户外 跑步", "室内 跑步"}
INDOOR_TYPES = {"Indoor Run", "室内 跑步"}
DISTANCE_UNITS = {"m": 1, "km": 1000, "mi": 1609.344}


def quantity(value, units):
    number = value["qty"]
    if isinstance(number, bool) or not isinstance(number, (int, float)):
        raise TypeError("Expected a numeric quantity")
    result = number * units[value["units"]]
    if not math.isfinite(result) or result < 0:
        raise ValueError("Expected a finite, non-negative quantity")
    return result


def parse_workout(workout, since):
    start = datetime.strptime(workout["start"], f"{DATE_FORMAT} %z")
    if since is not None and start < since:
        return None

    external_id = workout["id"]
    if not isinstance(external_id, str) or not external_id.strip():
        raise ValueError("Missing workout ID")
    end = datetime.strptime(workout["end"], f"{DATE_FORMAT} %z")
    duration = quantity({"qty": workout["duration"], "units": "s"}, {"s": 1})
    distance = quantity(workout["distance"], DISTANCE_UNITS)
    if end < start or not duration or distance <= 0.1:
        raise ValueError("Expected positive running distance and duration")

    points = [
        (float(point["latitude"]), float(point["longitude"]))
        for point in workout.get("route") or []
    ]
    if any(not (-90 <= lat <= 90 and -180 <= lon <= 180) for lat, lon in points):
        raise ValueError("Invalid route coordinate")
    encoded = polyline.encode(points) if len(points) >= 2 else ""
    if encoded and IGNORE_BEFORE_SAVING:
        encoded = filter_out(encoded) or ""

    indoor = (
        workout.get("isIndoor") is True
        or workout.get("location") in {"Indoor", "室内"}
        or workout["name"] in INDOOR_TYPES
    )
    heart_rate = workout.get("avgHeartRate") or (workout.get("heartRate") or {}).get(
        "avg"
    )
    elevation = workout.get("elevationUp")
    return external_id, {
        "name": "Treadmill Run" if indoor else "Run",
        "type": "Run",
        "subtype": "Treadmill" if indoor else "",
        "distance": distance,
        "moving_time": timedelta(seconds=duration),
        "elapsed_time": end - start,
        "start_date": start.astimezone(UTC).strftime(DATE_FORMAT),
        "start_date_local": start.strftime(DATE_FORMAT),
        "average_speed": distance / duration,
        "average_heartrate": (
            quantity(heart_rate, {"count/min": 1, "bpm": 1}) if heart_rate else None
        ),
        "elevation_gain": (
            quantity(elevation, {"m": 1, "ft": 0.3048}) if elevation else None
        ),
        "summary_polyline": encoded if "route" in workout else None,
    }


def read_workouts(source, since):
    paths = sorted(source.glob("*.json")) if source.is_dir() else [source]
    if not paths:
        raise ValueError("No JSON files found")
    parsed = {}
    skipped = 0
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
        workouts = document["data"].get("workouts", [])
        if not isinstance(workouts, list):
            raise TypeError(f"{path.name}: expected a workouts array")
        for index, workout in enumerate(workouts, start=1):
            try:
                item = (
                    parse_workout(workout, since)
                    if workout["name"] in RUN_TYPES
                    else None
                )
            except (
                KeyError,
                TypeError,
                ValueError,
                AttributeError,
                OverflowError,
            ) as exc:
                raise ValueError(
                    f"{path.name}: invalid workout #{index}: {exc}"
                ) from exc
            if item is None:
                skipped += 1
            else:
                external_id, fields = item
                # Later exports can fill in fields absent in earlier batches.
                existing = parsed.setdefault(external_id, {})
                merge_fields(existing, fields)
    return parsed, skipped


def merge_fields(existing, fields):
    optional_fields = {"summary_polyline", "average_heartrate", "elevation_gain"}
    for key, value in fields.items():
        if key not in optional_fields or key not in existing or value is not None:
            existing[key] = value


def save_workout(session, external_id, fields):
    run_id = session.scalar(
        select(workout_ids.c.run_id).where(workout_ids.c.external_id == external_id)
    )
    if run_id is None:
        digest = hashlib.sha256(f"health_auto_export:{external_id}".encode()).digest()
        # Negative IDs disjoint from ordinary positive activity IDs. Keep them
        # exactly representable as numbers in the frontend.
        run_id = -(int.from_bytes(digest[:8], "big") % (2**53 - 1) + 1)
        owner = session.scalar(
            select(workout_ids.c.external_id).where(workout_ids.c.run_id == run_id)
        )
        if owner is not None or session.get(Activity, run_id) is not None:
            raise ValueError(f"Activity ID collision at {run_id}")
        session.execute(
            insert(workout_ids).values(external_id=external_id, run_id=run_id)
        )

    activity = session.get(Activity, run_id)
    if activity is None:
        session.add(Activity(run_id=run_id, location_country="", **fields))
    else:
        merged = {key: getattr(activity, key) for key in fields}
        merge_fields(merged, fields)
        for key, value in merged.items():
            setattr(activity, key, value)


def import_workouts(source, db_path, output, since=None):
    source_path, database_path, output_path = (
        path.resolve() for path in (source, db_path, output)
    )
    if len({source_path, database_path, output_path}) != 3:
        raise ValueError("Source, database, and output must be different paths")
    if source.is_dir() and output_path.parent == source_path:
        raise ValueError("Write the generated JSON outside the source directory")

    workouts, skipped = read_workouts(source, since)
    generator = Generator(db_path)
    with generator.session as session:
        connection = session.connection()
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        workout_ids.create(connection, checkfirst=True)
        for external_id, fields in workouts.items():
            save_workout(session, external_id, fields)
        # Generator.load flushes the rows and commits after serialization.
        activities = generator.load()

    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        try:
            json.dump(activities, temporary, indent=0)
            temporary.close()
            temporary_path.replace(output)
        finally:
            temporary_path.unlink(missing_ok=True)

    return len(workouts), skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Workouts JSON file or directory")
    parser.add_argument("--db", type=Path, default=Path(SQL_FILE))
    parser.add_argument("--output", type=Path, default=Path(JSON_FILE))
    parser.add_argument(
        "--since", help="Inclusive ISO 8601 start timestamp with offset"
    )
    args = parser.parse_args()
    try:
        since = datetime.fromisoformat(args.since) if args.since else None
        if since is not None and since.tzinfo is None:
            raise ValueError("--since requires a time zone offset")
        count, skipped = import_workouts(args.source, args.db, args.output, since)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        parser.exit(1, f"Health Auto Export import failed: {exc}\n")
    print(f"Imported {count} running workouts; skipped {skipped} records.")


if __name__ == "__main__":
    main()
