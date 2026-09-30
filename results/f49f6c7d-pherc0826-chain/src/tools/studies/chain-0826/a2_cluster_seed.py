#!/usr/bin/env python3
# chain-0826 copy of seeds-at-scale-1447/tools/a2_cluster_seed.py, written 2026-09-26 by a coordinator agent (DECLARATION.md part 2):
# paths and names moved to chain-0826 and PHerc0826 (study root, prediction, raw volume, draw and queue file names, ledger
# slugs chain-0826-deliver-*); every other change is listed below this line; the text after the list is the original's.
#   A. MC.SCROLL is PHerc0826 for a seed of this study; --reference reads a 1447 seed of the 55 from seeds-at-scale-1447 with
#      MC.SCROLL PHerc1447, string for string against map-1447 as before.
"""a2_cluster_seed.py <seed> [--out <csv>]: item 74's arm a2 with the cluster rule, one row per delivered sheet of one seed,
beside the delivered square (DECLARATION.md addition of 2026-09-25T19:13:31Z). Default output
evidence/a2-cluster/<seed>.csv; its first line names this tool.

Inputs, read and never written:
  - the sheets as measure_seed_v3.sh links them: out/<seed>/sheets/patches/patch_<n>.bin; the delivered square and the
    sheet's sha256 from evidence/squares-<seed>.csv (square_mm_min_step, sha256; map_crossing.squares_rows, a missing
    column raises). A sheet whose bytes differ from its squares row is «not measurable (sheet changed since the squares
    row)»; a squares row whose status is not measured gets «not measurable (square status <status>)».
  - T* from lamina-crossing-detect/evidence/verdict.csv, arm a2_pred item RULE (map_crossing.verdict_row, which refuses
    unless the row passes); S from lamina-crossing-map-1447/evidence/cluster-calibration.csv, a2 RULE
    (cluster_rule.read_S). Read, never typed.
  - the measurement: stevens-remedy-half-on/tools/a2_after.py's a2_measure, imported unchanged (stride 8 points, a2
    angle above T*, four neighbour clusters on the stride grid, holes only around clusters of more than S points,
    taxicab 2, square.py largest_square, mm by the smaller median step times the manifest voxel).
The only reading of a low share: «no steep crossing (above 25 degrees against the surface prediction, 33 against the raw
scan) at the rate of ink labelled segments». A cluster rule square is not a bound on crossing.

--reference <seed of the 55>: runs the same code on that seed and compares every sheet, string for string, with
lamina-crossing-map-1447's map-1447.csv (a2_measurable, a2_flagged, a2_flagged_share) and map-1447-cluster-rule.csv
(a2_largest_cluster, a2_kept_points, a2_cluster_rule_square_mm); writes evidence/a2-cluster-reference.csv and exits 1 on
any difference.
"""
import csv, hashlib, os, subprocess, sys, time

R1 = "/data/scrollagent/runs/rev1"
S_DIR = R1 + "/chain-0826"
S_1447 = R1 + "/seeds-at-scale-1447"   # chain-0826 A: the --reference seed lives there
sys.path.insert(0, R1 + "/lamina-crossing-map-1447/tools")
sys.path.insert(0, R1 + "/stevens-remedy-half-on/tools")
import map_crossing as MC  # noqa: E402
import cluster_rule as CRL  # noqa: E402
import a2_after as A2  # noqa: E402


def use_scroll(scroll, study):
    """chain-0826 A: the scroll whose prediction a2_measure reads and the study whose squares and sheets are read."""
    global S_DIR
    MC.SCROLL = scroll
    MC.SAS = study
    S_DIR = study


use_scroll("PHerc0826", R1 + "/chain-0826")

TOOL = "chain-0826/tools/a2_cluster_seed.py"
NM = MC.NM
MAPD = R1 + "/lamina-crossing-map-1447/evidence"
COLS = ["seed", "sheet", "file", "sha256", "sha256_match_squares_row", "delivered_square_status",
        "delivered_square_mm", "a2_T_star", "a2_S", "a2_measurable", "a2_flagged", "a2_flagged_share",
        "a2_largest_cluster", "a2_kept_points", "a2_cluster_rule_square_mm", "seconds"]
KEYS = ["measurable", "flagged", "flagged_share", "largest_cluster", "kept_points", "cluster_rule_square_mm"]


def utc():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()


def measure_seed(seed):
    MC.D.selftest_passed(); MC.selftest_ok()
    T, _ = MC.verdict_row("a2")
    S, _ = CRL.read_S(); S = S["a2"]
    sq = MC.squares_rows(seed)
    if not sq:
        raise SystemExit("no squares row for %s" % seed)
    rows = []
    for n in sorted(sq):
        r = sq[n]
        p = "%s/out/%s/sheets/patches/patch_%d.bin" % (S_DIR, seed, n)
        row = {"seed": seed, "sheet": n, "file": os.path.basename(p), "a2_T_star": T, "a2_S": S,
               "delivered_square_status": MC.req(r, "status"), "delivered_square_mm": MC.req(r, "square_mm_min_step")}
        if not os.path.exists(p):
            raise SystemExit("%s: sheet file %s absent" % (seed, p))
        h = A2.sha(p)
        row["sha256"] = h
        row["sha256_match_squares_row"] = "yes" if h == MC.req(r, "sha256") else "no"
        t0 = time.time()
        if row["sha256_match_squares_row"] != "yes":
            a = {k: "not measurable (sheet changed since the squares row)" for k in KEYS}
        elif row["delivered_square_status"] != "measured":
            a = {k: "not measurable (square status %s)" % row["delivered_square_status"] for k in KEYS}
        else:
            a = A2.a2_measure(p, T, S)
        for k in KEYS:
            row["a2_" + k] = a[k]
        row["seconds"] = "%.1f" % (time.time() - t0)
        rows.append(row)
        print("%s S%d: flagged share %s, cluster rule square %s beside delivered %s (%s s)"
              % (seed, n, row["a2_flagged_share"], row["a2_cluster_rule_square_mm"], row["delivered_square_mm"],
                 row["seconds"]), flush=True)
    return rows, T, S


def write(out, rows, T, S, what):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out + ".part", "w", newline="") as fh:
        fh.write("# written by %s at %s: %s; a2 at T* %g (lamina-crossing-detect verdict.csv a2_pred RULE), cluster rule "
                 "S %d (lamina-crossing-map-1447 cluster-calibration.csv a2 RULE), stride %d, taxicab %d; measured by "
                 "stevens-remedy-half-on/tools/a2_after.py a2_measure, imported unchanged; delivered_square_mm is "
                 "square_mm_min_step of evidence/squares-<seed>.csv. The only reading of a low share: %s. A cluster rule "
                 "square is not a bound on crossing.\n" % (TOOL, utc(), what, T, S, MC.STRIDE, MC.K, MC.PHRASE))
        w = csv.DictWriter(fh, COLS, lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    os.replace(out + ".part", out)


def reference(seed):
    use_scroll("PHerc1447", S_1447)
    rows, T, S = measure_seed(seed)
    M = {int(r["sheet"]): r for r in MC.read_csv(MAPD + "/map-1447.csv") if r["seed"] == seed}
    C = {int(r["sheet"]): r for r in MC.read_csv(MAPD + "/map-1447-cluster-rule.csv") if r["seed"] == seed}
    if not M or set(M) != set(C) or set(M) != {r["sheet"] for r in rows}:
        raise SystemExit("%s: sheets of map-1447.csv %s, cluster rule %s, measured %s differ"
                         % (seed, sorted(M), sorted(C), [r["sheet"] for r in rows]))
    out = []
    for r in rows:
        n = r["sheet"]
        ref = {"measurable": M[n]["a2_measurable"], "flagged": M[n]["a2_flagged"],
               "flagged_share": M[n]["a2_flagged_share"], "largest_cluster": C[n]["a2_largest_cluster"],
               "kept_points": C[n]["a2_kept_points"], "cluster_rule_square_mm": C[n]["a2_cluster_rule_square_mm"],
               "delivered_square_mm": M[n]["delivered_square_mm"]}
        for k, v in ref.items():
            got = r["delivered_square_mm"] if k == "delivered_square_mm" else r["a2_" + k]
            out.append([seed, n, k, got, v, "yes" if str(got) == str(v) else "no"])
    p = R1 + "/chain-0826/evidence/a2-cluster-reference.csv"
    with open(p + ".part", "w", newline="") as fh:
        fh.write("# written by %s --reference %s at %s: every sheet of a seed of the 55, this tool against "
                 "lamina-crossing-map-1447 map-1447.csv and map-1447-cluster-rule.csv, string for string\n" % (TOOL, seed, utc()))
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["seed", "sheet", "quantity", "this_tool", "map_1447", "equal"])
        w.writerows(out)
    os.replace(p + ".part", p)
    bad = [x for x in out if x[5] != "yes"]
    print("reference %s: %d comparisons, %d equal" % (seed, len(out), len(out) - len(bad)))
    sys.exit(1 if bad else 0)


def main():
    if sys.argv[1] == "--reference":
        reference(sys.argv[2]); return
    seed = sys.argv[1]
    out = S_DIR + "/evidence/a2-cluster/%s.csv" % seed
    if len(sys.argv) > 3 and sys.argv[2] == "--out":
        out = sys.argv[3]
    rows, T, S = measure_seed(seed)
    write(out, rows, T, S, "one row per delivered sheet of %s" % seed)
    print("written %s: %d sheets" % (out, len(rows)))


if __name__ == "__main__":
    main()
