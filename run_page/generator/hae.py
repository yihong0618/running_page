"""Ownership and route privacy metadata for Health Auto Export activities."""

import hashlib
import json

import polyline_processor
from sqlalchemy import Column, Integer, MetaData, String, Table, inspect, select

workout_ids = Table(
    "health_auto_export_workouts",
    MetaData(),
    Column("id_digest", String, primary_key=True),
    Column("run_id", Integer, nullable=False, unique=True),
    Column("route_policy", String, nullable=False),
)


def route_policy():
    settings = json.dumps(
        [
            polyline_processor.IGNORE_START_END_RANGE,
            polyline_processor.IGNORE_RANGE,
            polyline_processor.IGNORE_POLYLINE,
        ]
    )
    return hashlib.sha256(settings.encode()).hexdigest()


def filter_route(encoded):
    if polyline_processor.IGNORE_START_END_RANGE > 0 or (
        polyline_processor.IGNORE_RANGE > 0 and polyline_processor.IGNORE_POLYLINE
    ):
        return polyline_processor.filter_out(encoded)
    return encoded


def saved_route_policies(session):
    if not inspect(session.connection()).has_table(workout_ids.name):
        return {}
    return dict(
        session.execute(select(workout_ids.c.run_id, workout_ids.c.route_policy)).all()
    )
