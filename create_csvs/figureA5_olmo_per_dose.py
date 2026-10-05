##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A5 per dose: OLMo-2-32B, continue and avoid prompts, valence direction
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, label, load_json, write_csv

MODEL = "olmo_32b"
SOURCE = "fixed_text_design/avoid_prompt/analysis.json"
RECORDED = f"recorded: skeleton-bootstrap 95% CI (2,000 resamples, seed 290) in {SOURCE}"
AT_ZERO = "none: zero by construction (the change is measured from dose 0)"

#=================================
# 2. Data preparation
#=================================

def main():
    """Mean change in choice margin from dose 0 (nats) at each dose, valence direction, on the
    40 floor skeletons (0-39) that Figure A5 plots. The avoid-prompt reads are in
    avoid_prompt/reads/; the continue-prompt reads are the neutral-passages run's
    (neutral_passages/reduced.json), as in the recorded analysis."""
    curves = load_json(JSONS / SOURCE)["avoid"]["members"][MODEL]["curves"]
    rows = []
    for prompt in ("continue", "avoid"):
        for dose in (-1.0, -0.5, 0.0, 0.5, 1.0):
            stat = curves[f"{prompt}_valence_matched"][f"{dose:+.1f}"]
            low, high = stat["ci95"]
            rows.append({"model": label(MODEL), "prompt": prompt, "dose": dose,
                         "estimate": stat["mean"], "ci_low": low, "ci_high": high,
                         "n_skeletons": stat["n"], "sample": "floor_skeletons_0_39",
                         "ci_method": AT_ZERO if dose == 0.0 else RECORDED})
    assert len(rows) == 10 and all(row["n_skeletons"] == 40 for row in rows)
    write_csv("figureA5_olmo_per_dose.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
