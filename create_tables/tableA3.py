##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Table A3: Cosine similarities between OLMo valence vectors
##########################################

#=================================
# 1. Setup and configuration
#=================================

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "create_csvs"))

from common import OUT, write_csv

STAGES = [("Base", "stage_base"), ("SFT", "stage_sft"), ("DPO", "stage_dpo"),
          ("Instruct", "stage_instruct")]

#=================================
# 2. Precomputed cosine similarities
#=================================

# The steering vectors are not distributed. tableA3_cosines.csv holds the cosine similarity of
# each pair of stage valence vectors (positive pole minus negative pole of each stage's
# route-B bank at layer 32), computed with correctly rounded sums before the vectors were removed.
COSINES = OUT / "tableA3_cosines.csv"

#=================================
# 3. Data preparation
#=================================

def main():
    with COSINES.open(newline="", encoding="utf-8") as handle:
        recorded = {(r["row"], r["column"]): r for r in csv.DictReader(handle)}
    if {int(r["layer"]) for r in recorded.values()} != {32}:
        raise ValueError("All OLMo stage vectors should be constructed at layer 32")
    rows = []
    for i, (row_name, row_bank) in enumerate(STAGES):
        for column_name, column_bank in STAGES[: i + 1]:
            value = float(recorded[(row_name, column_name)]["cosine"])
            rows.append({
                "row": row_name, "column": column_name, "cosine": value,
                "cosine_label": f"{value:.5f}", "layer": 32,
                "row_source": f"tableA3_cosines.csv ({row_bank})",
                "column_source": f"tableA3_cosines.csv ({column_bank})",
            })
    write_csv("tableA3.csv", rows)

#=================================
# 4. Save table data
#=================================

if __name__ == "__main__":
    main()
