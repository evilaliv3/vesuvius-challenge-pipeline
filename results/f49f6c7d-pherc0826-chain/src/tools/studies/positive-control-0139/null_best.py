#!/usr/bin/env python3
"""positive-control-0139/tools/null_best.py SURF: the best k 4 ba of 32 per null copy and of 64 over both, beside the sheet's
best of 32 (lattice), from evidence/control.csv (DECLARATION.md addition 09:13:32Z). Appends evidence/null-best.csv."""
import csv, os, subprocess, sys
S = "/data/scrollagent/runs/rev1/positive-control-0139"; surf = sys.argv[1]
rows = [r for r in csv.DictReader(l for l in open(S + "/evidence/control.csv") if not l.startswith('"#'))
        if r["k_vox"] == "4" and r["surface"] == surf and r["ba"] != "not measurable"]
t = subprocess.run(["date", "-u", "+%FT%TZ"], capture_output=True, text=True).stdout.strip()
def best(v):
    rr = [r for r in rows if r["variant"] in v]
    b = max(rr, key=lambda r: float(r["ba"])) if rr else None
    return len(rr), (b["ba"] if b else "not measurable"), (f"{b['variant']} k{b['orientation_k']} m{b['orientation_m']} {b['direction']} {b['checkpoint']}" if b else "")
sheet = best({"lattice"})
out = []
for name, v in (("nullplus", {"nullplus"}), ("nullminus", {"nullminus"}), ("both copies", {"nullplus", "nullminus"})):
    n, b, w = best(v)
    beyond = "yes" if (b != "not measurable" and sheet[1] != "not measurable" and float(sheet[1]) > float(b)) else "no"
    out.append(["positive-control-0139/tools/null_best.py", t, surf, name, n, b, w, sheet[0], sheet[1], sheet[2], beyond])
p = S + "/evidence/null-best.csv"; new = not os.path.exists(p)
with open(p, "a", newline="") as f:
    if new:
        f.write('"# written by positive-control-0139/tools/null_best.py; best k 4 balanced accuracy over the rows of each null copy (run_one_v2 gap minima copies, the sheet centring) against the sheet lattice best of 32, same labels and pixel rule; sheet_beyond_null = sheet best above the null best"\n')
        csv.writer(f).writerow(["tool", "time", "surface", "null", "null_rows", "null_best_ba", "null_best_row", "sheet_rows", "sheet_best_ba", "sheet_best_row", "sheet_beyond_null"])
    csv.writer(f).writerows(out)
for x in out: print(x[3:])
