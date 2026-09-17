# This file is a copy of tools/bench_rules.py of the working tree and differs from it in one
# way only: the bench whose committed results are the known reference is the frozen copy
# archived in this folder at umbilicus-bench/, found there with nothing set, and the run that
# scored the rules still lives outside and is named by UMBILICUS_BASELINE_RUN; the `source`
# column names that run the way this folder names it. Nothing else is changed.
"""The seven rules of the umbilicus bench on the bench's own slices, brought into the evidence.

This does not measure anything new. The measurement is the run of 2026-09-18 named by
UMBILICUS_BASELINE_RUN, which added the two villa rows (as published, and with the division
removed) to the bench harness and scored them beside the bench's five mask rules and its negative
control, on the bench's 46 heights at pyramid level 3, with the bench's own distance function and
the same published control points. This tool reads that run's rows.csv, checks it, and writes
evidence/bench-rules.csv so that the two sentences the paper spends on it expand macros
from an evidence file like every other number.

The checks are the reason this file exists rather than a copy:

  1. known reference. The six rows the bench already publishes (five mask rules and the control)
     must equal results/bench.json of the frozen bench in umbilicus-bench/ cell for cell. If the
     bench moves, this fails rather than printing a stale figure.
  2. arithmetic. Every stochastic row must carry 46 heights times 20 seeds, and no count of
     estimates outside the grid may exceed that. The two denominators the paper prints, 920 per
     scroll and variant and 3680 over the four scrolls, are computed here and not typed.
  3. shape. Four scrolls, eight rows each.

This sample is NOT the sample of Section V. 46 heights fixed by the store against 24 fixed by the
extent of the reference, level 3 of the surface prediction against the resolution of the normal
grid. The same centroid code gives 3.12 mm here and 3.51 mm there on PHerc0826. The two are never
pooled and no row of this file belongs in a table with a row of fifteen-k20.csv.

Output: evidence/bench-rules.csv.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L  # noqa: E402

RUN = os.environ.get("UMBILICUS_BASELINE_RUN") or os.path.join(L.SRC, "umbilicus-baseline")
BENCH = L.BENCH
SEEDS = 20
HEIGHTS = 46
# The bench's own rows, under the names results/bench.json gives them, and the two rows the run
# added. The order is the order the bench prints.
BENCH_ROWS = ("argmax", "centroid", "plateau_centroid", "plateau_nearest_centroid",
              "argmax + hampel", "fake axis (control)")
ADDED_ROWS = ("villa as published", "villa no division")
COLS = ["scroll", "rule", "input", "stochastic", "seeds", "heights", "level", "control_points",
        "median_mm", "iqr_mm", "p90_mm", "worst_mm", "estimates", "outside", "capped", "source"]
# What each row reads. The five mask rules and the control take a section of the surface
# prediction; the two villa rows take the normal grid at the same heights.
INPUT = {r: "mask" for r in BENCH_ROWS}
INPUT["fake axis (control)"] = "none"
INPUT.update({r: "normal grid" for r in ADDED_ROWS})


def main():
    rows_in = L.read_csv(os.path.join(RUN, "rows.csv"))
    by = {}
    for r in rows_in:
        by.setdefault(r["scroll"], {})[r["rule"]] = r
    scrolls = list(by)
    bad = []

    # ---- shape
    if len(scrolls) != 4:
        bad.append(f"four scrolls expected, {len(scrolls)} found")
    for s in scrolls:
        missing = [r for r in BENCH_ROWS + ADDED_ROWS if r not in by[s]]
        if missing:
            bad.append(f"{s}: rows missing: {missing}")

    # ---- known reference: the bench's own six rows against its committed results
    ref = json.load(open(os.path.join(BENCH, "results", "bench.json")))
    cells = 0
    for s in scrolls:
        if s not in ref:
            bad.append(f"{s}: not in results/bench.json")
            continue
        for rule in BENCH_ROWS:
            a, b = by[s].get(rule), ref[s]["rows"].get(rule)
            if not a or not b:
                bad.append(f"{s}/{rule}: not in both")
                continue
            for k in ("median_mm", "p90_mm", "worst_mm"):
                cells += 1
                if abs(float(a[k]) - float(b[k])) > 1e-9:
                    bad.append(f"{s}/{rule}/{k}: {a[k]} against {b[k]} in bench.json")
            if int(a["scored_on"]) != int(b["scored_on"]):
                bad.append(f"{s}/{rule}: {a['scored_on']} control points against {b['scored_on']}")

    # ---- arithmetic, and the two denominators the paper prints
    rows, total_estimates, total_outside_fixed = [], 0, 0
    for s in scrolls:
        for rule in BENCH_ROWS + ADDED_ROWS:
            r = by[s].get(rule)
            if not r:
                continue
            stoch = int(r["stochastic"])
            seeds = int(r["seeds"])
            heights = int(r["slices"])
            if stoch:
                if seeds != SEEDS or heights != HEIGHTS:
                    bad.append(f"{s}/{rule}: {heights} heights and {seeds} seeds, {HEIGHTS} and {SEEDS} expected")
                est = heights * seeds
            else:
                est = heights
            if int(r["outside"]) > est or int(r["capped"]) > est:
                bad.append(f"{s}/{rule}: {r['outside']} outside and {r['capped']} capped of {est}")
            if rule == "villa no division":
                total_estimates += est
                total_outside_fixed += int(r["outside"])
            rows.append(dict(scroll=s, rule=rule, input=INPUT[rule], stochastic=stoch, seeds=seeds,
                             heights=heights, level=3, control_points=int(r["scored_on"]),
                             median_mm=float(r["median_mm"]),
                             iqr_mm=r["iqr_mm"], p90_mm=float(r["p90_mm"]),
                             worst_mm=float(r["worst_mm"]), estimates=est,
                             outside=int(r["outside"]), capped=int(r["capped"]),
                             source="umbilicus-bench run of 2026-09-18"))

    print(f"  known reference (the bench's six rows against results/bench.json): "
          f"{'reproduced, ' + str(cells) + ' cells' if not bad else 'NOT'}")
    print(f"  the repaired estimator: {total_outside_fixed} estimates outside the grid of "
          f"{total_estimates} over {len(scrolls)} scrolls")
    if bad:
        for b in bad:
            print("  !!", b)
        raise SystemExit("bench_rules: the run does not check out")
    L.write_csv(os.path.join(L.EV, "bench-rules.csv"), COLS, rows)


if __name__ == "__main__":
    main()
