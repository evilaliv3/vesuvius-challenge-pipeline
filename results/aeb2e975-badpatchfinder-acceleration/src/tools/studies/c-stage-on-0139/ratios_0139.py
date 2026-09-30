#!/usr/bin/env python3
"""The c stage on the reference scroll: each arm against the untouched one, tree by tree.

Read from evidence/c-stage-times.csv (which tools/summarise.py writes from runs.csv) and from
evidence/trees.csv for the size of each tree. Nothing is averaged across trees and no
superlative is written here: a reader computes those over every row.

Two things this file carries that a bare ratio does not:

  ranges_overlap  whether the two arms' [min, max] over four runs each touch. A ratio whose
                  arms overlap is a ratio the runs cannot tell apart, and saying so in a
                  column is the only way the reader sees it at the ratio. This is the check
                  of the rule of 2026-09-22T02:17:25Z, as a column and not as a sentence.
  cores_busy      the widest reading of the two arms. These runs were taken on a shared
                  machine, up to 12.1 cores busy of 24, and a ratio of two timings taken at
                  different loads is worth less than one from the quiet bench. The column is
                  here so that is visible at the number rather than in a note.

Rule of 2026-09-22T04:17:45Z: the expected row count is stated and the tool refuses when the
count it got differs.
"""
import csv, os, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMES = os.path.join(S, "evidence", "c-stage-times.csv")
TREES = os.path.join(S, "evidence", "trees.csv")
OUT = os.path.join(S, "evidence", "c-stage-ratios.csv")
# The three comparisons worth making, and why each: plain against guarded isolates the orphan
# guard (00007) alone, plain against c2 is the pull request as a whole, and guarded against c2
# isolates the two changes under test (00008 and 00009) from the guard they sit on top of.
# evidence/binaries.csv is what says which patches each arm carries.
PAIRS = [("plain", "guarded"), ("plain", "c2"), ("guarded", "c2")]


def rows_of(path):
    with open(path) as fh:
        lines = fh.readlines()
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith(('"#', '#')):
        i += 1
    return list(csv.DictReader(lines[i:]))


def main():
    times = rows_of(TIMES)
    trees = {r["tree"]: r for r in rows_of(TREES)}
    by = {}
    order = []
    for r in times:
        by[(r["tree"], r["arm"])] = r
        if r["tree"] not in order:
            order.append(r["tree"])
    have = {r["arm"] for r in times}
    for a, b_ in PAIRS:
        for arm in (a, b_):
            if arm not in have:
                sys.exit("arm %s is not in %s" % (arm, TIMES))

    expected = len(order) * len(PAIRS)
    out = []
    for tree in order:
        t = trees.get(tree, {})
        for base, arm in PAIRS:
            b = by.get((tree, base))
            o = by.get((tree, arm))
            if b is None:
                sys.exit("no %s arm on tree %s" % (base, tree))
            if o is None:
                sys.exit("no %s arm on tree %s" % (arm, tree))
            bmin, bmax = float(b["min_seconds"]), float(b["max_seconds"])
            omin, omax = float(o["min_seconds"]), float(o["max_seconds"])
            overlap = not (omax < bmin or bmax < omin)
            out.append({
                "tree": tree,
                "patch_files": t.get("patch_files", "not measurable"),
                "baseline_arm": base,
                "rel_edges": t.get("rel_edges", "not measurable"),
                "fan_out": t.get("fan_out", "not measurable"),
                "arm": arm,
                "runs_baseline": b["runs"],
                "runs_this_arm": o["runs"],
                "median_baseline_seconds": b["median_seconds"],
                "median_this_arm_seconds": o["median_seconds"],
                "ratio_median_over_median": "%.3f" % (float(b["median_seconds"])
                                                      / float(o["median_seconds"])),
                "range_baseline_seconds": "%s to %s" % (b["min_seconds"], b["max_seconds"]),
                "range_this_arm_seconds": "%s to %s" % (o["min_seconds"], o["max_seconds"]),
                "ranges_overlap": "yes" if overlap else "no",
                "what_the_overlap_means": ("the four runs of each arm cannot tell these two "
                                           "apart on this tree" if overlap else
                                           "the two arms do not overlap on this tree, so the "
                                           "difference is larger than the runs' own spread"),
                "cores_busy_widest": "%s to %s" % (
                    min(b["cores_busy_min"], o["cores_busy_min"], key=float),
                    max(b["cores_busy_max"], o["cores_busy_max"], key=float)),
            })

    got = len(out)
    if got != expected:
        sys.exit("expected %d rows (%d trees times %d pairs), built %d"
                 % (expected, len(order), len(PAIRS), got))

    with open(OUT, "w", newline="") as fh:
        fh.write('"# one row per tree per arm of PHerc0139, the untouched arm against that arm, '
                 'written by tools/ratios_0139.py from evidence/c-stage-times.csv and '
                 'evidence/trees.csv. Three pairs per tree: plain against guarded is the orphan '
                 'guard 00007 alone, plain against c2 is the whole pull request, guarded '
                 'against c2 is 00008 and 00009 on top of the guard (evidence/binaries.csv, '
                 'column corrections_present). ratio_median_over_median is the baseline median '
                 'over the arm median, so above 1 means the arm is faster. ranges_overlap answers, in a '
                 'column, whether four runs of each arm can tell the two apart at all: a ratio '
                 'on an overlapping pair is not a measured difference. cores_busy_widest is the '
                 'widest reading over both arms and these runs were taken on a SHARED machine, '
                 'unlike the quiet bench of PLAN 58. Expected rows %d, written %d, and the tool '
                 'refuses rather than write a short file."\\n' % (expected, got))
        w = csv.writer(fh)
        w.writerow(list(out[0].keys()))
        for r in out:
            w.writerow(list(r.values()))
    print("wrote %s, %d rows (%d trees, %d pairs)" % (OUT, got, len(order), len(PAIRS)))
    for r in out:
        print("  %-7s %-8s over %-8s %7s over %-7s = %-6s  overlap %-3s  busy %s"
              % (r["tree"], r["baseline_arm"], r["arm"], r["median_baseline_seconds"],
                 r["median_this_arm_seconds"], r["ratio_median_over_median"],
                 r["ranges_overlap"], r["cores_busy_widest"]))


if __name__ == "__main__":
    main()
