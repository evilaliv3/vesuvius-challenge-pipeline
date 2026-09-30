#!/usr/bin/env python3
"""Read the kind of a growth from its log, on a running growth or a finished one.

The rule and its evidence are in OUTCOME.md. The share of the first 100,000 lines matching
`Patch <n> has <m> matches` separates the two kinds on sixteen growths of two scrolls: every
ribbon of ten at or below 0.04977, every tangle of six at or above 0.12002, nothing between.
The threshold below sits in that empty interval and was chosen AFTER those sixteen were seen,
which OUTCOME.md says in the section that states it; it is a fitted number, not a tested one.

Run to run it is stable to 0.00005 on the one seed grown twice with the machine's free memory
differing eightfold (evidence/repeat-control-seed44.csv), against a gap of about 0.07.

Usage: predict_kind.py <growth log> [<growth log> ...]
"""
import os
import sys

N = 100000
THRESHOLD = 0.085          # the midpoint of the empty interval 0.04977 to 0.12002
RIBBON_SEEN_UP_TO = 0.04977
TANGLE_SEEN_DOWN_TO = 0.12002


def share(path):
    hits = total = 0
    with open(path, errors="replace") as f:
        for line in f:
            total += 1
            if line.startswith("Patch ") and line.rstrip().endswith(" matches"):
                hits += 1
            if total >= N:
                return hits / N, total
    return None, total


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    bad = 0
    for p in sys.argv[1:]:
        if not os.path.exists(p):
            print("%s: no such log" % p)
            bad = 1
            continue
        s, total = share(p)
        if s is None:
            print("%s: not measurable yet, %d lines of the %d the rule needs" % (p, total, N))
            continue
        kind = "tangle" if s > THRESHOLD else "ribbon"
        where = ("inside the band every ribbon has been in" if s <= RIBBON_SEEN_UP_TO else
                 "inside the band every tangle has been in" if s >= TANGLE_SEEN_DOWN_TO else
                 "in the empty interval between the two bands, which nothing has yet occupied")
        print("%s: share %.5f over the first %d lines -> %s (%s)"
              % (os.path.basename(p), s, N, kind, where))
    return bad


if __name__ == "__main__":
    sys.exit(main())
