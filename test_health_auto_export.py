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


@pytest.mark.parametrize("incomplete", [None, [], [{"latitude": 40, "longitude": 100}]])
def test_incomplete_route_preserves_saved_route(importer, tmp_path, incomplete):
    source, db, output = (tmp_path / name for name in ("in.json", "db", "out.json"))
    route = [{"latitude": 40, "longitude": lon} for lon in range(100, 106)]
    write_export(source, workout("outdoor", route=route))
    importer.import_workouts(source, db, output)
    first = json.loads(output.read_text())[0]["summary_polyline"]
    assert first
    write_export(source, workout("outdoor", route=incomplete))
    importer.import_workouts(source, db, output)
    assert json.loads(output.read_text())[0]["summary_polyline"] == first


def test_legacy_privacy_migration_without_original_export(
    importer, tmp_path, monkeypatch
):
    import sqlite3

    monkeypatch.setattr("polyline_processor.IGNORE_START_END_RANGE", 0.01)
    source, db, output = (tmp_path / name for name in ("in.json", "db", "out.json"))
    raw_id = "original-private-workout-identifier"
    points = [(40, lon) for lon in range(100, 106)]
    route = [{"latitude": lat, "longitude": lon} for lat, lon in points]
    raw = polyline.encode(points)
    safe = polyline.encode(points[1:-1])
    write_export(source, workout(raw_id, route=route))
    importer.import_workouts(source, db, output)
    first = json.loads(output.read_text())[0]
    assert first["summary_polyline"] == safe
    with sqlite3.connect(db) as conn:
        conn.execute("DROP TABLE health_auto_export_workouts")
        conn.execute(
            "CREATE TABLE health_auto_export_workout_ids (external_id TEXT PRIMARY KEY,run_id INTEGER UNIQUE)"
        )
        conn.execute(
            "INSERT INTO health_auto_export_workout_ids VALUES (?,?)",
            (raw_id, first["run_id"]),
        )
        conn.execute("UPDATE activities SET summary_polyline=?", (raw,))
    write_export(source)
    for _ in range(2):
        importer.import_workouts(source, db, output)
        assert json.loads(output.read_text()) == [first]
        with sqlite3.connect(db) as conn:
            assert conn.execute(
                "SELECT summary_polyline FROM activities"
            ).fetchone() == (safe,)
            assert conn.execute(
                "SELECT id_digest FROM health_auto_export_workouts"
            ).fetchone() == (importer.workout_digest(raw_id).hex(),)
        assert raw_id.encode() not in db.read_bytes()
        assert raw.encode() not in db.read_bytes()
    write_export(source, workout(raw_id, route=route))
    importer.import_workouts(source, db, output)
    assert json.loads(output.read_text()) == [first]


def test_entire_route_within_privacy_radius_clears_map(importer, tmp_path, monkeypatch):
    monkeypatch.setattr("polyline_processor.IGNORE_START_END_RANGE", 1)
    source, db, output = (tmp_path / name for name in ("in.json", "db", "out.json"))
    for spacing in (0.1, 0.0001):
        points = [{"latitude": 40, "longitude": 100 + i * spacing} for i in range(6)]
        write_export(source, workout("outdoor", route=points))
        importer.import_workouts(source, db, output)
        assert bool(json.loads(output.read_text())[0]["summary_polyline"]) == (
            spacing == 0.1
        )


@pytest.mark.parametrize("filter_before_saving", [False, True])
def test_shared_export_respects_source_and_changed_privacy(
    importer, tmp_path, monkeypatch, filter_before_saving
):
    from datetime import timedelta

    monkeypatch.setattr("generator.IGNORE_BEFORE_SAVING", filter_before_saving)
    monkeypatch.setattr("polyline_processor.IGNORE_START_END_RANGE", 0.01)
    source, db, output = (tmp_path / name for name in ("in.json", "db", "out.json"))
    points = [(40, 100 + i) for i in range(6)]
    raw = polyline.encode(points)
    safe = polyline.encode(points[1:-1])
    route = [{"latitude": lat, "longitude": lon} for lat, lon in points]
    write_export(source, workout("outdoor", route=route))
    importer.import_workouts(source, db, output)
    generator = importer.Generator(db)
    with generator.session as session:
        session.add(
            importer.Activity(
                run_id=1,
                name="Other source",
                type="Run",
                distance=100,
                moving_time=timedelta(seconds=30),
                start_date_local="2025-01-02 07:00:00",
                summary_polyline=safe if filter_before_saving else raw,
            )
        )
        assert [row["summary_polyline"] for row in generator.load()] == [safe, safe]
        monkeypatch.setattr("polyline_processor.IGNORE_START_END_RANGE", 10000)
        assert not generator.load()[0]["summary_polyline"]


@pytest.mark.parametrize("hae_first", [False, True])
def test_existing_history_dedup_without_cutoff(importer, tmp_path, hae_first):
    from datetime import timedelta

    source = tmp_path / "export.json"
    database = tmp_path / "data.db"
    output = tmp_path / "activities.json"
    write_export(
        source,
        workout("same-as-strava"),
        workout("missing-from-strava", distance={"qty": 2, "units": "km"}),
    )
    if hae_first:
        assert importer.import_workouts(source, database, output) == (2, 0)

    with importer.Generator(database).session as session:
        session.add(
            importer.Activity(
                run_id=123,
                name="Original Strava title",
                type="Run",
                distance=4800,
                moving_time=timedelta(seconds=1780),
                elapsed_time=timedelta(seconds=1860),
                start_date="2024-12-31T23:00:30+00:00",
                start_date_local="2025-01-01 07:00:30",
            )
        )
        session.commit()

    for _ in range(2):
        assert importer.import_workouts(source, database, output) == (1, 1)
        runs = json.loads(output.read_text())
        assert len(runs) == 2
        original = next(run for run in runs if run["run_id"] == 123)
        assert original["name"] == "Original Strava title"
        assert original["distance"] == 4800
        with importer.Generator(database).session as session:
            owners = session.scalars(importer.select(importer.workout_ids.c.run_id))
            assert set(owners) == {
                run["run_id"] for run in runs if run["run_id"] != 123
            }
