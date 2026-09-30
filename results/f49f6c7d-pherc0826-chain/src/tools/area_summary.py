#!/usr/bin/env python3
"""The area numbers of PHerc. 0826, picked or recomputed from area-0826-90's files, one row each.

WHY IT EXISTS. paper_numbers.py picks ONE cell per macro. Several numbers of this work are not one
cell of a study file: the largest one lamina group is the largest of five group rows (the file's
rank column orders by joining, not by area), the count of seeds is the count of rows of the traced
reference, and a few rule values live only in a file's header line. Each of those is computed here,
over every row the word covers, and written as a row with the file, the column and the rows it
covers. A superlative is recomputed over all the rows it names, never taken from the row at hand.

THE CHECKS ARE COLUMNS: e.g. the tool's own «largest single growth run» row against the maximum over
every run row, and the union's sheet count against ten sheets per counted seed.

Usage: area_summary.py [--out PATH]
"""
import argparse, csv, os, re, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(S, "evidence", "studies", "area-0826-90")


def rd(name):
    p = os.path.join(A, name)
    with open(p, newline="") as fh:
        lines = [l for l in fh if not l.lstrip().startswith(('"#', "#"))]
    return list(csv.DictReader(lines))


def header(name):
    return open(os.path.join(A, name)).readline()


def one(rows, what, **kw):
    hit = [r for r in rows if all(r.get(k) == v for k, v in kw.items())]
    if len(hit) != 1:
        sys.exit("area_summary.py: %s: %d rows for %s" % (what, len(hit), kw))
    return hit[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "area-summary.csv"))
    a = ap.parse_args()
    out = []

    def put(q, v, src, col, rows_covered="", check="", check_value=""):
        out.append({"quantity": q, "value": v, "source_file": src, "source_column": col,
                    "rows_covered": rows_covered, "check": check, "check_value": check_value})

    # The seeds the area numbers are over: the traced reference, one row per seed plus a sum row.
    tr = rd("traced-reference.csv")
    seeds = [r for r in tr if r["seed"].startswith("PHerc0826-seed")]
    put("area_seeds", len(seeds), "area-0826-90/traced-reference.csv", "rows whose seed is a seed",
        "every seed row", "traced area equal in the three sources on every row",
        "%d of %d" % (sum(r["equal"] == "yes" for r in seeds), len(seeds)))

    # The union, three deduplication rules; the smallest (one-step) is the headline.
    un = rd("union.csv")
    for rule in ("one-step", "half-step", "bin-max"):
        put("union_%s_cm2" % rule.replace("-", "_"), one(un, "union", rule=rule)["unique_clean_cm2"],
            "area-0826-90/union.csv", "unique_clean_cm2", "rule = %s" % rule)
    vals = {r["rule"]: float(r["unique_clean_cm2"]) for r in un}
    head = [r["rule"] for r in un if r["headline"] == "yes"]
    put("union_headline_rule", head[0] if len(head) == 1 else "not measurable", "area-0826-90/union.csv",
        "headline", "every rule row", "the headline is the smallest of the rules",
        "yes" if len(head) == 1 and vals[head[0]] == min(vals.values()) else "no")
    r1 = one(un, "union", rule="one-step")
    put("union_sheets", r1["sheets"], "area-0826-90/union.csv", "sheets", "rule = one-step",
        "sheets equal ten per seed of the traced reference",
        "yes" if int(r1["sheets"]) == 10 * len(seeds) else "no, %s against %d" % (r1["sheets"], 10 * len(seeds)))
    put("union_clean_summed_cm2", r1["clean_summed_cm2"], "area-0826-90/union.csv", "clean_summed_cm2", "rule = one-step")
    put("union_all_cells_summed_cm2", r1["all_cells_summed_cm2"], "area-0826-90/union.csv", "all_cells_summed_cm2", "rule = one-step")
    put("union_largest_piece_cm2", r1["largest_piece_cm2"], "area-0826-90/union.csv", "largest_piece_cm2", "rule = one-step")
    put("union_largest_piece_sheet", r1["largest_piece_sheet"], "area-0826-90/union.csv", "largest_piece_sheet", "rule = one-step")
    put("stevens_quoted_cm2", r1["stevens_cm2"], "area-0826-90/union.csv", "stevens_cm2", "rule = one-step")

    # One lamina: the largest group by clean_unique_cm2, over every group row; the piece.
    ol = rd("one-lamina.csv")
    groups = [r for r in ol if r["kind"] == "group"]
    g = max(groups, key=lambda r: float(r["clean_unique_cm2"]))
    cover = "every group row (%d)" % len(groups)
    put("lamina_group_cm2", g["clean_unique_cm2"], "area-0826-90/one-lamina.csv", "clean_unique_cm2, max over group rows", cover)
    put("lamina_group_rank_by_joining", g["rank"], "area-0826-90/one-lamina.csv", "rank of that row", cover)
    put("lamina_group_sheets", g["sheets"], "area-0826-90/one-lamina.csv", "sheets of that row", cover)
    put("lamina_group_seeds", g["seeds"], "area-0826-90/one-lamina.csv", "seeds of that row", cover)
    put("lamina_group_square_mm", g["square_mm"], "area-0826-90/one-lamina.csv", "square_mm of that row", cover)
    put("lamina_group_conflicts_inside", g["conflicts_inside"], "area-0826-90/one-lamina.csv", "conflicts_inside of that row", cover,
        "conflicts_inside is 0 on every group row", "yes" if all(r["conflicts_inside"] == "0" for r in groups) else "no")
    put("lamina_groups_listed", len(groups), "area-0826-90/one-lamina.csv", "group rows", cover)
    pieces = [r for r in ol if r["kind"] == "piece"]
    p = max(pieces, key=lambda r: float(r["clean_unique_cm2"]))
    put("lamina_piece_cm2", p["clean_unique_cm2"], "area-0826-90/one-lamina.csv", "clean_unique_cm2, max over piece rows", "every piece row (%d)" % len(pieces))
    put("lamina_piece_sheet", p["square_or_piece_sheet"], "area-0826-90/one-lamina.csv", "square_or_piece_sheet of that row", "every piece row (%d)" % len(pieces))
    h = header("one-lamina.csv")
    for q, pat in (("lamina_pitch_vox", r"pitch ([0-9.]+) voxels"), ("lamina_refusals", r"\((\d+) refusals\)"),
                   ("lamina_wrapping_sheets", r"wrapping sheets \((\d+)\)"),
                   ("lamina_conflict_area_sq_vox", r"over (\d+) square voxels"),
                   ("lamina_conflict_pitches", r"within ([0-9.]+) pitch")):
        m = re.search(pat, h)
        if not m:
            sys.exit("area_summary.py: one-lamina.csv header has no %s" % q)
        put(q, m.group(1), "area-0826-90/one-lamina.csv", "header line", "header")

    # Stevens' formula: his reference and our runs.
    sm = rd("stevens-method-0826.csv")
    runs = [r for r in sm if r["run"].startswith("PHerc0826-seed")]
    ref = [r for r in sm if r["run"].startswith("Stevens PHerc1667")]
    if len(ref) != 1:
        sys.exit("area_summary.py: stevens-method-0826.csv has %d reference rows" % len(ref))
    put("stevens_reproduced_cm2", ref[0]["sum_components_cm2"], "area-0826-90/stevens-method-0826.csv", "sum_components_cm2", "row Stevens PHerc1667, one run, ten components (reference)")
    put("stevens_components", ref[0]["components"], "area-0826-90/stevens-method-0826.csv", "components", "row Stevens PHerc1667")
    best = max(runs, key=lambda r: float(r["sum_components_cm2"]))
    row_best = one(sm, "stevens", run="largest single growth run")
    put("stevens_formula_best_run_cm2", best["sum_components_cm2"], "area-0826-90/stevens-method-0826.csv",
        "sum_components_cm2, max over run rows", "every run row (%d)" % len(runs),
        "equals the tool's own «largest single growth run» row",
        "yes" if best["sum_components_cm2"] == row_best["sum_components_cm2"] and best["run"] == row_best["components"] else "no")
    put("stevens_formula_best_run", best["run"], "area-0826-90/stevens-method-0826.csv", "run of that row", "every run row (%d)" % len(runs))
    put("stevens_formula_runs", len(runs), "area-0826-90/stevens-method-0826.csv", "run rows", "every run row",
        "run rows equal the traced reference seeds", "yes" if len(runs) == len(seeds) else "no")
    put("stevens_formula_sum_runs_cm2", one(sm, "stevens", run="sum over %d growth runs" % len(runs))["sum_components_cm2"],
        "area-0826-90/stevens-method-0826.csv", "sum_components_cm2", "row sum over the runs")

    # One run measured as his: collections put through simpaper10 u and the chain's downstream.
    for tag, name in (("four", "collection-four-6365.csv"), ("control", "collection-control-6365.csv"),
                      ("setseed6365", "collection-setseed-seed6365.csv"),
                      ("setseed2019", "collection-setseed-seed2019.csv"),
                      ("setseed5630", "collection-setseed-seed5630.csv")):
        rows = rd(name)
        allr = one(rows, name, sheet="all 10 sheets")
        sheets = [r for r in rows if r["sheet"] != "all 10 sheets"]
        tot = sum(float(r["stevens_formula_cm2"]) for r in sheets)
        put("coll_%s_formula_cm2" % tag, allr["stevens_formula_cm2"], "area-0826-90/" + name, "stevens_formula_cm2", "row all 10 sheets",
            "sum of the sheet rows, to 4 decimals", "yes" if abs(tot - float(allr["stevens_formula_cm2"])) < 6e-4 else "no, %.4f" % tot)
        put("coll_%s_a2_share" % tag, allr["a2_share"], "area-0826-90/" + name, "a2_share", "row all 10 sheets")
        put("coll_%s_v2_cells" % tag, allr["v2_cells"], "area-0826-90/" + name, "v2_cells", "row all 10 sheets")
        put("coll_%s_clean_cm2" % tag, allr["clean_cm2"], "area-0826-90/" + name, "clean_cm2", "row all 10 sheets")
        put("coll_%s_square_mm" % tag, allr["square_mm_delivered"], "area-0826-90/" + name, "square_mm_delivered", "row all 10 sheets")
        m = re.search(r"union of clean cells ([0-9.]+) cm2", allr["square_mm_clean"])
        put("coll_%s_union_cm2" % tag, m.group(1) if m else "not measurable", "area-0826-90/" + name,
            "square_mm_clean of the all row, the text «union of clean cells X cm2»", "row all 10 sheets")
        put("coll_%s_sheets" % tag, len(sheets), "area-0826-90/" + name, "sheet rows", "every sheet row")

    r1b = rd("road1b-seeds.csv")
    m = re.search(r"the (\d+) nearest (seed\d+); (\d+) qualified", header("road1b-seeds.csv"))
    put("road1b_seeds", len(r1b), "area-0826-90/road1b-seeds.csv", "rows", "every row",
        "rows equal the header's count", "yes" if m and int(m.group(1)) == len(r1b) else "no")
    put("road1b_qualified", m.group(3) if m else "not measurable", "area-0826-90/road1b-seeds.csv", "header: N qualified", "header")
    put("road1b_min_square_mm", "%.4f" % min(float(r["largest_square_mm"]) for r in r1b), "area-0826-90/road1b-seeds.csv", "largest_square_mm, min over rows", "every row")
    # The seeds road 1b actually pools: ranks 1 to ROAD1B_USED of road1b-seeds.csv. The cut is a
    # decision, not a measurement: the director reduced the list from the file's 12 to 8 before
    # launch (2026-09-28T06:01:51Z, for time and memory; area-0826-90/DECLARATION.md, addition of
    # that morning, names the same eight and their 52,906 patches). It is written here once, as a
    # declared constant, and every number of the eight is computed from the file's rows.
    ROAD1B_USED = 8
    used = [r for r in r1b if int(r["rank"]) <= ROAD1B_USED]
    cover = "rows with rank 1 to %d" % ROAD1B_USED
    put("road1b_seeds_used", len(used), "area-0826-90/road1b-seeds.csv", "rows with rank at most the director's cut", cover,
        "rows found equal the cut", "yes" if len(used) == ROAD1B_USED else "no")
    put("road1b_patches_used", sum(int(r["patches"]) for r in used), "area-0826-90/road1b-seeds.csv", "patches, sum", cover)
    put("road1b_used_min_square_mm", "%.4f" % min(float(r["largest_square_mm"]) for r in used), "area-0826-90/road1b-seeds.csv", "largest_square_mm, min", cover)
    put("road1b_used_max_distance_vox", "%.1f" % max(float(r["distance_vox"]) for r in used), "area-0826-90/road1b-seeds.csv", "distance_vox, max", cover)
    put("road1b_max_distance_vox", "%.1f" % max(float(r["distance_vox"]) for r in r1b), "area-0826-90/road1b-seeds.csv", "distance_vox, max over rows", "every row")

    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/area_summary.py at %s from the copies of area-0826-90 in '
                 'src/evidence/studies (copy time in src/evidence/MANIFEST.csv); rows_covered says which rows '
                 'a value is over"\n' % now)
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    bad = [r for r in out if r["check_value"] and not (r["check_value"] == "yes" or re.fullmatch(r"(\d+) of \1", r["check_value"]))]
    for r in bad:
        print("  !! %s %s: %s" % (r["quantity"], r["check"], r["check_value"]))
    print("area_summary.py: %d rows to %s, %d check(s) not holding" % (len(out), a.out, len(bad)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
