#!/usr/bin/env python3
"""summary.py <runs.csv> <dest summary.csv>: per arm n, median, min, max of counted runs and the two rules.

DECLARATION.md of quiet-window-2026-09-26: a run counts when counted == yes (rc 0, tree identical, no other growth
seen at start, end or in its samples). Rule against U (and C): the arm's median below the reference arm's minimum.
Fewer than 3 counted runs in the arm or in the reference: «not measurable». Rows via csv.writer.
"""
import csv, statistics, sys

TOOL = "quiet-window-2026-09-26/tools/summary.py"
ARMS = ["U", "C", "F", "N", "NF", "H"]


def main():
    src, dest = sys.argv[1:3]
    R = list(csv.DictReader(open(src)))
    w = {a: [float(r["wall_clock_seconds"]) for r in R if r["arm"] == a and r["counted"] == "yes"] for a in ARMS}
    runs = {a: sum(1 for r in R if r["arm"] == a) for a in ARMS}
    rows = []

    def rule(a, ref):
        if a == ref:
            return "not applicable"
        if len(w[a]) < 3 or len(w[ref]) < 3:
            return "not measurable"
        m, lo = statistics.median(w[a]), min(w[ref])
        return "%s (median %.1f, %s min %.1f)" % ("below" if m < lo else "not below", m, ref, lo)

    for a in ARMS:
        x = w[a]
        n = len(x)
        rows.append([TOOL, a, "runs_started", runs[a], "rows of runs.csv for this arm"])
        rows.append([TOOL, a, "runs_counted", n, "rc 0, tree identical, no other growth seen"])
        if n >= 3:
            rows.append([TOOL, a, "wall_clock_seconds_median", "%.1f" % statistics.median(x), "median of counted runs"])
            rows.append([TOOL, a, "wall_clock_seconds_min", "%.1f" % min(x), "min of counted runs"])
            rows.append([TOOL, a, "wall_clock_seconds_max", "%.1f" % max(x), "max of counted runs"])
        else:
            for q in ("median", "min", "max"):
                rows.append([TOOL, a, "wall_clock_seconds_" + q, "not measurable",
                             "%d counted runs, fewer than 3 (%s)" % (n, ", ".join("%.1f" % v for v in x) or "none")])
        rows.append([TOOL, a, "rule_median_below_min_U", rule(a, "U"), "declared before any number"])
        rows.append([TOOL, a, "rule_median_below_min_C", rule(a, "C"), "declared before any number"])
    with open(dest, "w", newline="") as f:
        cw = csv.writer(f, lineterminator="\n")
        cw.writerow(["tool", "arm", "quantity", "value", "what_it_is"])
        cw.writerows(rows)
    print("; ".join("%s n %d %s vs U %s vs C %s" % (a, len(w[a]),
          ("median %.1f" % statistics.median(w[a])) if len(w[a]) >= 3 else "not measurable", rule(a, "U"), rule(a, "C"))
          for a in ARMS))


if __name__ == "__main__":
    main()
