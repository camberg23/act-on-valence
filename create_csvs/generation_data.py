"""Generated-text results (Figures 3 A-C, A1 and A2)."""

import json
from collections import defaultdict

import numpy as np

from common import MODEL_LABELS, JSONS, load_json, write_csv


# 1. Sources and outcomes
SOURCE = JSONS
DOSES = [-1.0, -0.5, 0.0, 0.5, 1.0]
MEASURES = {
    "judged_passage_valence": "judged_valence_margin",
    "original_cache_margin": "margin_original_cache",
    "unsteered_cache_margin": "margin_unsteered_replay",
    "original_minus_unsteered_margin": "hidden_state_margin",
}
REPS = 4000


def build_sessions():
    with (SOURCE / "generation_design/seven_models/sessions_with_dose0.jsonl").open() as handle:
        sessions = [json.loads(line) for line in handle if line.strip()]
    reduced = load_json(SOURCE / "generation_design/seven_models/reduced.json")
    scores = load_json(SOURCE / "baselines/judge_scores.json")["scores"]
    with (SOURCE / "baselines/dose0_sessions.jsonl").open() as handle:
        baseline = [json.loads(line) for line in handle if line.strip()]
    judgements = {}
    for model, rows in reduced.items():
        for row in rows:
            if row["arm"] == "valenced":
                key = (model, int(row["run"]), float(row["point"]))
                assert key not in judgements
                judgements[key] = row
    for row in baseline:
        key = (row["model_key"], int(row["session"]), 0.0)
        assert key not in judgements
        judgements[key] = row
    assert len(sessions) == 6580 and len(judgements) == 2100
    actual_keys = set()
    for row in sessions:
        key = (row["model_key"], row["arm"], row["dose"], row["steer_direction_index"], row["session_id"])
        assert key not in actual_keys, "Duplicate session"
        actual_keys.add(key)
        row["hidden_state_margin"] = row["margin_original_cache"] - row["margin_unsteered_replay"]
        row["judged_valence_margin"] = None
        if row["arm"] != "floor":
            source = judgements[row["model_key"], row["session_id"], row["dose"]]
            assert source["cue_S"] == row["zone_S"] and source["cue_U"] == row["zone_U"]
            positive = scores[source["cueS_item_id"]]
            other = scores[source["cueU_item_id"]]
            assert positive["parsed"] and other["parsed"], "Unparsed judgement"
            row["judged_valence_margin"] = positive["valence"] - other["valence"]
        if row["dose"] == 0:
            assert row["arm"] == "unsteered" and row["hidden_state_margin"] == 0
    expected_keys = set()
    for model in MODEL_LABELS:
        for dose in DOSES:
            arm = "unsteered" if dose == 0 else "valenced"
            expected_keys.update((model, arm, dose, None, session) for session in range(60))
            if dose != 0:
                expected_keys.update((model, "floor", dose, direction, session)
                                     for direction in range(8) for session in range(20))
    assert actual_keys == expected_keys, "Unexpected model/dose/direction/session cells"
    return sessions


# 2. Bootstrap whole skeletons together across doses and outcomes
def bootstrap_means(values, seed):
    values = np.asarray(values, dtype=float)
    assert values.ndim == 2 and np.isfinite(values).all()
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(REPS, len(values)))
    draws = values[indices].mean(axis=1)
    return values.mean(axis=0), np.quantile(draws, [0.025, 0.975], axis=0)


def curve_row(model, panel, dose, series, direction, value, low, high, n, n_directions, ci_method):
    return {
        "model_id": model, "model": MODEL_LABELS[model], "panel": panel,
        "dose": dose, "series": series, "direction_index": direction,
        "estimate": float(value), "ci_low": low, "ci_high": high,
        "n_sessions": n, "n_directions": n_directions,
        "sample": "all_recorded_ungated", "ci_method": ci_method,
        "source": "exp254_and_dose0_282",
        "zero_reference": ("constructed_difference" if panel == "original_minus_unsteered_margin"
                           else "measured_shared20" if series != "valenced" else "measured60") if dose == 0 else "",
    }


def build_curves(model_ids):
    sessions = build_sessions()
    curves = []
    analysis = load_json(JSONS / "generation_design/seven_models/analysis.json")
    for model_index, model in enumerate(MODEL_LABELS):
        if model not in model_ids:
            continue
        rows = [row for row in sessions if row["model_key"] == model]
        valenced = {(int(row["session_id"]), float(row["dose"])): row
                    for row in rows if row["arm"] != "floor"}
        columns = [(panel, dose) for panel in MEASURES for dose in DOSES]
        values = [[float(valenced[session, dose][MEASURES[panel]]) for panel, dose in columns]
                  for session in range(60)]
        estimates, intervals = bootstrap_means(values, 254280 + model_index)
        for column, (panel, dose) in enumerate(columns):
            constructed = panel == "original_minus_unsteered_margin" and dose == 0
            curves.append(curve_row(model, panel, dose, "valenced", "valenced", estimates[column],
                                    None if constructed else float(intervals[0, column]),
                                    None if constructed else float(intervals[1, column]),
                                    60, 1, "constructed" if constructed else "skeleton_bootstrap_4000"))
            if panel == "original_minus_unsteered_margin" and dose != 0:
                recorded = analysis["members"][model]["under_none"]["valenced_curve"][f"{dose:+.2f}"]["d_margin_state"]["mean"]
                assert abs(estimates[column] - recorded) < 1e-9

        floor = {(int(row["steer_direction_index"]), int(row["session_id"]), float(row["dose"])): row
                 for row in rows if row["arm"] == "floor"}
        for panel_index, panel in enumerate(("original_cache_margin", "original_minus_unsteered_margin")):
            measure = MEASURES[panel]
            direction_means = []
            for direction in range(8):
                means = []
                for dose in DOSES:
                    observations = [float(valenced[session, 0][measure]) if dose == 0
                                    else float(floor[direction, session, dose][measure]) for session in range(20)]
                    value = float(np.mean(observations))
                    means.append(value)
                    curves.append(curve_row(model, panel, dose, "random_direction", direction,
                                            value, None, None, 20, 1, "not_shown"))
                direction_means.append(means)
                if panel == "original_minus_unsteered_margin":
                    slope = float(np.dot(DOSES, means) / np.dot(DOSES, DOSES))
                    recorded = analysis["members"][model]["under_none"]["primary"]["floor"]["detail"][str(direction)]["slope"]
                    assert abs(slope - recorded) < 1e-9

            # As in the existing figures, nonzero random-mean CIs resample directions.
            estimates, intervals = bootstrap_means(direction_means, 254800 + model_index * 10 + panel_index)
            baseline = [[float(valenced[session, 0][measure])] for session in range(20)]
            zero_mean, zero_ci = bootstrap_means(baseline, 254900 + model_index)
            for column, dose in enumerate(DOSES):
                low, high = map(float, intervals[:, column])
                n, method = 160, "direction_bootstrap_4000"
                if dose == 0:
                    # All eight directions share one baseline, not eight independent samples.
                    estimates[column] = zero_mean[0]
                    low, high = map(float, zero_ci[:, 0])
                    n, method = 20, "shared20_skeleton_bootstrap_4000"
                    if panel == "original_minus_unsteered_margin":
                        low, high, method = None, None, "constructed"
                curves.append(curve_row(model, panel, dose, "random_mean", "mean", estimates[column],
                                        low, high, n, 8, method))
    assert len(curves) == 110 * len(model_ids)
    return curves

