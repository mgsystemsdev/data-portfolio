"""
Produce raw-only DMRB_board.csv: keep only input/dropdown/text columns; drop formula-derived.
Usage: python data-portfolio/scripts/slim_dmrb_csv.py [input_csv] [output_csv]
Defaults: data-portfolio/data/raw/DMRB_board.csv in and out.
"""
import sys
from pathlib import Path

import pandas as pd

# Columns to keep (canonical raw schema)
KEEP_COLUMNS = [
    "Unit", "Status", "Move_out", "Ready_Date", "Move_in",
    "Insp_status", "Paint_status", "MR_Status", "HK_Status", "CC_status",
    "Assign", "W_D", "QC", "Notes",
]

SCRIPT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV = SCRIPT_DIR / "data" / "raw" / "DMRB_board.csv"


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else src

    if not src.exists():
        print(f"Source not found: {src}")
        sys.exit(1)

    df = pd.read_csv(src)
    df.columns = df.columns.str.strip()

    existing = [c for c in KEEP_COLUMNS if c in df.columns]
    out = df[existing].copy()
    out.to_csv(dest, index=False)
    print(f"Slimmed to {len(existing)} columns, {len(out)} rows → {dest}")


if __name__ == "__main__":
    main()
