# This file is a copy of the same probe in the working tree and differs from it in one way
# only: the absolute paths of the machine it ran on
# are resolved inside this folder, from the file's own location (../../tools for the library and
# ../../inputs for the transcribed estimator). Nothing else is changed, and in particular nothing
# the docstring below says about what this file is.
"""POST HOC PROBE. The far field comparison made at the seed point of the refinement.

No number of the paper depends on this file. It was run on 2026-09-17, after the three rounds of
review of `A Far Field Attractor in the Umbilicus Score of Volume Cartographer`, on the same 360 slices
the paper already reports, with no criterion fixed beforehand. That is why its result is quoted in
the pull request text, where a maintainer is entitled to the best answer we have, and not in the
paper, where a number measured after the fact on the same slices would have to be pre-registered
to mean anything. It writes no CSV into evidence/ and feeds no macro.

The question. Section VIII of the paper names, without measuring it, the one comparison the code
could make that is neither blind nor self defeating: the bound of equation (1) against the weighted
mean at the point the search starts from, which is the best of the 1000 random candidates that
cpp:78-88 picks, a point the function already holds before the hill climb moves it. The two
comparisons the paper does measure are the mean at the reference control point, which the code does
not have, and the mean at the refined point, which the walk itself has pushed up to the bound.

The seed point is reproduced exactly as rev1_lib.estimate draws it: the same generator seeded with
the table's own seed, the samples drawn first and the candidates second, so the point scored here
is the point that run actually started from. lambda_max and the per slice outcome are read from
evidence/far-field-slices.csv rather than recomputed, so the probe cannot disagree with Table I by
recomputing anything.

Usage: seedpoint_probe.py [scroll ...]      (default: the fifteen scrolls, about two minutes)
Output: this file's own stdout, kept beside it in probe.log. Nothing else is written.
"""
import os
import sys
import time

import numpy as np

SRC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SRC, "tools"))
sys.path.insert(0, os.path.join(SRC, "inputs"))
import rev1_lib as L          # noqa: E402
import villa_estimator as ve  # noqa: E402


def main():
    scrolls = sys.argv[1:] or list(L.CFG)
    far = {(r["scroll"], int(r["z"])): r
           for r in L.read_csv(os.path.join(L.EV, "far-field-slices.csv"))}
    rows, t0 = [], time.perf_counter()
    for scroll in scrolls:
        for z in L.heights(scroll):
            s = L.grid15_slice(scroll, z)
            if s is None:
                continue
            mid, nrm, W, H = s
            ms, ns, rng = L.sample(mid, nrm, L.TABLE_SEED + z)
            cand = np.stack([rng.uniform(0, W, ve.N_CANDIDATES),
                             rng.uniform(0, H, ve.N_CANDIDATES)], 1)
            seed_pt = cand[int(np.argmax(ve.seed_score(cand, ms, ns)))]
            mean_at_seed = float(L.refine_score(seed_pt, ms, ns, True)[0])
            f = far[(scroll, z)]
            rows.append((float(f["lambda_max"]) > mean_at_seed, int(f["outside_seed_zero"])))
    tp = sum(1 for p, o in rows if p and o)
    fp = sum(1 for p, o in rows if p and not o)
    fn = sum(1 for p, o in rows if not p and o)
    tn = sum(1 for p, o in rows if not p and not o)
    print(f"slices {len(rows)}   elapsed {time.perf_counter() - t0:.0f}s")
    print(f"  at the seed point: fires on {tp + fp}, of which {fp} on a run that stayed inside; "
          f"misses {fn} of the {tp + fn} runs that left")
    print(f"  sensitivity {tp / (tp + fn):.2f}   specificity {tn / (tn + fp):.2f}")
    print("  the outcome is the single k = 0 run of each slice, so the runs that left number "
          f"{tp + fn}, against the 134 slices Table I counts by majority of the 20 seeds")
    print("  POST HOC: no criterion was fixed before this ran, and no published number uses it")


if __name__ == "__main__":
    main()
