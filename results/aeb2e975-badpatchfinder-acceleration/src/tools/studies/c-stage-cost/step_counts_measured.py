#!/usr/bin/env python3
"""The odometer step counts a counting build of the stage printed, read from its own log.

Two instruments, the same edit (tools/apply_counter.py) on two series: `unpruned` is the source
with the orphan guard alone, the odometer as upstream wrote it, and `pruned` is that source with
00008 and 00009 applied. The sequences column is the size of patchSequences at the end of the
enumeration: the two instruments must agree on it exactly, because 00008 changes which walks are
taken and not which chains are kept.

Usage: step_counts_measured.py <variant> <attempt> <log> [<variant> <attempt> <log> ...]
"""
import csv, os, re, sys

S = "/data/scrollagent/runs/rev1/c-stage-cost"
OUT = os.path.join(S, "evidence", "step-counts-measured.csv")
PAT = re.compile(r"^Odometer steps: length=(\d+) steps=(\d+) sequences=(\d+)")


def main():
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            fh.write("# measured by a counting build of the stage itself: one increment per visit "
                     "of the odometer's while body, printed once per chain length. variant is "
                     "`unpruned` for the source with the orphan guard alone and `pruned` for that "
                     "source with 00008 and 00009. odometer_steps is the count; sequences is the "
                     "number of chains kept, which the two variants must agree on. The counting "
                     "build is an instrument and is not in the delivered series.\n")
            w.writerow(["variant", "attempt", "length", "odometer_steps", "sequences", "log"])
        a = sys.argv[1:]
        for i in range(0, len(a), 3):
            variant, attempt, log = a[i], a[i + 1], a[i + 2]
            for line in open(log, errors="replace"):
                m = PAT.match(line)
                if m:
                    w.writerow([variant, attempt, m.group(1), m.group(2), m.group(3), log])
                    print("%-9s %s length %s: %s steps, %s sequences"
                          % (variant, attempt, m.group(1), m.group(2), m.group(3)))
    print("written to %s" % OUT)


if __name__ == "__main__":
    sys.exit(main())
