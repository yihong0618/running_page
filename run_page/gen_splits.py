"""Generate per-activity split / running-dynamics JSON from FIT/GPX/TCX files.

Self-contained on purpose (only depends on ``garmin_fit_sdk`` for FIT; GPX/TCX
use the stdlib XML parser) so it can be
vendored into other projects. The output is aggregated only: no coordinates,
no per-second series. One file per activity is written to
``public/splits/{run_id}.json`` plus ``public/splits/index.json``.

``run_id`` matches the id used in ``src/static/activities.json`` for FIT
imports: session start time as epoch milliseconds. GPX/TCX files (e.g. Keep,
named ``{keep_id}.gpx``) map to the numeric file name when it is a known
run_id, otherwise to start time in epoch ms (see ``resolve_run_id``). FIT wins
over TCX, TCX over GPX for the same run_id. GPX/TCX only yield pace, HR,
elevation (and cadence/power when the file has them).

Usage:
    python run_page/gen_splits.py                    # scan FIT_OUT, TCX_OUT, GPX_OUT
    python run_page/gen_splits.py --fit-only         # FIT only
    python run_page/gen_splits.py --fit-dir DIR ...  # other folders
    python run_page/gen_splits.py --force            # rebuild everything
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

FIT_EPOCH_S = 631065600  # 1989-12-31T00:00:00Z
SCHEMA_VERSION = 1
MAX_CHART_POINTS = 200
MIN_CHART_STEP_M = 50.0
ELEV_HYSTERESIS_M = 1.0

# Sports whose FIT cadence is reported per leg (steps/min = value * 2).
STEP_SPORTS = {"running", "walking", "hiking", "training", "generic"}

_HERE = os.path.dirname(os.path.realpath(__file__))
_ROOT = os.path.dirname(_HERE)
DEFAULT_FIT_DIR = os.path.join(_ROOT, "FIT_OUT")
DEFAULT_GPX_DIR = os.path.join(_ROOT, "GPX_OUT")
DEFAULT_TCX_DIR = os.path.join(_ROOT, "TCX_OUT")
DEFAULT_ACTIVITIES = os.path.join(_ROOT, "src", "static", "activities.json")
DEFAULT_OUT_DIR = os.path.join(_ROOT, "public", "splits")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def _num(value: Any) -> float | None:
    """Return a finite float or None (FIT invalid values become None)."""
    if value is None or isinstance(value, (bool, str, list, dict)):
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v


def _r(value: float | None, nd: int = 1) -> float | int | None:
    if value is None:
        return None
    if nd == 0:
        return round(value)
    return round(value, nd)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _max(values: list[float]) -> float | None:
    return max(values) if values else None


def _speed(msg: dict, key: str = "avg_speed") -> float | None:
    """Prefer enhanced_* speed; plain speed 65.535 means invalid."""
    v = _num(msg.get("enhanced_" + key))
    if v is None:
        v = _num(msg.get(key))
    if v is None or v >= 65.5 or v <= 0:
        return None
    return v


def _pace(speed: float | None) -> float | None:
    """Seconds per km from m/s."""
    if not speed or speed <= 0:
        return None
    return 1000.0 / speed


def _cadence(base: Any, frac: Any, per_leg: bool) -> float | None:
    b = _num(base)
    if b is None or b <= 0:
        return None
    f = _num(frac) or 0.0
    c = b + f
    return c * 2 if per_leg else c


def _positive(value: Any) -> float | None:
    v = _num(value)
    return v if v is not None and v > 0 else None


def _gct_balance(value: Any) -> float | None:
    """stance_time_balance is left-foot percentage (0-100)."""
    v = _num(value)
    if v is None or v <= 0 or v >= 100:
        return None
    return v


def _vo2max_from_garmin_140(msgs: dict) -> float | None:
    """Undocumented Garmin message 140, field 7: VO2max * 65536 / 3.5."""
    for m in msgs.get(140, []) or msgs.get("140", []) or []:
        raw = _num(m.get(7))
        if raw:
            v = raw * 3.5 / 65536
            if 20 <= v <= 95:
                return v
    return None


# --------------------------------------------------------------------------
# timer time (pauses excluded)
# --------------------------------------------------------------------------
def _pause_intervals(events: list[dict]) -> list[tuple[float, float]]:
    pauses: list[tuple[float, float]] = []
    stopped_at = None
    for e in sorted(events, key=lambda x: x.get("timestamp") or 0):
        if e.get("event") != "timer":
            continue
        ts = _num(e.get("timestamp"))
        if ts is None:
            continue
        et = e.get("event_type")
        if et in ("stop", "stop_all", "stop_disable", "stop_disable_all"):
            if stopped_at is None:
                stopped_at = ts
        elif et == "start" and stopped_at is not None:
            pauses.append((stopped_at, ts))
            stopped_at = None
    return pauses


class _Timer:
    def __init__(self, start: float, pauses: list[tuple[float, float]]):
        self.start = start
        self.pauses = pauses

    def at(self, ts: float) -> float:
        paused = 0.0
        for a, b in self.pauses:
            if ts <= a:
                break
            paused += min(ts, b) - a
        return max(0.0, ts - self.start - paused)


# --------------------------------------------------------------------------
# record normalisation
# --------------------------------------------------------------------------
def _records(msgs: dict, per_leg: bool, timer: _Timer) -> list[dict]:
    out = []
    last_d = -1.0
    for rec in msgs.get("record_mesgs", []) or []:
        ts = _num(rec.get("timestamp"))
        d = _num(rec.get("distance"))
        if ts is None or d is None:
            continue
        d = max(d, last_d)  # distance must be monotonic
        last_d = d
        alt = _num(rec.get("enhanced_altitude"))
        if alt is None:
            alt = _num(rec.get("altitude"))
        if alt is not None and not (-500 < alt < 9000):
            alt = None
        out.append(
            {
                "t": timer.at(ts),
                "d": d,
                "speed": _speed(rec, "speed"),
                "hr": _positive(rec.get("heart_rate")),
                "cad": _cadence(
                    rec.get("cadence"), rec.get("fractional_cadence"), per_leg
                ),
                "power": _positive(rec.get("power")),
                "alt": alt,
                "vo": _positive(rec.get("vertical_oscillation")),  # mm
                "gct": _positive(rec.get("stance_time")),  # ms
                "gctb": _gct_balance(rec.get("stance_time_balance")),
                "vr": _positive(rec.get("vertical_ratio")),  # %
                "step": _positive(rec.get("step_length")),  # mm
                "temp": _num(rec.get("temperature")),
                "resp": _positive(
                    rec.get("enhanced_respiration_rate") or rec.get("respiration_rate")
                ),
            }
        )
    return out


def _elev_gain_loss(alts: list[float]) -> tuple[float | None, float | None]:
    if len(alts) < 2:
        return None, None
    gain = loss = 0.0
    ref = alts[0]
    for a in alts[1:]:
        diff = a - ref
        if diff >= ELEV_HYSTERESIS_M:
            gain += diff
            ref = a
        elif diff <= -ELEV_HYSTERESIS_M:
            loss -= diff
            ref = a
    return gain, loss


def _aggregate(recs: list[dict], distance: float, duration: float) -> dict:
    def col(k):
        return [r[k] for r in recs if r[k] is not None]

    hr, cad, pw = col("hr"), col("cad"), col("power")
    step = col("step")
    gain, loss = _elev_gain_loss(col("alt"))
    speed = distance / duration if duration > 0 else None
    stride = _mean(step) / 1000 if step else None
    if stride is None and speed and _mean(cad):
        stride = speed * 60 / _mean(cad)
    return {
        "distance": _r(distance, 1),
        "time": _r(duration, 1),
        "pace": _r(_pace(speed), 1),
        "speed": _r(speed, 3),
        "hr_avg": _r(_mean(hr), 0),
        "hr_max": _r(_max(hr), 0),
        "cadence_avg": _r(_mean(cad), 0),
        "cadence_max": _r(_max(cad), 0),
        "stride_length": _r(stride, 2),
        "power_avg": _r(_mean(pw), 0),
        "power_max": _r(_max(pw), 0),
        "elev_gain": _r(gain, 1),
        "elev_loss": _r(loss, 1),
        "vertical_oscillation": _r(
            _mean(col("vo")) / 10 if col("vo") else None, 1
        ),  # cm
        "ground_contact_time": _r(_mean(col("gct")), 0),
        "gct_balance": _r(_mean(col("gctb")), 1),
        "vertical_ratio": _r(_mean(col("vr")), 1),
        "temperature": _r(_mean(col("temp")), 0),
        "respiration_rate": _r(_mean(col("resp")), 0),
    }


def _interp_t(a: dict, b: dict, d: float) -> float:
    if b["d"] == a["d"]:
        return b["t"]
    return a["t"] + (b["t"] - a["t"]) * (d - a["d"]) / (b["d"] - a["d"])


def build_km_splits(recs: list[dict], split_m: float = 1000.0) -> list[dict]:
    if len(recs) < 2:
        return []
    splits = []
    seg: list[dict] = []
    seg_start_d, seg_start_t = recs[0]["d"], recs[0]["t"]
    boundary = seg_start_d + split_m
    prev = recs[0]
    for r in recs:
        while r["d"] >= boundary:
            t_cross = _interp_t(prev, r, boundary)
            item = _aggregate(seg or [r], boundary - seg_start_d, t_cross - seg_start_t)
            item["index"] = len(splits) + 1
            splits.append(item)
            seg = []
            seg_start_d, seg_start_t = boundary, t_cross
            boundary += split_m
        seg.append(r)
        prev = r
    rest = recs[-1]["d"] - seg_start_d
    if rest >= 50 and seg:
        item = _aggregate(seg, rest, recs[-1]["t"] - seg_start_t)
        item["index"] = len(splits) + 1
        item["partial"] = True
        splits.append(item)
    return splits


def build_chart(recs: list[dict]) -> dict | None:
    if len(recs) < 2:
        return None
    total = recs[-1]["d"] - recs[0]["d"]
    if total <= 0:
        return None
    step = max(MIN_CHART_STEP_M, total / MAX_CHART_POINTS)
    keys = ("hr", "cad", "power", "alt", "gct", "vo", "vr", "temp")
    series: dict[str, list] = {k: [] for k in ("d", "t", "pace", *keys)}
    bucket: list[dict] = []
    edge = recs[0]["d"] + step
    t_origin = recs[0]["t"]

    def flush(rows):
        if not rows:
            return
        d0, d1 = rows[0]["d"], rows[-1]["d"]
        t0, t1 = rows[0]["t"], rows[-1]["t"]
        sp = [r["speed"] for r in rows if r["speed"]]
        speed = (d1 - d0) / (t1 - t0) if t1 > t0 and d1 > d0 else _mean(sp)
        series["d"].append(_r((d0 + d1) / 2 / 1000, 3))
        series["t"].append(_r((t0 + t1) / 2 - t_origin, 1))
        series["pace"].append(_r(_pace(speed), 0))
        for k in keys:
            vals = [r[k] for r in rows if r[k] is not None]
            v = _mean(vals)
            if k == "vo" and v is not None:
                v /= 10
            nd = 1 if k in ("alt", "vo", "vr") else 0
            series[k].append(_r(v, nd))

    # `bucket[0]` may be an anchor carried over from the previous bucket so
    # adjacent points share an endpoint; `fresh` counts rows added since.
    fresh = 0
    for r in recs:
        while r["d"] >= edge:
            # A sparse record can jump several buckets at once; only flush a
            # bucket that actually received new rows, so gaps produce no empty
            # or duplicated points.
            if fresh:
                flush(bucket)
                bucket = [bucket[-1]]
                fresh = 0
            edge += step
        bucket.append(r)
        fresh += 1
    if fresh:
        flush(bucket)
    # Drop series without any value to keep files small.
    return {
        k: v for k, v in series.items() if k == "d" or any(x is not None for x in v)
    }


def _lap_entry(lap: dict, idx: int, per_leg: bool) -> dict:
    timer = (
        _num(lap.get("total_timer_time")) or _num(lap.get("total_elapsed_time")) or 0
    )
    dist = _num(lap.get("total_distance")) or 0
    speed = _speed(lap) or (dist / timer if timer else None)
    step = _positive(lap.get("avg_step_length"))
    cad = _cadence(
        lap.get("avg_running_cadence") or lap.get("avg_cadence"),
        lap.get("avg_fractional_cadence"),
        per_leg,
    )
    vo = _positive(lap.get("avg_vertical_oscillation"))
    return {
        "index": idx,
        "distance": _r(dist, 1),
        "time": _r(timer, 1),
        "pace": _r(_pace(speed), 1),
        "speed": _r(speed, 3),
        "hr_avg": _r(_positive(lap.get("avg_heart_rate")), 0),
        "hr_max": _r(_positive(lap.get("max_heart_rate")), 0),
        "cadence_avg": _r(cad, 0),
        "cadence_max": _r(
            _cadence(
                lap.get("max_running_cadence") or lap.get("max_cadence"),
                lap.get("max_fractional_cadence"),
                per_leg,
            ),
            0,
        ),
        "stride_length": _r(step / 1000 if step else None, 2),
        "power_avg": _r(_positive(lap.get("avg_power")), 0),
        "power_max": _r(_positive(lap.get("max_power")), 0),
        "normalized_power": _r(_positive(lap.get("normalized_power")), 0),
        "elev_gain": _r(_num(lap.get("total_ascent")), 1),
        "elev_loss": _r(_num(lap.get("total_descent")), 1),
        "vertical_oscillation": _r(vo / 10 if vo else None, 1),
        "ground_contact_time": _r(_positive(lap.get("avg_stance_time")), 0),
        "gct_balance": _r(_gct_balance(lap.get("avg_stance_time_balance")), 1),
        "vertical_ratio": _r(_positive(lap.get("avg_vertical_ratio")), 1),
        "temperature": _r(_num(lap.get("avg_temperature")), 0),
        "calories": _r(_num(lap.get("total_calories")), 0),
        "intensity": (
            lap.get("intensity") if isinstance(lap.get("intensity"), str) else None
        ),
        "trigger": (
            lap.get("lap_trigger") if isinstance(lap.get("lap_trigger"), str) else None
        ),
    }


def _zones(msgs: dict) -> dict:
    out: dict = {}
    for z in msgs.get("time_in_zone_mesgs", []) or []:
        if z.get("reference_mesg") != "session":
            continue
        hr_t, hr_b = z.get("time_in_hr_zone"), z.get("hr_zone_high_boundary")
        if isinstance(hr_t, list) and any(_num(x) for x in hr_t):
            out["hr"] = {
                "seconds": [_r(_num(x) or 0, 0) for x in hr_t],
                "high_boundary": (
                    [_num(x) for x in hr_b] if isinstance(hr_b, list) else None
                ),
                "calc_type": (
                    z.get("hr_calc_type")
                    if isinstance(z.get("hr_calc_type"), str)
                    else None
                ),
                "max_hr": _num(z.get("max_heart_rate")),
                "resting_hr": _num(z.get("resting_heart_rate")),
                "threshold_hr": _num(z.get("threshold_heart_rate")),
            }
        p_t, p_b = z.get("time_in_power_zone"), z.get("power_zone_high_boundary")
        if isinstance(p_t, list) and any(_num(x) for x in p_t):
            out["power"] = {
                "seconds": [_r(_num(x) or 0, 0) for x in p_t],
                "high_boundary": (
                    [_num(x) for x in p_b] if isinstance(p_b, list) else None
                ),
                "ftp": _num(z.get("functional_threshold_power")),
            }
        break
    return out


def _hr_zones_from_records(recs: list[dict], max_hr: float | None) -> dict | None:
    """Fallback: 5 zones at 50/60/70/80/90 % of max HR."""
    if not max_hr:
        return None
    bounds = [max_hr * p for p in (0.6, 0.7, 0.8, 0.9)]
    secs = [0.0] * 6
    for a, b in zip(recs, recs[1:]):
        if a["hr"] is None:
            continue
        dt = b["t"] - a["t"]
        if dt <= 0 or dt > 30:
            continue
        z = 1 + sum(1 for x in bounds if a["hr"] > x) if a["hr"] >= max_hr * 0.5 else 0
        secs[z] += dt
    if not any(secs):
        return None
    return {
        "seconds": [round(s) for s in secs],
        "high_boundary": [round(max_hr * p) for p in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)],
        "calc_type": "percent_max_hr_estimated",
        "max_hr": max_hr,
    }


def _summary(session: dict, recs: list[dict], per_leg: bool, msgs: dict) -> dict:
    timer = _num(session.get("total_timer_time")) or 0
    dist = _num(session.get("total_distance")) or 0
    lap_like = _lap_entry(session, 0, per_leg)
    lap_like.pop("index", None)
    lap_like.pop("intensity", None)
    lap_like.pop("trigger", None)
    rec_agg = _aggregate(recs, dist, timer) if recs else {}
    # Fill gaps in the session message with record-derived values.
    for k, v in rec_agg.items():
        if lap_like.get(k) is None and v is not None:
            lap_like[k] = v
    max_speed = _speed(session, "max_speed")
    lap_like.update(
        {
            "elapsed_time": _r(_num(session.get("total_elapsed_time")), 1),
            "moving_time": _r(_num(session.get("total_moving_time")), 1),
            "best_pace": _r(_pace(max_speed), 1),
            "aerobic_te": _r(_num(session.get("total_training_effect")), 1),
            "anaerobic_te": _r(_num(session.get("total_anaerobic_training_effect")), 1),
            "training_load": _r(_num(session.get("training_load_peak")), 0),
            "training_stress_score": _r(_num(session.get("training_stress_score")), 1),
            "intensity_factor": _r(_num(session.get("intensity_factor")), 2),
            "vo2max": _r(_vo2max_from_garmin_140(msgs), 1),
            "temperature_min": _r(_num(session.get("min_temperature")), 0),
            "temperature_max": _r(_num(session.get("max_temperature")), 0),
            "steps": (
                _r(_num(session.get("total_strides")) * (2 if per_leg else 1), 0)
                if _num(session.get("total_strides")) and per_leg
                else None
            ),
            "rpe": _r((_num(session.get("workout_rpe")) or 0) / 10, 0) or None,
            "feel": _r(_num(session.get("workout_feel")), 0),
        }
    )
    return lap_like


def analyze_messages(msgs: dict) -> dict | None:
    sessions = msgs.get("session_mesgs") or []
    if not sessions:
        return None
    session = sessions[0]
    start = _num(session.get("start_time"))
    if start is None or _num(session.get("total_distance")) is None:
        return None
    sport = session.get("sport") if isinstance(session.get("sport"), str) else "unknown"
    sub_sport = (
        session.get("sub_sport") if isinstance(session.get("sub_sport"), str) else None
    )
    per_leg = sport.lower() in STEP_SPORTS
    timer = _Timer(start, _pause_intervals(msgs.get("event_mesgs", []) or []))
    recs = _records(msgs, per_leg, timer)
    summary = _summary(session, recs, per_leg, msgs)
    zones = _zones(msgs)
    if "hr" not in zones:
        z = _hr_zones_from_records(recs, summary.get("hr_max"))
        if z:
            zones["hr"] = z
    laps = [
        _lap_entry(lap, i + 1, per_leg)
        for i, lap in enumerate(msgs.get("lap_mesgs", []) or [])
        if (_num(lap.get("total_timer_time")) or 0) > 0
    ]
    device = None
    for f in msgs.get("file_id_mesgs", []) or []:
        prod = f.get("garmin_product") or f.get("product_name")
        if isinstance(prod, str):
            device = prod
    return {
        "version": SCHEMA_VERSION,
        "run_id": int((start + FIT_EPOCH_S) * 1000),
        "sport": sport,
        "sub_sport": sub_sport,
        "device": device,
        "summary": summary,
        "zones": zones or None,
        "splits": build_km_splits(recs),
        "laps": laps,
        "chart": build_chart(recs),
    }


def analyze_fit(path: str) -> dict | None:
    from garmin_fit_sdk import Decoder, Stream  # noqa: PLC0415

    if os.path.getsize(path) == 0:
        return None
    msgs, errors = Decoder(Stream.from_file(path)).read(
        convert_datetimes_to_dates=False
    )
    if errors:
        raise ValueError(f"FIT decode error: {errors}")
    return analyze_messages(msgs)


# --------------------------------------------------------------------------
# GPX / TCX (e.g. Keep, Strava/Nike exports) -> same internal records
# --------------------------------------------------------------------------
# GPX/TCX carry no timer events, so pauses are inferred: a gap longer than
# PAUSE_GAP_S during which the athlete moved slower than PAUSE_MAX_SPEED is
# removed from timer time (like a FIT timer stop). Shorter gaps are kept.
PAUSE_GAP_S = 30.0
PAUSE_MAX_SPEED = 0.5  # m/s
EARTH_R = 6371008.8
_SOURCE_RANK = {"fit": 0, "tcx": 1, "gpx": 2}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child(el, name: str):
    for c in el:
        if _local(c.tag) == name:
            return c
    return None


def _child_text(el, name: str) -> str | None:
    c = _child(el, name) if el is not None else None
    return c.text.strip() if c is not None and c.text else None


def _find_desc(el, names: tuple[str, ...]) -> str | None:
    """First descendant text whose local tag is in names (extensions)."""
    for c in el.iter():
        if c is not el and _local(c.tag) in names and c.text and c.text.strip():
            return c.text.strip()
    return None


def _parse_time(s: str | None) -> float | None:
    from datetime import datetime, timezone  # noqa: PLC0415

    if not s:
        return None
    s = s.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    )
    return 2 * EARTH_R * math.asin(min(1.0, math.sqrt(h)))


def _norm_sport(raw: str | None) -> str:
    s = (raw or "").strip().lower()
    if not s:
        return "running"
    if "run" in s or s in ("跑步", "1"):
        return "running"
    if "walk" in s:
        return "walking"
    if "hik" in s:
        return "hiking"
    if "bik" in s or "cycl" in s or "ride" in s:
        return "cycling"
    if "swim" in s:
        return "swimming"
    return s


def parse_gpx(text: str | bytes) -> tuple[list[dict], str | None]:
    import xml.etree.ElementTree as ET  # noqa: PLC0415

    root = ET.fromstring(text)
    sport = None
    pts = []
    for trk in root.iter():
        if _local(trk.tag) != "trk":
            continue
        sport = sport or _child_text(trk, "type")
        for p in trk.iter():
            if _local(p.tag) != "trkpt":
                continue
            ext = _child(p, "extensions")
            lat, lon = _num_s(p.get("lat")), _num_s(p.get("lon"))
            pts.append(
                {
                    "ts": _parse_time(_child_text(p, "time")),
                    "pos": (lat, lon) if lat is not None and lon is not None else None,
                    "dist": None,
                    "alt": _num_s(_child_text(p, "ele")),
                    "hr": (
                        _num_s(_find_desc(ext, ("hr", "heartrate")))
                        if ext is not None
                        else None
                    ),
                    "cad": (
                        _num_s(_find_desc(ext, ("cad", "cadence", "runcadence")))
                        if ext is not None
                        else None
                    ),
                    "speed": (
                        _num_s(_find_desc(ext, ("speed",))) if ext is not None else None
                    ),
                    "power": (
                        _num_s(_find_desc(ext, ("power", "watts")))
                        if ext is not None
                        else None
                    ),
                }
            )
    return pts, sport


def parse_tcx(text: str | bytes) -> tuple[list[dict], str | None]:
    import xml.etree.ElementTree as ET  # noqa: PLC0415

    root = ET.fromstring(text)
    sport = None
    pts = []
    for act in root.iter():
        if _local(act.tag) != "activity":
            continue
        sport = sport or act.get("Sport")
        for p in act.iter():
            if _local(p.tag) != "trackpoint":
                continue
            pos = _child(p, "position")
            lat = (
                _num_s(_child_text(pos, "latitudedegrees")) if pos is not None else None
            )
            lon = (
                _num_s(_child_text(pos, "longitudedegrees"))
                if pos is not None
                else None
            )
            hr_el = _child(p, "heartratebpm")
            ext = _child(p, "extensions")
            cad = _num_s(_child_text(p, "cadence"))
            if cad is None and ext is not None:
                cad = _num_s(_find_desc(ext, ("runcadence",)))
            pts.append(
                {
                    "ts": _parse_time(_child_text(p, "time")),
                    "pos": (lat, lon) if lat is not None and lon is not None else None,
                    "dist": _num_s(_child_text(p, "distancemeters")),
                    "alt": _num_s(_child_text(p, "altitudemeters")),
                    "hr": (
                        _num_s(_child_text(hr_el, "value"))
                        if hr_el is not None
                        else None
                    ),
                    "cad": cad,
                    "speed": (
                        _num_s(_find_desc(ext, ("speed",))) if ext is not None else None
                    ),
                    "power": (
                        _num_s(_find_desc(ext, ("watts", "power")))
                        if ext is not None
                        else None
                    ),
                }
            )
    return pts, sport


def _num_s(s: Any) -> float | None:
    if isinstance(s, str):
        try:
            return _num(float(s))
        except ValueError:
            return None
    return _num(s)


def _track_records(
    points: list[dict], per_leg: bool
) -> tuple[list[dict], float, float]:
    """Returns (records, start_ts, elapsed_s). Distance: TCX DistanceMeters when
    present on most points, else haversine along the positions."""
    pts = sorted((p for p in points if p["ts"] is not None), key=lambda p: p["ts"])
    if len(pts) < 2:
        return [], pts[0]["ts"] if pts else 0.0, 0.0
    use_dist = sum(1 for p in pts if p["dist"] is not None) >= 0.8 * len(pts)
    d = 0.0
    last_pos = None
    recs = []
    t = 0.0
    prev_ts = pts[0]["ts"]
    prev_d = 0.0
    for p in pts:
        if use_dist:
            if p["dist"] is not None:
                d = max(d, p["dist"])
        elif p["pos"] is not None:
            if last_pos is not None:
                d += _haversine(last_pos, p["pos"])
            last_pos = p["pos"]
        dt = p["ts"] - prev_ts
        if dt > 0:
            moved = d - prev_d
            if not (dt > PAUSE_GAP_S and moved / dt < PAUSE_MAX_SPEED):
                t += dt
        prev_ts, prev_d = p["ts"], d
        alt = p["alt"]
        if alt is not None and not (-500 < alt < 9000):
            alt = None
        speed = p["speed"]
        if speed is not None and (speed <= 0 or speed >= 65.5):
            speed = None
        recs.append(
            {
                "t": t,
                "d": d,
                "speed": speed,
                "hr": p["hr"] if p["hr"] and p["hr"] > 0 else None,
                "cad": _cadence(p["cad"], None, per_leg),
                "power": p["power"] if p["power"] and p["power"] > 0 else None,
                "alt": alt,
                "vo": None,
                "gct": None,
                "gctb": None,
                "vr": None,
                "step": None,
                "temp": None,
                "resp": None,
            }
        )
    return recs, pts[0]["ts"], pts[-1]["ts"] - pts[0]["ts"]


_EMPTY_SUMMARY_EXTRA = (
    "best_pace",
    "aerobic_te",
    "anaerobic_te",
    "training_load",
    "training_stress_score",
    "intensity_factor",
    "vo2max",
    "temperature_min",
    "temperature_max",
    "steps",
    "rpe",
    "feel",
    "calories",
    "normalized_power",
)


def analyze_track(
    points: list[dict], sport_raw: str | None, source: str
) -> dict | None:
    sport = _norm_sport(sport_raw)
    per_leg = sport in STEP_SPORTS
    recs, start_ts, elapsed = _track_records(points, per_leg)
    if len(recs) < 2 or recs[-1]["d"] <= 0 or recs[-1]["t"] <= 0:
        return None
    summary = _aggregate(recs, recs[-1]["d"], recs[-1]["t"])
    summary.update({k: None for k in _EMPTY_SUMMARY_EXTRA})
    summary["elapsed_time"] = _r(elapsed, 1)
    summary["moving_time"] = _r(recs[-1]["t"], 1)
    z = _hr_zones_from_records(recs, summary.get("hr_max"))
    return {
        "version": SCHEMA_VERSION,
        "run_id": int(round(start_ts * 1000)),
        "sport": sport,
        "sub_sport": None,
        "device": None,
        "source": source,
        "summary": summary,
        "zones": {"hr": z} if z else None,
        "splits": build_km_splits(recs),
        "laps": [],
        "chart": build_chart(recs),
    }


def analyze_gpx(path: str) -> dict | None:
    with open(path, "rb") as f:
        pts, sport = parse_gpx(f.read())
    return analyze_track(pts, sport, "gpx")


def analyze_tcx(path: str) -> dict | None:
    with open(path, "rb") as f:
        raw = f.read().lstrip()  # some exporters prepend whitespace
    pts, sport = parse_tcx(raw)
    return analyze_track(pts, sport, "tcx")


def analyze_file(path: str) -> dict | None:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".gpx":
        return analyze_gpx(path)
    if ext == ".tcx":
        return analyze_tcx(path)
    return analyze_fit(path)


def resolve_run_id(stem: str, start_ms: int, known: set[int]) -> int:
    """Map a GPX/TCX file to the activities.json run_id.

    Keep (and Garmin/Strava downloads) name files ``{activity_id}.gpx`` and use
    that id as run_id; plain GPX imports (gpx_sync) use start time in epoch ms.
    """
    stem_id = int(stem) if stem.isdigit() else None
    if stem_id is not None and stem_id in known:
        return stem_id
    if start_ms in known:
        return start_ms
    # Tolerate second-level rounding differences of start time.
    for delta in (-1000, 1000):
        if start_ms + delta in known:
            return start_ms + delta
    return stem_id if stem_id is not None else start_ms


def load_known_ids(path: str | None) -> set[int]:
    if not path or not os.path.exists(path):
        return set()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {int(a["run_id"]) for a in data if "run_id" in a}
    except (OSError, ValueError, TypeError, KeyError):
        return set()


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _iter_files(dirs: list[str], ext: str):
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.lower().endswith(ext):
                yield os.path.join(d, name)


def _iter_fit_files(dirs: list[str]):
    yield from _iter_files(dirs, ".fit")


def run(
    fit_dirs: list[str],
    out_dir: str,
    force: bool = False,
    quiet: bool = False,
    gpx_dirs: list[str] | None = None,
    tcx_dirs: list[str] | None = None,
    activities: str | None = None,
) -> int:
    os.makedirs(out_dir, exist_ok=True)
    stamp_file = os.path.join(out_dir, ".sources.json")
    try:
        with open(stamp_file, encoding="utf-8") as f:
            sources = json.load(f)
    except (OSError, ValueError):
        sources = {}
    known = load_known_ids(activities)

    def kind_of(key: str) -> str:
        return key.split(":", 1)[0] if ":" in key else "fit"

    # run_id -> best (lowest) source rank already on disk. FIT wins over TCX,
    # TCX (has device distance) over GPX.
    claimed: dict[int, int] = {}
    for key, v in sources.items():
        rid = v.get("run_id") if isinstance(v, dict) else None
        if rid is not None:
            r = _SOURCE_RANK[kind_of(key)]
            claimed[rid] = min(r, claimed.get(rid, r))

    jobs = [("fit", p) for p in _iter_files(fit_dirs, ".fit")]
    jobs += [("tcx", p) for p in _iter_files(tcx_dirs or [], ".tcx")]
    jobs += [("gpx", p) for p in _iter_files(gpx_dirs or [], ".gpx")]
    written = skipped = failed = shadowed = 0
    for kind, path in jobs:
        name = os.path.basename(path)
        key = name if kind == "fit" else f"{kind}:{name}"
        rank = _SOURCE_RANK[kind]
        mtime = os.path.getmtime(path)
        known_src = sources.get(key)
        if (
            not force
            and known_src
            and known_src.get("mtime") == mtime
            and (
                known_src.get("run_id") is None
                or os.path.exists(os.path.join(out_dir, f"{known_src['run_id']}.json"))
            )
            and (
                known_src.get("run_id") is None
                or claimed.get(known_src["run_id"], rank) >= rank
            )
        ):
            skipped += 1
            continue
        try:
            if os.path.getsize(path) == 0:
                data = None
            else:
                data = analyze_file(path)
        except Exception as e:  # noqa: BLE001
            failed += 1
            if not quiet:
                print(f"[splits] skip {key}: {e}")
            continue
        if not data:
            sources[key] = {"mtime": mtime, "run_id": None}
            continue
        if kind != "fit":
            stem = os.path.splitext(name)[0]
            data["run_id"] = resolve_run_id(stem, data["run_id"], known)
        rid = data["run_id"]
        if claimed.get(rid, rank) < rank:
            sources[key] = {"mtime": mtime, "run_id": None, "shadowed_by": rid}
            shadowed += 1
            continue
        claimed[rid] = rank
        with open(os.path.join(out_dir, f"{rid}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        sources[key] = {"mtime": mtime, "run_id": rid}
        written += 1
    ids = sorted(
        int(n[:-5])
        for n in os.listdir(out_dir)
        if n.endswith(".json") and n[:-5].isdigit()
    )
    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(ids, f, separators=(",", ":"))
    with open(stamp_file, "w", encoding="utf-8") as f:
        json.dump(sources, f, separators=(",", ":"))
    print(
        f"[splits] written={written} skipped={skipped} shadowed={shadowed} "
        f"failed={failed} total={len(ids)} -> {out_dir}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--fit-dir",
        action="append",
        help=f"FIT folder (repeatable, default {DEFAULT_FIT_DIR})",
    )
    p.add_argument(
        "--gpx-dir",
        action="append",
        help=f"GPX folder (repeatable, default {DEFAULT_GPX_DIR})",
    )
    p.add_argument(
        "--tcx-dir",
        action="append",
        help=f"TCX folder (repeatable, default {DEFAULT_TCX_DIR})",
    )
    p.add_argument("--fit-only", action="store_true", help="ignore GPX/TCX folders")
    p.add_argument(
        "--activities",
        default=DEFAULT_ACTIVITIES,
        help="activities.json used to map GPX/TCX files to run_id",
    )
    p.add_argument(
        "--out",
        default=DEFAULT_OUT_DIR,
        help=f"output folder (default {DEFAULT_OUT_DIR})",
    )
    p.add_argument("--force", action="store_true", help="rebuild all files")
    p.add_argument(
        "--file", help="analyze one FIT/GPX/TCX file and print JSON to stdout"
    )
    a = p.parse_args(argv)
    if a.file:
        print(json.dumps(analyze_file(a.file), ensure_ascii=False, indent=2))
        return 0
    return run(
        a.fit_dir or [DEFAULT_FIT_DIR],
        a.out,
        a.force,
        gpx_dirs=[] if a.fit_only else (a.gpx_dir or [DEFAULT_GPX_DIR]),
        tcx_dirs=[] if a.fit_only else (a.tcx_dir or [DEFAULT_TCX_DIR]),
        activities=a.activities,
    )


if __name__ == "__main__":
    sys.exit(main())
