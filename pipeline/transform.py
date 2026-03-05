"""Transform cleaned data into board-ready DataFrame: DV, DTBR, N/V/M, task dates."""
import numpy as np
import pandas as pd

TODAY = pd.Timestamp.now().normalize()
VERY_OLD = pd.Timestamp("1990-01-01")


def transform(data: dict) -> pd.DataFrame:
    """
    Build board-ready DataFrame: Unit, Status, dates, DV, DTBR, N/V/M, P, B, U, task dates.

    Args:
        data: {"dmrb": DataFrame} from clean_data.

    Returns:
        board_df with formula-equivalent columns computed in pandas.
    """
    if "dmrb" not in data or data["dmrb"].empty:
        return pd.DataFrame()

    df = data["dmrb"].copy()
    today = TODAY

    # DV: days vacant from Move_out to today
    if "Move_out" in df.columns:
        mo = pd.to_datetime(df["Move_out"], errors="coerce")
        df["DV"] = (today - mo).dt.days
    else:
        df["DV"] = pd.NA

    # DTBR: days to be ready (Move_in - today)
    if "Move_in" in df.columns:
        mi = pd.to_datetime(df["Move_in"], errors="coerce")
        df["DTBR"] = (mi - today).dt.days
    else:
        df["DTBR"] = pd.NA

    # N/V/M from dates only (priority order)
    mo = pd.to_datetime(df.get("Move_out"), errors="coerce") if "Move_out" in df.columns else pd.Series(dtype="datetime64[ns]")
    mi = pd.to_datetime(df.get("Move_in"), errors="coerce") if "Move_in" in df.columns else pd.Series(dtype="datetime64[ns]")
    move_in_past = mi.notna() & (mi <= today)
    move_out_past = mo.notna() & (mo <= today)
    move_in_future = mi.notna() & (mi > today)
    move_out_future = mo.notna() & (mo > today)
    move_in_empty_or_old = mi.isna() | (mi < VERY_OLD)

    df["N/V/M"] = np.select(
        [
            move_in_past,
            move_out_past & move_in_future,
            move_out_past & move_in_empty_or_old,
            move_out_future & move_in_future,
            move_out_future & move_in_empty_or_old,
        ],
        ["MOVE IN", "SMI", "VACANT", "NOTICE + SMI", "NOTICE"],
        default="",
    )

    # Task dates: WORKDAY(Move_out, k) for k=1..5
    if "Move_out" in df.columns:
        move_out = pd.to_datetime(df["Move_out"], errors="coerce")
        for i, col in enumerate(["Insp", "Paint", "MR", "HK", "CC"], start=1):
            df[col] = move_out + pd.offsets.BDay(i)
    else:
        for col in ["Insp", "Paint", "MR", "HK", "CC"]:
            df[col] = pd.NaT

    return df
