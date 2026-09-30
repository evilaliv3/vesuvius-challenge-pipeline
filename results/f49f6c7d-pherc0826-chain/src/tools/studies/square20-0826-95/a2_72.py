#!/usr/bin/env python3
"""a2_72.py <seed>: PLAN item 95 (c). New file, 2026-09-28T12:5xZ, coordinator agent. Imports chain-0826/tools/
a2_cluster_seed.py unchanged and runs its measure_seed and write with use_scroll("PHerc0826", this study), so the sheets
are out/<seed>/sheets/patches/ of the regrowth (measure72.sh links them from C80) and the squares file is this study's
evidence/squares-<seed>.csv. Output evidence/a2-cluster/<seed>.csv."""
import os, sys
sys.path.insert(0, "/data/scrollagent/runs/rev1/chain-0826/tools")
import a2_cluster_seed as A  # noqa: E402

S = "/data/scrollagent/runs/rev1/square20-0826-95"
A.use_scroll("PHerc0826", S)
A.TOOL = "square20-0826-95/tools/a2_72.py (chain-0826/tools/a2_cluster_seed.py imported unchanged)"
seed = sys.argv[1]
os.makedirs(S + "/evidence/a2-cluster", exist_ok=True)
out = S + "/evidence/a2-cluster/%s.csv" % seed
rows, T, St = A.measure_seed(seed)
A.write(out, rows, T, St, "one row per delivered sheet of %s, g 72000 regrowth, C80" % seed)
print("written %s: %d sheets" % (out, len(rows)))
