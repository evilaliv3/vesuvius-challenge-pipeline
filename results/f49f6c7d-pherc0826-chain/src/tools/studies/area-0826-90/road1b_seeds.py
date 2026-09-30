#!/usr/bin/env python3
"""road1b_seeds.py: the 12 delivered PHerc0826 seeds nearest seed6365 with largest square >= 10 mm (DECLARATION.md rule)."""
import csv, math, os, subprocess
C = "/data/scrollagent/runs/rev1/chain-0826"
EV = "/data/scrollagent/runs/rev1/area-0826-90/evidence"
L = [l for l in open(C + "/evidence/per-seed-queue.csv") if not l.startswith('"#')]
R = {r["attempt"]: r for r in csv.DictReader(L)}
ref = R["PHerc0826-seed6365"]
p0 = tuple(float(ref[k]) for k in ("seed_x", "seed_y", "seed_z"))
cand = []
for a, r in R.items():
    try:
        sq = float(r["largest_square_mm_min_step"])
    except ValueError:
        continue
    g = "%s/out/%s/growth" % (C, a)
    if not os.path.isdir(g + "/patches"):
        g = "%s/out/%s/C40" % (C, a)
    if not r["delivering_binary"].startswith("delivered") or sq < 10.0:
        continue
    if not os.path.isdir(g + "/patches"):
        continue
    d = math.dist(p0, tuple(float(r[k]) for k in ("seed_x", "seed_y", "seed_z")))
    cand.append((d, a, sq, len(os.listdir(g + "/patches")), g))
cand.sort()
pick = cand[:12]
t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
with open(EV + "/road1b-seeds.csv", "w", newline="") as fh:
    fh.write('"# written by area-0826-90/tools/road1b_seeds.py at %s: delivered PHerc0826 seeds of per-seed-queue.csv with '
             'largest_square_mm_min_step >= 10.0 and a patch folder on disk (growth/patches, else C40/patches), the 12 nearest seed6365; %d qualified"\n' % (t, len(cand)))
    w = csv.writer(fh)
    w.writerow(["rank", "attempt", "distance_vox", "largest_square_mm", "patches", "source"])
    for i, (d, a, sq, n, g) in enumerate(pick):
        w.writerow([i + 1, a, "%.1f" % d, sq, n, g])
print(len(cand), "qualified;", sum(x[3] for x in pick), "patches")
for x in pick:
    print(x)
