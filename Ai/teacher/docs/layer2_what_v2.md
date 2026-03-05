# 📘 LAYER 2 — THE WHAT
## The Lifecycle Contract
### One document. Twelve stages. Discovery-driven hybrid progression.

---

# I. The Boundary Rule

**Stages 1–9:** Jupyter Notebook only. This is the laboratory.
**Stage 10:** The gate. The notebook does not advance to production until Stage 10 passes completely.
**Stages 11–12:** src/ + app/ + scripts/ only. This is the factory.

Notebook is laboratory.
Pipeline is factory.
Stage 10 is the door between them.

No stage may begin until the previous stage's exit criteria are met.
No exception. No negotiation. No merging.

---

# II. Project Setup — Before Stage 1

Before analysis begins, the following must exist and be confirmed:

```
project_root/
├── data/
│   ├── raw/              ← dataset lives here. Never modified.
│   ├── processed/        ← pipeline outputs land here.
│   └── db/
│       └── turns.db      ← DuckDB database. Created at Stage 1.
├── notebooks/
│   └── exploration.ipynb
├── src/
│   ├── load.py           ← empty until Stage 12
│   ├── clean.py          ← empty until Stage 12
│   ├── transform.py      ← empty until Stage 12
│   ├── aggregate.py      ← empty until Stage 12
│   ├── validate.py       ← empty until Stage 12
│   ├── pipeline.py       ← empty until Stage 12
│   └── export_excel.py   ← empty until Stage 11
├── app/
│   └── streamlit_app.py  ← empty until Stage 11
├── scripts/
│   └── run_pipeline.py   ← empty until Stage 12
├── requirements.txt
└── README.md
```

All files exist. All files empty except requirements.txt and README.md.
No analysis begins before setup is stable.

**Three SQL Tables (created progressively, all live in turns.db):**

| Table | Created At | Purpose | Behavior |
|---|---|---|---|
| raw_turns | Stage 1 | Replaces Excel as source of truth | Recreated on every pipeline run |
| intelligence_current | Stage 9 | Holds final processed state per unit | Overwritten on every run |
| turn_snapshots | Stage 10 | Historical snapshots for trend analysis | Appended on every run |

---

# III. The Twelve Stages

## Stage 0 — SETUP

| | |
|---|---|
| **Dominant Tool** | System verification |
| **Output Artifact** | Confirmed folder structure |
| **Business Question** | Is the environment ready? |
| **Stack** | None |
| **Module Home** | N/A |

**Contract:** Folder structure matches canonical specification. Dataset file confirmed in data/raw/. data/db/ directory exists. All src/ and app/ modules empty. Notebook exists.

**Exit:** Structure verified. Dataset location confirmed. No code written yet.

---

## Stage 1 — LOAD

| | |
|---|---|
| **Dominant Tool** | Pandas + DuckDB |
| **Output Artifact** | `stage1_raw` DataFrame + `raw_turns` table |
| **Business Question** | Did the file load correctly, is the schema safe, and is raw_turns created? |
| **Stack** | Pandas, DuckDB, Python |
| **Module Home** | load.py |

**Discovery Checkpoint:**
- What sheet names exist in the file?
- What columns are present?
- What data types were inferred?
- Are there any trailing spaces in column names?
- Do date columns parse correctly?

Agent does NOT assume answers. Agent executes methods to discover.

**SQL Introduced Here:**
After stage1_raw is loaded and schema validated, DuckDB takes ownership of the raw data:
```sql
CREATE OR REPLACE TABLE raw_turns AS SELECT * FROM stage1_raw
SELECT COUNT(*) FROM raw_turns  -- must match stage1_raw shape
SELECT * FROM raw_turns LIMIT 5  -- verify structure
```

**Architectural Principle (state explicitly at this stage):**
Python loaded and validated the schema. SQL now owns the raw data.
Excel becomes the input — not the source of truth.

**Contract:** File is loaded. Column headers are clean. Data types are visible. Dates are parsed. Schema validated against expected columns. raw_turns created in turns.db. Row count reconciled between DataFrame and table.

**Exit Verification Checklist:**
From Stage 1 card, verify ALL Tier 1 methods executed:
- [ ] pd.read_excel (or pd.read_csv)
- [ ] df.columns.str.strip
- [ ] df.shape
- [ ] df.columns
- [ ] df.dtypes
- [ ] pd.to_datetime (on date columns)
- [ ] df.head
- [ ] assert list(df.columns) == EXPECTED_COLUMNS
- [ ] duckdb.connect + CREATE OR REPLACE TABLE raw_turns
- [ ] SELECT COUNT(*) reconcile vs df.shape
- [ ] SELECT * LIMIT 5 verify structure

**Gate:** raw_turns row count must match stage1_raw shape. If they disagree — investigate before advancing.

**Stack note:** SQL enters here (DuckDB only). raw_turns written. No NumPy.

---

## Stage 2 — INSPECT

| | |
|---|---|
| **Dominant Tool** | Pandas + DuckDB |
| **Output Artifact** | None (observational) |
| **Business Question** | What is the current condition of the data — in both Pandas and SQL? |
| **Stack** | Pandas, DuckDB, Python |
| **Module Home** | None (notebook observation only) |

**Discovery Checkpoint:**
- Which columns have nulls? How many?
- What are the value distributions in categorical columns?
- Are there duplicate rows?
- Do SQL null counts match Pandas null counts?

**SQL Introduced Here:**
Profile raw_turns in SQL alongside Pandas profiling:
```sql
SELECT COUNT(*) FROM raw_turns                                        -- reconcile vs df.shape
SELECT COUNT(*) - COUNT(col) AS nulls FROM raw_turns                  -- reconcile vs isna().sum()
SELECT col, COUNT(*) FROM raw_turns GROUP BY col                       -- reconcile vs value_counts
SELECT * FROM raw_turns WHERE col IS NULL                              -- surface nulls explicitly
```

**Contract:** Dataset profiled in both tools. SQL null counts reconcile with df.isna().sum(). If they disagree — investigate before advancing.

**Exit Verification Checklist:**
From Stage 2 card, verify ALL Tier 1 methods executed:
- [ ] df.info
- [ ] df.describe
- [ ] df.value_counts (on categorical columns)
- [ ] df.nunique
- [ ] df.isna
- [ ] df.isna().sum
- [ ] df.duplicated
- [ ] SELECT COUNT(*) reconcile
- [ ] SELECT null counts reconcile
- [ ] SELECT GROUP BY value distributions reconcile
- [ ] SELECT WHERE IS NULL

**Stack note:** No Streamlit. No transformations. Observation only. SQL must reconcile with Pandas.

---

## Stage 3 — CLEAN

| | |
|---|---|
| **Dominant Tool** | Pandas |
| **Output Artifact** | `stage3_cleaned` DataFrame |
| **Business Question** | Is the data consistent enough for reliable analysis? |
| **Stack** | Pandas, Python |
| **Module Home** | clean.py |

**Discovery Checkpoint:**
- Which string columns need normalization?
- Which columns have type inconsistencies?
- What null-handling strategy fits each column?

**No SQL at this stage.**

**Architectural Principle (state explicitly):**
SQL is not a cleaning tool. Python cleans. SQL stores and queries. No SQL writes during Stage 3.

**Contract:** Strings standardized. Types corrected. Nulls handled with explicit strategy. Duplicates addressed. Each cleaning step validated before the next begins.

**Exit Verification Checklist:**
From Stage 3 card, verify ALL Tier 1 methods executed:
- [ ] df['col'].str.lower / str.strip / str.replace
- [ ] df.astype
- [ ] df.fillna / df.dropna
- [ ] df.drop_duplicates
- [ ] assert statements validating cleaning

**Exit:** `stage3_cleaned` exists. Type consistency achieved. Cleaning logic documented.

---

## Stage 4 — SELECT

| | |
|---|---|
| **Dominant Tool** | Pandas + DuckDB |
| **Output Artifact** | Filtered operational DataFrame |
| **Business Question** | What is our operational scope? |
| **Stack** | Pandas, DuckDB, Python |
| **Module Home** | clean.py or load.py |

**Discovery Checkpoint:**
- What scope does the user want to analyze?
- Which rows meet operational criteria?
- Which columns are needed for analysis?

**SQL Introduced Here:**
Mirror Pandas boolean filtering with SQL WHERE against raw_turns:
```sql
SELECT * FROM raw_turns WHERE Status = 'Vacant'
SELECT * FROM raw_turns WHERE Status IN ('Vacant', 'Notice')
SELECT * FROM raw_turns WHERE Move_out IS NOT NULL AND Status = 'Vacant'
```

**Gate:** SQL row count must match Pandas filtered DataFrame row count. The reconciliation is the teaching moment — same logic, two tools.

**Contract:** Pandas filtering hardened. SQL WHERE mirrored. Both tools agree. Scope confirmed by user.

**Stack note:** Pandas boolean filtering must be hardened before SQL WHERE is introduced. SQL reconciles — it does not replace.

---

## Stage 5 — TRANSFORM (Core Facts)

| | |
|---|---|
| **Dominant Tool** | Pandas + NumPy |
| **Output Artifact** | `stage5_core_facts` DataFrame (+12 flags/features) |
| **Business Question** | What is the unit-level operational status? |
| **Stack** | Pandas, NumPy, Python |
| **Module Home** | transform.py |

**No SQL at this stage.**

**Architectural Principle:** Vectorized operations belong in Python. SQL receives the result — it does not compute it.

**Contract:** Row-level features created using vectorized NumPy operations. Boolean flags derived from business rules. No aggregation — all logic operates per-row.

**Stack note:** NumPy enters here. Required for performant vectorized operations. No SQL — row-level transforms belong in Python.

---

## Stage 6 — TRANSFORM (Task Mechanics)

| | |
|---|---|
| **Dominant Tool** | Pandas |
| **Output Artifact** | `stage6_task_mechanics` DataFrame (+5 workflow fields) |
| **Business Question** | What is the workflow state per unit? |
| **Stack** | Pandas, NumPy, Python |
| **Module Home** | transform.py |

**No SQL at this stage.**

**Architectural Principle:** Row-level task logic and sequence evaluation belong in Python. SQL is not the right tool for row-by-row conditional workflows.

---

## Stage 7 — AGGREGATE

### Stage 7A — Pandas Aggregation

| | |
|---|---|
| **Dominant Tool** | Pandas |
| **Output Artifact** | Summary tables |
| **Business Question** | What is the portfolio-level operational state? |
| **Stack** | Pandas, Python |
| **Module Home** | aggregate.py |

**Discovery Checkpoint:**
- What aggregation grains make operational sense?
- What KPIs would inform decisions given what the data revealed in Stages 2–6?

**No SQL yet.** Pandas groupby must be hardened before SQL GROUP BY is introduced.

**KPI Contract — mandatory for every KPI (11 fields):**
1. Name | 2. Purpose | 3. Formula | 4. Code | 5. Units
6. Aggregation grain | 7. Edge-case handling | 8. Validation check
9. Alternative Grain | 10. Sensitivity / Outlier Awareness | 11. Sample Sufficiency

**KPI Sanity — all four must pass:**
Range check + Reconciliation + Spot-check + Edge-case test

**Exit Gate to 7B:** All Pandas aggregation locked. All KPIs validated.

---

### Stage 7B — SQL from Zero (10 Patterns)

| | |
|---|---|
| **Dominant Tool** | DuckDB/SQL |
| **Output Artifact** | Validated SQL fluency |
| **Business Question** | Can I execute SQL from memory against raw_turns? |
| **Stack** | SQL/DuckDB, Python |
| **Module Home** | aggregate.py |

**Entry Condition:** Pandas groupby fully hardened.

**10 SQL Patterns (hardened in strict order, Recall Reconstruction mandatory for each):**

1. SELECT + WHERE
2. GROUP BY + COUNT
3. Multi-column GROUP BY with multiple aggregations
4. LEFT JOIN (raw_turns → turn_snapshots)
5. CASE WHEN conditional aggregation
6. ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)
7. CTE — WITH clause
8. Subquery
9. RANK() / DENSE_RANK() OVER
10. LAG() / LEAD() for trend detection across turn_snapshots

**Recall Reconstruction Protocol (mandatory per pattern):**
1. Close all references
2. Rewrite SQL from memory
3. Execute
4. Compare output to original
5. Explain logic verbally

**Exit Gate to Stage 8:** All 10 SQL patterns recall-ready.

**Portfolio Milestone:**
At this point, you have built: data loading, cleaning, transformation, KPI calculation, AND SQL fluency across 20 patterns. This is interview-ready.

---

## Stage 8 — SLA ENGINE

| | |
|---|---|
| **Dominant Tool** | Pandas + NumPy + DuckDB |
| **Output Artifact** | `stage8_sla_engine` DataFrame (+5 SLA flags) |
| **Business Question** | Which units are breaching performance standards? |
| **Stack** | Pandas, NumPy, DuckDB, Python |
| **Module Home** | transform.py |

**SQL Cross-Validation Introduced Here:**
After Python computes SLA flags, SQL validates them:
```sql
SELECT Unit FROM raw_turns WHERE Ready_Date IS NULL AND Move_out < CURRENT_DATE - INTERVAL 14 DAYS
SELECT COUNT(*) FROM raw_turns WHERE Status = 'Vacant' AND Move_out IS NOT NULL
```

**Gate:** SQL breach count must match Python SLA flag sum. If they disagree — there is a bug. Find it before advancing.

---

## Stage 9 — INTELLIGENCE ENGINE

| | |
|---|---|
| **Dominant Tool** | Pandas + NumPy + DuckDB |
| **Output Artifact** | `stage9_intelligence` DataFrame + `intelligence_current` table |
| **Business Question** | What decisions need to be made about each unit? |
| **Stack** | Pandas, NumPy, DuckDB, Python |
| **Module Home** | transform.py |

**intelligence_current Created Here:**
After Python computes the intelligence layer, write it to SQL:
```sql
CREATE OR REPLACE TABLE intelligence_current AS SELECT * FROM stage9_df
SELECT Operational_State, COUNT(*) FROM intelligence_current GROUP BY Operational_State
SELECT * FROM intelligence_current WHERE SLA_Breach = TRUE ORDER BY DTBR DESC
```

**Architectural Principle (state explicitly):**
Python computed the intelligence. SQL now owns the current state.
Streamlit will read from intelligence_current — not from Python DataFrames.

**Gate:** intelligence_current row count must match stage9 DataFrame row count.

---

## Stage 10 — VALIDATE (THE GATE)

| | |
|---|---|
| **Dominant Tool** | Python + DuckDB |
| **Output Artifact** | Validation report + `turn_snapshots` written |
| **Business Question** | Can we trust this intelligence? |
| **Stack** | Pandas, DuckDB, Python |
| **Module Home** | validate.py |

**turn_snapshots Created Here:**
```sql
INSERT INTO turn_snapshots
SELECT *, CURRENT_TIMESTAMP AS snapshot_time FROM intelligence_current
```

**Full SQL Validation Suite (all must pass):**
```sql
SELECT COUNT(*) FROM raw_turns                                         -- vs stage1_raw shape
SELECT COUNT(*) FROM intelligence_current                              -- vs stage9 shape
SELECT COUNT(*) FROM intelligence_current WHERE Unit IS NULL           -- must be 0
SELECT COUNT(*) - COUNT(DISTINCT Unit) FROM intelligence_current       -- must be 0
SELECT Operational_State, COUNT(*) FROM intelligence_current GROUP BY Operational_State  -- sanity
SELECT * FROM intelligence_current WHERE DTBR < 0                      -- impossible values
SELECT COUNT(*) FROM turn_snapshots                                    -- confirm snapshot written
```

**Full validation suite (all must pass):**
1. Schema validation
2. Type validation
3. Null integrity
4. Duplicate integrity
5. Row count reconciliation (Python + SQL)
6. KPI sanity (all 4 checks, all KPIs)
7. Assertion suite
8. Distribution plausibility check
9. SQL cross-validation suite (7 queries)

**All 9 checks must pass. Gate opens only when all pass.**

**Portfolio Milestone:**
At this point: complete production-grade data pipeline + validation discipline + three-table hybrid database. Stronger than most senior analyst portfolios.

**Exit:** All checks pass. `turn_snapshots` written. Notebook Complete = Yes.

---

## Stage 11 — PRESENT

| | |
|---|---|
| **Dominant Tool** | Streamlit + OpenPyXL |
| **Output Artifact** | Dashboard + Excel export |
| **Business Question** | How do we communicate this intelligence? |
| **Stack** | Pandas, DuckDB, Streamlit, OpenPyXL, Python |
| **Module Home** | app/streamlit_app.py + src/export_excel.py |

**UI reads exclusively from SQL. Zero DataFrame logic.**

```sql
SELECT * FROM intelligence_current ORDER BY DTBR DESC                  -- dashboard data
SELECT Status, COUNT(*) FROM intelligence_current GROUP BY Status      -- KPI display
SELECT snapshot_time, COUNT(*) FROM turn_snapshots
  GROUP BY snapshot_time ORDER BY snapshot_time                        -- trend chart
SELECT * FROM turn_snapshots WHERE SLA_Breach = TRUE
  ORDER BY snapshot_time DESC                                          -- historical SLA
```

**Contract:** Dashboard reads intelligence_current for current state, turn_snapshots for trends. Zero transformation logic in UI. Zero KPI recalculation. Excel export formatted and professional.

**Gate:** Unlocked only after Stage 10 + pipeline runs end-to-end + outputs match.

---

## Stage 12 — AUTOMATE

| | |
|---|---|
| **Dominant Tool** | Python + DuckDB |
| **Output Artifact** | run_full_pipeline executable |
| **Business Question** | Can we run this again next week on new data? |
| **Stack** | Python, DuckDB, SQL |
| **Module Home** | scripts/run_pipeline.py + src/pipeline.py |

**Pipeline sequence (mandatory order):**
1. `DROP TABLE IF EXISTS raw_turns` → recreate from Excel
2. Python transforms → write to intelligence_current
3. `INSERT INTO turn_snapshots` → snapshot current state
4. SQL validation suite → all checks pass
5. Streamlit reads from SQL → display results

**Idempotency Test:**
Run pipeline 10 times:
- raw_turns: same row count every run (recreated, not appended)
- intelligence_current: same row count every run (overwritten)
- turn_snapshots: grows by 90 rows per run (one snapshot per unit per run)

**Migration sequence (mandatory order):**
1. Stage 1 logic → load.py
2. Stage 3 logic → clean.py
3. Stages 5, 6, 8, 9 logic → transform.py
4. Stage 7 logic → aggregate.py
5. Stage 10 logic → validate.py
6. Orchestration → pipeline.py
7. Entry point → scripts/run_pipeline.py

Each migration step tested before the next begins.
After successful run: Production Ready = Yes.

---

# IV. Stage Transition Rules

A stage may not begin until:
- Exit criteria of previous stage are satisfied
- All validations at that stage pass
- All Tier 1 methods from Stage Method Map card executed (verified by agent)

No stage skipping. No stage merging. No assumptions about completion.
Verification against Stage Method Map card is mandatory before any stage transition.

---

# V. Module Responsibility Map

| Module | Responsibility | Source Stages |
|--------|---------------|---------------|
| load.py | File loading, schema validation, raw_turns creation | Stage 1 |
| clean.py | Type fixing, null handling, string normalization, scope filtering | Stages 3, 4 |
| transform.py | Row-level features, SLA flags, intelligence layer | Stages 5, 6, 8, 9 |
| aggregate.py | KPI calculations, grouping, summary tables, SQL aggregation | Stage 7 |
| validate.py | Schema, type, null, duplicate, KPI sanity, SQL cross-validation | Stage 10 |
| export_excel.py | Excel formatting and export | Stage 11 |
| pipeline.py | Orchestration only. No business logic. | Stage 12 |
| streamlit_app.py | Dashboard display. Reads turns.db only. Zero logic. | Stage 11 |
| run_pipeline.py | Entry point. Calls pipeline. Logs transitions. | Stage 12 |

---

# VI. Stack Evolution

| Stage | Active Stack | New Tool Introduced |
|-------|-------------|---------------------|
| 0 | None | N/A |
| 1 | Pandas, DuckDB, Python | Pandas, DuckDB |
| 2 | Pandas, DuckDB, Python | None |
| 3 | Pandas, Python | None (no SQL in cleaning) |
| 4 | Pandas, DuckDB, Python | None |
| 5 | Pandas, NumPy, Python | NumPy |
| 6 | Pandas, NumPy, Python | None |
| 7A | Pandas, Python | None |
| 7B | Pandas, DuckDB, Python | SQL depth (10 patterns) |
| 8 | Pandas, NumPy, DuckDB, Python | None |
| 9 | Pandas, NumPy, DuckDB, Python | None |
| 10 | Pandas, DuckDB, Python | None |
| 11 | Pandas, DuckDB, Streamlit, OpenPyXL, Python | Streamlit, OpenPyXL |
| 12 | Python, DuckDB, SQL | None (orchestration only) |

Stack additions are controlled.
No premature tool introduction allowed.

---

# VII. SQL Pattern Count by Stage

| Stage | New Patterns | Cumulative Total |
|---|---|---|
| S1 | 3 | 3 |
| S2 | 4 | 7 |
| S4 | 3 | 10 |
| S7B | 10 | 20 |
| S8 | 2 | 22 |
| S9 | 3 | 25 |
| S10 | 9 | 34 |
| S11 | 7 | 41 |
| S12 | 8 | 49 |

49 total SQL patterns across 3 normalized tables.
Hire-ready SQL profile by Stage 12.

---

# VIII. Completion Criteria

Project is complete when all 27 criteria pass (see Layer 4 for full specification).

Brief checklist:
- Pipeline executes end-to-end (`python scripts/run_pipeline.py`)
- All three tables populated and validated
- turn_snapshots grows by 90 on each run
- Dashboard reads from turns.db exclusively
- Outputs match notebook exactly
- Idempotency verified
- Performance documented
- All 9 validation checks pass
- All KPIs pass 4-check sanity
- UI contains zero logic
- User can defend all decisions including SQL choices

**27/27 = Complete. Not 26. Not "almost." 27.**
