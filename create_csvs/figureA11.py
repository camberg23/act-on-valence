##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A11: Addressing and storage halves of the cache
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, load_json, label, ci, write_csv

#=================================
# 2. Data preparation
#=================================

def main():
    data = load_json(JSONS / "fixed_text_design/kv_splice/analysis.json")
    rows = []
    for model_id, member in data["members"].items():
        for arm, result in member["arms"].items():
            if result["n_exposures"] != 1 or result["k"] != 1:
                continue
            for channel_key, channel_label in (("share_addressing", "addressing_keys"), ("share_storage", "storage_values")):
                stat = result["channels"][channel_key]
                lo, hi = ci(stat)
                rows.append({
                    "experiment": 271,
                    "model_id": model_id,
                    "model": label(model_id),
                    "arm": arm,
                    "spread": result.get("spread"),
                    "n_exposures": result.get("n_exposures"),
                    "strength": result.get("k"),
                    "channel": channel_label,
                    "share_of_full_cache_slope": stat.get("value"),
                    "ci_low": lo,
                    "ci_high": hi,
                    "n_shared_runs": result["channels"].get("n_shared_runs"),
                    "sample": "scale_relative_gated",
                })
    write_csv("figureA11.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
