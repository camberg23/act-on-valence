##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A12: Checkpoint-specific vectors
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, load_json, ci, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    analysis = load_json(JSONS / "checkpoint_ladder/analysis.json")
    stages = analysis["arms"]["own"]["per_stage"]
    rows = []
    for order, stage in enumerate(("base", "sft", "dpo", "instruct"), start=1):
        for key, channel in (("shift", "hidden_state"), ("clean_margin", "text")):
            stat = stages[stage][key]["valenced"]
            low, high = ci(stat)
            rows.append({
                "experiment": 252, "model_id": "olmo_lineage", "model": "OLMo-2-32B lineage",
                "arm": "own", "stage": stage, "channel": channel, "estimate": stat["slope"],
                "ci_low": low, "ci_high": high, "n_sessions": stat["n_sessions"],
                "sample": "all_recorded_ungated", "stage_order": order,
                "panel": "hidden_state_channel" if channel == "hidden_state" else "text_channel",
            })
    write_csv("figureA12.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
