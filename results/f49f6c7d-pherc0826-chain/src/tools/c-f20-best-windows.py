#!/usr/bin/env python3
"""Figure C20: the three best clean 20 x 20 mm windows of PHerc. 0826, as the checks found them, on the raw scan.

RAW SCAN, NO INK DETECTOR. Every grey here is the raw masked scan read at the grown points of a delivered sheet, or
along each point's normal, nothing else: no ink model, no ink map, no filter beyond a linear grey stretch. It is drawn
on the director's order of 2026-09-29T06:54:31Z (owner's word, the reframe around the checks), which asks for the best
windows figure with the axis aligned renders and the straightened sections «once they pass». No ink output of
best-windows-0826 is read.

What it reads, every file checked before a pixel is drawn.
  - The snapshot of best-windows-0826 in evidence/studies (windows.csv, renders.csv, straight.csv, aligned.csv), written
    by that study's bw.py, panels.py, straight.py and align.py, shipped under tools/studies/best-windows-0826. The best
    three windows are the rows with best3 set, in that column's order.
  - derived/checks-summary.csv (src/tools/checks_summary.py): which of the three straightened sections separate from a
    peak placed at random (that tool's rule). Only those are drawn; the others are named in the caption, not drawn.
  - The panel data the study saved from the same arrays it drew, /data/scrollagent/runs/rev1/best-windows-0826/scratch/
    panel-data/<tag>.npz (panels.py: the lattice render «current» and the axis aligned render «aligned» of its own
    tools/align.py) and straight-<tag>.npz (straight.py). Their sha256 are pinned below: render-routes-0826 may redo the
    axis aligned renders with its regrid_z.py, which is under the director's review, and a rewritten file must stop this
    figure rather than enter the article unseen.
Checks, each a row: the lattice render is cells_i by cells_j of its windows.csv row and its covered share is that row's
covered_share; the aligned render's covered share is renders.csv's aligned_covered_share; the cell step is the smaller
of the row's steps; the straightened section's median offset and share within 3 voxels, recomputed here from the saved
array by straight.py's rule, equal straight.csv's.

What it writes. The plotted table evidence/figures/c-f20-best-windows.csv (key, panel, what, source_file, source_column,
value), the PNG assets under paper/figures/assets (one pixel per lattice cell, per resampled point, per point and voxel
of the section), and src/tools/c-f20-best-windows-body.tex, the TikZ body that c-f20-best-windows.tex inputs. With --out
elsewhere than the default, the body and the assets go beside --out and the shipped ones are left alone.

Usage: c-f20-best-windows.py [--out CSV] [--png PNG]
"""
import argparse
import csv
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f20-best-windows"
PD = "/data/scrollagent/runs/rev1/best-windows-0826/scratch/panel-data"
BW = "evidence/studies/best-windows-0826"
CS = "evidence/derived/checks-summary.csv"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
# sha256 of the panel data as it was when this figure was written (2026-09-29, align.py resampling, straight.py of
# DECLARATION.md addition 06:46:40Z), one row per file in c-f20-best-windows-pins.csv. A different file stops the figure.
PIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), FIGURE + "-pins.csv")
W_CM, GAP_CM = 5.8, 0.25   # display choices: the side of each render, the gap between panels


def rd(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip('"').startswith("#")))


def pins():
    p = {}
    for r in rd(PIN_FILE):
        p[r["file"]] = r["sha256"]
    return p


def grey_u8(v, ok):
    """The study's panel rule: p1 to p99 of the window's nonzero covered values, holes white, a stored 0 black."""
    pool = v[ok & np.isfinite(v) & (v > 0)]
    lo, hi = np.percentile(pool, [1, 99])
    g = np.rint(np.clip((np.nan_to_num(v) - lo) / max(1e-9, hi - lo), 0, 1) * 255).astype(np.uint8)
    img = np.stack([g] * 3, -1)
    img[ok & (np.nan_to_num(v) == 0)] = 0
    img[~ok] = 255
    return img, float(lo), float(hi)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None, help="the asset base name; assets are <base>-<panel>.png")
    ap.add_argument("--bar-mm", type=float, default=5.0)
    ap.add_argument("--vbar-mm", type=float, default=0.5)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_out = os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    out = os.path.abspath(a.out or default_out)
    shipped = out == os.path.abspath(default_out)
    base = os.path.abspath(a.png or os.path.join(here, "paper/figures/assets/%s.png" % FIGURE))
    base = os.path.splitext(base)[0]
    body = os.path.join(here, "tools/%s-body.tex" % FIGURE) if shipped else os.path.join(os.path.dirname(out), "%s-body.tex" % FIGURE)
    busy = figlib.require_free_machine(2.0)
    rows = []

    def put(panel, what, source_file, source_column, value, key=""):
        rows.append(dict(key=key, panel=panel, what=what, source_file=source_file, source_column=source_column, value=value))

    W = rd(os.path.join(here, BW, "windows.csv"))
    R = {r["tag"]: r for r in rd(os.path.join(here, BW, "renders.csv"))}
    ST = {(r["tag"], r["line"]): r for r in rd(os.path.join(here, BW, "straight.csv"))}
    C = {r["quantity"]: r for r in rd(os.path.join(here, CS))}
    b3 = sorted([r for r in W if r["best3"]], key=lambda r: r["best3"])
    if len(b3) != 3:
        raise SystemExit("windows.csv: %d best3 rows, not 3" % len(b3))
    pinned = pins()
    vox_mm = float(re.match(r"\d+-([0-9.]+)um", RL.ZARR).group(1)) / 1000.0
    put("g", "voxel of the raw scan; mm", "rasterlib.py ZARR", "the volume's name", "%.6f" % vox_mm)
    side = C["windows_side_mm"]["value"]
    put("a;b;c", "declared window side; mm", CS, "windows_side_mm", side, key="side_mm")
    for q, k in (("windows_best3_angle_min_deg", "angle_min"), ("windows_best3_angle_max_deg", "angle_max"),
                 ("straight_peak_window_vox", "peak_window"), ("straight_random_median_vox", "random_median"),
                 ("straight_random_share", "random_share")):
        put("g", q, CS, q, C[q]["value"], key=k)
    assets, tags, meds = [], [], {}
    mnear = re.search(r"share_within_(\d+)_vox", ",".join(next(iter(ST.values())).keys()))
    near = int(mnear.group(1))
    put("g", "the near band of the section statistic; voxels", BW + "/straight.csv", "the column name share_within_N_vox", near, key="near_vox")
    for n, r in enumerate(b3, 1):
        tag = "bw" + r["rank"]
        tags.append(tag)
        wrel = BW + "/windows.csv"
        f = "%s.npz" % tag
        p = os.path.join(PD, f)
        h = RL.sha256(p)
        if pinned.get(f) != h:
            raise SystemExit("%s: sha256 %s is not the pinned %s; the panel data changed after this figure was written "
                             "(the axis aligned render may now come from regrid_z.py, under the director's review)"
                             % (p, h, pinned.get(f)))
        put("a;d", "%s panel data sha256 (pinned)" % tag, os.path.relpath(p, "/data/scrollagent/runs/rev1"), "", h)
        z = np.load(p)
        ci, cj = int(r["cells_i"]), int(r["cells_j"])
        cur, cok = z["current"], z["current_ok"]
        if cur.shape != (ci, cj):
            raise SystemExit("%s: lattice render %s is not %dx%d" % (tag, cur.shape, ci, cj))
        cov = float(cok.mean())
        if abs(cov - float(r["covered_share"])) > 5e-7:
            raise SystemExit("%s: covered share %.6f is not the row's %s" % (tag, cov, r["covered_share"]))
        step = min(float(r["step_i_mm"]), float(r["step_j_mm"]))
        if abs(float(z["step"]) - step) > 1e-6:
            raise SystemExit("%s: the saved step %.6f is not the row's %.6f" % (tag, float(z["step"]), step))
        al, aok = z["aligned"], z["aligned_ok"]
        acov = float(aok.mean())
        if abs(acov - float(R[tag]["aligned_covered_share"])) > 5e-7:
            raise SystemExit("%s: aligned covered share %.6f is not renders.csv's %s" % (tag, acov, R[tag]["aligned_covered_share"]))
        seed = r["seed"].replace("PHerc0826-seed", "")
        put("a", "%s seed" % tag, wrel, "seed", seed, key="seed_%d" % n)
        put("a", "%s sheet" % tag, wrel, "sheet", r["sheet"], key="sheet_%d" % n)
        put("a", "%s source" % tag, wrel, "source", r["source"])
        put("a", "%s window corner i0;j0 and cells" % tag, wrel, "i0; j0; cells_i; cells_j", "%s;%s;%d;%d" % (r["i0"], r["j0"], ci, cj))
        put("a", "%s covered share" % tag, wrel, "covered_share", r["covered_share"], key="covered_%d" % n)
        fl = r["flagged_share"]
        fl = fl.split(".")[0] if re.fullmatch(r"\d+\.0+", fl) else fl      # paper_numbers.py's rule 1: 0.000000 prints 0
        put("a", "%s flagged share" % tag, wrel, "flagged_share", fl, key="flagged_%d" % n)
        put("a", "%s window fibre score" % tag, wrel, "window_fibre", r["window_fibre"], key="fibre_%d" % n)
        put("a", "%s cell step; mm" % tag, wrel, "min(step_i_mm, step_j_mm)", "%.6f" % step)
        put("d", "%s aligned covered share" % tag, BW + "/renders.csv", "aligned_covered_share", R[tag]["aligned_covered_share"])
        put("d", "%s aligned median spacing; voxels" % tag, BW + "/renders.csv", "aligned_median_spacing_vox",
            R[tag]["aligned_median_spacing_vox"])
        g1, lo, hi = grey_u8(cur, cok)
        g2, lo2, hi2 = grey_u8(al, aok)
        g2 = g2[::-1].copy()          # the aligned rows run down in z; drawn z up
        put("a", "%s lattice grey p1;p99" % tag, "panel data", "current", "%.1f;%.1f" % (lo, hi))
        put("d", "%s aligned grey p1;p99" % tag, "panel data", "aligned", "%.1f;%.1f" % (lo2, hi2))
        f1, f2 = "%s-lattice-%d.png" % (base, n), "%s-aligned-%d.png" % (base, n)
        RL.save_png(f1, g1)
        RL.save_png(f2, g2)
        put("a", "%s lattice asset pixels sha256" % tag, os.path.basename(f1), "", RL.plane_sha(g1))
        put("d", "%s aligned asset pixels sha256" % tag, os.path.basename(f2), "", RL.plane_sha(g2))
        assets.append((f1, f2, step, cj))
        # the straightened sections: recomputed statistic against straight.csv, for every best window
        f = "straight-%s.npz" % tag
        p = os.path.join(PD, f)
        h = RL.sha256(p)
        if pinned.get(f) != h:
            raise SystemExit("%s: sha256 %s is not the pinned %s" % (p, h, pinned.get(f)))
        put("g", "%s straightened section data sha256 (pinned)" % tag, os.path.relpath(p, "/data/scrollagent/runs/rev1"), "", h)
        zs = np.load(p)
        pk = int(C["straight_peak_window_vox"]["value"])
        for line in "ij":
            S = zs["%s_img" % line]
            half = S.shape[1] // 2
            win = S[:, half - pk:half + pk + 1]
            colok = np.isfinite(win).all(1) & (np.nan_to_num(win) > 0).any(1)
            tstar = np.abs(np.argmax(np.where(np.isfinite(win), win, -1), axis=1) - pk)[colok]
            med, share = float(np.percentile(tstar, 50)), float((tstar <= near).mean())
            meds[(tag, line)] = (med, share)
            srow = ST[(tag, line)]
            same = abs(med - float(srow["peak_offset_median_vox"])) < 1e-9 and abs(share - float(srow["share_within_3_vox"])) < 5e-5
            put("g", "%s line %s median offset;share within 3, recomputed; equal to straight.csv" % (tag, line), BW + "/straight.csv",
                "peak_offset_median_vox; share_within_3_vox", "%g;%.4f;%s" % (med, share, "yes" if same else "no"),
                key="median_%s_%d" % (line, n))
            if not same:
                raise SystemExit("%s line %s: recomputed %g, %.4f; straight.csv %s, %s" % (
                    tag, line, med, share, srow["peak_offset_median_vox"], srow["share_within_3_vox"]))
        sep = C["straight_%s_separates" % tag]["value"]
        put("g", "%s straightened sections separate from random placement (checks_summary.py)" % tag, CS,
            "straight_%s_separates" % tag, sep)
    drawn = [t for t in tags if C["straight_%s_separates" % t]["value"] == "yes"]
    put("g", "best windows whose straightened section is drawn", CS, "straight_<tag>_separates = yes",
        " ".join(drawn) or "none", key="sections_drawn")
    if len(drawn) != 1 or drawn[0] != tags[0]:
        raise SystemExit("the layout draws the section of the first window only; the separating ones are %s" % drawn)
    others = [meds[(t, l)][0] for t in tags if t not in drawn for l in "ij"]
    put("g", "median offset of the sections not drawn, min", "this tool", "recomputed above", "%g" % min(others), key="other_min")
    put("g", "median offset of the sections not drawn, max", "this tool", "recomputed above", "%g" % max(others), key="other_max")
    put("g", "drawn section along j: median offset; voxels", "this tool", "recomputed above", "%g" % meds[(drawn[0], "j")][0], key="sec_median")
    put("g", "drawn section along j: share within the near band", "this tool", "recomputed above", "%.4f" % meds[(drawn[0], "j")][1], key="sec_share")
    n = 1
    zs = np.load(os.path.join(PD, "straight-%s.npz" % drawn[0]))
    S, lo, hi, colmm, ptok = zs["j_img"], float(zs["j_lo"]), float(zs["j_hi"]), float(zs["j_colmm"]), zs["j_pt_ok"]
    img = S.T[::-1]                                    # rows +t up, columns the line's points
    g = np.rint(np.clip((np.nan_to_num(img) - lo) / max(1e-9, hi - lo), 0, 1) * 255).astype(np.uint8)
    g = np.stack([g] * 3, -1)
    g[:, ~ptok] = 255
    f3 = "%s-section-%d.png" % (base, n)
    RL.save_png(f3, g)
    put("g", "section along j of %s; grey p1;p99.5 as straight.py" % drawn[0], "panel data", "j_lo; j_hi", "%.1f;%.1f" % (lo, hi))
    put("g", "section columns;rows", "panel data", "j_img", "%d;%d" % (g.shape[1], g.shape[0]))
    put("g", "section half height; voxels", "panel data", "j_img rows", (g.shape[0] - 1) // 2, key="half_rows")
    put("g", "section column spacing; mm", "panel data", "j_colmm", "%.5f" % colmm)
    put("g", "section rows against true scale, square pixels (display choice)", "this tool", "column spacing over voxel",
        "%.0f" % (colmm / vox_mm), key="stretch")
    put("g", "asset pixels sha256", os.path.basename(f3), "", RL.plane_sha(g))
    put("a;b;c;d;e;f;g", "scale bar; mm (display choice)", "argument --bar-mm", "", "%g" % a.bar_mm, key="bar_mm")
    put("g", "vertical scale bar; mm (display choice)", "argument --vbar-mm", "", "%g" % a.vbar_mm, key="vbar_mm")
    comment = ("figure C20, what the raster drew, written by src/tools/%s.py at %s (cores busy %s): the best three clean "
               "windows of best-windows-0826, the lattice render and the axis aligned render of that study's align.py, and "
               "the straightened section of each window that separates from random placement; RAW SCAN, NO INK DETECTOR. "
               "Not for a public repository without the owner's word."
               % (FIGURE, figlib.utc_now(), "not checked" if busy is None else "%.1f" % busy))
    figlib.write_plotted(out, comment, FIELDS, rows)

    # ---- the TikZ body: two rows of three renders, the section below at the full width
    L = ["% Generated by src/tools/c-f20-best-windows.py from evidence/figures/c-f20-best-windows.csv. Do not edit."]
    width = 3 * W_CM + 2 * GAP_CM
    sec_h = width * g.shape[0] / g.shape[1]      # square pixels: the rows stretched colmm / vox_mm times against true scale
    y_sec = 0.0
    y_al = sec_h + 0.75
    y_lat = y_al + W_CM + 0.55
    letters = "abcdef"
    for k, (f1, f2, step, ncols) in enumerate(assets):
        x = k * (W_CM + GAP_CM)
        for (f, y, lab) in ((f1, y_lat, letters[k]), (f2, y_al, letters[k + 3])):
            L.append(r"\node[anchor=south west, inner sep=0] at (%.4f,%.4f) {\includegraphics[width=%.4fcm,height=%.4fcm]{../paper/figures/assets/%s}};"
                     % (x, y, W_CM, W_CM, os.path.basename(f)))
            L.append(r"\draw[black, line width=0.4pt] (%.4f,%.4f) rectangle (%.4f,%.4f);" % (x, y, x + W_CM, y + W_CM))
            blen = a.bar_mm / (step * ncols) * W_CM
            x1 = x + W_CM - 0.2
            L.append(r"\fill[white, opacity=0.85] (%.4f,%.4f) rectangle (%.4f,%.4f);" % (x1 - blen - 0.12, y + 0.1, x1 + 0.12, y + 0.72))
            L.append(r"\fill[black] (%.4f,%.4f) rectangle (%.4f,%.4f);" % (x1 - blen, y + 0.22, x1, y + 0.3))
            L.append(r"\node[font=\footnotesize, anchor=south, inner sep=1pt] at (%.4f,%.4f) {%g mm};" % (x1 - blen / 2, y + 0.31, a.bar_mm))
            L.append(r"\node[anchor=north west, fill=white, fill opacity=0.88, text opacity=1, font=\footnotesize, inner sep=2pt] at (%.4f,%.4f) {(%s)};"
                     % (x + 0.1, y + W_CM - 0.1, lab))
        r = b3[k]
        L.append(r"\node[anchor=south west, font=\footnotesize, inner sep=1pt] at (%.4f,%.4f) {seed %s, sheet %s: lattice};"
                 % (x, y_lat + W_CM + 0.05, r["seed"].replace("PHerc0826-seed", ""), r["sheet"]))
        L.append(r"\node[anchor=south west, font=\footnotesize, inner sep=1pt] at (%.4f,%.4f) {axis aligned (align.py), $z$ up};"
                 % (x, y_al + W_CM + 0.05))
    L.append(r"\node[anchor=south west, inner sep=0] at (0,%.4f) {\includegraphics[width=%.4fcm,height=%.4fcm]{../paper/figures/assets/%s}};"
             % (y_sec, width, sec_h, os.path.basename(f3)))
    L.append(r"\draw[black, line width=0.4pt] (0,%.4f) rectangle (%.4f,%.4f);" % (y_sec, width, y_sec + sec_h))
    L.append(r"\draw[sasky, line width=0.5pt, opacity=0.55] (0,%.4f) -- (%.4f,%.4f);" % (y_sec + sec_h / 2, width, y_sec + sec_h / 2))
    L.append(r"\node[anchor=south west, font=\footnotesize, inner sep=1pt] at (0,%.4f) {(g) seed %s, straightened section along $j$ through the window centre, rows %s$\times$ true scale};"
             % (y_sec + sec_h + 0.05, b3[0]["seed"].replace("PHerc0826-seed", ""), "%.0f" % (colmm / vox_mm)))
    blen = a.bar_mm / (colmm * g.shape[1]) * width
    vlen = a.vbar_mm / vox_mm / g.shape[0] * sec_h
    x1 = width - 0.25
    L.append(r"\fill[white, opacity=0.85] (%.4f,%.4f) rectangle (%.4f,%.4f);" % (x1 - blen - 0.12, y_sec + 0.08, x1 + 0.12, y_sec + 0.7))
    L.append(r"\fill[black] (%.4f,%.4f) rectangle (%.4f,%.4f);" % (x1 - blen, y_sec + 0.2, x1, y_sec + 0.28))
    L.append(r"\node[font=\footnotesize, anchor=south, inner sep=1pt] at (%.4f,%.4f) {%g mm};" % (x1 - blen / 2, y_sec + 0.29, a.bar_mm))
    L.append(r"\fill[white, opacity=0.85] (0.08,%.4f) rectangle (1.25,%.4f);" % (y_sec + sec_h / 2 - vlen / 2 - 0.08, y_sec + sec_h / 2 + vlen / 2 + 0.08))
    L.append(r"\fill[black] (0.15,%.4f) rectangle (0.23,%.4f);" % (y_sec + sec_h / 2 - vlen / 2, y_sec + sec_h / 2 + vlen / 2))
    L.append(r"\node[font=\footnotesize, anchor=west, inner sep=1pt] at (0.26,%.4f) {%g mm};" % (y_sec + sec_h / 2, a.vbar_mm))
    L.append(r"\node[anchor=north east, fill=white, fill opacity=0.88, text opacity=1, font=\footnotesize, inner sep=2pt] at (%.4f,%.4f) {raw scan, no ink detector};"
             % (width - 0.1, y_lat + W_CM - 0.1))
    with open(body, "w") as fh:
        fh.write("\n".join(L) + "\n")
    sys.stderr.write("%s: %d rows; body %s\n" % (out, len(rows), body))


if __name__ == "__main__":
    main()
