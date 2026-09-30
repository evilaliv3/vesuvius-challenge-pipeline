#!/usr/bin/env python3
"""cuts_summary.py: what the axial cuts of study cuts-2715 say, for the article (director 2026-09-30).

Reads this work's copies of cuts-2715/verdict.csv (the seed 2715 R2d square: four cuts at the crack, two at dark streaks,
three controls), headline-cuts.csv and headline-air.csv (the headline square), air-reference.csv (the same air proxy on
the 2715 square and its dark corner), and render-routes-0826's candidate-2715.csv (the house dark threshold). The two
declared bars that live in a column name (the void run of 25 nodes, the air proxy's grey of 57) are read from that name.
Writes src/evidence/derived/cuts-summary.csv (quantity, value, source, how). Standard library only.
"""
import csv, os, re, subprocess, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(SRC, "evidence", "studies", "cuts-2715")
OUT = os.path.join(SRC, "evidence", "derived", "cuts-summary.csv")
CAND = os.path.join(SRC, "inputs", "render-routes-0826", "candidate-2715.csv")


def rows(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip('"').startswith("#")))


def bar_in_name(head, pattern, what):
    hits = {int(m.group(1)) for h in head for m in [re.search(pattern, h)] if m}
    if len(hits) != 1:
        sys.exit("cuts_summary.py: %s: %d values in the column names" % (what, len(hits)))
    return hits.pop()


def main():
    out = []

    def put(q, v, src, how):
        out.append(dict(quantity=q, value=v, source=src, how=how))

    V = rows(os.path.join(EV, "verdict.csv"))
    cuts = [r for r in V if r["cut"] != "overall"]
    runs = lambda r: int(r["rule_c_void_runs_25plus_post_hoc"])
    air = [r for r in cuts if runs(r) > 0]
    crack = [r for r in cuts if r["cut"] == "crack"]
    put("rd_cuts", len(cuts), "cuts-2715/verdict.csv", "rows other than overall")
    put("rd_crack_cuts", len(crack), "cuts-2715/verdict.csv", "rows with cut crack")
    put("rd_air_cuts", len(air), "cuts-2715/verdict.csv", "rows with rule_c_void_runs_25plus_post_hoc above 0")
    put("rd_air_cuts_not_crack", sum(r["cut"] != "crack" for r in air), "cuts-2715/verdict.csv",
        "of those, rows whose cut is not crack")
    put("rd_controls", sum(r["cut"] == "control" for r in cuts), "cuts-2715/verdict.csv", "rows with cut control")
    put("rd_streaks", sum(r["cut"].startswith("streak") for r in cuts), "cuts-2715/verdict.csv", "rows with cut streak*")
    put("void_run_nodes", bar_in_name(V[0].keys(), r"void_runs_(\d+)plus", "void run bar"), "cuts-2715/verdict.csv",
        "the bar in the column name rule_c_void_runs_<n>plus_post_hoc")
    c = rows(CAND)[-1]
    put("dark_threshold", c["dark_threshold"], "../inputs/render-routes-0826/candidate-2715.csv", "column dark_threshold")
    H = rows(os.path.join(EV, "headline-cuts.csv"))
    put("head_cuts", len(H), "cuts-2715/headline-cuts.csv", "rows")
    put("head_void_runs_bar", sum(int(r["void_runs_25plus"]) for r in H), "cuts-2715/headline-cuts.csv",
        "sum of void_runs_25plus")
    L = max(H, key=lambda r: int(r["longest_void_run_nodes"]))
    put("head_longest_nodes", L["longest_void_run_nodes"], "cuts-2715/headline-cuts.csv", "max of longest_void_run_nodes")
    put("head_longest_mm", L["longest_void_run_mm"], "cuts-2715/headline-cuts.csv", "longest_void_run_mm of that row")
    put("head_longest_columns", L["longest_void_run_columns"], "cuts-2715/headline-cuts.csv",
        "longest_void_run_columns of that row")
    put("head_longest_at_edge", "yes" if L["longest_void_run_columns"].split("..")[0] == L["first_column"] == "0" else "no",
        "cuts-2715/headline-cuts.csv", "the run starts at column 0, the first column of the square")
    E = {r["cut"]: r for r in rows(os.path.join(EV, "headline-eye.csv"))}
    put("head_longest_eye", E[L["cut"]]["note"], "cuts-2715/headline-eye.csv", "note of the same cut (a reading by eye)")
    A = rows(os.path.join(EV, "headline-air.csv"))[-1]
    R = rows(os.path.join(EV, "air-reference.csv"))[-1]
    b1 = bar_in_name(A.keys(), r"cells_le_(\d+)$", "air proxy bar")
    b2 = bar_in_name(R.keys(), r"^cells_le_(\d+)$", "air proxy bar of the reference")
    if b1 != b2:
        sys.exit("cuts_summary.py: the air proxy bars differ, %d and %d" % (b1, b2))
    put("air_bar", b1, "cuts-2715/headline-air.csv", "the bar in the column name cells_le_<n>")
    put("air_head", A["share_le_57_of_measurable"], "cuts-2715/headline-air.csv", "share_le_57_of_measurable")
    put("air_head_square_mm", A["square_mm"], "cuts-2715/headline-air.csv", "square_mm")
    put("air_rd", R["share_le_57_of_measurable"], "cuts-2715/air-reference.csv", "share_le_57_of_measurable")
    put("air_rd_corner", R["share_le_57_dark_corner_rows850_cols930"], "cuts-2715/air-reference.csv",
        "share_le_57_dark_corner_rows850_cols930")
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(OUT, "w", newline="") as fh:
        fh.write('"# written by src/tools/cuts_summary.py at %s: the axial cuts of study cuts-2715, from this work\'s copies"\n' % now)
        w = csv.DictWriter(fh, fieldnames=["quantity", "value", "source", "how"], lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print("cuts_summary.py: %d rows" % len(out))


if __name__ == "__main__":
    main()
