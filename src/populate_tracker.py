"""One-time script to populate the tracker with curated scholarships."""
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

SCHOLARSHIPS = [
    # name, org, url, amount, deadline, requirements, essay, local, status, notes
    ["Inland Ivy Foundation", "Inland Ivy Foundation", "https://www.sbsun.com/2026/03/06/inland-ivy-foundation-offers-scholarships-for-inland-empire-students/", "TBD", "TBD", "SB/Riverside County HS senior, 3.0+ GPA, 4-year college", "Yes", "Yes", "Research", "Check application directly — very local, strong fit"],
    ["IECF 2026 Scholarships", "Inland Empire Community Foundation", "https://www.iegives.org/iecfs-2026-scholarship-season-is-open/", "Varies", "April 15, 2026", "IE student, common application covers multiple awards", "Yes", "Yes", "Research", "One application = many scholarships. Check if still open for 2027 cycle"],
    ["Inland Empire Cash for College", "IE Cash for College", "https://iecashforcollege.org/scholarships/", "TBD", "TBD", "IE student, all backgrounds", "TBD", "Yes", "Research", "Open to all IE students including undocumented — broad eligibility"],
    ["Miracles & Dreams Foundation", "San Bernardino County Supervisor / Miracles & Dreams", "https://bosd3.sbcounty.gov/miracles-and-dreams-foundation-scholarship-opportunity-now-open/", "TBD", "TBD", "IE student admitted to or attending college", "TBD", "Yes", "Research", "County-backed — strong local connection"],
    ["Tencent America Scholarship", "Tencent America / Scholarship America", "https://scholarshipamerica.org/scholarship/tencentamerica/", "TBD", "TBD", "Preference for SB, LA, OC, Riverside, Ventura County students", "Yes", "Yes", "Research", "Tech company scholarship with local county preference"],
    ["College Pathways Scholarship", "Scholarships360", "https://scholarships360.org/scholarships/search/college-pathways-scholarship/", "TBD", "TBD", "SB/Riverside County HS junior or senior, healthcare career path", "Yes", "Yes", "Research", "Healthcare focus — may not fit advertising; confirm major requirements"],
    ["Cameron Impact Scholarship", "Cameron Impact", "https://www.fastweb.com/college-scholarships/articles/scholarships-for-high-school-juniors", "Full Tuition", "May 1, 2026", "HS Junior, 3.7+ GPA, leadership", "Yes", "No", "URGENT", "Full tuition — deadline May 1, 2026. Apply immediately!"],
    ["Bold.org $2,000 Monthly Scholarship", "Sallie / Bold.org", "https://bold.org/scholarships/by-year/high-school/juniors/", "$2,000", "April 30, 2026", "Current 11th grade student", "No", "No", "URGENT", "No essay required — apply in seconds. Deadline April 30!"],
    ["Bold.org High School Scholarships", "Bold.org", "https://bold.org/scholarships/by-year/high-school/", "$1,000+", "May 30, 2026", "High school student", "No", "No", "Apply", "Browse and apply to multiple awards on one platform"],
    ["Scholarships360 $10,000 No-Essay", "Scholarships360", "https://scholarships360.org/scholarships/california-scholarships/", "$10,000", "June 30, 2026", "California student", "No", "No", "Apply", "No essay — winner announced July 31, 2026"],
    ["California Scholarship Federation (CSF)", "CSF", "https://accessscholarships.com/scholarships-by-state/california-scholarships/", "Varies", "TBD", "California HS junior, CSF member (Penelope qualifies)", "TBD", "No", "Research", "Penelope is already a CSF member — strong eligibility"],
    ["Jack Kent Cooke Young Scholars", "Jack Kent Cooke Foundation", "https://www.jkcf.org/our-scholarships/", "Up to $40,000", "Rolling", "High financial need, exceptional academics", "Yes", "No", "Research", "Very competitive, need-based — confirm financial need eligibility"],
    ["Coca-Cola Scholars Program", "Coca-Cola Scholars Foundation", "https://www.coca-colascholarsfoundation.org/apply/", "$20,000", "October 2026", "Senior year only — apply fall 2026", "Yes", "No", "Future (Senior Year)", "Apply when Penelope starts senior year fall 2026"],
    ["US Senate Youth Program", "US Senate", "https://www.scholarshipsandgrants.us/other/community-service-scholarships/", "$10,000", "Aug–Nov 2026", "HS junior or senior in student government", "Yes", "No", "Research", "State-level selection — strong for leadership/civics angle"],
    ["Ontario-Montclair Promise Scholars", "Ontario-Montclair Schools Foundation", "https://www.dailybulletin.com/2026/01/15/ontario-montclair-schools-foundations-promise-scholars-gets-boost-from-recent-grant/", "TBD", "TBD", "IE area student", "TBD", "Yes", "Research", "Local foundation — confirm eligibility outside OM district"],
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
    rows = [s + ["", today] for s in SCHOLARSHIPS]  # add blank draft link + date added

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
