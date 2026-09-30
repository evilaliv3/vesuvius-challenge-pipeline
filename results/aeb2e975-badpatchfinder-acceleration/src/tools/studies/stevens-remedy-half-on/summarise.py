#!/usr/bin/env python3
"""stevens-remedy-half-on: evidence/per-seed.csv (one row per seed of evidence/ten-seeds.csv, plus a BAR row) and
evidence/per-sheet-arm-on.csv (the per seed a2_after.py files gathered). Every value read back from the run's rerun.csv
and the per sheet CSVs; a seed without them is 'not measurable' with the reason, never zero."""
import csv, glob, os, subprocess

ST = "/data/scrollagent/runs/rev1/stevens-remedy-half-on"
EV = ST + "/evidence"
NM = "not measurable"


def rows(p):
    return list(csv.DictReader(l for l in open(p, newline="") if not l.lstrip('"').startswith("#")))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def best(vals):
    v = [x for x in map(fnum, vals) if x is not None]
    return ("%.4f" % max(v)) if v else NM


def main():
    ten = [r["attempt"] for r in rows(EV + "/ten-seeds.csv")]
    out, sheets = [], []
    for a in ten:
        d = ST + "/scratch/arm-on/" + a
        r = {"seed": a}
        rc = {}
        if os.path.exists(d + "/rerun.csv"):
            rc = {x["quantity"]: x["value"] for x in rows(d + "/rerun.csv")}
        ps = EV + "/per-sheet-arm-on-%s.csv" % a
        if rc.get("downstream_return_code") != "0" or not os.path.exists(ps):
            why = ("downstream rc %s" % rc["downstream_return_code"]) if "downstream_return_code" in rc else \
                ("run not finished" if os.path.isdir(d) else "not run")
            if rc.get("downstream_return_code") == "0":
                why = "per sheet file absent"
            r.update(status="%s (%s)" % (NM, why))
            out.append(r); continue
        S = rows(ps); sheets += S
        r.update(status="measured",
                 sheets_delivered=sum(s["in_delivered"] == "yes" for s in S),
                 sheets_arm=sum(s["in_arm"] == "yes" for s in S),
                 sheets_byte_equal=sum(s["sheet_bytes_equal_delivered"] == "yes" for s in S))
        r["sheets_changed"] = len(S) - r["sheets_byte_equal"]
        r["delivered_sheets_changed"] = "yes" if r["sheets_changed"] > 0 else "no"
        r["badpatches_stage_c"] = rc.get("badpatches_csv_lines", NM)
        r["bridges_in_badbridges_csv"] = rc.get("bridges_in_badbridges_csv", NM)
        r["anneal_excluded_patches"] = rc.get("anneal_excluded_patches", NM)
        r["best_square_mm_before"] = best(s["square_mm_before"] for s in S)
        r["best_square_mm_after"] = best(s["square_mm_after"] for s in S)
        for k in ("cluster_rule_square_mm",):
            r["a2_best_%s_before" % k] = best(s["a2_%s_before" % k] for s in S)
            r["a2_best_%s_after" % k] = best(s["a2_%s_after" % k] for s in S)
        for k in ("kept_points",):
            for w in ("before", "after"):
                v = [fnum(s["a2_%s_%s" % (k, w)]) for s in S]
                r["a2_%s_sum_%s" % (k, w)] = ("%d" % sum(x for x in v if x is not None)) if any(x is not None for x in v) else NM
        for w in ("before", "after"):
            v = [fnum(s["a2_largest_cluster_%s" % w]) for s in S]
            v = [x for x in v if x is not None]
            r["a2_largest_cluster_%s" % w] = ("%d" % max(v)) if v else NM
        r["nm_seconds"] = rc.get("downstream_stage_nm_10_1000_seconds", NM)
        r["downstream_seconds"] = rc.get("downstream_wall_clock_seconds", NM)
        r["bytes_kept"] = rc.get("bytes_kept_after_prune", NM)
        out.append(r)
    cols = ["seed", "status", "sheets_delivered", "sheets_arm", "sheets_byte_equal", "sheets_changed",
            "delivered_sheets_changed", "badpatches_stage_c", "bridges_in_badbridges_csv", "anneal_excluded_patches",
            "best_square_mm_before", "best_square_mm_after", "a2_best_cluster_rule_square_mm_before",
            "a2_best_cluster_rule_square_mm_after", "a2_kept_points_sum_before", "a2_kept_points_sum_after",
            "a2_largest_cluster_before", "a2_largest_cluster_after", "nm_seconds", "downstream_seconds", "bytes_kept"]
    meas = [r for r in out if r["status"] == "measured"]
    changed = [r for r in meas if r["delivered_sheets_changed"] == "yes"]
    if changed:
        bar = "met: the remedy fully on changes the delivered sheets on %d of %d measured seeds" % (len(changed), len(meas))
    elif len(meas) == len(ten):
        bar = "not met: no delivered sheet changed on any of the ten seeds; the claim is closed as not reproduced"
    else:
        bar = "%s: %d of %d seeds measured, none changed" % (NM, len(meas), len(ten))
    t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(EV + "/per-seed.csv", "w", newline="") as fh:
        fh.write("# written by stevens-remedy-half-on/tools/summarise.py at %s: one row per seed of ten-seeds.csv, arm-on "
                 "(c, l, vm 10, bridges, nm 10 1000, manualBadPatch, vm 10, hm 10, fm 30 10, delivered binary) against "
                 "the delivery; best_* = the largest over the seed's sheets; a2 at T* 25, cluster rule S 101. Bar "
                 "(DECLARATION.md): the remedy fully on changes the delivered sheets on at least one seed of ten. "
                 "One annealing run per seed is one random draw (anneal.cpp:675).\n" % t)
        w = csv.DictWriter(fh, cols, restval="", lineterminator="\n")
        w.writeheader(); w.writerows(out)
        w.writerow({"seed": "BAR", "status": bar})
    if sheets:
        with open(EV + "/per-sheet-arm-on.csv", "w", newline="") as fh:
            fh.write("# written by stevens-remedy-half-on/tools/summarise.py at %s: the per-sheet-arm-on-<seed>.csv "
                     "files of tools/a2_after.py gathered, in ten-seeds.csv order\n" % t)
            w = csv.DictWriter(fh, list(sheets[0].keys()), lineterminator="\n")
            w.writeheader(); w.writerows(sheets)
    print(bar)


main()
