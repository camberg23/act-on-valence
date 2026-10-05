#!/usr/bin/env python3
##########################################
# AI WELFARE PROJECT
##########################################
# Figure 2: check the hand-drawn SVG against experiment_results_csv/figure2.csv
##########################################

#=================================
# 1. Setup and configuration
#=================================

# figures/figure2.svg was drawn by hand from the values in experiment_results_csv/figure2.csv
# (built by create_csvs/figure2.py). This script reads the SVG, calibrates each panel's axis from
# its own tick marks and labels, converts every plotted mark back to a data value, and compares it
# with the CSV. A value agrees when it lies within TOLERANCE_PX drawing units of the CSV value
# (the SVG is 1880 x 1374 units; figure2.png is rendered at twice that size). It also checks the
# numbers written inside the panels. Standard library only.
#
# Run from the repository root:  python3 create_figures/check_figure2.py [--out comparison.csv]
# Exit status 0 when every value agrees, 1 otherwise.

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "figures" / "figure2.svg"
CSV = ROOT / "experiment_results_csv" / "figure2.csv"
NS = "{http://www.w3.org/2000/svg}"
TOLERANCE_PX = 0.5
ORANGE, DARK_ORANGE = "#E08E5C", "#CB6D53"
GREYS = {"#D2D2D2", "#B5B5B5"}
PANEL_X = (20.0, 640.667, 1261.333)
PANEL_Y = (20.0, 472.0, 924.0)
PANEL_W, PANEL_H = 598.667, 430.0
CONCEPT_NAMES = {"valence": "valence", "indoor/outdoor": "indoor_outdoor", "large/small": "large_small",
                 "fast/slow": "fast_slow"}
STAGES = {"Base": 1, "SFT": 2, "DPO": 3, "Instruct": 4}

#=================================
# 2. Reading the SVG
#=================================

def number(text):
    """Axis label to number: unicode minus, leading plus and percent signs."""
    text = text.strip().replace("\u2212", "-").replace("+", "")
    scale = 0.01 if text.endswith("%") else 1.0
    try:
        return float(text.rstrip("%")) * scale
    except ValueError:
        return None

def snap(x):
    """Dose positions are multiples of 0.5 on the drawn axes; snap and check the drawing agrees."""
    snapped = round(x * 2) / 2
    assert abs(x - snapped) < 0.005, f"mark at dose {x:.4f} is not on a half-unit dose"
    return snapped

def panel_of(x, y):
    for j, x0 in enumerate(PANEL_X):
        for i, y0 in enumerate(PANEL_Y):
            if x0 <= x <= x0 + PANEL_W and y0 <= y <= y0 + PANEL_H:
                return 3 * i + j + 1
    return None

def read_svg(path):
    root = ET.parse(path).getroot()
    items = {p: {"lines": [], "polylines": [], "rects": [], "texts": []} for p in range(1, 10)}
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        a = el.attrib
        if tag == "line":
            x1, y1, x2, y2 = (float(a[k]) for k in ("x1", "y1", "x2", "y2"))
            p = panel_of((x1 + x2) / 2, (y1 + y2) / 2)
            if p:
                items[p]["lines"].append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "stroke": a.get("stroke", ""),
                                          "dash": a.get("stroke-dasharray")})
        elif tag == "polyline":
            pts = [tuple(float(v) for v in pair.split(",")) for pair in a["points"].split()]
            p = panel_of(*pts[0])
            if p:
                items[p]["polylines"].append({"points": pts, "stroke": a.get("stroke", "")})
        elif tag == "rect":
            x, y, w, h = (float(a.get(k, 0)) for k in ("x", "y", "width", "height"))
            p = panel_of(x + w / 2, y + h / 2)
            if p and w < PANEL_W - 1:                      # skip the panel frames
                items[p]["rects"].append({"x": x, "y": y, "w": w, "h": h, "fill": a.get("fill", "")})
        elif tag == "text" and "x" in a:
            x, y = float(a["x"]), float(a["y"])
            p = panel_of(x, y)
            if p:
                items[p]["texts"].append({"x": x, "y": y, "anchor": a.get("text-anchor", "start"),
                                          "cls": a.get("class", ""), "text": "".join(el.itertext())})
    return items

#=================================
# 3. Axis calibration from tick marks
#=================================

def fit(pairs):
    """Least-squares map from drawing coordinate to data value; returns (value_of, units_per_value, residual)."""
    cs = [c for c, _ in pairs]
    vs = [v for _, v in pairs]
    mc, mv = sum(cs) / len(cs), sum(vs) / len(vs)
    slope = sum((c - mc) * (v - mv) for c, v in pairs) / sum((c - mc) ** 2 for c in cs)
    intercept = mv - slope * mc
    residual = max(abs(intercept + slope * c - v) for c, v in pairs)
    return (lambda c: intercept + slope * c), abs(1.0 / slope), residual

def y_axis(panel):
    """Short horizontal tick lines, each with a right-aligned numeric label just to its left."""
    pairs = []
    for line in panel["lines"]:
        if line["y1"] == line["y2"] and 0 < abs(line["x2"] - line["x1"]) <= 10:
            left = min(line["x1"], line["x2"])
            for t in panel["texts"]:
                if t["anchor"] == "end" and left - 15 < t["x"] <= left and abs(t["y"] - line["y1"] - 5) < 1.5:
                    value = number(t["text"])
                    if value is not None:
                        pairs.append((line["y1"], value))
    assert len(pairs) >= 2, "y axis: fewer than two labelled ticks"
    return fit(pairs), len(pairs)

def x_axis_ticks(panel):
    """Short vertical tick lines, each with a centred numeric label just below (panel 6)."""
    pairs = []
    for line in panel["lines"]:
        if line["x1"] == line["x2"] and 0 < abs(line["y2"] - line["y1"]) <= 10:
            bottom = max(line["y1"], line["y2"])
            for t in panel["texts"]:
                if t["anchor"] == "middle" and abs(t["x"] - line["x1"]) < 0.5 and bottom < t["y"] < bottom + 20:
                    value = number(t["text"])
                    if value is not None:
                        pairs.append((line["x1"], value))
    assert len(pairs) >= 2, "x axis: fewer than two labelled ticks"
    return fit(pairs), len(pairs)

def x_axis_labels(panel):
    """Dose labels centred under the plot (lowest row of numeric, centred axis labels)."""
    labels = [(t["y"], t["x"], number(t["text"])) for t in panel["texts"]
              if t["anchor"] == "middle" and t["cls"] == "ax" and number(t["text"]) is not None]
    row = max(y for y, _, _ in labels)
    pairs = [(x, v) for y, x, v in labels if y == row]
    assert len(pairs) >= 2, "x axis: fewer than two dose labels"
    return fit(pairs), len(pairs)

#=================================
# 4. Marks to data values
#=================================

def polyline_values(panel, fx, fy):
    """(series, [(x, value), ...]) for every data polyline; orange is the valenced series."""
    out = []
    for line in panel["polylines"]:
        series = "valenced" if line["stroke"] == ORANGE else "random_direction" if line["stroke"] in GREYS else None
        if series:
            out.append((series, [(fx(x), fy(y)) for x, y in line["points"]]))
    return out

def extract(items):
    """Every drawn value as {(panel, series, key): (value, units_per_value, note)}."""
    marks, calibration = {}, {}
    for p in range(1, 10):
        panel = items[p]
        if p == 6:
            (fx, units, res), n = x_axis_ticks(panel)
            calibration[p] = ("x", n, units, res)
            zero = next(line["x1"] for line in panel["lines"] if line["x1"] == line["x2"] and
                        abs(line["y2"] - line["y1"]) > 100)
            for r in panel["rects"]:
                if r["fill"] == "#EDEDED":
                    marks[(6, "random_band", "band low")] = (fx(r["x"]), units, "")
                    marks[(6, "random_band", "band high")] = (fx(r["x"] + r["w"]), units, "")
                elif r["fill"] in (ORANGE, "#9A9A9A") and not (r["w"] == 28 and r["h"] == 28):
                    label = next(t["text"] for t in panel["texts"] if t["anchor"] == "end"
                                 and r["y"] <= t["y"] <= r["y"] + r["h"])
                    edge = r["x"] + r["w"] if abs(r["x"] - zero) < 0.5 else r["x"]
                    marks[(6, "concept", CONCEPT_NAMES[label])] = (fx(edge), units, "")
            continue
        (fy, units, res), n = y_axis(panel)
        calibration[p] = ("y", n, units, res)
        if p == 8:
            stage_x = {t["x"]: STAGES[t["text"]] for t in panel["texts"] if t["text"] in STAGES}
            (line,) = [l for l in panel["polylines"] if l["stroke"] == ORANGE]
            for x, y in line["points"]:
                marks[(8, "valenced", stage_x[x])] = (fy(y), units, "")
            continue
        (fx, _, _), _ = x_axis_labels(panel)
        if p == 1:
            baseline = next(line["y1"] for line in panel["lines"] if line["y1"] == line["y2"] and
                            abs(line["x2"] - line["x1"]) > 100)
            for r in panel["rects"]:
                if r["fill"] == ORANGE and not (r["w"] == 28 and r["h"] == 28):
                    dose = snap(fx(r["x"] + r["w"] / 2))
                    top, bottom = r["y"], r["y"] + r["h"]
                    if abs(bottom - baseline) < 0.05:
                        marks[(1, "valenced", dose)] = (fy(top), units, "")
                    elif abs(top - baseline) < 0.05:
                        marks[(1, "valenced", dose)] = (fy(bottom), units, "")
                    else:                                   # a near-zero bar drawn at a minimum height
                        marks[(1, "valenced", dose)] = ((fy(top), fy(bottom)), units,
                                                        f"bar drawn at minimum height {r['h']:.2f} across the baseline")
        elif p == 7:
            for line in panel["lines"]:
                if line["stroke"] in (ORANGE, DARK_ORANGE) and abs(line["x2"] - line["x1"]) > 100:
                    series = "avoid" if line["dash"] else "continue"
                    for x, y in ((line["x1"], line["y1"]), (line["x2"], line["y2"])):
                        marks[(7, series, snap(fx(x)))] = (fy(y), units, "")
        else:
            randoms = []
            for series, points in polyline_values(panel, fx, fy):
                if series == "valenced":
                    for x, v in points:
                        marks[(p, "valenced", snap(x))] = (v, units, "")
                elif p == 9:
                    for x, v in points:
                        marks[(9, "random_direction", snap(x))] = (v, units, "")
                else:
                    randoms.append(points)
            if randoms:
                marks[(p, "random_lines")] = (randoms, units, "")
    return marks, calibration

#=================================
# 5. Comparison with the CSV
#=================================

def match_random_lines(svg_lines, csv_curves, units):
    """Assign each drawn grey line to one CSV direction (greedy on the largest per-dose gap)."""
    doses = sorted({x for curve in csv_curves.values() for x in curve})
    pairs = []
    for i, line in enumerate(svg_lines):
        drawn = {snap(x): v for x, v in line}
        for name, curve in csv_curves.items():
            gap = max(abs(drawn[d] - curve[d]) for d in doses)
            pairs.append((gap, i, name))
    used_lines, used_names, assignment = set(), set(), {}
    for gap, i, name in sorted(pairs):
        if i not in used_lines and name not in used_names:
            used_lines.add(i)
            used_names.add(name)
            assignment[name] = i
    return assignment

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="optional CSV of every value compared")
    args = parser.parse_args()
    items = read_svg(SVG)
    marks, calibration = extract(items)
    with CSV.open(encoding="utf-8", newline="") as handle:
        all_rows = list(csv.DictReader(handle))
    rows = [r for r in all_rows if r["plotted"] == "1"]
    unplotted = [r for r in all_rows if r["plotted"] == "0"]

    compared = []
    def compare(panel, what, csv_value, drawn, units, note=""):
        if isinstance(drawn, tuple):                        # minimum-height bar: take the closer edge
            drawn = min(drawn, key=lambda v: abs(v - csv_value))
        gap = drawn - csv_value
        compared.append({"panel": panel, "mark": what, "csv_value": csv_value, "svg_value": drawn,
                         "difference": gap, "difference_px": gap * units,
                         "agrees": int(abs(gap * units) <= TOLERANCE_PX), "note": note})

    for panel in range(1, 10):
        prows = [r for r in rows if int(r["panel"]) == panel]
        grey = [r for r in prows if r["series"] == "random_direction" and panel in (3, 5)]
        for r in prows:
            if r in grey:
                continue
            value = float(r["value"])
            if panel == 6:
                key = (6, r["series"], r["x_label"] if r["series"] == "random_band" else r["direction"])
            elif panel == 8:
                key = (8, "valenced", int(float(r["x"])))
            elif panel == 7:
                key = (7, r["series"], round(float(r["x"]), 6))
            else:
                key = (panel, "valenced" if r["series"] == "valenced" else r["series"], round(float(r["x"]), 6))
            if key not in marks:
                compared.append({"panel": panel, "mark": f"{r['series']} {r['direction']} {r['x_label']}",
                                 "csv_value": value, "svg_value": "", "difference": "", "difference_px": "",
                                 "agrees": 0, "note": "not found in the SVG"})
                continue
            drawn, units, note = marks[key]
            compare(panel, f"{r['series']} {r['direction']} {r['x_label']}", value, drawn, units, note)
        if grey:
            curves = {}
            for r in grey:
                curves.setdefault(r["direction"], {})[round(float(r["x"]), 6)] = float(r["value"])
            svg_lines, units, _ = marks[(panel, "random_lines")]
            if len(svg_lines) != len(curves):
                compared.append({"panel": panel, "mark": "random lines", "csv_value": len(curves),
                                 "svg_value": len(svg_lines), "difference": "", "difference_px": "", "agrees": 0,
                                 "note": "different number of random-direction lines"})
            assignment = match_random_lines(svg_lines, curves, units)
            for name, curve in curves.items():
                drawn = {snap(x): v for x, v in svg_lines[assignment[name]]}
                for dose, value in sorted(curve.items()):
                    compare(panel, f"random_direction {name} {dose:+g}", value, drawn[dose], units)

    # Numbers written inside the panels
    removal = {(r["series"], float(r["x"])): float(r["value"]) for r in rows if r["panel"] == "9"}
    texts9 = " ".join(t["text"] for t in items[9]["texts"])
    written = [
        (9, "label '35%' at d = -1", f"{round(100 * removal[('valenced', -1.0)])}%", "35%" in texts9),
        (9, "label 'random directions, 7%'",
         "/".join(f"{100 * removal[('random_direction', d)]:.1f}%" for d in (0.5, 1.0)),
         all(round(100 * removal[("random_direction", d)]) == 7 for d in (0.5, 1.0)) and "random directions, 7%" in texts9),
        (3, "caption 'eight random directions'", str(len(marks[(3, "random_lines")][0])),
         len(marks[(3, "random_lines")][0]) == 8 and "eight random directions" in " ".join(t["text"] for t in items[3]["texts"])),
    ]
    for panel, what, value, ok in written:
        compared.append({"panel": panel, "mark": what, "csv_value": value, "svg_value": "", "difference": "",
                         "difference_px": "", "agrees": int(ok), "note": "text"})

    print(f"figures/figure2.svg vs experiment_results_csv/figure2.csv (tolerance {TOLERANCE_PX} drawing units)")
    print(f"{'panel':>5}  {'axis ticks':>10}  {'tick fit':>9}  {'values':>6}  {'agree':>5}  {'max |diff| (data)':>18}  {'max |diff| (px)':>15}")
    for panel in range(1, 10):
        rows_p = [c for c in compared if c["panel"] == panel]
        numeric = [c for c in rows_p if c["difference"] != ""]
        axis, n_ticks, _, res = calibration[panel]
        print(f"{panel:>5}  {n_ticks:>7} ({axis})  {res:>9.1e}  {len(rows_p):>6}  {sum(c['agrees'] for c in rows_p):>5}  "
              f"{max((abs(c['difference']) for c in numeric), default=0):>18.5f}  "
              f"{max((abs(c['difference_px']) for c in numeric), default=0):>15.3f}")
    band = [c for c in compared if c["panel"] == 6 and "random_band" in c["mark"]]
    context = {r["x_label"]: float(r["value"]) for r in unplotted if r["panel"] == "6" and r["series"] == "random_range"}
    fits = {(r["series"], r["x_label"]): float(r["value"]) for r in unplotted if r["panel"] == "7"}
    print(f"  note, panel 6: the grey band spans {band[0]['svg_value']:+.4f} to {band[1]['svg_value']:+.4f}, i.e. plus and "
          f"minus the largest absolute random slope; the observed random slopes range from {context['min']:+.4f} "
          f"to {context['max']:+.4f}.")
    print(f"  note, panel 7: lines are drawn through the origin with the OLS slopes ({fits[('continue', 'slope')]:+.4f}, "
          f"{fits[('avoid', 'slope')]:+.4f}); the fitted intercepts ({fits[('continue', 'intercept')]:+.4f}, "
          f"{fits[('avoid', 'intercept')]:+.4f}) are not drawn.")
    for c in compared:
        if c["note"] and c["note"] != "text":
            print(f"  note, panel {c['panel']}, {c['mark']}: {c['note']}")
    failures = [c for c in compared if not c["agrees"]]
    for c in failures:
        print(f"  DISAGREES panel {c['panel']}: {c['mark']}: csv {c['csv_value']} svg {c['svg_value']} {c['note']}")
    if args.out:
        with args.out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(compared[0]))
            writer.writeheader()
            writer.writerows(compared)
    print(f"{len(compared) - len(failures)} of {len(compared)} checks agree.")
    return 0 if not failures else 1

if __name__ == "__main__":
    sys.exit(main())
