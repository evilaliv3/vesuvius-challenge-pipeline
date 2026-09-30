#!/usr/bin/env python3
"""positive-control-0139/tools/score.py SURF VAR OTHER_SURF OTHER_VAR: rows of evidence/control.csv for one surface and
variant (DECLARATION.md «Scoring»). Written 2026-09-29 by an agent of the coordinator.

Every clean label point (scratch/labels-9362.npz) is matched to the render pixel of the surface whose 3D point
(score_ink_0139.points_at: pixel (i, j) at grid coordinate s (i + 0.5), s (j + 0.5), bilinear) is nearest, if within k
voxels (k = 2, 4) and the pixel is inside the render mask. The common region at k = label points matched at k by this
surface AND by OTHER (theirs lattice for ours; the named ours surface for theirs). Each back turned prediction
(scratch/SURF/VAR/p/<dir>-k<K>m<M>-<ckpt>.tif) is read at the matched pixels; score_ink_0139.ba_auc (ba at uint8 >= 128,
AUC ties one half, «not measurable» under 2,000 ink or no ink). ba on the surface's own matched set as a column.
"""
import csv, os, subprocess, sys
import numpy as np
import tifffile
from scipy.spatial import cKDTree

S = "/data/scrollagent/runs/rev1/positive-control-0139"
sys.path.insert(0, "/data/scrollagent/runs/rev1/squares-ink-1447/tools")
os.environ.setdefault("SA_EVIDENCE", S + "/evidence")
import score_ink_0139 as SC  # noqa: E402
TOOL = "positive-control-0139/tools/score.py"
HDR = ["tool", "time", "surface", "variant", "orientation_k", "orientation_m", "direction", "checkpoint", "k_vox",
       "ba", "auc", "n_common", "n_common_ink", "n_common_noink", "common_with", "ba_own", "auc_own", "n_own", "n_own_ink",
       "lamina_shift_vox", "centring", "surface_tifxyz", "prediction", "caveat"]
CAVEAT = ("clean held out region of pherc0139-w016 (0.1581 cm2), the organisers' online validation case during training; "
          "labels mapped from the 2.399 um grid by the affine of evidence/label-map.csv")


def now():
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True, check=True).stdout.strip()


def matched(surf, var, q):
    d = os.path.join(S, "scratch", surf, var)
    sf = os.path.join(d, "surface.txt")
    st = open(sf).read().strip() if os.path.exists(sf) else (
        os.path.join(S, "scratch", surf, "window.tifxyz") if var in ("lattice", "c", "d") else os.path.join(d, "surf.tifxyz"))
    P, V, s = SC.load_grid(st)
    m = tifffile.imread(os.path.join(d, "mask.tif")) > 0
    I, J = np.nonzero(m)
    pts, ok = SC.points_at(P, V, s, I, J)
    I, J, pts = I[ok], J[ok], pts[ok]
    dist, idx = cKDTree(pts).query(q, distance_upper_bound=6.0, workers=2)
    hit = np.isfinite(dist)
    pi = np.full(len(q), -1); pj = np.full(len(q), -1)
    pi[hit] = I[idx[hit]]; pj[hit] = J[idx[hit]]
    return st, dist, pi, pj


def main():
    surf, var, osurf, ovar = sys.argv[1:5]
    L = np.load(S + "/scratch/labels-9362.npz")
    q = L["p"].astype(np.float64); ink = L["ink"].astype(bool)
    st, dist, pi, pj = matched(surf, var, q)
    _, odist, _, _ = matched(osurf, ovar, q)
    shifts = {}
    sp = os.path.join(S, "evidence", "reads", f"{surf}-{var}", "shifts.txt")
    for line in open(sp):
        f = line.rstrip("\n").split(",")
        shifts[f[2]] = (f[3], f[6] if len(f) > 6 else "")
    out = os.environ.get("SCORE_OUT", os.path.join(S, "evidence", "control.csv"))
    new = not os.path.exists(out)
    rows = []
    for direction in ("forward", "reverse"):
        for K in range(4):
            for M in range(2):
                for ck in ("seed42", "seed43"):
                    pf = os.path.join(S, "scratch", surf, var, "p", f"{direction}-k{K}m{M}-{ck}.tif")
                    if not os.path.exists(pf):
                        continue
                    pr = tifffile.imread(pf)
                    for k in (2, 4):
                        own = dist <= k
                        com = own & (odist <= k)
                        vo = pr[pi[own], pj[own]]; vc = pr[pi[com], pj[com]]
                        ba, auc = SC.ba_auc(vc, ink[com])
                        bao, auco = SC.ba_auc(vo, ink[own])
                        rows.append([TOOL, now(), surf, var, K, M, direction, ck, k, ba, auc, int(com.sum()),
                                     int((com & ink).sum()), int((com & ~ink).sum()), f"{osurf} {ovar}", bao, auco,
                                     int(own.sum()), int((own & ink).sum()), shifts[direction][0], shifts[direction][1], st,
                                     os.path.relpath(pf, S), CAVEAT])
    with open(out, "a", newline="") as f:
        if new:
            f.write(f'"# written by {TOOL}; one row per surface x variant x orientation (k quarter turns, m mirror, tf.py) x direction x checkpoint x match radius k; ba = balanced accuracy at uint8 >= 128 on the common region (clean held out label pixels matched within k voxels by both surfaces); DECLARATION.md"\n')
            csv.writer(f).writerow(HDR)
        csv.writer(f).writerows(rows)
    b = [r for r in rows if r[8] == 4 and r[9] != "not measurable"]
    best = max(b, key=lambda r: float(r[9])) if b else None
    print(f"{surf} {var}: {len(rows)} rows; best k4 ba", best[9] if best else "none",
          f"(k {best[4]} m {best[5]} {best[6]} {best[7]}, n_common {best[11]})" if best else "")


if __name__ == "__main__":
    main()
