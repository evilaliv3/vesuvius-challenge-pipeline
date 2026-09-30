#!/usr/bin/env python3
"""stevens-remedy-half-on: the ten seeds by the rule of DECLARATION.md (all-55, in_set yes, sorted as strings,
random.Random(20260925).sample(list, 10)); writes evidence/ten-seeds.csv."""
import csv, random, subprocess

R1 = "/data/scrollagent/runs/rev1"
SRC = R1 + "/coverage-union-1447/evidence/union-seed-lists-2026-09-25.csv"
OUT = R1 + "/stevens-remedy-half-on/evidence/ten-seeds.csv"
rows = list(csv.DictReader(l for l in open(SRC, newline="") if not l.startswith('"#')))
pool = sorted(r["attempt"] for r in rows if r["seed_set"] == "all-55" and r["in_set"] == "yes")
assert len(pool) == 55, len(pool)
ten = random.Random(20260925).sample(pool, 10)
t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
with open(OUT, "w", newline="") as fh:
    fh.write("# written by stevens-remedy-half-on/tools/draw_seeds.py at %s: random.Random(20260925).sample of the %d "
             "all-55 in_set yes attempts of coverage-union-1447/evidence/union-seed-lists-2026-09-25.csv sorted as "
             "strings; draw_order 1 is the identity seed\n" % (t, len(pool)))
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["draw_order", "attempt", "pool_size"])
    for k, a in enumerate(ten, 1):
        w.writerow([k, a, len(pool)])
print(" ".join(ten))
