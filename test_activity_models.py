"""Offline regression tests for provider records and their consumers."""

import importlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parent / "run_page"))
    return importlib.import_module


@pytest.fixture(
    params=["keep", "nike", "endomondo", "joyrun", "codoon", "oppo", "tulipsport"]
)
def record(request, modules, monkeypatch):
    module = modules(f"{request.param}_sync")
    start = 1767268800
    end = start + 600
    if request.param == "keep":
        return module.parse_raw_data_to_activity(
            {
                "data": dict(
                    id="user_123_run",
                    startTime=start * 1000,
                    endTime=end * 1000,
                    heartRate=None,
                    geoPoints=None,
                    dataType="indoorRunning",
                    timezone="Asia/Shanghai",
                    duration=600,
                    distance=1000,
                )
            },
            [],
            [],
        )
    if request.param == "nike":
        return module.parse_no_gpx_data(
            dict(
                id="123",
                metrics=[{}],
                summaries=[dict(metric="distance", value=1)],
                start_epoch_ms=start * 1000,
                end_epoch_ms=end * 1000,
                active_duration_ms=600000,
            )
        )
    if request.param == "endomondo":
        return module.parse_run_endomondo_to_activity(
            dict(
                id="123",
                start_time="2026-01-01 12:00:00.000",
                end_time="2026-01-01 12:10:00.000",
                distance_km=1,
                duration_s=600,
            )
        )
    if request.param == "joyrun":
        client = object.__new__(module.Joyrun)
        return client.parse_raw_data_to_activity(
            {
                "runrecord": dict(
                    fid=123,
                    starttime=start,
                    endtime=end,
                    pause=[],
                    content=None,
                    heartrate=None,
                    city="",
                    province="",
                    meter=1000,
                    second=600,
                )
            },
            [],
        )
    if request.param == "codoon":
        client = object.__new__(module.Codoon)
        return client.parse_raw_data_to_activity(
            {
                "data": dict(
                    id=123,
                    start_time="2026-01-01T12:00:00",
                    end_time="2026-01-01T12:10:00",
                    sports_type=1,
                    total_time=600,
                    total_length=1000,
                )
            },
            [],
        )
    if request.param == "oppo":
        # GPX generation is independent of the normalized activity record.
        monkeypatch.setattr(module, "prepare_track_points", lambda *args: {})
        monkeypatch.setattr(
            module, "parse_points_to_gpx", lambda *args: module.gpxpy.gpx.GPX()
        )
        return module.parse_raw_data_to_activity(
            {
                "body": [
                    dict(
                        startTime=start * 1000,
                        endTime=end * 1000,
                        sportMode=10,
                        deviceName="test",
                        otherSportData=dict(
                            gpsPoint=[], totalTime=600, totalDistance=1000
                        ),
                    )
                ]
            },
            False,
            False,
        )
    return module.merge_summary_and_detail_to_activity(
        dict(
            id=123,
            name="test",
            type="Run",
            start_date=datetime.fromtimestamp(start, UTC),
            start_date_local=datetime.fromtimestamp(start, UTC),
            distance=1000,
            moving_time=timedelta(seconds=600),
            elapsed_time=timedelta(seconds=600),
            average_speed=1000 / 600,
            outdoor=False,
        ),
        dict(avg_hr=120, map_data_list=[]),
    )


def test_provider_record_sync_create_and_update(record, modules, tmp_path):
    models = modules("activity_models")
    generator = modules("generator")
    assert isinstance(record, models.ActivityRecord)
    assert isinstance(record.map, models.RunMap)
    assert record.distance == 1000
    assert record.moving_time == timedelta(seconds=600)
    assert record.elapsed_time == timedelta(seconds=600)
    assert record.start_latlng is None
    app = generator.Generator(tmp_path / "activities.db")
    try:
        app.sync_from_app([record])
        saved = app.session.get(generator.Activity, int(record.id))
        assert saved is not None
        assert saved.distance == record.distance
        assert saved.subtype == record.subtype
        assert saved.summary_polyline == ""
        assert saved.start_date == record.start_date
        assert saved.average_heartrate == record.average_heartrate
        app.sync_from_app([replace(record, distance=2000, name="updated")])
        assert saved.distance == 2000
        assert saved.name == "updated"
        assert app.session.query(generator.Activity).count() == 1
    finally:
        app.session.close()
        app.session.bind.dispose()


def test_gpx_import_to_record_and_database(modules, monkeypatch, tmp_path):
    generator = modules("generator")
    db = modules("generator.db")
    models = modules("activity_models")
    monkeypatch.setattr(db.g, "reverse", lambda *args, **kwargs: "Test location")
    monkeypatch.setattr(generator, "save_synced_data_file_list", lambda files: None)
    gpx = tmp_path / "run.gpx"
    gpx.write_text(
        """<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
<trk><name>Test run</name><type>Run</type><trkseg>
<trkpt lat="30" lon="120"><ele>10</ele><time>2026-01-01T12:00:00Z</time></trkpt>
<trkpt lat="30.01" lon="120.01"><ele>20</ele><time>2026-01-01T12:10:00Z</time></trkpt>
</trkseg></trk></gpx>"""
    )
    track = modules("gpxtrackposter.track").Track()
    track.load_gpx(str(gpx))
    activity = track.to_activity()
    assert isinstance(activity, models.ActivityRecord)
    assert activity.start_latlng == models.StartPoint(30, 120)
    assert activity.map.summary_polyline
    assert activity.distance > 1000
    app = generator.Generator(tmp_path / "activities.db")
    try:
        app.sync_from_data_dir(str(tmp_path))
        saved = app.session.get(generator.Activity, int(activity.id))
        assert saved is not None
        assert saved.summary_polyline == activity.map.summary_polyline
        assert saved.distance == activity.distance
        assert saved.moving_time == activity.moving_time
    finally:
        app.session.close()
        app.session.bind.dispose()


@pytest.mark.parametrize("record", ["keep"], indirect=True)
def test_keep_upload_path_preserves_record(record, modules, monkeypatch, tmp_path):
    sync = modules("keep_to_strava_sync")
    models = modules("activity_models")
    outdoor = replace(record, start_latlng=models.StartPoint(30, 120))
    monkeypatch.setattr(sync, "KEEP2STRAVA_BK_PATH", str(tmp_path / "backup.json"))
    monkeypatch.setattr(sync, "get_all_keep_tracks", lambda *args: [record, outdoor])
    indoor_result, outdoor_result = sync.run_keep_sync("", "", [])
    assert indoor_result == record
    assert outdoor_result == replace(
        outdoor, gpx_file_path=str(Path(sync.GPX_FOLDER) / f"{record.id}.gpx")
    )
    assert outdoor.gpx_file_path is None
