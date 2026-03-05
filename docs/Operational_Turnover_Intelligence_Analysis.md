# Operational Turnover Intelligence — Portfolio Analysis

**Goal:** Position you as a strong data analyst/designer with a portfolio piece you control, understand, and can explain.  
**Scope:** What’s working, what’s missing, and what to add (without changing architecture or scope).

---

## What’s Working Well

| Area | Why it helps |
|------|----------------|
| **Problem statement** | Clear business context (service manager, make-ready coordination, bottlenecks, cost of missed dates). |
| **End-to-end pipeline** | Load → clean → transform → enrich → metrics is visible and documented; you can walk through it in an interview. |
| **Real, controlled data** | DMRB_board.csv is real ops data; you own the snapshot and can explain every column. |
| **Transformation logic** | Clean / Transform / Enrich is documented with bullet points; DV, DTBR, N/V/M, task dates, SLA flags are all explained. |
| **Business metrics** | KPIs (units, avg DV, stalled, inspection/turn SLA breach, task completion %) are computed from the pipeline, not placeholders. |
| **Operational impact** | Concrete outcome (~50% reporting improvement, 20+ users) shows impact, not just technique. |
| **SQL tab** | Canonical “open turnovers + tasks” query and sample output show you think in unit/turnover/task terms. |
| **Full scrollable tables** | Raw and processed data are shown in full with fixed height; no hidden rows. |

---

## Gaps (What You Claim vs What’s Shown)

These are **narrative vs implementation** gaps—you mention capabilities that aren’t yet demonstrated on the page.

### 1. Visualizations

- **Skills / Visualizations:** You say “task pipeline counts, aging by state, workload crosstabs” and “Dashboard and visualization.”
- **Reality:** Analysis tab shows **tables only** (by_status, by_operational_state, task_pipeline_counts as a long-format table). No charts.
- **Recommendation:** Add 1–2 simple charts so “visualization” is real:
  - **Task pipeline:** Bar chart of task (Insp, Paint, MR, HK, CC) by status (Done / In Progress / Scheduled / Not Started), using existing `task_pipeline_counts`.
  - **Operational state:** Bar chart of unit count by `Operational_State` (using existing `by_operational_state`).
- Streamlit: `st.bar_chart` or `st.pyplot`/`altair`/`plotly` with a small DataFrame. Keeps scope minimal.

### 2. Assignee / Workload

- **Key Findings:** “Assignee workload is visible in crosstabs so load can be balanced.”
- **Reality:** `Assign` exists in DMRB_board.csv and in board_df, but **metrics.py** does not compute by-assignee counts or workload. Analysis tab has no assignee breakdown.
- **Recommendation:** In `metrics.py`, add something like `by_assignee`: count of units (or of open turnovers) per `Assign` value. In the Analysis tab, add a short “Units by Assignee” section and a small table or bar chart. That delivers on “workload crosstabs” without building a full crosstab.

### 3. Aging by Operational State

- **Visualizations / Trend:** You mention “aging by operational state (avg/max DV).”
- **Reality:** You show count by operational state (`by_operational_state`) but not **avg or max DV** (or Aging_Business_Days) per state.
- **Recommendation:** In `compute_metrics`, add e.g. `aging_by_state`: for each `Operational_State`, compute `avg(DV)` and `max(DV)` (or use `Aging_Business_Days`). Show as a small table in Analysis (“Avg / max days vacant by operational state”). One table, no new dependencies.

### 4. Data Quality / Validation

- **Skills:** “Data validation — Reconciliation checks, mismatch flagging, record alignment.”
- **Reality:** You correctly note the portfolio uses a single board snapshot (no reconciliation file). So “reconciliation” is described but not demonstrated.
- **Recommendation:** Add a small **Data quality** subsection (Data Pipeline or Analysis):
  - Row count before/after clean (e.g. “Rows after phase filter: N”).
  - Count of nulls for key columns (Move_out, Move_in, Status) or “Units with missing Move_in: N.”
  - Optional: date range (min/max Move_out) so readers see the window of data.
  - One sentence: “In production, reconciliation compared this board to the property report; here we show basic quality checks on the board snapshot.” That way you don’t overclaim reconciliation but you do show validation thinking.

### 5. Methodology / Reproducibility

- **For recruiters/hiring managers:** “How do I run this?” is often missing in portfolios.
- **Recommendation:** On the Overview or Data Pipeline tab, add one line: “Pipeline: Python 3.x, pandas; run locally with Streamlit (see repo README).” If the repo has a README with `pip install -r requirements.txt` and `streamlit run app.py`, reference it. No need for a full methods section.

### 6. SQL Depth

- **Current:** One static query + sample output. Good for “I think in SQL.”
- **Optional:** If `sql/turnover_queries.sql` (or similar) has more queries, add a second example (e.g. “Units by operational state” or “Stalled units”) so the SQL tab shows 2 use cases. Not required for “data analyst,” but strengthens the story.

---

## What You’re Not Missing (Keep As-Is)

- **Reconciliation logic:** You explicitly scoped it out (single CSV). Describing it in “Operational pipeline (context)” is enough; no need to implement it here.
- **Multiple data sources:** Same; the plan correctly keeps one primary source.
- **Trend over time:** Snapshot data doesn’t support real time series; “Trend Analysis” as narrative is fine.
- **Full MakeReady app:** Portfolio is “case study + pipeline + metrics,” not the full app. That’s appropriate.

---

## Suggested Priority

| Priority | Action | Effort |
|----------|--------|--------|
| **P1** | Add assignee metric + “Units by Assignee” table (and optional bar chart) so “workload” is real. | Low |
| **P2** | Add “Aging by operational state” (avg/max DV per state) table. | Low |
| **P3** | Add 1–2 bar charts (task pipeline by status; units by operational state). | Low |
| **P4** | Add a short Data quality line (row count, nulls or missing dates). | Low |
| **P5** | One sentence on reproducibility + README reference. | Trivial |
| **P6** | Optional: second SQL example if you have a query ready. | Trivial |

---

## Summary

You have a **strong base**: real problem, clear pipeline, documented logic, business metrics, and impact. The main gaps are **delivering on what you already claim** (visualizations, assignee workload, aging by state, light validation). Addressing P1–P5 would make the case study match the narrative and present you as a data analyst who designs pipelines, validates data, and turns metrics into clear visuals—without changing architecture or adding scope.
