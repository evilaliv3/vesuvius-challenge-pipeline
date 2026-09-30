#!/usr/bin/env python3
"""render-routes-0826/tools/align_square.py ROUTE NAME: the certified square of a row regridded with best-windows-0826's
tools/align.py (director 15:53:25Z): v = scan z, u = 3D arc length at constant z, u = 0 on the steepest ascent curve through the
square's centre, dz corrected once so rows and columns share the step. align.py's Field and resample_grid are IMPORTED unchanged
(never edited); this driver copies align.resample's steps for a surface that is not one of its targets (the upsampled tracer
crop): half = side // 2 + 64, field box 1.8 x half + 10 around the centre, h = median neighbour step in the square, a first pass
at dz = h, then dz = h^2 / median row step. A node is valid when its nearest crop node is covered and it sits within 2 voxels of
its z level (align.py's two rules).
Measured, one row of evidence/aligned-square.csv: z deviation, row and column steps, and the RESIDUAL in plane angle of the
grid after the regrid (v step against z projected on the tangent plane, regrid_z.step_angles used as a measuring function
only; and min(a, 90 - a)) over the centred square. Raw values sampled (nearest voxel, 20250821151701 level 0) through
routes.values (fetch plan row, 35 GB rule); the texture, z up, 5 mm bar, into outputs/artifacts/render-routes-0826/ (Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran);
arrays into scratch/aligned-<ROUTE>-<NAME>.npz for the figure."""
import csv, json, os, subprocess, sys
import numpy as np
H = "/data/scrollagent/runs/rev1/render-routes-0826"
sys.path.insert(0, H + "/tools")
import routes as RT  # noqa: E402
import regrid_z as RZ  # noqa: E402
sys.path.insert(0, "/data/scrollagent/runs/rev1/best-windows-0826/tools")
import align as AL  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
route, name = sys.argv[1:3]
j = json.load(open(H + "/scratch/rows/%s-%s.json" % (route, name)))
b = int(j["largest_certified_square_cells"]); i0, j0 = map(int, j["largest_certified_square_corner"].split())
if not (b > 0):
    raise SystemExit("refuse: no certified square in the row")
P, V = RT.surface(route, name)[:2]
S = b; MARG = 64
half = S // 2 + MARG
ic, jc = i0 + b // 2, j0 + b // 2
if not V[ic, jc]:
    ii, jj = np.nonzero(V); k = np.argmin((ii - ic) ** 2 + (jj - jc) ** 2); ic, jc = int(ii[k]), int(jj[k])
R = int(half * 1.8) + 10
a0, a1, b0, b1 = max(0, ic - R), min(V.shape[0], ic + R), max(0, jc - R), min(V.shape[1], jc + R)
Fd = AL.Field(P[a0:a1, b0:b1], V[a0:a1, b0:b1])
Wn = P[i0:i0 + b, j0:j0 + b]; Mw = V[i0:i0 + b, j0:j0 + b]
h = float(np.median(np.concatenate([np.linalg.norm((Wn[1:] - Wn[:-1])[Mw[1:] & Mw[:-1]], axis=1),
                                    np.linalg.norm((Wn[:, 1:] - Wn[:, :-1])[Mw[:, 1:] & Mw[:, :-1]], axis=1)])))
GI, GJ, zc, norg = AL.resample_grid(Fd, ic - a0, jc - b0, h, h, half)
Q = Fd.at(Fd.Praw, GI.ravel(), GJ.ravel()).reshape(GI.shape + (3,))
dv = np.linalg.norm(Q[1:] - Q[:-1], axis=-1); med1 = float(np.median(dv[np.isfinite(dv)]))
dz2 = h * h / med1
GI, GJ, zc, norg = AL.resample_grid(Fd, ic - a0, jc - b0, h, dz2, half)
Q = Fd.at(Fd.Praw, GI.ravel(), GJ.ravel()).reshape(GI.shape + (3,))
fin = np.isfinite(GI) & np.isfinite(Q).all(-1)
NI_ = np.full(GI.shape, -1); NJ_ = np.full(GI.shape, -1)
NI_[fin] = np.rint(GI[fin]).astype(int) + a0; NJ_[fin] = np.rint(GJ[fin]).astype(int) + b0
inb = fin & (NI_ >= 0) & (NI_ < V.shape[0]) & (NJ_ >= 0) & (NJ_ < V.shape[1])
val = np.zeros(GI.shape, bool); val[inb] = V[NI_[inb], NJ_[inb]]
zoff = np.abs(Q[..., 2] - (zc + (np.arange(GI.shape[0]) - half)[:, None] * dz2))
off = val & ~(zoff <= 2.0); val &= ~off
c0 = half - S // 2
sq = (slice(c0, c0 + S), slice(c0, c0 + S))
insq = np.zeros(GI.shape, bool)
insq[inb] = (NI_[inb] >= i0) & (NI_[inb] < i0 + b) & (NJ_[inb] >= j0) & (NJ_[inb] < j0 + b)
Qv = np.where(val[..., None], Q, np.nan)
a3, ai = RZ.step_angles(Qv, val, 0)      # v step (rows): 3D and in plane angle to z
a3u, _ = RZ.step_angles(Qv, val, 1)      # u step: 3D angle to z (90 when the row is at constant z)
A_ = ai[sq[0].start:sq[0].stop - 1, sq[1]]; A_ = A_[np.isfinite(A_)]
rot = np.minimum(A_, 90 - A_)
U_ = a3u[sq[0], sq[1].start:sq[1].stop - 1]; U_ = U_[np.isfinite(U_)]
VAL, vinfo = RT.values(Qv, val, "aligned-%s-%s" % (route, name))
if VAL is None:
    raise SystemExit("raw values not sampled: %s" % vinfo)
np.savez_compressed(H + "/scratch/aligned-%s-%s.npz" % (route, name), Q=Q.astype(np.float32), valid=val, insq=insq, VAL=VAL.astype(np.float32),
                    c0=c0, S=S, half=half, h=h, dz=dz2)
# texture of the centred square, z up (row index grows with z: flipped), 5 mm bar
v = VAL[sq].astype(float); ok = val[sq]
g = v[ok & np.isfinite(v) & (v > 0)]
lo, hi = np.percentile(g, [1, 99])
im = (np.clip((np.nan_to_num(v) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
rgb = np.stack([im] * 3, -1); rgb[~ok] = 255
rgb = rgb[::-1]
step_mm = h * 0.009362
cv = Image.new("RGB", (rgb.shape[1], rgb.shape[0] + 60), "white"); cv.paste(Image.fromarray(rgb), (0, 0)); d = ImageDraw.Draw(cv)
L = int(round(5.0 / step_mm)); d.rectangle([10, rgb.shape[0] + 8, 10 + L, rgb.shape[0] + 14], fill="black")
d.text((16 + L, rgb.shape[0] + 4), "5 mm", fill="black")
d.text((10, rgb.shape[0] + 22), "%s %s: certified square regridded with best-windows-0826 align.py (v = z up, u = arc length at constant z); "
       "residual in plane angle median %.2f deg" % (route, name, float(np.median(rot))), fill="black")
png = "/data/scrollagent/outputs/artifacts/render-routes-0826/%s-%s-aligned-texture.png" % (name, route)
cv.save(png)
row = dict(utc=subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(), route=route, surface=name, square_cells=S,
           square_corner="%d %d" % (i0, j0), tool="best-windows-0826/tools/align.py Field and resample_grid (imported unchanged)",
           h_vox="%.4f" % h, dz_first="%.4f" % h, median_row_step_first="%.4f" % med1, dz_final="%.4f" % dz2,
           rows_with_origin=norg, grid=GI.shape[0], square_valid_share="%.6f" % ok.mean(),
           square_share_from_certified_square="%.6f" % insq[sq].mean(), points_dropped_off_z=int(off.sum()),
           z_deviation_median_vox="%.4f" % float(np.median(zoff[val])), z_deviation_max_vox="%.4f" % float(zoff[val].max()),
           u_step_abs_90_minus_3d_angle_median_deg="%.4f" % float(np.median(np.abs(90 - U_))),
           residual_v_step_inplane_angle_median_deg="%.3f" % float(np.median(A_)),
           residual_v_step_inplane_angle_iqr_deg="%.3f" % float(np.percentile(A_, 75) - np.percentile(A_, 25)),
           residual_rotation_inplane_median_deg="%.3f" % float(np.median(rot)),
           residual_rotation_inplane_iqr_deg="%.3f" % float(np.percentile(rot, 75) - np.percentile(rot, 25)),
           before_rotation_inplane_median_deg=[r for r in RT.rows(H + "/evidence/routes.csv") if r["route"] == route and r["surface"] == name][-1]["rotation_inplane_median"],
           png=png)
p = H + "/evidence/aligned-square.csv"
new = not os.path.isfile(p)
with open(p, "a", newline="") as f:
    if new:
        f.write("# written by render-routes-0826/tools/align_square.py: a row's certified square regridded with best-windows-0826 align.py "
                "(v = scan z, u = 3D arc length at constant z); residual angles over the centred square after the regrid; "
                "before_rotation_inplane_median_deg from evidence/routes.csv (the tracer's own grid)\n")
    w = csv.DictWriter(f, list(row), lineterminator="\n")
    if new:
        w.writeheader()
    w.writerow(row)
print(json.dumps(row))
