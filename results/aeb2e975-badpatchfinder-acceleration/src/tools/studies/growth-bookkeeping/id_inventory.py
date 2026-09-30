#!/usr/bin/env python3
"""seed34's ids: what is on disk, what rel.csv names, and what the log says cannot be this run's.

Three sources, none of them prose:
  the patch files of the growth tree, listed with os.listdir;
  the 104 orphan ids of runs/rev1/badpatch-crash/evidence/orphan-patches.csv;
  the 413 ids of evidence/impossible-ids-seed34.csv, which tools/scan_growth_log.py took from the
  growth log because the aligner named them before this run could have created them.
"""
import csv, os

G = "/data/scrollagent/runs/rev1/seed-search-1447/out/PHerc1447-seed34/growth/patches"
ORPH = "/data/scrollagent/runs/rev1/badpatch-crash/evidence/orphan-patches.csv"
IMP = "/data/scrollagent/runs/rev1/growth-bookkeeping/evidence/impossible-ids-seed34.csv"
OUT = "/data/scrollagent/runs/rev1/growth-bookkeeping/evidence/id-inventory-seed34.csv"

have = {int(f[6:-4]) for f in os.listdir(G) if f.startswith("patch_") and f.endswith(".bin")}
orph = {int(r["patch"]) for r in csv.DictReader(open(ORPH))}
imp = {int(r[0]) for r in csv.reader(open(IMP)) if r and not r[0].startswith("#") and r[0] != "patch_id"}
top = max(imp)
rows = [
    ["patch files on disk", len(have), "os.listdir of the growth tree's patches folder"],
    ["lowest id with a file", min(have), "the same listing"],
    ["highest id with a file", max(have), "the same listing"],
    ["ids between 0 and the highest with no file", len([i for i in range(max(have) + 1) if i not in have]),
     "the numbers from 0 to 36,000 are 36,001 and 28,054 of them have a file; the growth "
     "erases an id whose patch did not grow enough or did not align"],
    ["of those, at or below the highest id the log says cannot be this run's",
     len([i for i in range(top + 1) if i not in have]),
     "the ceiling is %d, the largest id the aligner named before this run could have created it" % top],
    ["orphan ids of badpatch-crash", len(orph), "ids rel.csv names and the patches folder does not have"],
    ["highest orphan id", max(orph), "the same file"],
    ["ids the log says cannot be this run's", len(imp), "evidence/impossible-ids-seed34.csv"],
    ["of those, with no patch file", len(imp - have), "they are orphans"],
    ["of those, with a patch file", len(imp & have),
     "the new run created the same number again, so the rel.csv rows that name them point at "
     "geometry that is not the geometry the alignment was computed against"],
    ["orphans that the log also says cannot be this run's", len(orph & imp), "the intersection"],
    ["orphans the log cannot classify", len(orph - imp),
     "their number is at or below the highest id the run had created when they were named, so the "
     "test cannot tell them from a legitimate target; every one of them is below the ceiling of %d" % top],
]
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# one quantity per row about the patch ids of seed34's growth tree. value is the "
                "number, source says which file or listing it was counted from."])
    w.writerow(["quantity", "value", "source"])
    for r in rows:
        w.writerow(r)
print(open(OUT).read())
