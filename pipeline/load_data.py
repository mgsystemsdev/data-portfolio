"""Load raw data from data/raw. Primary source: DMRB_board.csv (the DMRB board sheet)."""
from pathlib import Path

import pandas as pd


def load_data(data_root: Path | None = None) -> dict:
    """
    Read DMRB_board.csv and return a dict with cleaned column names and coerced types.

    Args:
        data_root: Directory containing raw files. Defaults to pipeline's sibling data/raw.

    Returns:
        {"dmrb": DataFrame}. If file is missing, returns {"dmrb": pd.DataFrame()}.
    """
    if data_root is None:
        data_root = Path(__file__).resolve().parents[1] / "data" / "raw"

    csv_path = data_root / "DMRB_board.csv"
    if not csv_path.exists():
        return {"dmrb": pd.DataFrame()}

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    # Drop formula-derived columns so downstream uses only raw input/dropdown/text
    formula_cols = ["DV", "DTBR", "N/V/M", "P", "B", "U", "Insp", "Paint", "MR", "HK", "CC"]
    drop = [c for c in formula_cols if c in df.columns]
    if drop:
        df = df.drop(columns=drop)

    if "Unit" in df.columns:
        df["Unit"] = df["Unit"].astype(str).str.strip()
    for col in ("Move_out", "Ready_Date", "Move_in"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return {"dmrb": df}
