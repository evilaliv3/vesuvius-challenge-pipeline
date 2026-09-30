#!/usr/bin/env python3
"""positive-control-0139/tools/labelfree_table.py: evidence/labelfree/<SQID>/summary.csv (run_one_v2's summary_v2 form) of the
four w016 label free runs gathered into evidence/labelfree-w016.csv (rewritten from the summaries each time), with one
verdict row per sheet (DECLARATION.md addition 10:25:19Z): «signal yes on known ink» if any row of the named direction
(reverse) says signal yes, else «no on known ink (the 0826 statistic is blind)»; «not measurable» rows counted apart."""
import csv, glob, os, subprocess
S = "/data/scrollagent/runs/rev1/positive-control-0139"
TOOL = "positive-control-0139/tools/labelfree_table.py"
RUNS = [("A", "A-k3m1-predicted", "predicted k3 m1"), ("A", "A-k2m1-best", "best k2 m1"),
        ("Bx", "Bx-k3m1-predicted", "predicted k3 m1"), ("Bx", "Bx-k0m0-best", "best k0 m0")]
sq = {r["seed"]: r for r in csv.DictReader(l for l in open(S + "/evidence/labelfree-squares.csv") if not l.startswith('"#'))}
t = subprocess.run(["date", "-u", "+%FT%TZ"], capture_output=True, text=True).stdout.strip()
out, hdr = [], None
for sheet, sq_id, what in RUNS:
    p = f"{S}/evidence/labelfree/{sq_id}/summary.csv"
    if not os.path.exists(p):
        out.append({"sheet": sheet, "run": sq_id, "orientation": what, "signal": "not run yet"}); continue
    for r in csv.DictReader(l for l in open(p) if not l.startswith('"#')):
        s = sq["PC0139-seed" + sheet]
        out.append(dict(sheet=sheet, run=sq_id, orientation=what, square_mm=s["square_mm"], labelled_cells_share=s["labelled_cells_share"], **r))
cols = ["tool", "time", "sheet", "run", "orientation", "square_mm", "labelled_cells_share"]
for r in out:
    for k in r:
        if k not in cols:
            cols.append(k)
verdicts = []
for sheet in ("A", "Bx"):
    rr = [r for r in out if r["sheet"] == sheet and r.get("direction") == "reverse"]
    done = len([r for r in out if r["sheet"] == sheet and r.get("signal") != "not run yet"])
    yes = [r for r in rr if str(r.get("signal", "")).startswith("yes")]
    nm = [r for r in rr if "not measurable" in str(r.get("signal", ""))]
    v = "signal yes on known ink" if yes else ("no on known ink (the 0826 statistic is blind)" if rr and not nm else
         ("not measurable on the reverse rows" if rr else "not run yet"))
    verdicts.append(dict(sheet=sheet, run="VERDICT", orientation="reverse rows of the runs done", signal=v,
                         source=f"{len(rr)} reverse rows, {len(yes)} yes, {len(nm)} not measurable; {done} rows in all"))
with open(S + "/evidence/labelfree-w016.csv", "w", newline="") as f:
    f.write(f'"# written by {TOOL} at {t}; run_one_v2 label free statistic (copy tools/run_one_v2_0139.sh) on the w016 sheets; the named direction is reverse for all four runs (orient-rule.csv, control.csv); squares 20 mm with about 1.8 per cent of cells on clean labels, the rest unlabelled papyrus of the same written segment"\n')
    w = csv.DictWriter(f, cols, extrasaction="ignore"); w.writeheader()
    for r in out + verdicts:
        w.writerow(dict(r, tool=TOOL, time=t))
for v in verdicts:
    print(v["sheet"], v["signal"], "|", v["source"])
