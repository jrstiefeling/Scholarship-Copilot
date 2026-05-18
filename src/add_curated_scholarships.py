"""Adds manually curated high-value scholarships to the tracker."""
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

# name, org, url, amount, deadline, requirements, essay, local, status, notes
SCHOLARSHIPS = [
    # ── Hyper-Local Powerhouses ──────────────────────────────────────────────
    [
        "Esperanza Scholarship Foundation",
        "Esperanza Scholarship Foundation",
        "https://www.esperanzascholarship.org",
        "Varies (50–70 awarded annually)",
        "January 2027 (Senior year)",
        "Chaffey District student (Los Osos qualifies), community service",
        "Yes",
        "Yes",
        "Track — Apply Senior Year",
        "HIGHEST PRIORITY LOCAL. 50–70 awards/yr for Chaffey District students. 2026 window closed Mar 27 — set reminder for January 2027. Very high win probability.",
    ],
    [
        "RCCAAF Visual & Performing Arts Scholarship",
        "Rancho Cucamonga Community & Arts Foundation",
        "https://www.rccaaf.org",
        "Varies",
        "Spring 2027 (monitor for opening)",
        "Rancho Cucamonga student, arts/music/visual arts interest — Photos with Purpose qualifies",
        "Yes",
        "Yes",
        "Track — Apply Spring 2027",
        "Two Los Osos students won in 2026. Photos with Purpose club = strong fit for visual arts category. Monitor rccaaf.org for 2027 application opening.",
    ],
    [
        "CJUHSD Local Scholarship Packet",
        "Chaffey Joint Union High School District",
        "https://www.cjuhsd.net",
        "Varies (multiple scholarships in one packet)",
        "Early Spring 2027 (typically Feb–Mar)",
        "CJUHSD student (Penelope qualifies), various requirements per award",
        "Varies",
        "Yes",
        "Track — Request Spring 2027",
        "District releases an annual packet of local scholarships — ask counselor for 2027 packet in January. Most competitive pool is local only = high win odds.",
    ],
    # ── Industry-Specific California ─────────────────────────────────────────
    [
        "California Latino Legislative Caucus Foundation Scholarship",
        "California Latino Legislative Caucus Foundation",
        "https://www.cllcf.org",
        "Varies",
        "June 1, 2026",
        "Applications open April 1 — community service focus; broad eligibility",
        "Yes",
        "No",
        "URGENT — Apply Now",
        "Open NOW (April 1 – June 1, 2026). Community service focus matches Penelope's Alara Senior Living work. Confirm eligibility — some awards are open regardless of ethnicity.",
    ],
    [
        "CISOA Student Scholarship",
        "California IT in Education (CISOA)",
        "https://www.cisoa.org/scholarships",
        "$1,500",
        "March 2027 (closed March 2026)",
        "CA student interested in IT, Computer Science, or Educational Technology",
        "Yes",
        "No",
        "Track — Apply Early 2027",
        "Just closed for 2026 — prep early for 2027. Advertising/digital media angle may qualify under ed-tech track.",
    ],
    # ── Junior-Specific Leadership ────────────────────────────────────────────
    [
        "Coolidge Scholarship",
        "Calvin Coolidge Presidential Foundation",
        "https://www.coolidgescholarship.org",
        "Full ride (tuition, room, board)",
        "~November 2026",
        "JUNIORS ONLY — current 11th graders, academic excellence, leadership, public service",
        "Yes",
        "No",
        "HIGH PRIORITY — Apply Fall 2026",
        "FULL RIDE — one of the few full scholarships open exclusively to juniors. Penelope's GPA 4.3 + leadership roles make her competitive. Apply November 2026.",
    ],
    [
        "Horatio Alger Junior Scholarship",
        "Horatio Alger Association",
        "https://scholars.horatioalger.org",
        "$10,000 (+ mentorship network)",
        "~October 2026",
        "JUNIORS ONLY — must have overcome adversity, financial need, 2.0+ GPA, community involvement",
        "Yes",
        "No",
        "Research — Apply Fall 2026",
        "Specifically for juniors who have overcome hardship. Strong community service fit with Alara Senior Living. Financial need component — confirm eligibility.",
    ],
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
    rows = [s + ["", today] for s in SCHOLARSHIPS]
    service.spreadsheets().values().append(
        spreadsheetId=ids["spreadsheet_id"],
        range="Scholarships!A:L",
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()
    print(f"Added {len(rows)} scholarships to the tracker.")
    print(f"View: https://docs.google.com/spreadsheets/d/{ids['spreadsheet_id']}")

if __name__ == "__main__":
    main()
