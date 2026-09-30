#!/usr/bin/env python3
"""render-routes-0826/tools/three_defs.py: evidence/square-three-definitions.csv (DECLARATION addition 00:21Z): per R2 row the
square under (a) this study's rule (square-checks.csv, v2 against our 800 only), (b) the article as written
(square-checks-article.csv, also against other traced surfaces), (c) adjudicated (square-checks-adjudicated.csv), the crossing
partners with each verdict from crossing-pairs.csv (both sides), and exceeds_29_8961 under each; every value read from those CSVs."""
import csv, subprocess, sys
H = "/data/scrollagent/runs/rev1/render-routes-0826"


def rows(p):
    return list(csv.DictReader(l for l in open(p) if not l.lstrip('"').startswith("#")))


def last(p, key):
    d = {}
    for r in rows(p):
        d[(r["route"], r["surface"])] = r
    return d


A = last(H + "/evidence/square-checks.csv", None)
B = last(H + "/evidence/square-checks-article.csv", None)
C = last(H + "/evidence/square-checks-adjudicated.csv", None)
Pp = rows(H + "/evidence/crossing-pairs.csv")
out = []
for k, a in A.items():
    if not k[0].startswith("R2"):
        continue
    me = "%s %s" % k
    parts = []
    for r in Pp:
        if me not in (r["surface_1"], r["surface_2"]):
            continue
        other = r["surface_2"] if r["surface_1"] == me else r["surface_1"]
        tie = r["share_800_within_3vox_1"] == "0.0000" and r["share_800_within_3vox_2"] == "0.0000"
        v = "tie (no 800 sheet in the region)" if tie else ("tie" if r["flagged"] == "both" else ("kept" if r["kept"] == me else "flagged"))
        parts.append("%s: %s" % (other, v))
    va = a["square_mm"]
    vb = B[k]["certified_article_mm"] if k in B else "not measurable: no row"
    vc = C[k]["certified_adjudicated_mm"] if k in C else "not measurable: no row"

    def ex(v):
        try:
            return "yes" if float(v) > 29.8961 else "no"
        except ValueError:
            return "not measurable"
    out.append([k[0], k[1], va, vb, vc, ex(va), ex(vb), ex(vc), len(parts),
                sum(1 for s in parts if s.endswith(": flagged")), sum(1 for s in parts if ": tie" in s), "; ".join(parts) or "none"])
t = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
with open(H + "/evidence/square-three-definitions.csv", "w", newline="") as f:
    f.write("# written by render-routes-0826/tools/three_defs.py at %s: per R2 row the largest square under three definitions, read from "
            "square-checks.csv (a), square-checks-article.csv (b), square-checks-adjudicated.csv (c) and crossing-pairs.csv (partners and "
            "verdicts from this row's side; tie = both flagged by the rule)\n" % t)
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["route", "surface", "a_certified_this_study_mm", "b_certified_article_mm", "c_certified_adjudicated_mm",
                "a_exceeds_29_8961", "b_exceeds_29_8961", "c_exceeds_29_8961", "crossing_pairs", "pairs_flagged", "pairs_tied",
                "partners_and_verdicts"])
    w.writerows(out)
print(open(H + "/evidence/square-three-definitions.csv").read())
