#!/usr/bin/env python3
"""What the series costs on a small tree, and the run to run spread it has to be read against.

On seeds 01, 15 and 26 the enumeration this study attacks is a few seconds of a forty second
stage, so the series should read the same as the untouched binary there. It does not. This tool
reads back from evidence/runs.csv the repeated runs of the same tree with three binaries, all at
four threads on the same shared machine, and writes the spread beside the difference, so that the
difference is not reported as an effect unless it is larger than the spread.

Writes evidence/small-tree-cost.csv.
"""
import csv, os, statistics, sys

S = "/data/scrollagent/runs/rev1/c-stage-cost"
ATTEMPT = "PHerc1447-seed26"
GROUPS = {
    "plain (the binary that wrote the sheets)": ["spread-plain-1", "spread-plain-2",
                                                 "spread-plain-3", "plain-4threads"],
    "guarded (00007 only)": ["spread-guarded-1", "spread-guarded-2", "spread-guarded-3"],
    "00007 and 00008": ["spread-c1-1", "spread-c1-2", "spread-c1-3"],
    "00007, 00008 and 00009": ["spread-c2-1", "spread-c2-2", "spread-c2-3"],
}


def main():
    rows = []
    with open(os.path.join(S, "evidence", "runs.csv")) as f:
        for r in csv.reader(l for l in f if not l.startswith("#")):
            if r and r[0] != "tag":
                rows.append(r)
    out = os.path.join(S, "evidence", "small-tree-cost.csv")
    with open(out, "w", newline="") as fh:
        fh.write("# repeated runs of the c stage of PHerc1447-seed26, all at four threads on the "
                 "same shared machine within one hour, read back from evidence/runs.csv column "
                 "seconds on the rows whose stage is c. runs is how many; min, median and max are "
                 "of those seconds; spread is max minus min and is what a difference has to beat "
                 "before it is called an effect. The tags are in the tag column of runs.csv.\n")
        w = csv.writer(fh)
        w.writerow(["series", "attempt", "runs", "min_seconds", "median_seconds", "max_seconds",
                    "spread_seconds", "tags"])
        for name, tags in GROUPS.items():
            vals = [float(r[5]) for r in rows if r[0] in tags and r[1] == ATTEMPT and r[4] == "c"]
            if not vals:
                continue
            w.writerow([name, ATTEMPT, len(vals), "%.1f" % min(vals),
                        "%.1f" % statistics.median(vals), "%.1f" % max(vals),
                        "%.1f" % (max(vals) - min(vals)), " ".join(tags)])
            print("%-42s n=%d  min %.1f  median %.1f  max %.1f  spread %.1f"
                  % (name, len(vals), min(vals), statistics.median(vals), max(vals),
                     max(vals) - min(vals)))
    print("written to %s" % out)


if __name__ == "__main__":
    sys.exit(main())
