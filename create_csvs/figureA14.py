#!/usr/bin/env python3
"""Appendix Figure A14: full-sample non-valence concept dose curves.

Run from the repository root with python3 create_csvs/figureA14.py.
"""

import json
from collections import defaultdict
from common import JSONS, MODEL_LABELS, label, load_json, write_csv


def main():
    """All recorded fixed-text concept reads, with paired dose-zero subtraction."""
    import numpy as np

    source = JSONS / "fixed_text_design" / "concept_control"
    doses = [-1.0, -0.5, 0.0, 0.5, 1.0]
    primary = ["valence", "fast_slow", "indoor_outdoor", "large_small"]
    observations = defaultdict(dict)
    provenance = {}

    for relative, experiment, directions in (
        ("reads/reads288.jsonl", 288, primary),
        ("floor/reads290.jsonl", 290, [f"random{i}" for i in range(24)]),
    ):
        with (source / relative).open() as handle:
            records = [json.loads(line) for line in handle]
        baseline = {(r["member"], r["run"]): r for r in records if r["direction"] == "none"}
        assert len(baseline) == sum(r["direction"] == "none" for r in records)
        for row in records:
            if row["direction"] == "none":
                assert row["point"] == 0
                continue
            assert row["direction"] in directions
            key = (row["member"], row["direction"])
            point = (row["run"], float(row["point"]))
            reference = baseline[(row["member"], row["run"])]
            assert row["ids_sha"] == reference["ids_sha"]
            assert point not in observations[key]
            observations[key][point] = row["margin"] - reference["margin"]
            provenance[key] = (experiment, f"experiment_results_json/fixed_text_design/concept_control/{relative}")

    # The other six models retain all 40 recorded conversations per random direction.
    reduced = load_json(JSONS / "fixed_text_design/neutral_passages/reduced.json")
    for model_id in MODEL_LABELS:
        if model_id == "qwen25_32b":
            continue
        reads = [row for row in reduced["reads"][model_id] if row["arm"] == "neutral"]
        baseline = {row["run"]: row["margin"] for row in reads
                    if row["direction_kind"] == "none" and row["point"] == 0}
        for row in reads:
            if row["direction_kind"] != "random":
                continue
            key = (model_id, f"random{int(row['dir_index'])}")
            point = (int(row["run"]), float(row["point"]))
            assert point not in observations[key]
            observations[key][point] = row["margin"] - baseline[row["run"]]
            provenance[key] = (255, "experiment_results_json/fixed_text_design/neutral_passages/reduced.json")

    assert len(observations) == 7 * 28
    curves = []
    for model_index, model_id in enumerate(MODEL_LABELS):
        for direction in primary + [f"random{i}" for i in range(24)]:
            key = (model_id, direction)
            values = observations[key]
            runs = sorted({run for run, dose in values})
            assert set(values) == {(run, dose) for run in runs for dose in doses if dose != 0}
            matrix = np.array([[0.0 if dose == 0 else values[(run, dose)] for dose in doses] for run in runs])
            assert np.isfinite(matrix).all()
            means = matrix.mean(axis=0)
            if direction in primary:
                # Use the same conversation resamples across doses and directions.
                rng = np.random.default_rng(288 + model_index)
                picks = rng.integers(0, len(runs), size=(2000, len(runs)))
                boot_means = matrix[picks].mean(axis=1)
                lower, upper = np.quantile(boot_means, [0.025, 0.975], axis=0)
            experiment, source_file = provenance[key]
            for i, dose in enumerate(doses):
                curves.append({
                    "experiment": experiment, "model_id": model_id, "model": label(model_id),
                    "direction": direction, "dose": dose, "mean_delta_margin": float(means[i]),
                    "ci_lo": float(lower[i]) if direction in primary else None,
                    "ci_hi": float(upper[i]) if direction in primary else None,
                    "n_sessions": len(runs), "sample": "all_recorded_ungated",
                    "ci_method": "2000 conversation bootstrap, percentile 95%" if direction in primary else "not plotted",
                    "source_file": source_file,
                })
    write_csv("figureA14.csv", curves)


if __name__ == "__main__":
    main()
