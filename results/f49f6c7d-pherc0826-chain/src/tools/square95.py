#!/usr/bin/env python3
"""The five capped seeds regrown at g 72000 (item 95 (c), square20-0826-95), one row per seed and a few
over all, from the study's per seed files in this work's snapshot.

The study's own summary.csv is NOT read: its tool crashed and wrote «not measurable» in every cell
(queue item 2026-09-28-square20-0826-95-21mm-on-seed2604.md). Per seed:
  g36000 best    cap-check.csv best_square_mm_min_step, checked equal to the chain's per-seed-queue.csv
  at the cap     cap-check.csv at_cap (the g 36000 growth reached its generation cap)
  g72000 best    max square_mm_min_step over the measured rows of squares-<seed>.csv, and its sheet and cells
  cluster rule   max a2_cluster_rule_square_mm of a2-cluster/<seed>.csv
  generation     growth_highest_generation of runs-<seed>.csv, and whether it ended below 72000 by itself
  identity       identity-36000-<seed>.csv, rel rows up to generation 36000 equal as sets
Item 95 (f), added 2026-09-28 (director 21:22:13Z): the ten next capped seeds, rows of cap-check-next10.csv
with regrow = yes, also regrown at g 72000. Per seed, before = max square_mm_min_step over the measured rows of
the chain's own squares-<seed>.csv (g 36000, C40; checked equal to cap-check-next10.csv), after = the same over
square20-0826-95's squares-<seed>.csv (g 72000, C80). Scope «next10» gives their count and the largest
absolute change with its seed; scope «all» gives the largest absolute change among the five other than the
best seed.
Usage: square95.py [--out PATH]
"""
import argparse, csv, glob, os, re, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(S, "evidence", "studies", "square20-0826-95")
CH = os.path.join(S, "evidence", "studies", "chain-0826")


def rd(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "square95.csv"))
    a = ap.parse_args()
    cap = {r["attempt"]: r for r in rd(os.path.join(Q, "cap-check.csv"))}
    queue = {r["attempt"]: r for r in rd(os.path.join(CH, "per-seed-queue.csv"))}
    out = []

    def put(scope, q, v, src, check="", cv=""):
        out.append({"scope": scope, "quantity": q, "value": v, "source": src, "check": check, "check_value": cv})
    best_all = None
    for seed in sorted(cap, key=lambda s: -float(cap[s]["best_square_mm_min_step"])):
        c = cap[seed]
        put(seed, "g36000_best_mm", c["best_square_mm_min_step"], "cap-check.csv best_square_mm_min_step",
            "equals the chain's largest_square_mm_min_step",
            "yes" if abs(float(c["best_square_mm_min_step"]) - float(queue[seed]["largest_square_mm_min_step"])) < 5e-5 else "no")
        put(seed, "g36000_at_cap", c["at_cap"], "cap-check.csv at_cap")
        sq = [r for r in rd(os.path.join(Q, "squares-%s.csv" % seed)) if r["status"] == "measured"]
        b = max(sq, key=lambda r: float(r["square_mm_min_step"]))
        put(seed, "g72000_best_mm", b["square_mm_min_step"], "squares-<seed>.csv square_mm_min_step, max over measured sheets")
        put(seed, "g72000_best_sheet", b["sheet"], "that row, sheet")
        put(seed, "g72000_best_cells", b["square_cells"], "that row, square_cells")
        put(seed, "g72000_best_reaches_20mm", b["reaches_20mm"], "that row, reaches_20mm")
        a2 = rd(os.path.join(Q, "a2-cluster", "%s.csv" % seed))
        cr = max(float(r["a2_cluster_rule_square_mm"]) for r in a2 if re.fullmatch(r"[0-9.]+", r["a2_cluster_rule_square_mm"]))
        put(seed, "g72000_cluster_rule_mm", "%.4f" % cr, "a2-cluster/<seed>.csv a2_cluster_rule_square_mm, max")
        a2b = [r for r in a2 if r["sheet"] == b["sheet"]]
        put(seed, "g72000_best_sheet_a2_share", a2b[0]["a2_flagged_share"] if len(a2b) == 1 else "not measurable",
            "a2-cluster/<seed>.csv a2_flagged_share of the best sheet")
        runs = {r["quantity"]: r["value"] for r in rd(os.path.join(Q, "runs-%s.csv" % seed))}
        hg = int(runs["growth_highest_generation"])
        put(seed, "g72000_highest_generation", hg, "runs-<seed>.csv growth_highest_generation")
        put(seed, "g72000_ended_by_itself", "yes" if hg < 72000 else "no", "highest generation below 72000")
        idn = {r["quantity"]: r for r in rd(os.path.join(Q, "identity-36000-%s.csv" % seed))}
        put(seed, "identity_to_36000_as_sets", idn["rel_rows_both_at_most_36000_as_sets"]["equal"], "identity-36000-<seed>.csv")
        v = float(b["square_mm_min_step"])
        if best_all is None or v > best_all[0]:
            best_all = (v, seed, b)
    put("all", "seeds", len(cap), "cap-check.csv rows")
    put("all", "seeds_at_cap", sum(c["at_cap"] == "yes" for c in cap.values()), "cap-check.csv at_cap = yes")
    put("all", "seeds_ended_by_itself", sum(1 for r in out if r["quantity"] == "g72000_ended_by_itself" and r["value"] == "yes"), "rows above")
    put("all", "g72000_best_mm", "%.4f" % best_all[0], "max over the seeds' g72000_best_mm")
    put("all", "g72000_best_seed", best_all[1], "that seed")
    put("all", "seeds_20mm", sum(1 for r in out if r["quantity"] == "g72000_best_mm" and r["scope"] != "all" and float(r["value"]) >= 20.0), "g72000_best_mm >= 20")
    others = [float(r["value"]) for r in out if r["quantity"] == "g72000_best_mm" and r["scope"] not in ("all", best_all[1])]
    put("all", "others_min_mm", "%.4f" % min(others), "g72000_best_mm of the other seeds, min")
    put("all", "others_max_mm", "%.4f" % max(others), "g72000_best_mm of the other seeds, max")
    def best(path):
        m = [float(r["square_mm_min_step"]) for r in rd(path) if r["status"] == "measured"]
        if not m:
            sys.exit("%s: no measured sheet" % path)
        return max(m)
    ch5 = []
    for seed in cap:
        if seed == best_all[1]:
            continue
        b0 = best(os.path.join(CH, "squares-%s.csv" % seed))
        b1 = best(os.path.join(Q, "squares-%s.csv" % seed))
        ch5.append((abs(b1 - b0), seed, b0, b1))
    m5 = max(ch5)
    put("all", "others_largest_abs_change_mm", "%.4f" % m5[0],
        "max over the other seeds of abs(g72000 best - chain C40 best), squares files")
    put("all", "others_largest_abs_change_seed", m5[1], "that seed")
    b0 = best(os.path.join(CH, "squares-%s.csv" % best_all[1]))
    put("all", "best_seed_g36000_mm", "%.4f" % b0, "chain-0826 squares-<seed>.csv of the best seed, max measured")
    nx = [r for r in rd(os.path.join(Q, "cap-check-next10.csv")) if r["regrow"] == "yes"]
    chg = []
    for r in nx:
        seed = r["attempt"]
        b0 = best(os.path.join(CH, "squares-%s.csv" % seed))
        b1 = best(os.path.join(Q, "squares-%s.csv" % seed))
        ok = abs(b0 - float(r["best_square_mm_min_step"])) < 5e-5
        put(seed, "next10_g36000_best_mm", "%.4f" % b0, "chain-0826 squares-<seed>.csv, max measured (C40)",
            "equals cap-check-next10.csv best_square_mm_min_step", "yes" if ok else "no")
        if not ok:
            sys.exit("%s: chain squares best %.4f is not cap-check-next10's %s" % (seed, b0, r["best_square_mm_min_step"]))
        put(seed, "next10_g72000_best_mm", "%.4f" % b1, "square20-0826-95 squares-<seed>.csv, max measured (C80)")
        chg.append((abs(b1 - b0), seed, b0, b1))
    mx = max(chg)
    put("next10", "seeds", len(nx), "cap-check-next10.csv rows with regrow = yes")
    put("next10", "largest_abs_change_mm", "%.4f" % mx[0], "max abs(g72000 best - g36000 best) over the ten")
    put("next10", "largest_abs_change_seed", mx[1], "that seed")
    put("next10", "largest_abs_change_before_mm", "%.4f" % mx[2], "that seed, g36000 best")
    put("next10", "largest_abs_change_after_mm", "%.4f" % mx[3], "that seed, g72000 best")
    put("next10", "seeds_20mm", sum(c[3] >= 20.0 for c in chg), "g72000 best >= 20")
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/square95.py at %s from the snapshot of square20-0826-95 (per seed files; its summary.csv is not read)"\n' % now)
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for r in out:
        if r["scope"] in ("all", "next10") or r["quantity"].startswith("next10") or r["quantity"] in ("g72000_best_mm", "g36000_best_mm"):
            print("  %-20s %-26s %s %s" % (r["scope"], r["quantity"], r["value"], r["check_value"]))


if __name__ == "__main__":
    main()
