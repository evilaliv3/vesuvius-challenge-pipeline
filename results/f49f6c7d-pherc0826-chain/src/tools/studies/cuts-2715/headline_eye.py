#!/usr/bin/env python3
"""cuts-2715/tools/headline_eye.py: the agent's reading of the headline PNGs (judgement, not measurement) -> evidence/headline-eye.csv. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."""
import csv, subprocess
E = [
 ("headline-even0", "on papyrus", "surface on one of our sheets along a lamella, columns 530..747; no void"),
 ("headline-even1", "on papyrus", "on a lamella beside our sheet; the 5 void nodes (columns 660..664) are the surface grazing a thin gap"),
 ("headline-even2", "undecided", "on papyrus from column about 20 on; columns 0..3 sit at the tip of a fold in a large gap, the surface ends in air at the square's edge (4 nodes, 0.15 mm)"),
 ("headline-even3", "on papyrus", "on our sheet along a lamella bordering a long gap; 3 void nodes where it grazes the gap"),
 ("headline-even4", "on papyrus", "between two of our sheets on a lamella; no void of note"),
 ("headline-even5", "on papyrus", "runs along the lower edge of a lens shaped gap on a lamella; the scattered magenta inside the gap is our sheets' noise, not the surface"),
 ("headline-even6", "on papyrus", "on a lamella in dense papyrus, columns 0..275; no void"),
 ("headline-dark-row1", "on papyrus", "on our sheet across the whole cut; at columns 722..728 it crosses a small gap (7 nodes, 0.26 mm) between two lamellae and continues on our sheet"),
 ("headline-dark-row2", "undecided", "columns 0..18 (19 nodes, 0.71 mm) in air at the tip of the fold seen in even2; from column about 20 on the surface is on a lamella beside our sheet"),
 ("overall", "on papyrus", "no void run of 25 nodes or more on any of the 9 cuts; the only air is at the square's left edge (columns 0..18) where the surface leaves a fold tip, at most 0.71 mm; the dark corner problem of 2715 does not appear here"),
]
t = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
with open("/data/scrollagent/runs/rev1/cuts-2715/evidence/headline-eye.csv", "w", newline="") as f:
    f.write("# written by cuts-2715/tools/headline_eye.py at %s: eye reading of every headline PNG (judgement, not measurement)\n" % t)
    w = csv.writer(f, lineterminator="\n"); w.writerow(["cut", "eye", "note"]); w.writerows(E)
print(t)
