#!/usr/bin/env python3
"""The factor of each step of the growth acceleration, one quiet session at a time, on PHerc0826 only
(director 2026-09-28T08:03:17Z: the article measures the assembly on PHerc0826 alone).

Listed in runs/rev1/quiet-bench/FACTOR-SWEEP.md before its first write. Each row divides the median
of the old arm by the median of the new arm, BOTH from one clock summary of one quiet session (a
factor across two sessions is never written), and carries both medians, both run counts and both
ranges beside it. The growths of every counted run had trees identical to the old arm's (column
runs_counted of the summaries: «rc 0, tree identical, no other growth seen»).

Usage: speed_factors.py [--out PATH]
"""
import argparse, csv, os, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(S, "evidence", "studies")
STEPS = [  # step, scroll and seed, summary file, old arm, new arm, what changes
    ("hash and AVX-512 to MLP", "PHerc0826-seed237", "growth-exact-fixes-88/clock-summary-PHerc0826-seed237.csv", "HV3", "STACK"),
    ("zstd copy to LZ4HC copy, MLP", "PHerc0826-seed237", "hot-lines-88/clock-summary.csv", "Z", "L"),
]


def rd(rel):
    with open(os.path.join(EV, rel), newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))))


def val(rows, arm, q, rel):
    hit = [r for r in rows if r["arm"] == arm and r["quantity"] == q]
    if len(hit) != 1:
        sys.exit("speed_factors.py: %s: %d rows for %s %s" % (rel, len(hit), arm, q))
    return hit[0]["value"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "speed-factors.csv"))
    a = ap.parse_args()
    out = []
    for step, seed, rel, old, new in STEPS:
        rows = rd(rel)
        for clock, q in (("cpu", "run_cpu_seconds"), ("wall", "wall_clock_seconds")):
            om, nm = float(val(rows, old, q + "_median", rel)), float(val(rows, new, q + "_median", rel))
            out.append({"step": step, "seed": seed, "clock": clock, "old_arm": old, "new_arm": new,
                        "old_median_s": "%.2f" % om, "new_median_s": "%.2f" % nm,
                        "factor": "%.2f" % (om / nm),
                        "factor_is": "old median over new median (%.2f over %.2f)" % (om, nm),
                        "old_runs": val(rows, old, "runs_counted", rel), "new_runs": val(rows, new, "runs_counted", rel),
                        "old_range_s": "%s to %s" % (val(rows, old, q + "_min", rel), val(rows, old, q + "_max", rel)),
                        "new_range_s": "%s to %s" % (val(rows, new, q + "_min", rel), val(rows, new, q + "_max", rel)),
                        "old_cores_busy_median": val(rows, old, "cores_busy_over_run_median", rel),
                        "new_cores_busy_median": val(rows, new, "cores_busy_over_run_median", rel),
                        "source": rel})
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/speed_factors.py at %s: one row per step and clock, each from one quiet '
                 'session; factor = old median over new median, both named in factor_is"\n' % now)
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for r in out:
        print("  %-32s %-19s %-4s %s" % (r["step"], r["seed"], r["clock"], r["factor_is"]), r["factor"])


if __name__ == "__main__":
    main()
