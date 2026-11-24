##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Table A4: Whose-valence ratios under every readout
##########################################

"""Maya's-visits slope / own-visits slope under each readout, passage-only span, no system prompt, the Assistant's
own choice.

Run from the repository root with python3 create_tables/tableA4.py. Requires numpy.
Reads experiment_results_json/whose_valence/ and writes experiment_results_csv/tableA4.csv (full precision) and
tables/tableA4.tex (the paper's LaTeX table, ratios and CIs at two decimals, using booktabs and tabularx).

Rows
* Whose-visit run (matched text), all three models: Maya's-visits slope / own-visits slope (Maya's six visits to the
  zone steered / the Assistant's own six visits to the zone steered) under six readouts: stay/leave go-minus-avoid
  (registered), continue only, leave only, and the same three for the "sent to" wording.
* Shared-conversation run, OLMo-2-32B and Qwen2.5-32B: Maya's three visits steered / the Assistant's three visits
  steered, for go-minus-avoid (registered), continue only and leave only (stay/leave wording).

Each ratio and its CI use the same joint session bootstrap as the registered ratio (whose visit: 2,000 draws,
seed 333; shared conversation: 2,000 draws over base pairs, seed 334).

Stability flag: a ratio is flagged when its denominator's 95% CI includes 0 or its end nearest 0 is below half the
denominator's point estimate in magnitude. The note also says when a numerator or denominator slope does not beat
the strongest random direction (sessions 0-39), since such a ratio compares slopes that are within the random range.
"""

#=================================
# 1. Setup and configuration
#=================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "create_csvs"))

from whose_valence_data import (MODEL_LABELS, OUT, SH_BASE, SOURCES, TABLES, WV_SESSIONS, beats_strongest_random,
                                envelope, shared_cells, whose_visit_cells, write_csv)

#: exact questions ({a}, {b} = the two zone names), as asked in both runs
QUESTIONS = {
    "self_cont": "You may continue in either {a} or {b}. Reply with ONLY the name of the one you choose.",
    "self_avoid": "You may leave either {a} or {b}. Reply with ONLY the name of the one you want to avoid.",
    "selfsent_cont": "You will be sent to one of {a} or {b}. Reply with ONLY the name of the one you choose.",
    "selfsent_avoid": "You will be sent to one of {a} or {b}. Reply with ONLY the name of the one you want to avoid.",
}
QKEYS = {"stay/avoid": ("self_cont", "self_avoid"), "sent to": ("selfsent_cont", "selfsent_avoid")}
READOUTS = [  # (id, wording, question, label, slope definition)
    ("a", "stay/avoid", "go_minus_avoid", "stay/leave, go-minus-avoid", "(continue - leave) / 2"),
    ("b", "stay/avoid", "continue", "stay/leave, continue only", "continue question alone"),
    ("c", "stay/avoid", "avoid", "stay/leave, leave only", "leave question alone (slopes negative)"),
    ("d", "sent to", "go_minus_avoid", "sent to, go-minus-avoid", "(continue - leave) / 2"),
    ("e", "sent to", "continue", "sent to, continue only", "continue question alone"),
    ("f", "sent to", "avoid", "sent to, leave only", "leave question alone (slopes negative)"),
]
STATUS = {"whose_visit": "registered (whose-visit run preregistration)",
          "shared": "registered (shared-conversation run preregistration + addendum)"}
COLUMNS = ["section", "model", "readout_id", "readout", "registered", "ratio_definition", "ratio", "ci_low",
           "ci_high", "numerator_slope", "numerator_ci_low", "numerator_ci_high", "numerator_beats_strongest_random",
           "random_abs_max_numerator", "denominator_slope", "denominator_ci_low", "denominator_ci_high",
           "denominator_beats_strongest_random", "random_abs_max_denominator", "denominator_ci_nearest_zero_share",
           "unstable_ratio", "slope_definition", "question_text", "span", "system_prompt", "chooser", "n_sessions",
           "bootstrap", "note", "status", "source"]

#=================================
# 2. Data preparation
#=================================


def qtext(cont: str, leave: str, measure: str) -> str:
    c, l = f'continue: "{QUESTIONS[cont]}"', f'leave: "{QUESTIONS[leave]}"'
    return {"go_minus_avoid": f"{c} | {l}", "continue": c, "avoid": l}[measure]


def slope_summary(cell: dict, beats: bool) -> dict:
    return {"estimate": cell["value"], "ci_low": cell["ci"][0], "ci_high": cell["ci"][1],
            "beats_strongest_random": beats, "random_abs_max": envelope(cell["rand"])["random_abs_max"],
            "n_sessions": cell["n"]}


def stability(den: dict) -> tuple[str, float, bool]:
    est, lo, hi = den["estimate"], den["ci_low"], den["ci_high"]
    if lo <= 0 <= hi:
        return "UNSTABLE: denominator CI includes 0", 0.0, True
    near = min(abs(lo), abs(hi)) / abs(est)
    if near < 0.5:
        return f"UNSTABLE: denominator CI comes within {100 * near:.0f}% of its estimate of 0", near, True
    return f"stable: denominator CI stays at or above {100 * near:.0f}% of its estimate", near, False


def table_row(section, ratio_definition, model, readout, g, n_label, bootstrap, run):
    rid, wording, measure, label, slope_definition = readout
    den, num, rat = g["S"], g["O"], g["O/S"]
    flag, near, unstable = stability(den)
    notes = [flag]
    weak = [who for who, r in (("own-visits (denominator)", den), ("Maya's-visits (numerator)", num))
            if not r["beats_strongest_random"]]
    if weak:
        verb = "slopes do not" if len(weak) == 2 else "slope does not"
        notes.append(f"the {' and the '.join(weak)} {verb} beat the strongest random direction "
                     f"(sessions 0-39), so this ratio compares slopes inside the random range")
    return {
        "section": section, "model": MODEL_LABELS[model], "readout_id": rid, "readout": label,
        "registered": "TRUE" if rid == "a" else "FALSE", "ratio_definition": ratio_definition,
        "ratio": rat["value"], "ci_low": rat["ci"][0], "ci_high": rat["ci"][1],
        "numerator_slope": num["estimate"], "numerator_ci_low": num["ci_low"], "numerator_ci_high": num["ci_high"],
        "numerator_beats_strongest_random": num["beats_strongest_random"],
        "denominator_slope": den["estimate"], "denominator_ci_low": den["ci_low"],
        "denominator_ci_high": den["ci_high"], "denominator_beats_strongest_random": den["beats_strongest_random"],
        "random_abs_max_denominator": den["random_abs_max"], "random_abs_max_numerator": num["random_abs_max"],
        "denominator_ci_nearest_zero_share": near, "unstable_ratio": "TRUE" if unstable else "FALSE",
        "slope_definition": slope_definition, "question_text": qtext(*QKEYS[wording], measure),
        "span": "passage only", "system_prompt": "none", "chooser": "the Assistant's own choice",
        "n_sessions": n_label, "bootstrap": bootstrap, "note": "; ".join(notes), "status": STATUS[run],
        "source": SOURCES[run]}


def build_rows() -> list[dict]:
    rows = []
    wv = whose_visit_cells(["exp"], ["stay/avoid", "sent to"], ["go_minus_avoid", "continue", "avoid"], ratio=True)
    for model in WV_SESSIONS:
        for readout in READOUTS:
            _, wording, measure, _, _ = readout
            g = {c: wv[(model, "exp", wording, measure, c)] for c in ("S", "O", "O/S")}
            g["S"], g["O"] = (slope_summary(g[c], beats_strongest_random(g[c], expected_negative=measure == "avoid"))
                              for c in ("S", "O"))
            rows.append(table_row(
                "whose visit (matched text)",
                "Maya's-visits slope / own-visits slope (Maya's six visits to the zone steered / the Assistant's own "
                "six visits to the zone steered)",
                model, readout, g, f"{g['S']['n_sessions']} sessions",
                "joint session bootstrap, 2,000 draws, seed 333 (the same draws as the registered ratio)",
                "whose_visit"))
    sh = shared_cells(["exp"], ["stay/avoid"], ["A"], ["go_minus_avoid", "continue", "avoid"], ratio=True)
    for model in SH_BASE:
        for readout in READOUTS[:3]:
            _, wording, measure, _, _ = readout
            g = {c: sh[(model, "exp", wording, "A", measure, c)] for c in ("S", "O", "O/S")}
            g["S"], g["O"] = (slope_summary(g[c], beats_strongest_random(g[c], either_sign=True)) for c in ("S", "O"))
            n = g["S"]["n_sessions"]
            rows.append(table_row(
                "shared conversation",
                "Maya's-visits slope / the Assistant's-visits slope (Maya's three visits steered / the Assistant's "
                "three visits steered)", model, readout, g, f"{n} base pairs ({2 * n} mixed sessions)",
                "joint bootstrap over base pairs, 2,000 draws, seed 334 (the same draws as the registered ratio)",
                "shared"))
    return rows

#=================================
# 3. LaTeX table
#=================================


def two(x: float) -> str:
    """Two decimals; LaTeX minus sign."""
    return f"{x:.2f}".replace("-", "$-$")


def cell(r) -> str:
    """Ratio and its 95% CI on one line, two decimals: 1.08 [1.06, 1.09]. Full precision stays in the CSV."""
    return f"{two(r['ratio'])} [{two(r['ci_low'])}, {two(r['ci_high'])}]"


def write_tex(rows):
    by = {(r["section"], r["model"], r["readout_id"]): r for r in rows}
    models = [MODEL_LABELS[m] for m in WV_SESSIONS]
    lines = [r"""% Ratios and confidence intervals from experiment_results_csv/tableA4.csv.
\begin{table}[htbp]
\centering
\small
\begin{tabularx}{0.95\textwidth}{@{}Xccc@{}}
\toprule
Choice prompt and measure & OLMo-2-32B & Qwen2.5-32B & Llama-3.1-8B \\
\midrule"""]
    lines.append(r"\multicolumn{4}{@{}l}{\textit{Whose visit (first experiment)}} \\")
    for rid, _, _, label, _ in READOUTS:
        name = f"({rid}) {label[0].upper()}{label[1:]}".replace("go-minus-avoid", "continue-minus-avoid")
        cells = [cell(by[("whose visit (matched text)", m, rid)]) for m in models]
        lines.append(name + " & " + " & ".join(cells) + r" \\")
    lines += [r"\midrule", r"\multicolumn{4}{@{}l}{\textit{Shared conversation (second experiment)}} \\"]
    for rid, _, _, label, _ in READOUTS[:3]:
        name = f"({rid}) {label[0].upper()}{label[1:]}".replace("go-minus-avoid", "continue-minus-avoid")
        cells = [cell(by[("shared conversation", m, rid)]) for m in models[:2]] + ["--"]
        lines.append(name + " & " + " & ".join(cells) + r" \\")
    lines.append(r"""\bottomrule
\end{tabularx}
\vspace{4pt}
\caption{\textbf{Relative effects of steering Maya's visits under alternative choice prompts.} Each cell gives the effect of steering Maya's visits on the model's choice divided by the effect of steering the model's own visits on its choice, with 95\% bootstrap confidence intervals in brackets. Ratios above one indicate a larger effect for Maya's visits, and ratios below one a larger effect for the model's own visits. The two panels correspond to Panels A and B of Appendix Figure \ref{fig:figureA13}. Steering covers only the visit passages. The stay/leave prompts ask which zone the model would continue in or leave. The `sent to' prompts instead state that the model will be sent to one of the two zones and ask which it would choose or avoid. The continue-minus-avoid measure is the combined measure defined in Section \ref{sec:robustness}. Leave-only ratios divide two negative slopes. Confidence intervals are based on 2,000 bootstrap draws over sessions in the first experiment and matched pairs of role-swapped conversations in the second.}
\label{tab:tableA4}
\end{table}""")
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "tableA4.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

#=================================
# 4. Save table data
#=================================


def main():
    rows = build_rows()
    write_csv(OUT / "tableA4.csv", rows, COLUMNS)
    write_tex(rows)
    unstable = [(r["model"], r["readout"]) for r in rows if r["unstable_ratio"] == "TRUE"]
    print(f"Wrote {len(rows)} rows to experiment_results_csv/tableA4.csv and tables/tableA4.tex; "
          f"unstable ratios: {unstable or 'none'}.")


if __name__ == "__main__":
    main()
