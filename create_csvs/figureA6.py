##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A6: Best-passage and first-passage recall
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, MODEL_LABELS, load_json, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    """Export the supplied recall summaries without rescoring or filtering observations."""
    source = JSONS / "fixed_text_design/recall/analysis.json"
    analysis = load_json(source)
    members = analysis["members"]
    if set(members) != set(MODEL_LABELS):
        raise ValueError("Recall analysis must contain all seven models")

    rows = []
    for model_id, model in MODEL_LABELS.items():
        member = members[model_id]
        if set(member["random"]) != {str(k) for k in range(24)}:
            raise ValueError(f"Expected 24 recall control directions for {model_id}")
        for metric in ("fid", "best_fid"):
            for zone in ("S", "U"):
                for dose in (-1.0, -0.5, 0.0, 0.5, 1.0):
                    stat = member["rates_by_dose"][zone][f"{dose:+.1f}"]
                    low, high = stat[f"{metric}_ci95"]
                    rows.append({
                        "model_id": model_id, "model": model, "metric": metric,
                        "zone": zone, "series": zone, "direction": "valence",
                        "dose": dose, "estimate": stat[f"{metric}_mean"],
                        "ci_low": low, "ci_high": high, "n_sessions": stat["n"],
                        "sample": "all_recorded_ungated",
                        "ci_method": "supplied_absolute_mean_skeleton_bootstrap",
                    })

    write_csv("figureA6.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
