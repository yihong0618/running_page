import importlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from requests import HTTPError


@pytest.fixture
def drive(monkeypatch):
    pytest.importorskip("google.auth")
    monkeypatch.syspath_prepend(str(Path(__file__).parent / "run_page"))
    return importlib.import_module("health_auto_export_drive")


def response(payload=None, *, content=b"", error=None):
    result = Mock(content=content)
    result.json.return_value = payload
    result.raise_for_status.side_effect = error
    return result


def test_download_and_import_paginated_exports(drive, tmp_path):
    importer = importlib.import_module("health_auto_export_sync")
    client = Mock()
    folder = response({"mimeType": "application/vnd.google-apps.folder"})
    page_one = response(
        {
            "nextPageToken": "next",
            "files": [
                {"id": "new", "name": "../new.json", "modifiedTime": "2026-01-02Z"},
                {"id": "skip", "name": "other.csv"},
            ],
        }
    )
    page_two = response(
        {"files": [{"id": "old", "name": "same.json", "modifiedTime": "2026-01-01Z"}]}
    )

    def export(distance):
        return json.dumps(
            {
                "data": {
                    "workouts": [
                        {
                            "id": "same-run",
                            "name": "室内 跑步",
                            "start": "2026-01-01 08:00:00 +0800",
                            "end": "2026-01-01 08:25:00 +0800",
                            "duration": 1500,
                            "distance": {"qty": distance, "units": "km"},
                        }
                    ]
                }
            }
        ).encode()

    client.get.side_effect = [
        folder,
        page_one,
        page_two,
        response(content=export(4)),
        response(content=export(5)),
    ]
    exports = tmp_path / "downloads"
    exports.mkdir()
    assert drive.download_exports(client, "test-folder", exports) == 2
    assert sorted(p.name for p in exports.iterdir()) == [
        "00000001.json",
        "00000002.json",
    ]
    assert client.get.call_args_list[2].kwargs["params"]["pageToken"] == "next"
    assert client.get.call_args_list[3].args[0].endswith("/old")
    assert client.get.call_args_list[4].args[0].endswith("/new")
    db, output = tmp_path / "data.db", tmp_path / "activities.json"
    assert importer.import_workouts(exports, db, output) == (1, 0)
    activities = json.loads(output.read_text())
    assert len(activities) == 1
    assert activities[0]["distance"] == 5000


def test_empty_folder_and_access_error(drive, tmp_path):
    client = Mock()
    folder = response({"mimeType": "application/vnd.google-apps.folder"})
    client.get.side_effect = [folder, response({"files": []})]
    assert drive.download_exports(client, "test-folder", tmp_path) == 0
    client.get.side_effect = [response(error=HTTPError("403"))]
    with pytest.raises(HTTPError):
        drive.download_exports(client, "test-folder", tmp_path)
    assert list(tmp_path.iterdir()) == []
