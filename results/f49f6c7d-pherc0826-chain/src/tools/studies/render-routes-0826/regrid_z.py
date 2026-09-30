#!/usr/bin/env python3
"""regrid_z.py (FIGURES ONLY, never a number: director 2026-09-29T07:22:16Z; self test T2 failed its first declared bar, 0.622
against 0.5 degrees, run 06:47:32Z; state it in any caption): resample a sheet on the grid v = the scan's z, u = arc length along the sheet at constant z
(render-routes-0826 DECLARATION.md, "The regridding tool"; coordinator's addition of 2026-09-29T06:38:48Z). Standalone:
numpy, scipy, tifffile only. New file, coordinator agent, 2026-09-29.

    regrid_z.py selftest
        synthetic cases T1..T4 -> <study>/evidence/regrid-selftest.csv; exits 3 on a fail. Every other mode refuses unless
        the last selftest row set in that file passed.
    regrid_z.py run --input PATCH_BIN|TIFXYZ_DIR --umbilicus JSON --out TIFXYZ_DIR
                    [--box I0 I1 J0 J1] [--mask NPZ:ARRAY] [--fit spline|none] [--knot-mm 0.5] [--voxel-um 9.362]
                    [--h H] [--side N] [--centre I J] [--label L] [--csv CSV] [--max-dist-3d D]
        --box      inclusive index box of the INPUT grid (lattice i, j; tifxyz rows, cols) whose nodes enter the model
        --mask     only nodes where this boolean array (input grid shape) is true enter the model (e.g. a certified piece)
        --fit      spline: cubic tensor B spline r(a, z) with interior knots every --knot-mm on both axes (least squares,
                   ridge 1e-6 x mean diagonal); none: r linear on the Delaunay triangulation of the nodes in (a, z)
        --h        output step in voxels (default: median 3D distance between valid input neighbours along the first axis)
        --side     output grid side in nodes (default: the box's larger side + 128)
        --centre   input node the grid is centred on (default: the valid model node nearest the box centre)
        Output: tifxyz (x.tif, y.tif, z.tif float32, -1 invalid; rows = v (z grows down the rows), columns = u), meta.json
        (scale 1/h), and OUT.npz (X, Y, Z, valid, src_i, src_j, h); one row appended to --csv (default
        <study>/evidence/regrid.csv).

Geometry. Umbilicus c(z): linear interpolation of the JSON's control points (x, y, z), constant beyond its ends. For a node
p: theta = atan2(y - cy(z), x - cx(z)) unwrapped about the circular mean of the model nodes, r = |p_xy - c(z)|,
a = r_med (theta - theta_c) (voxels; r_med the median r, theta_c the centre node's theta). Rows z_v = z_c + (v - n//2) h.
Along each row the model is sampled at a steps of h/4 over the data's a range, the 3D polyline's cumulative length s is
taken from a = 0 (theta_c), and u_k = (k - n//2) h is inverted to a by linear interpolation; the node is the model's point
at (a_k, z_v). A node is valid when the model is defined there and the nearest model node in (a, z) is within 1.5 h; it
records that nearest input node (src_i, src_j).
"""
import argparse, csv, json, os, shutil, subprocess, sys, time
import numpy as np
import tifffile
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.interpolate import BSpline, LinearNDInterpolator
from scipy.spatial import cKDTree

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = "render-routes-0826/tools/regrid_z.py"
SELFTEST = STUDY + "/evidence/regrid-selftest.csv"
NM = "not measurable"
POINT = np.dtype([("x", "<f4"), ("y", "<f4"), ("px", "<f4"), ("py", "<f4"), ("pz", "<f4")])


def utc():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()


# ------------------------------------------------------------------------------------------------ input and output
def read_patch(path):
    """our lattice (certified_region.lattice_from_patch's convention: i = rint(x - min x), j = rint(y - min y))."""
    rec = np.fromfile(path, dtype=POINT)
    if rec.size == 0:
        raise SystemExit("refuse: %s empty" % path)
    u, v = rec["x"].astype(np.float64), rec["y"].astype(np.float64)
    ci, cj = np.rint(u - u.min()).astype(np.int64), np.rint(v - v.min()).astype(np.int64)
    if max(np.abs(u - u.min() - ci).max(), np.abs(v - v.min() - cj).max()) > 0.01:
        raise SystemExit("refuse: %s is not on an integer lattice" % path)
    ni, nj = int(ci.max()) + 1, int(cj.max()) + 1
    P = np.full((ni, nj, 3), np.nan); V = np.zeros((ni, nj), bool)
    P[ci, cj, 0], P[ci, cj, 1], P[ci, cj, 2] = rec["px"], rec["py"], rec["pz"]
    V[ci, cj] = True
    if int(V.sum()) != rec.size:
        raise SystemExit("refuse: lattice collisions in %s" % path)
    return P, V


def read_tifxyz(d):
    P = np.stack([tifffile.imread(os.path.join(d, a + ".tif")).astype(np.float64) for a in "xyz"], -1)
    V = np.all(np.isfinite(P), -1) & ~np.any(P == -1, -1)
    P[~V] = np.nan
    return P, V


def read_input(path):
    if os.path.isdir(path):
        return read_tifxyz(path)
    return read_patch(path)


def write_tifxyz(out, P, V, h, extra):
    if os.path.exists(out):
        raise SystemExit("refuse: %s exists" % out)
    tmp = out + ".partial"
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for k, a in zip("xyz", np.moveaxis(P, -1, 0)):
        tifffile.imwrite(os.path.join(tmp, k + ".tif"), np.where(V, a, -1).astype(np.float32))
    meta = {"type": "seg", "uuid": os.path.basename(out.rstrip("/")), "format": "tifxyz", "scale": [1.0 / h, 1.0 / h],
            "made_by": TOOL}
    meta.update(extra)
    json.dump(meta, open(os.path.join(tmp, "meta.json"), "w"), indent=1)
    os.rename(tmp, out)


def umbilicus(path):
    d = json.load(open(path))
    cp = d["control_points"] if isinstance(d, dict) else d
    z = np.array([c["z"] for c in cp], float); x = np.array([c["x"] for c in cp], float); y = np.array([c["y"] for c in cp], float)
    o = np.argsort(z)
    return z[o], x[o], y[o]


def centre(U, z):
    uz, ux, uy = U
    return np.interp(z, uz, ux), np.interp(z, uz, uy)


# ------------------------------------------------------------------------------------------------ the models
def bspline_rows_fast(x, t, k=3):
    """vectorised: the k + 1 nonzero basis functions of a clamped knot vector t at x."""
    nb = len(t) - k - 1
    x = np.clip(x, t[k], t[-k - 1])
    span = np.searchsorted(t, x, side="right") - 1
    span = np.clip(span, k, nb - 1)
    # de Boor Cox for the k + 1 functions N_{span-k..span}
    N = np.zeros((len(x), k + 1)); N[:, 0] = 1.0
    left = np.zeros((len(x), k + 1)); right = np.zeros((len(x), k + 1))
    for j in range(1, k + 1):
        left[:, j] = x - t[span + 1 - j]
        right[:, j] = t[span + j] - x
        saved = np.zeros(len(x))
        for r in range(j):
            den = right[:, r + 1] + left[:, j - r]
            tmp = np.where(den > 0, N[:, r] / np.where(den > 0, den, 1), 0.0)
            N[:, r] = saved + right[:, r + 1] * tmp
            saved = left[:, j - r] * tmp
        N[:, j] = saved
    idx = span[:, None] - k + np.arange(k + 1)[None, :]
    return idx, N, nb


def knots(lo, hi, step):
    n = max(1, int(np.ceil((hi - lo) / step)))
    inner = lo + (hi - lo) * np.arange(1, n) / n if n > 1 else np.zeros(0)
    return np.concatenate([[lo] * 4, inner, [hi] * 4])


class SplineModel:
    def __init__(self, a, z, r, step):
        self.lo = (a.min(), z.min()); self.hi = (a.max(), z.max())
        self.ta = knots(a.min(), a.max(), step); self.tz = knots(z.min(), z.max(), step)
        ia, va, na = bspline_rows_fast(a, self.ta); iz, vz, nz = bspline_rows_fast(z, self.tz)
        self.na, self.nz = na, nz
        rows = np.repeat(np.arange(len(a)), 16)
        cols = (ia[:, :, None] * nz + iz[:, None, :]).reshape(-1)
        vals = (va[:, :, None] * vz[:, None, :]).reshape(-1)
        A = sparse.csr_matrix((vals, (rows, cols)), shape=(len(a), na * nz))
        AtA = (A.T @ A).tocsc()
        lam = 1e-6 * AtA.diagonal().mean()
        self.c = spsolve(AtA + lam * sparse.identity(na * nz, format="csc"), A.T @ r)
        self.knots_a = len(self.ta) - 8; self.knots_z = len(self.tz) - 8

    def __call__(self, a, z):
        out = np.full(a.shape, np.nan)
        ok = (a >= self.lo[0]) & (a <= self.hi[0]) & (z >= self.lo[1]) & (z <= self.hi[1])
        if ok.any():
            ia, va, _ = bspline_rows_fast(a[ok], self.ta); iz, vz, _ = bspline_rows_fast(z[ok], self.tz)
            cols = ia[:, :, None] * self.nz + iz[:, None, :]
            out[ok] = (self.c[cols] * va[:, :, None] * vz[:, None, :]).sum((1, 2))
        return out


class LinearModel:
    def __init__(self, a, z, r):
        self.f = LinearNDInterpolator(np.column_stack([a, z]), r)
        self.knots_a = self.knots_z = 0

    def __call__(self, a, z):
        return self.f(np.column_stack([a.ravel(), z.ravel()])).reshape(a.shape)


# ------------------------------------------------------------------------------------------------ the regridding
def angle_to_z(D):
    n = np.linalg.norm(D, axis=-1)
    return np.degrees(np.arccos(np.clip(np.abs(D[..., 2]) / n, 0, 1)))


def normals(P, ok):
    """unit normal per node from the cross product of central differences (one sided at the edges); NaN where undefined."""
    def diff(ax):
        D = np.full(P.shape, np.nan)
        sl = [slice(None)] * 2
        a = [slice(None)] * 2; b = [slice(None)] * 2
        a[ax] = slice(2, None); b[ax] = slice(None, -2); sl[ax] = slice(1, -1)
        D[tuple(sl)] = (P[tuple(a)] - P[tuple(b)]) / 2.0
        return D
    Di, Dj = diff(0), diff(1)
    N = np.cross(Di, Dj)
    n = np.linalg.norm(N, axis=-1, keepdims=True)
    N = N / np.where(n > 0, n, np.nan)
    N[~ok] = np.nan
    return N


def step_angles(P, ok, axis=0):
    """per node with a valid neighbour along `axis`: the 3D angle of the step to z (best-windows-0826 align.py's
    arccos(|d_z| / |d|)) and the in plane angle between the step and z projected on the tangent plane (the node's normal)."""
    if axis == 0:
        D = P[1:] - P[:-1]; m = ok[1:] & ok[:-1]; Nn = normals(P, ok)[:-1]
    else:
        D = P[:, 1:] - P[:, :-1]; m = ok[:, 1:] & ok[:, :-1]; Nn = normals(P, ok)[:, :-1]
    a3 = np.full(m.shape, np.nan); a3[m] = angle_to_z(D[m])
    ez = np.array([0.0, 0.0, 1.0])
    zt = ez[None, None, :] - Nn[..., 2:3] * Nn
    zn = np.linalg.norm(zt, axis=-1)
    dn = np.linalg.norm(D, axis=-1)
    c = np.abs((D * zt).sum(-1)) / (dn * zn)
    ai = np.degrees(np.arccos(np.clip(c, 0, 1)))
    ai[~m | ~np.isfinite(ai)] = np.nan
    return a3, ai


def regrid(P, V, U, box=None, mask=None, fit="spline", knot_vox=53.41, h=None, side=None, centre_ij=None, max_dist_3d=None):
    ni, nj = V.shape
    i0, i1, j0, j1 = box if box is not None else (0, ni - 1, 0, nj - 1)
    M = V.copy()
    inbox = np.zeros_like(M); inbox[i0:i1 + 1, j0:j1 + 1] = True
    M &= inbox
    if mask is not None:
        M &= mask
    if M.sum() < 100:
        raise SystemExit("refuse: %d model nodes" % int(M.sum()))
    if h is None:
        d = np.linalg.norm(P[1:] - P[:-1], axis=-1)[M[1:] & M[:-1]]
        h = float(np.median(d))
    II, JJ = np.nonzero(M)
    p = P[II, JJ]
    cx, cy = centre(U, p[:, 2])
    th = np.arctan2(p[:, 1] - cy, p[:, 0] - cx)
    ref = np.arctan2(np.sin(th).mean(), np.cos(th).mean())
    th = np.angle(np.exp(1j * (th - ref)))
    r = np.hypot(p[:, 0] - cx, p[:, 1] - cy)
    rmed = float(np.median(r))
    if centre_ij is None:
        ci, cj = (i0 + i1) / 2.0, (j0 + j1) / 2.0
    else:
        ci, cj = centre_ij
    k0 = int(np.argmin((II - ci) ** 2 + (JJ - cj) ** 2))
    thc, zc = th[k0], float(p[k0, 2])
    a = rmed * (th - thc)
    z = p[:, 2]
    model = SplineModel(a, z, r, knot_vox) if fit == "spline" else LinearModel(a, z, r)
    res = np.abs(model(a, z) - r)
    # fold check: (a, z) bins of h x h whose nodes spread in r by more than 2 h
    ba, bz = np.floor(a / h).astype(np.int64), np.floor(z / h).astype(np.int64)
    key = (ba - ba.min()) * (bz.max() - bz.min() + 1) + (bz - bz.min())
    o = np.argsort(key); ks = key[o]; rs = r[o]
    starts = np.r_[0, np.nonzero(np.diff(ks))[0] + 1]
    mx = np.maximum.reduceat(rs, starts); mn = np.minimum.reduceat(rs, starts)
    cnt = np.diff(np.r_[starts, len(ks)])
    fold_nodes = int(cnt[(mx - mn) > 2 * h].sum())
    # grid
    if side is None:
        side = max(i1 - i0 + 1, j1 - j0 + 1) + 128
    n = int(side)
    zv = zc + (np.arange(n) - n // 2) * h
    da = h / 4.0
    alo, ahi = a.min(), a.max()
    As = np.arange(np.floor(alo / da) * da, ahi + da, da)
    i_zero = int(np.argmin(np.abs(As)))
    AA, ZZ = np.meshgrid(As, zv)
    RR = model(AA, ZZ)
    TT = thc + AA / rmed + ref
    CX, CY = centre(U, ZZ)
    X3 = np.stack([CX + RR * np.cos(TT), CY + RR * np.sin(TT), ZZ], -1)
    seg = np.linalg.norm(X3[:, 1:] - X3[:, :-1], axis=-1)
    tree = cKDTree(np.column_stack([a, z]))
    uk = (np.arange(n) - n // 2) * h
    Aout = np.full((n, n), np.nan)
    for v in range(n):
        defined = np.isfinite(RR[v])
        if not defined[i_zero]:
            continue
        lo = i_zero
        while lo > 0 and defined[lo - 1]:
            lo -= 1
        hi = i_zero
        while hi < len(As) - 1 and defined[hi + 1]:
            hi += 1
        s = np.concatenate([[0.0], np.cumsum(seg[v, lo:hi])])
        s -= s[i_zero - lo]
        inside = (uk >= s[0]) & (uk <= s[-1])
        Aout[v, inside] = np.interp(uk[inside], s, As[lo:hi + 1])
    ZO = np.repeat(zv[:, None], n, 1)
    ok = np.isfinite(Aout)
    RO = np.full((n, n), np.nan)
    RO[ok] = model(Aout[ok], ZO[ok])
    ok &= np.isfinite(RO)
    dist, nn = tree.query(np.column_stack([np.where(ok, Aout, 0).ravel(), ZO.ravel()]), distance_upper_bound=1.5 * h)
    near = (np.isfinite(dist) & (nn < len(a))).reshape(n, n)
    ok &= near
    TO = thc + Aout / rmed + ref
    CXo, CYo = centre(U, ZO)
    PO = np.stack([CXo + RO * np.cos(TO), CYo + RO * np.sin(TO), ZO], -1)
    off3d = 0
    if max_dist_3d is not None:
        # addition 2026-09-29T07:33Z item 4: a node is valid only within max_dist_3d voxels (3D) of a model node, so a model
        # that leaves the sheet (folds, r not single valued) does not render texture that is not on the sheet
        d3, _ = cKDTree(p).query(np.where(ok[..., None], PO, 0).reshape(-1, 3))
        far = (d3.reshape(n, n) > max_dist_3d) & ok
        off3d = int(far.sum())
        ok &= ~far
    PO[~ok] = np.nan
    src_i = np.full((n, n), -1, np.int64); src_j = np.full((n, n), -1, np.int64)
    nnr = nn.reshape(n, n)
    src_i[ok] = II[nnr[ok]]; src_j[ok] = JJ[nnr[ok]]
    # output measures
    du = np.linalg.norm(PO[:, 1:] - PO[:, :-1], axis=-1)[ok[:, 1:] & ok[:, :-1]]
    dv3 = (PO[1:] - PO[:-1])[ok[1:] & ok[:-1]]
    a3, ai = step_angles(PO, ok, 0)
    ang = a3[np.isfinite(a3)]; angi = ai[np.isfinite(ai)]
    uz = U[0]
    stats = dict(fit=fit, knot_vox="%.2f" % knot_vox if fit == "spline" else "", knots_a=model.knots_a, knots_z=model.knots_z,
                 h_vox="%.4f" % h, r_med_vox="%.1f" % rmed, theta_span_deg="%.2f" % np.degrees(th.max() - th.min()),
                 z_span="%d..%d" % (int(z.min()), int(z.max())),
                 leaves_umbilicus_z_range="yes" if (z.min() < uz[0] or z.max() > uz[-1]) else "no",
                 nodes_in=int(len(a)), nodes_out_valid=int(ok.sum()), side=n,
                 resid_median_vox="%.4f" % np.median(res[np.isfinite(res)]), resid_p95_vox="%.4f" % np.percentile(res[np.isfinite(res)], 95),
                 resid_max_vox="%.4f" % np.nanmax(res),
                 spacing_u_median_vox="%.4f" % np.median(du) if du.size else NM,
                 spacing_v_median_vox="%.4f" % np.median(np.linalg.norm(dv3, axis=-1)) if dv3.size else NM,
                 row_step_angle_to_z_median_deg="%.3f" % np.median(ang) if ang.size else NM,
                 row_step_angle_to_z_iqr_deg="%.3f" % (np.percentile(ang, 75) - np.percentile(ang, 25)) if ang.size else NM,
                 row_step_inplane_angle_to_z_median_deg="%.3f" % np.median(angi) if angi.size else NM,
                 row_step_inplane_angle_to_z_iqr_deg="%.3f" % (np.percentile(angi, 75) - np.percentile(angi, 25)) if angi.size else NM,
                 fold_share="%.6f" % (fold_nodes / len(a)),
                 max_dist_3d="%.3f" % max_dist_3d if max_dist_3d is not None else "", nodes_dropped_off_sheet=off3d, centre_i=int(II[k0]), centre_j=int(JJ[k0]))
    return PO, ok, src_i, src_j, h, stats, dict(model=model, a=a, z=z, r=r, rmed=rmed, thc=thc, ref=ref)


REG_COLS = ["utc", "label", "input", "box", "mask", "fit", "knot_vox", "knots_a", "knots_z", "h_vox", "r_med_vox", "theta_span_deg",
            "z_span", "leaves_umbilicus_z_range", "nodes_in", "nodes_out_valid", "side", "resid_median_vox", "resid_p95_vox",
            "resid_max_vox", "spacing_u_median_vox", "spacing_v_median_vox", "row_step_angle_to_z_median_deg",
            "row_step_angle_to_z_iqr_deg", "row_step_inplane_angle_to_z_median_deg", "row_step_inplane_angle_to_z_iqr_deg", "fold_share", "max_dist_3d", "nodes_dropped_off_sheet", "centre_i", "centre_j", "out", "seconds"]


def append_csv(path, cols, row, head):
    new = not os.path.isfile(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="") as f:
        if new:
            f.write(head + "\n")
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(cols)
        w.writerow([row.get(c, "") for c in cols])


def selftest_passed():
    if not os.path.isfile(SELFTEST):
        return False
    R = list(csv.DictReader(l for l in open(SELFTEST) if not l.startswith("#")))
    if not R:
        return False
    last = R[-1]["run"]
    return all(r["passed"] == "yes" for r in R if r["run"] == last)


def run(args):
    if not selftest_passed():
        raise SystemExit("refuse: regrid_z selftest has not passed (%s)" % SELFTEST)
    t0 = time.time()
    P, V = read_input(args.input)
    mask = None
    if args.mask:
        f, k = args.mask.rsplit(":", 1)
        mask = np.load(f)[k].astype(bool)
        if mask.shape != V.shape:
            raise SystemExit("refuse: mask shape %s, input %s" % (mask.shape, V.shape))
    U = umbilicus(args.umbilicus)
    kv = args.knot_mm * 1000.0 / args.voxel_um
    PO, ok, si, sj, h, st, _ = regrid(P, V, U, tuple(args.box) if args.box else None, mask, args.fit, kv, args.h, args.side,
                                       tuple(args.centre) if args.centre else None, args.max_dist_3d)
    write_tifxyz(args.out, PO, ok, h, {"regrid_z": st, "source": os.path.abspath(args.input)})
    np.savez_compressed(args.out.rstrip("/") + ".npz", X=PO[..., 0], Y=PO[..., 1], Z=PO[..., 2], valid=ok, src_i=si, src_j=sj, h=h)
    row = dict(st, utc=utc(), label=args.label or os.path.basename(args.out.rstrip("/")), input=args.input,
               box=" ".join(map(str, args.box)) if args.box else "all", mask=args.mask or "", out=args.out,
               seconds="%.1f" % (time.time() - t0))
    append_csv(args.csv or STUDY + "/evidence/regrid.csv", REG_COLS, row,
               "# one row per regridding, written by %s run: grid v = scan z (rows), u = arc length at constant z (columns), "
               "step h voxels; resid = |r_model - r| at the model nodes; fold_share = model nodes in (a, z) bins of h x h "
               "whose r spread exceeds 2 h; angle = row step to z (median, IQR)" % TOOL)
    print(json.dumps(row))


# ------------------------------------------------------------------------------------------------ self test
def synth(fn_r, tilt_deg=2.0, rot_deg=30.0, step=4.0, n=500, r0=1500.0, z0=8000.0):
    """a lattice of step `step` on the cylinder r = fn_r(z) around an axis tilted tilt_deg in x, grid axes rotated rot_deg
    to z; returns P (n, n, 3), V, umbilicus (z, x, y) and the axis function."""
    t = np.radians(tilt_deg)
    ax = lambda z: (4000.0 + np.tan(t) * (z - z0), 4000.0 + 0 * z)  # noqa: E731
    ro = np.radians(rot_deg)
    I, J = np.meshgrid(np.arange(n) - n / 2, np.arange(n) - n / 2, indexing="ij")
    s_arc = step * (I * np.cos(ro) - J * np.sin(ro))   # arc length (approximately, at r0) along the surface
    zz = z0 + step * (I * np.sin(ro) + J * np.cos(ro))
    th = s_arc / r0
    r = fn_r(zz)
    cx, cy = ax(zz)
    P = np.stack([cx + r * np.cos(th), cy + r * np.sin(th), zz], -1)
    V = np.ones((n, n), bool)
    uz = np.linspace(z0 - 4000, z0 + 4000, 41)
    ux, uy = ax(uz)
    return P, V, (uz, ux, uy), ax


def selftest():
    run_id = utc()
    rows = []

    def row(test, what, value, bar, passed):
        rows.append([run_id, test, what, value, bar, "yes" if passed else "no"])

    z0 = 8000.0
    rip = lambda z: 1500.0 + 3.0 * np.sin(2 * np.pi * (z - z0) / 400.0)  # noqa: E731
    P, V, U, ax = synth(rip)
    PO, ok, si, sj, h, st, _ = regrid(P, V, U, fit="none", side=300)
    cx, cy = centre(U, PO[..., 2])
    rtrue = rip(PO[..., 2])
    err = np.abs(np.hypot(PO[..., 0] - cx, PO[..., 1] - cy) - rtrue)[ok]
    ang = float(st["row_step_angle_to_z_median_deg"]); du = float(st["spacing_u_median_vox"])
    angi = float(st["row_step_inplane_angle_to_z_median_deg"])
    row("T1", "fit none: v step IN PLANE angle to z median (deg; the grid's shear, information)", "%.4f" % angi, "information", True)
    a3u, _ = step_angles(PO, ok, 1)
    dev = float(np.nanmedian(np.abs(90.0 - a3u)))
    row("T5", "fit none: median |90 - 3D angle of the u step to z| (deg)", "%.5f" % dev, "< 0.01", dev < 0.01)
    row("T1", "fit none: row step 3D angle to z median (deg; holds the sheet's inclination to z, information)", "%.4f" % ang,
        "information", True)
    row("T1", "fit none: u spacing median / h - 1", "%.5f" % (du / h - 1), "|x| < 0.01", abs(du / h - 1) < 0.01)
    row("T1", "fit none: |r_out - r_true| p95 (vox)", "%.4f" % np.percentile(err, 95), "< 0.1", np.percentile(err, 95) < 0.1)
    row("T1", "fit none: valid output nodes", int(ok.sum()), "> 50000", ok.sum() > 50000)
    smooth = lambda z: 1500.0 + 0.02 * (z - z0)  # noqa: E731
    P2, V2, U2, _ = synth(smooth)
    PO2, ok2, *_rest = regrid(P2, V2, U2, fit="spline", knot_vox=500.0 / 9.362, side=300)
    cx2, cy2 = centre(U2, PO2[..., 2])
    err2 = np.abs(np.hypot(PO2[..., 0] - cx2, PO2[..., 1] - cy2) - smooth(PO2[..., 2]))[ok2]
    row("T2", "fit spline 0.5 mm knots on a smooth cone: |r_out - r_true| p95 (vox)", "%.4f" % np.percentile(err2, 95), "< 0.1",
        np.percentile(err2, 95) < 0.1)
    st2 = _rest[3]
    row("T2", "fit spline: v step IN PLANE angle to z median (deg; the grid's shear, information)",
        st2["row_step_inplane_angle_to_z_median_deg"], "information", True)
    a3u2, _ = step_angles(PO2, ok2, 1)
    dev2 = float(np.nanmedian(np.abs(90.0 - a3u2)))
    row("T6", "fit spline: median |90 - 3D angle of the u step to z| (deg)", "%.5f" % dev2, "< 0.01", dev2 < 0.01)
    PO7, ok7, *_r7 = regrid(P, V, U, fit="none", side=300, max_dist_3d=2 * h)
    row("T7", "--max-dist-3d 2h on a surface without folds drops no node (nodes dropped)", _r7[3]["nodes_dropped_off_sheet"], "0",
        _r7[3]["nodes_dropped_off_sheet"] == 0 and int(ok7.sum()) == int(ok.sum()))
    tmpd = "/data/tmp/regrid-selftest-%d" % os.getpid()
    shutil.rmtree(tmpd, ignore_errors=True); os.makedirs(tmpd)
    try:
        write_tifxyz(tmpd + "/a", PO, ok, h, {})
        Q, W = read_tifxyz(tmpd + "/a")
        same = np.array_equal(W, ok) and np.array_equal(Q[W].astype(np.float32), PO[ok].astype(np.float32))
        row("T3", "tifxyz round trip (float32)", "equal" if same else "differs", "equal", same)
        m = 200
        rec = np.zeros(m * m, POINT)
        I, J = np.meshgrid(np.arange(m), np.arange(m), indexing="ij")
        rec["x"] = (I + 1000).ravel(); rec["y"] = (J + 1000).ravel()
        rec["px"], rec["py"], rec["pz"] = [P[:m, :m, k].astype(np.float32).ravel() for k in range(3)]
        rec.tofile(tmpd + "/p.bin")
        Pa, Va = read_patch(tmpd + "/p.bin")
        write_tifxyz(tmpd + "/b", Pa, Va, 4.0, {})
        Pb, Vb = read_tifxyz(tmpd + "/b")
        oa = regrid(Pa, Va, U, fit="none", side=150)
        ob = regrid(Pb, Vb, U, fit="none", side=150)
        same2 = np.array_equal(oa[1], ob[1]) and np.allclose(oa[0][oa[1]], ob[0][ob[1]], atol=1e-3)
        row("T4", "patch .bin and the same lattice as tifxyz give the same output", "equal" if same2 else "differs", "equal", same2)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    new = not os.path.isfile(SELFTEST)
    with open(SELFTEST, "a", newline="") as f:
        if new:
            f.write("# written by %s selftest: synthetic cylinder r = 1500 + 3 sin(2 pi z / 400) voxels around an axis tilted 2 "
                    "degrees, lattice step 4 voxels rotated 30 degrees to z (T1, T3, T4); smooth cone r = 1500 + 0.02 (z - z0) (T2)\n" % TOOL)
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(["run", "test", "what", "value", "bar", "passed"])
        w.writerows(rows)
    for r in rows:
        print(r)
    if not all(r[-1] == "yes" for r in rows):
        sys.exit(3)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        return selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["run"])
    ap.add_argument("--input", required=True); ap.add_argument("--umbilicus", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--box", type=int, nargs=4); ap.add_argument("--mask"); ap.add_argument("--fit", default="spline", choices=["spline", "none"])
    ap.add_argument("--knot-mm", type=float, default=0.5); ap.add_argument("--voxel-um", type=float, default=9.362)
    ap.add_argument("--h", type=float); ap.add_argument("--side", type=int); ap.add_argument("--centre", type=float, nargs=2)
    ap.add_argument("--label"); ap.add_argument("--csv")
    ap.add_argument("--max-dist-3d", type=float, help="a node is valid only within this 3D distance (voxels) of a model node")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
