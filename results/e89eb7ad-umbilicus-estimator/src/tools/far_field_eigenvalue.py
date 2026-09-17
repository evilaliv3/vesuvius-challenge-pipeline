# This file is a copy of tools/far_field_eigenvalue.py of the working tree and differs from it in
# one way only: the absolute paths of the machine the measurements ran on are replaced by paths
# inside this folder, resolved from the file's own location. Nothing else is changed.
"""The far field limit of the weighted mean, as an eigenvalue, on the slice of Fig. 2 and on two
synthetic sections.

Reviewer's point 1 on the short paper (2026-09-17). Let D be the distance of the candidate from
the section and u the unit direction from the candidate to the section. When D is much larger than
the section every weight 1/max(100, d_i) tends to 1/D and every direction from the candidate to a
segment tends to u, so the weighted mean of cpp:98-117 tends to the plain mean of (n_i . u)^2 over
the sampled normals, which is u^T C u with C = (1/N) sum_i n_i n_i^T. The maximum of that limit
over u is the largest eigenvalue of C. On a complete set of radial normals C is I/2 and the limit
is 1/2 whatever u; on a section whose normals are coherent it rises towards 1 along the mean
normal, and it can exceed the score the mean gives at the true centre once the normals there are
noisy. That is the mechanism by which the mean has no interior maximum on a partial prediction and
keeps one on a complete section.

Measured here, with the samples the estimator itself draws (rev1_lib.sample, 10000 draws with
replacement, the seed of the table for the real slice and the seed of the mechanism curve for the
synthetic ones): the two eigenvalues of C, the weighted mean at the true centre (the control point
of the reference, for the real slice), and, as a check of the algebra, the weighted mean evaluated
numerically a million units away along the eigenvector of the largest eigenvalue, which must
reproduce it.

Sections: the PHerc0826 xy slice 8000 that Fig. 2 draws, from the same cached grid file
figure_umbilicus.f2 reads; the circle 1:1 and the half circle of tools/synthetic_density.py.

Extended on 2026-09-17, second round of the reviewer's points: the same quantity on every one of
the 360 slices of the fifteen scrolls with a reference, to test whether equation (1) predicts
where the published estimator leaves the grid. Per slice, with the samples the table's own seed
draws: lambda_max of C, and the weighted mean at the reference control point of that slice, the
reference being used only to evaluate the score at a point known to lie on the axis, which is
measuring and not choosing. The prediction is the sign of lambda_max minus that score: when the
far field bound exceeds the score on the axis, the mean has somewhere better to go than the axis
and the climb should walk out.

The rule for what counts as leaving the grid is fixed here before the run, and not after seeing
the table: a slice counts as leaving the grid, as published, when more than half of its 20 seeds
land outside (k20-estimates.csv, variant as-is). The k = 0 seed of the frozen table is reported
beside it as a sensitivity, and both are written to the CSV.

Two predictors are computed, because the paper reports one and the code could only use the other
(third review round, 2026-09-17). The first compares lambda_max with the weighted mean at the
reference control point: that is the measurement, and it needs a reference the code does not have.
The second compares lambda_max with the weighted mean at the point the published search actually
returns on that slice, which is what a warning inside align_and_extract_umbilicus would compare,
since the refined score is the only score the function holds when it is about to return. The
second is evaluated per run rather than per slice, on the k = 0 seed of the frozen table, because
a warning fires inside one run: the estimate is the k = 0 as-published estimate of
k20-estimates.csv and the outcome is whether that same run left the grid. The two rates need not
coincide, and neither is used to correct the other.

Outputs: evidence/far-field-eigenvalue.csv (the three sections above),
far-field-slices.csv (one row per slice) and far-field-prediction.csv (the two by two table with
Fisher's exact test, on the majority rule and on the k = 0 seed). Cost: seconds for the three
sections, a couple of minutes for the 360 slices.

Usage: far_field_eigenvalue.py [--slices] [--scroll NAME]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "inputs"))
import rev1_lib as L          # noqa: E402
import synthetic_sections as S   # noqa: E402

SLICE_SCROLL, SLICE_Z = "PHerc0826", 8000
SLICE_FILE = os.path.join(L.NG, "cache", "pherc0826", "ngrid", "xy", "008000.grid")   # figure_umbilicus.f2
SYN_C = np.array([4000.0, 4000.0])        # synthetic_density.py
SYN_SEED = 60000                           # synthetic_density.mechanism_curve
FAR = 1.0e6


def analyse(name, source, mid, nrm, centre, seed):
    ms, ns, _ = L.sample(mid, nrm, seed)
    ns = ns / np.linalg.norm(ns, axis=1, keepdims=True)
    C = ns.T @ ns / len(ns)
    w, V = np.linalg.eigh(C)
    lam_min, lam_max = float(w[0]), float(w[1])
    e_max = V[:, 1]
    at_centre = float(L.refine_score(centre, ms, ns, True)[0])
    # the candidate a million units away along the eigenvector, on either side, and the algebra
    # says the mean there is lam_max in both places
    far = [float(L.refine_score(centre + s * FAR * e_max, ms, ns, True)[0]) for s in (1.0, -1.0)]
    far_min = [float(L.refine_score(centre + s * FAR * V[:, 0], ms, ns, True)[0]) for s in (1.0, -1.0)]
    return dict(section=name, source=source, n_segments=len(mid), n_samples=len(ms), seed=seed,
                lambda_max=round(lam_max, 4), lambda_min=round(lam_min, 4),
                eigenvector_max_x=round(float(e_max[0]), 4), eigenvector_max_y=round(float(e_max[1]), 4),
                mean_at_centre=round(at_centre, 4),
                mean_far_along_max=round(max(far), 4), mean_far_along_min=round(min(far_min), 4),
                far_over_centre=round(max(far) / at_centre, 4),
                far_distance_units=FAR)


def slice_rows(scrolls):
    """One row per slice: lambda_max, the weighted mean at the reference, and what happened."""
    out = []
    outside = {}
    est0 = {}
    # The outcome each slice is validated against is whether the run left the grid, and since
    # 2026-09-18 that run is the shipped function's, cpp-k20-estimates.csv, same slices and seeds
    # with no cap; the transcription's file is read only when the C++ one is absent. An estimate
    # that met the wall clock guard has no position and is skipped; there were none.
    est_file = os.path.join(L.EV, "cpp-k20-estimates.csv")
    if not os.path.exists(est_file):
        est_file = os.path.join(L.EV, "k20-estimates.csv")
    print(f"  outcomes read from {os.path.basename(est_file)}", flush=True)
    for r in L.read_csv(est_file):
        if r["variant"] != "as-is" or int(r.get("guard", 0)):
            continue
        if int(r["k"]) == 0:
            est0[(r["scroll"], int(r["z"]))] = (float(r["x"]), float(r["y"]))
        rec = outside.setdefault((r["scroll"], int(r["z"])), [0, 0, None])
        rec[0] += 1
        rec[1] += int(r["inside"]) == 0
        if int(r["k"]) == 0:
            rec[2] = int(r["inside"]) == 0
    for scroll in scrolls:
        ref = L.reference(scroll)
        sc = L.CFG[scroll]["grid_scale"]
        for z in L.heights(scroll):
            sl = L.grid15_slice(scroll, z)
            if sl is None:
                continue
            mid, nrm, Wg, Hg = sl
            ms, ns, _ = L.sample(mid, nrm, L.TABLE_SEED + z)
            ns = ns / np.linalg.norm(ns, axis=1, keepdims=True)
            w = np.linalg.eigvalsh(ns.T @ ns / len(ns))
            z0 = z * sc
            cp = np.array([np.interp(z0, ref[:, 2], ref[:, 0]) / sc,
                           np.interp(z0, ref[:, 2], ref[:, 1]) / sc])
            at_ref = float(L.refine_score(cp, ms, ns, True)[0])
            xy0 = est0.get((scroll, z))
            at_ref_refined = (float(L.refine_score(np.array(xy0), ms, ns, True)[0])
                              if xy0 else float("nan"))
            n, nout, k0 = outside.get((scroll, z), (0, 0, None))
            out.append(dict(scroll=scroll, z=z, segments=len(mid), samples=len(ms),
                            lambda_max=round(float(w[1]), 4), lambda_min=round(float(w[0]), 4),
                            mean_at_reference=round(at_ref, 4),
                            lambda_over_mean=round(float(w[1]) / at_ref, 4),
                            predicts_runaway=int(float(w[1]) > at_ref),
                            estimate_k0_x=round(xy0[0], 2) if xy0 else "",
                            estimate_k0_y=round(xy0[1], 2) if xy0 else "",
                            mean_at_refined=round(at_ref_refined, 4) if xy0 else "",
                            predicts_runaway_refined=int(float(w[1]) > at_ref_refined) if xy0 else "",
                            seeds=n, seeds_outside=nout,
                            outside_majority=int(nout * 2 > n) if n else "",
                            outside_seed_zero=int(k0) if k0 is not None else ""))
            r = out[-1]
            print(f"  {scroll:12s} z {z:6d}  lambda_max {r['lambda_max']:.4f}  mean at ref "
                  f"{r['mean_at_reference']:.4f}  predicts {r['predicts_runaway']}  "
                  f"outside {r['seeds_outside']:3d}/{r['seeds']}", flush=True)
    return out


def two_by_two(rows, key, label, pred="predicts_runaway"):
    """Predicted against observed, with Fisher's exact test."""
    from scipy.stats import fisher_exact
    rows = [r for r in rows if r[pred] != "" and r[key] != ""]
    cells = {}
    for p in (1, 0):
        for o in (1, 0):
            cells[(p, o)] = sum(1 for r in rows if r[pred] == p and r[key] == o)
    table = [[cells[(1, 1)], cells[(1, 0)]], [cells[(0, 1)], cells[(0, 0)]]]
    odds, p = fisher_exact(table)
    tp, fp, fn, tn = table[0][0], table[0][1], table[1][0], table[1][1]
    row = dict(rule=label, predictor=pred, n=sum(sum(t) for t in table),
               predicted_yes_observed_yes=tp, predicted_yes_observed_no=fp,
               predicted_no_observed_yes=fn, predicted_no_observed_no=tn,
               sensitivity=round(tp / (tp + fn), 3) if tp + fn else "",
               specificity=round(tn / (tn + fp), 3) if tn + fp else "",
               precision=round(tp / (tp + fp), 3) if tp + fp else "",
               accuracy=round((tp + tn) / sum(sum(t) for t in table), 3),
               odds_ratio=("inf" if odds == float("inf") else round(float(odds), 2)),
               fisher_p=f"{p:.2e}")
    print(f"  {label}: predicted yes {tp} of {tp + fp} ran away, predicted no {fn} of {fn + tn} "
          f"ran away; Fisher p {p:.2e}, odds {row['odds_ratio']}", flush=True)
    return row


def main():
    if "--slices" in sys.argv:
        scrolls = list(L.CFG)
        if "--scroll" in sys.argv:
            scrolls = [sys.argv[sys.argv.index("--scroll") + 1]]
        rows = slice_rows(scrolls)
        # WHY THIS GUARD EXISTS, and why it matters more here than anywhere else. far-field-slices.csv
        # is the ONLY input of far_field_scrolls.py, which writes Table I and its permutation test.
        # Demonstrated on 2026-09-18 with one of the fifteen scrolls on disk: this ran to the end,
        # exited 0, and replaced a 360 row file with a 24 row one, after which Table I would have
        # been rebuilt from the wreckage with nothing in the chain complaining. A tool that
        # destroys a paper's input and exits zero is the failure nobody notices until the number is
        # already published. The grids sit under inputs/ and are in no repository, so
        # a cache eviction or a moved path is enough.
        #
        # The test is scrolls that yielded NO slice at all, not empty slices: a height with no
        # published grid is fetched as a zero byte file on purpose and L.grid15_slice skips it, so a
        # complete cut legitimately has empty slices and a stricter test would refuse on good data.
        empty = [s for s in scrolls if not any(r["scroll"] == s for r in rows)]
        stem = "far-field"
        if empty and "--allow-missing" not in sys.argv:
            raise SystemExit(
                f"{len(empty)} of {len(scrolls)} scrolls have no grid slice on disk "
                f"({', '.join(empty[:4])}{', ...' if len(empty) > 4 else ''}). "
                f"Cut the slices into inputs/grid15/ as section 3 of ../README.md says, or pass "
                f"--allow-missing to write to {stem}-partial-*, which does not overwrite "
                f"{stem}-slices.csv and {stem}-prediction.csv.")
        if empty:
            stem += "-partial"
        L.write_csv(os.path.join(L.EV, f"{stem}-slices.csv"), list(rows[0]), rows)
        if len(scrolls) > 1:
            pred = [two_by_two(rows, "outside_majority", "majority of 20 seeds"),
                    two_by_two(rows, "outside_seed_zero", "seed of the frozen table"),
                    two_by_two(rows, "outside_seed_zero",
                               "refined score, the code's own comparison, seed of the frozen table",
                               pred="predicts_runaway_refined")]
            L.write_csv(os.path.join(L.EV, f"{stem}-prediction.csv"), list(pred[0]), pred)
        return
    rows = []
    h, paths, _ = L.read_grid(SLICE_FILE)
    mid, nrm = L.segments(paths)
    ref = L.reference(SLICE_SCROLL)
    sc = L.CFG[SLICE_SCROLL]["grid_scale"]
    z0 = SLICE_Z * sc
    cp = np.array([np.interp(z0, ref[:, 2], ref[:, 0]) / sc, np.interp(z0, ref[:, 2], ref[:, 1]) / sc])
    rows.append(analyse(f"{SLICE_SCROLL} xy {SLICE_Z}", os.path.relpath(SLICE_FILE, L.SRC),
                        mid, nrm, cp, L.TABLE_SEED + SLICE_Z))
    for name, make in (("circle 1:1", lambda: S.circles(*SYN_C)),
                       ("half circle", lambda: S.circles(*SYN_C, frac=0.5))):
        m2, n2 = S.polyline_segments(make())
        rows.append(analyse(name, "synthetic_sections.py", m2, n2, SYN_C, SYN_SEED))
    for r in rows:
        print(f"  {r['section']:22s} lambda_max {r['lambda_max']:.4f}  lambda_min {r['lambda_min']:.4f}  "
              f"mean at centre {r['mean_at_centre']:.4f}  far along max {r['mean_far_along_max']:.4f}  "
              f"far/centre {r['far_over_centre']:.3f}", flush=True)
        if abs(r["mean_far_along_max"] - r["lambda_max"]) > 2e-3:
            raise SystemExit(f"far field along the eigenvector does not reproduce lambda_max on {r['section']}")
    L.write_csv(os.path.join(L.EV, "far-field-eigenvalue.csv"), list(rows[0]), rows)


if __name__ == "__main__":
    main()
