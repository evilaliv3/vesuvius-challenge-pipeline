#!/usr/bin/env python3
"""cuts-2715/tools/air_ref.py: VAL <= 57 share on the 2715 S0 square as reference for the headline air proxy (DECLARATION addition).
-> evidence/air-reference.csv. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."""
import csv, subprocess
import numpy as np
RR = "/data/scrollagent/runs/rev1/render-routes-0826"
V = np.load(RR + "/scratch/values-R2dnative-PHerc0826-seed2715-S0-sq.npz")["VAL"].astype(float)[86:86 + 1120, 126:126 + 1120]
m = np.isfinite(V)
t = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
row = dict(utc=t, route="R2dnative", surface="PHerc0826-seed2715-S0-sq", cells=V.size, cells_measurable=int(m.sum()),
           cells_le_57=int((V[m] <= 57).sum()), share_le_57_of_measurable="%.4f" % (V[m] <= 57).mean(), square_median="%.1f" % np.median(V[m]),
           share_le_57_dark_corner_rows850_cols930="%.4f" % (V[850:, 930:][m[850:, 930:]] <= 57).mean())
with open("/data/scrollagent/runs/rev1/cuts-2715/evidence/air-reference.csv", "w", newline="") as f:
    f.write("# written by cuts-2715/tools/air_ref.py at %s: VAL <= 57 on the 2715 S0 square, reference for headline-air.csv\n" % t)
    w = csv.DictWriter(f, list(row), lineterminator="\n"); w.writeheader(); w.writerow(row)
print(row)
