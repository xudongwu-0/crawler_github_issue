# DECISIONS.md — Analysis Decision Log

## 2026-03-25: Initial Setup

### Environment Choice
- Using conda base environment (miniconda3) which has pandas 2.2.3, matplotlib 3.9.2, numpy 1.26.4, seaborn 0.13.2.
- Analysis conducted in Jupyter notebook `analysis.ipynb`.
- No LLM-assisted labeling in first pass; using keyword/rule-based classification + manual inspection.

### Data Source
- Corpus: 22,613 GitHub issues from `openclaw/openclaw`, exported via GitHub REST API.
- Fields: number, title, body, labels, state, created_at, updated_at, closed_at, user_login, html_url, statement_text.
- PRs were filtered out during export. No comments fetched.

---

(Decisions will be appended as analysis proceeds)
