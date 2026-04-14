import datetime
import math
import os
import sys

import arrow
import polyline as polyline_codec
import stravalib
from gpxtrackposter import track_loader
from sqlalchemy import func

from polyline_processor import filter_out

from .db import Activity, init_db, update_or_create_activity

# Bounding box spread threshold (degrees) for indoor activity detection.
# 0.002° ≈ 220m — treadmill GPS drift typically stays within this range.
INDOOR_SPREAD_THRESHOLD = float(os.getenv("INDOOR_SPREAD_THRESHOLD", "0.002"))

# Distance (degrees) to decide if a route is a loop (start ≈ end).
_LOOP_CLOSE_THRESHOLD = 0.003  # ~330m


def _haversine(lat1, lon1, lat2, lon2):
    """Return distance in metres between two WGS-84 points."""
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _interpolate(p1, p2, frac):
    """Linearly interpolate between two (lat, lng) points."""
    return (p1[0] + (p2[0] - p1[0]) * frac, p1[1] + (p2[1] - p1[1]) * frac)


def _route_length_m(coords):
    """Total length of a polyline in metres."""
    total = 0.0
    for i in range(len(coords) - 1):
        total += _haversine(
            coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1]
        )
    return total


def _is_loop(coords):
    """True if start and end are close enough to treat as a loop."""
    if len(coords) < 3:
        return False
    d = abs(coords[0][0] - coords[-1][0]) + abs(coords[0][1] - coords[-1][1])
    return d < _LOOP_CLOSE_THRESHOLD


def _build_route_for_distance(ref_coords, target_m):
    """Build a route of *target_m* metres along *ref_coords*.

    - If target_m <= reference route length, truncate.
    - If target_m > reference route length:
      - Loop route → keep cycling around.
      - Traverse route → ping-pong (out-and-back).
    Returns a list of (lat, lng) tuples.
    """
    if len(ref_coords) < 2 or target_m <= 0:
        return ref_coords[:1] if ref_coords else []

    loop = _is_loop(ref_coords)
    result = [ref_coords[0]]
    accumulated = 0.0

    # Build an iterator that yields successive points along the reference,
    # repeating as needed (loop or ping-pong).
    def _point_iter():
        """Yield (lat, lng) points indefinitely along the reference route."""
        forward = True
        idx = 0
        while True:
            yield ref_coords[idx]
            if forward:
                idx += 1
                if idx >= len(ref_coords):
                    if loop:
                        idx = 1  # skip duplicate start=end, wrap around
                    else:
                        forward = False
                        idx = len(ref_coords) - 2
            else:
                idx -= 1
                if idx < 0:
                    forward = True
                    idx = 1

    it = _point_iter()
    prev = next(it)  # first point (already in result)

    for pt in it:
        seg = _haversine(prev[0], prev[1], pt[0], pt[1])
        if seg < 0.01:
            prev = pt
            continue
        if accumulated + seg >= target_m:
            frac = (target_m - accumulated) / seg
            result.append(_interpolate(prev, pt, frac))
            break
        accumulated += seg
        result.append(pt)
        prev = pt
        # Safety: don't generate absurdly long polylines
        if len(result) > 50_000:
            break

    return result


from synced_data_file_logger import save_synced_data_file_list

IGNORE_BEFORE_SAVING = os.getenv("IGNORE_BEFORE_SAVING", False)


class Generator:
    def __init__(self, db_path):
        self.client = stravalib.Client()
        self.session = init_db(db_path)

        self.client_id = ""
        self.client_secret = ""
        self.refresh_token = ""
        self.only_run = False

    def set_strava_config(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

    def check_access(self):
        response = self.client.refresh_access_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=self.refresh_token,
        )
        # Update the authdata object
        self.access_token = response["access_token"]
        self.refresh_token = response["refresh_token"]

        self.client.access_token = response["access_token"]
        print("Access ok")

    def sync(self, force):
        """
        Sync activities means sync from strava
        TODO, better name later
        """
        self.check_access()

        print("Start syncing")
        if force:
            filters = {"before": datetime.datetime.now(datetime.timezone.utc)}
        else:
            last_activity = self.session.query(func.max(Activity.start_date)).scalar()
            if last_activity:
                last_activity_date = arrow.get(last_activity)
                last_activity_date = last_activity_date.shift(days=-7)
                filters = {"after": last_activity_date.datetime}
            else:
                filters = {"before": datetime.datetime.now(datetime.timezone.utc)}

        for activity in self.client.get_activities(**filters):
            if self.only_run and activity.type != "Run":
                continue
            if IGNORE_BEFORE_SAVING:
                if activity.map and activity.map.summary_polyline:
                    activity.map.summary_polyline = filter_out(
                        activity.map.summary_polyline
                    )
            #  strava use total_elevation_gain as elevation_gain
            activity.elevation_gain = activity.total_elevation_gain
            activity.subtype = activity.type
            created = update_or_create_activity(self.session, activity)
            if created:
                sys.stdout.write("+")
            else:
                sys.stdout.write(".")
            sys.stdout.flush()
        self.session.commit()

    def sync_from_data_dir(self, data_dir, file_suffix="gpx", activity_title_dict={}):
        loader = track_loader.TrackLoader()
        tracks = loader.load_tracks(
            data_dir, file_suffix=file_suffix, activity_title_dict=activity_title_dict
        )
        print(f"load {len(tracks)} tracks")
        if not tracks:
            print("No tracks found.")
            return

        synced_files = []

        for t in tracks:
            created = update_or_create_activity(
                self.session, t.to_namedtuple(run_from=file_suffix)
            )
            if created:
                sys.stdout.write("+")
            else:
                sys.stdout.write(".")
            synced_files.extend(t.file_names)
            sys.stdout.flush()

        save_synced_data_file_list(synced_files)

        self.session.commit()

    def sync_from_app(self, app_tracks):
        if not app_tracks:
            print("No tracks found.")
            return
        print("Syncing tracks '+' means new track '.' means update tracks")
        synced_files = []
        for t in app_tracks:
            created = update_or_create_activity(self.session, t)
            if created:
                sys.stdout.write("+")
            else:
                sys.stdout.write(".")
            if "file_names" in t:
                synced_files.extend(t.file_names)
            sys.stdout.flush()

        self.session.commit()

    def load(self):
        # if sub_type is not in the db, just add an empty string to it
        query = self.session.query(Activity).filter(Activity.distance > 0.1)
        if self.only_run:
            query = query.filter(Activity.type == "Run")

        activities = query.order_by(Activity.start_date_local)
        activity_list = []

        streak = 0
        last_date = None
        for activity in activities:
            # Determine running streak.
            date = datetime.datetime.strptime(
                activity.start_date_local, "%Y-%m-%d %H:%M:%S"  # type: ignore
            ).date()
            if last_date is None:
                streak = 1
            elif date == last_date:
                pass
            elif date == last_date + datetime.timedelta(days=1):
                streak += 1
            else:
                assert date > last_date
                streak = 1
            activity.streak = streak  # type: ignore
            last_date = date
            if not IGNORE_BEFORE_SAVING:
                activity.summary_polyline = filter_out(activity.summary_polyline)  # type: ignore
            activity_list.append(activity.to_dict())

        activity_list = self._fix_indoor_locations(activity_list)

        # Persist indoor subtype and virtual polyline back to DB so SVG generation can pick it up
        for a in activity_list:
            if a.get("subtype") == "indoor":
                db_activity = self.session.query(Activity).get(a["run_id"])
                if db_activity:
                    if db_activity.subtype != "indoor":
                        db_activity.subtype = "indoor"
                    poly = a.get("summary_polyline", "")
                    if poly and not db_activity.summary_polyline:
                        db_activity.summary_polyline = poly
        self.session.commit()

        return activity_list

    @staticmethod
    def _fix_indoor_locations(activity_list):
        """Replace indoor activity polylines with routes derived from the
        nearest previous outdoor activity.

        Indoor activities are identified by a multi-strategy approach:
        1. Subtype match: known indoor subtypes from data sources
           (Garmin FIT "treadmill", Strava/Keep "VirtualRun", etc.)
        2. No GPS data: activity has distance but empty polyline
        3. Tiny GPS spread: bounding box < ~10 m (noisy indoor GPS)
        For each indoor activity we:
        1. Take the most recent preceding outdoor route as reference.
        2. Truncate or extend it to match the indoor run's distance.
           - Loop routes (start ≈ end): keep cycling around.
           - Traverse routes: ping-pong (out-and-back).
        """
        if not activity_list:
            return activity_list

        INDOOR_SUBTYPES = {
            "treadmill",  # Garmin FIT sub_sport
            "indoor",  # generic indoor marker
            "virtualrun",  # Strava / Keep indoor running
            "virtual_run",  # alternate form
        }
        # ~10 m in degrees (0.0001° ≈ 11 m)
        TINY_SPREAD_THRESHOLD = 0.0001

        # Classify each activity as indoor or outdoor and cache decoded coords
        classified = []  # (dict, is_indoor, decoded_coords_or_None)
        for a in activity_list:
            subtype = (a.get("subtype") or "").lower()
            is_indoor = subtype in INDOOR_SUBTYPES

            poly = a.get("summary_polyline") or ""
            coords = None
            if poly:
                try:
                    coords = polyline_codec.decode(poly)
                    if len(coords) < 2:
                        coords = None
                except Exception:
                    coords = None

            # Strategy 2: no GPS data but has distance → indoor
            if not is_indoor and coords is None and a.get("distance", 0) > 100:
                is_indoor = True

            # Strategy 3: tiny GPS spread → noisy indoor GPS
            if not is_indoor and coords and len(coords) >= 2:
                lats = [c[0] for c in coords]
                lngs = [c[1] for c in coords]
                spread = max(max(lats) - min(lats), max(lngs) - min(lngs))
                if spread < TINY_SPREAD_THRESHOLD:
                    is_indoor = True

            classified.append((a, is_indoor, coords))

        # Replace indoor polylines using nearest previous outdoor route
        last_outdoor_coords = None
        last_outdoor_location = None
        indoor_count = 0
        for a, is_indoor, coords in classified:
            if not is_indoor:
                if coords is not None:
                    last_outdoor_coords = coords
                    last_outdoor_location = a.get("location_country")
            else:
                if last_outdoor_coords is not None:
                    target_m = a.get("distance", 0)
                    route = _build_route_for_distance(last_outdoor_coords, target_m)
                    if len(route) >= 2:
                        a["summary_polyline"] = polyline_codec.encode(route)
                    if not a.get("location_country") and last_outdoor_location:
                        a["location_country"] = last_outdoor_location
                    # Normalize subtype to "indoor" for frontend/SVG
                    a["subtype"] = "indoor"
                    indoor_count += 1

        if indoor_count > 0:
            print(
                f"\n  Fixed {indoor_count} indoor activities "
                f"with route from nearest outdoor activity"
            )

        return activity_list

    def get_old_tracks_ids(self):
        try:
            activities = self.session.query(Activity).all()
            return [str(a.run_id) for a in activities]
        except Exception as e:
            # pass the error
            print(f"something wrong with {str(e)}")
            return []

    def get_old_tracks_dates(self):
        try:
            activities = (
                self.session.query(Activity)
                .order_by(Activity.start_date_local.desc())
                .all()
            )
            return [str(a.start_date_local) for a in activities]
        except Exception as e:
            # pass the error
            print(f"something wrong with {str(e)}")
            return []
