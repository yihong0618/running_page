import importlib
from pathlib import Path

import polyline
import pytest


@pytest.fixture
def generator(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parent / "run_page"))
    monkeypatch.delenv("GENERATE_INDOOR_ROUTES", raising=False)
    return importlib.import_module("generator")


def _activities():
    return [
        {
            "run_id": 1,
            "distance": 2000,
            "type": "Run",
            "subtype": "Run",
            "summary_polyline": polyline.encode(
                [(30.0 + i * 0.005, 120.0) for i in range(5)]
            ),
            "location_country": "Outdoor location",
        },
        {
            "run_id": 2,
            "distance": 1000,
            "type": "Run",
            "subtype": "Run",
            "summary_polyline": None,
            "location_country": None,
        },
    ]


@pytest.mark.parametrize("subtype", ["Run", "treadmill", "indoor"])
@pytest.mark.parametrize("filter_before_saving", [False, True])
def test_load_preserves_source_routes_and_missing_gps(
    generator, monkeypatch, tmp_path, subtype, filter_before_saving
):
    monkeypatch.setattr(generator, "IGNORE_BEFORE_SAVING", filter_before_saving)
    activities = _activities()
    activities[1]["subtype"] = subtype
    app = generator.Generator(tmp_path / "activities.db")
    try:
        for activity in activities:
            date = f"2026-01-0{activity['run_id']} 12:00:00"
            app.session.add(
                generator.Activity(**activity, start_date=date, start_date_local=date)
            )
        app.session.commit()

        for _ in range(2):
            result = app.load()
            app.session.expire_all()
            outdoor = app.session.get(generator.Activity, 1)
            indoor = app.session.get(generator.Activity, 2)
            assert outdoor.summary_polyline == activities[0]["summary_polyline"]
            expected_route = activities[0]["summary_polyline"]
            if not filter_before_saving:
                expected_route = generator.filter_out(expected_route)
            assert result[0]["summary_polyline"] == expected_route
            assert result[1]["distance"] == indoor.distance == 1000
            assert result[1]["summary_polyline"] is None
            assert indoor.summary_polyline is None
            assert result[1]["subtype"] == indoor.subtype == subtype
            assert result[1]["location_country"] is None
            assert indoor.location_country is None
    finally:
        app.session.close()
        app.session.bind.dispose()
