# some code from
# https://github.com/DreamMryang/synchronizeTheRecordingOfOnelapToGiant.git
# https://github.com/moruoxian/SyncOnelapToXoss.git
# great thanks

import argparse
import base64
import hashlib
import json
import os
import time
import uuid
from urllib.parse import unquote, urlparse

import requests
from config import FIT_FOLDER

SIGNIN_URL = "https://www.onelap.cn/api/login"
BASE_APP_URL = "https://u.onelap.cn"
RECORD_PAGE_URL = f"{BASE_APP_URL}/recordPage"
LIST_URL = f"{BASE_APP_URL}/api/otm/ride_record/list"
DETAIL_URL = f"{BASE_APP_URL}/api/otm/ride_record/analysis/{{record_id}}"
FIT_DOWNLOAD_URL = f"{BASE_APP_URL}/api/otm/ride_record/analysis/fit_content/{{fit_key}}"
SIGN_KEY = "fe9f8382418fcdeb136461cac6acae7b"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"


def process_fit(file_content, fix_gcj02=True):
    """Post-process a downloaded Onelap FIT:

    - fill lap/session positions and lap event fields so Garmin Connect can
      draw the per-kilometer markers (Onelap/Magene strips them: laps have
      no start_position and session has no start position or event)
    - optionally convert GCJ-02 -> WGS-84 (Onelap exports FIT with GCJ-02
      coordinates, which show a ~500m offset in Garmin Connect; verified
      against Onelap's own start_location and OSM roads)
    """
    import logging

    import eviltransform
    from fit_tool.definition_message import DefinitionMessage
    from fit_tool.fit_file import FitFile
    from fit_tool.fit_file_builder import FitFileBuilder
    from fit_tool.profile.messages.lap_message import LapMessage
    from fit_tool.profile.messages.record_message import RecordMessage
    from fit_tool.profile.messages.session_message import SessionMessage

    # fit_tool logs a benign byte-diff warning per record when re-encoding
    # on read; the data itself roundtrips correctly, so keep it quiet
    logging.getLogger("fit_tool").setLevel(logging.ERROR)

    fit = FitFile.from_bytes(file_content)

    # record position timeline (degrees), sorted by timestamp
    timeline = sorted(
        (msg.timestamp, msg.position_lat, msg.position_long)
        for msg in (record.message for record in fit.records)
        if isinstance(msg, RecordMessage)
        and msg.timestamp is not None
        and msg.position_lat is not None
        and msg.position_long is not None
    )

    def position_at_or_after(when):
        if not timeline:
            return None, None
        for ts, lat, lng in timeline:
            if ts >= when:
                return lat, lng
        return timeline[0][1], timeline[0][2]

    def position_at_or_before(when):
        result = (None, None)
        for ts, lat, lng in timeline:
            if ts > when:
                break
            result = (lat, lng)
        if result == (None, None) and timeline:
            return timeline[-1][1], timeline[-1][2]
        return result

    changed = False
    lap_index = 0
    session_sport = None
    for record in fit.records:
        msg = record.message
        if isinstance(msg, SessionMessage) and getattr(msg, "sport", None):
            session_sport = msg.sport

    def open_fields(msg):
        # fields absent from the parsed definition start out non-growable;
        # allow growth so newly set values (positions, event fields) survive
        for field in msg.fields:
            field.growable = True

    for record in fit.records:
        msg = record.message
        if isinstance(msg, LapMessage):
            if (
                timeline
                and msg.start_time is not None
                and getattr(msg, "start_position_lat", None) is None
            ):
                open_fields(msg)
                msg.start_position_lat, msg.start_position_long = (
                    position_at_or_after(msg.start_time)
                )
                # fit_tool returns timestamps as unix milliseconds
                end_ts = msg.start_time + (msg.total_elapsed_time or 0) * 1000
                msg.end_position_lat, msg.end_position_long = position_at_or_before(
                    end_ts
                )
                # fit_tool enum setters take the raw profile int, not the name
                msg.event = 9  # lap
                msg.event_type = 1  # stop
                if getattr(msg, "sport", None) is None:
                    msg.sport = session_sport if session_sport is not None else 2
                if getattr(msg, "sub_sport", None) is None:
                    msg.sub_sport = 0  # generic
                if getattr(msg, "lap_trigger", None) is None:
                    msg.lap_trigger = 2  # distance
                if getattr(msg, "intensity", None) is None:
                    msg.intensity = 0  # active
                if getattr(msg, "message_index", None) is None:
                    msg.message_index = lap_index
                # drop the old definition so FitFileBuilder regenerates it
                # with the newly set fields
                msg.definition_message = None
                changed = True
            lap_index += 1
        elif isinstance(msg, SessionMessage):
            if timeline and getattr(msg, "start_position_lat", None) is None:
                open_fields(msg)
                msg.start_position_lat, msg.start_position_long = (
                    timeline[0][1],
                    timeline[0][2],
                )
                if getattr(msg, "event", None) is None:
                    msg.event = 8  # session
                if getattr(msg, "event_type", None) is None:
                    msg.event_type = 1  # stop
                if getattr(msg, "message_index", None) is None:
                    msg.message_index = 0
                # fit_tool's session profile has no end_position fields
                msg.definition_message = None
                changed = True

    if fix_gcj02 and timeline:
        for record in fit.records:
            msg = record.message
            for lat_key, lng_key in (
                ("position_lat", "position_long"),
                ("start_position_lat", "start_position_long"),
                ("end_position_lat", "end_position_long"),
            ):
                lat, lng = getattr(msg, lat_key, None), getattr(msg, lng_key, None)
                if lat is not None and lng is not None:
                    wgs_lat, wgs_lng = eviltransform.gcj2wgs_exact(lat, lng)
                    setattr(msg, lat_key, wgs_lat)
                    setattr(msg, lng_key, wgs_lng)
        changed = True

    if not changed:
        return file_content

    # rebuild so regenerated definitions (lap/session positions) are written
    builder = FitFileBuilder(auto_define=True)
    for record in fit.records:
        msg = record.message
        if isinstance(msg, DefinitionMessage):
            continue
        # fit_tool never passes the record header's local id into parsed
        # definitions (defaults to 0), which would make the builder collapse
        # every message onto local 0 and re-emit a definition before each
        # one; restore it from the header
        msg.local_id = record.header.local_id
        if msg.definition_message is not None:
            msg.definition_message.local_id = record.header.local_id
        builder.add(msg)
    print(
        f"FIT processed: {lap_index} laps"
        f"{' + GCJ-02 -> WGS-84' if fix_gcj02 else ''}"
    )
    return builder.build().to_bytes()


class Onelap:
    def __init__(self, account, password, fix_gcj02=False):
        self.account = account
        self.password = password
        self.fix_gcj02 = fix_gcj02
        self.session = None

    def login(self):
        nonce = uuid.uuid4().hex[:16]
        timestamp = str(int(time.time()))
        sign = hashlib.md5(
            f"account={self.account}&nonce={nonce}&***".encode()
        ).hexdigest()
        headers = {"nonce": nonce, "timestamp": timestamp, "sign": sign}

        try:
            login_response = requests.post(
                SIGNIN_URL,
                json={
                    "account": self.account,
                    "password": hashlib.md5(self.password.encode()).hexdigest(),
                },
                headers=headers,
            )
            login_response.raise_for_status()
            login_response = login_response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP POST request failed: {e}")

        data = login_response.get("data", [])
        if not data:
            raise RuntimeError(login_response.get("error"))

        return data[0]

    @staticmethod
    def sign_headers(params):
        nonce = uuid.uuid4().hex[:16]
        timestamp = str(int(time.time()))
        all_params = {**params, "nonce": nonce, "timestamp": timestamp}
        parts = [f"{key}={value}" for key, value in sorted(all_params.items())]
        string_to_sign = "&".join(parts) + f"&key={SIGN_KEY}"
        sign = hashlib.md5(string_to_sign.encode()).hexdigest()
        return {"nonce": nonce, "timestamp": timestamp, "sign": sign}

    def build_session(self):
        login_data = self.login()
        token = login_data.get("token")
        if not token:
            raise RuntimeError(login_data.get("error") or "login failed: no token")

        session = requests.Session()
        session.headers.update(
            {
                "Authorization": token,
                "User-Agent": USER_AGENT,
                "Origin": BASE_APP_URL,
                "Referer": RECORD_PAGE_URL,
            }
        )
        return session

    def get_session(self):
        if self.session is None:
            self.session = self.build_session()
        return self.session

    def post_list(self, payload):
        session = self.get_session()
        try:
            response = session.post(
                LIST_URL,
                json=payload,
                headers=self.sign_headers(payload),
                timeout=30,
            )
            response.raise_for_status()
            body = response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP POST request failed: {e}")

        data = body.get("data") or {}
        if not isinstance(data, dict):
            raise RuntimeError(f"unexpected list response: {body}")
        return data

    def get_activities(self):
        # first request fetches the first page and the total count,
        # then one more request pulls everything at once
        data = self.post_list({"page": 1, "limit": 20})
        activities = data.get("list") or []
        pagination = data.get("pagination") or {}
        total = data.get("total") or pagination.get("total") or 0
        if total > len(activities):
            activities = self.post_list({"page": 1, "limit": total}).get(
                "list"
            ) or activities

        if not activities:
            raise RuntimeError("no data returned.")

        return activities

    def list_activities(self):
        activities = self.get_activities()
        print(f"{len(activities)} activities")
        print(json.dumps(activities, ensure_ascii=False, indent=2))

    @staticmethod
    def find_fit_url(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in {"fiturl", "fit_url"} and item:
                    return str(item).strip()
                found = Onelap.find_fit_url(item)
                if found:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = Onelap.find_fit_url(item)
                if found:
                    return found
        return ""

    @staticmethod
    def fit_download_candidates(fit_url):
        candidates = [fit_url, unquote(fit_url)]
        if fit_url.startswith(("http://", "https://")):
            path = urlparse(fit_url).path
            candidates.append(path)
            if path:
                candidates.append(path.rsplit("/", 1)[-1])
        elif "/" in fit_url:
            candidates.append(fit_url.rsplit("/", 1)[-1])

        seen = set()
        unique = []
        for candidate in candidates:
            if candidate and candidate not in seen:
                seen.add(candidate)
                unique.append(candidate)
        return unique

    def get_fit_url(self, activity):
        """Return (record_id, fit_url) for one activity."""
        record_id = str(activity.get("_id") or activity.get("id") or "").strip()
        if not record_id:
            return "", ""

        session = self.get_session()
        try:
            response = session.get(DETAIL_URL.format(record_id=record_id), timeout=30)
            response.raise_for_status()
            detail = response.json().get("data") or {}
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP GET request failed: {e}")

        riding_record = detail.get("ridingRecord") or {}
        fit_url = str(riding_record.get("fitUrl") or "").strip()
        if not fit_url:
            fit_url = self.find_fit_url(detail)
        return record_id, fit_url

    def download_onelap_data(self):
        activities = self.get_activities()
        os.makedirs(FIT_FOLDER, exist_ok=True)
        session = self.get_session()
        for activity in activities:
            record_id, fit_url = self.get_fit_url(activity)
            if not fit_url:
                print(f"skip {record_id or activity}: no fit file")
                continue

            file_name = os.path.basename(unquote(fit_url)) or f"{record_id}.fit"
            file_path = os.path.join(FIT_FOLDER, file_name)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print(f"already exists {file_name}")
                continue

            for candidate in self.fit_download_candidates(fit_url):
                fit_key = base64.b64encode(candidate.encode()).decode()
                response = session.get(
                    FIT_DOWNLOAD_URL.format(fit_key=fit_key), timeout=60
                )
                if response.status_code == 200 and response.content:
                    content = process_fit(response.content, self.fix_gcj02)
                    with open(file_path, "wb") as file:
                        file.write(content)
                    print(f"download {file_name}")
                    break
            else:
                print(f"Failed to download {file_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("account", help="Onelap account")
    parser.add_argument("password", help="Onelap password")
    parser.add_argument(
        "--with-fit",
        dest="with_fit",
        action="store_true",
        help="get all Onelap data to fit and download",
    )
    parser.add_argument(
        "--gcj02",
        dest="gcj02",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="convert GCJ-02 coordinates in downloaded FIT to WGS-84, on by "
        "default (Onelap FIT exports are GCJ-02 and offset ~500m on Garmin); "
        "use --no-gcj02 to keep the original coordinates",
    )
    options = parser.parse_args()

    onelap = Onelap(options.account, options.password, fix_gcj02=options.gcj02)
    if options.with_fit:
        onelap.download_onelap_data()
    else:
        onelap.list_activities()
