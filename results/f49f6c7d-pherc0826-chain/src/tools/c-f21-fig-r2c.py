#!/usr/bin/env python3
"""c-f21-fig-r2c.py: the drawing of figure C21 (Figure 1), taken on 2026-09-30 from render-routes-0826's
article-figure/fig_r2c.py (shipped beside this work under src/tools/studies/render-routes-0826/) so that this work can
redraw it without touching the live study. Changes of the director's notes of 2026-09-30:
  * panel (a) is the square certified with crossings between traced surfaces adjudicated: side, cells and corner from
    this work's copy of square-checks-adjudicated.csv (src/inputs/render-routes-0826, sha256 in SHA256SUMS), the row of
    ROUTE and NAME; its texture is the study's scratch/values npz on the tracer's own grid, turned by quarter turns and a
    flip only so that the scan's z points up (fig_r2c.py prep's rule; the align.py regrid of the earlier square is not
    used, since it was made for that square);
  * panels (b) and (c) are the study's, of the square that passed the checks against our sheets before the adjudication, and are titled so;
  * panel (b) has no height of the cut and the data table no axial_z (locations withheld, the owner's decision).

Two steps, two interpreters, as fig_r2c.py:
  /data/scrollagent/.venv/bin/python c-f21-fig-r2c.py prep   -> /data/tmp/v5-0826/scratch/fig-adj-<ROUTE>-<NAME>.npz
  /data/tmp/umb-figvenv/bin/python   c-f21-fig-r2c.py plot   -> paper/figures/assets/r2c-<name>.pdf, .png, -data.csv
What it reads (never written): render-routes-0826/scratch/rows/<ROUTE>-<NAME>.json, scratch/values-, axial- and
sections-<ROUTE>-<NAME>.npz, the study's tools/routes.py (prep only, for the surface's z), this work's snapshot of
square-checks.csv and its copy of square-checks-adjudicated.csv. The PDF has no creation date, so a redraw of the same
data gives the same bytes. src/tools/c-f21-r2c.py pins the three outputs and this file by sha256.
Usage: c-f21-fig-r2c.py prep|plot [ROUTE NAME]   (default R2cnative PHerc0826-seed6273-squarecentre)
"""
import csv, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
H = "/data/scrollagent/runs/rev1/render-routes-0826"
sys.path.insert(0, HERE)
mode = sys.argv[1] if len(sys.argv) > 1 else "plot"
route, name = (sys.argv[2:4] if len(sys.argv) >= 4 else ("R2cnative", "PHerc0826-seed6273-squarecentre"))
SCR = "/data/tmp/v5-0826/scratch"


def rows(p):
    return list(csv.DictReader(l for l in open(p) if not l.lstrip('"').startswith("#")))


j = json.load(open(H + "/scratch/rows/%s-%s.json" % (route, name)))
sc = [r for r in rows(os.path.join(SRC, "evidence/studies/render-routes-0826/square-checks.csv"))
      if r["route"] == route and r["surface"] == name]
if len(sc) != 1:
    raise SystemExit("square-checks.csv (snapshot): %d rows of %s %s" % (len(sc), route, name))
sc = sc[0]
b = int(j["largest_certified_square_cells"])
if int(sc["square_cells"]) != b:
    raise SystemExit("the study's row json square (%d cells) is not the snapshot's (%s)" % (b, sc["square_cells"]))
ad = [r for r in rows(os.path.join(SRC, "inputs/render-routes-0826/square-checks-adjudicated.csv"))
      if r["route"] == route and r["surface"] == name]
if len(ad) != 1:
    raise SystemExit("square-checks-adjudicated.csv: %d rows of %s %s" % (len(ad), route, name))
ad = ad[0]
ba = int(ad["certified_adjudicated_cells"]); ai0, aj0 = map(int, ad["certified_adjudicated_corner"].split())
step = min(float(j["step_i_mm"]), float(j["step_j_mm"]))
if abs(float(ad["step_mm"]) - step) > 5e-7 or abs(ba * step - float(ad["certified_adjudicated_mm"])) > 5e-4:
    raise SystemExit("the adjudicated row's step or side does not agree with the study's grid")
FN = SCR + "/fig-adj-%s-%s.npz" % (route, name)
if mode == "prep":
    sys.path.insert(0, H + "/tools")
    import routes as RT  # noqa: E402
    z = np.load(H + "/scratch/values-%s-%s.npz" % (route, name))
    VAL = z["VAL"][ai0:ai0 + ba, aj0:aj0 + ba].astype(float); OK = z["V"][ai0:ai0 + ba, aj0:aj0 + ba]
    if VAL.shape != (ba, ba) or not OK.all():
        raise SystemExit("the adjudicated square is not fully covered on the values grid")
    P = RT.surface(route, name)[0]
    Pz = P[ai0:ai0 + ba, aj0:aj0 + ba, 2]
    dzi = np.nanmedian(np.diff(Pz, axis=0)); dzj = np.nanmedian(np.diff(Pz, axis=1))
    turn = "none"
    if abs(dzj) > abs(dzi):
        VAL, OK = VAL.T, OK.T; dzi = dzj; turn = "transposed"
    if dzi > 0:
        VAL, OK = VAL[::-1], OK[::-1]; turn += ", flipped"
    os.makedirs(SCR, exist_ok=True)
    np.savez_compressed(FN, VAL=VAL, OK=OK, turn=turn)
    print(FN); sys.exit(0)
zf = np.load(FN)
VAL, OK, turn = zf["VAL"], zf["OK"], str(zf["turn"])
import figstyle as F  # noqa: E402
F.use()
import matplotlib.pyplot as plt  # noqa: E402
# Text at 7 to 9 pt where the article prints this figure (owner's order of 2026-09-30): the page is scaled by about 1.28 to
# the text width, so the sizes here are the print sizes over that factor.
plt.rcParams.update({"font.size": 6.5, "axes.titlesize": 6.5, "legend.fontsize": 5.5})
fig = plt.figure(figsize=(F.PAGE_IN, 3.1))
gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1.25], height_ratios=[1, 1], wspace=0.08, hspace=0.35)
ax = fig.add_subplot(gs[:, 0])
g = VAL[OK & np.isfinite(VAL) & (VAL > 0)]
lo, hi = np.percentile(g, [1, 99])
im = np.clip((np.nan_to_num(VAL) - lo) / (hi - lo), 0, 1); im[~OK] = 1.0
ax.imshow(im, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
F.scale_bar_mpl(ax, step, length_mm=5)
ax.set_xticks([]); ax.set_yticks([]); ax.set_title("(a) certified square %.2f mm, z up" % float(ad["certified_adjudicated_mm"]))
ax2 = fig.add_subplot(gs[:, 1])
a = np.load(H + "/scratch/axial-%s-%s.npz" % (route, name))
img = a["img"]; gg = img[np.isfinite(img) & (img > 0)]; l2, h2 = np.percentile(gg, [1, 99.5])
ax2.imshow(np.clip((np.nan_to_num(img) - l2) / (h2 - l2), 0, 1), cmap="gray", vmin=0, vmax=1, interpolation="nearest")
mk = a["marks"]
for kind, col, lab in ((2, F.ORANGE, "our sheet seed1045 S0 (grown by the chain)"), (0, F.SKY, "tracer surface"), (1, F.BLUE, "tracer surface in the earlier square")):
    s = mk[mk[:, 2] == kind]
    if len(s):
        ax2.scatter(s[:, 0], s[:, 1], s=0.6, color=col, label=lab, linewidths=0)
F.scale_bar_mpl(ax2, 0.009362, length_mm=1)
ax2.set_xticks([]); ax2.set_yticks([]); ax2.set_title("(b) axial cut, earlier square")
ax2.legend(loc="upper left", markerscale=6, fontsize=5.5, handletextpad=0.2, borderpad=0.3, frameon=True, facecolor="white", framealpha=0.9, edgecolor="none")
sec = np.load(H + "/scratch/sections-%s-%s.npz" % (route, name))
for r_, axn in enumerate(("i", "j")):
    ax3 = fig.add_subplot(gs[r_, 2])
    S = sec["%s_img" % axn]; gg = S[np.isfinite(S) & (S > 0)]; l3, h3 = np.percentile(gg, [1, 99.5])
    ax3.imshow(np.clip((np.nan_to_num(S.T[::-1]) - l3) / (h3 - l3), 0, 1), cmap="gray", aspect="auto", interpolation="nearest")
    ax3.axhline(60, color=F.SKY, lw=0.4, alpha=0.6)
    F.scale_bar_mpl(ax3, float(sec["%s_colmm" % axn]), length_mm=5)
    ax3.set_xticks([]); ax3.set_yticks([])
    ax3.set_title("(c%d) earlier square, %s: median %s vox, %.0f%% within 3" % (
        r_ + 1, axn, sc["section_%s_peak_offset_median_vox" % axn], 100 * float(sc["section_%s_share_within_3_vox" % axn])), fontsize=6.5)
out = os.path.join(SRC, "paper/figures/assets/r2c-%s" % name.replace("PHerc0826-", ""))
fig.savefig(out + ".pdf", metadata={"CreationDate": None, "ModDate": None})
fig.savefig(out + ".png", dpi=300)
with open(out + "-data.csv", "w", newline="") as f:
    f.write("# written by src/tools/c-f21-fig-r2c.py (from render-routes-0826/article-figure/fig_r2c.py): what the figure shows, "
            "read from this work's snapshot of square-checks.csv (the earlier square, panels b and c), its copy of "
            "square-checks-adjudicated.csv (panel a) and the study's scratch/rows; the height of the axial cut is "
            "withheld (2026-09-30)\n")
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["route", "surface", "square_mm", "adjudicated_square_mm", "adjudicated_square_cells", "turn_to_z_up",
                "section_i_median_vox", "section_i_within3", "section_j_median_vox", "section_j_within3", "our_sheet",
                "our_sheet_within3_share"])
    w.writerow([route, name, sc["square_mm"], ad["certified_adjudicated_mm"], ba, turn, sc["section_i_peak_offset_median_vox"], sc["section_i_share_within_3_vox"],
                sc["section_j_peak_offset_median_vox"], sc["section_j_share_within_3_vox"], sc["within3_best_sheet"],
                sc["within3_share_all_cells"]])
print(out)
