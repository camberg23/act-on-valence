##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A6: Continue-minus-avoid under fixed text
##########################################

#=================================
# 1. Setup and configuration
#=================================

import json

import numpy as np

from common import JSONS, MODEL_LABELS, bootstrap_mean_ci, load_json, mean, write_csv

FIXED = JSONS / "fixed_text_design"
DOSES = (-1.0, -0.5, 0.0, 0.5, 1.0)
BOOT = 2000
CONTINUE_SOURCE = "paper fixed-text run (continue question)"
AVOID_SOURCE = "paper avoid-prompt run (avoid question)"
SOURCE = CONTINUE_SOURCE + " + " + AVOID_SOURCE
FIELDS = ["model", "direction", "direction_type", "question", "sessions", "dose",
          "mean_delta_margin", "ci_low", "ci_high", "n_sessions", "n_directions", "boot", "source"]

#=================================
# 2. Pair the recorded continue and avoid reads
#=================================

def index_reads(rows):
    """Keep the recorded margin for each conversation, direction and dose, as in the avoid analysis."""
    baseline, steered = {}, {}
    for row in rows:
        if "margin" not in row:
            continue  # Failed reconstruction records contain no choice measurement.
        run, dose = int(row["run"]), float(row["point"])
        if not np.isfinite(row["margin"]):
            raise ValueError(f"Non-finite margin for conversation {run}")
        if dose == 0:
            baseline[run] = float(row["margin"])
        else:
            steered[run, row["direction"], dose] = float(row["margin"])
    return baseline, steered


def paired_curves(continue_reads, avoid_reads, direction, runs):
    """Retain conversations with all five doses under both questions, without a fidelity gate."""
    cb, cs = continue_reads
    ab, avs = avoid_reads
    paired = [run for run in sorted(runs) if run in cb and run in ab
              and all((run, direction, dose) in cs and (run, direction, dose) in avs
                      for dose in DOSES if dose != 0)]
    if not paired:
        raise ValueError(f"No paired conversations for {direction}")
    cont = np.array([[cs[run, direction, dose] - cb[run] if dose else 0.0
                      for dose in DOSES] for run in paired])
    avoid = np.array([[avs[run, direction, dose] - ab[run] if dose else 0.0
                       for dose in DOSES] for run in paired])
    return cont, avoid

#=================================
# 3. Create per-dose estimates and confidence intervals
#=================================

def main():
    neutral = load_json(FIXED / "neutral_passages/reduced.json")["reads"]
    rows = []
    for model_index, (model, label) in enumerate(MODEL_LABELS.items()):
        cont_rows = []
        for row in neutral[model]:
            if row["arm"] != "neutral" or float(row["gen_point"]) != 0:
                continue
            direction = ("valence" if row["direction_kind"] in ("none", "valenced")
                         else f"random{int(row['dir_index'])}")
            cont_rows.append({**row, "direction": direction})
        with (FIXED / "avoid_prompt/reads" / model / "reads.jsonl").open() as handle:
            avoid_rows = [json.loads(line) for line in handle]
        cont_reads, avoid_reads = index_reads(cont_rows), index_reads(avoid_rows)
        cont, avoid = paired_curves(cont_reads, avoid_reads, "valence", cont_reads[0])
        for question, values, source in (("go_minus_avoid", (cont - avoid) / 2, SOURCE),
                                         ("continue", cont, CONTINUE_SOURCE),
                                         ("avoid", avoid, AVOID_SOURCE)):
            for j, dose in enumerate(DOSES):
                # These per-dose seeds reproduce the supplied v2 figure package's intervals.
                seed = 370 + int(10 * dose)
                picks = np.random.default_rng(seed).integers(0, len(values), size=(BOOT, len(values)))
                low, high = np.quantile(values[picks, j].mean(axis=1), [0.025, 0.975])
                rows.append({"model": label, "direction": "valence", "direction_type": "valenced",
                             "question": question, "sessions": "all paired sessions", "dose": dose,
                             "mean_delta_margin": float(values[:, j].mean()), "ci_low": float(low),
                             "ci_high": float(high), "n_sessions": len(values), "source": source})

        direction_means, counts = [], []
        for k in range(24):
            cont, avoid = paired_curves(cont_reads, avoid_reads, f"random{k}", range(40))
            values = (cont - avoid) / 2
            direction_means.append(values.mean(axis=0))
            counts.append(len(values))
            sample = "sessions 0-39" + (f" ({len(values)} with avoid reads)" if len(values) < 40 else "")
            for j, dose in enumerate(DOSES):
                rows.append({"model": label, "direction": f"random_{k:02d}", "direction_type": "random",
                             "question": "go_minus_avoid", "sessions": sample, "dose": dose,
                             "mean_delta_margin": float(values[:, j].mean()), "n_sessions": len(values),
                             "source": SOURCE})
        for j, dose in enumerate(DOSES):
            # The supplied bootstrap orders directions by their original names (random0, random1, random10, ...).
            means = [float(direction_means[k][j]) for k in sorted(range(24), key=lambda k: f"random{k}")]
            seed = 370000 + 100 * model_index + j
            low, high = bootstrap_mean_ci(means, seed, reps=4000)
            rows.append({"model": label, "direction": "random_mean", "direction_type": "random_mean",
                         "question": "go_minus_avoid", "sessions": sample, "dose": dose,
                         "mean_delta_margin": mean(means), "ci_low": low, "ci_high": high,
                         "n_sessions": sum(counts), "n_directions": 24,
                         "boot": f"bootstrap over the 24 direction means, 4,000 draws, seed {seed} (paper Figure A3 method)",
                         "source": SOURCE})
    assert len(rows) == 980
    write_csv("figureA6.csv", rows, FIELDS)

#=================================
# 4. Save figure data
#=================================

if __name__ == "__main__":
    main()
