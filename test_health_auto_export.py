import importlib
import json
from datetime import datetime
from pathlib import Path

import polyline
import pytest


@pytest.fixture
def importer(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parent / "run_page"))
    return importlib.import_module("health_auto_export_sync")


def workout(workout_id, name="Running", **fields):
    return {
        "id": workout_id,
        "name": name,
        "start": "2025-01-01 07:00:00 +0800",
        "end": "2025-01-01 07:31:00 +0800",
        "duration": 1800,
        "distance": {"qty": 3, "units": "mi"},
        **fields,
    }


def write_export(path, *workouts):
    path.write_text(json.dumps({"data": {"workouts": workouts}}), encoding="utf-8")


def test_import_routes_indoor_and_repeated_exports(importer, tmp_path, monkeypatch):
    monkeypatch.setattr("generator.filter_out", lambda value: value)
    source = tmp_path / "export.json"
    database = tmp_path / "data.db"
    output = tmp_path / "activities.json"
    points = [(37.77, -122.42), (37.78, -122.43)]
    outdoor = workout(
        "outdoor",
        "户外 跑步",
        route=[{"latitude": lat, "longitude": lon} for lat, lon in points],
        avgHeartRate={"qty": 150, "units": "count/min"},
    )
    indoor = workout("indoor", "室内 跑步")
    write_export(source, outdoor, indoor, workout("cycling", "Cycling"))
    since = datetime.fromisoformat("2024-12-31T23:00:00Z")
    assert importer.import_workouts(source, database, output, since) == (2, 1)
    first = output.read_bytes()
    assert importer.import_workouts(source, database, output, since) == (2, 1)
    assert output.read_bytes() == first

    runs = {run["name"]: run for run in json.loads(first)}
    route = runs["Run"]
    assert polyline.decode(route["summary_polyline"]) == points
    assert route["distance"] == pytest.approx(4828.032)
    assert route["start_date"] == "2024-12-31 23:00:00"
    assert route["start_date_local"] == "2025-01-01 07:00:00"
    assert route["average_heartrate"] == 150
    assert not runs["Treadmill Run"]["summary_polyline"]
    assert runs["Treadmill Run"]["moving_time"] == "0:30:00"

    del outdoor["route"]
    write_export(source, outdoor)
    importer.import_workouts(source, database, output)
    assert output.read_bytes() == first


def test_validation_preserves_previous_output(importer, tmp_path):
    source = tmp_path / "export.json"
    database = tmp_path / "data.db"
    output = tmp_path / "activities.json"
    write_export(source, workout("first"))
    importer.import_workouts(source, database, output)
    previous = output.read_bytes()
    write_export(
        source,
        workout("second"),
        workout("bad", distance={"qty": 1, "units": "unknown"}),
    )
    with pytest.raises(ValueError, match="invalid workout #2"):
        importer.import_workouts(source, database, output)
    assert output.read_bytes() == previous
    write_export(source, workout("first"))
    importer.import_workouts(source, database, output)
    assert output.read_bytes() == previous


def test_collision_does_not_replace_existing_activity(importer, tmp_path):
    source = tmp_path / "export.json"
    database = tmp_path / "data.db"
    output = tmp_path / "activities.json"
    write_export(source, workout("first"))
    importer.import_workouts(source, database, output)
    previous = output.read_bytes()
    generator = importer.Generator(database)
    with generator.session as session:
        session.execute(importer.workout_ids.delete())
        session.commit()
    with pytest.raises(ValueError, match="Activity ID collision"):
        importer.import_workouts(source, database, output)
    assert output.read_bytes() == previous
