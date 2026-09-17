# This file is a copy of tools/fifteen_k20.py of the working tree and differs from it in one way
# only: the absolute paths of the machine the measurements ran on are replaced by paths
# inside this folder, resolved from the file's own location. Nothing else is changed.
"""Tables II and III of the frozen paper with twenty seeds per slice, with intervals.

Meta B of the revision (inputs/note-twenty-seeds.md, written before this ran). The frozen tables
use one seed per slice, and the spread of the search between runs on one slice reaches 1.31 mm in
the median (evidence/search-noise.csv), so a margin of 0.41 or 0.80 mm over the centroid is
inside the noise of the search. Here every slice is estimated with twenty seeds,
20260915 + z + 1000 k for k = 0..19, so that k = 0 is exactly the seed of the frozen tables and
the k = 0 row has to reproduce evidence/fifteen.csv (known reference, checked by this tool).

Same slices as the frozen tables, same metric (bench.errors on the control points inside the
common z range), same baselines (filled-mask centroid at level 3 on the bench's own heights, the
constant axis), same threshold and criteria (preregistration-fifteen-references.md), applied as
written.

Per scroll and variant: the median over the twenty per-seed medians m_k, their IQR, and a 95 %
percentile bootstrap interval of the median, 1000 resamples, generator seed 20260916 written in
the CSV. One resample: for every slice one of its twenty estimates is drawn at random (with
replacement across resamples), the polyline is built, the control points are resampled with
replacement, the median is taken. The generator is seeded per scroll and rule
([20260916, scroll index, rule index]), so that tools/ablation_search.py, scoring the same
estimates, draws the same resamples and its cells a and b reproduce these rows to the digit. The margin over the centroid is the centroid's median (fixed)
minus the estimator's, with the interval of the estimator's bootstrap, and two flags: whether the
interval of the margin includes zero and whether it reaches below the 0.30 mm threshold.

    fifteen_k20.py --workers 12            # the fifteen scrolls, resuming from k20-estimates.csv
    fifteen_k20.py --reference-check       # twenty seeds on the four saved C++ slices, against
                                           # evidence/search-noise.csv (1.31 mm on 0125 z 6891)

Outputs: evidence/k20-estimates.csv (every estimate), fifteen-k20.csv (one row per
scroll and variant), fifteen-k20-verdicts.json, k20-search-noise.csv.
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L          # noqa: E402
import villa_estimator as ve  # noqa: E402

K = 20
B = 1000
BOOT_SEED = 20260916
RAW = os.path.join(L.EV, "k20-estimates.csv")
RAW_COLS = ["scroll", "z", "k", "seed", "variant", "x", "y", "inside", "capped"]


def seed_of(z, k):
    return L.TABLE_SEED + z + 1000 * k


def estimates_for(scroll):
    """Every estimate of one scroll: 24 slices, 20 seeds, both variants, grid units."""
    t0 = time.perf_counter()
    rows = []
    for z in L.heights(scroll):
        s = L.grid15_slice(scroll, z)
        if s is None:
            continue
        mid, nrm, W, H = s
        for k in range(K):
            for variant, divide in (("as-is", True), ("no-division", False)):
                xy, cap = L.estimate(mid, nrm, W, H, seed_of(z, k), divide)
                rows.append(dict(scroll=scroll, z=z, k=k, seed=seed_of(z, k), variant=variant,
                                 x=float(xy[0]), y=float(xy[1]),
                                 inside=int(0 <= xy[0] <= W and 0 <= xy[1] <= H), capped=int(cap)))
    print(f"  {scroll:12s} {len(rows)} estimates in {time.perf_counter() - t0:.0f}s", flush=True)
    return rows


def score(scroll, raw):
    """From the raw estimates of one scroll to the summary rows, both variants."""
    cfg = L.CFG[scroll]
    sc, mm = cfg["grid_scale"], cfg["voxel_um"] / 1000.0
    ref = L.reference(scroll)
    zs = sorted({r["z"] for r in raw})
    W = None
    for z in zs:
        s = L.grid15_slice(scroll, z)
        if s:
            W = s[2]
            break
    base = L.baselines(scroll, W)
    poly = {}
    for variant in ("as-is", "no-division"):
        poly[variant] = np.zeros((K, len(zs), 3))
        for r in raw:
            if r["variant"] == variant:
                poly[variant][r["k"], zs.index(r["z"])] = (r["x"] * sc, r["y"] * sc, r["z"] * sc)
    # the common z range, by the frozen tables' rule: every line, including the two baselines
    zlo = max([base["centroid"][:, 2].min(), base["fake_axis"][:, 2].min()] +
              [poly[v][0][:, 2].min() for v in poly])
    zhi = min([base["centroid"][:, 2].max(), base["fake_axis"][:, 2].max()] +
              [poly[v][0][:, 2].max() for v in poly])
    common = ref[(ref[:, 2] >= zlo) & (ref[:, 2] <= zhi)]
    out = []
    cen_e, _ = L.errors(common, base["centroid"], mm)
    fake_e, _ = L.errors(common, base["fake_axis"], mm)
    # one generator per scroll and rule, seeded from the bootstrap seed, the scroll's index and
    # the rule's index: a second tool scoring the same estimates then draws the same resamples
    scroll_i = list(L.CFG).index(scroll)
    rng = np.random.default_rng([BOOT_SEED, scroll_i, 99])
    cen_boot = np.array([np.median(rng.choice(cen_e, len(cen_e))) for _ in range(B)])
    cen_med = float(np.median(cen_e))
    for vi, variant in enumerate(("as-is", "no-division")):
        P = poly[variant]
        m_k = np.array([np.median(L.errors(common, P[k], mm)[0]) for k in range(K)])
        rng = np.random.default_rng([BOOT_SEED, scroll_i, vi])
        boot = np.empty(B)
        for b in range(B):
            pick = rng.integers(0, K, len(zs))
            pl = P[pick, np.arange(len(zs))]
            e, _ = L.errors(common, pl, mm)
            boot[b] = np.median(rng.choice(e, len(e)))
        lo, hi = np.percentile(boot, [2.5, 97.5])
        med = float(np.median(m_k))
        margin = cen_med - med
        m_lo, m_hi = cen_med - hi, cen_med - lo
        out.append(dict(
            scroll=scroll, block=cfg["block"], variant=variant, voxel_um=cfg["voxel_um"],
            slices=len(zs), seeds=K, control_points=len(common),
            z_lo=round(zlo), z_hi=round(zhi),
            median_k0_mm=round(float(m_k[0]), 2),
            median_mm=round(med, 2), iqr_mm=round(float(np.percentile(m_k, 75) - np.percentile(m_k, 25)), 2),
            min_mm=round(float(m_k.min()), 2), max_mm=round(float(m_k.max()), 2),
            ci_lo_mm=round(float(lo), 2), ci_hi_mm=round(float(hi), 2),
            inside=sum(r["inside"] for r in raw if r["variant"] == variant),
            inside_of=K * len(zs),
            centroid_mm=round(cen_med, 2),
            centroid_ci_lo_mm=round(float(np.percentile(cen_boot, 2.5)), 2),
            centroid_ci_hi_mm=round(float(np.percentile(cen_boot, 97.5)), 2),
            fake_axis_mm=round(float(np.median(fake_e)), 2),
            margin_vs_centroid_mm=round(margin, 2),
            margin_ci_lo_mm=round(float(m_lo), 2), margin_ci_hi_mm=round(float(m_hi), 2),
            margin_ci_includes_zero=int(m_lo <= 0 <= m_hi),
            margin_ci_below_threshold=int(m_lo < L.THRESHOLD_MM),
            bootstrap_resamples=B, bootstrap_seed=BOOT_SEED))
    return out


def verdict(rows, block, need_repair, need_beat):
    """make_numbers.verdict, applied to the medians over the twenty seeds."""
    T = L.THRESHOLD_MM
    b = {(q["scroll"]): q for q in rows if q["block"] == block and q["variant"] == "no-division"}
    a = {(q["scroll"]): q for q in rows if q["block"] == block and q["variant"] == "as-is"}
    repaired = [s for s in b if b[s]["median_mm"] < a[s]["median_mm"]]
    zero_outside = all(b[s]["inside"] == b[s]["inside_of"] for s in b)
    beats = [s for s in b if b[s]["margin_vs_centroid_mm"] >= T]
    never_double = all(b[s]["median_mm"] <= 2 * b[s]["centroid_mm"] for s in b)
    loses = [s for s in b if b[s]["margin_vs_centroid_mm"] <= -T]
    p1 = len(repaired) >= need_repair and zero_outside
    won = len(beats) >= need_beat and never_double
    lost = len(loses) >= need_beat
    return dict(n=len(b), repaired=len(repaired), zero_outside=zero_outside, beats=len(beats),
                beats_scrolls=sorted(beats), loses=len(loses), never_double=never_double,
                repair="won" if p1 else "lost",
                beat="won" if won else "lost" if lost else "neither won nor lost",
                margins_with_interval_including_zero=sorted(
                    s for s in beats if b[s]["margin_ci_includes_zero"]))


def sparse_slices(scroll):
    """Slices of the frozen tables with fewer than N_SAMPLES segments, where the frozen
    transcription capped its draw and this tool does not (audit of 2026-09-16)."""
    n = 0
    for z in L.heights(scroll):
        g = L.grid15_slice(scroll, z)
        n += bool(g) and len(g[0]) < ve.N_SAMPLES
    return n


def check_k0(rows):
    """k = 0 is the seed of the frozen tables: the medians must match fifteen.csv on every scroll
    whose slices all have at least N_SAMPLES segments; on the others the difference is the effect
    of the corrected sampling and is printed, not counted as a failure."""
    old = {q["scroll"]: q for q in L.read_csv(os.path.join(L.EV, "fifteen.csv"))}
    bad = []
    sparse = {s: sparse_slices(s) for s in L.CFG}
    for r in rows:
        q = old[r["scroll"]]
        want = float(q["published_mm"] if r["variant"] == "as-is" else q["no_division_mm"])
        r["sparse_slices"] = sparse[r["scroll"]]
        r["frozen_k0_mm"] = want
        if abs(want - r["median_k0_mm"]) > 0.011:
            if sparse[r["scroll"]]:
                print(f"  {r['scroll']} {r['variant']}: k = 0 moved from {want} to {r['median_k0_mm']} mm "
                      f"with the corrected sampling ({sparse[r['scroll']]} sparse slices)")
            else:
                bad.append((r["scroll"], r["variant"], want, r["median_k0_mm"]))
        if r["variant"] == "no-division" and abs(float(q["centroid_mm"]) - r["centroid_mm"]) > 0.011:
            bad.append((r["scroll"], "centroid", q["centroid_mm"], r["centroid_mm"]))
    print("  known reference (k = 0 against fifteen.csv):",
          "reproduced" if not bad else f"NOT reproduced: {bad}", flush=True)
    return bad


def reference_check():
    """Twenty seeds of the transcription on the four saved C++ slices, spread from the median."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "inputs"))
    import slices
    noise = {(q["scroll"], int(q["slice_z"]), q["variant"]): q
             for q in L.read_csv(os.path.join(L.EV, "search-noise.csv"))}
    rows = []
    for scroll, z, mid, nrm, W, H, mm in slices.saved():
        for variant, divide in (("as-is", True), ("no-division", False)):
            P = np.array([L.estimate(mid, nrm, W, H, seed_of(z, k), divide)[0] for k in range(K)])
            med = np.median(P, 0)
            d = np.sort(np.hypot(*(P - med).T) * mm)
            q = noise.get((scroll, z, variant))
            rows.append(dict(scroll=scroll, slice_z=z, variant=variant, seeds=K,
                             spread_median_mm=round(float(np.median(d)), 2),
                             spread_p90_mm=round(float(d[int(.9 * (K - 1))]), 2),
                             spread_worst_mm=round(float(d[-1]), 2),
                             cpp_spread_median_mm=q["spread_median_mm"] if q else "",
                             cpp_spread_worst_mm=q["spread_worst_mm"] if q else ""))
            print(f"  {scroll} z {z} {variant:12s} transcription {rows[-1]['spread_median_mm']:8.2f} mm"
                  f"   C++ {rows[-1]['cpp_spread_median_mm']}", flush=True)
    L.write_csv(os.path.join(L.EV, "k20-search-noise.csv"), list(rows[0]), rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--reference-check", action="store_true")
    a = ap.parse_args()
    if a.reference_check:
        reference_check()
        return 0
    t0 = time.perf_counter()
    raw = []
    if os.path.exists(RAW):
        for r in L.read_csv(RAW):
            raw.append(dict(r, z=int(r["z"]), k=int(r["k"]), seed=int(r["seed"]), x=float(r["x"]),
                            y=float(r["y"]), inside=int(r["inside"]), capped=int(r["capped"])))
    done = {r["scroll"] for r in raw}
    todo = [s for s in L.CFG if s not in done]
    if todo:
        with Pool(a.workers) as pool:
            for part in pool.imap_unordered(estimates_for, todo):
                raw.extend(part)
                L.write_csv(RAW, RAW_COLS, raw)       # written after each scroll, resumable
    rows = []
    for scroll in L.CFG:
        rows.extend(score(scroll, [r for r in raw if r["scroll"] == scroll]))
        print(f"  scored {scroll} ({time.perf_counter() - t0:.0f}s)", flush=True)
    bad = check_k0(rows)
    L.write_csv(os.path.join(L.EV, "fifteen-k20.csv"), list(rows[0]), rows)
    v = {"primary": verdict(rows, "primary", 4, 3), "confirmation": verdict(rows, "confirmation", 8, 6)}
    json.dump(v, open(os.path.join(L.EV, "fifteen-k20-verdicts.json"), "w"), indent=1)
    print(json.dumps(v, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
