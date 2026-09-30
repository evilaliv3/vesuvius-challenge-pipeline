#!/usr/bin/env python3
"""How much the three factors of evidence/a8-factor.csv move when the bench rows that had a
throttle relaunch in their window are dropped.

This does not replace a8-factor.csv. It answers one question: is any of the three factors
carried by a run the leftover throttle was sitting on. It recomputes each ratio twice, once
over every finished run of the arm and once over the finished runs that
evidence/throttle-overlap.csv marks `no`, and prints both with the run counts, so a factor
that rests on a single surviving run is visible as such.

Medians, as in a8-factor.csv: with two runs a median is their mean, and that is stated in the
row rather than hidden.

Writes evidence/a8-factor-sensitivity.csv.
"""
import csv, os, statistics

Q = "/data/scrollagent/runs/rev1/quiet-bench"
RUNS = os.path.join(Q, "evidence", "c-stage-runs.csv")
OVER = os.path.join(Q, "evidence", "throttle-overlap.csv")
OUT = os.path.join(Q, "evidence", "a8-factor-sensitivity.csv")
SEED = "PHerc1447-seed26"
RATIOS = [("A8's four changes", "noA8", "plain"),
          ("corrections 00008 and 00009", "plain", "c2"),
          ("all six changes together", "noA8", "c2")]


def read_after_comment(path):
    with open(path) as fh:
        lines = fh.readlines()
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith(('"#', '#')):
        i += 1
    return list(csv.DictReader(lines[i:]))


def main():
    over = {(r["tag"], r["attempt"], r["started_utc"]): r["throttle_relaunch_in_window"]
            for r in read_after_comment(OVER)}
    arms = {}
    for r in read_after_comment(RUNS):
        if r["attempt"] != SEED or r["return_code"] != "0" or r["cap_bit"] == "yes":
            continue
        touched = over.get((r["tag"], r["attempt"], r["started_utc"]), "unknown")
        arms.setdefault(r["tag"], []).append((float(r["seconds"]), touched))

    def med(arm, clean_only):
        v = [s for s, t in arms.get(arm, []) if not (clean_only and t.startswith("yes"))]
        return (statistics.median(v), len(v), v) if v else (None, 0, [])

    rows = []
    for name, num, den in RATIOS:
        n_all, nn, nv = med(num, False)
        d_all, dn, dv = med(den, False)
        n_cl, ncn, ncv = med(num, True)
        d_cl, dcn, dcv = med(den, True)
        rows.append({
            "ratio": name,
            "numerator_arm": num,
            "denominator_arm": den,
            "factor_over_every_finished_run": "%.2f" % (n_all / d_all),
            "numerator_runs_all": nn,
            "denominator_runs_all": dn,
            "factor_over_the_runs_no_relaunch_touched": ("%.2f" % (n_cl / d_cl))
                if n_cl and d_cl else "not computable, an arm has no untouched run",
            "numerator_runs_untouched": ncn,
            "denominator_runs_untouched": dcn,
            "numerator_seconds_untouched": "; ".join("%.1f" % x for x in sorted(ncv)) or "none",
            "denominator_seconds_untouched": "; ".join("%.1f" % x for x in sorted(dcv)) or "none",
            "how_much_the_factor_moves": ("%.2f" % (n_cl / d_cl - n_all / d_all))
                if n_cl and d_cl else "not computable",
        })
    with open(OUT, "w", newline="") as fh:
        fh.write('"# how the three factors of evidence/a8-factor.csv move when the runs that '
                 'evidence/throttle-overlap.csv marks yes are dropped, on %s only, written by '
                 'tools/factor_sensitivity.py. A column with two runs has a median that is '
                 'their mean. A column with one run has no spread and the run count says so. '
                 'This file adds no claim: it says how far each factor travels when the '
                 'disturbed rows are removed, and the reader compares that distance with the '
                 'spread in c-stage-summary.csv."\n' % SEED)
        w = csv.writer(fh)
        w.writerow(list(rows[0].keys()))
        for r in rows:
            w.writerow(list(r.values()))
    print("wrote", OUT)
    for r in rows:
        print("  %-28s all %s runs -> %s   untouched (%s/%s runs) -> %s   moves %s"
              % (r["ratio"], r["numerator_runs_all"] + r["denominator_runs_all"],
                 r["factor_over_every_finished_run"], r["numerator_runs_untouched"],
                 r["denominator_runs_untouched"],
                 r["factor_over_the_runs_no_relaunch_touched"], r["how_much_the_factor_moves"]))


if __name__ == "__main__":
    main()
