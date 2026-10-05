#!/usr/bin/env python3
##########################################
# AI WELFARE PROJECT
##########################################
# Accounting of negative valence steering in the paper's experiments
##########################################

"""Count how much negative (and, for comparison, positive) valence steering the paper's experiments used.

Only experiments, arms and conditions whose data appear in a figure or table of the paper are
counted; the ``figures`` column names them for every row.

One row per experiment and model, and per direction class. Valence rows fill the
``negative_*`` and ``positive_*`` columns. Random directions and the non-valence concept
directions are not valence steering: they get their own rows, only where the paper shows them,
and only fill the ``nonvalence_*`` columns, so they never enter a negative-valence total.

Units
- session: one independent conversation or frozen token stream. A design that re-reads the
  same frozen conversations (the fixed-text variants) counts them again for that design.
- generated turn: one model reply generated while the steering vector was added.
- read-only turn: one conversation turn (prompt and reply) that the model processed with the
  steering vector added while reading fixed text, with no generation under steering. Each
  steered read of a session counts its steered turns once.
- check passes: further steered forward passes over turns already counted, run only as
  instrument checks within these experiments (cache-fidelity re-forwards, self-report probe
  prefills). Counted in turns.
- token positions: positions that received the steering vector in the generated and read-only
  turns above (check passes excluded), where the committed records allow it.

``count_source`` says whether the session and turn counts come from the committed per-session
or per-read run records, or from per-arm summary counts in the committed analysis files;
``not countable`` marks a reported experiment whose records are not in this repository.
Corpus generation and the zero-dose baseline passages involve no steering and are not counted.
"""

#=================================
# 1. Setup and configuration
#=================================

import json
from collections import Counter

from common import JSONS, MODEL_LABELS, label, load_json, write_csv

MODELS = list(MODEL_LABELS)
FIXED = JSONS / "fixed_text_design"
CALIBRATION = JSONS / "dose_calibration"
N_EXPOSURES = 6                # conditioned-zone turns per session in the standard designs
STAGES = ("base", "sft", "dpo", "instruct")
STAGE_LABELS = {"base": "Base", "sft": "SFT", "dpo": "DPO", "instruct": "Instruct"}

VALENCE = "valence"
RANDOM = "random directions (not valence)"
CONCEPT = "concept directions (not valence)"
RECORDS = "run records"
SUMMARY = "run records (summary counts)"

FIELDS = [
    "family", "experiment", "figures", "model", "direction", "count_source",
    "doses", "strength_rho_d",
    "n_sessions_total",
    "n_sessions_negative", "negative_turns_generated", "negative_turns_read_only",
    "negative_turns_check_passes", "negative_token_positions",
    "n_sessions_positive", "positive_turns_generated", "positive_turns_read_only",
    "positive_turns_check_passes", "positive_token_positions",
    "nonvalence_sessions", "nonvalence_turns_generated", "nonvalence_turns_read_only",
    "nonvalence_token_positions",
    "token_source", "design_check", "notes",
]

STANDARD_DOSES = (-1.0, -0.5, 0.5, 1.0)


#=================================
# 2. Helpers
#=================================

def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]

def rho_by_model():
    """Each model's full-dose ratio, as recorded with the generation-design run."""
    members = load_json(JSONS / "generation_design/seven_models/prereg.json")["members"]
    return {model: float(members[model]["op_member"]) for model in MODELS}

def fmt_number(value):
    text = f"{value:.4g}"
    return text if text.startswith("-") else "+" + text

def doses_text(doses):
    return "; ".join(fmt_number(d) for d in sorted(doses))

def strength_text(doses, rho, k=1.0):
    return "; ".join(fmt_number(d * rho * k) for d in sorted(doses))

def strength_range(rho, ks, k_names):
    """Per-position strengths rho x d x k for d in {-1, -0.5, +0.5, +1} and several k."""
    values = sorted(d * rho * k for d in STANDARD_DOSES for k in ks)
    negative = [v for v in values if v < 0]
    positive = [v for v in values if v > 0]
    return (f"{fmt_number(min(negative))} to {fmt_number(max(negative))}; "
            f"{fmt_number(min(positive))} to {fmt_number(max(positive))} "
            f"(rho x d x k, k = {', '.join(k_names)})")

def round_tokens(mean, n):
    total = mean * n
    if abs(total - round(total)) > 1e-6:
        raise ValueError(f"span mean {mean} x {n} sessions is not a whole number of tokens")
    return int(round(total))

def skeleton_spans():
    """Steered conditioned-zone turns and token positions per committed neutral skeleton."""
    spans = {}
    for model in MODELS:
        per_run = {}
        for path in sorted((FIXED / "skeletons" / model / "neutral").glob("*.sessions.jsonl")):
            for session in read_jsonl(path):
                s_turns = [(s, e) for s, e, cue in session["turn_spans"] if cue == session["cue_S"]]
                per_run[int(session["run"])] = {
                    "turns": len(s_turns), "tokens": sum(e - s for s, e in s_turns),
                    "ids_sha": session["ids_sha"]}
        spans[model] = per_run
    return spans

def blank_counts():
    return {"sessions": 0, "gen": 0, "read": 0, "check": 0, "tokens": 0}

def make_row(family, experiment, figures, model, direction, source, doses, strength, total,
             neg=None, pos=None, other=None, token_source="", design_check="", notes="",
             tokens_known=True):
    row = {"family": family, "experiment": experiment, "figures": figures, "model": model,
           "direction": direction, "count_source": source, "doses": doses,
           "strength_rho_d": strength, "n_sessions_total": total,
           "token_source": token_source if tokens_known else "",
           "design_check": design_check, "notes": notes}
    for prefix, counts in (("negative", neg), ("positive", pos)):
        if counts is None:
            continue
        row[f"n_sessions_{prefix}"] = counts["sessions"]
        row[f"{prefix}_turns_generated"] = counts["gen"]
        row[f"{prefix}_turns_read_only"] = counts["read"]
        row[f"{prefix}_turns_check_passes"] = counts["check"]
        row[f"{prefix}_token_positions"] = counts["tokens"] if tokens_known else None
    if other is not None:
        row["nonvalence_sessions"] = other["sessions"]
        row["nonvalence_turns_generated"] = other["gen"]
        row["nonvalence_turns_read_only"] = other["read"]
        row["nonvalence_token_positions"] = other["tokens"] if tokens_known else None
    return row


#=================================
# 3. Generation design (Figures 3A-C, A1, A2, A4, A7A)
#=================================

def generation_design(rho):
    family = "Generation design"
    spec = load_json(JSONS / "generation_design/seven_models/spec.json")
    reduced = load_json(JSONS / "generation_design/seven_models/reduced.json")
    baseline = Counter(row["model_key"] for row in read_jsonl(JSONS / "baselines/dose0_sessions.jsonl"))
    rows = []
    for model in MODELS:
        sessions = reduced[model]
        if any(s["n_passages"] != 2 * N_EXPOSURES for s in sessions):
            raise ValueError(f"{model}: a generation-design session does not have 12 passages")
        valenced = [s for s in sessions if s["arm"] == "valenced"]
        floor = [s for s in sessions if s["arm"] == "floor"]
        per_dose = Counter(s["point"] for s in valenced)
        floor_cells = Counter((s["dir_index"], s["point"]) for s in floor)
        total = len(valenced) + len(floor) + baseline[model]
        expected_ok = (all(per_dose[d] == spec["val_n_sessions"] for d in STANDARD_DOSES)
                       and len(floor_cells) == len(spec["floor_dirs"]) * len(STANDARD_DOSES)
                       and all(n == spec["floor_n_sessions"] for n in floor_cells.values())
                       and baseline[model] == 60)
        check = (f"matches design: {spec['val_n_sessions']} sessions per dose, "
                 f"{spec['floor_n_sessions']} per random direction and dose, 60 at dose 0"
                 if expected_ok else f"records differ from design: {dict(per_dose)}")
        neg, pos = blank_counts(), blank_counts()
        for s in valenced:
            same, flipped = (neg, pos) if s["point"] < 0 else (pos, neg)
            same["sessions"] += 1
            flipped["sessions"] += 1
            same["gen"] += N_EXPOSURES                 # live generation under steering
            same["read"] += N_EXPOSURES                # steered re-read, same sign
            flipped["read"] += N_EXPOSURES             # re-read with the sign reversed (A4)
        other = {"sessions": len(floor) + len(valenced), "gen": N_EXPOSURES * len(floor),
                 "read": N_EXPOSURES * (3 * len(floor) + len(valenced)), "tokens": None}
        notes = ("Each valenced session was generated under steering on its 6 conditioned-zone "
                 "turns, then re-read with the same steering and with the sign reversed (Figure "
                 "A4), so every valenced session also had steering of the opposite sign. Of the "
                 f"negative read-only turns, {N_EXPOSURES * per_dose[-1.0] + N_EXPOSURES * per_dose[-0.5]} "
                 "are same-sign re-reads of negatively generated sessions and "
                 f"{N_EXPOSURES * per_dose[0.5] + N_EXPOSURES * per_dose[1.0]} are sign-reversed re-reads "
                 "of positively generated sessions. The choice was read from the live cache "
                 "with steering off. Steered turns cover the user prompt and the reply "
                 "(replies capped at 70 tokens); only total sequence lengths are recorded, so "
                 "token positions are not counted.")
        rows.append(make_row(
            family, "Steering during passage generation, with steered and sign-reversed re-reads",
            "3A-C, A1, A2, A4, A7A", label(model), VALENCE, RECORDS,
            doses_text(STANDARD_DOSES), strength_text(STANDARD_DOSES, rho[model]), total,
            neg=neg, pos=pos, design_check=check, notes=notes, tokens_known=False))
        rows.append(make_row(
            family, "Steering during passage generation, with steered and sign-reversed re-reads",
            "3B-C, A2, A4", label(model), RANDOM, RECORDS,
            doses_text(STANDARD_DOSES), "norm-matched to valence", total, other=other,
            design_check=check,
            notes=("640 sessions generated under 8 random directions (generated turns), each "
                   "re-read with the same direction, its sign reversed and another random "
                   "direction; every valenced session also had one random-direction re-read."),
            tokens_known=False))
    return rows


#=================================
# 4. Fixed-text design (Figures 3D, A3, A5, A7)
#=================================

def fixed_text_main(rho, spans):
    family = "Fixed-text design"
    spec = load_json(FIXED / "neutral_passages/spec.json")
    reduced = load_json(FIXED / "neutral_passages/reduced.json")
    rows = []
    for model in MODELS:
        sessions = reduced["sessions"][model]
        reads = reduced["reads"][model]
        neutral = [s for s in sessions if s["arm"] == "neutral"]
        steered = [s for s in sessions if s["arm"] == "steered"]
        for s in neutral:
            skeleton = spans[model][int(s["run"])]
            if skeleton["ids_sha"] != s["ids_sha"] or skeleton["turns"] != N_EXPOSURES:
                raise ValueError(f"{model} run {s['run']}: skeleton does not match the read session")

        def count(rows_, arm, sign):
            counts = blank_counts()
            runs = set()
            for r in rows_:
                if r["arm"] != arm or r["direction_kind"] != "valenced" or r["point"] * sign <= 0:
                    continue
                runs.add((r["gen_point"], r["run"]))
                counts["read"] += N_EXPOSURES
                passes = (2 if r.get("fresh_margin") is not None else 0) + \
                         (1 if r.get("probe_margin") is not None else 0)
                counts["check"] += N_EXPOSURES * passes
                if arm == "neutral":
                    counts["tokens"] += spans[model][int(r["run"])]["tokens"]
            counts["sessions"] = len(runs)
            return counts

        neg, pos = count(reads, "neutral", -1), count(reads, "neutral", +1)
        n_neutral = len(neutral)
        expected = spec["n_neutral"]
        check = (f"matches design: {expected} neutral sessions, each read at 4 nonzero doses"
                 if n_neutral == expected and neg["read"] == N_EXPOSURES * 2 * expected
                 else f"records differ from design ({n_neutral} of {expected} sessions)")
        rows.append(make_row(
            family, "Fixed unsteered passages, steering only while re-reading the conditioned-zone turns",
            "3D, A3, A5, A7", label(model), VALENCE, RECORDS,
            doses_text(STANDARD_DOSES), strength_text(STANDARD_DOSES, rho[model]), n_neutral,
            neg=neg, pos=pos, token_source=RECORDS, design_check=check,
            notes=("Nothing is generated under steering. The choice is scored with steering off. "
                   "Check passes: two cache-fidelity forwards at doses -1 and +1 and one "
                   "self-report probe prefill per read, as recorded per read. Token positions "
                   "from the committed skeleton turn spans.")))
        rnd = [r for r in reads if r["direction_kind"] == "random"]
        other = {"sessions": len({r["run"] for r in rnd}), "gen": 0,
                 "read": N_EXPOSURES * len(rnd),
                 "tokens": sum(spans[model][int(r["run"])]["tokens"] for r in rnd)}
        rows.append(make_row(
            family, "Fixed unsteered passages, steering only while re-reading the conditioned-zone turns",
            "3D, A3, A5, A14", label(model), RANDOM, RECORDS,
            doses_text(STANDARD_DOSES), "norm-matched to valence", n_neutral, other=other,
            token_source=RECORDS,
            design_check=("matches design: 24 directions x 4 doses on 40 sessions"
                          if len(rnd) == 24 * 4 * spec["n_floor"] else "records differ from design"),
            notes="24 random directions read on the first 40 neutral skeletons."))

        # The same design on passages generated under steering (Figure A7 panel B).
        neg_s, pos_s = count(reads, "steered", -1), count(reads, "steered", +1)
        n_gen_neg = sum(1 for s in steered if s["gen_point"] < 0)
        n_gen_pos = sum(1 for s in steered if s["gen_point"] > 0)
        neg_s["gen"], pos_s["gen"] = N_EXPOSURES * n_gen_neg, N_EXPOSURES * n_gen_pos
        neg_s["sessions"] = pos_s["sessions"] = len(steered)
        expected_steer = spec["n_steer"] * len(spec["steer_gen_doses"])
        rows.append(make_row(
            family, "Passages generated under steering at d = -1 or +1, then re-read at every dose",
            "A7B", label(model), VALENCE, RECORDS,
            doses_text(STANDARD_DOSES), strength_text(STANDARD_DOSES, rho[model]), len(steered),
            neg=neg_s, pos=pos_s, design_check=(
                f"matches design: {spec['n_steer']} sessions generated at each of d = -1 and +1"
                if len(steered) == expected_steer else "records differ from design"),
            notes=(f"{n_gen_neg} sessions generated at d = -1 and {n_gen_pos} at d = +1 (6 "
                   "conditioned-zone turns each); every session is then re-read at both negative "
                   "and both positive doses, so each has steering of both signs. Skeleton spans "
                   "for these sessions are not committed, so token positions are not counted."),
            tokens_known=False))
    return rows


#=================================
# 5. Fixed-text variants with per-read records (Figures A5, A6)
#=================================

def avoid_prompt(rho, spans):
    family = "Fixed-text design"
    rows = []
    for model in MODELS:
        reads = read_jsonl(FIXED / "avoid_prompt/reads" / model / "reads.jsonl")
        rebuild = load_json(FIXED / "avoid_prompt/reads" / model / "rebuild.json")
        if {r["stage"] for r in reads} != {"avoid"}:
            raise ValueError(f"{model}: unexpected stage in avoid-prompt reads")
        neg, pos, other = blank_counts(), blank_counts(), blank_counts()
        neg_runs, pos_runs, other_runs = set(), set(), set()
        for r in reads:
            if not r["n_steered_spans"]:
                continue
            skeleton = spans[model][int(r["run"])]
            if skeleton["ids_sha"] != r["ids_sha"] or skeleton["turns"] != r["n_steered_spans"]:
                raise ValueError(f"{model} run {r['run']}: avoid read does not match its skeleton")
            if r["direction_kind"] == "valenced":
                target, runs = (neg, neg_runs) if r["point"] < 0 else (pos, pos_runs)
            else:
                target, runs = other, other_runs
            runs.add(r["run"])
            target["read"] += r["n_steered_spans"]
            target["tokens"] += skeleton["tokens"]
        neg["sessions"], pos["sessions"], other["sessions"] = len(neg_runs), len(pos_runs), len(other_runs)
        n_ok = rebuild["n_ok"]
        check = (f"{n_ok} of {rebuild['n_selected']} planned sessions; "
                 f"{rebuild['n_selected'] - n_ok} skeletons could not be rebuilt byte-identically "
                 "and were not read" if n_ok != rebuild["n_selected"]
                 else f"matches design: {n_ok} sessions")
        experiment = "Fixed-text design with the final question asking which zone to avoid"
        rows.append(make_row(
            family, experiment, "A5", label(model), VALENCE, RECORDS,
            doses_text(STANDARD_DOSES), strength_text(STANDARD_DOSES, rho[model]), n_ok,
            neg=neg, pos=pos, token_source=RECORDS, design_check=check,
            notes=("Re-reads the committed neutral skeletons; nothing is generated. One steered "
                   "prefill per read, no check passes.")))
        rows.append(make_row(
            family, experiment, "A5", label(model), RANDOM, RECORDS,
            doses_text(STANDARD_DOSES), "norm-matched to valence", n_ok, other=other,
            token_source=RECORDS, design_check=check,
            notes="24 random directions on the first 40 skeletons (fewer where skeletons failed to rebuild)."))
    return rows

def recall(rho, spans):
    family = "Fixed-text design"
    rebuild = load_json(FIXED / "recall/rebuild.json")["members"]
    rows = []
    for model in MODELS:
        reads = []
        for path in sorted((FIXED / "recall/reads" / model).glob("recall_*.jsonl")):
            reads += read_jsonl(path)
        conditions = {}
        for r in reads:
            key = (r["run"], r["direction"], r["point"])
            conditions.setdefault(key, r)
            if r.get("choice_margin") is not None:
                conditions[key] = r
        neg, pos = blank_counts(), blank_counts()
        neg_runs, pos_runs = set(), set()
        for (run, _, point), r in sorted(conditions.items(), key=lambda item: str(item[0])):
            if not r["n_steered_spans"] or r["direction_kind"] != "valenced":
                continue                               # Figure A6 shows the valence direction only
            skeleton = spans[model][int(run)]
            if skeleton["ids_sha"] != r["ids_sha"] or skeleton["turns"] != r["n_steered_spans"]:
                raise ValueError(f"{model} run {run}: recall read does not match its skeleton")
            target, runs = (neg, neg_runs) if point < 0 else (pos, pos_runs)
            if r.get("choice_margin") is not None:
                target["check"] += r["n_steered_spans"]
            runs.add(run)
            target["read"] += r["n_steered_spans"]
            target["tokens"] += skeleton["tokens"]
        neg["sessions"], pos["sessions"] = len(neg_runs), len(pos_runs)
        info = rebuild[model]
        check = (f"{info['n_ok']} of {info['n_selected']} planned sessions; "
                 f"{info['n_selected'] - info['n_ok']} skeletons could not be rebuilt and were not read"
                 if info["n_ok"] != info["n_selected"] else f"matches design: {info['n_ok']} sessions")
        if len(reads) != info["rows"]:
            check += f"; {len(reads)} rows against {info['rows']} in rebuild.json"
        experiment = "Fixed-text design followed by word-for-word recall of a passage"
        rows.append(make_row(
            family, experiment, "A6", label(model), VALENCE, RECORDS,
            doses_text(STANDARD_DOSES), strength_text(STANDARD_DOSES, rho[model]), info["n_ok"],
            neg=neg, pos=pos, token_source=RECORDS, design_check=check,
            notes=("One steered prefill per condition; the recall replies for both zones are then "
                   "generated with steering off, from that steered cache. Check passes: one steered "
                   "re-read of the full recorded sequence per valence condition (choice-margin check).")))
    return rows


#=================================
# 6. Fixed-text variants with summary records (Figures A8-A11)
#=================================

def summary_family(rho, *, family, experiment, figures, model, arms, total, check, notes,
                   strength=None, include_random=True):
    """Counts for a fixed-text run whose records give per-arm session counts and mean spans.

    ``arms`` holds ``(n_sessions, n_floor_sessions, n_exposures, span_mean, k, read_passes)``.
    Every main session is read at d = -1, -0.5, +0.5 and +1; each of those reads carries a
    self-report probe prefill, and the reads at d = -1 and +1 two cache-fidelity forwards.
    """
    neg, pos = blank_counts(), blank_counts()
    other = blank_counts()
    for n, n_floor, exposures, span_mean, _k, read_passes in arms:
        for counts in (neg, pos):
            counts["sessions"] += n
            counts["read"] += n * 2 * exposures * read_passes
            counts["check"] += n * (2 + 2) * exposures
            counts["tokens"] += round_tokens(span_mean, n) * 2 * read_passes
        other["sessions"] += n_floor
        other["read"] += n_floor * 24 * 4 * exposures
    strengths = strength or strength_text(STANDARD_DOSES, rho[model])
    rows = [make_row(family, experiment, figures, label(model), VALENCE, SUMMARY,
                     doses_text(STANDARD_DOSES), strengths, total, neg=neg, pos=pos,
                     token_source="run records (per-arm mean steered span x sessions)",
                     design_check=check, notes=notes)]
    if include_random:
        rows.append(make_row(family, experiment, figures, label(model), RANDOM, SUMMARY,
                             doses_text(STANDARD_DOSES), "norm-matched to valence", total,
                             other=other, design_check=check,
                             notes="24 random directions x 4 doses on the floor sessions; spans for the floor subset are not recorded separately.",
                             tokens_known=False))
    return rows

def check_reads(per_arm, arms_used):
    """Confirm that each arm's recorded read count equals 5 reads per session plus the floor."""
    for name in arms_used:
        entry = per_arm[name]
        expected = entry["n_sessions"] * 5 + entry["n_floor_sessions"] * 96
        if entry["reads"] != expected:
            raise ValueError(f"{name}: {entry['reads']} reads recorded, {expected} expected")
        if entry["n_sessions"] != entry["expected_sessions"]:
            return False
    return True

def check_fidelity(instrument, entries):
    """Fidelity forwards run at d = -1, 0, +1 on main sessions and at d = +/-1 on the floor.

    The recorded fidelity-read total covers every arm of a run, so ``entries`` are all of the
    run's arms; agreement confirms the check-pass rule applied to the counted arms.
    """
    expected = sum(e["n_sessions"] * 3 + e["n_floor_sessions"] * 48 for e in entries)
    if instrument["n_adjudicable_reads"] != expected:
        raise ValueError(f"fidelity-read total {instrument['n_adjudicable_reads']} != {expected}")

def span_sweep(rho):
    analysis = load_json(FIXED / "span_sweep/analysis.json")
    rows = []
    for model in MODELS:
        per_arm = analysis["completeness"]["per_member"][model]
        spans = analysis["spans"][model]
        arms = ["bare", "sentence", "passage"]
        complete = check_reads(per_arm, arms)
        data = [(per_arm[a]["n_sessions"], per_arm[a]["n_floor_sessions"], N_EXPOSURES,
                 spans[a]["steered_span_tokens_mean"], 1.0, 1) for a in arms]
        total = sum(per_arm[a]["n_sessions"] for a in arms)
        check_fidelity(analysis["members"][model]["instrument"], per_arm.values())
        rows += summary_family(
            rho, family="Fixed-text design",
            experiment="Steered span: bare zone line, fixed sentence, or model passage",
            figures="A8", model=model, arms=data, total=total,
            check=("matches design: " + ", ".join(f"{a} {per_arm[a]['n_sessions']}" for a in arms)
                   + " sessions" if complete else "records differ from design"),
            notes=("No generation. Bare and sentence arms are new fixed token streams; the passage "
                   "arm re-reads the neutral skeletons. Check passes: probe prefill at every "
                   "nonzero dose and two fidelity forwards at d = -1 and +1 (per-read records not "
                   "committed; the recorded fidelity-read totals agree with this rule)."))
    return rows

def exposure_sweep(rho):
    analysis = load_json(FIXED / "exposure_sweep/analysis.json")
    rows = []
    arms = analysis["sweep_arms"]                      # bare_e1, bare_e2, bare_e3, bare_e6 (Figure A9)
    if [analysis["arm_exposures"][a] for a in arms] != [1, 2, 3, 6]:
        raise ValueError(f"unexpected exposure-sweep arms: {arms}")
    for model in MODELS:
        per_arm = analysis["completeness"]["per_member"][model]
        spans = analysis["spans"][model]
        complete = check_reads(per_arm, arms)
        data = [(per_arm[a]["n_sessions"], per_arm[a]["n_floor_sessions"], spans[a]["n_exposures"],
                 spans[a]["steered_span_tokens_mean"], 1.0, 1) for a in arms]
        total = sum(per_arm[a]["n_sessions"] for a in arms)
        check_fidelity(analysis["members"][model]["instrument"], per_arm.values())
        rows += summary_family(
            rho, family="Fixed-text design", experiment="Number of exposures to each zone (1, 2, 3 or 6)",
            figures="A9", model=model, arms=data, total=total,
            check=("matches design: 480 sessions in each of the 4 arms"
                   if complete else "records differ from design"),
            notes=("Arms bare_e1, bare_e2, bare_e3 and bare_e6, as plotted. Steered turns per read "
                   "equal the number of exposures. Check passes as in the span sweep."))
    return rows

def strength_ladder(rho):
    analysis = load_json(FIXED / "strength_ladder/analysis.json")
    rows = []
    arms = ["e1_k1", "e6_ksixth"]                      # the two conditions of Figure A10A
    for model in MODELS:
        per_arm = analysis["completeness"]["per_member"][model]
        spans = analysis["spans"][model]
        complete = check_reads(per_arm, arms)
        if [(spans[a]["n_exposures"], spans[a]["k"]) for a in arms] != [(1, 1.0), (6, 1 / 6)]:
            raise ValueError(f"{model}: unexpected exposures or strength in the A10A arms")
        data = [(per_arm[a]["n_sessions"], per_arm[a]["n_floor_sessions"], spans[a]["n_exposures"],
                 spans[a]["steered_span_tokens_mean"], spans[a]["k"], 1) for a in arms]
        strengths = strength_range(rho[model], [spans[a]["k"] for a in arms], ["1", "1/6"])
        total = sum(per_arm[a]["n_sessions"] for a in arms)
        check_fidelity(analysis["members"][model]["instrument"], per_arm.values())
        rows += summary_family(
            rho, family="Fixed-text design",
            experiment="One exposure at full strength or six exposures at one-sixth strength",
            figures="A10A", model=model, arms=data, total=total, strength=strengths,
            check=("matches design: 320 sessions in each of the 2 arms"
                   if complete else "records differ from design"),
            notes=("Arms e1_k1 and e6_ksixth, as plotted. Assistant turns are empty and a fixed "
                   "unsteered priming exchange precedes the zones. Strengths are rho x d x k per "
                   "position. Check passes as in the span sweep."),
            include_random=False)
    return rows

def strength_ladder_extension(rho):
    analysis = load_json(FIXED / "strength_ladder_extension/analysis.json")
    rows = []
    for model in ("olmo_32b", "qwen3_14b", "llama31_8b"):
        spans = analysis["spans"][model]
        instrument = analysis["members"][model]["instrument"]
        arms = list(spans)
        n_main = sum(spans[a]["n_sessions"] for a in arms)
        n_floor = 80 * len(arms)
        reads = sum(spans[a]["n_sessions"] * 5 for a in arms) + n_floor * 96
        if instrument["n_sessions"] != n_main or instrument["n_reads"] != reads:
            raise ValueError(f"{model}: extension instrument counts differ from the span records")
        data = [(spans[a]["n_sessions"], 80, spans[a]["n_exposures"],
                 spans[a]["steered_span_tokens_mean"], spans[a]["k"], 1) for a in arms]
        strengths = strength_range(rho[model], [spans[a]["k"] for a in arms],
                                   [analysis["grid"][a]["k_name"] for a in arms])
        if instrument["n_adjudicable_reads"] != n_main * 3 + n_floor * 48:
            raise ValueError(f"{model}: extension fidelity-read total differs from the rule")
        completeness = analysis["completeness"]["members"]
        listed = "; completeness block lists only OLMo-2-32B, the instrument block confirms all arms" \
            if model not in completeness else ""
        rows += summary_family(
            rho, family="Fixed-text design",
            experiment="Six exposures at per-exposure strength k from 1 down to 1/32",
            figures="A10B", model=model, arms=data, total=n_main, strength=strengths,
            check=f"matches design: {n_main} sessions, {reads} reads{listed}",
            notes=("Arms " + ", ".join(arms) + ", as plotted. Assistant turns are empty. "
                   "Strengths are rho x d x k per position. Check passes as in the span sweep."),
            include_random=False)
    return rows

def kv_splice(rho):
    analysis = load_json(FIXED / "kv_splice/analysis.json")
    spec = load_json(FIXED / "kv_splice/spec.json")
    rows = []
    arm = "e1_k1"                                      # the arm of Figure A11
    grid = spec["grid"][arm]
    n, n_floor, exposures = grid["n_main"], grid["n_floor"], grid["exposures"]
    if (exposures, grid["k"]) != (1, 1.0):
        raise ValueError("unexpected exposures or strength in the A11 arm")
    for model in ("olmo_32b", "qwen3_14b", "llama31_8b"):
        completeness = analysis["completeness"]["per_member"][model]
        spans = analysis["members"][model]["spans"]
        if completeness["sessions_per_arm"][arm] != n:
            raise ValueError(f"{model} {arm}: kv-splice session count differs from design")
        full_reads = completeness["reads_per_arm_condition"][f"{arm}|full"]
        if full_reads != n * 5 + n_floor * 96:
            raise ValueError(f"{model} {arm}: kv-splice full-condition reads differ from design")
        tokens = round_tokens(spans[arm]["steered_span_tokens_mean"], n)
        neg, pos = blank_counts(), blank_counts()
        for counts in (neg, pos):
            counts["sessions"] = n
            counts["read"] = n * 2 * 2 * exposures      # 2 doses x (prefix donor + full read)
            counts["check"] = n * 4 * exposures         # 2 probe prefills + 2 fidelity forwards
            counts["tokens"] = tokens * 2 * 2
        # The recorded fidelity-read total covers every arm of the run.
        if analysis["members"][model]["fidelity"]["n"] != sum(
                g["n_main"] * 3 + g["n_floor"] * 48 for g in spec["grid"].values()):
            raise ValueError(f"{model}: kv-splice fidelity-read total differs from the rule")
        check = (f"matches design: {n} sessions, {full_reads} full-condition reads"
                 if completeness["complete"] else "records differ from design")
        rows.append(make_row(
            "Fixed-text design", "Keys and values: steered and unsteered caches spliced together",
            "A11", label(model), VALENCE, SUMMARY,
            doses_text(STANDARD_DOSES), strength_text(STANDARD_DOSES, rho[model]), n,
            neg=neg, pos=pos,
            token_source="run records (per-arm steered span x sessions)", design_check=check,
            notes=("Arm e1_k1, as plotted. Per session and nonzero dose there are two steered "
                   "passes over the conditioned-zone turn: the prefix cache the key/value "
                   "conditions are spliced from, and the full read. The spliced reads add no "
                   "steered pass. Check passes: probe prefill at each nonzero dose and two "
                   "fidelity forwards at d = -1 and +1.")))
    return rows


#=================================
# 7. Checkpoint ladder (Figures 4, A12)
#=================================

def checkpoint_ladder():
    reduced = load_json(JSONS / "checkpoint_ladder/reduced.json")
    sessions = reduced["sessions"]
    rows = []
    streams = {}
    for s in sessions:
        if s["n_passages"] != 2 * N_EXPOSURES:
            raise ValueError("a checkpoint-ladder stream does not have 12 passages")
        streams[(s["direction_kind"], s.get("dir_index"), s["dose"], s["run"])] = s
    doses = sorted({s["dose"] for s in sessions})
    for stage in STAGES:
        stage_rows = [s for s in sessions if s["stage"] == stage]
        arms = Counter(s["arm"] for s in stage_rows)
        neg, pos = blank_counts(), blank_counts()
        for s in stage_rows:
            if s["direction_kind"] != "valenced":
                continue                               # Figures 4 and A12 show the valence direction only
            counts = neg if s["dose"] < 0 else pos
            counts["read"] += N_EXPOSURES
            if s.get("nt_margin_full") is not None:
                counts["check"] += N_EXPOSURES
        val_streams = [k for k in streams if k[0] == "valenced"]
        neg["sessions"] = sum(1 for k in val_streams if k[2] < 0)
        pos["sessions"] = sum(1 for k in val_streams if k[2] > 0)
        if stage == "instruct":
            neg["gen"] = N_EXPOSURES * neg["sessions"]
            pos["gen"] = N_EXPOSURES * pos["sessions"]
        check = ("matches design: 20 streams per dose and direction, re-read with both vectors"
                 if reduced["design"]["complete"] and all(n == 720 for n in arms.values())
                 and len(arms) == 2 else "records differ from design")
        model = f"OLMo-2-32B {STAGE_LABELS[stage]}"
        generated = ("The Instruct checkpoint generated all streams under steering with the "
                     "Instruct vector, counted in this row only. " if stage == "instruct" else
                     "Generated turns are counted in the Instruct row. ")
        notes = (generated + "This checkpoint re-read every stream once with the Instruct vector "
                 "(Figure 4) and once with its own vector (Figure A12). Check passes: one steered "
                 "full forward per steered re-read (cache-fidelity reference). Turn spans were "
                 "not kept in the committed records, so token positions are not counted.")
        rows.append(make_row(
            "Checkpoint ladder", "Instruct-generated streams re-read by each OLMo-2-32B checkpoint",
            "4, A12", model, VALENCE, RECORDS, doses_text(doses), strength_text(doses, 0.3),
            len(val_streams), neg=neg, pos=pos, design_check=check, notes=notes, tokens_known=False))
    return rows


#=================================
# 8. Self-administration and removal (Figures 5, A13)
#=================================

def lever():
    conversations = read_jsonl(JSONS / "lever/conversations.jsonl")
    rows = []
    for prompt, figures in (("zone", "5, A13"),):     # the exposure prompt of Figures 5 and A13
        convs = [c for c in conversations if c["prompt"] == prompt]
        cells = Counter(c["cond"] for c in convs)
        neg, pos, other = blank_counts(), blank_counts(), blank_counts()
        neg_conv, pos_conv, rand_conv = set(), set(), set()
        neg_default = neg_adjust = neg_exposure = 0
        design_max = 0
        for c in convs:
            for t in c["turns"]:
                role = t["imposed_role"]
                if role == "zero":
                    continue
                if role == "neg":
                    neg["gen"] += 1
                    neg_conv.add(c["cell"] + str(c["conv"]))
                    if t["phase"] == "exposure":
                        neg_exposure += 1
                    elif t["source"] == "operator":
                        neg_default += 1
                    elif t["source"] == "model_adjust":
                        neg_adjust += 1
                elif role == "pos":
                    pos["gen"] += 1
                    pos_conv.add(c["cell"] + str(c["conv"]))
                else:
                    other["gen"] += 1
                    rand_conv.add(c["cell"] + str(c["conv"]))
            if c["op_role"] == "neg":
                design_max += 7
        neg["sessions"], pos["sessions"], other["sessions"] = len(neg_conv), len(pos_conv), len(rand_conv)
        check = ("matches design: 200 conversations in each of 7 conditions"
                 if len(cells) == 7 and all(n == 200 for n in cells.values()) else
                 f"records differ from design: {dict(cells)}")
        notes = (f"Negative steered replies: {neg_exposure} exposure turns, {neg_default} offer "
                 f"rounds where the default negative steering was re-imposed (the model can reset "
                 f"it), and {neg_adjust} offer turns where the model applied negative steering to "
                 f"itself with adjust_context. Had the model never reset, the default would have "
                 f"been re-imposed on {design_max} offer rounds (7 per conversation). In every steered turn the whole conversation so far is "
                 "re-encoded under steering, so the steered positions include the context as well "
                 "as the reply; token counts are not recorded (only characters). Doses are the "
                 "imposed ones; self-administered steering uses the requested intensity times the "
                 "condition's dose, never more.")
        experiment = "Self-administration and removal tools (zone exposure prompt)"
        rows.append(make_row(
            "Self-administration and removal", experiment, figures, label("olmo_32b"), VALENCE,
            RECORDS, "-1; -0.5; +0.5; +1", "-0.3; -0.15; +0.15; +0.3", len(convs),
            neg=neg, pos=pos, design_check=check, notes=notes
            + " Positive turns include adjust_context calls in the zero-dose condition, whose tool applies positive steering.",
            tokens_known=False))
        rows.append(make_row(
            "Self-administration and removal", experiment, figures, label("olmo_32b"), RANDOM,
            RECORDS, "+0.5; +1 (magnitude only)", "norm-matched to valence", len(convs),
            other=other, design_check=check,
            notes="16 random directions; imposed and self-administered random-direction turns.",
            tokens_known=False))
    return rows


#=================================
# 9. Concept controls (Figure A14, Table A1)
#=================================

def concept_controls(rho, spans):
    source = FIXED / "concept_control"
    reads = read_jsonl(source / "reads/reads288.jsonl")
    floor = read_jsonl(source / "floor/reads290.jsonl")
    rows = []
    for model in MODELS:
        model_reads = [r for r in reads if r["member"] == model]
        runs = {r["run"] for r in model_reads}
        neg, pos, other = blank_counts(), blank_counts(), blank_counts()
        neg_runs, pos_runs, other_runs = set(), set(), set()
        for r in model_reads:
            if not r["n_steered_spans"]:
                continue
            skeleton = spans[model][int(r["run"])]
            if skeleton["ids_sha"] != r["ids_sha"] or skeleton["turns"] != r["n_steered_spans"]:
                raise ValueError(f"{model} run {r['run']}: concept read does not match its skeleton")
            if r["direction"] == "valence":
                target, target_runs = (neg, neg_runs) if r["point"] < 0 else (pos, pos_runs)
            else:
                target, target_runs = other, other_runs
            target_runs.add(r["run"])
            target["read"] += r["n_steered_spans"]
            target["tokens"] += skeleton["tokens"]
        neg["sessions"], pos["sessions"], other["sessions"] = len(neg_runs), len(pos_runs), len(other_runs)
        experiment = "Concept directions on the fixed-text design, with a valence comparison"
        rows.append(make_row(
            "Concept controls", experiment, "A14", label(model), VALENCE, RECORDS,
            doses_text(STANDARD_DOSES), strength_text(STANDARD_DOSES, rho[model]), len(runs),
            neg=neg, pos=pos, token_source=RECORDS,
            design_check=f"{len(runs)} of 160 skeletons rebuilt and read",
            notes="The valence line of Figure A14 re-read on the same neutral skeletons as the concept directions; one steered prefill per read."))
        rows.append(make_row(
            "Concept controls", experiment, "A14", label(model), CONCEPT, RECORDS,
            doses_text(STANDARD_DOSES), "norm-matched to valence", len(runs), other=other,
            token_source=RECORDS, design_check=f"{len(runs)} of 160 skeletons rebuilt and read",
            notes="Indoor/outdoor, large/small and fast/slow, each at both poles and two strengths."))
        if model == "qwen25_32b":
            rnd = [r for r in floor if r["n_steered_spans"]]
            for r in rnd:
                skeleton = spans[model][int(r["run"])]
                if skeleton["ids_sha"] != r["ids_sha"]:
                    raise ValueError(f"run {r['run']}: Qwen2.5 floor read does not match its skeleton")
            floor_counts = {"sessions": len({r["run"] for r in rnd}), "gen": 0,
                            "read": sum(r["n_steered_spans"] for r in rnd),
                            "tokens": sum(spans[model][int(r["run"])]["tokens"] for r in rnd)}
            rows.append(make_row(
                "Concept controls", "24 random directions on all 160 Qwen2.5-32B conversations",
                "A14", label(model), RANDOM, RECORDS, doses_text(STANDARD_DOSES),
                "norm-matched to valence", floor_counts["sessions"], other=floor_counts,
                token_source=RECORDS, design_check="matches design: 160 sessions x 24 directions x 4 doses"
                if len(rnd) == 160 * 96 else "records differ from design", notes=""))

        # Forced-choice concept-word probe (Table A1, which tabulates the three concepts only).
        probe = read_jsonl(source / "arrival" / model / "arrival_fc.jsonl")
        other, other_runs = blank_counts(), set()
        for r in probe:
            if not r["point"] or r["direction"] == "valence":
                continue
            other_runs.add(r["run"])
            other["read"] += 1
            other["tokens"] += r["q_len"] + sum(max(0, n - 1) for n in r["n_tokens_forms"].values())
        other["sessions"] = len(other_runs)
        probe_runs = len({r["run"] for r in probe})
        rows.append(make_row(
            "Concept controls", "Forced-choice concept-word probe after unsteered fixed text",
            "Table A1", label(model), CONCEPT, RECORDS,
            "-1; +1", "norm-matched to valence", probe_runs, other=other, token_source=RECORDS,
            design_check=f"{probe_runs} of 160 skeletons rebuilt and probed",
            notes=("Three concepts, both poles. The conversation is read without steering; "
                   "steering covers only the probe question turn and the scoring of the answer "
                   "words. Token positions: question tokens plus any answer-word tokens beyond "
                   "the first.")))
    return rows


#=================================
# 10. Dose calibration (Table A2)
#=================================

def dose_calibration():
    cells = load_json(CALIBRATION / "dose_scan_cells.json")
    scan = load_json(CALIBRATION / "dose_scan.json")
    rows = []
    for model in MODELS:
        if model not in cells:
            rows.append(make_row(
                "Dose calibration", "Scan of candidate strengths that set rho",
                "Table A2", label(model), VALENCE, "not countable", "", "", None,
                design_check="not countable from this repository",
                notes=("The scan that set rho = 0.30 for this model is not in this repository's "
                       "records, so its steering cannot be counted."),
                tokens_known=False))
            continue
        neg, pos = blank_counts(), blank_counts()
        neg_doses, pos_doses = [], []
        mismatch = []
        for name, cell in sorted(cells[model].items()):
            if cell["role"] == "zero":
                continue
            counts, doses = (neg, neg_doses) if cell["role"] == "neg" else (pos, pos_doses)
            doses.append(cell["dose"])
            n_conv = len(cell["welfare_conv"])
            turns = len(cell["conv_of_text"])
            if n_conv != 6 or turns != 18:
                mismatch.append(f"{name}: {n_conv} conversations, {turns} turns with text")
            counts["sessions"] += n_conv
            counts["gen"] += turns + 2 * 4 + len(cell["tool_calls"])
            counts["read"] += 2 * len(cell["margin"])
        neg_text = "; ".join(fmt_number(-d) for d in sorted(neg_doses, reverse=True))
        pos_text = "; ".join(fmt_number(d) for d in sorted(pos_doses))
        check = ("matches design: 6 conversations x 3 turns per cell, "
                 f"{scan[model]['n_cells']} cells" if not mismatch and scan[model]["scan_complete"]
                 else "; ".join(mismatch) or "records differ from design")
        rows.append(make_row(
            "Dose calibration", "Scan of candidate strengths that set rho", "Table A2",
            label(model), VALENCE, RECORDS, "candidate strengths (rho is chosen here)",
            neg_text + "; " + pos_text, len(cells[model]) * 6,
            neg=neg, pos=pos, design_check=check,
            notes=("Per strength and sign: 6 conversations of 3 generated turns (up to 150 tokens), "
                   "8 short self-report replies (from the configuration; only parsed answers are "
                   "recorded) and 4 tool-call replies, all generated with the vector added at every "
                   "position of the re-encoded conversation; read-only turns are the forced "
                   "self-report scoring passes (18 items x 2 answers). The arrival check re-encodes "
                   "the replies without steering. Token counts are not recorded."),
            tokens_known=False))
    return rows


#=================================
# 11. Save the table
#=================================

def main():
    rho = rho_by_model()
    spans = skeleton_spans()
    rows = []
    rows += generation_design(rho)
    rows += fixed_text_main(rho, spans)
    rows += avoid_prompt(rho, spans)
    rows += recall(rho, spans)
    rows += span_sweep(rho)
    rows += exposure_sweep(rho)
    rows += strength_ladder(rho)
    rows += strength_ladder_extension(rho)
    rows += kv_splice(rho)
    rows += checkpoint_ladder()
    rows += lever()
    rows += concept_controls(rho, spans)
    rows += dose_calibration()
    write_csv("negative_steering_exposure.csv", rows, FIELDS)

if __name__ == "__main__":
    main()
