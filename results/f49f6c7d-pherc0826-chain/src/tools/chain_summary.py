#!/usr/bin/env python3
"""The counts and squares of the chain on PHerc. 0826, from the snapshot in src/evidence/studies.

WHAT IT READS, all copies made by copy_evidence.py (the time of the copy is in MANIFEST.csv):
  chain-0826/seed-rule.csv        one row per draw, column group (the wave) and passes_rule
  chain-0826/ladder.csv           one row per seed grown at the ladder cap, column outcome
  chain-0826/per-seed-queue.csv   one row per ladder survivor, delivering_binary,
                                  growth_return_code, largest_square_mm_min_step
  chain-0826/squares-*.csv        one row per delivered sheet, square_mm_min_step
  chain-0826/a2-cluster/*.csv     one row per delivered sheet, a2 counts and the cluster rule square
  chain-0826/wave4-sources.csv    the header's threshold of the fourth wave's source rule

WHAT IT WRITES: src/evidence/derived/chain-summary.csv, one row per quantity and scope, with the
file and the column each value comes from. THE CHECKS ARE COLUMNS: `check` and `check_value` sit
beside a value that was checked, e.g. the best square per seed recomputed from the squares files
against the queue's own column, or the queued seeds against the ladder's survivors.

A value nobody measured is «not measurable», never a zero. The waves are named by the group column
of the chain's own files; wave N is the N-th group in draw order.

Usage: chain_summary.py [--out PATH]
"""
import argparse, csv, glob, os, re, statistics, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(S, "evidence", "studies", "chain-0826")
WAVES = None   # the groups of the files in draw order (batch-<first>-<last>-0826), read at run time


def rd(p):
    with open(p, newline="") as fh:
        lines = [l for l in fh if not l.lstrip().startswith(('"#', "#"))]
    return list(csv.DictReader(lines))


def f4(x):
    return "%.4f" % x


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "chain-summary.csv"))
    a = ap.parse_args()

    rule = rd(os.path.join(C, "seed-rule.csv"))
    ladder = rd(os.path.join(C, "ladder.csv"))
    queue = rd(os.path.join(C, "per-seed-queue.csv"))
    groups = sorted({r["group"] for r in rule} | {r["group"] for r in ladder}
                    | {r["seed_rule_group"] for r in queue})
    global WAVES
    bad = [g for g in groups if not re.fullmatch(r"batch-\d+-\d+-0826", g)]
    if bad:
        sys.exit("chain_summary.py: groups not of the form batch-<first>-<last>-0826: %s" % bad)
    WAVES = sorted(groups, key=lambda g: int(g.split("-")[1]))
    if len({r["attempt"] for r in ladder}) != len(ladder):
        sys.exit("chain_summary.py: ladder.csv repeats an attempt")

    # Best square per delivered seed, recomputed from the squares files.
    best_sq = {}
    for p in glob.glob(os.path.join(C, "squares-PHerc0826-seed*.csv")):
        rows = [r for r in rd(p) if r["status"] == "measured"]
        seed = os.path.basename(p)[len("squares-"):-len(".csv")]
        best_sq[seed] = max(float(r["square_mm_min_step"]) for r in rows) if rows else None

    # a2 per sheet.
    a2 = {}
    for p in glob.glob(os.path.join(C, "a2-cluster", "PHerc0826-seed*.csv")):
        a2[os.path.basename(p)[:-4]] = rd(p)
    tstar = {r["a2_T_star"] for rows in a2.values() for r in rows}
    sclus = {r["a2_S"] for rows in a2.values() for r in rows}
    if len(tstar) != 1 or len(sclus) != 1:
        sys.exit("chain_summary.py: a2 files carry T* %s and S %s, expected one each" % (tstar, sclus))

    head = open(os.path.join(C, "wave4-sources.csv")).readline()
    m = re.search(r"best >= ([0-9.]+) mm", head)
    if not m:
        sys.exit("chain_summary.py: wave4-sources.csv header states no source threshold")
    source_mm = float(m.group(1))

    out = []

    def put(scope, quantity, value, src, col, check="", check_value=""):
        out.append({"scope": scope, "quantity": quantity, "value": value, "source_file": src,
                    "source_column": col, "check": check, "check_value": check_value})

    scopes = [(w, "wave%d" % (i + 1)) for i, w in enumerate(WAVES)] + [(None, "all")]
    for g, tag in scopes:
        inw = (lambda r, k="group": g is None or r[k] == g)
        draws = [r for r in rule if inw(r)]
        passers = [r for r in draws if r["passes_rule"] == "yes"]
        lad = [r for r in ladder if inw(r)]
        surv = [r for r in lad if r["outcome"] == "still growing at the cap"]
        q = [r for r in queue if inw(r, "seed_rule_group")]
        deliv = [r for r in q if r["delivering_binary"].startswith("delivered")]
        crashed = [r for r in q if not r["delivering_binary"].startswith("delivered")
                   and r["growth_return_code"] == "139"]
        waiting = [r for r in q if not r["delivering_binary"].startswith("delivered")
                   and r["growth_return_code"] == "not measurable"]
        other = [r for r in q if not r["delivering_binary"].startswith("delivered")
                 and r not in crashed and r not in waiting]
        put(tag, "draws", len(draws), "chain-0826/seed-rule.csv", "rows of the wave (column group)")
        put(tag, "rule_passers", len(passers), "chain-0826/seed-rule.csv", "passes_rule = yes")
        put(tag, "ladder_grown", len(lad), "chain-0826/ladder.csv", "rows of the wave",
            "ladder rows equal rule passers", "yes" if len(lad) == len(passers) else "no, %d against %d" % (len(lad), len(passers)))
        # A wave whose ladder has not grown every rule passer yet has no survivor count: «ladder
        # unfinished», never a zero. The row over all waves counts the waves whose ladder is finished.
        unfinished = g is not None and len(lad) < len(passers)
        if g is None:
            fin = [w for w in WAVES if len([r for r in ladder if r["group"] == w]) >= len([r for r in rule if r["group"] == w and r["passes_rule"] == "yes"])]
            passers = [r for r in passers if r["group"] in fin]
            lad = [r for r in lad if r["group"] in fin]
            surv = [r for r in lad if r["outcome"] == "still growing at the cap"]
            put(tag, "waves_with_finished_ladder", len(fin), "chain-0826/ladder.csv; seed-rule.csv", "waves whose ladder rows reach their rule passers")
        put(tag, "ladder_survivors", "ladder unfinished" if unfinished else len(surv), "chain-0826/ladder.csv", "outcome = still growing at the cap")
        put(tag, "queued", len(q), "chain-0826/per-seed-queue.csv", "rows of the wave (column seed_rule_group)",
            "queued equal ladder survivors", "yes" if len(q) == len(surv) else "no, %d against %d" % (len(q), len(surv)))
        put(tag, "survivors_per_rule_passer", "ladder unfinished" if unfinished else (("%.4f" % (len(surv) / len(passers))) if passers else "not measurable"),
            "chain-0826/ladder.csv; seed-rule.csv", "ladder survivors over rule passers of the wave")
        put(tag, "delivered", len(deliv), "chain-0826/per-seed-queue.csv", "delivering_binary begins with delivered")
        put(tag, "growth_crashed", len(crashed), "chain-0826/per-seed-queue.csv", "growth_return_code = 139, not delivered")
        # A ladder survivor that the queue has no row for yet has not been grown to the end: it is waiting too (the referee,
        # 2026-09-30: wave 5's 20 survivors were in no column). The check column adds the four columns up.
        unqueued = (len(surv) - len(q)) if (not unfinished and len(surv) > len(q)) else 0
        nwait = len(waiting) + unqueued
        tot = len(deliv) + len(crashed) + nwait + len(other)
        put(tag, "waiting", nwait, "chain-0826/per-seed-queue.csv; chain-0826/ladder.csv",
            "growth_return_code not measurable, not delivered (%d); ladder survivors with no queue row (%d)" % (len(waiting), unqueued),
            "delivered + crashed + waiting + other equal ladder survivors",
            "yes" if unfinished or tot == len(surv) else "no, %d against %d" % (tot, len(surv)))
        put(tag, "not_delivered_other", len(other), "chain-0826/per-seed-queue.csv", "not delivered, growth_return_code neither 139 nor not measurable")
        best = []
        agree = 0
        for r in deliv:
            v = float(r["largest_square_mm_min_step"])
            best.append(v)
            mine = best_sq.get(r["attempt"])
            if mine is not None and abs(mine - v) < 5e-5:
                agree += 1
        put(tag, "best_square_seeds", len(best), "chain-0826/per-seed-queue.csv",
            "largest_square_mm_min_step of delivered seeds",
            "best recomputed from squares-<seed>.csv equals the queue's", "%d of %d" % (agree, len(best)))
        if best:
            put(tag, "best_square_median_mm", f4(statistics.median(best)), "chain-0826/per-seed-queue.csv", "largest_square_mm_min_step, median over delivered seeds")
            put(tag, "best_square_max_mm", f4(max(best)), "chain-0826/per-seed-queue.csv", "largest_square_mm_min_step, max over delivered seeds")
            put(tag, "seeds_square_at_least_source_mm", sum(b >= source_mm for b in best), "chain-0826/per-seed-queue.csv", "largest_square_mm_min_step >= the fourth wave's source threshold")
            put(tag, "seeds_square_at_least_20mm", sum(b >= 20.0 for b in best), "chain-0826/per-seed-queue.csv", "largest_square_mm_min_step >= 20")
        else:
            for k in ("best_square_median_mm", "best_square_max_mm"):
                put(tag, k, "not measurable", "chain-0826/per-seed-queue.csv", "no delivered seed")
            for k in ("seeds_square_at_least_source_mm", "seeds_square_at_least_20mm"):
                put(tag, k, 0, "chain-0826/per-seed-queue.csv", "no delivered seed, so none")
        # a2 over the delivered seeds of the scope
        sheets = [s for r in deliv for s in a2.get(r["attempt"], [])]
        missing = [r["attempt"] for r in deliv if r["attempt"] not in a2]
        put(tag, "a2_seeds_missing", len(missing), "chain-0826/a2-cluster/<seed>.csv", "delivered seeds with no a2 file")
        meas = sum(int(s["a2_measurable"]) for s in sheets)
        flag = sum(int(s["a2_flagged"]) for s in sheets)
        put(tag, "a2_sheets", len(sheets), "chain-0826/a2-cluster/<seed>.csv", "rows")
        put(tag, "a2_flagged_share", ("%.6f" % (flag / meas)) if meas else "not measurable",
            "chain-0826/a2-cluster/<seed>.csv", "sum a2_flagged over sum a2_measurable")
        crule = []
        for r in deliv:
            rows = a2.get(r["attempt"], [])
            vals = [float(s["a2_cluster_rule_square_mm"]) for s in rows
                    if re.fullmatch(r"[0-9.]+", s["a2_cluster_rule_square_mm"])]
            if vals:
                crule.append(max(vals))
        if crule:
            put(tag, "cluster_rule_best_median_mm", f4(statistics.median(crule)), "chain-0826/a2-cluster/<seed>.csv", "a2_cluster_rule_square_mm, largest per seed, median over seeds",
                "seeds with a cluster rule square", "%d of %d" % (len(crule), len(deliv)))
            put(tag, "cluster_rule_best_max_mm", f4(max(crule)), "chain-0826/a2-cluster/<seed>.csv", "a2_cluster_rule_square_mm, largest per seed, max over seeds")
            put(tag, "seeds_cluster_rule_at_least_source_mm", sum(c >= source_mm for c in crule), "chain-0826/a2-cluster/<seed>.csv", "largest a2_cluster_rule_square_mm >= the source threshold")
        if not crule:
            put(tag, "cluster_rule_best_median_mm", "not measurable", "chain-0826/a2-cluster/<seed>.csv", "no delivered seed")
            put(tag, "cluster_rule_best_max_mm", "not measurable", "chain-0826/a2-cluster/<seed>.csv", "no delivered seed")
            put(tag, "seeds_cluster_rule_at_least_source_mm", 0, "chain-0826/a2-cluster/<seed>.csv", "no delivered seed, so none")
        sheets20 = [s for s in sheets if re.fullmatch(r"[0-9.]+", s["delivered_square_mm"]) and float(s["delivered_square_mm"]) >= 20.0]
        both20 = [s for s in sheets20 if re.fullmatch(r"[0-9.]+", s["a2_cluster_rule_square_mm"]) and float(s["a2_cluster_rule_square_mm"]) >= 20.0]
        put(tag, "sheets_delivered_at_least_20mm", len(sheets20), "chain-0826/a2-cluster/<seed>.csv", "delivered_square_mm >= 20")
        put(tag, "sheets_both_at_least_20mm", len(both20), "chain-0826/a2-cluster/<seed>.csv", "delivered_square_mm and a2_cluster_rule_square_mm both >= 20")

    for wtag, f5 in (("wave5", "wave5-near-draw.csv"),):
        p5 = os.path.join(C, f5)
        if os.path.exists(p5):
            n5 = rd(p5)
            h5 = open(p5).readline()
            m5 = re.search(r"at (\d+) to (\d+) voxels", h5)
            put(wtag, "near_sources", len(n5), "chain-0826/" + f5, "rows")
            put(wtag, "near_draws_made", sum(int(r["draws_made"]) for r in n5), "chain-0826/" + f5, "sum of draws_made")
            put(wtag, "near_draws_per_source_max", max(int(r["drawn"]) for r in n5), "chain-0826/" + f5, "max of drawn")
            put(wtag, "near_shell_min_vox", m5.group(1) if m5 else "not measurable", "chain-0826/" + f5, "header")
            put(wtag, "near_shell_max_vox", m5.group(2) if m5 else "not measurable", "chain-0826/" + f5, "header")
            src5 = rd(os.path.join(C, "wave5-sources.csv"))
            hs = open(os.path.join(C, "wave5-sources.csv")).readline()
            m6 = re.search(r"best >= ([0-9.]+) mm", hs)
            put(wtag, "source_threshold_mm", m6.group(1) if m6 else "not measurable", "chain-0826/wave5-sources.csv", "header")
    near = rd(os.path.join(C, "wave4-near-draw.csv"))
    nh = open(os.path.join(C, "wave4-near-draw.csv")).readline()
    m = re.search(r"at (\d+) to (\d+) voxels", nh)
    if not m:
        sys.exit("chain_summary.py: wave4-near-draw.csv header states no shell")
    put("wave4", "near_sources", len(near), "chain-0826/wave4-near-draw.csv", "rows",
        "sources equal wave4-sources.csv rows with is_source yes",
        "yes" if len(near) == sum(r["is_source"] == "yes" for r in rd(os.path.join(C, "wave4-sources.csv"))) else "no")
    put("wave4", "near_draws_made", sum(int(r["draws_made"]) for r in near), "chain-0826/wave4-near-draw.csv", "sum of draws_made")
    put("wave4", "near_draws_per_source_max", max(int(r["drawn"]) for r in near), "chain-0826/wave4-near-draw.csv", "max of drawn")
    put("wave4", "near_shell_min_vox", m.group(1), "chain-0826/wave4-near-draw.csv", "header: at X to Y voxels")
    put("wave4", "near_shell_max_vox", m.group(2), "chain-0826/wave4-near-draw.csv", "header: at X to Y voxels")
    bo = rd(os.path.join(C, "build-objects-check.csv"))
    oo = [r for r in bo if r["build_mode"] == "objects_only"]
    put("build", "objects_check_builds", len(bo), "chain-0826/build-objects-check.csv", "rows")
    put("build", "objects_only_builds", len(oo), "chain-0826/build-objects-check.csv", "build_mode = objects_only",
        "objects only builds whose sha256 equals a full make of the same seed", "%d of %d" % (sum(r["equal"] == "yes" for r in oo), len(oo)))
    put("build", "objects_check_variants", len({r["variant"] for r in bo}), "chain-0826/build-objects-check.csv", "distinct variant")
    put("rule", "a2_T_star_deg", tstar.pop(), "chain-0826/a2-cluster/<seed>.csv", "a2_T_star")
    put("rule", "a2_S", sclus.pop(), "chain-0826/a2-cluster/<seed>.csv", "a2_S")
    put("rule", "source_threshold_mm", "%.1f" % source_mm, "chain-0826/wave4-sources.csv", "header: best >= X mm")
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/chain_summary.py at %s from the snapshot of chain-0826 in '
                 'src/evidence/studies (copy time in src/evidence/MANIFEST.csv); waves 1 to 4 are the '
                 'groups %s"\n' % (now, " ".join(WAVES)))
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    bad = [r for r in out if r["check_value"] and not (r["check_value"] == "yes" or re.fullmatch(r"(\d+) of \1", r["check_value"]))]
    for r in bad:
        print("  !! %s %s: %s" % (r["scope"], r["check"], r["check_value"]))
    print("chain_summary.py: %d rows to %s, %d check(s) not holding" % (len(out), a.out, len(bad)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
