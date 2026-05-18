"""
searcher.py — finds 2026/2027 scholarships using the Brave Search API,
prioritising local Rancho Cucamonga / San Bernardino County / Los Osos
awards and junior-year eligible scholarships.

Also scrapes CJUHSD and Los Osos HS pages directly for any listed scholarships.
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "config" / "profile.json"
RESULTS_PATH = ROOT / "config" / "scholarships_found.json"

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

SEARCH_QUERIES = [
    # CJUHSD / Los Osos direct
    'site:cjuhsd.net scholarship',
    'site:lososos.cjuhsd.net scholarship',
    '"Chaffey Joint Union" scholarship 2026',
    '"Chaffey Joint Union" "local scholarship packet" 2026',
    '"Los Osos High School" scholarship 2026 apply',
    '"CJUHSD" scholarship booster 2026',
    # Known hyperlocal — named scholarships
    '"Esperanza Scholarship Foundation" Chaffey 2027',
    '"Esperanza Scholarship" "Rancho Cucamonga" OR "Chaffey" apply',
    '"RCCAAF" scholarship 2026 OR 2027',
    '"Rancho Cucamonga Community" arts scholarship 2026 2027',
    # Hyperlocal general
    '"Rancho Cucamonga" scholarship 2026 high school',
    '"Rancho Cucamonga" scholarship 2027 junior senior',
    '"Los Osos High School" scholarship booster',
    '"San Bernardino County" scholarship 2026 high school student',
    '"Alta Loma" OR "Etiwanda" OR "Rancho Cucamonga" scholarship apply 2026',
    # Regional California
    '"Inland Empire" scholarship 2026 high school',
    'California high school junior scholarship 2026 apply',
    'California 11th grade scholarship 2026',
    # Industry-specific California
    '"California Latino Legislative Caucus" scholarship 2026 apply',
    '"CISOA" student scholarship 2026 2027',
    'California arts visual performing scholarship high school 2026',
    'California advertising communications scholarship high school 2026',
    # Junior-specific leadership
    '"Coolidge Scholarship" high school junior 2026',
    '"Horatio Alger" junior scholarship 2026 apply',
    'full ride scholarship high school junior 2026',
    'scholarship specifically high school juniors leadership 2026',
    # General junior-year
    'scholarship for high school juniors 2026 apply',
    'scholarship junior year 2026 no essay',
    'scholarship junior year 2026 community service',
]

# Pages to scrape directly for scholarship links
DIRECT_SCRAPE_URLS = [
    "https://www.cjuhsd.net",
    "https://www.cjuhsd.net/apps/pages/index.jsp?uREC_ID=1770930&type=d",
]

PRIORITY_KEYWORDS = [
    "rancho cucamonga", "los osos", "san bernardino", "inland empire",
    "alta loma", "ontario", "upland", "chino", "fontana", "pomona",
    "california resident", "ca resident", "cjuhsd", "chaffey",
    "esperanza", "rccaaf",
]

# Extra score bonus for the most hyperlocal keywords
HYPERLOCAL_KEYWORDS = [
    "los osos high school", "cjuhsd", "chaffey joint union",
    "rancho cucamonga", "alta loma", "esperanza scholarship",
    "rccaaf", "rancho cucamonga community",
]

# Junior-only awards that should be top priority for Penelope right now
JUNIOR_ONLY_KEYWORDS = [
    "coolidge scholarship", "horatio alger junior", "junior only",
    "only for juniors", "current junior", "11th grade only",
]

JUNIOR_KEYWORDS = [
    "junior", "11th grade", "sophomore junior", "10th 11th", "current junior",
    "class of 2026",
]

DISQUALIFY_KEYWORDS = [
    "graduate student", "college student", "undergraduate only",
    "seniors only", "12th grade only",
]

# URLs from these domains are never real scholarship pages
NOISE_DOMAINS = [
    "wikipedia.org", "maxpreps.com", "niche.com", "grokipedia.com",
    "privateschoolreview.com", "contactout.com", "ivyliving.com",
    "libguides", "patch.com/california/temecula", "tiktok.com",
    "cde.ca.gov/SchoolDirectory", "redlandsdailyfacts.com/2026/03/11",
]

# Results must contain at least one of these to be kept
RELEVANCE_REQUIRED = [
    "scholarship", "award", "grant", "apply", "application",
    "financial aid", "foundation", "bursary",
]


def load_profile() -> dict:
    with open(PROFILE_PATH) as f:
        return json.load(f)


def brave_search(query: str, count: int = 10) -> list[dict]:
    if not BRAVE_API_KEY:
        raise EnvironmentError(
            "Set BRAVE_API_KEY environment variable. "
            "Get a free key at https://brave.com/search/api/"
        )
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    params = {"q": query, "count": count, "freshness": "py"}  # past year
    resp = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("web", {}).get("results", [])


def score_result(result: dict) -> int:
    text = (result.get("title", "") + " " + result.get("description", "")).lower()
    url = result.get("url", "").lower()
    score = 0

    # Hyperlocal bonus (highest priority — these beat everything)
    for kw in HYPERLOCAL_KEYWORDS:
        if kw in text or kw in url:
            score += 25

    for kw in PRIORITY_KEYWORDS:
        if kw in text:
            score += 10
    for kw in JUNIOR_KEYWORDS:
        if kw in text:
            score += 5
    for kw in DISQUALIFY_KEYWORDS:
        if kw in text:
            score -= 20

    # Boost CJUHSD / Los Osos official domains
    if "cjuhsd.net" in url or "lososos" in url:
        score += 30

    # Boost junior-only awards — Penelope has exclusive access right now
    for kw in JUNIOR_ONLY_KEYWORDS:
        if kw in text:
            score += 20

    # Prefer results that look like scholarship application pages
    if any(x in url for x in ["scholarship", "award", "apply", "foundation"]):
        score += 3
    return score


def extract_deadline(text: str) -> str:
    patterns = [
        r"deadline[:\s]+([A-Za-z]+ \d{1,2},?\s*202[67])",
        r"(january|february|march|april|may|june|july|august|september|october|november|december)"
        r"\s+\d{1,2},?\s*202[67]",
        r"due[:\s]+([A-Za-z]+ \d{1,2})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return "Unknown"


class _LinkParser(HTMLParser):
    """Extracts all href links and visible text from an HTML page."""
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []  # (href, anchor_text)
        self._current_href = None
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_d = dict(attrs)
            self._current_href = attrs_d.get("href", "")
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "a" and self._current_href:
            text = "".join(self._buf).strip()
            self.links.append((self._current_href, text))
            self._current_href = None
            self._buf = []

    def handle_data(self, data):
        if self._current_href is not None:
            self._buf.append(data)


def scrape_page_for_scholarships(base_url: str) -> list[dict]:
    """Fetch a page and extract any links/text that mention scholarships."""
    results = []
    try:
        resp = requests.get(base_url, timeout=10,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; ScholarshipBot/1.0)"})
        resp.raise_for_status()
    except Exception as e:
        print(f"    Could not scrape {base_url}: {e}")
        return results

    parser = _LinkParser()
    parser.feed(resp.text)

    for href, anchor in parser.links:
        combined = (href + " " + anchor).lower()
        if not any(rk in combined for rk in RELEVANCE_REQUIRED):
            continue
        # Resolve relative URLs
        if href.startswith("http"):
            full_url = href
        elif href.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
        else:
            continue

        if any(nd in full_url.lower() for nd in NOISE_DOMAINS):
            continue

        results.append({
            "title": anchor or f"Scholarship link from {base_url}",
            "url": full_url,
            "description": f"Found on {base_url}",
            "deadline": extract_deadline(anchor),
            "score": score_result({"title": anchor, "description": "", "url": full_url}),
            "local": any(kw in combined for kw in PRIORITY_KEYWORDS),
            "junior_eligible": any(kw in combined for kw in JUNIOR_KEYWORDS),
            "found_at": datetime.now().isoformat(),
            "source": "direct_scrape",
        })

    return results


def search_scholarships() -> list[dict]:
    profile = load_profile()
    gpa = profile["academics"].get("gpa_unweighted")
    major = profile["academics"].get("intended_major", "")

    all_results: dict[str, dict] = {}  # url → result

    # Direct scrape of CJUHSD and Los Osos pages first
    print("  Scraping CJUHSD and Los Osos High School pages directly...")
    for url in DIRECT_SCRAPE_URLS:
        scraped = scrape_page_for_scholarships(url)
        for r in scraped:
            if r["url"] not in all_results:
                all_results[r["url"]] = r
    print(f"    Found {len(all_results)} links from direct scrape.")

    for query in SEARCH_QUERIES:
        print(f"  Searching: {query}")
        try:
            results = brave_search(query)
        except Exception as e:
            print(f"    Error: {e}")
            time.sleep(1)
            continue

        for r in results:
            url = r.get("url", "")
            if not url or url in all_results:
                continue
            # Filter out noise domains
            if any(nd in url.lower() for nd in NOISE_DOMAINS):
                continue
            text = r.get("title", "") + " " + r.get("description", "")
            # Must mention scholarship/award/apply to be relevant
            if not any(rk in text.lower() for rk in RELEVANCE_REQUIRED):
                continue
            all_results[url] = {
                "title": r.get("title", ""),
                "url": url,
                "description": r.get("description", ""),
                "deadline": extract_deadline(text),
                "score": score_result(r),
                "local": any(kw in text.lower() for kw in PRIORITY_KEYWORDS),
                "junior_eligible": any(kw in text.lower() for kw in JUNIOR_KEYWORDS),
                "found_at": datetime.now().isoformat(),
            }
        time.sleep(0.5)  # be kind to the API

    scholarships = sorted(all_results.values(), key=lambda x: x["score"], reverse=True)

    print(f"\nFound {len(scholarships)} unique scholarships.")
    _save_results(scholarships)
    return scholarships


def _save_results(scholarships: list[dict]) -> None:
    with open(RESULTS_PATH, "w") as f:
        json.dump(scholarships, f, indent=2)
    print(f"Results saved to {RESULTS_PATH}")


def print_summary(scholarships: list[dict], top_n: int = 20) -> None:
    print(f"\n{'='*60}")
    print(f"TOP {top_n} SCHOLARSHIPS")
    print(f"{'='*60}")
    for i, s in enumerate(scholarships[:top_n], 1):
        local_tag = " [LOCAL]" if s["local"] else ""
        junior_tag = " [JUNIOR OK]" if s["junior_eligible"] else ""
        print(f"\n{i}. {s['title']}{local_tag}{junior_tag}")
        print(f"   URL:      {s['url']}")
        print(f"   Deadline: {s['deadline']}")
        print(f"   Score:    {s['score']}")
        if s["description"]:
            print(f"   Summary:  {s['description'][:120]}...")


if __name__ == "__main__":
    print("Scholarship Co-Pilot — Searcher")
    print("Searching for 2026/2027 scholarships...\n")
    results = search_scholarships()
    print_summary(results)
