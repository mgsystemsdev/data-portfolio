"""Enrichment layer: business-day aging, task state, operational state, stall detection, SLA flags."""
import numpy as np
import pandas as pd
from datetime import date

TASK_SEQUENCE = ["Inspection", "Paint", "MR", "HK", "CC"]
STATUS_COLS = ["Insp_status", "Paint_status", "MR_Status", "HK_Status", "CC_status"]
# Task name -> (status_col, SLA business days)
TASK_SLA_DAYS = {"Inspection": 1, "Paint": 2, "MR": 3, "HK": 6, "CC": 7}
INSPECTION_SLA_DAYS = 1
TURN_SLA_DAYS = 10
MOVE_IN_BUFFER_DAYS = 2


def _business_days(start_series: pd.Series, end_date: date) -> pd.Series:
    """Business days from each start date to end_date."""
    out = pd.Series(index=start_series.index, dtype=float)
    start_series = pd.to_datetime(start_series, errors="coerce")
    for i in start_series.index:
        s = start_series.loc[i]
        if pd.isna(s):
            out.loc[i] = np.nan
        else:
            try:
                out.loc[i] = np.busday_count(s.date(), end_date)
            except Exception:
                out.loc[i] = np.nan
    return out


def _normalize_status(s: pd.Series) -> pd.Series:
    """Blank/NaN -> Not Started; then title case."""
    out = s.fillna("").astype(str).str.strip()
    out = out.replace("", "Not Started").str.title()
    return out


def enrich(board_df: pd.DataFrame, today: date | None = None) -> pd.DataFrame:
    """
    Add Tier 1 and Tier 2 derived columns for case study strength.

    Input: board_df from transform (Unit, Status, dates, DV, DTBR, N/V/M, P, B, U, task dates, status cols).
    Output: same DataFrame with Aging_Business_Days, Task_State, Task_Completion_Ratio,
    Table_Current_Task, Table_Next_Task, Is_Task_Stalled, Operational_State, Is_Unit_Ready,
    Is_Unit_Ready_For_Moving, Days_To_MoveIn, SLA flags, etc.
    """
    if board_df is None or board_df.empty:
        return board_df

    today = today or date.today()
    df = board_df.copy()

    # ----- Helpers from N/V/M and others -----
    nvm = df.get("N/V/M", pd.Series(dtype=object)).fillna("").astype(str).str.strip().str.upper()
    df["Is_Vacant"] = nvm.eq("VACANT")
    df["Is_SMI"] = nvm.str.contains("SMI|MOVE IN", regex=True, na=False)
    df["Is_On_Notice"] = nvm.str.contains("NOTICE", na=False)
    df["Is_MoveIn_Present"] = df["Move_in"].notna() if "Move_in" in df.columns else False
    df["Is_QC_Done"] = df["QC"].fillna("").astype(str).str.strip().str.upper().eq("DONE") if "QC" in df.columns else False

    # ----- Aging_Business_Days -----
    if "Move_out" in df.columns:
        df["Aging_Business_Days"] = _business_days(df["Move_out"], today)
    else:
        df["Aging_Business_Days"] = np.nan

    # ----- Normalize status columns -----
    for col in STATUS_COLS:
        if col in df.columns:
            df[col] = _normalize_status(df[col])

    # ----- Task_State, Task_Completion_Ratio -----
    status_cols_present = [c for c in STATUS_COLS if c in df.columns]
    if status_cols_present:
        done_count = df[status_cols_present].apply(lambda x: x.str.upper().eq("DONE").sum(), axis=1)
        not_started_count = df[status_cols_present].apply(lambda x: x.str.upper().eq("NOT STARTED").sum(), axis=1)
        n = len(status_cols_present)
        df["Task_Completion_Ratio"] = (done_count / n * 100).round(0)
        df["Task_State"] = np.select(
            [done_count == n, not_started_count == n],
            ["All Tasks Complete", "Not Started"],
            default="In Progress",
        )
    else:
        df["Task_Completion_Ratio"] = 0
        df["Task_State"] = "Not Started"

    # ----- Table_Current_Task, Table_Next_Task -----
    def first_not_done(row):
        for i, task in enumerate(TASK_SEQUENCE):
            col = STATUS_COLS[i] if i < len(STATUS_COLS) else None
            if col and col in row.index and str(row[col]).upper() != "DONE":
                return i, task
        return len(TASK_SEQUENCE), ""

    cur_next = df.apply(
        lambda row: first_not_done(row),
        axis=1,
        result_type="expand",
    )
    cur_next.columns = ["_cur_idx", "_cur_name"]
    df["Table_Current_Task"] = cur_next["_cur_name"]
    next_idx = cur_next["_cur_idx"].add(1)
    df["Table_Next_Task"] = next_idx.apply(
        lambda i: TASK_SEQUENCE[int(i)] if pd.notna(i) and 0 <= int(i) < len(TASK_SEQUENCE) else ""
    )

    # ----- Is_Task_Stalled -----
    stall_series = pd.Series(False, index=df.index)
    for i, task in enumerate(TASK_SEQUENCE):
        col = STATUS_COLS[i] if i < len(STATUS_COLS) else None
        if not col or col not in df.columns:
            continue
        sla_days = TASK_SLA_DAYS.get(task, 7)
        stall_series = stall_series | (
            df["Is_Vacant"]
            & ~df[col].str.upper().eq("DONE")
            & (df["Aging_Business_Days"] > sla_days)
        )
    df["Is_Task_Stalled"] = stall_series

    # ----- Is_Unit_Ready -----
    status_ready = df["Status"].fillna("").astype(str).str.strip().str.upper().eq("VACANT READY") if "Status" in df.columns else False
    df["Is_Unit_Ready"] = status_ready & (df["Task_State"] == "All Tasks Complete")

    # ----- Tier 2: Is_Unit_Ready_For_Moving, Days_To_MoveIn -----
    df["Days_To_MoveIn"] = np.nan
    if "Move_in" in df.columns:
        mi = pd.to_datetime(df["Move_in"], errors="coerce")
        df["Days_To_MoveIn"] = (mi - pd.Timestamp(today)).dt.days
    df["Is_Unit_Ready_For_Moving"] = df["Is_Unit_Ready"] & df["Is_MoveIn_Present"] & df["Is_QC_Done"]

    # ----- Operational_State -----
    def _operational_state(row):
        if row["Is_On_Notice"]:
            return "On Notice - Scheduled" if row["Is_SMI"] else "On Notice"
        if not (row["Is_Vacant"] or row["Is_SMI"]):
            return "Out of Scope"
        if row["Is_MoveIn_Present"] and not row["Is_Unit_Ready_For_Moving"] and row["Is_Vacant"] and not row["Is_Unit_Ready"]:
            return "Move-In Risk"
        if row["Is_Unit_Ready"] and row["Is_MoveIn_Present"] and not row["Is_QC_Done"]:
            return "QC Hold"
        if row["Is_Task_Stalled"]:
            return "Work Stalled"
        if row["Task_State"] == "In Progress":
            return "In Progress"
        if row["Is_Unit_Ready"]:
            return "Apartment Ready"
        return "Pending Start"

    df["Operational_State"] = df.apply(_operational_state, axis=1)

    # ----- SLA flags -----
    insp_upper = df["Insp_status"].str.upper() if "Insp_status" in df.columns else pd.Series("", index=df.index)
    df["Inspection_SLA_Breach"] = (
        df["Is_Vacant"]
        & (insp_upper != "DONE")
        & (df["Aging_Business_Days"] > INSPECTION_SLA_DAYS)
    )
    df["SLA_Breach"] = (
        df["Is_Vacant"]
        & ~df["Is_Unit_Ready"]
        & (df["Aging_Business_Days"] > TURN_SLA_DAYS)
    )
    df["SLA_MoveIn_Breach"] = (
        df["Is_MoveIn_Present"]
        & ~df["Is_Unit_Ready_For_Moving"]
        & (df["Days_To_MoveIn"] >= 0)
        & (df["Days_To_MoveIn"] <= MOVE_IN_BUFFER_DAYS)
    )
    is_ready_declared = df["Ready_Date"].notna() if "Ready_Date" in df.columns else False
    today_ts = pd.Timestamp(today)
    past_ready = is_ready_declared & (pd.to_datetime(df["Ready_Date"], errors="coerce") <= today_ts)
    df["Plan_Breach"] = past_ready & ~df["Is_Unit_Ready"]

    return df
