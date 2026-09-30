#!/usr/bin/env python3
"""The numbers of the section «The checks as a tool», picked or recomputed from best-windows-0826's files, one row each.

WHY IT EXISTS. The reframe of 2026-09-29 (director 06:54:31Z, owner's word) puts the automatic checks at the centre
of the article: which delivered sheet holds a clean 20 x 20 mm window, found without a person. best-windows-0826 wrote
the search (windows.csv, attempts.csv), the axis aligned resampling of its own tools/align.py (aligned.csv, angles.csv)
and the straightened sections of the best three windows (straight.csv). paper_numbers.py picks ONE cell per macro, so the
counts over rows, the rule values of the header lines and the reading of the straightened sections are written here,
each with its file, its column and the rows it covers.

THE READING OF THE STRAIGHTENED SECTIONS IS THIS ARTICLE'S, NOT THE STUDY'S. best-windows-0826 declared the statistic
(peak_offset_median_vox: the median over the line's columns of the offset of the brightest voxel within +-W of the
traced sheet, and share_within_3_vox) and said that it is «a number to check against the picture, not a proof»; it
declared no bar. The reference used here is arithmetic, not a measured null: a peak placed uniformly at random on the
2W + 1 integer offsets of the window would give the median |t| and the share within 3 voxels computed below. A section
«separates from random placement» when, on BOTH of its lines, its median is below that median and its share is above
that share. The rule is written here before the figure uses it and is the only one the text applies; it is not a
certificate of one layer, and the text says so.

Usage: checks_summary.py [--out PATH]
"""
import argparse, csv, os, re, statistics, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BW = os.path.join(S, "evidence", "studies", "best-windows-0826")
FS = os.path.join(S, "evidence", "derived", "fibre-summary.csv")
REL = "best-windows-0826/"


def rd(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))))


def header(p):
    return open(p).readline()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "checks-summary.csv"))
    a = ap.parse_args()
    out = []

    def put(q, v, src, col, rows_covered="", check="", check_value=""):
        out.append({"quantity": q, "value": v, "source_file": src, "source_column": col,
                    "rows_covered": rows_covered, "check": check, "check_value": check_value})

    wp = os.path.join(BW, "windows.csv")
    W = rd(wp)
    h = header(wp)
    rules = {}
    for q, pat in (("windows_side_mm", r"window = ceil\((\d+) / step\)"),
                   ("windows_covered_bar", r"covered_share >= ([0-9.]+)"),
                   ("windows_flagged_bar", r"flagged_share <= ([0-9.]+)"),
                   ("windows_fibre_bar", r"passes at >= ([0-9.]+)"),
                   ("windows_tile_cells", r"accepted (\d+) x \d+ tiles")):
        m = re.search(pat, h)
        if not m:
            sys.exit("checks_summary.py: windows.csv header has no %s" % q)
        rules[q] = m.group(1)
    fs = {r["quantity"]: r["value"] for r in rd(FS)}
    for q, v in rules.items():
        chk = ("equals the fibre bar of the certified pieces (fibre-summary.csv fibre_bar)", "yes" if v == fs["fibre_bar"] else "no") \
            if q == "windows_fibre_bar" else ("", "")
        put(q, v, REL + "windows.csv", "header line", "header", *chk)
    side = int(rules["windows_side_mm"])
    put("windows_area_cm2", "%g" % (side * side / 100.0), REL + "windows.csv", "header line: side squared, mm2 to cm2", "header")
    # Every window is at least the declared side on both axes (the study's ceil rule).
    put("windows_mm_min", "%.4f" % min(min(float(r["window_mm_i"]), float(r["window_mm_j"])) for r in W),
        REL + "windows.csv", "window_mm_i, window_mm_j, min", "every row (%d)" % len(W),
        "every window at least the declared side", "yes" if all(float(r["window_mm_i"]) >= side and float(r["window_mm_j"]) >= side for r in W) else "no")
    put("windows_sheets_searched", len(W), REL + "windows.csv", "rows", "every row",
        "equals the certified pieces that pass the fibre bar (fibre-summary.csv fibre_pieces_passing)",
        "yes" if str(len(W)) == fs["fibre_pieces_passing"] else "no")
    put("windows_seeds_searched", len({r["seed"] for r in W}), REL + "windows.csv", "distinct seed", "every row")
    cand = [r for r in W if r["status"] != "no candidate"]
    put("windows_with_candidate", len(cand), REL + "windows.csv", "status != no candidate", "every row")
    put("windows_no_candidate", len(W) - len(cand), REL + "windows.csv", "status = no candidate", "every row")
    clean = [r for r in W if r["status"] == "clean window"]
    ok_rule = all(float(r["covered_share"]) >= float(rules["windows_covered_bar"]) and
                  float(r["flagged_share"]) <= float(rules["windows_flagged_bar"]) and
                  float(r["window_fibre"]) >= float(rules["windows_fibre_bar"]) and r["sat_equals_direct"] == "yes" for r in clean)
    put("windows_clean", len(clean), REL + "windows.csv", "status = clean window", "every row",
        "every clean row meets the three bars of the header and its summed area check", "yes" if ok_rule else "no")
    # Director 2026-09-29T16:23:24Z: C40 and C80 are two runs of the same sheet; the texts count distinct (seed, sheet).
    sh = lambda rs: len({(r["seed"], r["sheet"]) for r in rs})
    put("windows_clean_sheets", sh(clean), REL + "windows.csv", "distinct (seed, sheet) of the clean rows", "the clean rows (%d)" % len(clean))
    put("windows_sheets_distinct", sh(W), REL + "windows.csv", "distinct (seed, sheet)", "every row (%d)" % len(W))
    put("windows_candidate_sheets", sh(cand), REL + "windows.csv", "distinct (seed, sheet) of rows with a candidate", "status != no candidate")
    cs_ = {(r["seed"], r["sheet"]) for r in clean}
    put("windows_candidate_sheets_not_clean", len({(r["seed"], r["sheet"]) for r in cand} - cs_), REL + "windows.csv",
        "distinct (seed, sheet) with a candidate and no clean window on either run", "status != no candidate")
    put("windows_clean_seeds", len({r["seed"] for r in clean}), REL + "windows.csv", "distinct seed of the clean rows",
        "the clean rows (%d)" % len(clean))
    put("windows_clean_sources", len({r["source"] for r in clean}), REL + "windows.csv", "distinct source of the clean rows",
        "the clean rows (%d)" % len(clean))
    noclean = [r for r in W if r["status"] == "no clean window"]
    att = rd(os.path.join(BW, "attempts.csv"))
    labels = {r["label"] for r in noclean}
    fail = [r for r in att if r["label"] in labels]
    put("windows_no_clean", len(noclean), REL + "windows.csv", "status = no clean window", "every row",
        "every attempt of those rows failed on too few whole tiles, none on a score under the bar (attempts.csv status)",
        "yes" if fail and all(r["status"].startswith("not measurable") and "tiles accepted" in r["status"] for r in fail) else "no")
    ranked = sorted(clean, key=lambda r: int(r["rank"]))
    best = ranked[0]
    for k, col in (("windows_best_covered", "covered_share"), ("windows_best_hole", "hole_share"),
                   ("windows_best_flagged", "flagged_share"), ("windows_best_fibre", "window_fibre"),
                   ("windows_best_tiles", "tiles_accepted"), ("windows_best_sheet", "sheet"), ("windows_best_source", "source")):
        put(k, best[col], REL + "windows.csv", col, "rank = 1 (%s)" % best["label"])
    put("windows_best_seed", best["seed"].replace("PHerc0826-seed", ""), REL + "windows.csv", "seed", "rank = 1 (%s)" % best["label"])
    b3 = sorted([r for r in W if r["best3"]], key=lambda r: r["best3"])
    put("windows_best3_seeds", ", ".join(r["seed"].replace("PHerc0826-seed", "") for r in b3), REL + "windows.csv",
        "seed of the rows with best3 set, in its order", "best3 rows (%d)" % len(b3),
        "three different seeds", "yes" if len({r["seed"] for r in b3}) == len(b3) == 3 else "no")
    put("windows_best3_flagged_max", max(b3, key=lambda r: float(r["flagged_share"]))["flagged_share"], REL + "windows.csv",
        "flagged_share, max", "best3 rows")
    put("windows_best3_covered_min", min(b3, key=lambda r: float(r["covered_share"]))["covered_share"], REL + "windows.csv",
        "covered_share, min", "best3 rows")
    tiles = [int(r["tiles_accepted"]) for r in clean]
    put("windows_clean_tiles_min", min(tiles), REL + "windows.csv", "tiles_accepted, min", "the clean rows")
    put("windows_clean_tiles_max", max(tiles), REL + "windows.csv", "tiles_accepted, max", "the clean rows")
    put("windows_tiles_per_window", max(int(r["tiles"]) for r in clean), REL + "windows.csv", "tiles, max", "the clean rows")
    st = rd(os.path.join(BW, "selftest.csv"))
    put("windows_selftests_passing", sum(r["passes"] == "yes" for r in st), REL + "selftest.csv", "passes = yes",
        "every row (%d)" % len(st), "every self test passes", "yes" if all(r["passes"] == "yes" for r in st) else "no")
    # The grid's angle to the scan's height axis, the axis nearer z of each best window (angles.csv).
    ang = {r["tag"]: r for r in rd(os.path.join(BW, "angles.csv"))}
    tag_of = {r["label"]: "bw" + r["rank"] for r in b3}
    near = [min(float(ang[tag_of[r["label"]]]["angle_i_to_z_median"]), float(ang[tag_of[r["label"]]]["angle_j_to_z_median"])) for r in b3]
    put("windows_best3_angle_min_deg", "%.1f" % min(near), REL + "angles.csv", "min(angle_i_to_z_median, angle_j_to_z_median), min",
        "the best3 tags (%s)" % " ".join(tag_of[r["label"]] for r in b3))
    put("windows_best3_angle_max_deg", "%.1f" % max(near), REL + "angles.csv", "min(angle_i_to_z_median, angle_j_to_z_median), max",
        "the best3 tags")
    al = {r["tag"]: r for r in rd(os.path.join(BW, "aligned.csv"))}
    put("windows_aligned_tool", "align.py", REL + "aligned.csv", "comment line: written by", "header",
        "the resampling is best-windows-0826's own align.py", "yes" if "written by best-windows-0826/tools/align.py" in header(os.path.join(BW, "aligned.csv")) else "no")
    put("windows_aligned_spacing_min_vox", min(al[tag_of[r["label"]]]["median_row_step_vox"] for r in b3), REL + "aligned.csv",
        "median_row_step_vox, min", "best3 tags")
    # The straightened sections and their reading (see the docstring).
    sp = os.path.join(BW, "straight.csv")
    SR = rd(sp)
    wins = {r["peak_window_vox"] for r in SR}
    if len(wins) != 1:
        sys.exit("checks_summary.py: straight.csv has more than one peak window")
    wv = int(wins.pop())
    offs = sorted(abs(t) for t in range(-wv, wv + 1))
    rnd_med = statistics.median(offs)
    rnd_share = sum(t <= 3 for t in offs) / len(offs)
    put("straight_peak_window_vox", wv, REL + "straight.csv", "peak_window_vox", "every row")
    mn = re.search(r"share_within_(\d+)_vox", ",".join(SR[0].keys()))
    if not mn or int(mn.group(1)) != 3:
        sys.exit("checks_summary.py: straight.csv has no share_within_3_vox column")
    put("straight_near_vox", mn.group(1), REL + "straight.csv", "the column name share_within_N_vox", "header")
    put("straight_random_median_vox", "%g" % rnd_med, "this tool", "median |t| over the %d integer offsets -%d to %d" % (len(offs), wv, wv),
        "arithmetic, not a measured null")
    put("straight_random_share", "%.4f" % rnd_share, "this tool", "share of |t| <= 3 over the same offsets", "arithmetic, not a measured null")
    by = {}
    for r in SR:
        by.setdefault(r["tag"], {})[r["line"]] = r
    passing = []
    for tag in [tag_of[r["label"]] for r in b3] + sorted(t for t in by if not t.startswith("bw")):
        d = by.get(tag, {})
        if set(d) != {"i", "j"}:
            put("straight_%s_separates" % tag, "not measured", REL + "straight.csv", "rows of this tag", "tag = %s" % tag)
            continue
        sep = all(float(d[l]["peak_offset_median_vox"]) < rnd_med and float(d[l]["share_within_3_vox"]) > rnd_share for l in "ij")
        if sep:
            passing.append(tag)
        for l in "ij":
            put("straight_%s_%s_median_vox" % (tag, l), "%g" % float(d[l]["peak_offset_median_vox"]), REL + "straight.csv",
                "peak_offset_median_vox", "tag = %s, line = %s" % (tag, l))
            put("straight_%s_%s_share" % (tag, l), d[l]["share_within_3_vox"], REL + "straight.csv", "share_within_3_vox",
                "tag = %s, line = %s" % (tag, l))
        put("straight_%s_separates" % tag, "yes" if sep else "no", "this tool",
            "both lines: median below the random median and share above the random share", "tag = %s" % tag)
    b3tags = [tag_of[r["label"]] for r in b3]
    put("straight_best3_separating", sum(t in passing for t in b3tags), "this tool", "best3 tags that separate", " ".join(b3tags))
    fail_meds = [float(by[t][l]["peak_offset_median_vox"]) for t in by if t not in passing for l in "ij"]
    pass_meds = [float(by[t][l]["peak_offset_median_vox"]) for t in passing for l in "ij"]
    put("straight_separating_median_min_vox", "%g" % min(pass_meds) if pass_meds else "none", REL + "straight.csv",
        "peak_offset_median_vox, min over the separating tags", " ".join(passing) or "none")
    put("straight_separating_median_max_vox", "%g" % max(pass_meds) if pass_meds else "none", REL + "straight.csv",
        "peak_offset_median_vox, max over the separating tags", " ".join(passing) or "none")
    put("straight_other_median_min_vox", "%g" % min(fail_meds) if fail_meds else "none", REL + "straight.csv",
        "peak_offset_median_vox, min over the other tags", " ".join(t for t in by if t not in passing))
    put("straight_other_median_max_vox", "%g" % max(fail_meds) if fail_meds else "none", REL + "straight.csv",
        "peak_offset_median_vox, max over the other tags", " ".join(t for t in by if t not in passing))
    put("straight_separating_seed", ", ".join(r["seed"].replace("PHerc0826-seed", "") for r in b3 if tag_of[r["label"]] in passing) or "none",
        REL + "windows.csv", "seed of the separating best3 rows", " ".join(passing) or "none")
    # The positive control (positive-control-0139). verdict.csv is appended, never rewritten: the text reads, for each of
    # our sheets, the LAST row whose variant is the lattice render and whose best read is that sheet's (the reads of a
    # sheet against the organisers' segment on that sheet's own common region). null-best.csv: the LAST «both copies»
    # row of each sheet. labelfree-w016.csv: run_one_v2's label free statistic on known ink (director 12:52:52Z).
    PCD = os.path.join(S, "evidence", "studies", "positive-control-0139")
    PR = "positive-control-0139/"
    vrows = rd(os.path.join(PCD, "verdict.csv"))
    nrows = rd(os.path.join(PCD, "null-best.csv"))
    put("pc_verdict_rows", len(vrows), PR + "verdict.csv", "rows", "every row")
    for sheet, tag in (("ours-A-S0", "a"), ("ours-Bx-S0", "b")):
        vs = [r for r in vrows if r["variants_of_ours"] == "lattice" and r["ours_best_row"].startswith(sheet + " ")]
        if not vs:
            sys.exit("checks_summary.py: verdict.csv has no lattice row for %s" % sheet)
        v = vs[-1]
        cov = "last lattice row of %s (time %s)" % (sheet, v["time"])
        put("pc_%s_ours_ba" % tag, v["ours_best_ba"], PR + "verdict.csv", "ours_best_ba", cov)
        put("pc_%s_theirs_ba" % tag, v["theirs_best_ba"], PR + "verdict.csv", "theirs_best_ba", cov)
        mn = re.search(r"n_common (\d+)", v["ours_best_row"])
        put("pc_%s_common" % tag, mn.group(1), PR + "verdict.csv", "ours_best_row: n_common", cov)
        ns = [r for r in nrows if r["surface"] == sheet and r["null"] == "both copies"]
        if not ns:
            sys.exit("checks_summary.py: null-best.csv has no both copies row for %s" % sheet)
        n = ns[-1]
        ncov = "last both copies row of %s (time %s)" % (sheet, n["time"])
        put("pc_%s_ours_reads" % tag, n["sheet_rows"], PR + "null-best.csv", "sheet_rows", ncov)
        put("pc_%s_null_best" % tag, n["null_best_ba"], PR + "null-best.csv", "null_best_ba", ncov)
        put("pc_%s_null_reads" % tag, n["null_rows"], PR + "null-best.csv", "null_rows", ncov)
        put("pc_%s_beyond_null" % tag, n["sheet_beyond_null"], PR + "null-best.csv", "sheet_beyond_null", ncov,
            "the sheet best is that of verdict.csv", "yes" if n["sheet_best_ba"] == v["ours_best_ba"] else "no")
    last = [r for r in vrows if r["variants_of_ours"] == "lattice"][-1]
    put("pc_bar_ink", re.search(r"(0\.\d+)", [r for r in vrows if r["branch"].startswith("neither")][0]["branch"]).group(1)
        if any(r["branch"].startswith("neither") for r in vrows) else "not stated", PR + "verdict.csv", "branch: the bar in words", "every row")
    put("pc_branch", last["branch"], PR + "verdict.csv", "branch", "last lattice row (time %s)" % last["time"])
    lf = rd(os.path.join(PCD, "labelfree-w016.csv"))
    runs_ = [r for r in lf if r["run"] != "VERDICT"]
    yes = [r for r in runs_ if r["signal"] == "yes"]
    put("pc_labelfree_rows", len(runs_), PR + "labelfree-w016.csv", "rows other than VERDICT", "every row")
    put("pc_labelfree_yes", len(yes), PR + "labelfree-w016.csv", "signal = yes", "rows other than VERDICT",
        "every row says yes or no", "yes" if all(r["signal"] in ("yes", "no") for r in runs_) else "no")
    put("pc_labelfree_square_mm", "%.0f" % float(runs_[0]["square_mm"]), PR + "labelfree-w016.csv", "square_mm, rounded", "every row",
        "every square within half a millimetre of it", "yes" if all(abs(float(r["square_mm"]) - round(float(runs_[0]["square_mm"]))) < 0.5 for r in runs_) else "no")
    blind = len(yes) == 0 and all(r["sheet_beyond_null"] == "yes" for r in nrows if r["null"] == "both copies" and r is not None)
    put("pc_ink_0826_reading", "not measurable at our sensitivity" if blind else "undecided", "this tool",
        "director 2026-09-29T12:52:52Z: the label free statistic says no on every known ink row while our sheets read the labels "
        "beyond their nulls", "labelfree-w016.csv, null-best.csv")
    ctl = rd(os.path.join(PCD, "control.csv"))
    mr = {re.search(r"\(([0-9.]+) cm2\)", r["caveat"]).group(1) for r in ctl if re.search(r"\(([0-9.]+) cm2\)", r["caveat"])}
    put("pc_region_cm2", mr.pop() if len(mr) == 1 else "not stated", PR + "control.csv", "caveat: the clean region in cm2", "every row",
        "one value on every row", "yes" if not mr else "no")
    put("pc_match_vox", re.search(r"at k = (\d+)", header(os.path.join(PCD, "verdict.csv"))).group(1), PR + "verdict.csv",
        "header: at k = N", "header")
    # The headline (render-routes-0826, route R2c): our start, the organisers' tracer on a 60 mm crop, our checks
    # (director 2026-09-29T12:52:52Z and 15:38:23Z). The R2cnative rows of square-checks.csv and routes.csv.
    RRD = os.path.join(S, "evidence", "studies", "render-routes-0826")
    RRR = "render-routes-0826/"
    sqc = [r for r in rd(os.path.join(RRD, "square-checks.csv")) if r["route"] == "R2cnative"]
    rts = {r["surface"]: r for r in rd(os.path.join(RRD, "routes.csv")) if r.get("route") == "R2cnative"}
    runs = {r["start"]: r for r in rd(os.path.join(RRD, "r2c-runs.csv"))}
    order = sorted(sqc, key=lambda r: -float(r["square_mm"]))
    for k, r in zip(("one", "two"), order):
        sf = r["surface"]
        cov = "route R2cnative, surface %s (time %s)" % (sf, r["utc"])
        put("r2c_%s_seed" % k, sf.split("-")[1].replace("seed", ""), RRR + "square-checks.csv", "surface", cov)
        for col, q in (("square_mm", "square_mm"), ("strict_square_mm", "strict_mm"), ("pairwise_square_mm", "pairwise_mm"),
                       ("section_i_share_within_3_vox", "sec_i_share"), ("section_j_share_within_3_vox", "sec_j_share"),
                       ("within3_share_all_cells", "on_ours_share")):
            put("r2c_%s_%s" % (k, q), r[col], RRR + "square-checks.csv", col, cov)
        for col, q in (("section_i_peak_offset_median_vox", "sec_i_median"), ("section_j_peak_offset_median_vox", "sec_j_median")):
            put("r2c_%s_%s" % (k, q), "%g" % float(r[col]), RRR + "square-checks.csv", col, cov)
        put("r2c_%s_our_sheet" % k, r["within3_best_sheet"].replace("PHerc0826-", ""), RRR + "square-checks.csv", "within3_best_sheet", cov)
        flags = [r[c] for c in ("in_square_v2", "in_square_self_conflict_a", "in_square_self_conflict_b", "in_square_a2_rule", "in_square_holes")]
        put("r2c_%s_flags" % k, sum(int(x) for x in flags), RRR + "square-checks.csv",
            "in_square_v2 + self_conflict_a + self_conflict_b + a2_rule + holes", cov,
            "the certified square carries no flag", "yes" if all(x == "0" for x in flags) else "no")
        t = rts[sf]
        put("r2c_%s_fibre" % k, t["fibre"], RRR + "routes.csv", "fibre", cov, "the square does not touch the crop's edge",
            "yes" if t["square_touches_crop_edge"] == "no" else "no")
        put("r2c_%s_fibre_tiles" % k, t["fibre_tiles"], RRR + "routes.csv", "fibre_tiles", cov)
        put("r2c_%s_window" % k, t["window"], RRR + "routes.csv", "window", cov)
        put("r2c_%s_rotation_deg" % k, t["rotation_inplane_median"], RRR + "routes.csv", "rotation_inplane_median", cov)
        put("r2c_%s_generations" % k, runs[sf]["max_gen"], RRR + "r2c-runs.csv", "max_gen", "start %s" % sf)
    al = [r for r in rd(os.path.join(RRD, "aligned-square.csv")) if r["route"] == "R2cnative" and r["surface"] == order[0]["surface"]]
    if al:
        a0 = al[-1]
        cov = "route R2cnative, surface %s (time %s)" % (a0["surface"], a0["utc"])
        put("r2c_one_aligned_residual_deg", a0["residual_rotation_inplane_median_deg"], RRR + "aligned-square.csv",
            "residual_rotation_inplane_median_deg", cov, "the regrid is best-windows-0826's align.py",
            "yes" if a0["tool"].startswith("best-windows-0826/tools/align.py") else "no")
        put("r2c_one_aligned_from_square", a0["square_share_from_certified_square"], RRR + "aligned-square.csv",
            "square_share_from_certified_square", cov)
    dec = open(os.path.join(S, "prereg", "render-routes-0826.md")).read()
    mc = re.search(r"\((\d+) x (\d+) mm\)", dec)
    put("r2c_crop_mm", mc.group(1) if mc and mc.group(1) == mc.group(2) else "not stated", "prereg/render-routes-0826.md",
        "«Route R2cnative: ... (N x N mm)»", "the declaration")
    ho = header(os.path.join(RRD, "old-square-on-r2c.csv"))
    oq = rd(os.path.join(RRD, "old-square-on-r2c.csv"))
    mo = re.search(r"the R2b ([0-9.]+) mm square", ho)
    put("r2c_old_square_mm", mo.group(1), RRR + "old-square-on-r2c.csv", "header line", "header")
    sc = [r for r in oq if r["check"].startswith("self conflict")]
    put("r2c_old_conflict_pairs_outside", sum(int(r["cause_outside_old_crop"]) for r in sc), RRR + "old-square-on-r2c.csv",
        "cause_outside_old_crop, sum over the self conflict rows (a end and b end)", "self conflict rows",
        "none of those pairs has its other end inside the old crop", "yes" if all(r["cause_inside_old_crop"] == "0" for r in sc) else "no")
    others = [r for r in oq if not r["check"].startswith("self conflict")]
    put("r2c_old_other_flags", sum(int(r["flagged_old_square_cells"]) for r in others), RRR + "old-square-on-r2c.csv",
        "flagged_old_square_cells, sum over holes, v2 and a2 rows", "those rows")
    st = [r for r in rd(os.path.join(RRD, "regrid-selftest.csv")) if r["passed"] == "no"]
    put("regrid_first_fail_value", st[0]["value"] if st else "none", RRR + "regrid-selftest.csv", "value of the first row with passed no",
        st[0]["run"] + " " + st[0]["test"] if st else "")
    put("regrid_first_fail_bar", st[0]["bar"].replace("< ", "") if st else "none", RRR + "regrid-selftest.csv", "bar of that row", "")
    rc = rd(os.path.join(S, "evidence", "studies", "ink-finetune-k2", "refcheck.csv"))
    put("refcheck_ncc_min", min(r["best_ncc"] for r in rc), "ink-finetune-k2/refcheck.csv", "best_ncc, min", "every row (%d)" % len(rc),
        "every row passes at k0 m0 with no offset", "yes" if all(r["verdict"] == "pass" and r["best_k"] == "0" and r["best_dy"] == "0"
                                                                  and r["best_dx"] == "0" for r in rc) else "no")
    put("refcheck_segments", len(rc), "ink-finetune-k2/refcheck.csv", "rows", "every row")
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/checks_summary.py from the copies of best-windows-0826 in src/evidence/studies and '
                 'derived/fibre-summary.csv; rows_covered says which rows a value is over; the straightened section reading is '
                 'this tool\'s rule (docstring), arithmetic, not a measured null"\n')
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    bad = [r for r in out if r["check"] and r["check_value"] not in ("", "yes")]
    for r in bad:
        print("checks_summary.py: check failed: %s %s" % (r["quantity"], r["check_value"]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
