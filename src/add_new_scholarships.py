"""Adds newly discovered scholarships to the tracker."""
import json
from datetime import datetime
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
IDS_PATH = ROOT / "config" / "google_ids.json"
TOKEN_PATH = ROOT / "credentials" / "token.json"
CREDS_PATH = ROOT / "credentials" / "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

NEW_SCHOLARSHIPS = [
    ["Montclair to College (MTC)", "City of Montclair", "https://www.cityofmontclair.org/montclair-to-college/", "TBD", "TBD", "IE area student, dual enrollment program with college credits", "TBD", "Yes", "Research", "City-backed program — confirm eligibility for Rancho Cucamonga residents"],
    ["Horace Boatwright Memorial Scholarship", "San Bernardino Countywide Gangs & Drugs Task Force", "https://www.excelsior.com/graduation/scholarships", "TBD", "TBD", "Graduating senior who has overcome adversity, continuing education", "Yes", "Yes", "Research", "SB County-backed — adversity/resilience angle; confirm open to non-Excelsior students"],
]

def get_credentials():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds

def main():
    ids = json.loads(IDS_PATH.read_text())
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    today = datetime.now().strftime("%Y-%m-%d")
    rows = [s + ["", today] for s in NEW_SCHOLARSHIPS]
    service.spreadsheets().values().append(
        spreadsheetId=ids["spreadsheet_id"],
        range="Scholarships!A:L",
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()
    print(f"Added {len(rows)} new scholarships to the tracker.")

if __name__ == "__main__":
    main()
