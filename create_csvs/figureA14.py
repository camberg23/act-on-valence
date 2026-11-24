##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A14: Whose valence, whole-turn span (Panels A and B of Figure A13)
##########################################

"""Panels A and B of Figure A13 with the whole-turn span: the steering also covers the user turn, whose wording
differs between conditions.

Run from the repository root with python3 create_csvs/figureA14.py. Requires numpy.
Reads experiment_results_json/whose_valence/ and writes experiment_results_csv/figureA14.csv.
"""

#=================================
# 1. Setup and configuration
#=================================

from whose_valence_data import FIGURE_COLUMNS, OUT, panel_a_rows, panel_b_rows, write_csv

#=================================
# 2. Data preparation
#=================================


def main():
    rows = panel_a_rows("whole") + panel_b_rows("whole")
    write_csv(OUT / "figureA14.csv", rows, FIGURE_COLUMNS)
    print(f"Wrote {len(rows)} rows to experiment_results_csv/figureA14.csv.")

#=================================
# 3. Save figure data
#=================================


if __name__ == "__main__":
    main()
