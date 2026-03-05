"""Compute metrics from board-ready DataFrame for the Analysis tab."""
import pandas as pd

STATUS_COLS = ["Insp_status", "Paint_status", "MR_Status", "HK_Status", "CC_status"]
TASK_NAMES = ["Insp", "Paint", "MR", "HK", "CC"]


def compute_metrics(board_df: pd.DataFrame) -> dict:
    """
    Compute units_total, avg_dv, by_status, task_pipeline_counts, and enrichment-based metrics.

    Args:
        board_df: DataFrame from transform + enrichment (Unit, DV, Status, enrichment cols).

    Returns:
        dict with units_total, avg_dv, by_status, task_pipeline_counts, stalled_count,
        avg_completion_pct, by_operational_state, by_assignee, aging_by_state,
        sla_breach counts.
    """
    if board_df is None or board_df.empty:
        return {
            "units_total": 0,
            "avg_dv": None,
            "by_status": pd.DataFrame(),
            "task_pipeline_counts": None,
            "stalled_count": 0,
            "avg_completion_pct": None,
            "by_operational_state": pd.DataFrame(),
            "by_assignee": pd.DataFrame(),
            "aging_by_state": pd.DataFrame(),
            "inspection_sla_breach_count": 0,
            "sla_breach_count": 0,
        }

    units_total = board_df["Unit"].notna().sum() if "Unit" in board_df.columns else len(board_df)

    avg_dv = None
    if "DV" in board_df.columns:
        valid = board_df["DV"].dropna()
        avg_dv = float(valid.mean()) if len(valid) > 0 else None

    by_status = pd.DataFrame()
    if "Status" in board_df.columns:
        by_status = board_df["Status"].value_counts().reset_index()
        by_status.columns = ["Status", "count"]

    # Task pipeline counts from status columns (Done, In Progress, Scheduled, Not Started)
    task_pipeline_counts = None
    status_cols_present = [c for c in STATUS_COLS if c in board_df.columns]
    if status_cols_present:
        rows = []
        for i, col in enumerate(status_cols_present):
            task_name = TASK_NAMES[i] if i < len(TASK_NAMES) else col
            counts = board_df[col].value_counts()
            for val, n in counts.items():
                rows.append({"Task": task_name, "Status": str(val), "count": int(n)})
        task_pipeline_counts = pd.DataFrame(rows) if rows else None

    # Enrichment-based metrics
    stalled_count = int(board_df["Is_Task_Stalled"].sum()) if "Is_Task_Stalled" in board_df.columns else 0
    avg_completion_pct = None
    if "Task_Completion_Ratio" in board_df.columns:
        v = board_df["Task_Completion_Ratio"].dropna()
        avg_completion_pct = float(v.mean()) if len(v) > 0 else None
    by_operational_state = pd.DataFrame()
    if "Operational_State" in board_df.columns:
        by_operational_state = board_df["Operational_State"].value_counts().reset_index()
        by_operational_state.columns = ["Operational_State", "count"]

    # Assignee workload: count units per Assign; normalize blank to "Unassigned"
    by_assignee = pd.DataFrame()
    if "Assign" in board_df.columns:
        assign_series = board_df["Assign"].fillna("").astype(str).str.strip()
        assign_series = assign_series.replace("", "Unassigned")
        by_assignee = assign_series.value_counts().reset_index()
        by_assignee.columns = ["Assignee", "count"]

    # Aging by operational state: avg and max DV (or Aging_Business_Days) per state
    aging_by_state = pd.DataFrame()
    if "Operational_State" in board_df.columns:
        aging_col = "Aging_Business_Days" if "Aging_Business_Days" in board_df.columns else "DV"
        if aging_col in board_df.columns:
            aging_by_state = (
                board_df.groupby("Operational_State", dropna=False)[aging_col]
                .agg(["mean", "max"])
                .round(1)
                .reset_index()
            )
            aging_by_state.columns = ["Operational_State", "avg_dv", "max_dv"]

    inspection_sla_breach_count = int(board_df["Inspection_SLA_Breach"].sum()) if "Inspection_SLA_Breach" in board_df.columns else 0
    sla_breach_count = int(board_df["SLA_Breach"].sum()) if "SLA_Breach" in board_df.columns else 0

    return {
        "units_total": int(units_total),
        "avg_dv": avg_dv,
        "by_status": by_status,
        "task_pipeline_counts": task_pipeline_counts,
        "stalled_count": stalled_count,
        "avg_completion_pct": avg_completion_pct,
        "by_operational_state": by_operational_state,
        "by_assignee": by_assignee,
        "aging_by_state": aging_by_state,
        "inspection_sla_breach_count": inspection_sla_breach_count,
        "sla_breach_count": sla_breach_count,
    }
