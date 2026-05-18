# Scholarship Copilot

Automation scripts for discovering scholarships, maintaining a tracker, and drafting application content.

## Setup

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create required local credential files (do not commit these):
   - `credentials/credentials.json` (Google OAuth Desktop client JSON)
   - `credentials/token.json` (generated after first auth flow)

4. Set required API key environment variables:

```bash
export BRAVE_API_KEY="REPLACE_ME"
export ANTHROPIC_API_KEY="REPLACE_ME"
```

5. Update placeholders:
   - `config/profile.json` with real student data
   - `config/google_ids.json` with your sheet/folder IDs (or run `src/google_setup.py` first)

## Notes on security

- The repository intentionally excludes `credentials/` via `.gitignore`.
- Keep all API keys in environment variables, not source code.
- Replace placeholder values in config files before production use.
