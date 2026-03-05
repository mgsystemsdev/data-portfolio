# Career & Data Portfolio Plan

**Miguel A. Gonzalez Almonte**  
Plano, TX • mg.systems.dev@gmail.com • mgsystemsdev.github.io • github.com/mgsystemsdev • linkedin.com/in/miguel-gonzalez-8a389791

This document ties together: (1) recruiter-facing career positioning, (2) resume alignment and gaps, and (3) the plan to populate the data portfolio with real analysis from DMRB and reference context.

---

## Part I — Career Positioning (Recruiter-Facing)

### Who Is Miguel Gonzalez

**Miguel A. Gonzalez Almonte** is an **operations leader** who builds **data-driven and automated systems** to solve real workflow problems. He combines 10+ years in maintenance and service operations with data analytics, Python automation, and AI-assisted decision systems.

**Headline (Analytics focus):**  
**Operations Leader & Data Automation Developer**  
*Turning Operational Workflows into Data-Driven Systems*

**Headline (AI positioning):**  
**Operations Leader | Data & AI Automation Developer**  
*Building Software Solutions for Real Business Workflows*

**Core narrative:**  
Operations leader who built software to solve real problems — not a software engineer who used to do operations. Story: **Operations → Data → Automation → AI.**

### Career Transition

Miguel is transitioning from operations leadership into technical roles by combining **10+ years of operational analytics** with new **production-level skills** in Python, SQL, and data automation. This is a **capability migration**: the same systems thinking and domain expertise, now evidenced by shipped software, data models, and automation.

### Core Competencies

- Operational Data Analytics
- Python Data Automation
- SQL Data Modeling
- Business Intelligence Dashboards
- Workflow Automation
- AI-Assisted Decision Systems

### Experience Timeline (Knowledge Areas)

| Area | Years | Context |
|------|--------|---------|
| **Service & Operations / Project Management** | 10+ years | Maintenance, operations, guest services; leading teams, process improvement, adoption of new tools. |
| **Data, Excel, Dashboards & Analytics** | 10 years | Excel and Power BI dashboards, operational KPIs, data pipelines, BI reporting, workflow optimization. |
| **AI, Python, Data Automation** | 2 years | Custom GPT/Gemini workflows, API integrations, Python automation, prompt orchestration, LLM-augmented dashboards. |

*Do not inflate these numbers. Honesty builds credibility.*

### Target Roles (Focused)

- **Primary:** Analytics Engineer / Data Analytics Developer — build trusted metrics, models, and pipelines; turn operations into reliable data infrastructure.
- **Secondary:** AI Workflow & Automation Developer — orchestrate LLMs with APIs, dashboards, and lightweight Python.
- **Backup:** Data Analyst / BI Developer — SQL, Excel, Power BI/Tableau, stakeholder communication.

*One clear lane in recruiter-facing material.*

### Tech Stack

- **Languages & data:** Python (data workflows & automation), Pandas, SQL
- **Tools:** Streamlit, Power BI, Supabase
- **LLM systems:** GPT-4, Gemini, Claude
- **Automation:** API integrations, prompt orchestration, workflow tooling

### Flagship Project: MakeReady Operational Intelligence System

*(Formerly referenced as Make Ready Digital Board / DMRB.)*

- **What:** Operational intelligence system (software + Streamlit web app) for coordinating make-ready work and unit turnover.
- **Problem:** Replacing whiteboard and ad-hoc tracking with a single, streamlined digital workflow.
- **Tech:** Python, Streamlit, SQLite/Supabase, Power BI, Pandas.
- **Impact:** Reduced turnover/operational timelines by **~50%**; adopted by **20+ users**.
- **Why it works:** Real operational software, used by real users, with measurable impact.

*In interviews, be ready to explain how each impact number was measured (baseline vs. after).*

### The Story in One Line

**Not:** "I learned to code."  
**Yes:** "I solved operational problems for 10 years. Then I built software to eliminate them."

---

## Part II — Resume Analysis & Alignment

*Reference: `resume.md` in this folder.*

### How the Resume Aligns with Positioning

| Element | In resume.md | Verdict |
|--------|----------------|---------|
| **Headline** | "Operational Systems Architect" + SQL • Python • Data Engineering • Process Infrastructure | Strong; avoids "self-taught," signals systems ownership. |
| **Narrative** | Operations → data infrastructure → pipelines, validation, reliability | Aligned with primary target (Analytics Engineer / Data Analytics Developer). |
| **Target lane** | Implied: data/analytics infrastructure, pipelines | Fits Analytics Engineer / Data Analytics Developer. |
| **Experience timeline** | 10+ years operations, 2+ years data infrastructure | Slightly narrower than "10 years data/analytics" in positioning; summary could note longer Excel/dashboard history. |
| **Flagship project** | "Operational Intelligence Pipeline" + "Revenue & Transaction Integrity Engine" + "Data Validation & Guardrail Framework" | **Gap:** MakeReady is not named; the 50% / 20+ users story is missing. |

### Strengths of the Current Resume

- **Headline** — "Operational Systems Architect" is senior and credible.
- **Professional summary** — Clear value prop (10+ ops, 2+ data infrastructure, pipelines, validation, audit-ready).
- **Core Capabilities** — Very strong for analytics/data engineering: specific SQL (CTEs, window functions, NULL-safe, row multiplication), ETL, validation, Pandas pipelines.
- **Quantified impact** — 30% audit improvement, 40% less manual oversight, 70% reporting time reduction, $100K+ savings, 15% fewer delays, 50% reporting turnaround.
- **Projects** — Three systems (pipeline, revenue/transaction integrity, validation) show range.
- **Structure** — Clear sections, scannable, ATS-friendly.

### Gaps and Recommended Fixes

| Issue | Recommendation |
|-------|----------------|
| **MakeReady not named** | Add a **Selected Systems Project** (or rename the first) to **"MakeReady Operational Intelligence System"** with problem, stack, and outcome (e.g. ~50% faster turnover, 20+ users). Keep the other two projects. |
| **$100K+ savings (RPM)** | Be ready to explain: what was measured, baseline vs. after, time period. Optionally soften to "significant cost avoidance" if exact number is hard to defend. |
| **150+ properties (MAA)** | Confirm scope (your scope vs. company total). Rephrase if needed (e.g. "across portfolio" or "across X properties"). |
| **AI/LLMs absent** | Fine for Analytics Engineer focus. For AI Workflow roles, add one short bullet or capability line (e.g. "AI-assisted decision systems"). |
| **Contact** | Add phone (787-367-9843) in the contact block for applications. |

### ATS & Recruiter Readability

- Sections and formatting are standard and parse-friendly.
- Keywords are strong for data/analytics engineering (SQL, Python, Pandas, ETL, CTEs, validation, Power BI, Git, Supabase).
- When exporting to PDF, keep to **2 pages max** (trim Core Capabilities or project bullets if needed).

---

## Part III — Data Portfolio Population Plan

*Goal: Populate the data portfolio with real data analysis from `refecerence_context` and `the-dmrb` so recruiters see the same story as the resume and positioning.*

### Source Inventory

**refecerence_context**

| Location | Contents | Use in portfolio |
|----------|----------|------------------|
| **Reports/data/** | Units.csv, Move-Outs.csv, Pending Move Ins.csv, Available Units.csv, DMRB_raw.xlsx, PendingFAS-.csv | Raw data description, sample rows |
| **Reports/output/** | reconciliation_output.xlsx, Final_Report.xlsx | Reconciliation results, "golden" comparison |
| **Reports/reconciliation_check.py** | Recon vs DMRB merge, mismatch flags (Missing in DMRB, Avail Date, Move In), styled Excel output | Pipeline narrative, transformation logic, insights |
| **Reports/clean_up.py** | Process Available Units, Move Ins; phase filter (5,7,8); datetime parsing; Excel output | Cleaning steps, transformation |
| **Reports/backfill_recon.py**, **movein_records.py** | Backfill Recon from DMRB; move-in records | Transformation logic |
| **ui /viewsst/pivot_analytics.py** | Task pipeline counts, Aging by Operational_State/DV, Workload crosstabs, Stall tracker | KPIs, visualizations, analysis |
| **ui /viewsst/full_table_view.py**, **unit_cards.py**, **unit_overview.py**, **flag_bridge_view.py** | Full table, unit cards, flag view | Processed dataset / table view |
| **ui /logic/filters.py**, **filter_controls.py** | Phase, status, N/V/M filters | Analysis (filtering) |

**the-dmrb**

| Location | Contents | Use in portfolio |
|----------|----------|------------------|
| **db/schema.sql**, **db/migrations/** | property, unit, turnover, task_template, task, import_batch, sla_event, audit_log, etc. | Target schema, SQL logic, data model |
| **domain/lifecycle.py** | derive_lifecycle_phase, effective_move_out_date, N/V/M | Lifecycle rules, analysis |
| **domain/risk_engine.py**, **domain/sla_engine.py** | Risk and SLA logic | Analysis (risk/SLA) |
| **domain/enrichment.py** | compute_facts, compute_intelligence, compute_sla_breaches, enrich_row | Enrichment pipeline, transformation |
| **domain/unit_identity.py** | Normalize unit code, parse phase/building/unit | Cleaning, identity |
| **services/board_query_service.py** | Board rows, flag bridge, turnover detail | SQL / query concepts |
| **docs/UNIT_MASTER_CSV_ANALYSIS.md**, **UNIT_IDENTITY.md**, **BACKEND_ENRICHMENT_DELIVERABLES.md** | Data profile, identity rules, enrichment summary | Overview, dataset description, pipeline |
| **data/test_imports/*.csv** | Test move_outs, available_units, pending_move_ins, pending_fas | Sample inputs for pipeline |

### Current Portfolio State

- **Page 1 – Operational Turnover Intelligence:** Placeholder only ("Replace with…").
- **Page 2 – Inventory Flow Analytics:** Placeholder only.
- **Page 3 – Revenue Subscription Analytics:** Placeholder only; no source data in DMRB/reference context (out of scope or "Coming soon").
- **Page 4 – About Me:** Can align with Part I of this plan.
- **sql/turnover_queries.sql:** Empty. **inventory_queries.sql**, **revenue_queries.sql:** Empty.
- **pipeline/** (transform, clean_data, load_data, metrics): Stubs or minimal.

### Mapping: Sources → Portfolio Sections (Page 1)

| Portfolio section | Source(s) | Action |
|-------------------|-----------|--------|
| **Overview – Problem Statement** | BACKEND_ENRICHMENT_DELIVERABLES, reconciliation intent | 2–3 sentences: make-ready coordination, reporting chaos, single source of truth. |
| **Overview – Skills** | Reports (pandas, merge, date logic), the-dmrb (SQL, schema, domain) | Bullets: SQL schema design, pandas ETL, reconciliation, lifecycle/SLA derivation, validation. |
| **Overview – Dataset** | Reports/data CSVs, DMRB_raw, UNIT_MASTER_CSV_ANALYSIS, schema.sql | Units, move-outs, available units, pending move-ins; canonical schema (unit, turnover, task). |
| **Data Pipeline – Raw Data** | Reports/data/*.csv, DMRB_raw.xlsx, UNIT_MASTER_CSV_ANALYSIS | List sources; sample rows; header/quirk notes. |
| **Data Pipeline – Cleaning** | clean_up.py, unit_identity, reconciliation_check | Strip, phase filter, datetime coercion, unit normalize. |
| **Data Pipeline – Transformation** | backfill_recon, reconciliation_check (merge, flags), enrichment, lifecycle | Recon ↔ DMRB merge, mismatch flags, enrichment (DV, operational state), lifecycle phase. |
| **Data Pipeline – Processed** | Final_Report / reconciliation_output, pivot_analytics columns | Board-ready dataset: unit, status, dates, task pipeline, assignee. |
| **SQL Logic** | schema.sql, board_query_service | 1–2 real queries (open turnovers, unit + lifecycle); explanation; sample output. |
| **Analysis – KPIs** | pivot_analytics (Task Pipeline, Aging, Stalled), reconciliation (mismatch counts) | 3–5 metrics: units by state, avg/max DV, stalled count, recon mismatches. |
| **Analysis – Visualizations** | pivot_analytics (task pipeline table, aging, crosstabs, stall table) | Tables/charts; reuse or recreate in data-portfolio/visuals. |
| **Insights** | reconciliation_check (what mismatches mean), pivot (stalls, workload) | Key findings + operational impact (single source of truth, 50% faster, 20+ users). |

### Mapping: Page 2 (Inventory Flow)

Treat "unit flow" (available → move-out → pending move-in) as inventory. Use **clean_up.py** and **Reports/data** (Available Units, Move-Outs, Pending Move Ins) for Overview, Pipeline, and one query; same KPI/insight style as Page 1, framed as flow and velocity.

### Phased Fill Plan

**Phase 1 – Page 1 content (narrative only)**  
Write Overview, Data Pipeline, SQL Logic (add 1–2 queries to `sql/turnover_queries.sql`), Analysis (KPIs, placeholder or static table), Insights. No live pipeline yet; portfolio tells the story with copy and sample data.

**Phase 2 – Page 1 live pipeline and visuals**  
Copy or link Reports/data into data-portfolio/data/raw. Implement load_data → clean_data → transform (and optionally metrics) from clean_up.py, reconciliation_check, unit_identity. Run turnover_queries; replace placeholders with real tables/charts from processed data.

**Phase 3 – Page 2 (Inventory Flow)**  
Overview + Dataset from clean_up + Reports/data. Reuse pipeline; add one transform or view for unit flow. Add 1–2 queries to inventory_queries.sql; fill Analysis and Insights.

**Phase 4 – Polish**  
Align About Me and Home with Part I. Page 3: "Coming soon" or hide until revenue data exists. Optional README summarizing refecerence_context vs the-dmrb and how each maps to portfolio pages.

### File-Level Checklist

- [ ] **Reconciliation & reports:** reconciliation_check.py, clean_up.py, backfill_recon.py, movein_records.py → pipeline narrative, transformation, insights. Reports/data and output → raw and processed description.
- [ ] **UI/analysis:** pivot_analytics.py → KPIs, visuals; full_table_view, unit_cards, flag_bridge_view → processed dataset.
- [ ] **the-dmrb:** schema.sql + migrations → pipeline + SQL; lifecycle, enrichment, risk, sla → analysis; UNIT_MASTER_CSV_ANALYSIS, BACKEND_ENRICHMENT_DELIVERABLES → overview + dataset.
- [ ] **data-portfolio:** Populate sql/turnover_queries.sql (then inventory_queries.sql); implement pipeline/ from reference logic; fill pages/1 and pages/2; set pages/3 to "Coming soon" or hide; copy minimal raw data into data-portfolio/data/raw.

---

## Summary

1. **Part I** is the single recruiter-facing career story: operations leader → data automation developer, with one flagship (MakeReady), clear target roles, and the "10 years problems, then software" line.
2. **Part II** ensures the resume supports that story and names MakeReady with defensible impact; it also flags small fixes (contact, $100K, 150+ properties, optional AI line).
3. **Part III** turns DMRB and reference context into portfolio proof: same pipeline, reconciliation, and analysis that the resume and positioning describe, so recruiters see one consistent narrative across resume, positioning, and portfolio.

*Keep this document internal. Use Part I for LinkedIn, About Me, and talking points; use Part II when updating resume.md; use Part III when implementing data-portfolio pages and pipeline.*
