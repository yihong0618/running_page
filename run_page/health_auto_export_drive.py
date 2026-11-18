"""Download Health Auto Export JSON files from a private Google Drive folder."""

import argparse
import json
import os
import re
from pathlib import Path

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from requests import RequestException

DRIVE_FILES = "https://www.googleapis.com/drive/v3/files"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


def download_exports(client, folder_id, destination):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", folder_id):
        raise ValueError("Set HAE_DRIVE_FOLDER_ID to the Drive folder ID")
    # A listing can appear empty if the folder was never shared with this identity.
    folder = client.get(
        f"{DRIVE_FILES}/{folder_id}",
        params={"fields": "mimeType", "supportsAllDrives": "true"},
        timeout=30,
    )
    folder.raise_for_status()
    if folder.json().get("mimeType") != "application/vnd.google-apps.folder":
        raise ValueError("HAE_DRIVE_FOLDER_ID must identify a folder")

    params = {
        "q": f"'{folder_id}' in parents and trashed = false "
        "and mimeType != 'application/vnd.google-apps.folder' "
        "and mimeType != 'application/vnd.google-apps.shortcut'",
        "fields": "nextPageToken,incompleteSearch,files(id,name,modifiedTime)",
        "pageSize": 1000,
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
    }
    files = {}
    while True:
        response = client.get(DRIVE_FILES, params=params, timeout=30)
        response.raise_for_status()
        page = response.json()
        if page.get("incompleteSearch"):
            raise ValueError("Google Drive returned an incomplete folder listing")
        for file in page.get("files", []):
            if file["name"].lower().endswith(".json"):
                files[file["id"]] = file["modifiedTime"]
        token = page.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token

    for index, file_id in enumerate(
        sorted(files, key=lambda item: (files[item], item)), start=1
    ):
        response = client.get(
            f"{DRIVE_FILES}/{file_id}",
            params={"alt": "media", "supportsAllDrives": "true"},
            timeout=60,
        )
        response.raise_for_status()
        # Drive filenames can contain personal information or path separators.
        (destination / f"{index:08d}.json").write_bytes(response.content)
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="Empty temporary directory")
    args = parser.parse_args()
    try:
        if any(args.destination.iterdir()):
            raise ValueError("Destination must be empty")
        credentials = Credentials.from_service_account_info(
            json.loads(os.environ.get("HAE_DRIVE_SERVICE_ACCOUNT_JSON", "")),
            scopes=[DRIVE_SCOPE],
        )
        with AuthorizedSession(credentials) as client:
            count = download_exports(
                client, os.environ.get("HAE_DRIVE_FOLDER_ID", ""), args.destination
            )
    except RequestException as exc:
        status = exc.response.status_code if exc.response is not None else "unavailable"
        parser.exit(1, f"Google Drive request failed (HTTP status: {status}).\n")
    except (GoogleAuthError, ValueError, KeyError, TypeError, OSError):
        parser.exit(
            1,
            "Could not download HAE files. Check Drive credentials, folder ID, sharing, and destination.\n",
        )
    print(f"Downloaded {count} Health Auto Export JSON files.")


if __name__ == "__main__":
    main()
