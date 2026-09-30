#!/usr/bin/env python3
"""Figure C15, a raster: item 91's arms C and D of one seed on the same axial slice of PHerc. 0826, same crop and
scale; the drawing is figure C13's (src/tools/c-f13-setseed.py, imported), pointed at item 91's sheets.

Why C and D, and not A and B. Item 91 (runs/rev1/stevens-changes-0826-91) grows the same seeds under four codes.
B is A plus the bad patch finder changes of work S; D is C plus the SetSeed patch alone. The pair that isolates the bad
patch finder, A against B, gives sheets that are byte identical on every seed where both ran: this script counts
that from the sha256 column of the two arms' squares CSVs and writes it as a row, and a picture of two identical
panels would say nothing more than that row. So the before and after picture is drawn for D against C, the pair
whose only difference is SetSeed.

Which seed, declared before drawing: among the seeds where both C and D have a squares CSV, the one whose C run has
the lower median of the per run largest square (square_mm_min_step, max over sheets), ties by seed name. Neither
arm's result for the drawn seed chooses it beyond that rank.

The squares CSVs are read from this work's snapshot under evidence/studies when present, else from the live study;
the rows say which. NO INK: a plane of the scan and sheet geometry only.

Usage: c-f15-setseed-91.py [--out CSV] [--png PNG]
"""
import argparse
import csv
import glob
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figlib  # noqa: E402

FIGURE = "c-f15-setseed-91"
RUNS = "/data/scrollagent/runs/rev1"
S91 = "stevens-changes-0826-91"


def rows_of(path):
    lines = [l for l in open(path, newline="") if not l.lstrip('"').startswith("#")]
    return list(csv.DictReader(lines))


def squares(here, arm, seed):
    rel = "%s/evidence/measures/squares-%s-%s.csv" % (S91, arm, seed)
    shipped = os.path.join(here, "evidence/studies", S91, "measures", "squares-%s-%s.csv" % (arm, seed))
    p = shipped if os.path.exists(shipped) else os.path.join(RUNS, rel)
    return (p, rel) if os.path.exists(p) else (None, rel)


def best_mm(path):
    v = [float(r["square_mm_min_step"]) for r in rows_of(path)
         if r["status"] == "measured" and figlib.number(r["square_mm_min_step"]) is not None]
    return max(v) if v else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()
    here = os.path.dirname(HERE)
    extra = []

    def put(what, source_file, source_column, value, key=""):
        extra.append(dict(key=key, panel="a;b", what=what, source_file=source_file, source_column=source_column,
                          value=value))

    seeds = sorted({os.path.basename(p)[len("squares-C-"):-4]
                    for p in glob.glob(os.path.join(RUNS, S91, "evidence/measures/squares-C-*.csv"))})
    both, ab_seeds, ab_same, ab_total = [], 0, 0, 0
    for s in seeds:
        pc, _ = squares(here, "C", s)
        pd, _ = squares(here, "D", s)
        if pc and pd and best_mm(pc) is not None and best_mm(pd) is not None:
            both.append((best_mm(pc), s))
    for s in sorted({os.path.basename(p)[len("squares-A-"):-4]
                     for p in glob.glob(os.path.join(RUNS, S91, "evidence/measures/squares-A-*.csv"))}):
        pa, _ = squares(here, "A", s)
        pb, _ = squares(here, "B", s)
        if not (pa and pb):
            continue
        ha = {r["sheet"]: r["sha256"] for r in rows_of(pa)}
        hb = {r["sheet"]: r["sha256"] for r in rows_of(pb)}
        ab_seeds += 1
        for k in sorted(set(ha) | set(hb)):
            ab_total += 1
            ab_same += int(ha.get(k) is not None and ha.get(k) == hb.get(k))
    if not both:
        raise SystemExit("no seed of item 91 has both C and D squares")
    both.sort()
    pick = both[(len(both) - 1) // 2]
    seed = pick[1]
    put("seeds of item 91 with C and D squares", S91 + "/evidence/measures/squares-{C,D}-*.csv", "files", len(both),
        key="seeds_cd")
    put("seed drawn: lower median of C's largest square over those seeds", S91 + "/evidence/measures/squares-C-*.csv",
        "square_mm_min_step (max over sheets)", "%s at %.4f" % (seed, pick[0]))
    put("seeds of item 91 with A and B squares", S91 + "/evidence/measures/squares-{A,B}-*.csv", "files", ab_seeds,
        key="seeds_ab")
    put("sheets of those seeds byte identical between A and B", S91 + "/evidence/measures/squares-{A,B}-*.csv",
        "sha256", ab_same, key="ab_identical_sheets")
    put("sheets of those seeds", S91 + "/evidence/measures/squares-{A,B}-*.csv", "sheet", ab_total, key="ab_sheets")

    spec = importlib.util.spec_from_file_location("c_f13", os.path.join(HERE, "c-f13-setseed.py"))
    c13 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c13)
    argv = ["--seed", seed,
            "--before", S91 + "/scratch/coll/C-{seed}/C40", "--before-squares", S91 + "/evidence/measures/squares-C-{seed}.csv",
            "--before-name", "C, without SetSeed",
            "--after", S91 + "/scratch/coll/D-{seed}/C40", "--after-squares", S91 + "/evidence/measures/squares-D-{seed}.csv",
            "--after-name", "D, with SetSeed"]
    if a.out:
        argv += ["--out", a.out]
    if a.png:
        argv += ["--png", a.png]
    c13.main(argv, figure=FIGURE, extra_rows=extra)


if __name__ == "__main__":
    main()
