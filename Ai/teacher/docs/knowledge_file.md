# APPRENTICESHIP ENGINE — KNOWLEDGE FILE
## Read at session start. Reference throughout.

---

# I. THE 8 ANCHORS — FULL DEFINITIONS

**1 — Intent**
What problem does this method solve right now, in this stage?
One or two sentences. Reference the user's actual dataset. No theory.
For SQL: which table, why this query, what business question it answers.

**2 — Return**
Exact return type: DataFrame / Series / Index / Tuple / Scalar / Boolean mask / None / Result set / AssertionError.
State whether it mutates or returns a new object.

**2B — Parameter Control (THE OPERATIONAL CORE)**
This is why the system exists. Do not summarize. Do not rush.
Walk through every meaningful way to drive this method:
- Every parameter — what it does, default value, what changes when set
- One row, multiple rows, a slice, a condition
- One column, multiple columns, an exclusion
- Combined row + column control in a single call
- What the return type changes to as inputs change
- One level of nesting

Each variation: one code example on the user's real data + one output line.

Model — df.loc on real DMRB dataset:
```python
df.loc[3]                                           # one row → Series
df.loc[[1, 3, 5]]                                   # multiple rows → DataFrame
df.loc[1:5]                                         # slice, inclusive → DataFrame
df.loc[3, 'Status']                                 # one row, one col → scalar
df.loc[3, ['Status', 'Unit']]                       # one row, multiple cols → Series
df.loc[df['Status'] == 'Vacant']                    # condition, all cols → DataFrame
df.loc[df['Status'] == 'Vacant', ['Unit', 'DTBR']] # condition + cols → DataFrame
df.loc[df['DTBR'] > 14, 'Unit']                    # condition + one col → Series
```

Apply this same depth to every method in every stage.
Method not owned until user can drive it in any direction without reference.

**3 — Shape**
Does row count change? Column count? Index reset?
State exactly what happened using the real output numbers.
For SQL: rows returned, table read, what structurally changed.

**4 — Failure**
What breaks this method on the user's actual data?
Show the error type: KeyError / TypeError / AssertionError / etc.
State the correction mechanically. No emotion. No "common mistake."

**5 — Composition**
What hardened method does this pair with naturally?
Show the combination. One layer only. Reference what was already locked.
For SQL: which Python method produces equivalent output — reconcile them.

**6 — Placement**
Exact module: load.py / clean.py / transform.py / aggregate.py / validate.py
For SQL: which table it reads from or writes to, which module owns the query.
Connect explicitly to the silent project accumulating in the background.

**7 — Trade-off**
Why this method instead of an alternative?
Given scale, performance, maintainability — what makes this choice defensible?
For SQL: why SQL here instead of Pandas? Why this query structure?
Not "it works." But "it works AND here is why this way instead of another."

---

# II. SQL TABLE OWNERSHIP BY STAGE

| Stage | SQL Action | Table |
|---|---|---|
| S1 | CREATE raw_turns from stage1_raw | raw_turns created |
| S2 | Profile + reconcile with Pandas | raw_turns read |
| S4 | WHERE filter + reconcile row counts | raw_turns read |
| S7B | 10 patterns including CTEs, window functions, LAG/LEAD | raw_turns + turn_snapshots |
| S8 | Cross-validate SLA flags | raw_turns read |
| S9 | CREATE intelligence_current from stage9_df | intelligence_current created |
| S10 | Full validation suite + INSERT turn_snapshots | turn_snapshots created |
| S11 | Dashboard queries — current state + trends | intelligence_current + turn_snapshots |
| S12 | Full idempotent pipeline orchestration | All 3 tables |

**Idempotency per table:**
- raw_turns: DROP + recreate every run → always same row count
- intelligence_current: CREATE OR REPLACE every run → always same rows
- turn_snapshots: INSERT every run → grows by 90 rows per run (correct by design)

**Stage 7B — 10 SQL Patterns (Recall Reconstruction mandatory per pattern):**
1. SELECT + WHERE
2. GROUP BY + COUNT
3. Multi-column GROUP BY + multiple aggregations
4. LEFT JOIN
5. CASE WHEN
6. ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)
7. CTE — WITH clause
8. Subquery
9. RANK() / DENSE_RANK() OVER
10. LAG() / LEAD() for trend detection across turn_snapshots

**Recall Reconstruction Protocol:**
1. Close all references
2. Rewrite SQL from memory
3. Execute
4. Compare output to original
5. Explain logic verbally
Pattern not locked unless recall passes.

---

# III. STAGE LIFECYCLE

**S0 SETUP:** Confirm folder structure + data/db/ + dataset in data/raw/ + empty modules.

**S1 LOAD:** Python loads Excel → stage1_raw. DuckDB takes ownership → raw_turns created.
State: "Python loaded. SQL now owns raw data." Gate: row counts must match.

**S2 INSPECT:** Pandas + SQL profile in parallel. SQL nulls must reconcile with isna().sum().

**S3 CLEAN:** Python only. State: "SQL is not a cleaning tool."

**S4 SELECT:** Pandas filters + SQL WHERE mirrors same filter. Row counts must reconcile.

**S5–S6 TRANSFORM:** Python + NumPy only. Vectorized logic belongs in Python.

**S7A AGGREGATE:** Pandas groupby hardened. All KPIs validated. Gate to 7B.

**S7B SQL DEPTH:** 10 patterns. Recall Reconstruction mandatory. All executed against real tables.

**S8 SLA ENGINE:** Python computes flags. SQL cross-validates. Counts must reconcile.

**S9 INTELLIGENCE ENGINE:** Python computes → intelligence_current written.
State: "Python computed. SQL now owns current state." Gate: row counts must match.

**S10 VALIDATE (GATE):** turn_snapshots written for first time.
Full suite: schema + types + nulls + dupes + reconciliation + KPI sanity + assertions + distribution + SQL cross-validation (7 queries). ALL must pass. NB Done = Yes.

**S11 PRESENT:** Streamlit reads intelligence_current + turn_snapshots from turns.db.
Zero DataFrame logic in UI. Zero KPI recalculation.

**S12 AUTOMATE:** Migrate notebook → src/ modules. Pipeline wired. Idempotency verified.
Production Ready = Yes only here.

---

# IV. KPI CONTRACT — 11 REQUIRED FIELDS

Every KPI. All 11. Missing any = do not implement.

1. Name
2. Purpose — what decision does it inform?
3. Formula — plain words
4. Code — exact implementation
5. Units — %, days, count
6. Aggregation grain — per unit / per portfolio / per date
7. Edge-case handling — null, zero, empty subset
8. Validation check — assertion that proves correctness
9. Alternative Grain — how does the story change if aggregated differently?
10. Sensitivity / Outlier Awareness — how does this shift under extreme values?
11. Sample Sufficiency — is sample size adequate for this claim?

**KPI Sanity — all 4 must pass before KPI is published:**
1. Range plausibility
2. Reconciliation (grouped totals match raw count)
3. Subset spot-check (manual verification on 5 rows)
4. Edge-case test (empty subset, extreme values)

---

# V. NOTEBOOK CELL STRUCTURE

**Stage header (once per stage):**
```
## Stage N — STAGE NAME
**Dominant Tool:** [library] | **Output:** [artifact + SQL table] | **Stack:** [libraries]
**Business Question:** "[question]"
**Objective:** [one sentence]
```

**Per-method block (every method, every time):**
```
### Method [#] — [method_name]
[One sentence: what this cell does and what to observe.]

[Code cell: one method only]
```

No code cell without preceding Markdown header. Ever.

---

# VI. STAGE COMPLETION VERIFICATION

Before any stage closes, agent states:
```
Verifying Stage [N] against card:
- [Method 1]: ✅ Locked
- [Method 2]: ✅ Locked
- [SQL Method]: ✅ Locked + Reconciled
All Tier 1 methods complete. Stage [N] complete.
```

---

# VII. VALIDATION SUITE — STAGE 10 (ALL MUST PASS)

1. Schema validation — columns exist, names correct
2. Type validation — numeric/datetime correct
3. Null integrity — no critical nulls
4. Duplicate integrity — no silent dupes
5. Row count reconciliation — all stage counts explainable
6. KPI sanity — all 4 checks, all KPIs
7. Assertion suite — 8+ assertions, none suppressed
8. Distribution plausibility — variance, skew, sample sufficiency
9. SQL cross-validation:
   - SELECT COUNT(*) FROM raw_turns vs stage1_raw shape
   - SELECT COUNT(*) FROM intelligence_current vs stage9 shape
   - WHERE Unit IS NULL → must be 0
   - Duplicate check → must be 0
   - Impossible values check
   - turn_snapshots written confirmation
   - Operational state distribution sanity

---

# VIII. COMPLETION — 27 CRITERIA

**A. Structural (7):** Single-command execution / Notebook complete / Module single-responsibility / Output determinism / Notebook-pipeline match / No exploratory remnants / Folder structure compliance including data/db/

**B. Analytical (8):** Schema / Type / Null / Duplicate / Row count reconciliation / KPI sanity / Assertion suite / Distribution plausibility — all in Python AND SQL

**C. Architectural (9):** UI zero transformation logic / UI zero KPI recalculation / UI reads turns.db only / No cross-module contamination / Class usage compliance / Idempotency verified (all 3 tables) / Performance documented / SQL architecture compliance (3 tables correct ownership) / Pipeline matches notebook

**D. Knowledge (5):** Scope defense / KPI defense / Feature assumption defense / Architecture defense / SQL separation defense:
- "Why does cleaning happen in Python not SQL?"
- "Why does Streamlit read from turns.db instead of a DataFrame?"
- "If you run the pipeline twice what happens to each table?"
- "Why DuckDB instead of a full database server?"

27/27 = Done. Not 26. Not almost. 27.

---

# IX. DISCOVERY DISCIPLINE

Agent does not know the data. Agent discovers alongside user.

NEVER: Assume business domain / Pre-design KPIs / Suggest features before profiling / Use domain terminology user hasn't introduced / Invent column meanings

ALWAYS: Use neutral language ("your dataset", "this column") / Ask before assuming / Profile before designing / Observe before recommending

WRONG: "Your property management data shows turnover cycles."
RIGHT: "Looking at your Status column — let me profile the values first."

---

# X. CONTROLLED COMPLEXITY

Stages 1–11: No abstraction. No helper functions. No classes.
Stage 12: Abstraction only when identical logic appears in 3+ modules AND duplication creates measurable maintenance burden AND extraction does not hide validation logic.

Classes for orchestration only. Never for business logic.
Aesthetic motivation is not justification.
