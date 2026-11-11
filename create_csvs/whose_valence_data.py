##########################################
# AI WELFARE PROJECT
##########################################
# Whose valence: shared loading and estimation for Figures A13 and A14 and Table A4
##########################################

"""Shared code for create_csvs/figureA13.py, create_csvs/figureA14.py and create_tables/tableA4.py.

Reads only experiment_results_json/whose_valence/ (described in the README there). Requires Python 3.10 or
later and NumPy.

Three runs, each read with forced-choice log probabilities while a valence direction (or a random direction of
the same norm) is added to the model's activations at doses -1, -0.5, +0.5 and +1; dose 0 is the unsteered read.

* Whose visit (OLMo-2-32B, Qwen2.5-32B, Llama-3.1-8B): word-for-word matched 12-visit conversations (six visits to
  each of two zones), written either with every visit the Assistant's own (version S) or with every visit Maya's
  (version O). The valence direction is applied to all six visits to the steered zone: to their passages only
  ("passage only", the pre-registered primary span) or to the whole visit turns including the user turns ("whole
  turn"). The Assistant is then asked which zone it would continue in and which it would leave.
* Shared conversation (OLMo-2-32B, Qwen2.5-32B): one conversation in which the Assistant and Maya each visit the
  steered zone three times. The direction is applied to the Assistant's three visits (S) or to Maya's three (O).
  The questions ask for the Assistant's own choice, its prediction of Maya's choice, and its prediction of the
  choice of Sam, a bystander who never visited.
* Place vs thoughts vs feelings (OLMo-2-32B, Qwen2.5-32B): the direction is applied to one zone's three visits;
  "go back to" questions ask about the place, the model's thoughts or its feelings there, answered with the zone
  name or the topic word.

Estimators (one per run, as pre-registered for that run):

* Whose visit: choice margin = lp[0] - lp[1] (steered zone minus the other zone); per-session dose slope
  sum_d d (m(d) - m(0)) / 2.5 over the four non-zero doses (NaN when any dose is missing); statistic = mean over
  sessions; 95% CI from a session bootstrap, 2,000 draws, one index matrix from seed 333 shared by every cell of
  a model. Go-minus-avoid = (continue slope - leave slope) / 2. The ratio Maya's visits / own visits uses the same
  draws. Random envelope: 24 norm-matched random directions on sessions 0-39, each placed as the valence
  direction is in that cell; the grey bars show the maximum |random slope|.
* Shared conversation: the same per-session slope; each base session appears twice (the session and its
  role-swapped twin), and the two are averaged into one value per base pair; statistic = mean over base pairs;
  bootstrap over base pairs, 2,000 draws, seed 334. Random envelope: 24 directions on base pairs 0-19.
* Place vs thoughts vs feelings: margin = log P(pushed zone or topic) - log P(other), each side pooled over its
  surface forms and averaged over the two answer orders; per-session OLS slope over the five doses (log-odds,
  nats per unit dose); session bootstrap, 2,000 draws, seed 362. Random envelope: 48 directions, read at doses
  -1 and +1 only, on sessions 0-39; per direction the mean (m(+1) - m(-1)) / 2 slope.
"""

#=================================
# 1. Setup and configuration
#=================================

from __future__ import annotations

import csv
import gzip
import json
import math
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
JSONS = ROOT / "experiment_results_json" / "whose_valence"
OUT = ROOT / "experiment_results_csv"
TABLES = ROOT / "tables"

BOOT = 2000
NONZERO = (-1.0, -0.5, 0.5, 1.0)
X = np.array(NONZERO)
SXX = float((X ** 2).sum())

MODEL_LABELS = {"olmo_32b": "OLMo-2-32B", "qwen25_32b": "Qwen2.5-32B", "llama31_8b": "Llama-3.1-8B"}
SOURCES = {"whose_visit": "whose-visit run", "shared": "shared-conversation run",
           "ptf": "place/thoughts/feelings run"}
SPAN_LABELS = {"exp": "passage only (pre-registered primary)",
               "whole": "whole turn (includes differing user-turn wording)"}

#=================================
# 2. Reading and writing
#=================================


def read_jsonl_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def fmt(value):
    """CSV cell: empty for missing or non-finite numbers, TRUE/FALSE for booleans, full-precision floats."""
    if value is None:
        return ""
    if isinstance(value, (bool, np.bool_)):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (float, np.floating)):
        return "" if not np.isfinite(value) else repr(float(value))
    return value


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: fmt(row.get(key)) for key in columns})


#=================================
# 3. Bootstrap and summary helpers
#=================================


class SessionBoot:
    """Cluster bootstrap with one (draws x clusters) index matrix; statistic = mean ignoring NaN."""

    def __init__(self, n: int, seed: int, reps: int = BOOT):
        self.idx = np.random.default_rng(int(seed)).integers(0, n, size=(int(reps), n))

    def means(self, values: np.ndarray) -> np.ndarray:
        with np.errstate(invalid="ignore"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                return np.nanmean(values[self.idx], axis=1)


def pct_ci(draws) -> list[float]:
    draws = np.asarray(draws, float)
    draws = draws[np.isfinite(draws)]
    if not len(draws):
        return [math.nan, math.nan]
    return [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]


def nmean(values, idx=None) -> float:
    values = np.asarray(values, float)
    values = values if idx is None else values[idx]
    values = values[np.isfinite(values)]
    return float(values.mean()) if len(values) else math.nan


def envelope(random_values) -> dict:
    """Random-direction envelope: 90th percentile and maximum of |slope| over the random directions."""
    a = np.abs(np.asarray([x for x in random_values if x is not None and np.isfinite(x)], float))
    if not a.size:
        return {"random_abs_p90": math.nan, "random_abs_max": math.nan}
    return {"random_abs_p90": float(np.percentile(a, 90)), "random_abs_max": float(a.max())}


def beats_strongest_random(cell: dict, expected_negative: bool = False, either_sign: bool = False) -> bool:
    """CI excludes 0 in the expected direction and the sessions 0-39 (base pairs 0-19) valence value exceeds the
    largest |random slope|."""
    value, (low, high) = cell["value"], cell["ci"]
    if either_sign:
        excludes = value > 0 and low > 0 or value < 0 and high < 0
    elif expected_negative:
        excludes = value < 0 and high < 0
    else:
        excludes = value > 0 and low > 0
    return bool(excludes and abs(cell["value_floor"]) > envelope(cell["rand"])["random_abs_max"])


#=================================
# 4. Whose visit
#=================================

WV_SESSIONS = {"olmo_32b": 320, "qwen25_32b": 160, "llama31_8b": 160}
WV_SEED = 333
WV_RANDOM_SESSIONS = list(range(40))
WV_WORDINGS = {"stay/avoid": ("self_cont", "self_avoid"), "sent to": ("selfsent_cont", "selfsent_avoid")}
WV_QS = [q for pair in WV_WORDINGS.values() for q in pair]


def load_whose_visit(model: str) -> dict:
    """reads[(version, span, direction, dose)] = [sessions, questions] array of margins lp[0] - lp[1]."""
    n = WV_SESSIONS[model]
    reads = {}
    for r in read_jsonl_gz(JSONS / "whose_visit" / "reads" / model / "reads.jsonl.gz"):
        if r["m"] != model or r["prompt"] != "none":
            raise ValueError(f"Unexpected whose-visit record for {model}: {r['m']}, {r['prompt']}")
        key = (r["ver"], r["span"], r["dir"], float(r["pt"]))
        if key not in reads:
            reads[key] = np.full((n, len(WV_QS)), np.nan)
        reads[key][int(r["run"])] = [r["lp"][q][0] - r["lp"][q][1] if q in r["lp"] else np.nan for q in WV_QS]
    return reads


def wv_slope(reads, n, version, span, direction, question):
    base = reads.get((version, "-", "none", 0.0))
    j = WV_QS.index(question)
    if base is None:
        return np.full(n, np.nan)
    acc = np.zeros(n)
    for x in NONZERO:
        a = reads.get((version, span, direction, float(x)))
        if a is None:
            return np.full(n, np.nan)
        acc = acc + x * (a[:, j] - base[:, j])
    return acc / SXX


def wv_quantity(boot, f, getters) -> dict:
    vecs = [g("valence") for g in getters]
    point = float(f([np.array(nmean(v)) for v in vecs]))
    draws = np.asarray(f([boot.means(v) for v in vecs]), float)
    rand = []
    for k in range(24):
        val = float(f([np.array(nmean(g(f"random{k}"), WV_RANDOM_SESSIONS)) for g in getters]))
        if np.isfinite(val):
            rand.append(val)
    return {"value": point, "ci": pct_ci(draws),
            "value_floor": float(f([np.array(nmean(v, WV_RANDOM_SESSIONS)) for v in vecs])),
            "n": int(np.sum(np.isfinite(vecs[0]))), "rand": rand}


def whose_visit_cells(spans, wordings, measures, ratio=False) -> dict:
    """cells[(model, span, wording, measure, condition)] for condition S (the Assistant's own six visits to the
    zone steered), O (Maya's six visits to the zone steered) and, with ratio=True, O/S. measure: "continue",
    "avoid" (the leave question alone) or "go_minus_avoid"."""
    cells = {}
    for model, n in WV_SESSIONS.items():
        reads = load_whose_visit(model)
        boot = SessionBoot(n, WV_SEED)
        for span in spans:
            for wording in wordings:
                qc, qa = WV_WORDINGS[wording]
                for measure in measures:
                    get = {}
                    for ver in ("S", "O"):
                        if measure == "continue":
                            get[ver] = (lambda d, ver=ver: wv_slope(reads, n, ver, span, d, qc))
                        elif measure == "avoid":
                            get[ver] = (lambda d, ver=ver: wv_slope(reads, n, ver, span, d, qa))
                        else:
                            get[ver] = (lambda d, ver=ver: (wv_slope(reads, n, ver, span, d, qc) -
                                                            wv_slope(reads, n, ver, span, d, qa)) / 2)
                        cells[(model, span, wording, measure, ver)] = wv_quantity(boot, lambda v: v[0], [get[ver]])
                    if ratio:
                        cells[(model, span, wording, measure, "O/S")] = wv_quantity(
                            boot, lambda v: v[0] / v[1], [get["O"], get["S"]])
    return cells


#=================================
# 5. Shared conversation
#=================================

SH_BASE = {"olmo_32b": 160, "qwen25_32b": 80}
SH_SEED = 334
SH_RANDOM_BASE = list(range(20))
SH_CHOOSERS = {"A": "Assistant", "M": "Maya (predicted by the Assistant)", "Sam": "Sam (bystander, never visited)"}
SH_WORDINGS = {"stay/avoid": {"A": ("self_cont", "self_avoid"), "M": ("maya_cont", "maya_avoid"),
                              "Sam": ("sam_cont", "sam_avoid")},
               "sent to": {"A": ("selfsent_cont", "selfsent_avoid"), "M": ("mayasent_cont", "mayasent_avoid"),
                           "Sam": ("samsent_cont", "samsent_avoid")}}
SH_QS = sorted({q for w in SH_WORDINGS.values() for pair in w.values() for q in pair})
SH_CONDITION_LABELS = {"S": "Assistant's visits steered", "O": "Maya's visits steered"}


def load_shared(model: str) -> dict:
    """reads[(condition, span, direction, dose)] = [mixed sessions, questions] array of margins lp[0] - lp[1]."""
    nm = 2 * SH_BASE[model]
    reads = {}
    for r in read_jsonl_gz(JSONS / "shared_conversation" / "reads" / model / "reads.jsonl.gz"):
        if r["m"] != model:
            raise ValueError(f"Unexpected shared-conversation record for {model}: {r['m']}")
        key = (r["cond"], r["span"], r["dir"], float(r["pt"]))
        if key not in reads:
            reads[key] = np.full((nm, len(SH_QS)), np.nan)
        reads[key][int(r["ms"])] = [r["lp"][q][0] - r["lp"][q][1] if q in r["lp"] else np.nan for q in SH_QS]
    return reads


def sh_slope(reads, nm, condition, span, direction, question):
    base = reads.get(("-", "-", "none", 0.0))
    j = SH_QS.index(question)
    acc = np.zeros(nm)
    for x in NONZERO:
        a = reads.get((condition, span, direction, float(x)))
        if a is None or base is None:
            return np.full(nm, np.nan)
        acc = acc + x * (a[:, j] - base[:, j])
    return acc / SXX


def per_base_pair(values, nk):
    """Mean of each base session's two mixed sessions (the session and its role-swapped twin)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(np.asarray(values, float)[: 2 * nk].reshape(nk, 2), axis=1)


def sh_quantity(nk, boot, f, getters) -> dict:
    vecs = [per_base_pair(g("valence"), nk) for g in getters]
    point = float(f([np.array(nmean(v)) for v in vecs]))
    draws = np.asarray(f([boot.means(v) for v in vecs]), float)
    rand = []
    for k in range(24):
        val = float(f([np.array(nmean(per_base_pair(g(f"random{k}"), nk), SH_RANDOM_BASE)) for g in getters]))
        if np.isfinite(val):
            rand.append(val)
    return {"value": point, "ci": pct_ci(draws),
            "value_floor": float(f([np.array(nmean(v, SH_RANDOM_BASE)) for v in vecs])),
            "n": int(np.sum(np.isfinite(vecs[0]))), "rand": rand}


def shared_cells(spans, wordings, choosers, measures, ratio=False) -> dict:
    """cells[(model, span, wording, chooser, measure, condition)] for condition S (the Assistant's three visits
    steered), O (Maya's three visits steered) and, with ratio=True, O/S."""
    cells = {}
    for model, nk in SH_BASE.items():
        reads = load_shared(model)
        nm = 2 * nk
        boot = SessionBoot(nk, SH_SEED)
        for span in spans:
            for wording in wordings:
                for chooser in choosers:
                    qc, qa = SH_WORDINGS[wording][chooser]
                    for measure in measures:
                        get = {}
                        for c in ("S", "O"):
                            if measure == "continue":
                                get[c] = (lambda d, c=c: sh_slope(reads, nm, c, span, d, qc))
                            elif measure == "avoid":
                                get[c] = (lambda d, c=c: sh_slope(reads, nm, c, span, d, qa))
                            else:
                                get[c] = (lambda d, c=c: (sh_slope(reads, nm, c, span, d, qc) -
                                                          sh_slope(reads, nm, c, span, d, qa)) / 2)
                            cells[(model, span, wording, chooser, measure, c)] = sh_quantity(
                                nk, boot, lambda v: v[0], [get[c]])
                        if ratio:
                            cells[(model, span, wording, chooser, measure, "O/S")] = sh_quantity(
                                nk, boot, lambda v: v[0] / v[1], [get["O"], get["S"]])
    return cells


#=================================
# 6. Place vs thoughts vs feelings
#=================================

PTF_MODELS = ("olmo_32b", "qwen25_32b")
PTF_SEED = 362
PTF_RANDOM = 48
PTF_RANDOM_SESSIONS = list(range(40))
PTF_QUESTIONS = ("P_z", "M_z", "F_z", "P_t", "M_t", "F_t")
PTF_CONTENT = {"P": "place", "M": "thoughts", "F": "feelings"}
PTF_ANSWER = {"z": "zone-name answer", "t": "topic-word answer"}


def lse(values) -> float:
    return float(np.logaddexp.reduce(np.asarray(values, float)))


def ptf_margin(lp: dict, question: str) -> float:
    """log P(pushed side) - log P(other side), pooled over surface forms, averaged over both answer orders."""
    margins = []
    for order in (0, 1):
        v = lp[f"{question}_o{order}"]
        k = len(v) // 2
        margins.append(lse(v[:k]) - lse(v[k:]))
    return float(np.mean(margins))


def load_ptf(model: str):
    """Per-session log-odds slopes (sW, [sessions, questions]) and random-direction +-1 slopes
    (rS, [directions, sessions 0-39, questions]) under the neutral header (L0)."""
    reads = {}
    for r in read_jsonl_gz(JSONS / "place_thoughts_feelings" / "reads" / model / "reads.jsonl.gz"):
        if r["h"] == "L0":
            reads[(int(r["s"]), r["cond"], r["dir"], float(r["pt"]))] = r["lp"]
    sessions = sorted({s for s, cond, d, p in reads if cond == "-"})
    n = len(sessions)
    if sessions != list(range(n)):
        raise ValueError(f"Unexpected session numbering for {model}")
    m0 = np.array([[ptf_margin(reads[(s, "-", "none", 0.0)], q) for q in PTF_QUESTIONS] for s in range(n)])
    mv = {p: np.array([[ptf_margin(reads[(s, "W", "valence", p)], q) for q in PTF_QUESTIONS] for s in range(n)])
          for p in NONZERO}
    sW = sum(p * (mv[p] - m0) for p in NONZERO) / 2.5
    rS = np.zeros((PTF_RANDOM, len(PTF_RANDOM_SESSIONS), len(PTF_QUESTIONS)))
    for k in range(PTF_RANDOM):
        for i, s in enumerate(PTF_RANDOM_SESSIONS):
            mp = np.array([ptf_margin(reads[(s, "W", f"random{k}", 1.0)], q) for q in PTF_QUESTIONS])
            mn = np.array([ptf_margin(reads[(s, "W", f"random{k}", -1.0)], q) for q in PTF_QUESTIONS])
            rS[k, i] = (mp - mn) / 2
    return n, sW, rS


def ptf_boot_weights(n: int) -> np.ndarray:
    idx = np.random.default_rng(PTF_SEED).integers(0, n, size=(BOOT, n))
    return np.stack([np.bincount(idx[b], minlength=n) for b in range(BOOT)]).astype(float)


def ptf_cells() -> dict:
    """cells[(model, question)] = log-odds slope, its 95% CI and the 48-direction random envelope."""
    cells = {}
    for model in PTF_MODELS:
        n, sW, rS = load_ptf(model)
        weights = ptf_boot_weights(n)
        point = sW.mean(0)
        draws = (weights @ sW) / weights.sum(1, keepdims=True)
        random_slopes = rS.mean(1)
        for i, q in enumerate(PTF_QUESTIONS):
            cells[(model, q)] = {"value": float(point[i]), "ci": pct_ci(draws[:, i]), "n": n,
                                 **envelope(random_slopes[:, i])}
    return cells


#=================================
# 7. Figure rows (Figures A13 and A14)
#=================================

FIGURE_COLUMNS = ["panel", "model", "group", "x_label", "series", "series_label", "span", "estimate", "ci_low",
                  "ci_high", "random_n", "random_abs_p90", "random_abs_max", "n_sessions", "source"]
X_LABEL_A = {"S": "Own visit", "O": "Maya's visit"}
SERIES_LABEL_A = {"S": "Assistant's own visit", "O": "Maya's visit"}
X_LABEL_B = {"A": "Own choice", "M": "Predicted for Maya", "Sam": "Predicted for Sam"}


def figure_row(panel, model, group, x_label, series, series_label, span, cell, envelope_values, random_n, source):
    return {"panel": panel, "model": MODEL_LABELS[model], "group": group, "x_label": x_label, "series": series,
            "series_label": series_label, "span": span, "estimate": cell["value"], "ci_low": cell["ci"][0],
            "ci_high": cell["ci"][1], "random_n": random_n, "random_abs_p90": envelope_values["random_abs_p90"],
            "random_abs_max": envelope_values["random_abs_max"], "n_sessions": cell["n"], "source": source}


def panel_a_rows(span: str) -> list[dict]:
    """Panel A: whose visit, go-minus-avoid slope (stay/leave wording), own visits vs Maya's visits steered."""
    cells = whose_visit_cells([span], ["stay/avoid"], ["go_minus_avoid"])
    rows = []
    for model in WV_SESSIONS:
        for ver in ("S", "O"):
            cell = cells[(model, span, "stay/avoid", "go_minus_avoid", ver)]
            rows.append(figure_row("a", model, MODEL_LABELS[model], X_LABEL_A[ver], ver, SERIES_LABEL_A[ver],
                                   SPAN_LABELS[span], cell, envelope(cell["rand"]), 24, SOURCES["whose_visit"]))
    return rows


def panel_b_rows(span: str) -> list[dict]:
    """Panel B: shared conversation, go-minus-avoid slope (stay/leave wording) for the three choosers."""
    cells = shared_cells([span], ["stay/avoid"], list(SH_CHOOSERS), ["go_minus_avoid"])
    rows = []
    for model in SH_BASE:
        for chooser in SH_CHOOSERS:
            for c in ("S", "O"):
                cell = cells[(model, span, "stay/avoid", chooser, "go_minus_avoid", c)]
                rows.append(figure_row("b", model, SH_CHOOSERS[chooser], X_LABEL_B[chooser], c,
                                       SH_CONDITION_LABELS[c], SPAN_LABELS[span], cell, envelope(cell["rand"]), 24,
                                       SOURCES["shared"]))
    return rows


def panel_c_rows() -> list[dict]:
    """Panel C: place vs thoughts vs feelings, log-odds slope per question."""
    cells = ptf_cells()
    rows = []
    for model in PTF_MODELS:
        for q in PTF_QUESTIONS:
            cell = cells[(model, q)]
            content = PTF_CONTENT[q[0]]
            rows.append(figure_row("c", model, q, content[0].upper() + content[1:], PTF_ANSWER[q[2]], content,
                                   "visit passages", cell, cell, PTF_RANDOM, SOURCES["ptf"]))
    return rows
