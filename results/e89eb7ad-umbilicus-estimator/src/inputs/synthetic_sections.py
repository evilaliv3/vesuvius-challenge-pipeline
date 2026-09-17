"""P5: synthetic cross sections with a centre known by construction.

Here the answer is known, so the word is ERROR, not distance. Seven families, each with one
parameter made to grow, and the breaking point declared before running: the first value of the
parameter at which the median error over 20 seeds exceeds 200 grid units, which is 1.87 mm at
9.362 um, the order of the distance the fixed estimator has on a real scroll.

Family A, perfect concentric circles, is the paired known reference: a variant that misses the
centre of concentric circles has a broken bench, and nothing else in the table may be read.
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core

W = H = 8000.0
CX = CY = 4000.0
ARC = 12.0                    # target spacing between consecutive points, in grid units
RADII = np.arange(300.0, 3501.0, 80.0)
SEEDS = range(20)
BREAK_UNITS = 200.0
MM = 0.009362                 # a level 0 scroll at 9.362 um, one grid unit per voxel


def polyline_segments(polys):
    """Midpoints and unit normals, the way normalgridtools.cpp:33-63 builds them."""
    mids, nrms = [], []
    for p in polys:
        p = np.asarray(p, float)
        if len(p) < 2:
            continue
        a, b = p[:-1], p[1:]
        t = b - a
        ln = np.hypot(t[:, 0], t[:, 1])
        ok = ln > 0
        a, b, t, ln = a[ok], b[ok], t[ok], ln[ok]
        if not len(a):
            continue
        t = t / ln[:, None]
        mids.append((a + b) * 0.5)
        nrms.append(np.stack([-t[:, 1], t[:, 0]], 1))
    return np.concatenate(mids), np.concatenate(nrms)


def circles(cx, cy, ratio=1.0, frac=1.0, noise=0.0, rng=None, radii=RADII):
    out = []
    for r in radii:
        n = max(8, int(2 * np.pi * r / ARC))
        th = np.linspace(0, 2 * np.pi * frac, max(3, int(n * frac)), endpoint=(frac >= 1.0))
        x = cx + r * np.cos(th)
        y = cy + (r / ratio) * np.sin(th)
        if noise:
            x = x + rng.normal(0, noise, len(th))
            y = y + rng.normal(0, noise, len(th))
        out.append(np.stack([x, y], 1))
    return out


def spiral(cx, cy, pitch):
    r0, r1 = 300.0, 3500.0
    turns = (r1 - r0) / pitch
    th = np.linspace(0, 2 * np.pi * turns, max(100, int(2 * np.pi * turns * r1 / ARC)))
    r = r0 + pitch * th / (2 * np.pi)
    return [np.stack([cx + r * np.cos(th), cy + r * np.sin(th)], 1)]


def configs():
    yield "A concentric circles", "none", 0.0, (CX, CY), lambda rng: circles(CX, CY)
    for e in (1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0):
        yield "B ellipses", "axis ratio", e, (CX, CY), (lambda rng, e=e: circles(CX, CY, ratio=e))
    for p in (40.0, 80.0, 160.0, 320.0):
        yield "C spiral", "pitch", p, (CX, CY), (lambda rng, p=p: spiral(CX, CY, p))
    for f in (1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1):
        yield "D partial arcs", "angular fraction", f, (CX, CY), (lambda rng, f=f: circles(CX, CY, frac=f))
    for s in (0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0):
        yield "E position noise", "sigma units", s, (CX, CY), (lambda rng, s=s: circles(CX, CY, noise=s, rng=rng))
    for d in (0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99):
        yield "F missing segments", "fraction removed", d, (CX, CY), (lambda rng: circles(CX, CY))
    for g in (0.0, 500.0, 1000.0, 2000.0, 3000.0, 3800.0):
        yield ("G centre away from the middle", "distance from the middle of the frame", g,
               (CX + g / np.sqrt(2), CY + g / np.sqrt(2)),
               (lambda rng, g=g: circles(CX + g / np.sqrt(2), CY + g / np.sqrt(2))))


def main():
    rows = []
    for fam, pname, pval, truth, make in configs():
        drop = pval if fam.startswith("F") else 0.0
        errs = {True: [], False: []}
        for seed in SEEDS:
            rng = np.random.default_rng(50000 + seed)
            mid, nrm = polyline_segments(make(rng))
            if drop:
                keep = rng.random(len(mid)) >= drop
                if keep.sum() < 50:
                    keep[rng.choice(len(mid), 50, replace=False)] = True
                mid, nrm = mid[keep], nrm[keep]
            for divide in (True, False):
                xy, cap = core.estimate(mid, nrm, W, H, 60000 + seed, divide)
                errs[divide].append(np.hypot(xy[0] - truth[0], xy[1] - truth[1]))
        row = dict(family=fam, parameter=pname, value=pval, n_seeds=len(SEEDS),
                   segments=int(len(mid)))
        for divide, tag in ((True, "as_is"), (False, "no_division")):
            e = np.array(errs[divide])
            row[f"median_units_{tag}"] = round(float(np.median(e)), 1)
            row[f"median_mm_{tag}"] = round(float(np.median(e)) * MM, 3)
            row[f"p90_units_{tag}"] = round(float(np.percentile(e, 90)), 1)
            row[f"broken_{tag}"] = int(np.median(e) > BREAK_UNITS)
        rows.append(row)
        print(fam, pname, pval, "as is", row["median_units_as_is"],
              "sum", row["median_units_no_division"], flush=True)
    out = os.path.join(os.path.dirname(HERE), "evidence", "synthetic-sections.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("written", out)


if __name__ == "__main__":
    main()
