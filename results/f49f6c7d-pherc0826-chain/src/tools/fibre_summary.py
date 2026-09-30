#!/usr/bin/env python3
"""The fibre numbers of PHerc. 0826, picked or recomputed from certified-piece-0826's files, one row each.

WHY IT EXISTS. The area figures of the article are pieces of delivered sheets; whether the raw scan on
a piece shows the fibres of papyrus is measured by certified-piece-0826 (fibre.py, fibre2.py) as a fibre
score per certified piece, with a bar declared before it was computed. paper_numbers.py picks ONE
cell per macro; the rule values live in the files' header lines and the per sheet scores must be
matched to the sheets the area study names. Each is written here as a row with its file, column and
the rows it covers. The largest passing piece and square are recomputed over every ranked row, and
checked against the file's own summary rows.

Usage: fibre_summary.py [--out PATH]
"""
import argparse, csv, os, re, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(S, "evidence", "studies", "certified-piece-0826")
AS = os.path.join(S, "evidence", "derived", "area-summary.csv")
OL = os.path.join(S, "evidence", "studies", "area-0826-90", "one-lamina.csv")


def rd(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))))


def header(p):
    return open(p).readline()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "fibre-summary.csv"))
    a = ap.parse_args()
    out = []

    def put(q, v, src, col, rows_covered="", check="", check_value=""):
        out.append({"quantity": q, "value": v, "source_file": src, "source_column": col,
                    "rows_covered": rows_covered, "check": check, "check_value": check_value})

    rk_p, sc_p = os.path.join(F, "fibre-ranking.csv"), os.path.join(F, "fibre-score.csv")
    rk_all = rd(rk_p)
    rk = [r for r in rk_all if not r["label"].startswith("LARGEST_")]
    summ = {r["label"]: r for r in rk_all if r["label"].startswith("LARGEST_")}
    h = header(rk_p)
    m = re.search(r"bar ([0-9.]+) = ([0-9.]+) x reference ([0-9.]+) \(([^)]+)\)", h)
    if not m:
        sys.exit("fibre_summary.py: fibre-ranking.csv header has no bar")
    put("fibre_bar", m.group(1), "certified-piece-0826/fibre-ranking.csv", "header line", "header",
        "bar equals factor x reference to 4 decimals", "yes" if abs(float(m.group(2)) * float(m.group(3)) - float(m.group(1))) < 6e-5 else "no")
    put("fibre_bar_factor", m.group(2), "certified-piece-0826/fibre-ranking.csv", "header line", "header")
    ref_sheet = "C40-PHerc0826-seed3648-S0"
    sc = {r["label"]: r for r in rd(sc_p)}
    put("fibre_reference_score", sc[ref_sheet]["fibre_score"], "certified-piece-0826/fibre-score.csv", "fibre_score",
        "label = %s" % ref_sheet, "equals the reference in the ranking header", "yes" if sc[ref_sheet]["fibre_score"] == m.group(3) else "no")
    put("fibre_reference_sheet", ref_sheet.split("-", 1)[1], "certified-piece-0826/fibre-score.csv", "label", "label = %s" % ref_sheet)
    whites = {r["white_noise_share"] for r in sc.values()}
    put("fibre_white_noise", whites.pop() if len(whites) == 1 else "not measurable", "certified-piece-0826/fibre-score.csv",
        "white_noise_share", "every row", "one value on every row", "yes" if len(whites) == 0 else "no")
    hs = header(sc_p)
    for q, pat in (("fibre_window_cells", r"accepted (\d+) x \d+ windows"), ("fibre_period_min_mm", r"periods ([0-9.]+) to"),
                   ("fibre_period_max_mm", r"periods [0-9.]+ to ([0-9.]+) mm")):
        mm = re.search(pat, hs)
        if not mm:
            sys.exit("fibre_summary.py: fibre-score.csv header has no %s" % q)
        put(q, mm.group(1), "certified-piece-0826/fibre-score.csv", "header line", "header")
    meas = [r for r in rk if re.fullmatch(r"[0-9.]+", r["fibre_score"])]
    nw = max(int(r["windows_accepted"]) for r in meas)
    put("fibre_windows", nw, "certified-piece-0826/fibre-ranking.csv", "windows_accepted, max", "every ranked row")
    put("fibre_pieces_fewer_windows", sum(int(r["windows_accepted"]) < nw for r in meas), "certified-piece-0826/fibre-ranking.csv",
        "rows with a score and fewer windows than the max", "every ranked row")
    put("fibre_pieces_not_measurable", len(rk) - len(meas), "certified-piece-0826/fibre-ranking.csv",
        "rows with no score (no window fits)", "every ranked row", "none of them passes",
        "yes" if all(r["passes_bar"] == "no" for r in rk if r not in meas) else "no")
    put("fibre_pieces_ranked", len(rk), "certified-piece-0826/fibre-ranking.csv", "rows", "every ranked row")
    ok = [r for r in rk if r["passes_bar"] == "yes"]
    put("fibre_pieces_passing", len(ok), "certified-piece-0826/fibre-ranking.csv", "passes_bar = yes", "every ranked row",
        "passes_bar equals fibre_score >= bar on every row",
        "yes" if all((r["passes_bar"] == "yes") == (re.fullmatch(r"[0-9.]+", r["fibre_score"]) is not None and
                     float(r["fibre_score"]) >= float(m.group(1))) for r in rk) else "no")
    mp = re.search(r"every certified piece of ([0-9.]+) cm2 or more", h)
    if not mp:
        sys.exit("fibre_summary.py: fibre-ranking.csv header has no population")
    put("fibre_population_min_cm2", mp.group(1), "certified-piece-0826/fibre-ranking.csv", "header line", "header",
        "every ranked row at or above it", "yes" if all(float(r["strict_piece_cm2"]) >= float(mp.group(1)) for r in rk) else "no")
    best = max(ok, key=lambda r: float(r["strict_piece_cm2"]))
    same = summ.get("LARGEST_PIECE_PASSING", {}).get("strict_piece_cm2") == best["strict_piece_cm2"]
    put("fibre_best_piece_cm2", best["strict_piece_cm2"], "certified-piece-0826/fibre-ranking.csv", "strict_piece_cm2, max over passing rows",
        "rows with passes_bar = yes (%d)" % len(ok), "equals the file's LARGEST_PIECE_PASSING row", "yes" if same else "no")
    put("fibre_best_piece_sheet", best["seed"] + "-S" + best["sheet"], "certified-piece-0826/fibre-ranking.csv", "seed, sheet of that row", "")
    put("fibre_best_piece_source", best["source"], "certified-piece-0826/fibre-ranking.csv", "source of that row", "")
    put("fibre_best_piece_score", best["fibre_score"], "certified-piece-0826/fibre-ranking.csv", "fibre_score of that row", "")
    # Director 2026-09-29T03:21:23Z: the largest passing piece is the reference sheet itself, so the text also
    # names the largest passing piece OTHER than the reference: every row of the reference seed is left out
    # (its C80 row is the same sheet regrown at g 72000, not another piece of papyrus).
    ref_seed = "PHerc0826-" + ref_sheet.split("-")[2]
    others = [r for r in ok if r["seed"] != ref_seed]
    bo = max(others, key=lambda r: float(r["strict_piece_cm2"]))
    put("fibre_best_other_piece_cm2", bo["strict_piece_cm2"], "certified-piece-0826/fibre-ranking.csv",
        "strict_piece_cm2, max over passing rows whose seed is not the reference's",
        "rows with passes_bar = yes and seed != %s (%d)" % (ref_seed, len(others)))
    put("fibre_best_other_piece_sheet", bo["seed"] + "-S" + bo["sheet"], "certified-piece-0826/fibre-ranking.csv", "seed, sheet of that row", "")
    put("fibre_best_other_piece_source", bo["source"], "certified-piece-0826/fibre-ranking.csv", "source of that row", "")
    put("fibre_best_other_piece_score", bo["fibre_score"], "certified-piece-0826/fibre-ranking.csv", "fibre_score of that row", "")
    # Director 2026-09-29T06:54:31Z (the reframe around the checks): the largest certified pieces that come BEFORE the
    # first passing piece in the ranking, the sheets that look best by size and fail the fibre test. Recomputed here in
    # descending strict_piece_cm2 over every ranked row, checked against the file's own order.
    desc = sorted(rk, key=lambda r: -float(r["strict_piece_cm2"]))
    top = []
    for r in desc:
        if r["passes_bar"] == "yes":
            break
        top.append(r)
    fails = [float(r["fibre_score"]) for r in top if re.fullmatch(r"[0-9.]+", r["fibre_score"])]
    src_top = "certified-piece-0826/fibre-ranking.csv"
    cov = "the ranked rows larger than the largest passing piece (%d)" % len(top)
    put("fibre_top_failing_count", len(top), src_top, "rows before the first passes_bar = yes, strict_piece_cm2 descending",
        "every ranked row", "the file lists the same rows first, in the same order",
        "yes" if [r["label"] for r in rk[:len(top)]] == [r["label"] for r in top] else "no")
    put("fibre_top_failing_scored", len(fails), src_top, "fibre_score measured on those rows", cov,
        "each measured on the full count of windows", "yes" if all(int(r["windows_accepted"]) == nw for r in top) else "no")
    put("fibre_top_failing_score_min", "%.4f" % min(fails), src_top, "fibre_score, min", cov)
    put("fibre_top_failing_score_max", "%.4f" % max(fails), src_top, "fibre_score, max", cov,
        "under the bar", "yes" if max(fails) < float(m.group(1)) else "no")
    put("fibre_top_failing_piece_min_cm2", min(top, key=lambda r: float(r["strict_piece_cm2"]))["strict_piece_cm2"], src_top,
        "strict_piece_cm2, min", cov)
    put("fibre_top_failing_piece_max_cm2", top[0]["strict_piece_cm2"], src_top, "strict_piece_cm2, max", cov)
    put("fibre_top_failing_sheets", ", ".join(r["seed"].replace("PHerc0826-seed", "") for r in top), src_top,
        "seed numbers of those rows, in order", cov)
    put("fibre_top_failing_square_max_mm", max(top, key=lambda r: float(r["certified_square_mm"]))["certified_square_mm"], src_top,
        "certified_square_mm, max", cov)
    bsq = max(ok, key=lambda r: float(r["certified_square_mm"]))
    same = summ.get("LARGEST_SQUARE_PASSING", {}).get("certified_square_mm") == bsq["certified_square_mm"]
    put("fibre_best_square_mm", bsq["certified_square_mm"], "certified-piece-0826/fibre-ranking.csv", "certified_square_mm, max over passing rows",
        "rows with passes_bar = yes (%d)" % len(ok), "equals the file's LARGEST_SQUARE_PASSING row", "yes" if same else "no")
    put("fibre_best_square_sheet", bsq["seed"] + "-S" + bsq["sheet"], "certified-piece-0826/fibre-ranking.csv", "seed, sheet of that row", "")
    put("fibre_best_square_score", bsq["fibre_score"], "certified-piece-0826/fibre-ranking.csv", "fibre_score of that row", "")
    # The sheets the area figures name: their C40 row of the ranking (the area study grew C40 sheets).
    area = {r["quantity"]: r["value"] for r in rd(AS)}
    by = {r["label"]: r for r in rk}
    for q, key in (("fibre_union_piece_score", "union_largest_piece_sheet"), ("fibre_lamina_piece_score", "lamina_piece_sheet")):
        L = "C40-" + area[key]
        r = by.get(L)
        put(q, r["fibre_score"] if r else "not measured", "certified-piece-0826/fibre-ranking.csv", "fibre_score",
            "label = %s (area-summary.csv %s)" % (L, key), "the sheet's certified piece, not the area study's clean piece", "")
        put(q.replace("_score", "_certified_cm2"), r["strict_piece_cm2"] if r else "not measured",
            "certified-piece-0826/fibre-ranking.csv", "strict_piece_cm2", "label = %s" % L)
    groups = [r for r in rd(OL) if r["kind"] == "group"]
    g = max(groups, key=lambda r: float(r["clean_unique_cm2"]))
    mem = ["C40-" + x for x in g["members"].split()]
    scored = [by[x] for x in mem if x in by]
    put("fibre_group_members_scored", len(scored), "certified-piece-0826/fibre-ranking.csv", "rows whose label is a member",
        "members of the largest group of area-0826-90/one-lamina.csv (%d)" % len(mem))
    big = max(scored, key=lambda r: float(r["strict_piece_cm2"])) if scored else None
    put("fibre_group_member_sheet", big["seed"] + "-S" + big["sheet"] if big else "none", "certified-piece-0826/fibre-ranking.csv",
        "seed, sheet of the scored member with the largest certified piece", "the scored members")
    put("fibre_group_member_score", big["fibre_score"] if big else "not measured", "certified-piece-0826/fibre-ranking.csv",
        "fibre_score of that row", "the scored members")
    # Director 2026-09-29T04:22:11Z: the pooled four seed run of area-0826-90 (collection-four-6365.csv). Its seeds are
    # read from the declaration shipped as src/prereg/area-0826-90.md, «(1) One collection, declared»; a piece of any of
    # them in the ranking (every certified piece of the population minimum or more, any source) would be scored there.
    pr = open(os.path.join(S, "prereg", "area-0826-90.md")).read()
    mc = re.search(r"\*\*Seeds\*\*: (seed\d+) \(the largest run.*?\): (seed\d+), (seed\d+), (seed\d+) \(", pr, re.S)
    if not mc:
        sys.exit("fibre_summary.py: prereg/area-0826-90.md names no four seed collection")
    four = ["PHerc0826-" + x for x in mc.groups()]
    put("fibre_coll_four_seeds", len(four), "prereg/area-0826-90.md", "(1) One collection, declared: Seeds", " ".join(four))
    hit = [r for r in rk if r["seed"] in four]
    put("fibre_coll_four_seeds_ranked", len({r["seed"] for r in hit}), "certified-piece-0826/fibre-ranking.csv",
        "rows whose seed is one of the four", "every ranked row (%d)" % len(rk))
    put("fibre_coll_four_pieces_ranked", len(hit), "certified-piece-0826/fibre-ranking.csv", "rows whose seed is one of the four",
        "every ranked row (%d)" % len(rk))
    hs4 = [x for x in sc if any(x.split("-", 1)[1].startswith(f + "-") for f in four)]
    put("fibre_coll_four_scores", len(hs4), "certified-piece-0826/fibre-score.csv", "rows whose label names one of the four", "every row")
    put("fibre_coll_four_legend", "four seeds as one run (%s)" % ("not scored by the fibre test" if not hit and not hs4 else
        "fibre score %s to %s" % (min(r["fibre_score"] for r in hit), max(r["fibre_score"] for r in hit))),
        "this tool", "legend of the four seed line of the Stevens formula figure", "")
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/fibre_summary.py from the copies of certified-piece-0826 in src/evidence/studies and '
                 'derived/area-summary.csv; rows_covered says which rows a value is over"\n')
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    bad = [r for r in out if r["check"] and r["check_value"] not in ("", "yes")]
    for r in bad:
        print("fibre_summary.py: check failed: %s %s" % (r["quantity"], r["check_value"]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
