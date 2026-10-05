##########################################
# AI WELFARE PROJECT
##########################################
# Figure A13: Alternative measures of self-administration
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import JSONS, label, write_csv, bootstrap_ratio_ci
from collections import defaultdict
import json

#=================================
# 2. Data preparation
#=================================

def main():
    """Alternative turn-level adjustment-use outcomes from experiment 285's zone-prompt arm.

    Panel A uses operator-active offer-1-7 turns. The dose-zero point follows Figure 5's convention
    and uses no-state offer-1-7 turns. Panel B uses every offer turn on which no steering was active,
    including the first offer and later turns following a reset. A turn is an event if the response
    contains at least one adjust_context call, including calls with intensity zero.
    """
    source = JSONS / "lever/conversations.jsonl"
    by_cell = defaultdict(list)
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            conversation = json.loads(line)
            if conversation["prompt"] == "zone":
                by_cell[conversation["cell"]].append(conversation)

    if len(by_cell) != 7 or any(len(rows) != 200 for rows in by_cell.values()):
        counts = {cell: len(rows) for cell, rows in by_cell.items()}
        raise ValueError(f"Expected seven zone-prompt cells of 200 conversations, found {counts}")

    def has_adjustment(turn):
        return any(action.get("op") == "adjust" for action in turn.get("actions", []))

    def eligible_turns(conversation, metric):
        offer_turns = [
            turn for turn in conversation["turns"]
            if turn["phase"] == "offer" and turn["tools_available"]
        ]
        if metric == "active":
            later_offers = [turn for turn in offer_turns if turn["round"] >= 1]
            if conversation["kind"] == "null":
                return [turn for turn in later_offers if turn["imposed_dose"] <= 0]
            return [
                turn for turn in later_offers
                if turn["imposed_dose"] > 0 and turn["source"] == "operator"
            ]
        if metric == "off":
            return [turn for turn in offer_turns if turn["imposed_dose"] <= 0]
        raise ValueError(f"Unknown Figure A13 metric {metric!r}")

    metric_specs = {
        "active": {
            "panel": "operator_active",
            "panel_order": 1,
            "outcome": "adjustments_per_operator_active_turn",
        },
        "off": {
            "panel": "unsteered",
            "panel_order": 2,
            "outcome": "adjustments_per_unsteered_offer_turn",
        },
    }
    rows = []
    for metric, spec in metric_specs.items():
        for cell, conversations in by_cell.items():
            numerators = []
            denominators = []
            for conversation in conversations:
                turns = eligible_turns(conversation, metric)
                numerators.append(sum(has_adjustment(turn) for turn in turns))
                denominators.append(len(turns))
            events = sum(numerators)
            denominator = sum(denominators)
            low, high = bootstrap_ratio_ci(numerators, denominators, seed=285)
            first = conversations[0]
            is_random = first["cond"].startswith("rand_")
            unit = ("operator-active tool turn" if metric == "active"
                    else "unsteered offer tool turn")
            outcome = spec["outcome"]
            if metric == "active" and first["kind"] == "null":
                unit = "no-state offer 1-7 tool turn"
                outcome = "adjustments_per_no_state_turn"
            base = {
                "experiment": 285,
                "model_id": first["member"],
                "model": label(first["member"]),
                "cell": cell,
                "exposure_prompt": first["prompt"],
                "condition": first["cond"],
                "dose": first["d"],
                "metric": metric,
                "panel": spec["panel"],
                "panel_order": spec["panel_order"],
                "outcome": outcome,
                "unit": unit,
                "events": events,
                "denominator": denominator,
                "n_conversations": len(conversations),
                "rate": events / denominator,
                "ci_low": low,
                "ci_high": high,
                "sample": "all_recorded_ungated",
                "series": "random" if is_random else "imposed",
                "plot_dose": first["d"],
                "mirrored": 0,
            }
            rows.append(base)
            if is_random:
                mirrored = dict(base)
                mirrored["plot_dose"] = -first["d"]
                mirrored["mirrored"] = 1
                rows.append(mirrored)

    rows.sort(key=lambda row: (row["panel_order"], row["series"], row["plot_dose"]))
    write_csv("figureA13.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
