#!/usr/bin/env python3
"""align.py: best-windows-0826 DECLARATION.md addition 2026-09-29T06:23:23Z (director 06:21:28Z). New file, coordinator
agent. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran. Imports bw.py (and through it certified-piece-0826 fibre2.py's sheet loader) unchanged.

    align.py angles                 -> evidence/angles.csv (every clean window of windows.csv and seed5364 C40 S0's certified square)
    align.py resample <tag>         -> scratch/aligned/<tag>.bin (reader's patch format) and .npz, one row of evidence/aligned.csv
    align.py targets                prints the targets (tag label i0 j0 cells_i cells_j what)

Targets: the best 3 of windows.csv (tag bw<rank>) and «cert5364» = C40-PHerc0826-seed5364-S0's certified square
(square20-0826-95 certified-squares.csv corner and cells).
"""
import csv, json, math, os, subprocess, sys, time
import numpy as np
from scipy import ndimage

HERE = "/data/scrollagent/runs/rev1/best-windows-0826"
sys.path.insert(0, HERE + "/tools")
import bw  # noqa: E402
F2 = bw.F2
TOOL = "best-windows-0826/tools/align.py"
OUTA = HERE + "/scratch/aligned"
MARG = 64
NM = bw.NM
CERT = "/data/scrollagent/runs/rev1/square20-0826-95/evidence/certified-squares.csv"


def now():
    return bw.now()


def windows():
    return list(csv.DictReader(l for l in open(HERE + "/evidence/windows.csv") if not l.startswith("#")))


def targets(all_clean=False):
    T = []
    for r in windows():
        if not r["rank"]:
            continue
        if all_clean or r["best3"]:
            tag = "bw%s" % r["rank"]
            T.append(dict(tag=tag, label=r["label"], i0=int(r["i0"]), j0=int(r["j0"]), ci=int(r["cells_i"]), cj=int(r["cells_j"]),
                          what="clean window rank %s%s" % (r["rank"], (", " + r["best3"]) if r["best3"] else "")))
    c = [r for r in bw.rows(CERT) if r["source"] == "C40" and r["seed"] == "PHerc0826-seed5364" and r["sheet"] == "0"][0]
    n = int(c["certified_square_cells"])
    T.append(dict(tag="cert5364", label="C40-PHerc0826-seed5364-S0", i0=int(c["certified_corner_i"]), j0=int(c["certified_corner_j"]),
                  ci=n, cj=n, what="certified square %s mm (certified-squares.csv)" % c["certified_square_mm"]))
    return T


def sheet_points(label):
    rec, IDX, piece, si, sj, bbox, msrc, CI, CJ = F2.load_sheet(label)
    ni, nj = IDX.shape
    P = np.full((ni, nj, 3), np.nan)
    P[CI, CJ, 0], P[CI, CJ, 1], P[CI, CJ, 2] = rec["px"], rec["py"], rec["pz"]
    return P, IDX >= 0, si, sj


def angle_stats(P, V, i0, j0, ci, cj, axis):
    W = P[i0:i0 + ci, j0:j0 + cj]; M = V[i0:i0 + ci, j0:j0 + cj]
    if axis == 0:
        d = W[1:] - W[:-1]; ok = M[1:] & M[:-1]
    else:
        d = W[:, 1:] - W[:, :-1]; ok = M[:, 1:] & M[:, :-1]
    d = d[ok]
    a = np.degrees(np.arccos(np.clip(np.abs(d[:, 2]) / np.linalg.norm(d, axis=1), 0, 1)))
    q = np.percentile(a, [25, 50, 75])
    return q[1], q[2] - q[0], len(a), float(np.median(np.linalg.norm(d, axis=1)))


def angles():
    rows = []
    cache = {}
    for t in targets(all_clean=True):
        if t["label"] not in cache:
            cache.clear(); cache[t["label"]] = sheet_points(t["label"])
        P, V, si, sj = cache[t["label"]]
        mi, qi, ni_, hi = angle_stats(P, V, t["i0"], t["j0"], t["ci"], t["cj"], 0)
        mj, qj, nj_, hj = angle_stats(P, V, t["i0"], t["j0"], t["ci"], t["cj"], 1)
        rows.append([t["tag"], t["label"], t["what"], t["i0"], t["j0"], t["ci"], t["cj"], "%.2f" % mi, "%.2f" % qi, ni_, "%.2f" % mj,
                     "%.2f" % qj, nj_, "%.4f" % hi, "%.4f" % hj])
        print(rows[-1], flush=True)
    with open(HERE + "/evidence/angles.csv", "w", newline="") as f:
        f.write("# written by %s angles at %s: per window, the acute angle between the line of each lattice step (i: p(i+1,j)-p(i,j), "
                "j: p(i,j+1)-p(i,j), both cells covered) and the scan's z axis, degrees; median and IQR (q75 - q25) over the window's "
                "cells; step_*_vox = median 3D length of the step; DECLARATION.md addition 2026-09-29T06:23:23Z\n" % (TOOL, now()))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tag", "label", "what", "i0", "j0", "cells_i", "cells_j", "angle_i_to_z_median", "angle_i_to_z_iqr", "steps_i",
                    "angle_j_to_z_median", "angle_j_to_z_iqr", "steps_j", "step_i_vox", "step_j_vox"])
        w.writerows(rows)


# ---------------------------------------------------------------- resampling
class Field:
    def __init__(self, P, V):
        # holes filled for the tracing only: normalized Gaussian convolution at sigma 2, then 8, then 32 cells where still empty
        w = V.astype(np.float64)
        Pf = np.where(V[..., None], P, np.nan)
        for sg in (2.0, 8.0, 32.0):
            sw = ndimage.gaussian_filter(w, sg)
            for c in range(3):
                s = ndimage.gaussian_filter(np.where(V, P[..., c], 0.0), sg)
                with np.errstate(invalid="ignore", divide="ignore"):
                    Pf[..., c] = np.where(np.isfinite(Pf[..., c]), Pf[..., c], np.where(sw > 1e-3, s / sw, np.nan))
        # the tracing runs on the filled field smoothed at sigma 1.5 cells (the lattice points jitter by about a voxel); the
        # resampled points are read from the unsmoothed filled field (Praw) at the traced parameters
        self.Praw = Pf
        Pf = np.stack([ndimage.gaussian_filter(np.nan_to_num(Pf[..., c], nan=0.0), 1.5) /
                       np.maximum(ndimage.gaussian_filter(np.isfinite(Pf[..., c]).astype(float), 1.5), 1e-9) for c in range(3)], -1)
        Pf[~np.isfinite(self.Praw).all(-1)] = np.nan
        self.P = Pf
        self.Pi = np.stack([np.gradient(Pf[..., c], axis=0) for c in range(3)], -1)
        self.Pj = np.stack([np.gradient(Pf[..., c], axis=1) for c in range(3)], -1)
        self.V = V
        self.shape = V.shape

    def at(self, A, i, j):
        co = np.vstack([i, j])
        return np.stack([ndimage.map_coordinates(A[..., c], co, order=1, mode="constant", cval=np.nan) for c in range(A.shape[-1])], -1)

    def local(self, i, j):
        p = self.at(self.P, i, j); pi = self.at(self.Pi, i, j); pj = self.at(self.Pj, i, j)
        zi, zj = pi[:, 2], pj[:, 2]
        g11 = (pi * pi).sum(1); g12 = (pi * pj).sum(1); g22 = (pj * pj).sum(1)
        det = g11 * g22 - g12 * g12
        # surface gradient direction of z in parameter space: G^-1 grad z
        di = (g22 * zi - g12 * zj) / det; dj = (-g12 * zi + g11 * zj) / det
        return p, pi, pj, zi, zj, di, dj


def origins(Fd, ic, jc, zc, dz, nup, ndn):
    """Steepest ascent curve of z on the sheet through (ic, jc): parameter points at z = zc + v dz, v = -ndn..nup."""
    out = {0: (float(ic), float(jc))}
    for sgn, n in ((1, nup), (-1, ndn)):
        i, j = np.array([float(ic)]), np.array([float(jc)])
        for v in range(1, n + 1):
            target = zc + sgn * v * dz
            for _ in range(8):  # sub steps: move toward target along G^-1 grad z
                p, pi, pj, zi, zj, di, dj = Fd.local(i, j)
                if not np.isfinite(p).all() or not np.isfinite(di).all():
                    break
                t = (target - p[0, 2]) / (zi * di + zj * dj)
                t = np.clip(t, -2.0, 2.0) if False else t
                step = np.hypot(t * di, t * dj)
                if step[0] > 1.0:
                    t = t / step[0]
                i, j = i + t * di, j + t * dj
                if abs(float(target - p[0, 2])) < 1e-3:
                    break
            p = Fd.at(Fd.P, i, j)
            if not np.isfinite(p).all():
                break
            out[sgn * v] = (float(i[0]), float(j[0]))
    return out


def trace_rows(Fd, org, zc, dz, h, nk):
    """For each row v with an origin, trace the contour z = z_v both ways; return dict v -> (u array, i array, j array)."""
    vs = sorted(org)
    zt = np.array([zc + v * dz for v in vs])
    res = {}
    hs = h / 4.0
    nsteps = int(math.ceil((nk + 2) * h / hs))
    for sgn in (1, -1):
        i = np.array([org[v][0] for v in vs]); j = np.array([org[v][1] for v in vs])
        alive = np.ones(len(vs), bool)
        U = [np.zeros(len(vs))]; Is = [i.copy()]; Js = [j.copy()]
        u = np.zeros(len(vs))
        for n in range(nsteps):
            p, pi, pj, zi, zj, di, dj = Fd.local(i, j)
            ti, tj = -zj * sgn, zi * sgn
            sp = np.linalg.norm(pi * ti[:, None] + pj * tj[:, None], axis=1)
            ok = alive & np.isfinite(sp) & (sp > 1e-9)
            f = np.where(ok, hs / np.where(ok, sp, 1), 0)
            i2, j2 = i + f * ti, j + f * tj
            # Newton back onto z_v
            for _ in range(3):
                p2, pi2, pj2, zi2, zj2, di2, dj2 = Fd.local(i2, j2)
                t = (zt - p2[:, 2]) / (zi2 * di2 + zj2 * dj2)
                i2, j2 = i2 + np.where(ok & np.isfinite(t), t * di2, 0), j2 + np.where(ok & np.isfinite(t), t * dj2, 0)
            p3 = Fd.at(Fd.P, i2, j2)
            dl = np.linalg.norm(p3 - p, axis=1)
            # guard (addition 06:3xZ): a step that jumps (3D length over 2 x the step) or does not land on its z level (0.5 voxel)
            # ends the row's trace there
            ok2 = ok & np.isfinite(dl) & (dl < 2 * hs) & (np.abs(p3[:, 2] - zt) < 0.5)
            alive = ok2
            u = u + np.where(ok2, dl, 0)
            i, j = np.where(ok2, i2, i), np.where(ok2, j2, j)
            U.append(np.where(ok2, u, np.nan)); Is.append(i.copy()); Js.append(j.copy())
            if not alive.any():
                break
        U = np.array(U); Is = np.array(Is); Js = np.array(Js)
        for n, v in enumerate(vs):
            m = np.isfinite(U[:, n])
            res.setdefault(v, {})[sgn] = (U[m, n], Is[m, n], Js[m, n])
    return res


def resample_grid(Fd, ic, jc, h, dz, half):
    nk = half
    zc = float(Fd.P[ic, jc, 2])
    org = origins(Fd, ic, jc, zc, dz, half, half)
    tr = trace_rows(Fd, org, zc, dz, h, nk)
    n = 2 * half + 1
    GI = np.full((n, n), np.nan); GJ = np.full((n, n), np.nan)
    for v, d in tr.items():
        for sgn, (U, I, J) in d.items():
            ks = np.arange(0, nk + 1)
            uk = ks * h
            m = uk <= (U[-1] if len(U) else -1)
            if len(U) < 2:
                continue
            ii = np.interp(uk[m], U, I); jj = np.interp(uk[m], U, J)
            cols = half + sgn * ks[m]
            GI[half + v, cols] = ii; GJ[half + v, cols] = jj   # row index = half + v (z grows with the row)
    return GI, GJ, zc, len(org)


def resample(tag):
    os.makedirs(OUTA, exist_ok=True)
    t0 = time.time()
    T = {t["tag"]: t for t in targets(all_clean=True)}[tag]
    L = T["label"]
    P, V, si, sj = sheet_points(L)
    z, src, si, sj = bw.masks(L)
    flag = bw.flag_of(z)
    S = max(T["ci"], T["cj"])
    half = S // 2 + MARG
    ic, jc = T["i0"] + T["ci"] // 2, T["j0"] + T["cj"] // 2
    if not V[ic, jc]:
        ii, jj = np.nonzero(V); k = np.argmin((ii - ic) ** 2 + (jj - jc) ** 2); ic, jc = int(ii[k]), int(jj[k])
    R = int(half * 1.8) + 10
    a0, a1, b0, b1 = max(0, ic - R), min(V.shape[0], ic + R), max(0, jc - R), min(V.shape[1], jc + R)
    Fd = Field(P[a0:a1, b0:b1], V[a0:a1, b0:b1])
    Wn = P[T["i0"]:T["i0"] + T["ci"], T["j0"]:T["j0"] + T["cj"]]; Mw = V[T["i0"]:T["i0"] + T["ci"], T["j0"]:T["j0"] + T["cj"]]
    h = float(np.median(np.concatenate([np.linalg.norm((Wn[1:] - Wn[:-1])[Mw[1:] & Mw[:-1]], axis=1),
                                        np.linalg.norm((Wn[:, 1:] - Wn[:, :-1])[Mw[:, 1:] & Mw[:, :-1]], axis=1)])))
    dz = h
    GI, GJ, zc, norg = resample_grid(Fd, ic - a0, jc - b0, h, dz, half)
    Q = Fd.at(Fd.Praw, GI.ravel(), GJ.ravel()).reshape(GI.shape + (3,))
    dv = np.linalg.norm(Q[1:] - Q[:-1], axis=-1); dv = dv[np.isfinite(dv)]
    med1 = float(np.median(dv))
    dz2 = h * h / med1
    GI, GJ, zc, norg = resample_grid(Fd, ic - a0, jc - b0, h, dz2, half)
    Q = Fd.at(Fd.Praw, GI.ravel(), GJ.ravel()).reshape(GI.shape + (3,))
    dv = np.linalg.norm(Q[1:] - Q[:-1], axis=-1); dv = dv[np.isfinite(dv)]
    du = np.linalg.norm(Q[:, 1:] - Q[:, :-1], axis=-1); du = du[np.isfinite(du)]
    # validity: nearest lattice cell covered
    fin = np.isfinite(GI) & np.isfinite(Q).all(-1)
    NI_ = np.full(GI.shape, -1); NJ_ = np.full(GI.shape, -1)
    NI_[fin] = np.rint(GI[fin]).astype(int) + a0; NJ_[fin] = np.rint(GJ[fin]).astype(int) + b0
    inb = fin & (NI_ >= 0) & (NI_ < V.shape[0]) & (NJ_ >= 0) & (NJ_ < V.shape[1])
    val = np.zeros(GI.shape, bool); val[inb] = V[NI_[inb], NJ_[inb]]
    # guard: a resampled point off its z level by more than 2 voxels (unsmoothed point far from the smoothed trace) is dropped
    zoff = np.abs(Q[..., 2] - (zc + (np.arange(GI.shape[0]) - half)[:, None] * dz2))
    off = val & ~(zoff <= 2.0)
    n_off = int(off.sum()); val &= ~off
    fl = np.zeros(GI.shape, bool); fl[inb] = flag[NI_[inb], NJ_[inb]]
    zdev = np.abs(Q[..., 2] - (zc + (np.arange(GI.shape[0]) - half)[:, None] * dz2))[val]
    # the aligned square: centred, side S, corner at (half - S//2) both ways
    c0 = half - S // 2
    sq = (slice(c0, c0 + S), slice(c0, c0 + S))
    n2 = S * S
    # inside the lattice window?
    inwin = np.zeros(GI.shape, bool)
    inwin[inb] = (NI_[inb] >= T["i0"]) & (NI_[inb] < T["i0"] + T["ci"]) & (NJ_[inb] >= T["j0"]) & (NJ_[inb] < T["j0"] + T["cj"])
    # records: x = column (u), y = row (v, z grows with y); shift so both start at 0
    yy, xx = np.nonzero(val)
    x0, y0 = int(xx.min()), int(yy.min())
    rec = np.zeros(len(xx), dtype=bw.PT.POINT)
    rec["x"] = xx - x0; rec["y"] = yy - y0
    rec["px"], rec["py"], rec["pz"] = Q[yy, xx, 0], Q[yy, xx, 1], Q[yy, xx, 2]
    rec.tofile(OUTA + "/%s.bin.part" % tag); os.replace(OUTA + "/%s.bin.part" % tag, OUTA + "/%s.bin" % tag)
    np.savez_compressed(OUTA + "/%s.npz" % tag, Q=Q.astype(np.float32), valid=val, flag=fl, inwin=inwin, NI=NI_, NJ=NJ_,
                        v2=np.where(inb, z["v2"][np.clip(NI_, 0, V.shape[0] - 1), np.clip(NJ_, 0, V.shape[1] - 1)], False) & val,
                        sc=np.where(inb, (z["self_conflict"] | z["b_end"])[np.clip(NI_, 0, V.shape[0] - 1), np.clip(NJ_, 0, V.shape[1] - 1)], False) & val,
                        a2r=np.where(inb, z["a2_rule"][np.clip(NI_, 0, V.shape[0] - 1), np.clip(NJ_, 0, V.shape[1] - 1)], False) & val,
                        half=half, S=S, x0=x0, y0=y0, c0=c0)
    row = dict(tag=tag, label=L, what=T["what"], S=S, grid=GI.shape[0], margin=MARG, centre_cell="%d %d" % (ic, jc),
               centre_z="%.2f" % zc, h_vox="%.4f" % h, dz_first=("%.4f" % dz), median_row_step_first="%.4f" % med1,
               dz_final="%.4f" % dz2, median_row_step_vox="%.4f" % float(np.median(dv)), median_col_step_vox="%.4f" % float(np.median(du)),
               rows_with_origin=norg, z_deviation_max_vox="%.4f" % float(zdev.max()), z_deviation_median_vox="%.4f" % float(np.median(zdev)),
               square_corner_x=c0 - x0, square_corner_y=c0 - y0, grid_ni=int(rec["x"].max()) + 1, grid_nj=int(rec["y"].max()) + 1,
               points=len(rec), points_dropped_off_z=n_off, step_mm="%.6f" % min(si, sj),
               square_covered_share="%.6f" % (val[sq].sum() / n2), square_flagged_share="%.6f" % (fl[sq].sum() / n2),
               square_in_lattice_window_share="%.6f" % (inwin[sq].sum() / n2), seconds=round(time.time() - t0, 1))
    p = HERE + "/evidence/aligned.csv"
    new = not os.path.isfile(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write("# written by %s resample: one row per target; grid v = scan z (row), u = 3D arc length at constant z (column), "
                    "u = 0 on the steepest ascent curve through the centre; dz_final = h^2 / median row step of a first pass; shares of "
                    "the centred aligned square of side S read in the nearest lattice cell's masks; square_corner_x/y and grid_ni/nj in "
                    "the patch file's own x/y (the reader's I0 J0 NI NJ); DECLARATION.md addition 2026-09-29T06:23:23Z\n" % TOOL)
        w = csv.DictWriter(f, list(row), lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow(row)
    print(json.dumps(row), flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "angles":
        angles()
    elif a[0] == "resample":
        resample(a[1])
    elif a[0] == "targets":
        for t in targets(all_clean=len(a) > 1):
            print(t["tag"], t["label"], t["i0"], t["j0"], t["ci"], t["cj"])
