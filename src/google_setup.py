"""
google_setup.py — creates the Google Sheets tracker and Drive folder
for the Scholarship Co-Pilot.  Run once to bootstrap.

Prerequisites:
  pip install google-auth google-auth-oauthlib google-api-python-client
  Place credentials.json (OAuth 2.0 Desktop client) in credentials/
"""

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
CREDS_PATH = ROOT / "credentials" / "credentials.json"
TOKEN_PATH = ROOT / "credentials" / "token.json"
IDS_PATH = ROOT / "config" / "google_ids.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

TRACKER_TITLE = "Daughter's Scholarship Tracker"
DRAFTS_FOLDER = "Scholarship Drafts"

SHEET_HEADERS = [
    "Scholarship Name",
    "Organization",
    "URL",
    "Amount",
    "Deadline",
    "Requirements",
    "Essay Required",
    "Local",
    "Status",
    "Notes",
    "Draft Doc Link",
    "Date Added",
]


def get_credentials() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                raise FileNotFoundError(
                    f"Missing {CREDS_PATH}\n"
                    "Download OAuth 2.0 credentials from Google Cloud Console:\n"
                    "  https://console.cloud.google.com/apis/credentials\n"
                    "Create a Desktop app client and save as credentials/credentials.json"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def create_tracker_spreadsheet(sheets_service, drive_service, folder_id: str) -> str:
    spreadsheet = {
        "properties": {"title": TRACKER_TITLE},
        "sheets": [
            {
                "properties": {"title": "Scholarships", "sheetId": 0},
                "data": [{
                    "startRow": 0,
                    "startColumn": 0,
                    "rowData": [{
                        "values": [{"userEnteredValue": {"stringValue": h}} for h in SHEET_HEADERS]
                    }]
                }],
            },
            {"properties": {"title": "Stats", "sheetId": 1}},
            {"properties": {"title": "Notes", "sheetId": 2}},
        ],
    }
    result = sheets_service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = result["spreadsheetId"]

    # Style the header row
    requests = [
        {
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.26, "green": 0.52, "blue": 0.96},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": "CENTER",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        },
        {
            "updateSheetProperties": {
                "properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {"sheetId": 0, "dimension": "COLUMNS", "startIndex": 0, "endIndex": len(SHEET_HEADERS)}
            }
        },
    ]
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()

    # Move into the drafts folder
    drive_service.files().update(
        fileId=spreadsheet_id,
        addParents=folder_id,
        removeParents="root",
        fields="id, parents",
    ).execute()

    print(f"  Created spreadsheet: {TRACKER_TITLE}")
    print(f"  https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    return spreadsheet_id


def create_drafts_folder(drive_service) -> str:
    metadata = {
        "name": DRAFTS_FOLDER,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = drive_service.files().create(body=metadata, fields="id").execute()
    folder_id = folder["id"]
    print(f"  Created Drive folder: {DRAFTS_FOLDER}")
    print(f"  https://drive.google.com/drive/folders/{folder_id}")
    return folder_id


def setup() -> dict:
    print("Authenticating with Google...")
    creds = get_credentials()
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    print(f"\nCreating Drive folder '{DRAFTS_FOLDER}'...")
    folder_id = create_drafts_folder(drive_service)

    print(f"\nCreating spreadsheet '{TRACKER_TITLE}'...")
    spreadsheet_id = create_tracker_spreadsheet(sheets_service, drive_service, folder_id)

    ids = {"spreadsheet_id": spreadsheet_id, "drafts_folder_id": folder_id}
    with open(IDS_PATH, "w") as f:
        json.dump(ids, f, indent=2)
    print(f"\nIDs saved to {IDS_PATH}")
    return ids


if __name__ == "__main__":
    print("Scholarship Co-Pilot — Google Setup\n")
    ids = setup()
    print("\nSetup complete!")
    print(f"  Spreadsheet ID : {ids['spreadsheet_id']}")
    print(f"  Folder ID      : {ids['drafts_folder_id']}")
