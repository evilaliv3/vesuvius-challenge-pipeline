#!/usr/bin/env python3
"""What one delivered ribbon costs, with the quiet bench's seconds where they exist.

evidence/cost-per-ribbon.csv was written before the quiet bench and takes every `c` stage from
the shared machine. Three of its six seeds have since been measured again with nothing else
running, and one of the three, seed26, had a «before» taken at twenty four threads against an
«after» at four, which is not a pair at all. This recomputes the table with the quiet seconds
where they exist and writes it BESIDE the old file, never over it: the old one is the record of
what was believed.

Which second replaces which: the quiet bench's `plain` arm is the untouched binary, so it
replaces `c_stage_before`, and its `c2` arm replaces `c_stage_after`. Medians over the runs that
finished, from quiet-bench/evidence/c-stage-runs.csv, and the row says for each seed whether its
seconds are quiet or shared.

Rule of 2026-09-22T04:17:45Z: the expected row count and the count written are both in the file.
"""
import csv, os, statistics, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = os.path.join(S, "evidence", "cost-per-ribbon.csv")
BENCH = "/data/scrollagent/runs/rev1/quiet-bench/evidence/c-stage-runs.csv"
OUT = os.path.join(S, "evidence", "cost-per-ribbon-quiet.csv")


def rows(path):
    with open(path) as fh:
        lines = fh.readlines()
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith(('"#', '#')):
        i += 1
    return list(csv.DictReader(lines[i:]))


def main():
    for p in (OLD, BENCH):
        if not os.path.exists(p):
            sys.exit("missing %s" % p)
    old = rows(OLD)
    quiet = {}
    for r in rows(BENCH):
        if r["return_code"] != "0" or r["cap_bit"] == "yes":
            continue
        quiet.setdefault((r["attempt"], r["tag"]), []).append(float(r["seconds"]))

    out = []
    for r in old:
        a = r["attempt"]
        before, after = float(r["c_stage_before"]), float(r["c_stage_after"])
        src = "shared machine, as the old file had it"
        p, c = quiet.get((a, "plain")), quiet.get((a, "c2"))
        if p and c:
            before, after = statistics.median(p), statistics.median(c)
            src = "quiet bench, medians of %d and %d runs" % (len(p), len(c))
        g = float(r["growth_seconds"])
        out.append({
            "attempt": a, "kind": r["kind"], "fan_out": r["fan_out"],
            "growth_seconds": "%.0f" % g,
            "c_stage_before": "%.1f" % before, "c_stage_after": "%.1f" % after,
            "where_the_c_seconds_come_from": src,
            "growth_plus_c_before": "%.1f" % (g + before),
            "growth_plus_c_after": "%.1f" % (g + after),
        })

    n = len(out)
    if n != len(old):
        sys.exit("expected %d rows and built %d" % (len(old), n))
    quiet_n = sum(1 for r in out if r["where_the_c_seconds_come_from"].startswith("quiet"))

    def tot(kind, col):
        return sum(float(r[col]) for r in out if kind is None or r["kind"] == kind)

    with open(OUT, "w", newline="") as fh:
        fh.write('"# what one delivered ribbon costs in machine time, recomputed by '
                 'tools/cost_per_ribbon.py with the quiet bench\'s seconds where they exist. '
                 'growth_seconds is unchanged and was measured with two or three growths in '
                 'parallel, so it is a cost record and not a result. The c seconds of %d of the '
                 '%d seeds are the quiet bench\'s, medians of the runs that finished, and the '
                 'column beside them says so per row. Written beside '
                 'evidence/cost-per-ribbon.csv and not over it."\n' % (quiet_n, n))
        w = csv.writer(fh)
        w.writerow(list(out[0].keys()))
        for r in out:
            w.writerow(list(r.values()))
        w.writerow([])
        w.writerow(["# totals, recomputed here and not carried"])
        for kind in ("ribbon", "tangle", None):
            lab = kind or "all six"
            w.writerow(["total %s" % lab, "", "",
                        "%.0f" % tot(kind, "growth_seconds"),
                        "%.1f" % tot(kind, "c_stage_before"),
                        "%.1f" % tot(kind, "c_stage_after"), "",
                        "%.1f" % tot(kind, "growth_plus_c_before"),
                        "%.1f" % tot(kind, "growth_plus_c_after")])
    print("wrote %s, %d rows, %d of them with quiet seconds" % (OUT, n, quiet_n))
    for r in out:
        print("  %-18s %-7s growth %7s  before %9s  after %8s  %s"
              % (r["attempt"], r["kind"], r["growth_seconds"], r["c_stage_before"],
                 r["c_stage_after"], r["where_the_c_seconds_come_from"][:30]))
    for kind in ("ribbon", "tangle", None):
        lab = kind or "all six"
        print("  total %-8s before %10.1f s  after %9.1f s  per seed after %.2f h"
              % (lab, tot(kind, "growth_plus_c_before"), tot(kind, "growth_plus_c_after"),
                 tot(kind, "growth_plus_c_after") / (3 if kind else 6) / 3600.0))


if __name__ == "__main__":
    main()
