#!/usr/bin/env python3
"""stevens_method.py: evidence/stevens-method.csv (how Stevens' 365 cm2 was measured, one property per row with its source)
and evidence/stevens-method-0826.csv (our PHerc0826 components measured the same way: cells x step_i_mm x step_j_mm per
component, summed per growth run and over runs, every overlap counted). Known reference first: the same function on his ten
PHerc1667 components must give 363.8629 cm2 (field-0826-0800/evidence/field-sums.csv)."""
import glob, html, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import area90 as A
A.TOOL = "area-0826-90/tools/stevens_method.py"  # the CSV header names this tool

R1 = A.R1
F = R1 + "/field-0826-0800/evidence"


def comp_area(row):
    return int(row["points"]) * float(row["step_i_mm"]) * float(row["step_j_mm"]) / 100.0


def page_text(p):
    t = open(p, encoding="utf-8").read()
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def main():
    # known reference: his ten components
    his = []
    for p in sorted(glob.glob(F + "/squares-delivered-PHerc1667-patch_*.csv")):
        for r in A.read_rows(p):
            his.append((r["point"], comp_area(r), r))
    his_sum = sum(a for _, a, _ in his)
    ref = [r for r in A.read_rows(F + "/field-sums.csv") if r["scroll"] == "PHerc1667"][0]["delivered_area_cm2_sum"]
    if "%.4f" % his_sum != ref:
        raise SystemExit("REFUSED: %.4f against field-sums.csv %s" % (his_sum, ref))
    big = max(his, key=lambda x: x[1])
    ext_i = int(big[2]["cells_i"]) * float(big[2]["step_i_mm"]); ext_j = int(big[2]["cells_j"]) * float(big[2]["step_j_mm"])
    radii = [float(r["inscribed_radius_mm"]) for r in A.read_rows(F + "/umbilicus-PHerc1667.csv")
             if r["inscribed_radius_mm"] != A.NM]
    circ = 2 * math.pi * max(radii)
    win = sorted(glob.glob(A.EV + "/winners-*.html"))[-1]
    t = page_text(win)
    i = t.find("Patch-based unwrapping")
    quote = t[i:t.find("PHerc. 1667", i) + len("PHerc. 1667")]
    r12 = R1 + "/stevens-reports/evidence/report12-pages.txt"
    L12 = open(r12).read().split("\n")
    rows = [
        ["what is counted", "coverage in cm2 of flattened components", quote, os.path.relpath(win, R1), "winners text"],
        ["how components are made", "patches whose 2D alignments imply incompatible 3D places are dropped, the rest joined "
         "into flattened components (one 2D surface each)", quote, os.path.relpath(win, R1), "winners text"],
        ["component of one run", "one large component, a few medium, many small; the large one is used",
         " ".join(x.strip() for x in L12[175:181]), os.path.relpath(r12, R1), "lines 176 to 181"],
        ["one winding or several", "several: his method unwraps across windings (0139: a 3-winding unwrapping)",
         " ".join(x.strip() for x in L12[16:19]), os.path.relpath(r12, R1), "lines 17 to 19"],
        ["one winding or several, PHerc1667 indication", "largest component flattened extent %.1f x %.1f mm against the "
         "largest inscribed circle circumference %.1f mm of PHerc1667 (max inscribed radius %.4f mm): the extent exceeds one "
         "turn of that circle; an indication only, the section is not a circle" % (ext_i, ext_j, circ, max(radii)),
         "cells_i, cells_j, step_i_mm, step_j_mm of %s; inscribed_radius_mm" % big[0],
         "field-0826-0800/evidence/squares-delivered-PHerc1667-patch_*.csv; umbilicus-PHerc1667.csv", "computed here"],
        ["area tool in his code", "none: no area measurement in the scrollreading clone (af00234); the only reproduction is "
         "ours", "grep -i cm2|mm2|area over *.py *.sh *.c *.cpp: cost functions and cover weights only",
         "/data/repositories/scrollreading", "grep"],
        ["our reproduction of 365", "sum over his ten components of cells x step_i_mm x step_j_mm = %.4f cm2" % his_sum,
         "delivered_area_cm2=\"%.6f\" % (n * si * sj / 100.0)", "field-0826-0800/tools/field_table_v2.py", "line 103"],
        ["union or sum", "sum over components, every overlap between components counted (a bound, not a deduplicated "
         "coverage)", ref, "field-0826-0800/evidence/field-sums.csv", "row PHerc1667, column how"],
        ["deduplicated", "within a component yes by construction (one 2D grid point per place of the flattened surface); "
         "between components no", "", "field-sums.csv; report12 lines 170 to 181", "reading"],
        ["cleaned", "no crossing or steep-angle cells removed; his bad patch removal acts before the join", quote,
         os.path.relpath(win, R1), "winners text"],
        ["input", "bruniss' s4_059_medial prediction (report10 page 2), not the organisers' m7", "",
         "stevens-reports/evidence/stevens-runs.csv", "director.md row item 69"],
    ]
    A.write_csv(A.EV + "/stevens-method.csv", "how Stevens' «around 365 cm2» on PHerc1667 is measured, one property per "
                "row with its source; known reference passed: his ten components give %.4f cm2 = field-sums.csv" % his_sum,
                ["property", "value", "quote_or_value", "source", "where"], rows)
    # ours, the same formula
    out, tot, best = [], 0.0, None
    for seed, n, _ in A.seeds_frozen():
        rs = A.read_rows("%s/evidence/squares-%s.csv" % (A.CHAIN, seed))
        rs = [r for r in rs if int(r["sheet"]) < n]
        if len(rs) != n:
            raise SystemExit("REFUSED: %s has %d squares rows for %d sheets" % (seed, len(rs), n))
        s = sum(comp_area(r) for r in rs)
        tot += s
        big_c = max(comp_area(r) for r in rs)
        out.append([seed, n, "%.4f" % s, "%.4f" % big_c])
        if best is None or s > best[1]:
            best = (seed, s)
    out.append(["sum over %d growth runs" % len(out), sum(r[1] for r in out), "%.4f" % tot, ""])
    out.append(["largest single growth run", best[0], "%.4f" % best[1], ""])
    out.append(["Stevens PHerc1667, one run, ten components (reference)", len(his), "%.4f" % his_sum, "%.4f" % big[1]])
    A.write_csv(A.EV + "/stevens-method-0826.csv", "PHerc0826 components (delivered sheets C40/patch_<k>.bin of each seed) "
                "measured as Stevens' 365 is: cells x step_i_mm x step_j_mm per component from chain-0826/evidence/"
                "squares-<seed>.csv (square.py), summed per growth run and over runs, every overlap counted, not cleaned, not "
                "deduplicated; his ten components with the same function beside", ["run", "components",
                                                                                   "sum_components_cm2",
                                                                                   "largest_component_cm2"], out)
    print("his %.4f; ours: sum %.4f over %d runs, largest run %s %.4f" % (his_sum, tot, len(out) - 3, best[0], best[1]))


if __name__ == "__main__":
    main()
