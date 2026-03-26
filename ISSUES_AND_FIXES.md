# ISSUES_AND_FIXES.md — Execution Problems and Solutions

## 2026-03-25: Data Export Phase

### Problem 1: GitHub API 422 at page 100
- GitHub REST API returns HTTP 422 for `page >= 100` (hard limit: 10,000 items).
- Repository has 22,610+ issues, so simple pagination can't cover all.
- **Fix**: 3-pass strategy — asc + desc list-issues (covers ~9,900 each direction), then Search API with recursive date-range splitting for the gap in the middle.

### Problem 2: VS Code crash from large JSON progress file
- Initial implementation saved all fetched issues into a single `_fetch_progress.json` for resume support.
- File reached 44MB after 8,414 issues → VS Code file watcher choked.
- **Fix**: Switched to JSONL output (append-only) + tiny `_progress.txt` storing only page number.

### Problem 3: Rate limiting without token
- Without auth, GitHub API allows only 60 requests/hour.
- Hit 403 after ~51 pages.
- **Fix**: Used personal access token (stored in `.env`), raising limit to 5,000/hour.

---

(Issues will be appended as analysis proceeds)
