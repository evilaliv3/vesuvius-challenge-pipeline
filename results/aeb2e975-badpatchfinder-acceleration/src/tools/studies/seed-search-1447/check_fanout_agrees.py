#!/usr/bin/env python3
"""Refuse if evidence/alignment-fanout.csv has drifted from evidence/per-seed.csv.

The fan out file copies five columns from per-seed.csv so that a tool can join the fan out and
the square in one read. A copy drifts: on 2026-09-22 it read `not measurable` for seeds 34, 35
and 44 while per-seed.csv measured 5.2008, 7.6721 and 11.1968, so anything joining on it was
silently losing three of the nine points and would have drawn a figure with eight.

Exit 0 if they agree, 1 if they do not, naming every disagreement.
"""
import csv
import os
import sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIED = ("largest_square_mm_min_step", "traced_area_mm2", "in_the_distribution",
          "downstream_return_code", "growth_return_code")

# The columns this file MEASURES rather than copies. They are not compared against per-seed.csv,
# which does not carry them; they are checked for being absent on a row whose tree exists. On
# 2026-09-22 seed44 read `not measurable` in every one of them for hours after its clean regrowth,
# because this guard compared only the copies and passed. A check that looks only at what it was
# built to look at is rule (a) of coordinator.md section 2, and this is that rule turned on the
# guard itself.
MEASURED = ("edges", "keys", "patch_files", "keys_without_a_patch_file", "fan_out",
            "chain_cost_at_length_5")
TREES = "/data/scrollagent/runs/rev1/seed-search-1447/out"


def rows_of(p):
    lines = open(p).read().splitlines(True)
    if lines[0].lstrip().startswith('"#') or lines[0].lstrip().startswith('#'):
        lines = lines[1:]
    return list(csv.DictReader(lines))


def main():
    per = {r["attempt"]: r for r in rows_of(os.path.join(S, "evidence", "per-seed.csv"))}
    fan = rows_of(os.path.join(S, "evidence", "alignment-fanout.csv"))
    bad = []
    for r in fan:
        p = per.get(r["attempt"])
        if not p:
            bad.append((r["attempt"], "attempt", "absent from per-seed.csv", ""))
            continue
        for c in COPIED:
            if c in r and c in p and r[c] != p[c]:
                bad.append((r["attempt"], c, r[c], p[c]))
        # and the measured columns: absent is only allowed when there is no tree to measure
        rel = os.path.join(TREES, r["attempt"], "growth", "rel.csv")
        if os.path.exists(rel):
            for c in MEASURED:
                if r.get(c, "") == "not measurable":
                    bad.append((r["attempt"], c, "not measurable",
                                "the tree exists at %s, so it can be measured" % rel))
    for a, c, x, y in bad:
        print("  %-22s %-30s fan out says %-16s per-seed says %s" % (a, c, x, y))
    print("%d disagreement(s) over %d rows and %d copied columns"
          % (len(bad), len(fan), len(COPIED)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
