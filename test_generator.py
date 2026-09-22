import copy
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


@pytest.mark.parametrize("setting", ["false", "0", "no", " FALSE "])
def test_disable_indoor_routes_preserves_original_data(generator, monkeypatch, setting):
    monkeypatch.setenv("GENERATE_INDOOR_ROUTES", setting)
    activities = _activities()
    activities.append(
        {
            **activities[1],
            "run_id": 3,
            "subtype": "indoor",
            "summary_polyline": activities[0]["summary_polyline"],
        }
    )
    original = copy.deepcopy(activities)

    result = generator.Generator._fix_indoor_locations(activities)

    assert result == original
    assert activities == original


@pytest.mark.parametrize("setting", [None, "true", "1"])
def test_indoor_routes_remain_enabled_by_default(generator, monkeypatch, setting):
    if setting is not None:
        monkeypatch.setenv("GENERATE_INDOOR_ROUTES", setting)
    activities = _activities()
    outdoor = copy.deepcopy(activities[0])

    result = generator.Generator._fix_indoor_locations(activities)

    assert result[0] == outdoor
    assert result[1]["subtype"] == "indoor"
    assert result[1]["location_country"] == outdoor["location_country"]
    coords = polyline.decode(result[1]["summary_polyline"])
    assert coords[0] == (30.0, 120.0)
    assert generator._route_length_m(coords) == pytest.approx(1000, abs=1)


@pytest.mark.parametrize("enabled", [False, True])
def test_load_respects_indoor_route_setting_in_export_and_database(
    generator, monkeypatch, tmp_path, enabled
):
    monkeypatch.setenv("GENERATE_INDOOR_ROUTES", str(enabled))
    app = generator.Generator(tmp_path / "activities.db")
    try:
        for activity in _activities():
            date = f"2026-01-0{activity['run_id']} 12:00:00"
            app.session.add(
                generator.Activity(**activity, start_date=date, start_date_local=date)
            )
        app.session.commit()

        result = app.load()

        app.session.expire_all()
        saved = app.session.get(generator.Activity, 2)
        assert result[1]["distance"] == saved.distance == 1000
        if enabled:
            assert result[1]["summary_polyline"]
            assert saved.summary_polyline == result[1]["summary_polyline"]
            assert result[1]["subtype"] == saved.subtype == "indoor"
        else:
            assert result[1]["summary_polyline"] is None
            assert saved.summary_polyline is None
            assert result[1]["subtype"] == saved.subtype == "Run"
            assert result[1]["location_country"] is None
            assert saved.location_country is None
    finally:
        app.session.close()
        app.session.bind.dispose()
