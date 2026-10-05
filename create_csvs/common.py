##########################################
# AI WELFARE PROJECT
##########################################
# Shared paths, CSV writing and bootstrap functions
##########################################

#=================================
# 1. Setup and configuration
#=================================

from __future__ import annotations
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSONS = ROOT / "experiment_results_json"
OUT = ROOT / "experiment_results_csv"

MODEL_LABELS = {
    "olmo_32b": "OLMo-2-32B",
    "qwen25_32b": "Qwen2.5-32B",
    "qwen3_14b": "Qwen3-14B",
    "qwen3_32b": "Qwen3-32B",
    "mistral24b": "Mistral-24B",
    "gemma3_27b": "Gemma-3-27B",
    "llama31_8b": "Llama-3.1-8B",
}

#=================================
# 2. Data loading and formatting
#=================================

def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)

def label(model: str) -> str:
    return MODEL_LABELS.get(model, model)

def dose_number(key):
    return float(key)

def scalar(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value

#=================================
# 3. Save CSV files
#=================================

def write_csv(name: str, rows: list[dict], fieldnames: list[str] | None = None):
    OUT.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows produced for {name}")
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: scalar(row.get(key)) for key in fieldnames})

#=================================
# 4. Summary statistics
#=================================

def ci(stat: dict | None):
    if not stat:
        return (None, None)
    values = stat.get("ci95") or stat.get("ci")
    if not values:
        return (None, None)
    return (values[0], values[1])

def mean(values):
    values = [float(value) for value in values if value is not None]
    return statistics.fmean(values) if values else None

#=================================
# 5. Bootstrap confidence intervals
#=================================

def bootstrap_mean_ci(values, seed: int, reps: int = 4000):
    values = [float(value) for value in values if value is not None]
    if not values:
        return (None, None)
    if len(values) == 1 or max(values) == min(values):
        return (values[0], values[0])
    rng = random.Random(seed)
    n = len(values)
    draws = []
    for _ in range(reps):
        draws.append(statistics.fmean(values[rng.randrange(n)] for _ in range(n)))
    draws.sort()
    return (draws[int(0.025 * reps)], draws[int(0.975 * reps) - 1])

def bootstrap_ratio_ci(numerators, denominators, seed: int, reps: int = 10_000):
    """Cluster-bootstrap a pooled event rate, with one numerator and denominator per cluster."""
    numerators = [int(value) for value in numerators]
    denominators = [int(value) for value in denominators]
    if len(numerators) != len(denominators) or not numerators:
        raise ValueError("Ratio bootstrap requires equally sized, non-empty inputs")
    if sum(denominators) == 0:
        raise ValueError("Ratio bootstrap denominator is zero")
    rng = random.Random(seed)
    n = len(numerators)
    draws = []
    for _ in range(reps):
        sampled = [rng.randrange(n) for _ in range(n)]
        numerator = sum(numerators[index] for index in sampled)
        denominator = sum(denominators[index] for index in sampled)
        draws.append(numerator / denominator)
    draws.sort()
    return (draws[int(0.025 * reps)], draws[int(0.975 * reps) - 1])
