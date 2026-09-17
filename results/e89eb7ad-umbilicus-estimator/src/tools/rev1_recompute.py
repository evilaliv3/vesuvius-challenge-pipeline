# This file is a copy of tools/rev1_recompute.py of the working tree and differs from it in one way
# only: the absolute paths of the machine the measurements ran on are replaced by paths
# inside this folder, resolved from the file's own location. Nothing else is changed.
"""Recompute every measurement of the paper that runs the estimator, with the faithful sample.

The audit of 2026-09-16 found that the frozen transcription drew min(10000, n) segments while the
C++ always draws 10000 with replacement. Everything under tools/ now samples through
rev1_lib.sample; this tool redoes, with that sampling, the evidence files that the frozen run
produced and that the revision had until now only copied:

  twentythree      the five reference-free properties on the 24 scrolls of grid23 (inside the grid,
                   seed spread over three seeds, median jump along z, distance from the segment
                   centroid, interior-maximum probe), both variants, same slices and seeds as
                   the frozen run of the competition set
  positions        every estimate of that run, one row per slice and variant (figures 6 and 7)
  synthetic        the seven families of sections with a known centre (battery P5), 20 seeds,
                   both variants, same configurations as inputs/synthetic_sections.py
  noise-by-variant which variant is the steadier between runs, on the four saved bench slices,
                   30 repeats per group, Mann-Whitney U and the A12 effect size (battery P2)

Outputs go to evidence/<name>-refit.csv, never to the frozen run. The old files stay.

    rev1_recompute.py twentythree --workers 12
    rev1_recompute.py synthetic --workers 12
    rev1_recompute.py noise --workers 8
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "inputs"))
import rev1_lib as L                          # noqa: E402
import villa_estimator as ve                  # noqa: E402

SEEDS = (20260915, 7, 123456)                 # the seeds of the frozen competition-set run
MM = 0.009362


def interior_max(ms, ns, centre, divide, half=200.0, step=4.0):
    """villa_estimator.interior_max, on samples drawn by the faithful rule."""
    g = np.arange(-half, half + 1, step)
    LX, LY = np.meshgrid(centre[0] + g, centre[1] + g)
    lat = np.stack([LX.ravel(), LY.ravel()], 1)
    m = lat[int(np.argmax(L.refine_score(lat, ms, ns, divide)))]
    return bool(abs(m[0] - centre[0]) < half - 1 and abs(m[1] - centre[1]) < half - 1)


def one_scroll(scroll):
    t0 = time.perf_counter()
    sl = L.grid23_slices(scroll)
    res = {True: [], False: []}
    spread, gridc, rows, W, H = [], [], [], None, None
    for z, mid, nrm, W, H in sl:
        for divide in (True, False):
            xy, cap = L.estimate(mid, nrm, W, H, SEEDS[0] + z, divide)
            res[divide].append((z, xy))
            rows.append(dict(scroll=scroll, z=z, variant="as-is" if divide else "no-division",
                             x=round(float(xy[0]), 2), y=round(float(xy[1]), 2), width=W, height=H,
                             inside=int(0 <= xy[0] <= W and 0 <= xy[1] <= H), capped=int(cap)))
        trio = np.array([L.estimate(mid, nrm, W, H, s + z, False)[0] for s in SEEDS])
        spread.append(np.median(np.hypot(*(trio - np.median(trio, 0)).T)))
        gridc.append(mid.mean(0))
    if W is None or len(res[False]) < 3:
        return [], None

    def stats(pairs):
        xy = np.array([p[1] for p in pairs])
        inside = int(((xy[:, 0] >= 0) & (xy[:, 0] <= W) & (xy[:, 1] >= 0) & (xy[:, 1] <= H)).sum())
        jumps = np.hypot(*np.diff(xy, axis=0).T)
        return xy, inside, float(np.median(jumps)), float(jumps.max())

    xy_a, in_a, jmed_a, _ = stats(res[True])
    xy_f, in_f, jmed_f, jmax_f = stats(res[False])
    dcent = np.hypot(*(xy_f - np.array(gridc)).T)
    mid_i = len(res[False]) // 2
    z_mid, xy_mid = res[False][mid_i]
    m2, n2, W2, H2 = next((m, n, w, h) for z, m, n, w, h in sl if z == z_mid)
    ms2, ns2, _ = L.sample(m2, n2, SEEDS[0] + z_mid)
    r = dict(scroll=scroll, width=W, slices=len(res[False]), inside_as_is=in_a, inside_fixed=in_f,
             jump_med_as_is_pct=100 * jmed_a / W, jump_med_fixed_pct=100 * jmed_f / W,
             jump_max_fixed_pct=100 * jmax_f / W,
             seed_spread_pct=100 * float(np.median(spread)) / W,
             centroid_med_pct=100 * float(np.median(dcent)) / W,
             interior_max=interior_max(ms2, ns2, xy_mid, False),
             interior_max_as_is=interior_max(ms2, ns2, [p for p in res[True] if p[0] == z_mid][0][1], True))
    print(f"  {scroll:12s} inside {in_a:2d}->{in_f:2d}/{len(res[False])}  jump {r['jump_med_as_is_pct']:6.2f}->"
          f"{r['jump_med_fixed_pct']:5.2f}%  seed {r['seed_spread_pct']:5.2f}%  ({time.perf_counter()-t0:.0f}s)", flush=True)
    return rows, r


def twentythree(workers):
    # WHY THIS GUARD EXISTS. A tool that destroys a paper's input and exits zero is the failure
    # nobody notices until the number is already published. This took its scroll list from whatever
    # was in inputs/grid23/, so a partial cut wrote a short twentythree-refit.csv and a short
    # positions-24-refit.csv, which figure_umbilicus_gallery.py draws Figure 4 from, at exit 0 and
    # with no row saying anything was absent. Both files are kept in this repository and the cut
    # grid slices are not, so the reader who reaches that state has no way back. The run is defined
    # on the 24 scrolls of inputs/scrolls-24.json, so that is the list.
    #
    # Two ways a scroll can be absent, and both are counted: no directory at all, and a directory
    # too thin for one_scroll to return a summary, which it drops silently. Empty single heights
    # are not counted: a height with no published grid is cut as a zero byte file on purpose.
    #
    # Refusal rather than a row recording the gap, because every column here is a statistic over
    # the slices of that scroll. A row with the statistics left blank would either be dropped by
    # the reader, which is the same silent loss, or read as a number, which is worse.
    declared = sorted(json.load(open(os.path.join(L.NG, "scrolls-24.json"))))
    d23 = os.path.join(L.NG, "grid23")
    # a missing directory is no scrolls, not a traceback: the guard below is the message
    have = set(os.listdir(d23)) if os.path.isdir(d23) else set()
    names = [s for s in declared if s in have]
    with Pool(workers) as pool:
        parts = pool.map(one_scroll, names, chunksize=1)
    pos = [r for rows, _ in parts for r in rows]
    summ = [s for _, s in parts if s]
    gone = [s for s in declared if s not in {r["scroll"] for r in summ}]
    stem = "twentythree-refit"
    if gone and "--allow-missing" not in sys.argv:
        raise SystemExit(
            f"{len(gone)} of {len(declared)} scrolls gave no cut slices to measure "
            f"({', '.join(gone[:4])}{', ...' if len(gone) > 4 else ''}). "
            f"Cut them into inputs/grid23/ as section 3 of ../README.md says, or pass "
            f"--allow-missing to write to {stem}-partial.csv and positions-24-refit-partial.csv, "
            f"which do not overwrite {stem}.csv and positions-24-refit.csv.")
    pstem = "positions-24-refit-partial" if gone else "positions-24-refit"
    if gone:
        stem += "-partial"
    L.write_csv(os.path.join(L.EV, f"{pstem}.csv"),
                ["scroll", "z", "variant", "x", "y", "width", "height", "inside", "capped"], pos)
    L.write_csv(os.path.join(L.EV, f"{stem}.csv"), list(summ[0]), summ)
    old = {r["scroll"]: r for r in L.read_csv(os.path.join(L.EV, "twentythree.csv"))}
    moved = [(s["scroll"], int(old[s["scroll"]]["inside_fixed"]), s["inside_fixed"],
              round(float(old[s["scroll"]]["jump_med_fixed_pct"]), 2), round(s["jump_med_fixed_pct"], 2))
             for s in summ if int(old[s["scroll"]]["inside_fixed"]) != s["inside_fixed"]
             or abs(float(old[s["scroll"]]["jump_med_fixed_pct"]) - s["jump_med_fixed_pct"]) > 0.005]
    print(f"  rows that moved against the frozen run: {len(moved)} of {len(summ)}")
    for m in moved:
        print("   ", m)


def one_section(idx):
    """The configuration is rebuilt inside the worker: synthetic_sections.configs() yields closures, which
    a process pool cannot pickle."""
    import synthetic_sections as S
    name, pname, pval, truth, make = list(S.configs())[idx]
    drop = pval if name.startswith("F") else 0.0
    errs = {True: [], False: []}
    nseg = 0
    for seed in range(20):
        rng = np.random.default_rng(50000 + seed)
        mid, nrm = S.polyline_segments(make(rng))
        if drop:
            keep = rng.random(len(mid)) >= drop
            if keep.sum() < 50:
                keep[rng.choice(len(mid), 50, replace=False)] = True
            mid, nrm = mid[keep], nrm[keep]
        nseg = len(mid)
        for divide in (True, False):
            xy, _ = L.estimate(mid, nrm, S.W, S.H, 60000 + seed, divide)
            errs[divide].append(float(np.hypot(xy[0] - truth[0], xy[1] - truth[1])))
    row = dict(family=name, parameter=pname, value=pval, n_seeds=20, segments=nseg)
    for divide, tag in ((True, "as_is"), (False, "no_division")):
        e = np.array(errs[divide])
        row[f"median_units_{tag}"] = round(float(np.median(e)), 1)
        row[f"median_mm_{tag}"] = round(float(np.median(e)) * MM, 3)
        row[f"p90_units_{tag}"] = round(float(np.percentile(e, 90)), 1)
        row[f"broken_{tag}"] = int(np.median(e) > 200.0)
    print(f"  {name:22s} {pname:32s} {pval:8.2f}  as-is {row['median_units_as_is']:7.1f}  "
          f"sum {row['median_units_no_division']:7.1f}", flush=True)
    return row


def synthetic(workers):
    import synthetic_sections as S
    n_cfg = len(list(S.configs()))
    with Pool(workers) as pool:
        rows = pool.map(one_section, range(n_cfg), chunksize=1)
    cols = ["family", "parameter", "value", "n_seeds", "segments", "median_units_as_is",
            "median_mm_as_is", "p90_units_as_is", "broken_as_is", "median_units_no_division",
            "median_mm_no_division", "p90_units_no_division", "broken_no_division"]
    L.write_csv(os.path.join(L.EV, "synthetic-sections-refit.csv"), cols, rows)
    old = {(r["family"], r["value"]): r for r in L.read_csv(os.path.join(L.EV, "synthetic-sections.csv"))}
    moved = [(r["family"], r["value"], float(old[(r["family"], str(r["value"]))]["median_units_no_division"]),
              r["median_units_no_division"]) for r in rows
             if (r["family"], str(r["value"])) in old
             and abs(float(old[(r["family"], str(r["value"]))]["median_units_no_division"]) - r["median_units_no_division"]) > 0.05]
    print(f"  sections that moved: {len(moved)} of {len(rows)}")
    for m in moved:
        print("   ", m)


def one_noise(arg):
    scroll, z, mid, nrm, W, H, mm = arg
    from scipy import stats as st
    d = {}
    for divide, tag in ((True, "as_is"), (False, "no_division")):
        P = np.array([L.estimate(mid, nrm, W, H, 90000 + k, divide)[0] for k in range(30)])
        med = np.median(P, 0)
        d[tag] = np.hypot(*(P - med).T) * mm
    a, b = d["as_is"], d["no_division"]
    u, p = st.mannwhitneyu(a, b, alternative="two-sided")
    a12 = u / (len(a) * len(b))
    print(f"  {scroll} z {z}: as-is {np.median(a):.3f} mm, sum {np.median(b):.3f} mm, A12 {a12:.3f}, p {p:.4f}", flush=True)
    return dict(scroll=scroll, z=z, n_per_group=30, median_as_is_mm=round(float(np.median(a)), 3),
                median_no_division_mm=round(float(np.median(b)), 3), U=float(u),
                p=round(float(p), 6), a12_as_is_vs_no_division=round(float(a12), 3))


def noise(workers):
    import slices
    with Pool(workers) as pool:
        rows = pool.map(one_noise, slices.saved(), chunksize=1)
    L.write_csv(os.path.join(L.EV, "noise-by-variant-refit.csv"), list(rows[0]), rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["twentythree", "synthetic", "noise"])
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    {"twentythree": twentythree, "synthetic": synthetic, "noise": noise}[a.what](a.workers)
