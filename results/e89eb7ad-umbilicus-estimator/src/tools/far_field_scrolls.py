# This file is a copy of tools/far_field_scrolls.py of the working tree. Nothing is changed in it:
# it reads and writes evidence/ through rev1_lib and carries no path of the machine.
"""Equation (1) against the runs with the scroll as the unit, not the slice.

Two independent model reviews of the 9 page paper, 2026-09-18, made the same objection to the
pooled Fisher test of Table I: the 360 slices are not 360 independent observations. They are 24
slices from each of 15 scrolls, and slices of one scroll share the same geometry, the same
prediction, the same scanning artefacts and the same annotator, so a test that treats them as
independent inflates its own p value. The objection is right and the pooled test is dropped rather
than kept as a second opinion.

What replaces it needs no pooling and no distributional assumption.

1. The per scroll table. For each scroll: how many of its slices satisfy the condition, how many
   of its runs leave the grid, and how many of those leaving runs the condition failed to flag.
   The claim of Section II is that the last number is zero, and it is reported scroll by scroll so
   that a reader can see it is not carried by one scroll.

2. A permutation test that conditions on each scroll. The predictor is shuffled among the slices
   OF ONE SCROLL, independently in each scroll, which keeps every scroll's own counts fixed: the
   number of slices that satisfy the condition and the number whose run left the grid are the same
   in every shuffle as in the data. Only the pairing between them is broken, which is exactly the
   null being tested, and nothing is assumed about how scrolls differ from each other.

   The statistic is the number of leaving runs that the condition flags. Under that null the count
   of one scroll is hypergeometric, so the exact p value is available in closed form when the
   observed count is the largest the shuffling can produce, which it is here: with no misses, every
   leaving run already sits in a flagged slice, and a shuffle can only do as well or worse. The
   exact p is then the probability that every scroll's leaving runs land, by chance, inside its own
   flagged slices, prod_i C(k_i, r_i) / C(n_i, r_i). The simulation is run as well, at the number
   of rounds the reviewer used, and reported beside it: a simulation can only report its own
   resolution floor, and the exact value is what the paper quotes.

Input: evidence/far-field-slices.csv, written by far_field_eigenvalue.py --slices.
Nothing is recomputed from the grids here.
Outputs: evidence/far-field-per-scroll.csv and far-field-permutation.csv.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L  # noqa: E402

ROUNDS = 200_000
SEED = 20260918
PRED, OUT = "predicts_runaway", "outside_majority"


def main():
    # an alternative input, for checking the formula on a file that is not the one of record;
    # nothing is written in that case
    src = sys.argv[sys.argv.index("--input") + 1] if "--input" in sys.argv else \
        os.path.join(L.EV, "far-field-slices.csv")
    rows = L.read_csv(src)
    scrolls, per = [], []
    for s in dict.fromkeys(r["scroll"] for r in rows):
        rr = [q for q in rows if q["scroll"] == s]
        n = len(rr)
        k = sum(int(q[PRED]) for q in rr)                       # slices the condition flags
        r = sum(int(q[OUT]) for q in rr)                        # runs that left the grid
        tp = sum(int(q[PRED]) and int(q[OUT]) for q in rr)
        miss = r - tp
        # the chance that this scroll's r leaving runs all land in its k flagged slices
        p_scroll = math.comb(k, r) / math.comb(n, r) if r <= k else 0.0
        per.append(dict(scroll=s, slices=n, flagged=k, left_the_grid=r, flagged_and_left=tp,
                        missed=miss, all_flagged=int(miss == 0),
                        p_scroll=f"{p_scroll:.4g}" if r else "1 (no run left)"))
        scrolls.append((n, k, r, tp))
        print(f"  {s:12s} slices {n:3d}  flagged {k:3d}  left {r:3d}  flagged and left {tp:3d}  "
              f"missed {miss}", flush=True)

    n_scrolls = len(per)
    zero_miss = sum(q["all_flagged"] for q in per)
    with_runaway = sum(1 for q in per if q["left_the_grid"])
    all_flagged_among_those = sum(1 for q in per if q["left_the_grid"] and not q["missed"])
    observed = sum(t for _, _, _, t in scrolls)
    upper = sum(min(k, r) for _, k, r, _ in scrolls)

    # Exact: P(T >= observed) under the within scroll null, where T is a sum over scrolls of
    # independent hypergeometric counts (how many of a scroll's r leaving runs land in its k
    # flagged slices when the predictor is shuffled among its n). The distribution of the sum is
    # the convolution of the fifteen pmfs, each on 0..min(k, r), so the tail is exact and cheap.
    # When the observed count is the largest reachable this reduces to the product of the
    # per scroll probabilities, which is the formula this tool used until 2026-09-18 13:03 UTC;
    # that formula is P(T = max) and understates the tail as soon as one scroll has a miss, which
    # the shipped walk produced on one slice. Checked: on the transcription's file, where
    # observed equals the maximum, the convolution returns the product to the digit.
    dist = {0: 1.0}
    for n, k, r, _ in scrolls:
        if not r:
            continue
        pmf = {t: math.comb(k, t) * math.comb(n - k, r - t) / math.comb(n, r)
               for t in range(max(0, r - (n - k)), min(k, r) + 1)}
        nxt = {}
        for a, pa in dist.items():
            for t, pt in pmf.items():
                nxt[a + t] = nxt.get(a + t, 0.0) + pa * pt
        dist = nxt
    exact = sum(pv for t, pv in dist.items() if t >= observed)

    # the same test by simulation, at the reviewer's number of rounds
    rng = np.random.default_rng(SEED)
    hits = 0
    for _ in range(ROUNDS):
        tot = 0
        for n, k, r, _ in scrolls:
            if r:
                tot += int(rng.permutation(n)[:k].__lt__(r).sum()) if False else \
                       int(np.count_nonzero(rng.choice(n, k, replace=False) < r))
        if tot >= observed:
            hits += 1
    sim_p = (hits + 1) / (ROUNDS + 1)

    print(f"\n  scrolls {n_scrolls}, zero misses in {zero_miss} of them; "
          f"{with_runaway} have a run that left, and in {all_flagged_among_those} of those every "
          f"leaving run was flagged")
    print(f"  observed flagged-and-left {observed}, the largest the shuffling can reach {upper}"
          + ("" if observed == upper else f": {upper - observed} short of it, so the exact p is the"
             " tail P(T >= observed) and not the product"))
    print(f"  exact permutation p {exact:.3g}")
    print(f"  simulation: {hits} of {ROUNDS:,} shuffles reached it, p <= {sim_p:.1e} (seed {SEED})")

    if "--input" in sys.argv:
        print("  (--input given: nothing written)")
        return
    L.write_csv(os.path.join(L.EV, "far-field-per-scroll.csv"), list(per[0]), per)
    L.write_csv(os.path.join(L.EV, "far-field-permutation.csv"),
                ["test", "unit", "scrolls", "slices", "scrolls_zero_misses",
                 "scrolls_with_a_leaving_run", "scrolls_all_leaving_runs_flagged",
                 "observed_flagged_and_left", "max_reachable_by_shuffling", "exact_p",
                 "sim_rounds", "sim_hits", "sim_p_upper_bound", "sim_seed", "note"],
                [dict(test="within-scroll permutation of the predictor", unit="scroll",
                      scrolls=n_scrolls, slices=len(rows), scrolls_zero_misses=zero_miss,
                      scrolls_with_a_leaving_run=with_runaway,
                      scrolls_all_leaving_runs_flagged=all_flagged_among_those,
                      observed_flagged_and_left=observed, max_reachable_by_shuffling=upper,
                      exact_p=f"{exact:.3g}", sim_rounds=ROUNDS, sim_hits=hits,
                      sim_p_upper_bound=f"{sim_p:.1e}", sim_seed=SEED,
                      note="each scroll's own counts are held fixed; the pooled Fisher test of "
                           "far-field-prediction.csv is not used, the slices being nested in scrolls")])


if __name__ == "__main__":
    main()
