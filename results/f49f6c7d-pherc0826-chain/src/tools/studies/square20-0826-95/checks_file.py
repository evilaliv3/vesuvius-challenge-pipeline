#!/usr/bin/env python3
"""checks_file.py: writes evidence/checks-PHerc0826-seed2604.csv for the article (coordinator's request, 2026-09-28). New file,
2026-09-28T14:3xZ, coordinator agent. Reads evidence/check95-T72.csv and evidence/check95-box-T72.csv (seed2604 C80 sheet 0,
the 21.7474 mm square) and nothing else. Verdict about the cells inside the square, by the reading declared in DECLARATION.md
before the checks ran: «clean» when 0 flagged cells lie inside, «crossing found» otherwise, «not measurable» when the check
file is absent."""
import csv, os, subprocess
E = "/data/scrollagent/runs/rev1/square20-0826-95/evidence"
def rows(p):
    return list(csv.DictReader([l for l in open(p, newline="") if not l.lstrip('"').startswith("#")])) if os.path.exists(p) else []
k = {r["quantity"]: r for r in rows(E + "/check95-T72.csv")}
b = (rows(E + "/check95-box-T72.csv") or [{}])[0]
out = []
def v(q):
    return "not measurable" if q not in k else ("clean" if int(k[q]["inside_square"]) == 0 else "crossing found")
cov = k.get("covered_cells", {})
out.append(["v2_crossing", v("v2_cells"), "21.7474", cov.get("inside_square", ""), k.get("v2_cells", {}).get("inside_square", ""),
            k.get("v2_crossed_cells", {}).get("inside_square", ""), k.get("v2_jumped_cells", {}).get("inside_square", ""),
            cov.get("whole_sheet", ""), k.get("v2_cells", {}).get("whole_sheet", ""), "",
            k.get("largest_square_avoiding_v2", {}).get("inside_square", ""),
            "sheet_cross_v2 pair_v2 and marks as area-0826-90 ran them, partners the 800 sheets plus 9 siblings; flagged = crossed or jumped"])
out.append(["one_lamina", v("self_conflict_cells"), "21.7474", cov.get("inside_square", ""),
            k.get("self_conflict_cells", {}).get("inside_square", ""), "", "", cov.get("whole_sheet", ""),
            k.get("self_conflict_cells", {}).get("whole_sheet", ""),
            b.get("self_conflict_working_cells_in_square_with_itself", "not measurable"),
            k.get("largest_square_avoiding_self_conflict", {}).get("inside_square", ""),
            "area-0826-90 lamina.conflicts self conflict at one pitch 15.125 voxels; square_with_itself: working cells (stride 2) of the square in conflict with another cell of the square, of %s" % b.get("working_cells_in_square", "?")])
t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
with open(E + "/checks-PHerc0826-seed2604.csv", "w", newline="") as f:
    f.write("# written by square20-0826-95/tools/checks_file.py at %s from evidence/check95-T72.csv and check95-box-T72.csv: "
            "PHerc0826-seed2604 C80 (g 72000) sheet 0, verdict about the cells inside the 21.7474 mm square (581 cells at 600, 648)\n" % t)
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["check", "verdict", "square_mm", "cells_in_square", "flagged_cells_in_square", "crossed_cells_in_square",
                "jumped_cells_in_square", "cells_whole_sheet", "flagged_cells_whole_sheet", "square_with_itself_working_cells",
                "largest_square_avoiding_flagged_mm", "method"])
    w.writerows(out)
for r in out:
    print(r[:11])
