#!/usr/bin/env python3
"""render-routes-0826/article-figure/fig_r2c.py ROUTE NAME: the headline figure of the reframed article (director 11:53:25Z (3)),
from the data files of this study, never from PNGs: (a) the certified square's texture (raw scan, nearest voxel, one pixel per
node), turned by quarter turns and a flip only so that the scan's z points up (the grid axis nearer z, sign by the mean z
step), 5 mm bar; (b) the axial cut at the square's centre height with the tracer's trace, the square's nodes and our sheet's
trace; (c) the straightened sections along the square's two centre lines (brightest layer offsets in evidence/square-checks.csv).
House style: results/figstyle.py (Times, Okabe Ito). PNG and PDF into this folder only; kept private while the study ran (Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.), never into the
article folder or anything public.
Two steps, two interpreters (matplotlib lives only in /data/tmp/umb-figvenv, which has no tifffile):
    /data/scrollagent/.venv/bin/python fig_r2c.py prep ROUTE NAME   -> scratch/fig-<ROUTE>-<NAME>.npz (square texture turned z up)
    /data/tmp/umb-figvenv/bin/python   fig_r2c.py plot ROUTE NAME   -> r2c-<name>.pdf, .png, -data.csv"""
import csv, json, os, sys
import numpy as np
H = "/data/scrollagent/runs/rev1/render-routes-0826"
sys.path.insert(0, "/data/repositories/vesuvius-challenge-pipeline-private/results")
mode, route, name = sys.argv[1:4]


def rows(p):
    return list(csv.DictReader(l for l in open(p) if not l.lstrip('"').startswith("#")))


j = json.load(open(H + "/scratch/rows/%s-%s.json" % (route, name)))
sc = [r for r in rows(H + "/evidence/square-checks.csv") if r["route"] == route and r["surface"] == name][-1]
b = int(j["largest_certified_square_cells"]); i0, j0 = map(int, j["largest_certified_square_corner"].split())
FN = H + "/scratch/fig-%s-%s.npz" % (route, name)
if mode == "prep":
    sys.path.insert(0, H + "/tools")
    import routes as RT  # noqa: E402
    z = np.load(H + "/scratch/values-%s-%s.npz" % (route, name))
    VAL = z["VAL"][i0:i0 + b, j0:j0 + b].astype(float); OK = z["V"][i0:i0 + b, j0:j0 + b]
    P, V = RT.surface(route, name)[:2]
    AN = H + "/scratch/aligned-%s-%s.npz" % (route, name)
    if os.path.isfile(AN):                   # the square regridded by best-windows-0826 align.py (tools/align_square.py): z up
        za = np.load(AN); c0, S_ = int(za["c0"]), int(za["S"])
        VAL = za["VAL"][c0:c0 + S_, c0:c0 + S_].astype(float)[::-1]; OK = za["valid"][c0:c0 + S_, c0:c0 + S_][::-1]
        ar = [r for r in rows(H + "/evidence/aligned-square.csv") if r["route"] == route and r["surface"] == name][-1]
        turn = "align.py regrid, residual in plane rotation %s deg (was %s)" % (ar["residual_rotation_inplane_median_deg"],
                                                                                 ar["before_rotation_inplane_median_deg"])
        np.savez_compressed(FN, VAL=VAL, OK=OK, turn=turn, h=float(za["h"]))
        print(FN); sys.exit(0)
    Pz = P[i0:i0 + b, j0:j0 + b, 2]
    dzi = np.nanmedian(np.diff(Pz, axis=0)); dzj = np.nanmedian(np.diff(Pz, axis=1))
    turn = "none"
    if abs(dzj) > abs(dzi):          # z runs along the columns: transpose so it runs along the rows
        VAL, OK, Pz = VAL.T, OK.T, Pz.T; dzi = dzj; turn = "transposed"
    if dzi > 0:                      # z grows down the rows: flip so it grows up
        VAL, OK = VAL[::-1], OK[::-1]; turn += ", flipped"
    np.savez_compressed(FN, VAL=VAL, OK=OK, turn=turn)
    print(FN); sys.exit(0)
zf = np.load(FN)
VAL, OK, turn = zf["VAL"], zf["OK"], str(zf["turn"])
import figstyle as F  # noqa: E402
step = min(float(j["step_i_mm"]), float(j["step_j_mm"]))
F.use()
import matplotlib.pyplot as plt  # noqa: E402
fig = plt.figure(figsize=(F.PAGE_IN, 3.1))
gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1.25], height_ratios=[1, 1], wspace=0.08, hspace=0.35)
ax = fig.add_subplot(gs[:, 0])
g = VAL[OK & np.isfinite(VAL) & (VAL > 0)]
lo, hi = np.percentile(g, [1, 99])
im = np.clip((np.nan_to_num(VAL) - lo) / (hi - lo), 0, 1); im[~OK] = 1.0
ax.imshow(im, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
F.scale_bar_mpl(ax, float(zf["h"]) * 0.009362 if "h" in zf.files else step, length_mm=5)
ax.set_xticks([]); ax.set_yticks([]); ax.set_title("(a) square %.2f mm, z up%s" % (b * step, " (align.py)" if "align" in turn else ""))
ax2 = fig.add_subplot(gs[:, 1])
a = np.load(H + "/scratch/axial-%s-%s.npz" % (route, name))
img = a["img"]; gg = img[np.isfinite(img) & (img > 0)]; l2, h2 = np.percentile(gg, [1, 99.5])
ax2.imshow(np.clip((np.nan_to_num(img) - l2) / (h2 - l2), 0, 1), cmap="gray", vmin=0, vmax=1, interpolation="nearest")
mk = a["marks"]
for kind, col, lab in ((2, F.ORANGE, "our certified sheet"), (0, F.SKY, "tracer surface"), (1, F.BLUE, "tracer surface in the certified square")):
    s = mk[mk[:, 2] == kind]
    if len(s):
        ax2.scatter(s[:, 0], s[:, 1], s=0.6, color=col, label=lab, linewidths=0)
F.scale_bar_mpl(ax2, 0.009362, length_mm=1)
ax2.set_xticks([]); ax2.set_yticks([]); ax2.set_title("(b) axial cut, z %d" % int(a["z"]))
ax2.legend(loc="upper left", markerscale=8, fontsize=6, frameon=True, facecolor="white", framealpha=0.9, edgecolor="none")
sec = np.load(H + "/scratch/sections-%s-%s.npz" % (route, name))
for r_, axn in enumerate(("i", "j")):
    ax3 = fig.add_subplot(gs[r_, 2])
    S = sec["%s_img" % axn]; gg = S[np.isfinite(S) & (S > 0)]; l3, h3 = np.percentile(gg, [1, 99.5])
    ax3.imshow(np.clip((np.nan_to_num(S.T[::-1]) - l3) / (h3 - l3), 0, 1), cmap="gray", aspect="auto", interpolation="nearest")
    ax3.axhline(60, color=F.SKY, lw=0.4, alpha=0.6)
    F.scale_bar_mpl(ax3, float(sec["%s_colmm" % axn]), length_mm=5)
    ax3.set_xticks([]); ax3.set_yticks([])
    ax3.set_title("(c%d) section along %s: offset median %s vox, %.0f%% within 3" % (
        r_ + 1, axn, sc["section_%s_peak_offset_median_vox" % axn], 100 * float(sc["section_%s_share_within_3_vox" % axn])), fontsize=7)
out = H + "/article-figure/r2c-%s" % name.replace("PHerc0826-", "")
fig.savefig(out + ".pdf"); fig.savefig(out + ".png", dpi=300)
with open(out + "-data.csv", "w", newline="") as f:
    f.write("# written by render-routes-0826/article-figure/fig_r2c.py: what the figure shows, read from evidence/square-checks.csv and "
            "scratch/rows\n")
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["route", "surface", "square_mm", "turn_to_z_up", "section_i_median_vox", "section_i_within3", "section_j_median_vox",
                "section_j_within3", "our_sheet", "our_sheet_within3_share", "axial_z"])
    w.writerow([route, name, "%.4f" % (b * step), turn, sc["section_i_peak_offset_median_vox"], sc["section_i_share_within_3_vox"],
                sc["section_j_peak_offset_median_vox"], sc["section_j_share_within_3_vox"], sc["within3_best_sheet"],
                sc["within3_share_all_cells"], int(a["z"])])
print(out)
