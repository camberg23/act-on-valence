#!/usr/bin/env python3
##########################################
# AI WELFARE PROJECT
##########################################
# Build all paper table CSVs
##########################################

#=================================
# 1. Setup and configuration
#=================================

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "create_csvs"))

from common import OUT

#=================================
# 2. Create the output folder
#=================================

OUT.mkdir(exist_ok=True)

#=================================
# 3. Run the table scripts in paper order
#=================================

for name in ("table1", "tableA1", "tableA2", "tableA3"):
    importlib.import_module(name).main()
print("Table CSVs created in experiment_results_csv/.")
