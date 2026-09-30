#!/usr/bin/env python3
"""Where in seed34's rel.csv do the rows that name a patch with no geometry sit.

rel.csv is written at simpaper10.cpp:557 of the built corrected copy: one row per alignment, the
first column the key of the alignment map, which is the patch the round had just grown, the
second the id the aligner read out of surface.bp. This reads the file once and reports, for three
populations of second column ids, how many rows name them and what the first column of those rows
is: if the ids came from an earlier run's points left in surface.bp, the rows that name them are
the early rounds, before those points were overwritten.
"""
import csv, os, statistics, sys

REL = "/data/scrollagent/runs/rev1/seed-search-1447/out/PHerc1447-seed34/growth/rel.csv"
ORPH = "/data/scrollagent/runs/rev1/badpatch-crash/evidence/orphan-patches.csv"
IMP = "/data/scrollagent/runs/rev1/growth-bookkeeping/evidence/impossible-ids-seed34.csv"
OUT = "/data/scrollagent/runs/rev1/growth-bookkeeping/evidence/orphan-rows.csv"


def main():
    orph = {int(r["patch"]) for r in csv.DictReader(open(ORPH))}
    imp = set()
    for r in csv.reader(open(IMP)):
        if r and not r[0].startswith("#") and r[0] != "patch_id":
            imp.add(int(r[0]))
    pops = {"orphan_ids_104": orph, "impossible_ids_413": imp,
            "impossible_and_orphan_86": imp & orph, "every_row": None}
    first = {k: [] for k in pops}
    rows = 0
    col0 = set()
    col1 = set()
    with open(REL) as fh:
        for line in fh:
            i = line.find(",")
            j = line.find(",", i + 1)
            if i < 0 or j < 0:
                continue
            a = int(line[:i]); b = int(line[i + 1:j])
            rows += 1
            col0.add(a); col1.add(b)
            for k, s in pops.items():
                if s is None or b in s:
                    first[k].append(a)
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# seed34's growth rel.csv read once. population: which second column ids the "
                    "row must name. rows: how many rows name one of them. "
                    "first_column_min/median/max: the patch that had just been grown when the row "
                    "was written, which orders the rows in time. total_rows, distinct_first_column "
                    "and distinct_second_column describe the whole file."])
        w.writerow(["population", "rows", "first_column_min", "first_column_median",
                    "first_column_max", "total_rows", "distinct_first_column",
                    "distinct_second_column"])
        for k in ["every_row", "orphan_ids_104", "impossible_ids_413", "impossible_and_orphan_86"]:
            v = first[k]
            w.writerow([k, len(v), min(v) if v else "", int(statistics.median(v)) if v else "",
                        max(v) if v else "", rows, len(col0), len(col1)])
    print(open(OUT).read())


if __name__ == "__main__":
    sys.exit(main())
