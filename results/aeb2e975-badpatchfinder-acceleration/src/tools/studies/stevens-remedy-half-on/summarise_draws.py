#!/usr/bin/env python3
"""stevens-remedy-half-on, DECLARATION.md addition of 2026-09-25T18:43:23Z: evidence/draws-per-sheet.csv,
evidence/draws-per-seed.csv (the three seeds, draws d0 to d3: best square and best a2 cluster rule square, spreads) and
evidence/overlap-per-seed.csv (evidence/overlap-per-sheet.csv pooled per seed and draw over the sheets that pass the
reconstruction gate, the declared class, each seed's reading and the study's READING row). Every value read back from a
CSV a tool wrote; a missing value is 'not measurable' with its reason, never zero. The last printed line is the reading."""
import csv, itertools, os, subprocess

ST = "/data/scrollagent/runs/rev1/stevens-remedy-half-on"
EV = ST + "/evidence"
NM = "not measurable"
SEEDS = ["PHerc1447-seed355", "PHerc1447-seed262", "PHerc1447-seed664"]
DRAWS = ["d0", "d1", "d2", "d3"]
TOOL = "stevens-remedy-half-on/tools/summarise_draws.py"
MIN_PTS = 30


def rows(p):
    return list(csv.DictReader(l for l in open(p, newline="") if not l.lstrip('"').startswith("#")))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def utc():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()


def run_dir(seed, d):
    return ST + ("/scratch/arm-on/%s" % seed if d == "d0" else "/scratch/draws/%s-%s" % (seed, d))


def per_sheet_file(seed, d):
    return EV + ("/per-sheet-arm-on-%s.csv" % seed if d == "d0" else "/per-sheet-draw%s-%s.csv" % (d[1], seed))


def excl_set(seed, d):
    p = run_dir(seed, d) + "/view/annealState_out.csv"
    return set(int(l) for l in open(p) if l.strip()) if os.path.exists(p) else None


def write(path, header, cols, R):
    with open(path + ".part", "w", newline="") as fh:
        fh.write("# written by %s at %s: %s\n" % (TOOL, utc(), header))
        w = csv.DictWriter(fh, cols, lineterminator="\n", extrasaction="ignore"); w.writeheader(); w.writerows(R)
    os.rename(path + ".part", path)


def draws():
    sheet_rows, seed_rows = [], []
    for s in SEEDS:
        per = {}
        for d in DRAWS:
            p = per_sheet_file(s, d)
            per[d] = {int(r["sheet"]): r for r in rows(p)} if os.path.exists(p) else None
        sheets = sorted(set().union(*[set(v) for v in per.values() if v]))
        for n in sheets:
            r = {"seed": s, "sheet": n}
            for d in DRAWS:
                x = per[d].get(n) if per[d] else None
                if x and "square_mm_before" not in r:
                    r["square_mm_before"] = x["square_mm_before"]; r["a2_cluster_rule_square_mm_before"] = x["a2_cluster_rule_square_mm_before"]
                r["square_mm_%s" % d] = x["square_mm_after"] if x else "%s (draw absent)" % NM
                r["a2_cluster_rule_square_mm_%s" % d] = x["a2_cluster_rule_square_mm_after"] if x else "%s (draw absent)" % NM
                r["bytes_equal_delivered_%s" % d] = x["sheet_bytes_equal_delivered"] if x else "%s (draw absent)" % NM
            v = [fnum(r["square_mm_%s" % d]) for d in DRAWS[1:]]
            r["square_spread_d1_d3_mm"] = "%.4f" % (max(v) - min(v)) if all(x is not None for x in v) else NM
            sheet_rows.append(r)
        r = {"seed": s}
        for d in DRAWS:
            S = per[d]
            rc = {}
            if os.path.exists(run_dir(s, d) + "/rerun.csv"):
                rc = {x["quantity"]: x["value"] for x in rows(run_dir(s, d) + "/rerun.csv")}
            r["anneal_excluded_patches_%s" % d] = rc.get("anneal_excluded_patches", NM)
            if not S:
                for k in ("best_square_mm", "a2_best_cluster_rule_square_mm", "sheets_changed"):
                    r["%s_%s" % (k, d)] = "%s (draw absent or failed)" % NM
                continue
            if "best_square_mm_before" not in r:
                b = [fnum(x["square_mm_before"]) for x in S.values()]; b = [x for x in b if x is not None]
                r["best_square_mm_before"] = "%.4f" % max(b) if b else NM
                b = [fnum(x["a2_cluster_rule_square_mm_before"]) for x in S.values()]; b = [x for x in b if x is not None]
                r["a2_best_cluster_rule_square_mm_before"] = "%.4f" % max(b) if b else NM
            for k, col in (("best_square_mm", "square_mm_after"), ("a2_best_cluster_rule_square_mm", "a2_cluster_rule_square_mm_after")):
                v = [fnum(x[col]) for x in S.values()]; v = [x for x in v if x is not None]
                r["%s_%s" % (k, d)] = "%.4f" % max(v) if v else NM
            r["sheets_changed_%s" % d] = sum(x["sheet_bytes_equal_delivered"] != "yes" for x in S.values())
        for k in ("best_square_mm", "a2_best_cluster_rule_square_mm"):
            for lab, ds in (("d1_d3", DRAWS[1:]), ("d0_d3", DRAWS)):
                v = [fnum(r.get("%s_%s" % (k, d))) for d in ds]
                r["%s_spread_%s" % (k, lab)] = "%.4f" % (max(v) - min(v)) if all(x is not None for x in v) else NM
        E = {d: excl_set(s, d) for d in DRAWS}
        J = [len(E[a] & E[b]) / len(E[a] | E[b]) for a, b in itertools.combinations(DRAWS[1:], 2) if E[a] is not None and E[b] is not None and (E[a] | E[b])]
        r["excluded_jaccard_mean_d1_d3"] = "%.4f" % (sum(J) / len(J)) if len(J) == 3 else NM
        ALL = [E[d] for d in DRAWS[1:]]
        r["excluded_in_all_three_d1_d3"] = len(set.intersection(*ALL)) if all(x is not None for x in ALL) else NM
        seed_rows.append(r)
    scol = ["seed", "sheet", "square_mm_before"] + ["square_mm_%s" % d for d in DRAWS] + ["square_spread_d1_d3_mm",
            "a2_cluster_rule_square_mm_before"] + ["a2_cluster_rule_square_mm_%s" % d for d in DRAWS] + \
           ["bytes_equal_delivered_%s" % d for d in DRAWS]
    write(EV + "/draws-per-sheet.csv", "one row per sheet of the three seeds; square_mm = square.py square_mm_min_step, "
          "a2 cluster rule square at T* 25, S 101; before = delivered, d0 = the ten seed arm, d1 to d3 = new draws of the same "
          "arm (nm 10 1000; each annealing one random draw, anneal.cpp:675); values read back from per-sheet-arm-on-<seed>.csv "
          "and per-sheet-draw<k>-<seed>.csv (tools/a2_after.py)", scol, sheet_rows)
    dcol = ["seed", "best_square_mm_before"] + ["best_square_mm_%s" % d for d in DRAWS] + \
           ["best_square_mm_spread_d1_d3", "best_square_mm_spread_d0_d3", "a2_best_cluster_rule_square_mm_before"] + \
           ["a2_best_cluster_rule_square_mm_%s" % d for d in DRAWS] + \
           ["a2_best_cluster_rule_square_mm_spread_d1_d3", "a2_best_cluster_rule_square_mm_spread_d0_d3"] + \
           ["sheets_changed_%s" % d for d in DRAWS] + ["anneal_excluded_patches_%s" % d for d in DRAWS] + \
           ["excluded_jaccard_mean_d1_d3", "excluded_in_all_three_d1_d3"]
    write(EV + "/draws-per-seed.csv", "one row per seed; best = the largest over the seed's sheets; spread = max minus min "
          "over the draws named; excluded_jaccard = mean pairwise |intersection|/|union| of annealState_out.csv over d1 to d3",
          dcol, seed_rows)
    return seed_rows


def klass(E, A):
    if E >= 2:
        return "R" if A >= 0.5 else "P"
    if E > 1.5:
        return "I"
    return "H"


def overlap():
    R = rows(EV + "/overlap-per-sheet.csv")
    out = []
    order = []
    for r in R:
        k = (r["seed"], r["draw"])
        if k not in order:
            order.append(k)
    per_seed_class = {}
    for seed, d in order:
        S = [r for r in R if r["seed"] == seed and r["draw"] == d]
        o = {"seed": seed, "draw": d}
        if len(S) == 1 and S[0]["sheet"] == "all":
            o.update(sheets_pooled=0, status=S[0]["source"], klass=S[0]["source"]); out.append(o); continue
        ok = [r for r in S if r["reconstruction_gate"] == "pass" and fnum(r["measurable_points"]) is not None]
        o["sheets_pooled"] = len(ok); o["sheets_not_pooled"] = len(S) - len(ok)
        o["excluded_patches_in_draw"] = S[0]["excluded_patches_in_draw"]
        for c in ("covered_cells", "cells_in_excluded", "measurable_points", "flagged_points", "measurable_in_excluded",
                  "flagged_in_excluded", "kept_points", "kept_in_excluded"):
            o[c] = sum(int(r[c]) for r in ok)
        sh = lambda a, b: ("%.6f" % (a / b)) if b else NM
        o["e_cells"] = sh(o["cells_in_excluded"], o["covered_cells"])
        M, F, Me, Fe, K, Ke = (o[c] for c in ("measurable_points", "flagged_points", "measurable_in_excluded",
                                                "flagged_in_excluded", "kept_points", "kept_in_excluded"))
        o.update(f=sh(F, M), e=sh(Me, M), A=sh(Fe, F), B=sh(Fe, Me), f_k=sh(K, M), A_k=sh(Ke, K), B_k=sh(Ke, Me))
        o["E"] = "%.4f" % ((Fe / Me) / (F / M)) if (M and F and Me) else NM
        o["E_k"] = "%.4f" % ((Ke / Me) / (K / M)) if (M and K and Me) else NM
        if F < MIN_PTS or Me < MIN_PTS:
            o["status"] = "%s (too few points: flagged %d, in excluded %d, rule needs %d each)" % (NM, F, Me, MIN_PTS)
            o["klass"] = NM
        else:
            o["status"] = "readable"
            o["klass"] = klass(float(o["E"]), float(o["A"]))
            per_seed_class.setdefault(seed, []).append((d, o["klass"]))
        out.append(o)
    names = {"R": "R (supports removes crossings)", "P": "P (partial)", "I": "I (indeterminate)",
             "H": "H (supports holes alone; does not exclude crossings below 25 degrees)"}
    seeds = []
    for seed, _ in order:
        if seed not in seeds:
            seeds.append(seed)
    reading = {}
    for seed in seeds:
        L = per_seed_class.get(seed, [])
        drawn = [d for s, d in order if s == seed]
        if not L:
            c = "%s (no readable draw)" % NM
        elif len(set(k for _, k in L)) == 1:
            c = L[0][1]
        else:
            c = "unstable across draws"
        reading[seed] = c
        out.append({"seed": seed, "draw": "SEED", "status": "readable draws %s of %s (%s)" % (
            len(L), len(drawn), " ".join("%s %s" % x for x in L)), "klass": names.get(c, c)})
    nR = sum(reading.get(s) == "R" for s in SEEDS); nH = sum(reading.get(s) == "H" for s in SEEDS)
    if nR >= 2 and nH == 0:
        rd = "R: the declared rule favours «removes crossings» (%d of 3 seeds R, none H)" % nR
    elif nH >= 2 and nR == 0:
        rd = "H: the declared rule favours «holes alone» (%d of 3 seeds H, none R); this does not exclude crossings below a2's 25 degrees" % nH
    else:
        rd = "the data do not choose (%s)" % ", ".join("%s %s" % (s.split("-")[1], reading.get(s, NM)) for s in SEEDS)
    out.append({"seed": "READING", "draw": "", "status": "three seeds %s over draws d0 to d3" % ", ".join(SEEDS),
                "klass": rd})
    cols = ["seed", "draw", "status", "klass", "sheets_pooled", "sheets_not_pooled", "excluded_patches_in_draw",
            "covered_cells", "cells_in_excluded", "e_cells", "measurable_points", "flagged_points", "measurable_in_excluded",
            "flagged_in_excluded", "f", "e", "A", "B", "E", "kept_points", "kept_in_excluded", "f_k", "A_k", "B_k", "E_k"]
    write(EV + "/overlap-per-seed.csv", "evidence/overlap-per-sheet.csv pooled per seed and draw over the sheets passing "
          "the reconstruction gate; f flagged share, e share of measurable points in excluded patches, e_cells the same over "
          "all covered cells, A share of flagged points in excluded patches, B share of excluded points flagged, E = B/f "
          "enrichment; _k with the cluster rule's kept points. Rule (DECLARATION.md 2026-09-25T18:43:23Z): readable when "
          "flagged and excluded points are at least 30 each; R E>=2 and A>=0.5, P E>=2 and A<0.5, I 1.5<E<2, H E<=1.5; a "
          "seed's reading is the class shared by all its readable draws; READING over the three seeds", cols, out)
    return rd


if __name__ == "__main__":
    draws()
    print(overlap())
