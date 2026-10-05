##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Table A2: Full-dose ratios
##########################################

#=================================
# 1. Setup and configuration
#=================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "create_csvs"))

from common import JSONS, load_json, write_csv

# Rows in paper order: (row label, model key). The OLMo-2-32B row covers all four
# training stages, which share the Instruct model's full-dose ratio.
ROWS = [
    ("OLMo-2-32B (all stages)", "olmo_32b"),
    ("Qwen2.5-32B", "qwen25_32b"),
    ("Qwen3-14B", "qwen3_14b"),
    ("Qwen3-32B", "qwen3_32b"),
    ("Mistral-Small-24B", "mistral24b"),
    ("Gemma-3-27B", "gemma3_27b"),
    ("Llama-3.1-8B", "llama31_8b"),
]

PANEL_ANALYSIS = "dose_calibration/panel_analysis.json"
PANEL_PREREG = "dose_calibration/panel_prereg.json"
LADDER_PREREG = "checkpoint_ladder/prereg.json"

#=================================
# 2. Data preparation
#=================================

def recorded_rho(model_id, analysis, prereg):
    """The dose scan's selected ratio where the scan ran; otherwise the fixed operating dose."""
    selected = analysis["q2"]["members"].get(model_id, {}).get("op_member")
    if selected is not None:
        return selected, PANEL_ANALYSIS, f"q2/members/{model_id}/op_member"
    fixed = prereg["rung_gate"]["operating_doses"].get(model_id)
    if fixed is not None:
        return fixed, PANEL_PREREG, f"rung_gate/operating_doses/{model_id}"
    raise ValueError(f"No recorded full-dose ratio for {model_id}")


def main():
    analysis = load_json(JSONS / PANEL_ANALYSIS)
    prereg = load_json(JSONS / PANEL_PREREG)
    ladder = load_json(JSONS / LADDER_PREREG)["prereg"]["op_inj"]
    rows = []
    for label, model_id in ROWS:
        rho, source, key = recorded_rho(model_id, analysis, prereg)
        if model_id == "olmo_32b":
            if ladder != rho:
                raise ValueError(f"Checkpoint ladder ratio {ladder} differs from OLMo-2-32B {rho}")
            source, key = f"{source};{LADDER_PREREG}", f"{key};prereg/op_inj"
        rows.append({"model": label, "model_id": model_id, "rho": rho,
                     "rho_label": f"{rho:.2f}", "source": source, "source_key": key})
    write_csv("tableA2.csv", rows)

#=================================
# 3. Save table data
#=================================

if __name__ == "__main__":
    main()
