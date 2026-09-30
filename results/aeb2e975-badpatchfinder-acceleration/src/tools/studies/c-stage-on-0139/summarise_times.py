#!/usr/bin/env python3
"""The `c` stage time of each arm on each PHerc0139 tree, with its spread, from evidence/runs.csv.

Adapted from runs/rev1/c-stage-cost/tools/summarise_times.py. What was adapted: that tool read one
run per seed and compared it with a reference time recorded elsewhere; this one reads the repeated
runs of this study, groups them by tree and arm, and reports each arm's own spread, because one
run of each is not a time. No reference time from another study enters here.

Two CSVs:

  evidence/c-stage-times.csv    one row per tree and arm: runs, min, median, max, spread.
  evidence/c-stage-diff.csv     one row per tree: plain against c2, and guarded against c2, with
                                the difference of the medians, the difference as a percentage of
                                the plain median, and whether the two arms' observed ranges
                                overlap. When they overlap the verdict reads «not separable from
                                the spread», never a number dressed as an effect.

Only rows whose tag begins with `time-` are read: the pilot runs and the identity runs shared the
machine with other work of this study and are not times.
"""
import collections, csv, os, statistics, subprocess, sys

S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
RUNS = os.path.join(S, "evidence", "runs.csv")
T1 = os.path.join(S, "evidence", "c-stage-times.csv")
T2 = os.path.join(S, "evidence", "c-stage-diff.csv")
ORDER = ["A", "repeat", "b40", "S", "D450", "C", "D150", "P2"]


def main():
    when = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    g = collections.defaultdict(list)
    busy = collections.defaultdict(list)
    with open(RUNS) as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            if r["stage"] != "c" or not r["tag"].startswith("time-"):
                continue
            if r["return_code"] != "0":
                continue
            g[(r["tree"], r["arm"])].append(float(r["seconds"]))
            busy[(r["tree"], r["arm"])].append(float(r["cores_busy_at_start"]))

    keys = sorted(g, key=lambda k: (ORDER.index(k[0]) if k[0] in ORDER else 99, k[1]))
    with open(T1, "w", newline="") as f:
        f.write("# the c stage of one arm on one tree, over the repeated runs of tag time-*. "
                "seconds are the wall clock column of evidence/runs.csv, each run on its own "
                "fresh working copy; runs that returned non zero are excluded and named in the "
                "outcome. cores_busy_min and cores_busy_max are the machine reading taken just "
                "before each of those runs, so a time taken on a loaded machine can be told from "
                "one taken on a quiet one.\n")
        w = csv.writer(f)
        w.writerow(["tree", "arm", "runs", "min_seconds", "median_seconds", "max_seconds",
                    "spread_seconds", "cores_busy_min", "cores_busy_max", "summarised_utc"])
        for k in keys:
            v = sorted(g[k])
            w.writerow([k[0], k[1], len(v), "%.1f" % v[0], "%.1f" % statistics.median(v),
                        "%.1f" % v[-1], "%.1f" % (v[-1] - v[0]),
                        "%.1f" % min(busy[k]), "%.1f" % max(busy[k]), when])

    trees = sorted({t for (t, _) in g}, key=lambda t: ORDER.index(t) if t in ORDER else 99)
    with open(T2, "w", newline="") as f:
        f.write("# one row per tree and per pair of arms. delta_seconds is the median of arm_b "
                "minus the median of arm_a, delta_percent the same as a percentage of arm_a's "
                "median. ranges_overlap is yes when the two arms' observed [min, max] intervals "
                "intersect; when they do, verdict reads 'not separable from the spread' and the "
                "delta is information only.\n")
        w = csv.writer(f)
        w.writerow(["tree", "arm_a", "arm_b", "runs_a", "runs_b", "median_a", "median_b",
                    "delta_seconds", "delta_percent", "ranges_overlap", "verdict",
                    "summarised_utc"])
        for t in trees:
            for a, b in (("plain", "c2"), ("plain", "guarded"), ("guarded", "c2")):
                if (t, a) not in g or (t, b) not in g:
                    continue
                va, vb = sorted(g[(t, a)]), sorted(g[(t, b)])
                ma, mb = statistics.median(va), statistics.median(vb)
                overlap = not (va[-1] < vb[0] or vb[-1] < va[0])
                w.writerow([t, a, b, len(va), len(vb), "%.1f" % ma, "%.1f" % mb,
                            "%+.1f" % (mb - ma), "%+.1f" % (100.0 * (mb - ma) / ma),
                            "yes" if overlap else "no",
                            "not separable from the spread" if overlap
                            else ("%s is slower" % b if mb > ma else "%s is faster" % b), when])
    for p in (T1, T2):
        print("== " + p)
        print(open(p).read())


if __name__ == "__main__":
    sys.exit(main())
