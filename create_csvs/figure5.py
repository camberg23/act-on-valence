##########################################
# AI WELFARE PROJECT
##########################################
# Figure 5: OLMo removal and self-administration
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, load_json, label, write_csv

#=================================
# 2. Data preparation
#=================================

def load_tool_results():
    cells = load_json(JSONS / "lever/analysis.json")["cells"]
    rows = []
    for cell_id, cell in cells.items():
        if cell["prompt"] != "zone":
            continue
        for outcome, key, unit in (
            ("resets_per_state_active_turn", "reset_rate_per_operator_active_turn", "operator-active tool turn"),
            ("self_administration_at_first_offer", "clean_self_admin", "conversation"),
        ):
            stat = cell[key]
            rows.append({
                "experiment": 285, "model_id": "olmo_32b", "model": label("olmo_32b"),
                "cell": cell_id, "exposure_prompt": cell["prompt"], "condition": cell["cond"],
                "dose": cell["d"], "outcome": outcome, "unit": unit,
                "events": stat["k"], "denominator": stat["n_turns"] if "n_turns" in stat else stat["n"],
                "n_conversations": cell["n"], "rate": stat["rate"],
                "ci_low": stat["lo"], "ci_high": stat["hi"], "sample": "all_recorded_ungated",
            })
    return rows

def prepare_rows(exp285_rows):
    """Figure 5: removal and self-administration on the paper's dose axis, zone prompt only.

    Random directions have no sign, so each random cell is written twice, at ``-|d|`` and ``+|d|``.
    The ``mirrored`` column marks the negative-side copy.
    """
    panels = {
        "resets_per_state_active_turn": ("removal", 1),
        "self_administration_at_first_offer": ("self_administration", 2),
    }
    rows = []
    for row in exp285_rows:
        if row["exposure_prompt"] != "zone" or row["outcome"] not in panels:
            continue
        panel, panel_order = panels[row["outcome"]]
        is_random = row["condition"].startswith("rand_")
        for mirrored in ((0, 1) if is_random else (0,)):
            plotted = dict(row)
            plotted["panel"] = panel
            plotted["panel_order"] = panel_order
            plotted["series"] = "random" if is_random else "imposed"
            plotted["plot_dose"] = -row["dose"] if mirrored else row["dose"]
            plotted["mirrored"] = mirrored
            rows.append(plotted)
    rows.sort(key=lambda row: (row["panel_order"], row["series"], row["plot_dose"]))
    write_csv("figure5.csv", rows)

def main():
    prepare_rows(load_tool_results())

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
