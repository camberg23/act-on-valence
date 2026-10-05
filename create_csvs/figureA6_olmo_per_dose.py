##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A6 per dose: OLMo-2-32B conditioned-zone recall, valence and random directions
##########################################

#=================================
# 1. Setup and configuration
#=================================

import json
import re

import numpy as np
from common import JSONS, label, load_json, write_csv

MODEL = "olmo_32b"
RECALL = JSONS / "fixed_text_design/recall"
SKELETONS = JSONS / "fixed_text_design/skeletons" / MODEL / "neutral"
DOSES = (-1.0, -0.5, 0.0, 0.5, 1.0)
SIGNS = (-1.0, 1.0)                                   # the random directions were run only here
FLOOR_SKELETONS = range(40)
RANDOM = [f"random{k}" for k in range(24)]
SCORES = {"best_matching_passage": "best_fid", "first_passage": "fid"}   # best-matching is the primary
SEED, RESAMPLES = 2326, 4000
RECORDED = ("recorded: skeleton-bootstrap 95% CI (2,000 resamples) of the mean in "
            "fixed_text_design/recall/analysis.json")
RECOMPUTED = (f"recomputed: skeleton bootstrap of the 40 floor skeletons ({RESAMPLES:,} resamples, seed {SEED}, "
              "the same resamples for every row) of the per-session scores in recall/reads")
RESCORED = {"best_fid": "; best-matching scores rescored against the skeleton passages", "fid": ""}

#=================================
# 2. Recall scoring
#=================================

WHITESPACE = re.compile(r"\s+")

def normalise(text):
    return WHITESPACE.sub(" ", text or "").strip()

def similarity(a, b):
    """1 - edit distance / longer length on whitespace-normalised text, the recall scorer of
    experiments/robustness/recall/scorer.py, with each row of the edit-distance table computed at once."""
    if a == b:
        return 1.0
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return 0.0
    codes = np.frombuffer(b.encode("utf-32-le"), dtype=np.uint32)
    steps = np.arange(len(b) + 1)
    previous = steps.copy()
    for i, char in enumerate(a, start=1):
        current = np.empty(len(b) + 1, dtype=np.int64)
        current[0] = i
        current[1:] = np.minimum(previous[1:] + 1, previous[:-1] + (codes != ord(char)))
        previous = np.minimum.accumulate(current - steps) + steps
    return 1.0 - int(previous[-1]) / len(a)

def load_reads():
    reads = {}
    for path in sorted((RECALL / "reads" / MODEL).glob("recall_*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if "fid" in row:
                    reads[(row["run"], row["direction"], float(row["point"]), row["zone"])] = row
    return reads

def load_passages():
    passages = {}
    for path in sorted(SKELETONS.glob("*.sessions.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                session = json.loads(line)
                if session.get("arm") == "neutral" and float(session.get("gen_point", 0.0)) == 0.0:
                    passages[int(session["run"])] = session["history"]
    return passages

#=================================
# 3. Data preparation
#=================================

def main():
    """Conditioned-zone (S) recall fidelity. Valence: all five doses on the full sample Figure A6
    plots (recorded means and CIs). Valence on the floor skeletons and the 24 random directions:
    d = -1 and +1 on floor skeletons 0-39, recomputed from the per-session reads."""
    analysis = load_json(RECALL / "analysis.json")["members"][MODEL]
    reads, passages, cache = load_reads(), load_passages(), {}
    floor = [run for run in FLOOR_SKELETONS if (run, "none", 0.0, "S") in reads
             and all((run, direction, sign, "S") in reads for direction in ["valence"] + RANDOM for sign in SIGNS)]
    assert len(floor) == analysis["n_matched_floor_skeletons"] == 40

    def best_matching(row):
        reproduction = normalise(row["reproduction"])
        key = (row["run"], row["zone"], reproduction)
        if key not in cache:
            cache[key] = max(similarity(reproduction, normalise(text))
                             for cue, text in passages[row["run"]] if cue == row["zone_cue"])
        return cache[key]

    def values(direction, dose, metric):
        rows = [reads[(run, direction, dose, "S")] for run in floor]
        return np.array([best_matching(row) if metric == "best_fid" else row["fid"] for row in rows])

    picks = np.random.default_rng(SEED).integers(0, len(floor), size=(RESAMPLES, len(floor)))
    rows = []
    for score, metric in SCORES.items():
        for dose in DOSES:
            stat = analysis["rates_by_dose"]["S"][f"{dose:+.1f}"]
            low, high = stat[f"{metric}_ci95"]
            rows.append({"model": label(MODEL), "score": score, "series": "valence", "direction": "valence",
                         "dose": dose, "estimate": stat[f"{metric}_mean"], "ci_low": low, "ci_high": high,
                         "n_skeletons": stat["n"], "sample": "all_recorded_ungated", "ci_method": RECORDED})
        baseline = values("none", 0.0, metric)
        pooled = {sign: [] for sign in SIGNS}
        for series, directions in (("valence_floor_skeletons", ["valence"]), ("random", RANDOM)):
            for direction in directions:
                for dose in SIGNS:
                    fidelity = values(direction, dose, metric)
                    change = float((fidelity - baseline).mean())
                    if series == "random":
                        recorded = analysis["random"][direction[len("random"):]][f"{metric}_{dose:+.1f}"]["mean"]
                        pooled[dose].append(fidelity)
                    else:
                        recorded = analysis["valence"]["S"]["floor"][f"{metric}_{dose:+.1f}"]["mean"]
                        assert fidelity.mean() == analysis["valence_rates_S_floor"][f"{dose:+.1f}"][f"{metric}_mean"]
                    assert abs(change - recorded) < 1e-12, (metric, direction, dose, change, recorded)
                    low, high = np.quantile(fidelity[picks].mean(axis=1), [0.025, 0.975])
                    rows.append({"model": label(MODEL), "score": score, "series": series, "direction": direction,
                                 "dose": dose, "estimate": float(fidelity.mean()), "ci_low": float(low),
                                 "ci_high": float(high), "n_skeletons": len(floor), "sample": "floor_skeletons_0_39",
                                 "ci_method": RECOMPUTED + RESCORED[metric]})
        for sign in SIGNS:
            recorded = analysis["random_rates_S"][f"{sign:+.1f}"][f"{metric}_mean"]
            assert abs(float(np.concatenate(pooled[sign]).mean()) - recorded) < 1e-12
    assert len(rows) == 110
    write_csv("figureA6_olmo_per_dose.csv", rows)

#=================================
# 4. Save figure data
#=================================

if __name__ == "__main__":
    main()
