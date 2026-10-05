##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A5: Continue and avoid prompts
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, MODEL_LABELS, load_json, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    analysis = load_json(JSONS / "fixed_text_design/avoid_prompt/analysis.json")["avoid"]["members"]
    rows = []
    for model in MODEL_LABELS:
        curves = analysis[model]["curves"]
        for prompt in ("continue", "avoid"):
            series = dict(curves[f"{prompt}_random_matched"])
            series["valence"] = curves[f"{prompt}_valence_matched"]
            for direction, curve in series.items():
                for dose in (-1.0, -0.5, 0.0, 0.5, 1.0):
                    stat = curve[f"{dose:+.1f}"]
                    low, high = stat["ci95"] if direction == "valence" else (None, None)
                    rows.append({"member": model, "prompt": prompt, "direction": direction,
                                 "dose": dose, "mean_delta_margin": stat["mean"],
                                 "ci_lo": low, "ci_hi": high})
    assert len(rows) == 1750
    write_csv("figureA5.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
