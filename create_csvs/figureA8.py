##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A8: Injected span
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, load_json, label, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    analysis = load_json(JSONS / "fixed_text_design/span_sweep/analysis.json")
    rows = []
    for model, member in analysis["members"].items():
        for stat in member["under_none"]["span_curve"]:
            low, high = stat["ci95_full_n"]
            floor = [d["slope"] for d in member["under_none"]["arms"][stat["arm"]]["floor"]["detail"].values()]
            assert abs(max(floor) - stat["floor_max"]) < 1e-9
            largest = max(abs(slope) for slope in floor)
            rows.append({"model_id": model, "model": label(model), "span": stat["arm"],
                         "estimate": stat["slope_full_n"], "ci_low": low, "ci_high": high,
                         "n_sessions": stat["n_sessions_full_n"], "largest_abs_random_slope": largest,
                         "clears_random_floor": stat["slope_full_n"] > largest,
                         "steered_span_tokens": stat["steered_span_tokens"], "sample": "all_recorded_ungated"})
    write_csv("figureA8.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
