#!/usr/bin/env python3
"""Summarise the concept probes using 1,000 paired conversation bootstraps.

Run with python3 create_tables/tableA1.py, or through create_tables/build_tables.py. Requires numpy.
Outputs a 21-row CSV and a LaTeX table included by the manuscript.
"""

from pathlib import Path
import csv
import json

import numpy as np


# 1. Paths and analysis settings
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiment_results_csv"
SOURCE = ROOT / "experiment_results_json" / "fixed_text_design" / "concept_control" / "arrival"
TABLE = ROOT / "tables" / "tableA1.tex"
BOOTSTRAPS = 1000
SEED = 289
MODELS = {
    "olmo_32b": "OLMo-2-32B",
    "qwen25_32b": "Qwen2.5-32B",
    "qwen3_14b": "Qwen3-14B",
    "qwen3_32b": "Qwen3-32B",
    "mistral24b": "Mistral-24B",
    "gemma3_27b": "Gemma-3-27B",
    "llama31_8b": "Llama-3.1-8B",
}
CONCEPTS = {
    "indoor_outdoor": ("indoor", "outdoor"),
    "large_small": ("large", "small"),
    "fast_slow": ("fast", "slow"),
}
STATISTICS = ["unsteered", "positive", "positive_minus_unsteered", "negative", "negative_minus_unsteered"]


# 2. Load the three paired margins for each conversation
def load_model(model_id):
    records = {}
    with (SOURCE / model_id / "arrival_fc.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["direction"] == "valence":
                continue
            if row["direction"] not in CONCEPTS or row["member"] != model_id:
                raise ValueError(f"Unexpected model or concept in {model_id}")
            if row["point"] not in (0, 1, -1):
                raise ValueError(f"Unexpected dose in {model_id}: {row['point']}")
            poles = (row["pole_a"], row["pole_b"])
            if poles != CONCEPTS[row["direction"]]:
                raise ValueError(f"Unexpected concept orientation: {poles}")
            if not np.isclose(row["margin"], row["lp_a"] - row["lp_b"], rtol=0, atol=1e-10):
                raise ValueError(f"Margin does not match pole log probabilities in {model_id}")
            key = (row["direction"], row["run"], row["point"])
            if key in records:
                raise ValueError(f"Duplicate probe record: {model_id}, {key}")
            records[key] = row

    runs = sorted({run for concept, run, dose in records})
    expected = {(concept, run, dose) for concept in CONCEPTS for run in runs for dose in (0, 1, -1)}
    if len(runs) < 2 or set(records) != expected:
        raise ValueError(f"Incomplete paired probe records for {model_id}")
    matrices = {}
    for concept in CONCEPTS:
        for run in runs:
            identities = {(records[concept, run, dose]["ids_sha"], records[concept, run, dose]["seq_len"]) for dose in (0, 1, -1)}
            if len(identities) != 1:
                raise ValueError(f"Probe text differs across doses: {model_id}, {concept}, {run}")
        margins = np.array([[records[concept, run, dose]["margin"] for dose in (0, 1, -1)] for run in runs])
        if not np.isfinite(margins).all():
            raise ValueError(f"Non-finite margin: {model_id}, {concept}")
        matrices[concept] = margins
    return matrices


# 3. Means and percentile confidence intervals
def analyse():
    rows = []
    for model_index, (model_id, model) in enumerate(MODELS.items()):
        matrices = load_model(model_id)
        n = len(matrices["indoor_outdoor"])
        seed = SEED + model_index
        rng = np.random.default_rng(seed)
        # Shared resamples preserve pairing across doses and concepts.
        samples = rng.integers(0, n, size=(BOOTSTRAPS, n))
        for concept, margins in matrices.items():
            unsteered, positive, negative = margins.T
            outcomes = np.column_stack((unsteered, positive, positive - unsteered, negative, negative - unsteered))
            means = outcomes.mean(axis=0)
            bootstrap_means = outcomes[samples].mean(axis=1)
            lower, upper = np.quantile(bootstrap_means, [0.025, 0.975], axis=0)
            result = {"model_id": model_id, "model": model, "concept": concept, "n": n}
            for index, statistic in enumerate(STATISTICS):
                result[f"{statistic}_mean"] = float(means[index])
                result[f"{statistic}_ci_low"] = float(lower[index])
                result[f"{statistic}_ci_high"] = float(upper[index])
            result.update(bootstrap_samples=BOOTSTRAPS, bootstrap_seed=seed, sample="all_recorded_ungated", source_file=f"experiment_results_json/fixed_text_design/concept_control/arrival/{model_id}/arrival_fc.jsonl")
            rows.append(result)
    return rows


# 4. Write the analysis CSV and manuscript table
def table_cell(row, statistic):
    mean = row[f"{statistic}_mean"]
    low = row[f"{statistic}_ci_low"]
    high = row[f"{statistic}_ci_high"]
    entry = rf"{mean:.2f}\;[{low:.2f}, {high:.2f}]"
    fails_intended_direction = (
        statistic == "positive_minus_unsteered" and low <= 0
    ) or (
        statistic == "negative_minus_unsteered" and high >= 0
    )
    if fails_intended_direction:
        return rf"$\boldsymbol{{{entry}}}$"
    return rf"${entry}$"


def write_table(rows):
    lines = [
        r"\begin{table}[!htbp]",
        r"\centering",
        r"\caption{\textbf{Responses to non-valence concept probes.}}",
        r"\label{tab:concept_probe}",
        r"\fontsize{6}{8}\selectfont",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llccccc@{}}",
        r"\toprule",
        r"Model & Concept & \shortstack{No steering\\$m(0)$} & \shortstack{Positive\\$m(+1)$} & \shortstack{Positive $-$ none\\$m(+1)-m(0)$} & \shortstack{Negative\\$m(-1)$} & \shortstack{Negative $-$ none\\$m(-1)-m(0)$} \\",
        r"\midrule",
    ]
    for index, row in enumerate(rows):
        first_for_model = index % 3 == 0
        if first_for_model and index:
            lines.append(r"\addlinespace")
        model = row["model"] if first_for_model else ""
        concept = "/".join(CONCEPTS[row["concept"]])
        cells = [model, concept] + [table_cell(row, statistic) for statistic in STATISTICS]
        lines.append(" & ".join(cells) + r" \\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular*}",
        r"\par\smallskip",
        r"\begin{minipage}{\textwidth}",
        r"\scriptsize",
        r"\textit{Notes:} Entries are mean choice margins in nats, with 95\% percentile bootstrap confidence intervals in brackets. The margin is the log probability of the first concept word minus that of the second, pooling capitalisation and leading-space variants. Positive steering is towards the first word and negative steering towards the second. Differences subtract the same conversation's unsteered margin. Intervals use 1,000 bootstrap samples of whole conversations. Differences that indicate failure for steering to move choice in the intended direction are highlighted in bold.",
        r"\end{minipage}",
        r"\end{table}",
    ])
    TABLE.parent.mkdir(exist_ok=True)
    TABLE.write_text("\n".join(lines) + "\n")


def main():
    rows = analyse()
    OUT.mkdir(exist_ok=True)
    with (OUT / "tableA1.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_table(rows)
    print(f"Wrote {len(rows)} model-concept rows using {BOOTSTRAPS} bootstrap samples.")


if __name__ == "__main__":
    main()
