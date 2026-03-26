# OpenClaw Issue Corpus Analysis — Full Report

> **Corpus**: 22,613 GitHub issues from `openclaw/openclaw`  
> **Date range**: 2025-11-27 → 2026-03-25 (~118 days)  
> **Analysis date**: 2026-03-25  

---

## 1. Corpus Overview

| Metric | Value |
|---|---|
| Total issues | 22,613 |
| Closed | 13,362 (59.1%) |
| Open | 9,251 (40.9%) |
| Unique contributors | 14,058 |
| Unique labels | 47 |
| Issues with labels | 56.3% |
| Mean body length | 2,184 chars |
| Median lifetime (closed) | 2.8 days |

### Temporal Trend

The project experienced a dramatic explosion in issue volume starting late January 2026 — from ~20 issues/week to ~3,000 issues/week — coinciding with what appears to be a major public launch or viral adoption event.

### Top TF-IDF Keywords

**Unigrams**: agent, gateway, session, model, telegram, error, tool, context, memory, browser  
**Bigrams**: root cause, proposed solution, openclaw gateway, feature request

---

## 2. Theme Taxonomy (12 themes, scored keyword + label classifier)

The classifier assigns each issue to zero or more themes via regex keyword matching and label overlap, with a minimum-hits threshold to avoid over-classification. Each issue gets a **primary theme** (highest score).

| Theme | Multi-label | % | Primary | % |
|---|---|---|---|---|
| Gateway / Connectivity | 10,534 | 46.6% | 4,761 | 21.1% |
| Channel Integration | 8,222 | 36.4% | 2,658 | 11.8% |
| Model / LLM / Provider | 8,002 | 35.4% | 3,403 | 15.0% |
| Session Management | 7,562 | 33.4% | 660 | 2.9% |
| Installation / Deploy | 6,558 | 29.0% | 3,463 | 15.3% |
| Tool Use / Plugins | 5,264 | 23.3% | 757 | 3.3% |
| Crash / Error | 4,100 | 18.1% | 800 | 3.5% |
| Security / Auth | 4,058 | 17.9% | 716 | 3.2% |
| Memory / Context | 3,631 | 16.1% | 1,033 | 4.6% |
| Agent Orchestration | 3,125 | 13.8% | 1,027 | 4.5% |
| Scheduling / Automation | 2,580 | 11.4% | 1,318 | 5.8% |
| UI / UX | 2,384 | 10.5% | 295 | 1.3% |
| Uncategorized | — | — | 1,722 | 7.6% |

**Key finding**: Gateway/Connectivity is the dominant theme (21% primary), followed by Installation/Deploy (15%) and Model/LLM/Provider (15%). This reflects a project whose community struggles most with infrastructure reliability and onboarding.

### Top Co-occurrence Pairs (Jaccard similarity)

1. Gateway × Channel Integration (J=0.31) — messaging infra tightly coupled
2. Model × Session (J=0.29) — LLM interactions drive session concerns
3. Install × Crash (J=0.29) — setup failures cascade into crashes
4. Gateway × Session (J=0.29) — connection issues affect sessions
5. Gateway × Install (J=0.29) — deployment and connectivity intertwined

---

## 3. Stability / Plasticity / Generalization (S/P/G) Analysis

Using the continual-learning S/P/G framework mapped to software systems:

| Dimension | Multi-label | % | Primary | % | Median lifetime |
|---|---|---|---|---|---|
| **Stability** | 13,257 | 58.6% | 10,662 | 47.1% | 2.8d |
| **Plasticity** | 13,160 | 58.2% | 7,960 | 35.2% | 3.3d |
| **Generalization** | 4,794 | 21.2% | 614 | 2.7% | 4.4d |
| Unclassified | — | — | 3,377 | 14.9% | 1.7d |

### Key Findings

1. **Stability dominates** (47% primary) — nearly half of all issues relate to keeping things working. This is typical for a rapidly-growing project under heavy load.

2. **Plasticity is substantial** (35%) — strong demand for new features, extensibility, and provider support. The project is in an "additive" phase.

3. **Generalization is underrepresented** (2.7%) — cross-platform, edge-case, and scalability concerns are rarely the *primary* focus, suggesting the community is still focused on "make it work at all" before "make it work everywhere."

4. **Stability issues close faster** (2.8d) than Plasticity (3.3d) — bugs get patched quicker than features get built.

5. **Generalization issues are rare but slow** (4.4d median) — they're harder to resolve.

### Temporal Evolution

- Stability rose from ~40% to ~68% of weekly issues over the project's lifetime — the scaling pain is real and worsening.
- Plasticity has been steady at ~55-60%, showing consistent feature demand.
- Generalization grew from ~0% to ~23%, beginning to emerge as the project matures.

---

## 4. Design Tensions

The S-P gap reveals which subsystems face the most acute tension between "keep it stable" and "make it flexible":

| Theme | Stability % | Plasticity % | Gap | Tension |
|---|---|---|---|---|
| Crash / Error | 98.3% | 48.4% | **+49.9%** | S >> P |
| Installation / Deploy | 76.3% | 53.9% | **+22.4%** | S >> P |
| Gateway / Connectivity | 69.3% | 57.6% | **+11.7%** | S >> P |
| Tool Use / Plugins | 65.5% | 81.2% | **-15.7%** | P >> S |
| Memory / Context | 60.0% | 71.1% | **-11.2%** | P >> S |
| Agent Orchestration | 63.2% | 67.1% | -3.9 | balanced |
| Session Management | 63.1% | 62.1% | +1.0 | balanced |
| Security / Auth | 66.2% | 66.1% | +0.1 | balanced |

**Interpretation**:
- **Infrastructure subsystems** (Gateway, Install, Crash) are dominated by stability pressure — users need them to *not break*.
- **Extension subsystems** (Tool Use, Memory) are dominated by plasticity pressure — users want them to *do more*.
- This mirrors the classic **infrastructure vs. application layer** tension in platform engineering.

---

## 5. Pain-Point Index

Composite metric: `volume × open_fraction × (1 + log(still_open))`. Higher = more unresolved community pain.

| Rank | Theme | Pain Index | Volume | Open % | Still Open |
|---|---|---|---|---|---|
| 1 | **Gateway / Connectivity** | 41,366 | 10,534 | 41.8% | 4,405 |
| 2 | Model / LLM / Provider | 31,789 | 8,002 | 43.4% | 3,473 |
| 3 | Channel Integration | 30,279 | 8,222 | 40.4% | 3,324 |
| 4 | Session Management | 29,734 | 7,562 | 43.2% | 3,270 |
| 5 | Installation / Deploy | 26,560 | 6,558 | 45.0% | 2,954 |
| 6 | Crash / Error | 20,153 | 4,100 | **56.2%** | 2,305 |

**Crash / Error** has the lowest close rate (43.8%) — these are the hardest to fix.  
**Gateway / Connectivity** has the highest absolute pain — most volume + many still open.

---

## 6. Research Narrative

### The Stability-Plasticity Dilemma in Agent Platforms

OpenClaw's issue corpus reveals a project caught in a classic **stability-plasticity dilemma**:

1. **Rapid growth** (20→3000 issues/week) strains infrastructure faster than it can be hardened.
2. **Gateway/Connectivity** is the #1 pain point — the central nervous system of the platform is its weakest link.
3. **Stability is rising over time** (40%→68%) while Plasticity holds steady (~58%) — the project is accumulating stability debt faster than it can service it.
4. **Extension systems** (tools, memory, agents) want more features, but infrastructure can't keep up — the platform layer is a bottleneck for the application layer.
5. **Generalization is nascent** (2.7% primary) — the project hasn't yet grappled with cross-platform, edge-case, or scaling challenges in a systematic way.

### Recurring Failure Modes
- Gateway crash loops under multi-channel load
- Session state corruption from race conditions  
- Installation failures cascading into runtime crashes (J=0.29 co-occurrence)
- Tool/plugin calls silently dropped in certain channels

### Design Implications
- **Invest in gateway resilience** — it's the #1 pain point and the foundation for all messaging channels
- **Decouple channel adapters** — the tight coupling (J=0.31 with Gateway) means one channel's issues affect all
- **Formalize the tool/plugin API** — high plasticity demand suggests the current extension model is ad-hoc
- **Build observability** — many crash issues mention difficulty diagnosing root causes

---

## 7. Methodology Notes

- **Theme classification**: 12 themes defined via keyword regex + label matching, with minimum-hit thresholds to avoid over-classification. Mean 2.92 themes/issue.
- **S/P/G classification**: Keyword-rule-based scoring with label boosting. The generic `bug` label was excluded (34% of issues, too broad to be informative). Specific sub-labels (`regression`, `bug:crash`, `bug:behavior`, `enhancement`) were used instead.
- **Pain-Point Index**: Composite of volume, open fraction, and log-scaled count of still-open issues.
- **All figures** saved to `figures/` directory.

---

## 8. Output Files

| File | Description |
|---|---|
| `analysis.ipynb` | Full analysis notebook with all code and outputs |
| `theme_table.csv` | Theme distribution, resolution, and S/P/G breakdown |
| `spg_classification.csv` | Per-issue S/P/G scores and theme assignments |
| `representative_cases.csv` | Top 3 representative issues per theme |
| `figures/` | All generated charts (8 figures) |
| `analysis_summary.md` | This report |
