##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A7: Text-differenced and neutral-substrate estimates
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, MODEL_LABELS, load_json, label, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    generated = load_json(JSONS / "generation_design/seven_models/analysis.json")["members"]
    fixed = load_json(JSONS / "fixed_text_design/neutral_passages/analysis.json")["members"]
    rows = []
    for model in MODEL_LABELS:
        gen = generated[model]["under_none"]["primary"]["differenced_margin_slope"]
        neutral = fixed[model]["under_none"]["primary"]["differenced_margin_slope_full_n"]
        paired = fixed[model]["under_none"]["pairing"]["neutral_vs_steered"]
        for panel, x, y, x_measure, y_measure, sample in (
            ("exp254_vs_exp255_neutral", gen["slope"], neutral["slope"],
             "exp254_steering_generated_text", "exp255_neutral_fixed_text", "all_recorded_ungated"),
            ("exp255_steered_vs_neutral", paired["slope_b"], paired["slope_a"],
             "exp255_steered_substrate", "exp255_neutral_fixed_text", "matched_skeletons_ungated"),
        ):
            rows.append({"panel": panel, "model_id": model, "model": label(model),
                         "x_estimate": x, "x_measure": x_measure, "y_estimate": y,
                         "y_measure": y_measure, "sample": sample})
    write_csv("figureA7.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
