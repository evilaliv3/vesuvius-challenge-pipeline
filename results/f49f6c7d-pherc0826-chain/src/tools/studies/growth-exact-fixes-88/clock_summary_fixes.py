#!/usr/bin/env python3
"""clock_summary_fixes.py <clock-runs.csv> <dest clock-summary.csv>: growth-exact-fixes-88's quiet clock (DECLARATION.md).
A copy of growth-lto-pgo-1447/tools/clock_summary.py (not touched) with arms HV3 and STACK only; the rule unchanged: an arm
passes on CPU when its median run_cpu_seconds over counted runs is below HV3's minimum, and on wall clock when its median
wall_clock_seconds is below HV3's minimum; fewer than 3 counted runs in the arm or in HV3: «not measurable».
"""
import csv, statistics, sys

TOOL = "growth-exact-fixes-88/tools/clock_summary_fixes.py"
ARMS = ["HV3", "STACK"]


def num(v):
    try:
        return float(v)
    except ValueError:
        return None


def main():
    src, dest = sys.argv[1:3]
    R = list(csv.DictReader(open(src)))
    C = {a: [r for r in R if r["arm"] == a and r["counted"] == "yes"] for a in ARMS}
    runs = {a: sum(1 for r in R if r["arm"] == a) for a in ARMS}
    rows = []

    def vals(a, col):
        return [v for v in (num(r[col]) for r in C[a]) if v is not None]

    def rule(a, col):
        if a == "HV3":
            return "not applicable"
        x, ref = vals(a, col), vals("HV3", col)
        if len(C[a]) < 3 or len(C["HV3"]) < 3 or len(x) != len(C[a]) or len(ref) != len(C["HV3"]):
            return "not measurable"
        m, lo = statistics.median(x), min(ref)
        return "%s (median %.1f, HV3 min %.1f)" % ("pass" if m < lo else "fail", m, lo)

    def stats(a, col, what):
        x = vals(a, col)
        if len(C[a]) >= 3 and len(x) == len(C[a]):
            for q, f in (("median", statistics.median), ("min", min), ("max", max)):
                rows.append([TOOL, a, "%s_%s" % (col, q), "%.2f" % f(x), "%s of counted runs (%s)" % (q, what)])
        else:
            for q in ("median", "min", "max"):
                rows.append([TOOL, a, "%s_%s" % (col, q), "not measurable",
                             "%d counted runs, fewer than 3 or a value not read" % len(C[a])])

    for a in ARMS:
        rows.append([TOOL, a, "runs_started", runs[a], "rows of clock-runs.csv for this arm"])
        rows.append([TOOL, a, "runs_counted", len(C[a]), "rc 0, tree identical, no other growth seen, others under 1.0"])
        stats(a, "run_cpu_seconds", "CPU seconds of the growth, the runner's reaped children")
        rows.append([TOOL, a, "rule_cpu_median_below_HV3_min", rule(a, "run_cpu_seconds"), "declared in growth-exact-fixes-88/DECLARATION.md before any number"])
        stats(a, "wall_clock_seconds", "peak.py")
        rows.append([TOOL, a, "rule_wall_median_below_HV3_min", rule(a, "wall_clock_seconds"), "declared in growth-exact-fixes-88/DECLARATION.md before any number"])
        stats(a, "cores_busy_over_run", "cores busy on the machine over the run, /proc/stat")
        stats(a, "cores_busy_others_over_run", "cores busy minus run CPU over wall")
    with open(dest, "w", newline="") as f:
        cw = csv.writer(f, lineterminator="\n")
        cw.writerow(["tool", "arm", "quantity", "value", "what_it_is"])
        cw.writerows(rows)
    d = {(r[1], r[2]): r[3] for r in rows}
    print("; ".join("%s n %d cpu median %s wall median %s: cpu %s, wall %s" % (
        a, len(C[a]), d[(a, "run_cpu_seconds_median")], d[(a, "wall_clock_seconds_median")],
        rule(a, "run_cpu_seconds"), rule(a, "wall_clock_seconds")) for a in ARMS))


if __name__ == "__main__":
    main()
