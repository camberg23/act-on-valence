"""Fixed-text dose curves shared by Figures 3 and A3."""
from common import JSONS, MODEL_LABELS, load_json, label, ci, mean, bootstrap_mean_ci, defaultdict


def summarise_random_curves(groups: dict, panel: str, model_id: str, seed_base: int):
    rows = []
    by_dose = defaultdict(list)
    for direction_index, dose_values in sorted(groups.items()):
        for dose, values in sorted(dose_values.items()):
            value = mean(values)
            by_dose[dose].append(value)
            rows.append({
                "panel": panel,
                "model_id": model_id,
                "model": label(model_id),
                "dose": dose,
                "series": "random_direction",
                "direction_kind": "random",
                "direction_index": direction_index,
                "estimate": value,
                "n_sessions": len(values),
                "n_directions": 1,
                "sample": "all_recorded_ungated",
            })
    for index, (dose, direction_means) in enumerate(sorted(by_dose.items())):
        lo, hi = bootstrap_mean_ci(direction_means, seed_base + index)
        rows.append({
            "panel": panel,
            "model_id": model_id,
            "model": label(model_id),
            "dose": dose,
            "series": "random_mean",
            "direction_kind": "random",
            "direction_index": "mean",
            "estimate": mean(direction_means),
            "ci_low": lo,
            "ci_high": hi,
            "n_sessions": sum(len(groups[d][dose]) for d in groups if dose in groups[d]),
            "n_directions": len(direction_means),
            "sample": "all_recorded_ungated",
        })
    return rows

def build_curves(model_ids):
    reduced = load_json(JSONS / "fixed_text_design/neutral_passages/reduced.json")
    analysis = load_json(JSONS / "fixed_text_design/neutral_passages/analysis.json")
    rows = []
    for model_index, model in enumerate(MODEL_LABELS):
        if model not in model_ids:
            continue
        reading = analysis["members"][model]["under_none"]
        for dose, stat in reading["valenced_curve"].items():
            low, high = ci(stat)
            rows.append({
                "panel": "steered_minus_clean_margin", "model_id": model, "model": label(model),
                "dose": float(dose), "series": "valenced", "direction_kind": "valenced",
                "direction_index": "valenced", "estimate": stat["mean"], "ci_low": low, "ci_high": high,
                "n_sessions": stat["n"], "n_directions": 1, "sample": "all_recorded_ungated",
            })
        reads = [row for row in reduced["reads"][model] if row["arm"] == "neutral"]
        baseline = {row["run"]: row["margin"] for row in reads
                    if row["direction_kind"] == "none" and row["point"] == 0}
        groups = defaultdict(lambda: defaultdict(list))
        for row in reads:
            if row["direction_kind"] == "random":
                delta = row["margin"] - baseline[row["run"]]
                groups[int(row["dir_index"])][float(row["point"])].append(delta)
        for direction in groups:
            groups[direction][0.0] = [0.0]
        rows.extend(summarise_random_curves(groups, "steered_minus_clean_margin", model,
                                           255000 + model_index * 100))
    return rows
