##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A13: Whose valence does the model act on? (passage-only span)
##########################################

"""Panel A: whose visit (matched text); Panel B: shared conversation and bystander; Panel C: place vs thoughts vs
feelings. Panels A and B use the passage-only span, each run's pre-registered primary.

Run from the repository root with python3 create_csvs/figureA13.py. Requires numpy.
Reads experiment_results_json/whose_valence/ and writes experiment_results_csv/figureA13.csv.
"""

#=================================
# 1. Setup and configuration
#=================================

from whose_valence_data import FIGURE_COLUMNS, OUT, panel_a_rows, panel_b_rows, panel_c_rows, write_csv

#=================================
# 2. Data preparation
#=================================


def main():
    rows = panel_a_rows("exp") + panel_b_rows("exp") + panel_c_rows()
    write_csv(OUT / "figureA13.csv", rows, FIGURE_COLUMNS)
    print(f"Wrote {len(rows)} rows to experiment_results_csv/figureA13.csv.")

#=================================
# 3. Save figure data
#=================================


if __name__ == "__main__":
    main()
