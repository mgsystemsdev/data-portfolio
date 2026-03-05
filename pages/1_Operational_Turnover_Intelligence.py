from pathlib import Path

import pandas as pd
import streamlit as st

from pipeline.clean_data import clean_data
from pipeline.enrichment import enrich
from pipeline.load_data import load_data
from pipeline.metrics import compute_metrics
from pipeline.transform import transform

st.title("Operational Turnover Intelligence")

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "raw"


@st.cache_data
def get_pipeline_data():
    """Load → clean → transform → enrich. Returns raw dict, cleaned dict, and board_df."""
    raw = load_data(DATA_ROOT)
    cleaned = clean_data(raw)
    board_df = transform(cleaned)
    board_df = enrich(board_df)
    return {"raw": raw, "cleaned": cleaned, "board_df": board_df}

tab_overview, tab_pipeline, tab_sql, tab_analysis, tab_insights = st.tabs([
    "Overview",
    "Data Pipeline",
    "SQL Logic",
    "Analysis",
    "Insights",
])

# --- Overview ---
with tab_overview:
    st.subheader("Problem Statement")
    st.markdown(
        "As a service manager in apartment communities, I had to coordinate make-ready work across "
        "units and vendors. The main questions were: **Which units are on track vs. stalled?** "
        "**Are our board dates aligned with the property's official reconciliation?** "
        "**Where are the bottlenecks?** This mattered because missed dates cost money and delayed move-ins."
    )

    st.subheader("Skills Demonstrated")
    st.markdown(
        "- **SQL** — Schema design and queries (unit, turnover, task); open-turnover and board views\n"
        "- **Pandas ETL** — Cleaning, merge, and date handling; reconciliation and validation logic\n"
        "- **Data validation** — Reconciliation checks, mismatch flagging, record alignment\n"
        "- **Lifecycle and operational state** — Phase derivation, DV (days vacant), task pipeline status\n"
        "- **Dashboard and visualization** — Task pipeline counts, aging by state, workload crosstabs"
    )

    st.subheader("Dataset Description")
    st.markdown(
        "Data comes from property operations: **Units** (master list), **Move-Outs**, **Available Units**, "
        "**Pending Move Ins**, and the **DMRB board sheet** (make-ready tracking). The property's "
        "**Reconciliation report** is the source of truth for dates and status. The canonical model "
        "uses **unit**, **turnover**, and **task** entities—aligned with the system schema used in "
        "the MakeReady Operational Intelligence application."
    )
    st.caption("Pipeline: Python 3, pandas; run locally with Streamlit (see repo README for `pip install` and `streamlit run`).")

# --- Data Pipeline ---
with tab_pipeline:
    pipeline = get_pipeline_data()
    raw_df = pipeline["raw"].get("dmrb", pd.DataFrame())
    board_df = pipeline["board_df"]

    st.subheader("Raw Data")
    st.markdown(
        "Primary source: **DMRB_board.csv** (the DMRB board sheet). The raw file contains **only input and dropdown columns**: "
        "Unit, Status, Move_out, Ready_Date, Move_in, task status dropdowns (Insp_status, Paint_status, MR_Status, HK_Status, CC_status), "
        "Assign, W_D, QC, Notes. **No formula-derived columns** (DV, DTBR, N/V/M, P, B, U, task dates) — those are computed in the pipeline. "
        "This pipeline backs the **MakeReady Operational Intelligence** system."
    )
    if raw_df.empty:
        st.info("Add **DMRB_board.csv** to `data/raw` to see raw data. You can create it from DMRB_raw.xlsx using `python scripts/export_dmrb_to_csv.py`.")
    else:
        st.dataframe(raw_df, use_container_width=True, height=400)

    st.subheader("Operational pipeline (context)")
    st.markdown(
        "**Data sources in operations:** In the real system, the pipeline used several inputs: "
        "**Units** (master unit list); **Move-Outs** (date the unit was vacated); **Available Units** "
        "(Available Date, Move-In Ready Date); **Pending Move Ins** (scheduled move-in dates); "
        "**Pending FAS** (Final Account Statement — lease end / MO cancel dates used to confirm move-out and update status); "
        "and the **DMRB board** (make-ready tracking: unit, status, dates, task pipeline, assignee, etc.). "
        "In operations the board was an Excel sheet; in this portfolio the same data is provided as **DMRB_board.csv**.\n\n"
        "**Operational pipeline (what was run in operations):** "
        "(1) **Cleanup** — Combine property exports (Available Units, Pending Move Ins, Move-Outs, Pending FAS): "
        "strip and normalize unit codes, restrict to phases 5/7/8, parse dates, merge into a Reconciliation view and other sheets, write Final_Report.xlsx. "
        "(2) **Backfill** — Read Final_Report (Reconciliation sheet) and the board (DMRB); fill blanks in Reconciliation (e.g. Status, Available Date, Move-In Ready Date) from the board; write back to Final_Report. "
        "(3) **Reconciliation check** — Compare Reconciliation to the board on Unit: flag units missing in the board, Available Date or Move In Date differences beyond a tolerance, dates present in Recon but blank on the board; write a mismatch report (e.g. reconciliation_output.xlsx). "
        "Together, cleanup, backfill, and reconciliation check keep the board and the property's official report aligned.\n\n"
        "**What this case study does:** This portfolio does not include the Excel file, the other CSVs, or the scripts that run cleanup, backfill, or reconciliation check. "
        "We use a **snapshot of the board** — **DMRB_board.csv** — and run load → clean → transform → enrich → metrics to reproduce the **same board view** (unit, status, dates, DV, task pipeline, operational state, SLA flags) and show how the board data is structured, without the full operational pipeline or the DMRB Excel."
    )

    st.subheader("Cleaning Steps")
    st.markdown(
        "- **Unit code** — Strip leading/trailing spaces; normalize to canonical phase-building-unit (e.g. 5-18-0206)\n"
        "- **Phase filter** — Restrict to phases 5, 7, 8 for the portfolio scope\n"
        "- **Datetime coercion** — Parse move-out, ready date, move-in as dates; coerce errors to null\n"
        "- **Null handling** — Preserve nulls for missing dates; use in mismatch logic later"
    )

    st.subheader("Transformation Logic")
    st.markdown(
        "The pipeline has three stages:\n\n"
        "**Clean**\n"
        "- Derives **phase** and **P, B, U** (phase, building, unit number) from Unit by splitting on hyphen.\n\n"
        "**Transform**\n"
        "- Adds **DV** (days vacant) from Move_out to today.\n"
        "- Adds **DTBR** (days to move-in) from today to Move_in.\n"
        "- Adds **N/V/M** (lifecycle stage: MOVE IN, SMI, VACANT, NOTICE + SMI, NOTICE) from dates only.\n"
        "- Adds **task dates** (Insp, Paint, MR, HK, CC) via business-day offsets from Move_out (1–5 business days).\n\n"
        "**Enrichment**\n"
        "- Adds **Aging_Business_Days** (business days from Move_out to today).\n"
        "- Adds **Task_State** (All Tasks Complete / Not Started / In Progress) and **Task_Completion_Ratio** (0–100%).\n"
        "- Adds **Table_Current_Task** and **Table_Next_Task** (next step in the pipeline).\n"
        "- Adds **Is_Task_Stalled** (unit vacant, task not done, past SLA window).\n"
        "- Adds **Operational_State** (On Notice, Move-In Risk, QC Hold, Work Stalled, In Progress, Pending Start, Apartment Ready, Out of Scope).\n"
        "- Adds **Is_Unit_Ready** and unit-ready-for-moving logic.\n"
        "- Adds **SLA breach flags**: inspection (within 1 biz day), turn (ready within 10 biz days), move-in, and plan breach."
    )

    st.subheader("Processed Dataset")
    st.markdown(
        "The **board-ready dataset** includes: Unit, Status, dates, DV, DTBR, N/V/M, P, B, U, task dates and status columns, "
        "plus enrichment columns (Aging_Business_Days, Task_State, Task_Completion_Ratio, Table_Current_Task, Table_Next_Task, "
        "Is_Task_Stalled, Operational_State, Is_Unit_Ready, and SLA breach flags). This feeds the MakeReady Operational Intelligence "
        "board and analytics."
    )
    if board_df.empty:
        st.info("Run the pipeline with **DMRB_board.csv** in `data/raw` to see the processed dataset.")
    else:
        st.dataframe(board_df, use_container_width=True, height=400)

    st.subheader("Data quality")
    if raw_df.empty and board_df.empty:
        st.caption("Add **DMRB_board.csv** to `data/raw` to see quality checks.")
    else:
        raw_n = len(raw_df)
        clean_n = len(board_df)
        st.markdown(f"- **Raw row count:** {raw_n}")
        st.markdown(f"- **Rows after clean** (phase filter): {clean_n}")
        if not board_df.empty:
            if "Move_in" in board_df.columns:
                missing_mi = int(board_df["Move_in"].isna().sum())
                st.markdown(f"- **Units with missing Move_in:** {missing_mi}")
            if "Move_out" in board_df.columns:
                mo = pd.to_datetime(board_df["Move_out"], errors="coerce")
                valid = mo.dropna()
                if len(valid) > 0:
                    st.markdown(f"- **Move_out date range:** {valid.min().strftime('%Y-%m-%d')} to {valid.max().strftime('%Y-%m-%d')}")
        st.caption("In production, reconciliation compared this board to the property report; here we show basic quality checks on the board snapshot.")

# --- SQL Logic ---
with tab_sql:
    st.subheader("Key Query")
    st.code(
        "-- Open turnovers with unit and task info (canonical schema)\n"
        "SELECT\n"
        "    u.unit_code_norm AS unit,\n"
        "    t.move_out_date,\n"
        "    t.move_in_date,\n"
        "    t.manual_ready_status AS status,\n"
        "    tk.task_type,\n"
        "    tk.execution_status\n"
        "FROM turnover t\n"
        "JOIN unit u ON u.unit_id = t.unit_id\n"
        "LEFT JOIN task tk ON tk.turnover_id = t.turnover_id\n"
        "WHERE t.closed_at IS NULL AND t.canceled_at IS NULL\n"
        "ORDER BY t.move_out_date, u.unit_code_norm, tk.task_type;",
        language="sql",
    )

    st.subheader("Explanation")
    st.markdown(
        "This query returns **open turnovers** (not closed or canceled) with unit code, key dates, "
        "manual ready status, and each task's type and execution status. It powers the board view "
        "and ensures we only work with active make-ready cycles. The LEFT JOIN to task allows units "
        "with no tasks yet to still appear."
    )

    st.subheader("Query Output")
    sample_output = [
        {"unit": "5-18-0206", "move_out_date": "2025-01-31", "move_in_date": "2026-02-27", "status": "Vacant not ready", "task_type": "Insp", "execution_status": "VENDOR_COMPLETED"},
        {"unit": "5-18-0206", "move_out_date": "2025-01-31", "move_in_date": "2026-02-27", "status": "Vacant not ready", "task_type": "Paint", "execution_status": "IN_PROGRESS"},
        {"unit": "7-02-0302", "move_out_date": "2025-01-02", "move_in_date": None, "status": "Vacant ready", "task_type": "CC", "execution_status": "VENDOR_COMPLETED"},
        {"unit": "8-01-4058", "move_out_date": "2025-01-18", "move_in_date": "2026-02-18", "status": "Vacant ready", "task_type": "MR", "execution_status": "VENDOR_COMPLETED"},
    ]
    st.dataframe(pd.DataFrame(sample_output), use_container_width=True)

# --- Analysis ---
with tab_analysis:
    pipeline = get_pipeline_data()
    board_df = pipeline["board_df"]
    metrics = compute_metrics(board_df)

    st.subheader("KPI Metrics")
    if board_df.empty:
        st.info("Add **DMRB_board.csv** to `data/raw` and run the pipeline to see metrics.")
    else:
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Units (open turnover)", metrics["units_total"], "by operational state")
        with m2:
            avg_dv = metrics["avg_dv"]
            st.metric("Avg days vacant (DV)", f"{avg_dv:.1f}" if avg_dv is not None else "—", "across units")
        with m3:
            st.metric("Stalled units", metrics["stalled_count"], "task not progressing")
        with m4:
            st.metric("Inspection SLA breach", metrics["inspection_sla_breach_count"], "inspection > 1 biz day")
        with m5:
            st.metric("Turn SLA breach", metrics["sla_breach_count"], "not ready after 10 biz days")

        avg_pct = metrics.get("avg_completion_pct")
        if avg_pct is not None:
            st.metric("Avg task completion %", f"{avg_pct:.0f}%", "across units")

        if not metrics["by_status"].empty:
            st.subheader("Units by Status")
            st.dataframe(metrics["by_status"], use_container_width=True)

        if not metrics.get("by_operational_state", pd.DataFrame()).empty:
            st.subheader("Units by Operational State")
            st.dataframe(metrics["by_operational_state"], use_container_width=True)

        if not metrics.get("by_assignee", pd.DataFrame()).empty:
            st.subheader("Units by Assignee")
            st.dataframe(metrics["by_assignee"], use_container_width=True)
            chart_assignee = metrics["by_assignee"].set_index("Assignee")
            st.bar_chart(chart_assignee)

        if not metrics.get("aging_by_state", pd.DataFrame()).empty:
            st.subheader("Aging by operational state")
            st.dataframe(metrics["aging_by_state"], use_container_width=True)

    st.subheader("Visualizations")
    st.markdown(
        "In the full system, **task pipeline counts** (Insp, Paint, MR, HK, CC by status), "
        "**aging by operational state** (avg/max DV), and **workload crosstabs** are built from the processed dataset."
    )
    if metrics.get("task_pipeline_counts") is not None and not metrics["task_pipeline_counts"].empty:
        st.dataframe(metrics["task_pipeline_counts"], use_container_width=True)
        task_counts = metrics["task_pipeline_counts"]
        task_pivot = task_counts.pivot(index="Task", columns="Status", values="count").fillna(0)
        st.bar_chart(task_pivot)
    else:
        st.caption("Task columns (Insp, Paint, MR, HK, CC) in DMRB_board.csv will show pipeline counts here.")
        task_counts = pd.DataFrame([
            {"Task": "Insp", "Done": 42, "In Progress": 3, "Scheduled": 2},
            {"Task": "Paint", "Done": 38, "In Progress": 5, "Scheduled": 4},
            {"Task": "MR", "Done": 35, "In Progress": 6, "Scheduled": 6},
            {"Task": "HK", "Done": 32, "In Progress": 7, "Scheduled": 8},
            {"Task": "CC", "Done": 28, "In Progress": 4, "Scheduled": 15},
        ])
        st.dataframe(task_counts.set_index("Task"), use_container_width=True)
    if not metrics.get("by_operational_state", pd.DataFrame()).empty:
        st.caption("Units by operational state")
        chart_state = metrics["by_operational_state"].set_index("Operational_State")
        st.bar_chart(chart_state)

    st.subheader("Trend Analysis")
    st.markdown(
        "Aging by operational state shows where units stall (e.g. units stuck in Paint or MR). "
        "Reconciliation highlights date drift between the property's report and the board—units "
        "missing in DMRB or with avail/move-in date mismatches need correction first so the board "
        "stays the single source of truth."
    )

# --- Insights ---
with tab_insights:
    st.subheader("Key Findings")
    st.markdown(
        "- **Reconciliation** catches units missing in the board and date mismatches (available date, move-in) so the board and property report stay aligned.\n"
        "- **Aging by operational state** reveals where units stall (e.g. Insp/Paint/MR) and need attention.\n"
        "- **Assignee workload** is visible in crosstabs so load can be balanced.\n"
        "- A **single source of truth** (board + reconciled dates) reduces confusion and duplicate tracking.\n"
        "- **Stall tracker** surfaces units with tasks not progressing for follow-up."
    )

    st.subheader("Operational Impact")
    st.markdown(
        "The MakeReady Operational Intelligence system became the single source of truth for make-ready "
        "coordination. Reporting turnaround improved by **~50%**; the board was adopted by **20+ users**. "
        "Reconciliation and pipeline design turned operational complexity into structured, audit-ready data."
    )

    st.subheader("Recommendations")
    st.markdown(
        "- Run **reconciliation regularly** (e.g. after each import or board update) to flag mismatches early.\n"
        "- **Fix units \"missing in DMRB\"** first, then resolve date differences so the board stays complete."
    )
