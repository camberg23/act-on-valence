##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A4: Original, opposite-steered and random-steered caches
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, load_json, label, ci, dose_number, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    data = load_json(JSONS / "generation_design/seven_models/analysis.json")
    curves = []
    series = {
        "d_margin_state": "natural_minus_clean",
        "d_margin_tf": "matched_minus_clean",
        "d_margin_opposite": "opposite_minus_clean",
        "d_margin_random": "random_minus_clean",
    }
    for model_id, member in data["members"].items():
        reading = member["under_none"]
        doses_seen = set()
        for dose_key, point in reading["valenced_curve"].items():
            doses_seen.add(dose_number(dose_key))
            for source_key, series_label in series.items():
                stat = point[source_key]
                lo, hi = ci(stat)
                curves.append({
                    "experiment": 254,
                    "model_id": model_id,
                    "model": label(model_id),
                    "dose": dose_number(dose_key),
                    "series": series_label,
                    "estimate": stat.get("mean"),
                    "ci_low": lo,
                    "ci_high": hi,
                    "n_sessions": stat.get("n"),
                    "sample": "all_recorded_ungated",
                })
        if 0.0 not in doses_seen:
            n_sessions = next(iter(reading["valenced_curve"].values())).get("n_sessions")
            for series_label in series.values():
                curves.append({
                    "experiment": 254,
                    "model_id": model_id,
                    "model": label(model_id),
                    "dose": 0.0,
                    "series": series_label,
                    "estimate": 0.0,
                    "ci_low": 0.0,
                    "ci_high": 0.0,
                    "n_sessions": n_sessions,
                    "sample": "all_recorded_ungated",
                })
    write_csv("figureA4.csv", curves)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
