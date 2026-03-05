"""
One-off: Export DMRB board sheet from DMRB_raw.xlsx to data/raw/DMRB_board.csv.
Run from repo root: python data-portfolio/scripts/export_dmrb_to_csv.py
Or with custom paths: python data-portfolio/scripts/export_dmrb_to_csv.py <xlsx_path> <csv_path>
"""
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SRC = REPO_ROOT / "refecerence_context" / "Reports" / "data" / "DMRB_raw.xlsx"
DEFAULT_DEST = Path(__file__).resolve().parents[1] / "data" / "raw" / "DMRB_board.csv"


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DEST

    if not src.exists():
        print(f"Source not found: {src}")
        print("Usage: python export_dmrb_to_csv.py [xlsx_path] [csv_path]")
        sys.exit(1)

    dest.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(src, sheet_name="DMRB ")
    df.columns = df.columns.str.strip()
    df.to_csv(dest, index=False)
    print(f"Exported {len(df)} rows to {dest}")


if __name__ == "__main__":
    main()
