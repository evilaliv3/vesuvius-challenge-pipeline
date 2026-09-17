# This file is a copy of tools/synthetic_density.py of the working tree and differs from it in one way
# only: the absolute paths of the machine the measurements ran on are replaced by paths
# inside this folder, resolved from the file's own location. Nothing else is changed.
"""Density bias of the weighted sum against the weighted mean, on sections with a known centre.

Meta A of the revision (prereg/note-density-bias.md, written before this ran). The referee's
point: a weighted sum rewards the side of the section that has more segments, a weighted mean
normalises the density away. Here the answer is known, so the word is error, not distance.

Sections, 8000 by 8000 grid units, true centre (4000, 4000), radii 300..3500 step 80 as family A of
the battery (inputs/synthetic_sections.py, reused, not retyped):
  circle 1:1        the known reference: must reproduce the curve of Fig. 2 of the frozen paper
  ellipse 1.4       axes ratio 1.4
  half circle       sheet interrupted on one side, family D at fraction 0.5
  density 1:2, 1:5, 1:10   full circles, the half-plane x < 4000 thinned to 1/2, 1/5, 1/10 of
                    its points, the half-plane x > 4000 kept whole: the dense side is +x

For each section and each of 20 seeds: the maximum of the sum field and of the mean field on a
lattice of step 4 in a window of plus or minus 600 units around the true centre, on the SAME
10000 samples villa_estimator.sample draws (seed 60000 + s), then the full estimate of both
variants with villa's own search. Reported: distance of the field maximum from the true centre, its
x component (positive towards the dense side), median and p90 over the seeds, in grid units and in
millimetres at 9.362 um; the same for the estimates.

Outputs: evidence/synthetic-density.csv, evidence/mechanism-curve.csv (the
Fig. 2 curve recomputed on the 1:1 section and on the section figure_umbilicus.f1 draws), and the
figure is drawn by tools/figure_rev1.py from the CSV.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "inputs"))
import rev1_lib as L                 # noqa: E402
import synthetic_sections as S       # noqa: E402
import villa_estimator as ve         # noqa: E402

W = H = 8000.0
C = np.array([4000.0, 4000.0])
SEEDS = range(20)
MM = 0.009362
HALF, STEP = 600.0, 4.0


def thin(mid, nrm, ratio, rng):
    """Keep every segment with x > cx, keep 1/ratio of those with x < cx."""
    if ratio <= 1:
        return mid, nrm
    left = mid[:, 0] < C[0]
    keep = ~left | (rng.random(len(mid)) < 1.0 / ratio)
    return mid[keep], nrm[keep]


def both_fields(cand, ms, ns, c=100.0, block=128):
    """Sum and mean of cpp:98-117 on the same candidates, one pass, two outputs."""
    cand = np.atleast_2d(np.asarray(cand, float))
    sm, mn = np.empty(len(cand)), np.empty(len(cand))
    for s in range(0, len(cand), block):
        cos2, d = ve._cos2(cand[s:s + block], ms, ns)
        w = 1.0 / np.maximum(c, d)
        num = (cos2 * w).sum(1)
        sm[s:s + block] = num
        mn[s:s + block] = num / w.sum(1)
    return sm, mn


def configs():
    yield "circle 1:1", 1.0, lambda rng: S.circles(*C)
    yield "ellipse 1.4", 1.0, lambda rng: S.circles(*C, ratio=1.4)
    yield "half circle", 1.0, lambda rng: S.circles(*C, frac=0.5)
    for r in (2.0, 5.0, 10.0):
        yield f"density 1:{int(r)}", r, lambda rng: S.circles(*C)


def summarise(P):
    """P: (n, 2) positions. Distance from the true centre and x offset, median and p90."""
    d = np.hypot(*(P - C).T)
    dx = P[:, 0] - C[0]
    return dict(err_median_units=round(float(np.median(d)), 1),
                err_p90_units=round(float(np.percentile(d, 90)), 1),
                err_median_mm=round(float(np.median(d)) * MM, 3),
                dx_median_units=round(float(np.median(dx)), 1),
                dy_median_units=round(float(np.median(P[:, 1] - C[1])), 1))


def mechanism_curve():
    """Fig. 2 of the frozen paper, recomputed: score against distance from the centre, two ways.

    Two sections: the one figure_umbilicus.f1 draws (one turn of a spiral, r = 400 + 600 th/2pi,
    4000 points, centred at the origin) and the circle 1:1 of this tool. The known reference is
    the shape: the sum has a maximum at finite distance and falls beyond it, the mean does not.
    """
    rows = []
    th = np.linspace(0, 2 * np.pi, 4000, endpoint=False)
    r = 400 + 30 * th / (2 * np.pi) * 20
    mid = np.stack([r * np.cos(th), r * np.sin(th)], 1)
    t = np.gradient(mid, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    D = np.logspace(1, 6, 140)
    cand = np.stack([D, np.zeros_like(D)], 1)
    sm, mn = both_fields(cand, mid, nrm)
    for dd, a, b in zip(D, sm, mn):
        rows.append(dict(section="f1 spiral", distance_units=round(float(dd), 3),
                         weighted_sum=float(a), weighted_mean=float(b)))
    mid2, nrm2 = S.polyline_segments(S.circles(*C))
    ms, ns, _ = ve.sample(mid2, nrm2, 60000)
    cand = np.stack([C[0] + D, np.full_like(D, C[1])], 1)
    sm, mn = both_fields(cand, ms, ns)
    for dd, a, b in zip(D, sm, mn):
        rows.append(dict(section="circle 1:1", distance_units=round(float(dd), 3),
                         weighted_sum=float(a), weighted_mean=float(b)))
    L.write_csv(os.path.join(L.EV, "mechanism-curve.csv"),
                ["section", "distance_units", "weighted_sum", "weighted_mean"], rows)
    for sec in ("f1 spiral", "circle 1:1"):
        rr = [q for q in rows if q["section"] == sec]
        s = np.array([q["weighted_sum"] for q in rr])
        m = np.array([q["weighted_mean"] for q in rr])
        far = len(rr) - 1
        print(f"  {sec}: sum max at {rr[int(np.argmax(s))]['distance_units']} units, "
              f"sum far/max {s[far] / s.max():.2e}, mean far/max {m[far] / m.max():.3f}",
              flush=True)


def main():
    os.makedirs(L.LOGS, exist_ok=True)
    t0 = time.perf_counter()
    mechanism_curve()
    g = np.arange(-HALF, HALF + 1, STEP)
    LX, LY = np.meshgrid(C[0] + g, C[1] + g)
    lattice = np.stack([LX.ravel(), LY.ravel()], 1)
    rows = []
    for name, ratio, make in configs():
        maxs = {"sum": [], "mean": []}
        ests = {"sum": [], "mean": []}
        nseg = 0
        for s in SEEDS:
            rng = np.random.default_rng(50000 + s)
            mid, nrm = S.polyline_segments(make(rng))
            mid, nrm = thin(mid, nrm, ratio, rng)
            nseg = len(mid)
            ms, ns, _ = ve.sample(mid, nrm, 60000 + s)
            sm, mn = both_fields(lattice, ms, ns)
            maxs["sum"].append(lattice[int(np.argmax(sm))])
            maxs["mean"].append(lattice[int(np.argmax(mn))])
            ests["sum"].append(ve.estimate(mid, nrm, W, H, 60000 + s, False)[0])
            ests["mean"].append(ve.estimate(mid, nrm, W, H, 60000 + s, True)[0])
        left = int((mid[:, 0] < C[0]).sum())
        for obj in ("sum", "mean"):
            row = dict(section=name, density_ratio=ratio, objective=obj, n_seeds=len(SEEDS),
                       segments=nseg, segments_sparse_side=left, lattice_step=STEP,
                       lattice_half=HALF)
            row.update({f"fieldmax_{k}": v for k, v in summarise(np.array(maxs[obj])).items()})
            row.update({f"estimate_{k}": v for k, v in summarise(np.array(ests[obj])).items()})
            rows.append(row)
            print(f"  {name:14s} {obj:4s} field max err {row['fieldmax_err_median_units']:7.1f} "
                  f"dx {row['fieldmax_dx_median_units']:7.1f}   estimate err "
                  f"{row['estimate_err_median_units']:7.1f} dx {row['estimate_dx_median_units']:7.1f}"
                  f"   ({time.perf_counter() - t0:.0f}s)", flush=True)
    L.write_csv(os.path.join(L.EV, "synthetic-density.csv"), list(rows[0]), rows)


if __name__ == "__main__":
    main()
