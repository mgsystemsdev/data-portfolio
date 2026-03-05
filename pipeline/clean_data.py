"""Clean loaded data: strip Unit, derive phase, filter phases 5/7/8, ensure datetimes."""
import pandas as pd


def clean_data(data: dict) -> dict:
    """
    Clean the dict from load_data. Strip Unit, derive phase, optional phase filter, coerce dates.

    Args:
        data: {"dmrb": DataFrame} from load_data.

    Returns:
        Same structure with cleaned DataFrames.
    """
    if "dmrb" not in data or data["dmrb"].empty:
        return {"dmrb": pd.DataFrame()}

    df = data["dmrb"].copy()

    if "Unit" in df.columns:
        df["Unit"] = df["Unit"].astype(str).str.strip()

    # Normalize "Unit 5-18-0206" -> "5-18-0206" so phase derivation works
    unit_str = df["Unit"].str.replace("Unit ", "", regex=False)
    df["Unit"] = unit_str
    # Derive phase (P), building (B), unit number (U) from segments
    parts = unit_str.str.split("-")
    df["phase"] = pd.to_numeric(parts.str[0], errors="coerce")
    df["P"] = pd.to_numeric(parts.str[0], errors="coerce")
    df["B"] = parts.str[1]
    df["U"] = parts.str[-1]

    # Optional phase filter: 5, 7, 8
    df = df[df["phase"].isin([5, 7, 8])].copy()

    for col in ("Move_out", "Ready_Date", "Move_in"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return {"dmrb": df.reset_index(drop=True)}
