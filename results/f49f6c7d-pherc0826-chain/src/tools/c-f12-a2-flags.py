#!/usr/bin/env python3
"""Figure C12, a raster: one delivered PHerc. 0826 sheet in its own grid, with the steep crossing flags
of arm a2, the cells the cluster rule cuts, and the largest square before and after the rule.

Which sheet, declared before drawing. Over every row of evidence/studies/chain-0826/a2-cluster/<seed>.csv (the snapshot this work ships), the
sheet where a2_cluster_rule_square_mm is furthest below delivered_square_mm (ties: seed name, then
sheet). The rows where the two differ are counted into the table so the reader sees how rare it is.

What is recomputed, and the check that it is the chain's own number. The flags are recomputed here with
the chain's measuring code, imported and not copied: stevens-remedy-half-on/tools/a2_after.py's
modules (lamina-crossing-detect detect.py for the lattice, the two normals and the angle;
lamina-crossing-map-1447 map_crossing.py and cluster_rule.py for the stride points, the clusters and the
holes; seed-search-1447 square.py for the square). The loop is a2_measure's loop, written out so that
the flagged grid and the holes are kept instead of reduced to counts. Before a pixel is drawn, the
counts it gives (a2_measurable, a2_flagged, a2_largest_cluster, a2_kept_points,
a2_cluster_rule_square_mm) must equal the row of the a2-cluster CSV string for string, and the delivered
square must equal the squares row's corner and side; otherwise the script stops.

What is drawn, all in the sheet's own parametrisation grid, one pixel per --px cells (a covered cell
is grey, an empty one white): stride points flagged above T* (orange), flagged points in a cluster of
more than S (red, these are the ones the rule acts on), the cells the rule cuts (dark red), the
delivered square (blue outline) and the square after the rule (green outline). Geometry only; no
texture, no volume data along the sheet: NO INK.

Usage: c-f12-a2-flags.py [--out CSV] [--png PNG]
"""
import argparse
import csv
import glob
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

R1 = "/data/scrollagent/runs/rev1"
sys.path.insert(0, R1 + "/lamina-crossing-map-1447/tools")
sys.path.insert(0, R1 + "/stevens-remedy-half-on/tools")
import map_crossing as MC  # noqa: E402
import cluster_rule as CRL  # noqa: E402
import a2_after as A2  # noqa: E402

FIGURE = "c-f12-a2-flags"
CHAIN = R1 + "/chain-0826"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
STUDIES_REL = "evidence/studies/chain-0826"
GREY, WHITE = (175, 175, 175), (255, 255, 255)
FLAG, KEPT, CUT = (255, 150, 0), (220, 20, 20), (120, 0, 0)
BEFORE, AFTER = (30, 90, 230), (0, 170, 60)


def read_rows(path):
    lines = [l for l in open(path, newline="") if not l.lstrip('"').startswith("#")]
    return list(csv.DictReader(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    ap.add_argument("--zoom", type=int, default=3, help="panel b pixels per grid cell side")
    ap.add_argument("--margin", type=int, default=40, help="panel b cells around the two squares")
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    png = a.png or os.path.join(here, "paper/figures/%s.png" % FIGURE)
    busy = figlib.require_free_machine(2.0)
    rows = []

    snap = os.path.join(here, STUDIES_REL)

    def put(panel, what, source_file, source_column, value, key=""):
        rows.append(dict(key=key, panel=panel, what=what, source_file=source_file, source_column=source_column, value=value))

    # ------------------------------------------------------------------ the sheet, by the declared rule
    cand, total, differ = [], 0, 0
    for p in sorted(glob.glob(snap + "/a2-cluster/PHerc0826-seed*.csv")):
        for r in read_rows(p):
            d, c = figlib.number(r.get("delivered_square_mm")), figlib.number(r.get("a2_cluster_rule_square_mm"))
            if d is None or c is None:
                continue
            total += 1
            if c < d:
                differ += 1
                cand.append((-(d - c), r["seed"], int(r["sheet"]), r, p))
    if not cand:
        raise SystemExit("no sheet where the cluster rule square is below the delivered square")
    cand.sort(key=lambda t: (t[0], t[1], t[2]))
    _, seed, n, arow, apath = cand[0]
    put("a", "measured sheets in the a2-cluster files", "evidence/studies/chain-0826/a2-cluster/*.csv",
        "delivered_square_mm and a2_cluster_rule_square_mm both numbers", total, key="sheets_measured")
    put("a", "of them with the cluster rule square below the delivered square", "evidence/studies/chain-0826/a2-cluster/*.csv",
        "a2_cluster_rule_square_mm < delivered_square_mm", differ, key="sheets_rule_below")
    put("a", "seed drawn (largest drop)", os.path.relpath(apath, here), "seed", seed.replace("PHerc0826-seed", ""), key="seed")
    put("a", "sheet drawn (largest drop)", os.path.relpath(apath, here), "sheet", n, key="sheet")
    put("a", "delivered square; mm", os.path.relpath(apath, here), "delivered_square_mm", arow["delivered_square_mm"], key="delivered_square_mm")
    put("a", "square after the cluster rule; mm", os.path.relpath(apath, here), "a2_cluster_rule_square_mm",
        arow["a2_cluster_rule_square_mm"], key="rule_square_mm")

    sq = MC.read_csv(snap + "/squares-%s.csv" % seed)
    sq = [r for r in sq if int(r["sheet"]) == n]
    if len(sq) != 1:
        raise SystemExit("%s sheet %d: %d squares rows" % (seed, n, len(sq)))
    sq = sq[0]
    path = "%s/out/%s/sheets/patches/patch_%d.bin" % (CHAIN, seed, n)
    h = A2.sha(path)
    if h != sq["sha256"] or h != arow["sha256"]:
        raise SystemExit("%s: sha256 %s differs from its squares or a2 row" % (path, h))
    put("a", "sheet file", os.path.relpath(os.path.realpath(path), R1), "sha256", h)

    # ------------------------------------------------------------------ a2_measure, written out
    MC.SCROLL = "PHerc0826"
    MC.SAS = CHAIN
    MC.D.selftest_passed()
    MC.selftest_ok()
    T, _ = MC.verdict_row("a2")
    S, _ = CRL.read_S()
    S = S["a2"]
    D, SQ = MC.D, MC.SQ
    t0 = time.time()
    px, py, pz, valid, _ = D.CR.lattice_from_patch(path)
    vol = D.PredVol(MC.SCROLL, cap=64)
    ii, jj = MC.eval_points(valid)
    C = vol.ch
    key = (np.rint(pz[ii, jj]).astype(np.int64) // C) * 10 ** 8 + (np.rint(py[ii, jj]).astype(np.int64) // C) * 10 ** 4 \
        + (np.rint(px[ii, jj]).astype(np.int64) // C)
    order = np.argsort(key, kind="stable")
    gi, gj = (valid.shape[0] + MC.STRIDE - 1) // MC.STRIDE, (valid.shape[1] + MC.STRIDE - 1) // MC.STRIDE
    gflag = np.zeros((gi, gj), bool)
    meas = fl = 0
    for i, j in zip(ii[order], jj[order]):
        ns = D.surface_normal(px, py, pz, valid, i, j)
        if ns is None:
            continue
        nt, _, _ = D.tensor_normal(vol, float(px[i, j]), float(py[i, j]), float(pz[i, j]), "pred")
        if nt is None:
            continue
        meas += 1
        if D.angle_deg(ns, nt) > T:
            fl += 1
            gflag[i // MC.STRIDE, j // MC.STRIDE] = True
    gsize, sz = CRL.clusters(gflag)
    hS, kept = CRL.rule_holes(gsize, S, valid)
    px32, py32, pz32 = px.astype(np.float32), py.astype(np.float32), pz.astype(np.float32)
    si, _ = SQ.median_step(valid, px32, py32, pz32, 0)
    sj, _ = SQ.median_step(valid, px32, py32, pz32, 1)
    vox_um, _ = D.voxel_um(MC.SCROLL)
    s1, i1, j1 = SQ.largest_square(valid)
    s2, i2, j2 = SQ.largest_square(valid & ~hS)
    got = dict(a2_measurable=meas, a2_flagged=fl, a2_largest_cluster=int(sz.max()) if len(sz) else 0,
               a2_kept_points=int(kept.sum()), a2_cluster_rule_square_mm=MC.mm_side(s2, si, sj, vox_um))
    for k, v in got.items():
        if str(v) != str(arow[k]):
            raise SystemExit("recomputed %s = %s, the a2-cluster row says %s: refusing to draw" % (k, v, arow[k]))
        put("a", "recomputed here and equal to the a2-cluster row: " + k, os.path.relpath(apath, here), k, v)
    for k, v in (("square_cells", s1), ("square_corner_i", i1), ("square_corner_j", j1)):
        if int(sq[k]) != int(v):
            raise SystemExit("recomputed delivered %s = %s, squares row says %s" % (k, v, sq[k]))
    sys.stderr.write("a2 recomputed in %.0f s, equal to the chain's row\n" % (time.time() - t0))
    put("a", "T* (degrees)", "lamina-crossing-detect verdict.csv a2_pred RULE", "T_star", "%g" % T, key="t_star_deg")
    put("a", "S (flagged points a cluster must exceed)", "lamina-crossing-map-1447 cluster-calibration.csv a2 RULE", "S", "%d" % S, key="cluster_s")
    put("a", "stride between evaluated points; cells", "lamina-crossing-map-1447/tools/map_crossing.py", "STRIDE", MC.STRIDE)
    put("a", "cut radius around a kept point; cells (taxicab)", "lamina-crossing-map-1447/tools/map_crossing.py", "K", MC.K)
    put("a", "grid cells i by j", "lattice_from_patch", "", "%d;%d" % valid.shape)
    put("a", "covered cells", "lattice_from_patch", "valid", int(valid.sum()))
    put("a", "cells the rule cuts", "cluster_rule.rule_holes", "", int(hS.sum()))
    put("a", "delivered square side; corner i; corner j (cells)", "square.py largest_square of valid; equal to the squares row",
        "square_cells; square_corner_i; square_corner_j", "%d;%d;%d" % (s1, i1, j1))
    put("a", "square after the rule side; corner i; corner j (cells)", "square.py largest_square of valid minus the cut cells",
        "", "%d;%d;%d" % (s2, i2, j2))
    put("a", "median cell steps i;j; voxels", "square.py median_step", "", "%.4f;%.4f" % (si, sj))

    # ------------------------------------------------------------------ the picture
    fi, fj = np.nonzero(gflag & ~kept)
    ki, kj = np.nonzero(kept)
    mm_per_cell = min(si, sj) * vox_um * 1e-3
    bar_mm = 5.0

    def draw(r_dot, r_kept):
        img = np.empty(valid.shape + (3,), np.uint8)
        img[:] = WHITE
        img[valid] = GREY
        img[hS] = CUT
        RL.dots(img, fi * MC.STRIDE, fj * MC.STRIDE, FLAG, r=r_dot)
        RL.dots(img, ki * MC.STRIDE, kj * MC.STRIDE, KEPT, r=r_kept)
        return img

    # panel a: the whole sheet, cropped to its covered cells, one pixel per cell, flags as dots of 5 cells
    va = draw(2, 2)
    RL.outline(va, i1, j1, s1, BEFORE, width=6)
    RL.outline(va, i2, j2, s2, AFTER, width=6)
    ci_, cj_ = np.nonzero(valid)
    a0, a1_, b0, b1 = ci_.min(), ci_.max() + 1, cj_.min(), cj_.max() + 1
    pa = va[a0:a1_, b0:b1].copy()
    # panel b: the two squares and a margin, --zoom pixels per cell, each flag on its own stride cell
    m = a.margin
    z0i, z1i = max(min(i1, i2) - m, 0), min(max(i1 + s1, i2 + s2) + m, valid.shape[0])
    z0j, z1j = max(min(j1, j2) - m, 0), min(max(j1 + s1, j2 + s2) + m, valid.shape[1])
    vb = draw(1, 0)[z0i:z1i, z0j:z1j]
    vb = np.repeat(np.repeat(vb, a.zoom, 0), a.zoom, 1)
    RL.outline(vb, (i1 - z0i) * a.zoom, (j1 - z0j) * a.zoom, s1 * a.zoom, BEFORE, width=6)
    RL.outline(vb, (i2 - z0i) * a.zoom, (j2 - z0j) * a.zoom, s2 * a.zoom, AFTER, width=6)
    put("a", "panel a crop i0;i1;j0;j1 (cells)", "bounding box of the covered cells", "", "%d;%d;%d;%d" % (a0, a1_, b0, b1))
    put("a", "panel a pixels per cell side; flag dot side in cells", "", "", "1; 5")
    put("b", "panel b crop i0;i1;j0;j1 (cells)", "the two squares plus the margin", "argument --margin", "%d;%d;%d;%d" % (z0i, z1i, z0j, z1j))
    put("b", "panel b pixels per cell side; flag dot side in cells", "argument --zoom", "", "%d; 3 (a flag in a large cluster: 1; the cut cells around it show)" % a.zoom)
    put("a", "flagged stride points; not in a cluster above S", "", "", int(len(fi)))
    put("a", "flagged stride points; in a cluster above S", "", "", int(len(ki)))
    put("a", "mm per cell (smaller median step times the voxel)", "square.py median_step; PHerc0826 manifest", "", "%.6f" % mm_per_cell)
    S = RL.print_size(pa.shape[1] + vb.shape[1] + 30, RL.COLUMNWIDTH_BP)
    pa, nbar_a = RL.scale_bar(pa, bar_mm, mm_per_cell, "%g mm" % bar_mm, where="bottom-left", colour=(0, 0, 0), size=48, height=14, box=None)
    vb, nbar_b = RL.scale_bar(vb, bar_mm, mm_per_cell / a.zoom, "%g mm" % bar_mm, where="bottom-left", colour=(0, 0, 0), size=48, height=14, box=(255, 255, 255))
    put("a;b", "scale bar; mm (display choice)", "", "", "%g" % bar_mm, key="scale_bar_mm")
    put("a;b", "scale bar; pixels in a; pixels in b", "", "", "%d; %d" % (nbar_a, nbar_b))
    pa = RL.label(pa, "a", colour=(0, 0, 0), box=None, size=60)
    vb = RL.label(vb, "b", colour=(0, 0, 0), box=(255, 255, 255), size=60)
    body, boxes = RL.side_by_side([pa, vb], gap=30)
    for name, box in zip("ab", boxes):
        put(name, "panel box in the png below the key; x;y;w;h", "paper/figures/%s.png" % FIGURE, "rasterlib.side_by_side",
            ";".join(str(v) for v in box))
    key1 = [(GREY, "covered"), (FLAG, "steep crossing flag"), (KEPT, "flag in a large cluster")]
    KH = 3 * (S + 10) + 20                     # the key: three lines at the print size
    pad = np.full((body.shape[0] + KH, body.shape[1], 3), 255, np.uint8)
    pad[KH:] = body
    pad = RL.legend(pad, key1, xy=(14, 10), size=S, box=None, text=(0, 0, 0))
    from PIL import Image, ImageDraw
    x2 = int(14 + S + 12 + max(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(t, font=RL.font(S)) for _, t in key1) + 2 * S)
    pad = RL.legend(pad, [(CUT, "cells cut by the rule")], xy=(x2, 10), size=S, box=None, text=(0, 0, 0))
    pad = legend_dark(pad, [(BEFORE, "largest square as delivered"), (AFTER, "largest square after the rule")],
                      xy=(x2, 10 + S + 10), size=S)
    RL.save_png(png, pad)
    comment = ("figure C12, what the raster drew, written by src/tools/%s.py at %s (cores busy %s): one delivered "
               "PHerc0826 sheet in its own grid with arm a2 recomputed by the chain's own imported code and checked "
               "equal to its a2-cluster row. Geometry only: NO INK."
               % (FIGURE, figlib.utc_now(), "not checked" if busy is None else "%.1f" % busy))
    figlib.write_plotted(out, comment, FIELDS, rows)
    sys.stderr.write("%s\n%s: %d rows\n" % (png, out, len(rows)))


def legend_dark(img, items, xy, size=20):
    """Outline swatches (a hollow square in the colour) with black words, for the two squares."""
    from PIL import Image, ImageDraw
    pil = Image.fromarray(img)
    d = ImageDraw.Draw(pil)
    f = RL.font(size)
    x, y = xy
    for k, (c, t) in enumerate(items):
        yy = y + k * (size + 10)
        d.rectangle([x, yy + 3, x + size - 4, yy + size - 1], outline=tuple(c), width=6)
        d.text((x + size + 8, yy), t, fill=(0, 0, 0), font=f)
    return np.asarray(pil).copy()


if __name__ == "__main__":
    main()
