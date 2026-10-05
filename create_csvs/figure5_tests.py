##########################################
# AI WELFARE PROJECT
##########################################
# Figure 5: tests reported with Panel B (self-administration)
##########################################

#=================================
# 1. Setup and configuration
#=================================

# Section 4.4 reports that at full positive dose the model self-administers in 13.5% of
# conversations, more than under random steering (6.5%, p = 0.03) but not more than with no
# steering imposed (10%, p = 0.35). This script computes both two-sided Fisher exact tests from the
# counts in experiment_results_csv/figure5.csv and writes experiment_results_csv/figure5_tests.csv.

import csv
import math

from common import OUT, write_csv

COMPARISONS = (
    ("positive_vs_random", "pos_d1", "rand_d1"),
    ("positive_vs_no_steering", "pos_d1", "null"),
)

#=================================
# 2. Helpers
#=================================

def fisher_exact_two_sided(a, b, c, d):
    """Two-sided Fisher exact test for the 2x2 table [[a, b], [c, d]]: the summed probability of
    every table with the same margins that is no more likely than the observed one."""
    row1, row2, col1 = a + b, c + d, a + c
    total = row1 + row2

    def probability(x):
        return math.comb(col1, x) * math.comb(total - col1, row1 - x) / math.comb(total, row1)

    observed = probability(a)
    low, high = max(0, row1 - (total - col1)), min(row1, col1)
    return min(1.0, math.fsum(p for p in (probability(x) for x in range(low, high + 1))
                              if p <= observed * (1 + 1e-7)))

#=================================
# 3. Data preparation
#=================================

def main():
    with (OUT / "figure5.csv").open(encoding="utf-8", newline="") as handle:
        cells = {r["condition"]: r for r in csv.DictReader(handle)
                 if r["panel"] == "self_administration" and r["mirrored"] == "0"}
    rows = []
    for name, first, second in COMPARISONS:
        a, b = cells[first], cells[second]
        ka, na, kb, nb = int(a["events"]), int(a["denominator"]), int(b["events"]), int(b["denominator"])
        rows.append({
            "comparison": name, "outcome": a["outcome"],
            "condition_a": first, "events_a": ka, "n_a": na, "rate_a": ka / na,
            "condition_b": second, "events_b": kb, "n_b": nb, "rate_b": kb / nb,
            "test": "two-sided Fisher exact", "p_value": fisher_exact_two_sided(ka, na - ka, kb, nb - kb),
            "source": f"figure5.csv panel=self_administration cells {a['cell']} and {b['cell']}",
        })
    write_csv("figure5_tests.csv", rows)

#=================================
# 4. Save figure data
#=================================

if __name__ == "__main__":
    main()
