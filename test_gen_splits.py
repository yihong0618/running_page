"""Synthetic checks for run_page/gen_splits.py (no FIT file needed)."""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "run_page"))

from gen_splits import (  # noqa: E402
    FIT_EPOCH_S,
    MAX_CHART_POINTS,
    _hr_zones_from_records,
    _zones,
    analyze_messages,
    build_chart,
)

CHART_KEYS = ("d", "t", "pace", "hr", "cad", "power", "alt", "gct", "vo", "vr", "temp")


def _rec(t, d, hr=150, speed=4.0):
    return {
        "t": t,
        "d": d,
        "speed": speed,
        "hr": hr,
        "cad": 170,
        "power": 300,
        "alt": 100.0,
        "vo": 80.0,
        "gct": 240.0,
        "gctb": None,
        "vr": 7.5,
        "step": 1400.0,
        "temp": 20.0,
        "resp": None,
    }


def _messages(paused: bool = False):
    start = 1_100_000_000
    records = []
    # 2.5 km at 4 m/s (250 s/km), 1 record per second, with a 60 s pause at 1 km.
    t = start
    d = 0.0
    while d < 2500:
        records.append(
            {
                "timestamp": t,
                "distance": d,
                "enhanced_speed": 4.0,
                "heart_rate": 150,
                "cadence": 85,
                "fractional_cadence": 0.5,
                "power": 300,
                "enhanced_altitude": 100 + (d / 100),
                "vertical_oscillation": 80.0,
                "stance_time": 240.0,
                "step_length": 1400.0,
                "position_lat": 1,
                "position_long": 2,
            }
        )
        t += 1
        d += 4
        if paused and abs(d - 1000) < 1e-6:
            t += 60
    events = [{"timestamp": start, "event": "timer", "event_type": "start"}]
    if paused:
        events += [
            {"timestamp": start + 250, "event": "timer", "event_type": "stop_all"},
            {"timestamp": start + 310, "event": "timer", "event_type": "start"},
        ]
    return {
        "session_mesgs": [
            {
                "start_time": start,
                "total_distance": 2500.0,
                "total_timer_time": 625.0,
                "total_elapsed_time": 685.0 if paused else 625.0,
                "sport": "running",
                "avg_heart_rate": 150,
                "avg_running_cadence": 85,
                "avg_fractional_cadence": 0.5,
                "enhanced_avg_speed": 4.0,
                "total_training_effect": 3.1,
            }
        ],
        "lap_mesgs": [
            {
                "total_timer_time": 312.5,
                "total_distance": 1250.0,
                "avg_heart_rate": 148,
            },
            {
                "total_timer_time": 312.5,
                "total_distance": 1250.0,
                "avg_heart_rate": 152,
            },
        ],
        "record_mesgs": records,
        "event_mesgs": events,
    }


def test_splits_basic():
    out = analyze_messages(_messages())
    assert out["run_id"] == (1_100_000_000 + FIT_EPOCH_S) * 1000
    km = out["splits"]
    assert [s["index"] for s in km] == [1, 2, 3]
    assert km[0]["pace"] == 250.0
    assert km[0]["cadence_avg"] == 171  # (85 + 0.5) * 2
    assert km[0]["stride_length"] == 1.4
    assert km[0]["vertical_oscillation"] == 8.0
    assert km[2]["partial"] is True
    assert len(out["laps"]) == 2
    assert out["summary"]["aerobic_te"] == 3.1


def test_pause_excluded():
    out = analyze_messages(_messages(paused=True))
    assert abs(out["splits"][1]["time"] - 250) < 1.5


def test_no_coordinates_in_output():
    text = repr(analyze_messages(_messages()))
    assert re.search(r"'(position_\w+|lat|lng|lon|latitude|longitude)'", text) is None


def test_missing_session():
    assert analyze_messages({"record_mesgs": []}) is None


def test_build_chart_format():
    recs = [_rec(i, i * 4.0) for i in range(1000)]  # ~4 km
    c = build_chart(recs)
    assert set(c) == set(CHART_KEYS)
    n = len(c["d"])
    assert 1 < n <= MAX_CHART_POINTS + 1
    assert all(len(c[k]) == n for k in CHART_KEYS)
    assert c["d"] == sorted(c["d"]) and c["t"] == sorted(c["t"])
    assert c["pace"][n // 2] == 250  # 4 m/s
    assert c["vo"][0] == 8.0  # mm -> cm
    assert build_chart(recs[:1]) is None


def test_build_chart_sparse_gap_spans_many_buckets():
    # Dense 0-200 m, then one record jumps to 5 km (GPS/sensor gap), then dense.
    recs = [_rec(i, i * 4.0) for i in range(51)]
    recs += [_rec(1000 + i, 5000.0 + i * 4.0) for i in range(51)]
    c = build_chart(recs)
    n = len(c["d"])
    assert all(len(c[k]) == n for k in CHART_KEYS)
    assert len(set(c["d"])) == n, "duplicate points"
    assert all(v is not None for v in c["pace"]), "empty point"
    assert c["d"] == sorted(c["d"])
    # The ~4.8 km gap must not be filled with one point per skipped bucket.
    step_km = (recs[-1]["d"] - recs[0]["d"]) / MAX_CHART_POINTS / 1000
    gap_pts = [d for d in c["d"] if 0.3 < d < 4.9]
    assert len(gap_pts) <= 1, (gap_pts, step_km)


def test_zones_from_time_in_zone():
    msgs = {
        "time_in_zone_mesgs": [
            {"reference_mesg": "lap", "time_in_hr_zone": [9, 9]},
            {
                "reference_mesg": "session",
                "time_in_hr_zone": [10, 20, 30, 40, 50, 60],
                "hr_zone_high_boundary": [100, 120, 140, 160, 180, 200],
                "hr_calc_type": "percent_max_hr",
                "max_heart_rate": 200,
                "threshold_heart_rate": 175,
                "time_in_power_zone": [5, 6, 7],
                "power_zone_high_boundary": [200, 300, 400],
                "functional_threshold_power": 320,
            },
        ]
    }
    z = _zones(msgs)
    assert z["hr"]["seconds"] == [10, 20, 30, 40, 50, 60]
    assert z["hr"]["high_boundary"][-1] == 200
    assert z["hr"]["calc_type"] == "percent_max_hr"
    assert z["hr"]["threshold_hr"] == 175
    assert z["power"]["seconds"] == [5, 6, 7]
    assert z["power"]["ftp"] == 320
    assert _zones({}) == {}


def test_hr_zones_from_records_estimated():
    # 100 s each at 55 %, 75 %, 95 % of max 200.
    recs = []
    t = 0
    for hr in (110, 150, 190):
        for _ in range(100):
            recs.append(_rec(t, t * 4.0, hr=hr))
            t += 1
    z = _hr_zones_from_records(recs, 200)
    assert z["calc_type"] == "percent_max_hr_estimated"
    assert z["high_boundary"] == [100, 120, 140, 160, 180, 200]
    assert z["seconds"][1] == 100 and z["seconds"][3] == 100
    assert z["seconds"][5] == 99  # last sample has no successor
    assert sum(z["seconds"]) == 299
    assert _hr_zones_from_records(recs, None) is None


def test_summary_running_dynamics():
    m = _messages()
    m["session_mesgs"][0].update(
        {
            "avg_vertical_oscillation": 85.0,
            "avg_stance_time": 245.0,
            "avg_stance_time_balance": 50.2,
            "avg_vertical_ratio": 7.8,
            "avg_step_length": 1420.0,
            "avg_power": 310,
            "total_anaerobic_training_effect": 1.2,
            "total_strides": 900,
        }
    )
    s = analyze_messages(m)["summary"]
    assert s["vertical_oscillation"] == 8.5
    assert s["ground_contact_time"] == 245
    assert s["gct_balance"] == 50.2
    assert s["vertical_ratio"] == 7.8
    assert s["stride_length"] == 1.42
    assert s["power_avg"] == 310
    assert s["anaerobic_te"] == 1.2
    assert s["steps"] == 1800  # strides per leg * 2
    assert s["cadence_avg"] == 171


def test_cycling_cadence_not_doubled():
    m = _messages()
    sess = m["session_mesgs"][0]
    sess["sport"] = "cycling"
    sess.pop("avg_running_cadence")
    sess["avg_cadence"] = 85
    sess["avg_fractional_cadence"] = 0
    sess["total_strides"] = 900
    for r in m["record_mesgs"]:
        r["fractional_cadence"] = 0
    out = analyze_messages(m)
    assert out["summary"]["cadence_avg"] == 85
    assert out["summary"]["steps"] is None
    assert out["splits"][0]["cadence_avg"] == 85
    assert max(v for v in out["chart"]["cad"] if v is not None) == 85


# --------------------------------------------------------------------------
# GPX / TCX (synthetic, no real data)
# --------------------------------------------------------------------------
import json as _json  # noqa: E402
import tempfile  # noqa: E402

from gen_splits import (  # noqa: E402
    analyze_track,
    parse_gpx,
    parse_tcx,
    resolve_run_id,
    run,
)

_LAT_PER_M = 1 / 111195.0  # degrees latitude per metre (approx.)


def _gpx(n=601, step_s=1, step_m=4.0, pause_at=None, pause_s=0, hr=True):
    pts = []
    t = 1_700_000_000
    for i in range(n):
        if pause_at is not None and i == pause_at:
            t += pause_s
        ts = __import__("time").strftime(
            "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t)
        )
        ext = (
            f"<extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>{140 + i % 20}</gpxtpx:hr>"
            "</gpxtpx:TrackPointExtension></extensions>"
            if hr
            else ""
        )
        pts.append(
            f'<trkpt lat="{30 + i * step_m * _LAT_PER_M:.8f}" lon="120.0">'
            f"<ele>{10 + (i % 50) * 0.2:.1f}</ele><time>{ts}</time>{ext}</trkpt>"
        )
        t += step_s
    return (
        '<?xml version="1.0"?><gpx version="1.1" creator="t" '
        'xmlns="http://www.topografix.com/GPX/1/1" '
        'xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">'
        "<trk><type>running</type><trkseg>" + "".join(pts) + "</trkseg></trk></gpx>"
    )


def _tcx(n=601, step_m=4.0, cadence=None):
    pts = []
    t = 1_700_000_000
    for i in range(n):
        ts = __import__("time").strftime(
            "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t + i)
        )
        cad = f"<Cadence>{cadence}</Cadence>" if cadence else ""
        pts.append(
            f"<Trackpoint><Time>{ts}</Time><DistanceMeters>{i * step_m}</DistanceMeters>"
            f"<HeartRateBpm><Value>150</Value></HeartRateBpm>{cad}</Trackpoint>"
        )
    return (
        '<?xml version="1.0"?><TrainingCenterDatabase '
        'xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">'
        '<Activities><Activity Sport="Running"><Id>x</Id><Lap><Track>'
        + "".join(pts)
        + "</Track></Lap></Activity></Activities></TrainingCenterDatabase>"
    )


def test_gpx_basic_splits_and_missing_fields():
    pts, sport = parse_gpx(_gpx())
    data = analyze_track(pts, sport, "gpx")
    assert data["run_id"] == 1_700_000_000_000
    assert data["sport"] == "running"
    s = data["summary"]
    assert abs(s["distance"] - 2400) < 5
    assert s["time"] == 600
    assert len(data["splits"]) == 3 and data["splits"][-1].get("partial")
    assert abs(data["splits"][0]["pace"] - 250) < 2  # 4 m/s -> 4'10"
    assert s["hr_avg"] is not None and s["elev_gain"] is not None
    for k in (
        "cadence_avg",
        "stride_length",
        "power_avg",
        "vertical_oscillation",
        "ground_contact_time",
        "aerobic_te",
        "training_load",
        "vo2max",
    ):
        assert s[k] is None, k
    assert data["zones"]["hr"]["calc_type"] == "percent_max_hr_estimated"
    assert data["laps"] == []
    chart = data["chart"]
    assert "pace" in chart and "hr" in chart and "alt" in chart
    for k in ("cad", "power", "gct", "vo", "vr", "temp"):
        assert k not in chart


def test_gpx_without_hr_has_no_zones():
    pts, sport = parse_gpx(_gpx(hr=False))
    data = analyze_track(pts, sport, "gpx")
    assert data["summary"]["hr_avg"] is None
    assert data["zones"] is None
    assert "hr" not in data["chart"]


def test_gpx_long_stationary_gap_is_a_pause():
    xml = _gpx(pause_at=300, pause_s=120)
    data = analyze_track(*parse_gpx(xml), "gpx")
    assert data["summary"]["time"] == 599  # gap interval dropped
    assert data["summary"]["elapsed_time"] == 720


def test_tcx_uses_distance_meters_and_cadence():
    data = analyze_track(*parse_tcx(_tcx(cadence=85)), "tcx")
    s = data["summary"]
    assert s["distance"] == 2400
    assert s["hr_avg"] == 150
    assert s["cadence_avg"] == 170  # per-leg cadence doubled for running
    assert s["stride_length"] is not None


def test_resolve_run_id():
    assert resolve_run_id("123456", 1_700_000_000_000, {123456}) == 123456
    assert resolve_run_id("abc", 1_700_000_000_000, {1_700_000_000_000}) == (
        1_700_000_000_000
    )
    assert resolve_run_id("abc", 1_700_000_000_000, {1_700_000_001_000}) == (
        1_700_000_001_000
    )
    assert resolve_run_id("99", 1_700_000_000_000, set()) == 99
    assert resolve_run_id("abc", 1_700_000_000_000, set()) == 1_700_000_000_000


def test_run_gpx_and_tcx_priority():
    with tempfile.TemporaryDirectory() as tmp:
        gdir, tdir, out = (os.path.join(tmp, x) for x in ("g", "t", "o"))
        os.makedirs(gdir)
        os.makedirs(tdir)
        with open(os.path.join(gdir, "42.gpx"), "w", encoding="utf-8") as f:
            f.write(_gpx())
        with open(os.path.join(tdir, "42.tcx"), "w", encoding="utf-8") as f:
            f.write(_tcx(cadence=85))
        acts = os.path.join(tmp, "a.json")
        with open(acts, "w", encoding="utf-8") as f:
            _json.dump([{"run_id": 42}], f)
        run([], out, quiet=True, gpx_dirs=[gdir], tcx_dirs=[tdir], activities=acts)
        with open(os.path.join(out, "42.json"), encoding="utf-8") as f:
            data = _json.load(f)
        assert data["source"] == "tcx"  # TCX beats GPX
        with open(os.path.join(out, "index.json"), encoding="utf-8") as f:
            assert _json.load(f) == [42]
        # second run is fully cached and keeps TCX
        run([], out, quiet=True, gpx_dirs=[gdir], tcx_dirs=[tdir], activities=acts)
        with open(os.path.join(out, "42.json"), encoding="utf-8") as f:
            assert _json.load(f)["source"] == "tcx"
