"""
drafter.py — generates a tailored scholarship essay draft in a new Google Doc.

Usage:
  python src/drafter.py --name "Scholarship Name" --prompt "Essay prompt here" [--word-limit 650]

Prerequisites:
  pip install anthropic google-auth google-auth-oauthlib google-api-python-client
  Run src/google_setup.py first.
  Set ANTHROPIC_API_KEY environment variable.
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

import anthropic
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "config" / "profile.json"
IDS_PATH = ROOT / "config" / "google_ids.json"
TOKEN_PATH = ROOT / "credentials" / "token.json"
CREDS_PATH = ROOT / "credentials" / "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def get_credentials() -> Credentials:
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


def build_profile_summary(profile: dict) -> str:
    s = profile["student"]
    a = profile["academics"]
    p = profile["personal"]
    et = profile["essay_themes"]

    ecs = "\n".join(
        f"  - {e['activity']} ({e['role']}, {e.get('years_involved','?')} yrs, "
        f"~{e.get('hours_per_week','?')} hrs/wk): {e.get('description','')}"
        for e in profile.get("extracurriculars", []) if e.get("activity")
    ) or "  (not filled in yet)"

    awards = "\n".join(
        f"  - {aw['title']} ({aw.get('year','')}, {aw.get('issuing_organization','')})"
        for aw in profile.get("awards_and_honors", []) if aw.get("title")
    ) or "  (not filled in yet)"

    service = "\n".join(
        f"  - {cs['organization']}: {cs.get('total_hours','?')} hrs — {cs.get('description','')}"
        for cs in profile.get("community_service", []) if cs.get("organization")
    ) or "  (not filled in yet)"

    return f"""
STUDENT PROFILE
Name: {s.get('first_name','')} {s.get('last_name','')}
School: {profile['school']['name']}, {profile['school']['city']}, CA
Grade: {s.get('grade','')} | Graduation: {s.get('graduation_year','')}
GPA (unweighted): {a.get('gpa_unweighted','?')} | (weighted): {a.get('gpa_weighted','?')}
Intended Major: {a.get('intended_major','?')}
Languages: {', '.join(p.get('languages_spoken', [])) or 'English'}
First-gen college student: {p.get('first_generation_college_student','?')}
California resident: {p.get('california_resident', True)} | Rancho Cucamonga resident: {p.get('rancho_cucamonga_resident', True)}

EXTRACURRICULARS:
{ecs}

COMMUNITY SERVICE:
{service}

AWARDS & HONORS:
{awards}

CORE VALUES: {', '.join(et.get('core_values', [])) or '?'}
FUTURE GOALS: {et.get('future_goals','?')}
UNIQUE STORY: {et.get('unique_story','?')}
CHALLENGES OVERCOME: {et.get('challenges_overcome','?')}
DEFINING EXPERIENCES: {'; '.join(et.get('defining_experiences', [])) or '?'}
""".strip()


def generate_essay(scholarship_name: str, prompt: str, word_limit: int, profile: dict) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise EnvironmentError("Set ANTHROPIC_API_KEY environment variable.")

    client = anthropic.Anthropic(api_key=api_key)
    profile_summary = build_profile_summary(profile)

    system_prompt = """You are an expert college and scholarship essay coach specialising in
authentic, compelling personal statements for high school students. You write in the
student's own voice — warm, specific, never generic. You avoid clichés and always ground
each essay in concrete details, real moments, and genuine emotion. The essay must read as
if the student wrote it, not an AI."""

    user_prompt = f"""Write a scholarship essay for the student described below.

SCHOLARSHIP: {scholarship_name}
ESSAY PROMPT: {prompt}
WORD LIMIT: approximately {word_limit} words

{profile_summary}

Guidelines:
- Open with a vivid, specific scene or moment — not a quote or definition.
- Connect personal experiences directly to the scholarship's values/mission.
- Show growth, impact, and future direction.
- Use the student's real details from the profile above.
- Stay within {word_limit} words (aim for {int(word_limit * 0.9)}–{word_limit}).
- Do NOT include a title, header, or "Dear Committee" salutation.
- End with forward-looking purpose, not a summary.

Write the essay now:"""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text.strip()


def count_words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def create_google_doc(docs_service, drive_service, folder_id: str,
                      scholarship_name: str, prompt: str,
                      essay: str, profile: dict) -> str:
    s = profile["student"]
    student_name = f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or "Student"
    date_str = datetime.now().strftime("%Y-%m-%d")
    doc_title = f"{scholarship_name} — Essay Draft ({date_str})"

    doc = docs_service.documents().create(body={"title": doc_title}).execute()
    doc_id = doc["documentId"]

    # Move into Scholarship Drafts folder
    drive_service.files().update(
        fileId=doc_id,
        addParents=folder_id,
        removeParents="root",
        fields="id, parents",
    ).execute()

    word_count = count_words(essay)

    # Build document content
    requests = [
        # Title
        {"insertText": {"location": {"index": 1}, "text": f"{doc_title}\n\n"}},
        # Metadata section
        {"insertText": {"location": {"index": len(doc_title) + 3},
                        "text": f"Student: {student_name}\nScholarship: {scholarship_name}\n"
                                f"Prompt: {prompt}\nWord count: {word_count}\n"
                                f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
                                f"{'─' * 60}\n\nESSAY DRAFT\n\n{'─' * 60}\n\n"}},
    ]
    docs_service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()

    # Get current end index and insert essay
    doc_content = docs_service.documents().get(documentId=doc_id).execute()
    end_index = doc_content["body"]["content"][-1]["endIndex"] - 1
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{"insertText": {"location": {"index": end_index}, "text": essay}}]},
    ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"  Created doc: {doc_title}")
    print(f"  {doc_url}")
    return doc_url


def add_to_tracker(sheets_service, spreadsheet_id: str,
                   scholarship_name: str, doc_url: str) -> None:
    row = [
        scholarship_name, "", "", "", "", "", "Yes", "", "Draft Written", "",
        doc_url, datetime.now().strftime("%Y-%m-%d"),
    ]
    sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Scholarships!A:L",
        valueInputOption="USER_ENTERED",
        body={"values": [row]},
    ).execute()
    print(f"  Added row to tracker spreadsheet.")


def draft(scholarship_name: str, prompt: str, word_limit: int = 650) -> str:
    profile = load_json(PROFILE_PATH)
    ids = load_json(IDS_PATH)

    print(f"\nGenerating essay for: {scholarship_name}")
    print(f"Prompt: {prompt[:80]}...")
    essay = generate_essay(scholarship_name, prompt, word_limit, profile)
    print(f"Essay generated ({count_words(essay)} words).")

    print("\nConnecting to Google...")
    creds = get_credentials()
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    print("Creating Google Doc...")
    doc_url = create_google_doc(
        docs_service, drive_service,
        ids["drafts_folder_id"],
        scholarship_name, prompt, essay, profile,
    )

    print("Updating tracker...")
    add_to_tracker(sheets_service, ids["spreadsheet_id"], scholarship_name, doc_url)

    print(f"\nDone! Open your draft here:\n  {doc_url}")
    return doc_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a scholarship essay draft.")
    parser.add_argument("--name", required=True, help="Scholarship name")
    parser.add_argument("--prompt", required=True, help="Essay prompt")
    parser.add_argument("--word-limit", type=int, default=650, help="Word limit (default 650)")
    args = parser.parse_args()

    draft(args.name, args.prompt, args.word_limit)
