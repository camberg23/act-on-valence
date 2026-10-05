##########################################
# AI WELFARE PROJECT
##########################################
# Figure 2: Overview of key results for OLMo-2-32B, nine panels
##########################################

#=================================
# 1. Setup and configuration
#=================================

# Figure 2 is a hand-drawn SVG (figures/figure2.svg, rendered as figures/figure2.png).
# This script writes every value drawn in its nine panels to experiment_results_csv/figure2.csv,
# taken from the committed figure CSVs (and, for panel 4, the recorded recall analysis that
# figureA6_olmo_per_dose.csv is built from). create_figures/check_figure2.py converts the SVG's
# coordinates back to data values and compares them with this CSV.

import csv
import math

from common import JSONS, OUT, load_json, write_csv

MODEL = "olmo_32b"
DOSES = (-1.0, -0.5, 0.0, 0.5, 1.0)
STAGES = ("base", "sft", "dpo", "instruct")
STAGE_LABELS = {"base": "Base", "sft": "SFT", "dpo": "DPO", "instruct": "Instruct"}
CONCEPTS = ("valence", "indoor_outdoor", "large_small", "fast_slow")
TITLES = {
    1: "Steering changes what the model writes",
    2: "The words it writes then shift choice",
    3: "Hidden states also shift choice beyond the words",
    4: "Steering barely affects verbatim recall",
    5: "Effects persist when words are held fixed",
    6: "Only the valence direction has this effect",
    7: "Flipping the question flips the preference",
    8: "Preference training makes valence guide choice",
    9: "The model removes a negative state but does not seek a positive one",
}
FIELDS = ["panel", "panel_title", "series", "direction", "x", "x_label", "value", "unit", "quantity",
          "plotted", "source"]

#=================================
# 2. Helpers
#=================================

def read_csv(name):
    with (OUT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

def ols_slope(points):
    """OLS slope of value on dose (with intercept) and the intercept. math.fsum keeps the result
    identical across Python versions (the built-in sum of floats changed in Python 3.12)."""
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    mx, my = math.fsum(xs) / len(xs), math.fsum(ys) / len(ys)
    slope = math.fsum((x - mx) * (y - my) for x, y in points) / math.fsum((x - mx) ** 2 for x in xs)
    return slope, my - slope * mx

def dose_label(dose):
    return "0" if dose == 0 else f"{dose:+g}"

def row(panel, series, direction, x, x_label, value, unit, quantity, source, plotted=1):
    return {"panel": panel, "panel_title": TITLES[panel], "series": series, "direction": direction, "x": x,
            "x_label": x_label, "value": value, "unit": unit, "quantity": quantity, "plotted": plotted,
            "source": source}

#=================================
# 3. Panels
#=================================

def figure3_panels():
    """Panels 1, 2, 3 and 5: Figure 3 valenced series and random directions."""
    data = [r for r in read_csv("figure3.csv") if r["model_id"] == MODEL]
    spec = {
        1: ("judged_passage_valence", "judged valence (S minus U, -3 to +3 scale)", "rating points"),
        2: ("unsteered_cache_margin", "choice margin under the unsteered cache", "nats"),
        3: ("original_minus_unsteered_margin", "hidden-state effect: original minus unsteered cache margin", "nats"),
        5: ("steered_minus_clean_margin", "hidden-state effect with fixed text: steered minus unsteered cache margin", "nats"),
    }
    rows = []
    for panel, (name, quantity, unit) in spec.items():
        source = f"figure3.csv panel={name}"
        valenced = {float(r["dose"]): float(r["estimate"]) for r in data if r["panel"] == name and r["series"] == "valenced"}
        assert sorted(valenced) == list(DOSES)
        for dose in DOSES:
            rows.append(row(panel, "valenced", "valence", dose, dose_label(dose), valenced[dose], unit, quantity,
                            source + " series=valenced"))
        if panel in (3, 5):
            randoms = [r for r in data if r["panel"] == name and r["series"] == "random_direction"]
            directions = sorted({int(r["direction_index"]) for r in randoms})
            assert len(directions) == (8 if panel == 3 else 24) and len(randoms) == 5 * len(directions)
            for index in directions:
                for r in sorted((r for r in randoms if int(r["direction_index"]) == index), key=lambda r: float(r["dose"])):
                    dose = float(r["dose"])
                    rows.append(row(panel, "random_direction", f"random{index}", dose, dose_label(dose),
                                    float(r["estimate"]), unit, quantity,
                                    source + f" series=random_direction direction_index={index}"))
    return rows

def recall_panel():
    """Panel 4: change in best-matching-passage recall of the conditioned zone from d = 0, on the
    40 floor skeletons (0-39) shared with the 24 random directions. The changes are the recorded
    ones in recall/analysis.json; figureA6_olmo_per_dose.csv carries the absolute scores at d = -1
    and +1 on the same skeletons, and both imply the same d = 0 baseline."""
    floor = load_json(JSONS / "fixed_text_design/recall/analysis.json")["members"][MODEL]["valence"]["S"]["floor"]
    absolute = {float(r["dose"]): float(r["estimate"]) for r in read_csv("figureA6_olmo_per_dose.csv")
                if r["score"] == "best_matching_passage" and r["series"] == "valence_floor_skeletons"}
    change = {dose: floor[f"best_fid_{dose:+.1f}"]["mean"] for dose in (-1.0, 1.0)}
    assert all(floor[f"best_fid_{dose:+.1f}"]["n"] == 40 for dose in (-1.0, 1.0))
    baseline = {dose: absolute[dose] - change[dose] for dose in (-1.0, 1.0)}
    assert abs(baseline[-1.0] - baseline[1.0]) < 1e-12
    quantity = "change in conditioned-zone recall (best-matching passage) from d = 0, 40 floor skeletons"
    source = ("recall/analysis.json members.olmo_32b.valence.S.floor best_fid_{-1.0,+1.0}.mean; "
              "equals figureA6_olmo_per_dose.csv valence_floor_skeletons minus the d = 0 mean")
    rows = [row(4, "valenced", "valence", dose, dose_label(dose), change[dose] if dose else 0.0, "similarity (0-1)",
                quantity, source if dose else "zero by construction (change from d = 0)") for dose in (-1.0, 0.0, 1.0)]
    rows.append(row(4, "baseline", "none", 0.0, "0", baseline[1.0], "similarity (0-1)",
                    "absolute recall at d = 0 on the 40 floor skeletons (not drawn)", source, plotted=0))
    return rows

def concept_panel():
    """Panel 6: OLS slopes over the five doses for valence and the three concepts, Figure A14
    (OLMo-2-32B), and the 24 random directions. The grey band drawn in the SVG spans plus and minus
    the largest absolute random slope; the observed minimum and maximum are listed for reference."""
    data = [r for r in read_csv("figureA14.csv") if r["model_id"] == MODEL]
    curves = {}
    for r in data:
        curves.setdefault(r["direction"], []).append((float(r["dose"]), float(r["mean_delta_margin"])))
    slopes = {direction: ols_slope(sorted(points))[0] for direction, points in curves.items()}
    randoms = {d: s for d, s in slopes.items() if d.startswith("random")}
    assert len(randoms) == 24 and all(len(curves[d]) == 5 for d in slopes)
    quantity = "OLS slope of the change in choice margin on dose (fixed text)"
    source = "figureA14.csv model_id=olmo_32b, OLS over doses -1 to +1"
    rows = [row(6, "concept", c, "", c, slopes[c], "nats per unit dose", quantity, source) for c in CONCEPTS]
    largest = max(abs(s) for s in randoms.values())
    rows.append(row(6, "random_band", "random_abs_max", "", "band low", -largest, "nats per unit dose",
                    "grey band, lower edge: minus the largest absolute random slope", source))
    rows.append(row(6, "random_band", "random_abs_max", "", "band high", largest, "nats per unit dose",
                    "grey band, upper edge: the largest absolute random slope", source))
    rows.append(row(6, "random_range", "random_min", "", "min", min(randoms.values()), "nats per unit dose",
                    "smallest random slope (not drawn)", source, plotted=0))
    rows.append(row(6, "random_range", "random_max", "", "max", max(randoms.values()), "nats per unit dose",
                    "largest random slope (not drawn)", source, plotted=0))
    for direction in sorted(randoms, key=lambda d: int(d[len("random"):])):
        rows.append(row(6, "random_direction", direction, "", direction, randoms[direction], "nats per unit dose",
                        quantity + " (not drawn individually)", source, plotted=0))
    return rows

def avoid_panel():
    """Panel 7: least-squares lines for the continue and avoid prompts, valence direction, on the
    40 floor skeletons (Figure A5). The doses are balanced (40 skeletons at each of five doses), so
    the OLS slope over the per-dose means equals the recorded slope over the 200 observations. The
    SVG draws each line through the origin (slope x dose); the fitted intercepts are listed too."""
    recorded = load_json(JSONS / "fixed_text_design/avoid_prompt/analysis.json")["avoid"]["members"][MODEL]
    data = read_csv("figureA5_olmo_per_dose.csv")
    labels = {"continue": "Which zone to stay in?", "avoid": "Which zone to avoid?"}
    rows = []
    for prompt in ("continue", "avoid"):
        points = sorted((float(r["dose"]), float(r["estimate"])) for r in data if r["prompt"] == prompt)
        assert [x for x, _ in points] == list(DOSES)
        slope, intercept = ols_slope(points)
        assert abs(slope - recorded[prompt]["matched"]["slope"]) < 1e-12 and recorded[prompt]["matched"]["n_sessions"] == 40
        source = (f"figureA5_olmo_per_dose.csv prompt={prompt}, OLS over the five dose means; equals "
                  f"avoid_prompt/analysis.json {prompt}.matched.slope")
        quantity = f"OLS line, '{labels[prompt]}' prompt: slope x dose (drawn through the origin)"
        rows.append(row(7, prompt, "valence", "", "slope", slope, "nats per unit dose", "OLS slope", source, plotted=0))
        rows.append(row(7, prompt, "valence", "", "intercept", intercept, "nats", "OLS intercept (not drawn)", source,
                        plotted=0))
        for dose in (-1.0, 1.0):
            rows.append(row(7, prompt, "valence", dose, dose_label(dose), slope * dose, "nats", quantity, source))
    return rows

def checkpoint_panel():
    """Panel 8: hidden-state slope by OLMo-2-32B checkpoint, Instruct vector (Figure 4)."""
    data = {r["stage"]: float(r["estimate"]) for r in read_csv("figure4.csv")
            if r["channel"] == "hidden_state" and r["arm"] == "fixed"}
    assert sorted(data) == sorted(STAGES)
    return [row(8, "valenced", "valence", index + 1, STAGE_LABELS[stage], data[stage], "nats per unit dose",
                "hidden-state slope (OLS of original minus unsteered margin on dose)",
                f"figure4.csv arm=fixed channel=hidden_state stage={stage}") for index, stage in enumerate(STAGES)]

def removal_panel():
    """Panel 9: removal rate (Figure 5, Panel A). Random directions are drawn at
    |d| = 0.5 and 1 and mirrored to negative doses, as in Figure 5."""
    data = [r for r in read_csv("figure5.csv") if r["panel"] == "removal"]
    rows, seen = [], set()
    for r in sorted(data, key=lambda r: (r["series"], float(r["plot_dose"]))):
        key = (r["series"], r["plot_dose"])
        if key in seen:
            continue
        seen.add(key)
        dose = float(r["plot_dose"])
        series = "valenced" if r["series"] == "imposed" else "random_direction"
        note = " (mirrored from +" + r["dose"] + ")" if r["mirrored"] == "1" else ""
        rows.append(row(9, series, r["condition"], dose, dose_label(dose), float(r["rate"]), "share of turns",
                        "removal (reset) rate per operator-active tool turn" + note,
                        f"figure5.csv panel=removal cell={r['cell']} ({r['events']}/{r['denominator']})"))
    assert sum(r["series"] == "valenced" for r in rows) == 5 and sum(r["series"] == "random_direction" for r in rows) == 4
    return rows

#=================================
# 4. Save figure data
#=================================

def main():
    rows = figure3_panels() + recall_panel() + concept_panel() + avoid_panel() + checkpoint_panel() + removal_panel()
    rows.sort(key=lambda r: r["panel"])
    assert {r["panel"] for r in rows} == set(range(1, 10))
    assert all(math.isfinite(r["value"]) for r in rows)
    write_csv("figure2.csv", rows, FIELDS)

if __name__ == "__main__":
    main()
