##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A10: Concentration and strength of injection
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, load_json, label, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    original = load_json(JSONS / "fixed_text_design/strength_ladder/analysis.json")
    extension = load_json(JSONS / "fixed_text_design/strength_ladder_extension/analysis.json")
    conditions = {"e1_k1": "one_sighting_full_strength", "e6_ksixth": "six_sightings_one_sixth_strength"}
    rows = []
    for model, member in original["members"].items():
        for stat in member["under_none"]["row_total"]:
            if stat["arm"] in conditions:
                low, high = stat["ci95_full_n"]
                rows.append({"panel": "constant_total_comparison", "model_id": model, "model": label(model),
                             "condition": conditions[stat["arm"]], "strength": stat["k"],
                             "estimate": stat["slope_full_n"], "ci_low": low, "ci_high": high,
                             "sample": "all_recorded_ungated"})
    for model, member in extension["members"].items():
        if model not in ("olmo_32b", "qwen3_14b", "llama31_8b"):
            continue
        for stat in member["under_none"]["ladder"]:
            low, high = stat["ci95"]
            rows.append({"panel": "six_sighting_strength_ladder", "model_id": model, "model": label(model),
                         "condition": stat["arm"], "strength": stat["k"], "estimate": stat["slope"],
                         "ci_low": low, "ci_high": high, "sample": "all_recorded_ungated"})
    write_csv("figureA10.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
