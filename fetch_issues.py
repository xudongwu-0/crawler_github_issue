#!/usr/bin/env python3
"""
Minimal GitHub issue exporter for openclaw/openclaw.
Fetches ALL issues (open + closed), filters out PRs, saves to JSONL + CSV.

Strategy to bypass GitHub's 9,900-item pagination limit:
  Pass 1: list-issues, sort=created, direction=asc  -> oldest  ~9,900
  Pass 2: list-issues, sort=created, direction=desc -> newest  ~9,900
  Pass 3: Search API with created date range for any gap in the middle

All results are deduplicated by issue number.
"""

import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# ─── Configuration ────────────────────────────────────────────────────────────
REPO = "openclaw/openclaw"
ISSUES_API = f"https://api.github.com/repos/{REPO}/issues"
SEARCH_API = "https://api.github.com/search/issues"
PER_PAGE = 100
MAX_PAGE = 99        # GitHub hard limit for page-based pagination
MAX_RETRIES = 6
RETRY_BACKOFF = 2

# Output files
JSONL_FILE = "openclaw_issues.jsonl"
CSV_FILE = "openclaw_issues.csv"
ENV_FILE = ".env"

FIELDS = [
    "number", "title", "body", "labels", "state",
    "created_at", "updated_at", "closed_at",
    "user_login", "html_url", "statement_text",
]


# ─── Token loading ───────────────────────────────────────────────────────────
def load_token():
    """Load GitHub token from environment variable or .env file."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ENV_FILE)
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if token:
                        return token
    return None


# ─── HTTP helpers ────────────────────────────────────────────────────────────
def make_request(url, token=None):
    """GET request with retry + rate-limit awareness. Returns (json_data, next_url)."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "openclaw-issue-exporter",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Parse Link header for next page
                link_header = resp.getheader("Link") or ""
                next_url = None
                for part in link_header.split(","):
                    if 'rel="next"' in part:
                        next_url = part.split("<")[1].split(">")[0]
                # Proactive rate-limit check
                remaining = resp.getheader("X-RateLimit-Remaining")
                if remaining and int(remaining) <= 2:
                    reset_ts = int(resp.getheader("X-RateLimit-Reset") or 0)
                    wait_sec = max(reset_ts - int(time.time()), 1) + 5
                    print(f"  Rate limit low ({remaining}), sleeping {wait_sec}s ...")
                    time.sleep(wait_sec)
                return data, next_url
        except urllib.error.HTTPError as e:
            if e.code == 403:
                reset_ts = e.headers.get("X-RateLimit-Reset")
                if reset_ts:
                    wait_sec = max(int(reset_ts) - int(time.time()), 1) + 5
                    print(f"  Rate limited (403). Waiting {wait_sec}s ...")
                    time.sleep(wait_sec)
                    continue
            if e.code == 422:
                raise  # Don't retry unprocessable entity
            wait = RETRY_BACKOFF * (2 ** (attempt - 1))
            print(f"  [retry {attempt}/{MAX_RETRIES}] HTTP {e.code} — waiting {wait}s")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(wait)
        except (urllib.error.URLError, OSError) as e:
            wait = RETRY_BACKOFF * (2 ** (attempt - 1))
            print(f"  [retry {attempt}/{MAX_RETRIES}] {e} — waiting {wait}s")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(wait)


# ─── Field extraction ────────────────────────────────────────────────────────
def extract_fields(item):
    """Extract fields from a raw API item. Works for both list and search APIs."""
    body = item.get("body") or ""
    title = item.get("title") or ""
    labels = [l["name"] for l in (item.get("labels") or [])]
    user = item.get("user") or {}
    return {
        "number": item["number"],
        "title": title,
        "body": body,
        "labels": labels,
        "state": item["state"],
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "closed_at": item.get("closed_at"),
        "user_login": user.get("login", ""),
        "html_url": item.get("html_url", ""),
        "statement_text": f"{title}\n\n{body}",
    }


# ─── Pass 1 & 2: List-issues endpoint ───────────────────────────────────────
def fetch_issues_list_api(token, direction="desc"):
    """Fetch up to ~9,900 issues using the list-issues endpoint.
    direction: 'asc' for oldest-first, 'desc' for newest-first.
    Returns dict of {number: issue_dict}.
    """
    print(f"\n{'='*60}")
    print(f"List API pass: direction={direction} (up to {MAX_PAGE * PER_PAGE} items)")
    print(f"{'='*60}")

    results = {}
    url = f"{ISSUES_API}?state=all&sort=created&direction={direction}&per_page={PER_PAGE}&page=1"
    page = 1

    while url and page <= MAX_PAGE:
        print(f"  Page {page}/{MAX_PAGE} ...", end=" ", flush=True)
        data, next_url = make_request(url, token)
        count = 0
        for item in data:
            if "pull_request" in item:
                continue
            issue = extract_fields(item)
            results[issue["number"]] = issue
            count += 1
        print(f"+{count} issues (unique: {len(results)})")
        if not data:
            break
        url = next_url
        page += 1

    return results


# ─── Pass 3: Search API for middle gap ───────────────────────────────────────
def fetch_issues_search_api(token, date_start, date_end, known_numbers):
    """Fetch issues in a created date range using Search API.
    Recursively splits ranges if >1000 results.
    Returns dict of {number: issue_dict} for NEW issues only.
    """
    results = {}
    _search_recursive(token, date_start, date_end, known_numbers, results, depth=0)
    return results


def _search_recursive(token, d_start, d_end, known_numbers, results, depth):
    """Recursive date-range search. Splits if results > 1000."""
    indent = "    " * (depth + 1)
    query = f"repo:{REPO} type:issue created:{d_start}..{d_end}"
    url = f"{SEARCH_API}?q={urllib.request.quote(query)}&per_page={PER_PAGE}&page=1"

    print(f"{indent}Search created:{d_start}..{d_end}", end=" ", flush=True)
    data, _ = make_request(url, token)
    total = data.get("total_count", 0)
    print(f"=> {total} results")

    if total == 0:
        return

    if total > 1000:
        # Split date range in half
        dt_start = datetime.strptime(d_start, "%Y-%m-%d")
        dt_end = datetime.strptime(d_end, "%Y-%m-%d")
        if dt_start >= dt_end:
            print(f"{indent}  WARNING: single day {d_start} has {total} issues, fetching first 1000")
        else:
            mid = dt_start + (dt_end - dt_start) / 2
            mid_str = mid.strftime("%Y-%m-%d")
            next_day = (mid + timedelta(days=1)).strftime("%Y-%m-%d")
            _search_recursive(token, d_start, mid_str, known_numbers, results, depth + 1)
            _search_recursive(token, next_day, d_end, known_numbers, results, depth + 1)
            return

    # Fetch all pages for this range (max 10 pages = 1000 items)
    page = 1
    page_url = url
    while page_url and page <= 10:
        if page > 1:
            data, _ = make_request(page_url, token)
        for item in data.get("items", []):
            num = item["number"]
            if num not in known_numbers and num not in results:
                results[num] = extract_fields(item)
        fetched_so_far = page * PER_PAGE
        if fetched_so_far < total and page < 10:
            page += 1
            page_url = f"{SEARCH_API}?q={urllib.request.quote(query)}&per_page={PER_PAGE}&page={page}"
        else:
            break

    print(f"{indent}  => {len(results)} new issues from gap search so far")


# ─── Save functions ──────────────────────────────────────────────────────────
def save_jsonl(issues, path):
    with open(path, "w", encoding="utf-8") as f:
        for issue in issues:
            f.write(json.dumps(issue, ensure_ascii=False) + "\n")
    print(f"Saved {len(issues)} issues to {path}")


def save_csv(issues, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for issue in issues:
            row = dict(issue)
            row["labels"] = ";".join(row["labels"])
            writer.writerow(row)
    print(f"Saved {len(issues)} issues to {path}")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    token = load_token()
    if not token:
        print("ERROR: GITHUB_TOKEN required. Set in .env file or environment variable.")
        sys.exit(1)
    print("Token loaded.\n")

    out_dir = os.path.dirname(os.path.abspath(__file__))

    # Pass 1: oldest issues first (ascending)
    asc_issues = fetch_issues_list_api(token, direction="asc")

    # Pass 2: newest issues first (descending)
    desc_issues = fetch_issues_list_api(token, direction="desc")

    # Merge passes
    all_issues = {}
    all_issues.update(asc_issues)
    all_issues.update(desc_issues)
    print(f"\nAfter Pass 1+2: {len(all_issues)} unique issues")

    # Pass 3: fill any date gap in the middle using Search API
    if asc_issues and desc_issues:
        asc_dates = sorted(v["created_at"] for v in asc_issues.values())
        desc_dates = sorted(v["created_at"] for v in desc_issues.values())
        asc_latest = asc_dates[-1][:10]   # latest date from ascending pass
        desc_oldest = desc_dates[0][:10]  # oldest date from descending pass

        print(f"Ascending pass latest:  {asc_latest}")
        print(f"Descending pass oldest: {desc_oldest}")

        if asc_latest >= desc_oldest:
            print("Passes overlap — no gap. All issues fetched!")
        else:
            print(f"\nGap: {asc_latest} to {desc_oldest}. Filling with Search API...")
            gap_issues = fetch_issues_search_api(
                token, asc_latest, desc_oldest, set(all_issues.keys())
            )
            all_issues.update(gap_issues)
            print(f"After gap fill: {len(all_issues)} unique issues")

    # Sort by issue number
    sorted_issues = [all_issues[n] for n in sorted(all_issues.keys())]
    print(f"\nTotal unique issues: {len(sorted_issues)}")

    # Save outputs
    save_jsonl(sorted_issues, os.path.join(out_dir, JSONL_FILE))
    save_csv(sorted_issues, os.path.join(out_dir, CSV_FILE))
    print("\nDone!")


if __name__ == "__main__":
    main()
