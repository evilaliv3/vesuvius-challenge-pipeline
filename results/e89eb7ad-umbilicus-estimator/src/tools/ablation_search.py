"""The four cells of Section III-C, which the frozen paper states without a number.

Meta C, point 2 of the revision (inputs/note-twenty-seeds.md). Same fifteen scrolls, same slices,
same twenty seeds per slice as tools/fifteen_k20.py, same metric and bootstrap, four estimators:

  a  published            weighted mean, villa's search (cpp:78-142 as transcribed)
  b  division removed     weighted sum, villa's search: the one-line repair
  c  rewritten, mean      the rewritten search (float64, clipped to the grid, probes from a fixed
                          centre, step halves when none improves, one objective), weighted mean
  d  rewritten, sum       the same search with the weighted sum

Cells a and b are computed here again, not read from fifteen-k20.csv: they are the same
calculation done by a second tool, and the known reference is that the b column of this file
matches fifteen-k20.csv (checked at the end). If it does not, one of the two tools is wrong.

    ablation_search.py --workers 12

Outputs: evidence/ablation-estimates.csv (every estimate), ablation-search.csv.
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L          # noqa: E402

K, B, BOOT_SEED = 20, 1000, 20260916
CELLS = {"a": (True, "villa"), "b": (False, "villa"), "c": (True, "rewritten"), "d": (False, "rewritten")}
RAW = os.path.join(L.EV, "ablation-estimates.csv")
RAW_COLS = ["scroll", "z", "k", "seed", "cell", "x", "y", "inside"]


def estimates_for(scroll):
    t0 = time.perf_counter()
    rows = []
    for z in L.heights(scroll):
        s = L.grid15_slice(scroll, z)
        if s is None:
            continue
        mid, nrm, W, H = s
        for k in range(K):
            seed = L.TABLE_SEED + z + 1000 * k
            for cell, (divide, search) in CELLS.items():
                xy, _ = L.estimate(mid, nrm, W, H, seed, divide, search=search)
                rows.append(dict(scroll=scroll, z=z, k=k, seed=seed, cell=cell,
                                 x=float(xy[0]), y=float(xy[1]),
                                 inside=int(0 <= xy[0] <= W and 0 <= xy[1] <= H)))
    print(f"  {scroll:12s} {len(rows)} estimates in {time.perf_counter() - t0:.0f}s", flush=True)
    return rows


def score(scroll, raw):
    cfg = L.CFG[scroll]
    sc, mm = cfg["grid_scale"], cfg["voxel_um"] / 1000.0
    ref = L.reference(scroll)
    zs = sorted({r["z"] for r in raw})
    W = next(L.grid15_slice(scroll, z)[2] for z in zs if L.grid15_slice(scroll, z))
    base = L.baselines(scroll, W)
    P = {c: np.zeros((K, len(zs), 3)) for c in CELLS}
    for r in raw:
        P[r["cell"]][r["k"], zs.index(r["z"])] = (r["x"] * sc, r["y"] * sc, r["z"] * sc)
    zlo = max([base["centroid"][:, 2].min(), base["fake_axis"][:, 2].min()] + [P[c][0][:, 2].min() for c in P])
    zhi = min([base["centroid"][:, 2].max(), base["fake_axis"][:, 2].max()] + [P[c][0][:, 2].max() for c in P])
    common = ref[(ref[:, 2] >= zlo) & (ref[:, 2] <= zhi)]
    cen_med = float(np.median(L.errors(common, base["centroid"], mm)[0]))
    scroll_i = list(L.CFG).index(scroll)
    out = []
    for ci, cell in enumerate(CELLS):
        m_k = np.array([np.median(L.errors(common, P[cell][k], mm)[0]) for k in range(K)])
        rng = np.random.default_rng([BOOT_SEED, scroll_i, ci])   # same draws as fifteen_k20.py
        boot = np.empty(B)
        for b in range(B):
            pick = rng.integers(0, K, len(zs))
            e, _ = L.errors(common, P[cell][pick, np.arange(len(zs))], mm)
            boot[b] = np.median(rng.choice(e, len(e)))
        lo, hi = np.percentile(boot, [2.5, 97.5])
        med = float(np.median(m_k))
        out.append(dict(scroll=scroll, block=cfg["block"], cell=cell,
                        objective="mean" if CELLS[cell][0] else "sum", search=CELLS[cell][1],
                        control_points=len(common), slices=len(zs), seeds=K,
                        median_mm=round(med, 2),
                        iqr_mm=round(float(np.percentile(m_k, 75) - np.percentile(m_k, 25)), 2),
                        ci_lo_mm=round(float(lo), 2), ci_hi_mm=round(float(hi), 2),
                        inside=sum(r["inside"] for r in raw if r["cell"] == cell), inside_of=K * len(zs),
                        centroid_mm=round(cen_med, 2), margin_vs_centroid_mm=round(cen_med - med, 2),
                        margin_ci_lo_mm=round(cen_med - float(hi), 2),
                        margin_ci_hi_mm=round(cen_med - float(lo), 2),
                        bootstrap_resamples=B, bootstrap_seed=BOOT_SEED))
    return out


def check_b(rows):
    """Cell b must match the no-division rows of fifteen-k20.csv: same calculation, two tools."""
    p = os.path.join(L.EV, "fifteen-k20.csv")
    if not os.path.exists(p):
        print("  fifteen-k20.csv not there yet: the cross-check is left for later")
        return []
    k20 = {(q["scroll"], q["variant"]): q for q in L.read_csv(p)}
    bad = []
    for r in rows:
        v = {"a": "as-is", "b": "no-division"}.get(r["cell"])
        if not v:
            continue
        q = k20[(r["scroll"], v)]
        for col in ("median_mm", "ci_lo_mm", "ci_hi_mm", "inside"):
            if abs(float(q[col]) - float(r[col])) > 0.011:
                bad.append((r["scroll"], r["cell"], col, q[col], r[col]))
    print("  known reference (cells a, b against fifteen-k20.csv):",
          "identical" if not bad else f"DIFFERENT: {bad}", flush=True)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    raw = []
    if os.path.exists(RAW):
        for r in L.read_csv(RAW):
            raw.append(dict(r, z=int(r["z"]), k=int(r["k"]), seed=int(r["seed"]), x=float(r["x"]),
                            y=float(r["y"]), inside=int(r["inside"])))
    todo = [s for s in L.CFG if s not in {r["scroll"] for r in raw}]
    if todo:
        with Pool(a.workers) as pool:
            for part in pool.imap_unordered(estimates_for, todo):
                raw.extend(part)
                L.write_csv(RAW, RAW_COLS, raw)
    rows = []
    for scroll in L.CFG:
        rows.extend(score(scroll, [r for r in raw if r["scroll"] == scroll]))
    L.write_csv(os.path.join(L.EV, "ablation-search.csv"), list(rows[0]), rows)
    return 1 if check_b(rows) else 0


if __name__ == "__main__":
    sys.exit(main())
