#!/usr/bin/env python3
##########################################
# AI WELFARE PROJECT
##########################################
# Build all paper figure CSVs
##########################################

#=================================
# 1. Setup and configuration
#=================================

import importlib
from common import OUT


#=================================
# 2. Create the output folder
#=================================

OUT.mkdir(exist_ok=True)

#=================================
# 3. Run the figure scripts in paper order
#=================================

# figure5_tests reads figure5.csv; figure2 (the values drawn in the hand-drawn Figure 2) reads the other
# figure CSVs, so it runs after them. negative_steering_exposure is not a figure: it counts the negative
# steering in each experiment from the JSON records (see the README).
figure_names = [f"figure{i}" for i in range(3, 6)] + [f"figureA{i}" for i in range(1, 15)] + ["figureA5_olmo_per_dose", "figureA6_olmo_per_dose", "figure5_tests", "figure2"]
for name in figure_names + ["negative_steering_exposure"]:
    importlib.import_module(name).main()
print("CSVs created in experiment_results_csv/.")
