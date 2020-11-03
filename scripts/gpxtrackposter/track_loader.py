"""Handle parsing of GPX files and writing/loading of cached data"""


# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import hashlib
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import shutil
import concurrent.futures
from .exceptions import ParameterError, TrackLoadError
from .track import Track
from .year_range import YearRange

from generator.db import init_db, Activity

log = logging.getLogger(__name__)


def load_gpx_file(file_name):
    """Load an individual GPX file as a track by using Track.load_gpx()"""
    t = Track()
    t.load_gpx(file_name)
    return t


def load_cached_track_file(cache_file_name, file_name):
    """Load an individual track from cache files"""
    try:
        t = Track()
        t.load_cache(cache_file_name)
        t.file_names = [os.path.basename(file_name)]
        log.info(f"Loaded track {file_name} from cache file {cache_file_name}")
        return t
    except Exception as e:
        raise TrackLoadError("Failed to load track from cache.") from e


class TrackLoader:
    """Handle the loading of tracks from cache and/or GPX files

    Attributes:
        min_length: All tracks shorter than this value are filtered out.
        special_file_names: Tracks marked as special in command line args
        year_range: All tracks outside of this range will be filtered out.
        cache_dir: Directory used to store cached tracks

    Methods:
        clear_cache: Remove cache directory
        load_tracks: Load all data from cache and GPX files
    """

    def __init__(self):
        self.min_length = 1000
        self.special_file_names = []
        self.year_range = YearRange()
        self.cache_dir = None
        self._cache_file_names = {}

    def clear_cache(self):
        """Remove cache directory, if it exists"""
        if os.path.isdir(self.cache_dir):
            log.info(f"Removing cache dir: {self.cache_dir}")
            try:
                shutil.rmtree(self.cache_dir)
            except OSError as e:
                log.error(f"Failed: {e}")

    def load_tracks(self, base_dir):
        """Load tracks base_dir and return as a List of tracks"""
        file_names = [x for x in self._list_gpx_files(base_dir)]
        log.info(f"GPX files: {len(file_names)}")
        print(len(file_names))

        tracks = []

        # load track from cache
        cached_tracks = {}
        # self.clear_cache()
        if self.cache_dir:
            log.info(f"Trying to load {len(file_names)} track(s) from cache...")
            cached_tracks = self._load_tracks_from_cache(file_names)
            log.info(f"Loaded tracks from cache: {len(cached_tracks)}")
            tracks = list(cached_tracks.values())

        # load remaining gpx files
        remaining_file_names = [f for f in file_names if f not in cached_tracks]
        if remaining_file_names:
            log.info(
                f"Trying to load {len(remaining_file_names)} track(s) from GPX files; this may take a while..."
            )
            loaded_tracks = self._load_tracks(remaining_file_names)
            tracks.extend(loaded_tracks.values())
            log.info(f"Conventionally loaded tracks: {len(loaded_tracks)}")
            self._store_tracks_to_cache(loaded_tracks)

        tracks = self._filter_tracks(tracks)

        # merge tracks that took place within one hour
        tracks = self._merge_tracks(tracks)
        # filter out tracks with length < min_length
        return [t for t in tracks if t.length >= self.min_length]

    def load_tracks_from_db(self, sql_file, is_grid=False):
        session = init_db(sql_file)
        if is_grid:
            activities = (
                session.query(Activity)
                .filter(Activity.summary_polyline != "")
                .order_by(Activity.start_date_local)
            )
        else:
            activities = session.query(Activity).order_by(Activity.start_date_local)
        tracks = []
        for activate in activities:
            t = Track()
            t.load_from_db(activate)
            tracks.append(t)
        print(len(tracks))
        tracks = self._filter_tracks(tracks)
        print(len(tracks))
        # merge tracks that took place within one hour
        tracks = self._merge_tracks(tracks)
        return [t for t in tracks if t.length >= self.min_length]

    def _filter_tracks(self, tracks):
        filtered_tracks = []
        for t in tracks:
            file_name = t.file_names[0]
            if int(t.length) == 0:
                log.info(f"{file_name}: skipping empty track")
            elif not t.start_time_local:
                log.info(f"{file_name}: skipping track without start time")
            elif not self.year_range.contains(t.start_time_local):
                log.info(
                    f"{file_name}: skipping track with wrong year {t.start_time_local.year}"
                )
            else:
                t.special = file_name in self.special_file_names
                filtered_tracks.append(t)
        return filtered_tracks

    @staticmethod
    def _merge_tracks(tracks):
        log.info("Merging tracks...")
        tracks = sorted(tracks, key=lambda t1: t1.start_time_local)
        merged_tracks = []
        last_end_time = None
        for t in tracks:
            if last_end_time is None:
                merged_tracks.append(t)
            else:
                dt = (t.start_time_local - last_end_time).total_seconds()
                if 0 < dt < 3600:
                    merged_tracks[-1].append(t)
                else:
                    merged_tracks.append(t)
            last_end_time = t.end_time_local
        log.info(f"Merged {len(tracks) - len(merged_tracks)} track(s)")
        return merged_tracks

    @staticmethod
    def _load_tracks(file_names):
        tracks = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_file_name = {
                executor.submit(load_gpx_file, file_name): file_name
                for file_name in file_names
            }
        for future in concurrent.futures.as_completed(future_to_file_name):
            file_name = future_to_file_name[future]
            try:
                t = future.result()
            except TrackLoadError as e:
                log.error(f"Error while loading {file_name}: {e}")
            else:
                tracks[file_name] = t

        return tracks

    def _load_tracks_from_cache(self, file_names):
        tracks = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_file_name = {
                executor.submit(
                    load_cached_track_file,
                    self._get_cache_file_name(file_name),
                    file_name,
                ): file_name
                for file_name in file_names
            }
        for future in concurrent.futures.as_completed(future_to_file_name):
            file_name = future_to_file_name[future]
            try:
                t = future.result()
            except Exception:
                # silently ignore failed cache load attempts
                pass
            else:
                tracks[file_name] = t
        return tracks

    def _store_tracks_to_cache(self, tracks):
        if (not tracks) or (not self.cache_dir):
            return

        log.info(f"Storing {len(tracks)} track(s) to cache...")
        for (file_name, t) in tracks.items():
            try:
                t.store_cache(self._get_cache_file_name(file_name))
            except Exception as e:
                log.error(f"Failed to store track {file_name} to cache: {e}")
            else:
                log.info(f"Stored track {file_name} to cache")

    @staticmethod
    def _list_gpx_files(base_dir):
        base_dir = os.path.abspath(base_dir)
        if not os.path.isdir(base_dir):
            raise ParameterError(f"Not a directory: {base_dir}")
        for name in os.listdir(base_dir):
            if name.startswith("."):
                continue
            path_name = os.path.join(base_dir, name)
            if name.endswith(".gpx") and os.path.isfile(path_name):
                yield path_name

    def _get_cache_file_name(self, file_name):
        assert self.cache_dir

        if file_name in self._cache_file_names:
            return self._cache_file_names[file_name]

        try:
            checksum = hashlib.sha256(open(file_name, "rb").read()).hexdigest()
        except PermissionError as e:
            raise TrackLoadError("Failed to compute checksum (bad permissions).") from e
        except Exception as e:
            raise TrackLoadError("Failed to compute checksum.") from e

        cache_file_name = os.path.join(self.cache_dir, f"{checksum}.json")
        self._cache_file_names[file_name] = cache_file_name
        return cache_file_name
