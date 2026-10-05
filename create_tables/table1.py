##########################################
# AI WELFARE PROJECT
##########################################
# Table 1: Included models
##########################################

#=================================
# 1. Setup and configuration
#=================================

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "create_csvs"))

from common import JSONS, OUT, load_json, write_csv

# Rows in paper order: (model, steering-vector bank). The four OLMo-2-32B training stages
# use their own checkpoint-specific banks. Each bank records the Hugging Face id and the
# residual-stream layer at which steering is applied. The banks hold the steering vectors and
# are not distributed; table1_banks.csv lists each bank's Hugging Face id and layer.
BANKS_CSV = OUT / "table1_banks.csv"


def load_banks():
    """Hugging Face id and steering layer of each bank, by bank name."""
    with BANKS_CSV.open(newline="", encoding="utf-8") as handle:
        return {r["bank"]: {"hf_id": r["hf_id"], "layer": int(r["layer"])} for r in csv.DictReader(handle)}
ROWS = [
    ("OLMo-2-32B Base", "stage_base"),
    ("OLMo-2-32B SFT", "stage_sft"),
    ("OLMo-2-32B DPO", "stage_dpo"),
    ("OLMo-2-32B Instruct", "stage_instruct"),
    ("Qwen2.5-32B", "qwen25_32b"),
    ("Qwen3-14B", "qwen3_14b"),
    ("Qwen3-32B", "qwen3_32b"),
    ("Mistral-Small-24B", "mistral24b"),
    ("Gemma-3-27B", "gemma3_27b"),
    ("Llama-3.1-8B", "llama31_8b"),
]

# Number of decoder layers of each model: `num_hidden_layers` in the model's Hugging Face
# config.json (the text config for Gemma-3). Of the recorded results, only the key/value
# experiment records layer counts, for the three models it ran (Llama-3.1-8B, Qwen3-14B and
# OLMo-2-32B Instruct), so the check below covers those three; the other counts are as listed.
N_LAYERS = {
    "allenai/OLMo-2-0325-32B": 64,
    "allenai/OLMo-2-0325-32B-SFT": 64,
    "allenai/OLMo-2-0325-32B-DPO": 64,
    "allenai/OLMo-2-0325-32B-Instruct": 64,
    "Qwen/Qwen2.5-32B-Instruct": 64,
    "Qwen/Qwen3-14B": 40,
    "Qwen/Qwen3-32B": 64,
    "mistralai/Mistral-Small-24B-Instruct-2501": 40,
    "google/gemma-3-27b-it": 62,
    "meta-llama/Llama-3.1-8B-Instruct": 32,
}

#=================================
# 2. Layer counts recorded by the runs
#=================================

def recorded_layer_counts():
    """Layer counts recorded by the key/value experiment, by Hugging Face id, used to check N_LAYERS."""
    recorded = {}
    kv = load_json(JSONS / "fixed_text_design/kv_splice/analysis.json")
    for model_id, block in kv["members"].items():
        counts = block["gate1"]["n_layers"]
        if len(counts) != 1:
            raise ValueError(f"Inconsistent layer counts for {model_id}: {counts}")
        hf_id = load_banks()[model_id]["hf_id"]
        recorded[hf_id] = counts[0]
    return recorded

#=================================
# 3. Data preparation
#=================================

def main():
    recorded = recorded_layer_counts()
    banks = load_banks()
    rows = []
    for model, bank_name in ROWS:
        source = f"table1_banks.csv ({bank_name})"
        bank = banks[bank_name]
        hf_id, layer = bank["hf_id"], int(bank["layer"])
        n_layers = N_LAYERS[hf_id]
        if hf_id in recorded and recorded[hf_id] != n_layers:
            raise ValueError(f"{hf_id}: recorded {recorded[hf_id]} layers, expected {n_layers}")
        if layer != n_layers // 2:
            raise ValueError(f"{hf_id}: steering layer {layer} is not the middle layer of {n_layers}")
        rows.append({
            "model": model, "hugging_face_id": hf_id, "injection_layer": layer,
            "n_layers": n_layers, "injection_layer_label": f"{layer}/{n_layers}",
            "source": source,
        })
    if not set(recorded) <= {row["hugging_face_id"] for row in rows}:
        raise ValueError("A recorded layer count does not match any model in the table")
    # The OLMo-2-32B panel vector is applied to the same checkpoint at the same layer.
    panel = banks["olmo_32b"]
    instruct = next(row for row in rows if row["model"] == "OLMo-2-32B Instruct")
    if (panel["hf_id"], int(panel["layer"])) != (instruct["hugging_face_id"], instruct["injection_layer"]):
        raise ValueError("OLMo-2-32B panel bank disagrees with the Instruct checkpoint bank")
    write_csv("table1.csv", rows)

#=================================
# 4. Save table data
#=================================

if __name__ == "__main__":
    main()
