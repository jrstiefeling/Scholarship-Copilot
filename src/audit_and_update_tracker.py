"""
Audits existing tracker rows based on Penelope's updated profile
(Caucasian, $250k+ income, no financial need, gay/LGBTQ+) and
appends new LGBTQ+-specific scholarships.
"""
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

# Scholarships to mark "Does Not Qualify" and why
# Key = substring to match in column A (name), Value = reason
DISQUALIFY = {
    "Jack Kent Cooke": "DISQUALIFIED — requires demonstrated financial need; $250k+ household income exceeds threshold",
    "Horatio Alger Junior": "DISQUALIFIED — financial need is a core requirement; $250k+ household income likely disqualifies",
    "California Latino Legislative Caucus": "DISQUALIFIED — targets Latino students; Penelope is Caucasian (verify if any open-eligibility tracks exist)",
    "Inland Empire Cash for College": "DISQUALIFIED — designed for students with financial need; $250k+ household income disqualifies",
    "College Pathways Scholarship": "DISQUALIFIED — requires healthcare career path; Penelope intends to study Advertising",
}

# Scholarships to flag for manual verification
FLAG = {
    "IECF": "FLAG — Some IECF awards are need-based; review individual awards in the common app and only apply to merit tracks",
    "Ontario-Montclair Promise": "FLAG — Confirm not need-based and open to non-OM District students",
    "Montclair to College": "FLAG — Program may have income/need requirements; confirm eligibility",
}

# New LGBTQ+ scholarships to add
# name, org, url, amount, deadline, requirements, essay, local, status, notes
LGBTQ_SCHOLARSHIPS = [
    [
        "Point Foundation Scholarship",
        "Point Foundation",
        "https://www.pointfoundation.org/point-apply/apply-for-scholarship/",
        "Up to $14,000/year (renewable)",
        "~January 2027 (apply senior year)",
        "LGBTQ+ student, demonstrated leadership in LGBTQ+ community, academic merit — NO financial need requirement",
        "Yes",
        "No",
        "Track — Apply Senior Year",
        "Most prestigious LGBTQ+ scholarship in the US. Merit + leadership based. No income requirement. Penelope's photography/advocacy work is a strong fit. Highly competitive — start prep now.",
    ],
    [
        "PFLAG National Scholarship",
        "PFLAG National",
        "https://pflag.org/scholarship",
        "$1,000–$5,000",
        "~March 2027 (apply senior year)",
        "LGBTQ+ student OR child of LGBTQ+ parent, merit-based, various tracks including some with no financial need requirement",
        "Yes",
        "No",
        "Track — Apply Senior Year",
        "Multiple award tracks. Look for the 'academic achievement' and 'creative arts' tracks which don't require financial need. Visual arts/advertising focus is a strong angle.",
    ],
    [
        "Human Rights Campaign Foundation Scholarship",
        "Human Rights Campaign Foundation",
        "https://www.hrc.org/hrc-story/scholarships",
        "Varies ($3,000–$10,000)",
        "~February 2027 (apply senior year)",
        "LGBTQ+ student, merit and community involvement — most tracks no income requirement",
        "Yes",
        "No",
        "Track — Apply Senior Year",
        "HRC is the largest LGBTQ+ civil rights org in the US. Community service and leadership focus aligns with Penelope's profile.",
    ],
    [
        "Lesley Gore Scholarship",
        "Ms. Foundation for Women",
        "https://forwomen.org",
        "$10,000",
        "~Fall 2026 (monitor for opening)",
        "LGBTQ+ young woman pursuing arts, media, or creative fields — strong fit for advertising",
        "Yes",
        "No",
        "HIGH PRIORITY — Monitor Fall 2026",
        "Named after singer-activist Lesley Gore. LGBTQ+ women in creative fields. Penelope's photography + advertising + LGBTQ+ identity = near-perfect match.",
    ],
    [
        "NGLCC Foundation Scholarship",
        "National LGBT Chamber of Commerce Foundation",
        "https://nglcc.org/programs/scholarships",
        "Varies",
        "~Spring 2027 (apply senior year)",
        "LGBTQ+ student pursuing business, marketing, communications, or entrepreneurship — advertising qualifies",
        "Yes",
        "No",
        "Track — Apply Senior Year",
        "Business/marketing focus directly aligns with Advertising major. LGBTQ+ identity + career direction = strong fit.",
    ],
    [
        "Equality California Scholarship",
        "Equality California Institute",
        "https://www.eqca.org",
        "Varies",
        "Monitor for 2026/2027 cycle",
        "California LGBTQ+ student, community advocacy",
        "Yes",
        "Yes",
        "Research — CA Specific",
        "California's leading LGBTQ+ advocacy org. State-specific = smaller applicant pool. Community service angle is strong.",
    ],
    [
        "Matthew Shepard Foundation Scholarship",
        "Matthew Shepard Foundation",
        "https://www.matthewshepard.org/scholarships",
        "Varies",
        "Monitor for 2026/2027 cycle",
        "LGBTQ+ student, commitment to erase hate and promote inclusion through storytelling or advocacy",
        "Yes",
        "No",
        "Research",
        "Storytelling/advocacy mission aligns directly with Photos with Purpose club. LGBTQ+ identity + visual storytelling = compelling application.",
    ],
    [
        "Live Out Loud Young Innovators Scholarship",
        "Live Out Loud",
        "https://liveoutloud.org/scholarships",
        "Varies",
        "Monitor for 2026/2027 cycle",
        "LGBTQ+ high school student showing creative innovation and leadership",
        "Yes",
        "No",
        "Research",
        "Focused on LGBTQ+ youth who are creative innovators. Yearbook Vice Editor + Photos with Purpose President = strong leadership narrative.",
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
    sid = ids["spreadsheet_id"]
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    # Read existing rows
    result = service.spreadsheets().values().get(
        spreadsheetId=sid, range="Scholarships!A:L"
    ).execute()
    rows = result.get("values", [])
    header = rows[0] if rows else []

    # Col indices (0-based): A=0 name, I=8 status, J=9 notes
    STATUS_COL = 8
    NOTES_COL = 9

    batch_updates = []
    disqualified_count = 0
    flagged_count = 0

    for i, row in enumerate(rows[1:], start=2):  # row 2 is first data row (1-indexed)
        name = row[0] if row else ""

        for key, reason in DISQUALIFY.items():
            if key.lower() in name.lower():
                # Update status cell
                batch_updates.append({
                    "range": f"Scholarships!I{i}",
                    "values": [["Does Not Qualify"]]
                })
                # Update notes cell
                existing_note = row[NOTES_COL] if len(row) > NOTES_COL else ""
                batch_updates.append({
                    "range": f"Scholarships!J{i}",
                    "values": [[reason]]
                })
                disqualified_count += 1
                print(f"  DISQUALIFIED: {name}")
                break

        for key, reason in FLAG.items():
            if key.lower() in name.lower():
                existing_status = row[STATUS_COL] if len(row) > STATUS_COL else ""
                if "Disqualified" not in existing_status:
                    batch_updates.append({
                        "range": f"Scholarships!J{i}",
                        "values": [[reason]]
                    })
                    flagged_count += 1
                    print(f"  FLAGGED: {name}")
                break

    # Apply all cell updates
    if batch_updates:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sid,
            body={"valueInputOption": "USER_ENTERED", "data": batch_updates}
        ).execute()

    print(f"\n  {disqualified_count} scholarships marked Does Not Qualify")
    print(f"  {flagged_count} scholarships flagged for manual verification")

    # Append new LGBTQ+ scholarships
    today = datetime.now().strftime("%Y-%m-%d")
    new_rows = [s + ["", today] for s in LGBTQ_SCHOLARSHIPS]
    service.spreadsheets().values().append(
        spreadsheetId=sid,
        range="Scholarships!A:L",
        valueInputOption="USER_ENTERED",
        body={"values": new_rows},
    ).execute()
    print(f"  {len(new_rows)} LGBTQ+ scholarships added")
    print(f"\nView: https://docs.google.com/spreadsheets/d/{sid}")


if __name__ == "__main__":
    main()
