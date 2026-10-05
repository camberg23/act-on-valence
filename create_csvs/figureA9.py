##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A9: Effect of the number of exposures
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, load_json, label, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    analysis = load_json(JSONS / "fixed_text_design/exposure_sweep/analysis.json")
    rows = []
    for model, member in analysis["members"].items():
        for stat in member["under_none"]["exposure_curve"]:
            low, high = stat["ci95_matched"]
            for series, estimate, lo, hi in (
                ("valenced", stat["slope_matched"], low, high),
                ("largest_random_direction", stat["floor_max"], None, None),
            ):
                rows.append({"model_id": model, "model": label(model), "n_exposures": stat["n_exposures"],
                             "series": series, "estimate": estimate, "ci_low": lo, "ci_high": hi,
                             "sample": "matched_skeletons_ungated"})
    write_csv("figureA9.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
