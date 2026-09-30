#!/usr/bin/env python3
"""traced_sum.py: evidence/traced-reference.csv from scratch/traced/<seed>.json (area90.py traced), the known reference:
traced_area.py's own functions on each seed's delivered sheets against chain-0826/evidence/area-<seed>.csv, and the sum over
seeds with no dedup between seeds against the queue file's traced_area_mm2 sum."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import area90 as A
A.TOOL = "area-0826-90/tools/traced_sum.py"  # the CSV header names this tool
rows, tot, totq, bad = [], 0.0, 0.0, 0
for seed, n, q in A.seeds_frozen():
    p = A.SCR + "/traced/%s.json" % seed
    if not os.path.isfile(p):
        raise SystemExit("REFUSED: %s missing" % p)
    d = json.load(open(p))
    tot += d["traced_area_mm2"]; totq += q
    ok = d["equal"] == "yes" and "%.1f" % q == d["area_csv_traced_area_mm2"]
    bad += not ok
    rows.append([seed, d["files"], d["points"], d["spacing"], "%.1f" % d["traced_area_mm2"], d["area_csv_traced_area_mm2"],
                 "%.1f" % q, "yes" if ok else "no"])
rows.append(["sum over %d seeds, no dedup between seeds, cm2" % len(rows), "", "", "", "%.4f" % (tot / 100), "",
             "%.4f" % (totq / 100), "yes" if abs(tot - totq) < 0.05 * len(rows) and not bad else "no"])
A.write_csv(A.EV + "/traced-reference.csv", "known reference: pipeline/tools/traced_area.py patch_files, spacing and "
            "union_cells imported and run on chain-0826/out/<seed>/sheets, voxel %s um from voxel.py; against "
            "evidence/area-<seed>.csv and the traced_area_mm2 column of per-seed-queue.csv" % A.VOX_UM,
            ["seed", "files", "points", "spacing_vox", "traced_area_mm2_here", "area_csv_traced_area_mm2",
             "queue_traced_area_mm2", "equal"], rows)
print("traced sum %.4f cm2 here, %.4f in the queue file, %d seeds differing" % (tot / 100, totq / 100, bad))
