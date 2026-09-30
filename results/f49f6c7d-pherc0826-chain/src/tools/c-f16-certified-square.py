#!/usr/bin/env python3
"""Figure C16, the page 1 image: the certified square of PHerc. 0826 seed 5364, sheet 0 of the chain as run
(C40, g 36000), on the raw scan texture sampled along that sheet, with the hole free square of the same sheet
beside it and a magnified window of the fibres inside the certified square.

RAW SCAN, NO INK DETECTOR. The grey is the raw masked scan read at the sheet's points, nothing else: no ink
model, no ink map, no filter beyond a linear grey stretch. It is drawn on the director's order of
2026-09-28T18:29:38Z (owner's word), which asks for raw scan texture with our surface on it and the label
«raw scan, no ink detector». rasterlib.py deliberately has no sampler along a sheet; the one used here is
this file's own and is used for this figure only.

What it reads, every file checked before a pixel is drawn.
  - The sheet, /data/scrollagent/runs/rev1/chain-0826/out/PHerc0826-seed5364/C40/<file of sheet 0>, whose
    sha256 must equal the one its row of evidence/studies/chain-0826/squares-PHerc0826-seed5364.csv recorded;
    the same row gives the lattice, the cell steps and the hole free square (square_cells, square_corner_i,
    square_corner_j, square_mm_min_step).
  - The certified square: the C40 row of seed 5364 sheet 0 of
    /data/scrollagent/runs/rev1/square20-0826-95/evidence/certified-squares.csv (written by
    square20-0826-95/tools/cert.py; certified_square_cells, certified_corner_i, certified_corner_j,
    certified_square_mm), sha256 in the table. That file is still rewritten while the study
    runs, so only the one row enters the table, with a sha256 of its cells. The superlative «largest certified
    square of the chain as run» is recomputed from the article's frozen evidence/studies/search-yield-0826/
    yield-seeds.csv (column best_certified_mm per delivered seed), which must give this seed the row's value;
    the tool stops otherwise, or if the square is not the largest alone.
  - The flag masks of that sheet, scratch/check_best/seed5364-C40-S0.npz (square20-0826-95/tools/check_best.py,
    cert.py's method), sha256 in the table: every cell of the certified square must be covered and carry no
    flag (v2 crossed or jumped, self conflict at one pitch, a2 cluster rule hole), or the tool stops.
  - The main panel's grey, scratch/texture_best/seed5364-C40-S0.csv (square20-0826-95/tools/texture_best.py:
    one row per covered cell of the square and 60 cells around it, the nearest level 0 voxel of the raw
    masked scan at the cell's px, py, pz), sha256 in the table. Its px, py, pz are compared with the sheet
    file's, and its grey values are recomputed here from the raw chunks at the nearest voxel; both must agree
    on every cell.
  - The zoom's grey: the raw masked scan at level 0 from the two local chunk caches texture_best.py used
    (square20-0826-95/scratch/raw-chunks, chain-0826/scratch/raw-chunks-20250821151701), sampled trilinearly
    at --zoom-samples points per cell side, the volume position of each sample interpolated bilinearly between
    the four covered cells around it.

The zoom window. Its side is --zoom-mm over the smaller cell step, rounded to cells. Among the windows of that
side whose corner lies on a stride of --zoom-stride cells and which lie wholly inside the certified square, the
one with the largest local contrast of the main panel's grey is taken, the mean absolute difference between
neighbouring cells along i plus along j (first in row order on a tie). A first rule, the largest standard
deviation, picked windows dominated by dark gaps between fibres, which show no fibre; local contrast is high where
the fibres are. The rule and the window are rows of the table.

What it writes. The plotted table evidence/figures/c-f16-certified-square.csv (key, panel, what, source_file,
source_column, value; nothing that depends on the moment or the load of the run, which go in the comment line
only), two PNG assets (--png and --png with -zoom before its extension), and src/tools/c-f16-certified-square-
body.tex, the TikZ body that c-f16-certified-square.tex inputs: the two images, the outlines, the zoom frame and
its connectors, the scale bars and the legend, every coordinate and number formed from the rows written.
With --out elsewhere than the default, the body goes beside --out and the shipped one is left alone.

Usage: c-f16-certified-square.py [--out CSV] [--png PNG]
"""
import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f16-certified-square"
RUNS = "/data/scrollagent/runs/rev1"
SEED, SHEET = "PHerc0826-seed5364", "0"
ST = RUNS + "/square20-0826-95"
CERT_CSV = ST + "/evidence/certified-squares.csv"
MASKS = ST + "/scratch/check_best/seed5364-C40-S0.npz"
TEXTURE = ST + "/scratch/texture_best/seed5364-C40-S0.csv"
SHEET_DIR = RUNS + "/chain-0826/out/" + SEED + "/C40"
SQUARES_REL = "evidence/studies/chain-0826/squares-PHerc0826-seed5364.csv"
CACHES = (ST + "/scratch/raw-chunks", RUNS + "/chain-0826/scratch/raw-chunks-20250821151701")
SHAPE, CH = (16920, 8169, 8169), 128   # raw level 0 of 20250821151701, as texture_best.py reads it
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
PANEL_CM = 8.4          # the side of each panel in the figure (display choice)
GAP_CM = 0.55


class Chunks:
    """Level 0 raw chunks from the two local flat caches only; a chunk in neither stops the tool."""

    def __init__(self):
        self.cache, self.read = {}, 0

    def get(self, c):
        if c in self.cache:
            return self.cache[c]
        a = "missing"
        for d in CACHES:
            base = "%s/%d_%d_%d" % ((d,) + c)
            if os.path.exists(base + ".bin"):
                a = np.fromfile(base + ".bin", dtype=np.uint8).reshape(CH, CH, CH)
                break
            if os.path.exists(base + ".absent"):
                a = None
                break
        if isinstance(a, str):
            raise SystemExit("chunk %r is in neither local cache: run texture_best.py's fetch first" % (c,))
        if len(self.cache) > 400:
            self.cache.clear()
        self.cache[c] = a
        self.read += 1
        return a

    def voxels(self, zi, yi, xi):
        """Integer voxel values as float; nan outside the volume or in an absent chunk."""
        out = np.full(zi.shape, np.nan)
        ins = (xi >= 0) & (yi >= 0) & (zi >= 0) & (zi < SHAPE[0]) & (yi < SHAPE[1]) & (xi < SHAPE[2])
        idx = np.flatnonzero(ins)
        key = (zi[idx] // CH) * 10 ** 8 + (yi[idx] // CH) * 10 ** 4 + (xi[idx] // CH)
        order = np.argsort(key, kind="stable")
        idx, key = idx[order], key[order]
        starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        ends = np.r_[starts[1:], len(idx)]
        for s0, s1 in zip(starts, ends):
            k = int(key[s0])
            blk = self.get((k // 10 ** 8, (k // 10 ** 4) % 10 ** 4, k % 10 ** 4))
            if blk is None:
                continue
            ii = idx[s0:s1]
            out[ii] = blk[zi[ii] % CH, yi[ii] % CH, xi[ii] % CH]
        return out

    def nearest(self, x, y, z):
        return self.voxels(np.rint(z).astype(np.int64), np.rint(y).astype(np.int64), np.rint(x).astype(np.int64))

    def trilinear(self, x, y, z):
        x0, y0, z0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64), np.floor(z).astype(np.int64)
        fx, fy, fz = x - x0, y - y0, z - z0
        out = np.zeros(x.shape)
        for dz in (0, 1):
            for dy in (0, 1):
                for dx in (0, 1):
                    w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                    out += w * self.voxels(z0 + dz, y0 + dy, x0 + dx)
        return out


def stretch_u8(v, lo, hi):
    g = np.clip((v - lo) / max(1e-9, hi - lo), 0, 1) * 255
    return np.rint(g).astype(np.uint8)


def read_csv_rows(path):
    lines = [l for l in open(path, newline="") if not l.lstrip('"').startswith("#")]
    return list(csv.DictReader(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    ap.add_argument("--zoom-mm", type=float, default=2.0)
    ap.add_argument("--zoom-stride", type=int, default=8)
    ap.add_argument("--zoom-samples", type=int, default=8)
    ap.add_argument("--bar-mm", type=float, default=5.0)
    ap.add_argument("--zoom-bar-mm", type=float, default=0.5)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_out = os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    out = os.path.abspath(a.out or default_out)
    png = os.path.abspath(a.png or os.path.join(here, "paper/figures/assets/%s-texture.png" % FIGURE))
    root, ext = os.path.splitext(png)
    png_zoom = root.replace("-texture", "") + "-zoom" + ext if root.endswith("-texture") else root + "-zoom" + ext
    body = (os.path.join(here, "tools/%s-body.tex" % FIGURE) if out == os.path.abspath(default_out)
            else os.path.join(os.path.dirname(out), "%s-body.tex" % FIGURE))
    busy = figlib.require_free_machine(2.0)
    rows = []

    def put(panel, what, source_file, source_column, value, key=""):
        rows.append(dict(key=key, panel=panel, what=what, source_file=source_file, source_column=source_column,
                         value=value))

    # ---- the sheet and its squares row
    sq_rows = [r for r in read_csv_rows(os.path.join(here, SQUARES_REL)) if r["sheet"] == SHEET]
    if len(sq_rows) != 1 or sq_rows[0]["status"] != "measured":
        raise SystemExit("%s: no single measured row for sheet %s" % (SQUARES_REL, SHEET))
    sq = sq_rows[0]
    sheet = os.path.join(SHEET_DIR, sq["file"])
    got = RL.sha256(sheet)
    if got != sq["sha256"]:
        raise SystemExit("%s: sha256 %s is not the %s its squares row measured" % (sheet, got, sq["sha256"]))
    put("a", "seed number", SQUARES_REL, "point", SEED.replace("PHerc0826-seed", ""), key="seed")
    put("a", "sheet", SQUARES_REL, "sheet", SHEET, key="sheet")
    put("a", "sheet file sha256 (equal to the squares row)", os.path.relpath(sheet, RUNS), "sha256", got)
    mask, px, py, pz, _ = figlib.read_sheet(sheet)
    ni, nj = int(sq["cells_i"]), int(sq["cells_j"])
    if mask.shape != (ni, nj):
        raise SystemExit("lattice %s is not the squares row's %dx%d" % (mask.shape, ni, nj))
    put("a", "lattice cells_i;cells_j", SQUARES_REL, "cells_i; cells_j", "%d;%d" % (ni, nj))
    step = min(float(sq["step_i_mm"]), float(sq["step_j_mm"]))
    put("a", "cell step i;j; mm", SQUARES_REL, "step_i_mm; step_j_mm", "%s;%s" % (sq["step_i_mm"], sq["step_j_mm"]))
    put("a", "cell step used for every length in the figure; mm", SQUARES_REL, "smaller of step_i_mm and step_j_mm",
        "%.6f" % step, key="step_mm")
    hs, hi0, hj0 = int(sq["square_cells"]), int(sq["square_corner_i"]), int(sq["square_corner_j"])
    put("a", "hole free square; cells", SQUARES_REL, "square_cells", hs, key="hole_free_cells")
    put("a", "hole free square corner i;j", SQUARES_REL, "square_corner_i; square_corner_j", "%d;%d" % (hi0, hj0))
    put("a", "hole free square; mm", SQUARES_REL, "square_mm_min_step", sq["square_mm_min_step"], key="hole_free_mm")

    # ---- the certified square (one row of certified-squares.csv), and the superlative over the frozen seeds
    cert_all = read_csv_rows(CERT_CSV)
    crow = [r for r in cert_all if r["source"] == "C40" and r["seed"] == SEED and r["sheet"] == SHEET]
    if len(crow) != 1 or crow[0]["status"] != "measured":
        raise SystemExit("%s: no single measured C40 row for %s sheet %s" % (CERT_CSV, SEED, SHEET))
    cr = crow[0]
    cs, ci0, cj0 = int(cr["certified_square_cells"]), int(cr["certified_corner_i"]), int(cr["certified_corner_j"])
    crel = os.path.relpath(CERT_CSV, RUNS)
    # certified-squares.csv is still rewritten by cert_watch.sh, so only this one row enters the table
    import hashlib
    cells = [cr[f] for f in sorted(cr)]
    put("a", "sha256 of the C40 row of the seed and sheet (its cells in the order of its sorted column names joined "
        "by a tab)", crel, "every column of that row", hashlib.sha256("\t".join(cells).encode()).hexdigest())
    put("a", "certified square; cells", crel, "certified_square_cells (C40 row of the seed and sheet)", cs,
        key="certified_cells")
    put("a", "certified square corner i;j", crel, "certified_corner_i; certified_corner_j", "%d;%d" % (ci0, cj0))
    put("a", "certified square; mm", crel, "certified_square_mm", cr["certified_square_mm"], key="certified_mm")
    for f in ("status", "hole_free_square_mm", "hole_free_equal_squares_row", "v2_cells", "self_conflict_cells",
              "a2_rule_cells", "certified_cells", "masks"):
        put("a", "the same row; %s" % f, crel, f, cr[f])
    if abs(cs * step - float(cr["certified_square_mm"])) > 5e-4:
        raise SystemExit("certified cells times the step %.4f differ from certified_square_mm %s"
                         % (cs * step, cr["certified_square_mm"]))
    if cr["hole_free_equal_squares_row"] != "yes":
        raise SystemExit("certified-squares.csv says its hole free square differs from the squares row")
    # the ranking: the article's frozen per seed table, which the search yield paragraph counts from
    yrel = "evidence/studies/search-yield-0826/yield-seeds.csv"
    ys = read_csv_rows(os.path.join(here, yrel))
    mine = [r for r in ys if r["seed"] == SEED]
    if len(mine) != 1 or mine[0]["best_certified_mm"] != cr["certified_square_mm"]:
        raise SystemExit("%s: best_certified_mm of %s is %r, not the row's %s"
                         % (yrel, SEED, [r["best_certified_mm"] for r in mine], cr["certified_square_mm"]))
    meas = [(r["seed"], float(r["best_certified_mm"])) for r in ys if figlib.number(r["best_certified_mm"]) is not None]
    top = max(v for _, v in meas)
    ties = sorted(sd for sd, v in meas if v == top)
    below = [v for _, v in meas if v < top]
    put("a", "seeds of the chain as run with a measured best certified square", yrel,
        "seed; best_certified_mm (a number)", len(meas), key="certified_seeds")
    put("a", "delivered seeds in that file", yrel, "seed", len(ys))
    put("a", "largest best certified square over those seeds; mm", yrel, "best_certified_mm", "%.4f" % top)
    put("a", "seeds at that value", yrel, "seed", "; ".join(ties))
    put("a", "next distinct value below it; mm", yrel, "best_certified_mm",
        "%.4f" % max(below) if below else figlib.NOT_MEASURABLE, key="certified_runner_up_mm")
    is_largest = "yes" if ties == [SEED] else "no"
    put("a", "this seed's square is the largest alone", yrel, "", is_largest, key="is_largest")
    if is_largest != "yes":
        raise SystemExit("the drawn square is not the single largest certified square of the chain as run: %s" % ties)

    # ---- the masks: every certified cell covered and unflagged
    k = np.load(MASKS)
    if k["valid"].shape != (ni, nj) or not np.array_equal(k["valid"], mask):
        raise SystemExit("%s: its covered mask is not the sheet's" % MASKS)
    put("a", "masks sha256", os.path.relpath(MASKS, RUNS), "", RL.sha256(MASKS))
    flag = k["v2c"] | k["v2j"] | k["self_conflict"] | k["a2_rule"]
    full = np.zeros((ni, nj), bool)
    full[ci0:ci0 + cs, cj0:cj0 + cs] = True
    ncov, nflag = int((full & mask).sum()), int((full & flag).sum())
    put("a", "certified square cells covered; of cells", os.path.relpath(MASKS, RUNS), "valid",
        "%d;%d" % (ncov, cs * cs))
    put("a", "certified square cells flagged (v2 crossed or jumped; self conflict; a2 cluster rule)",
        os.path.relpath(MASKS, RUNS), "v2c | v2j | self_conflict | a2_rule", nflag, key="certified_flagged")
    if ncov != cs * cs or nflag:
        raise SystemExit("the certified square is not covered and unflagged: %d covered, %d flagged" % (ncov, nflag))
    hf = np.zeros((ni, nj), bool)
    hf[hi0:hi0 + hs, hj0:hj0 + hs] = True
    if int((hf & mask).sum()) != hs * hs:
        raise SystemExit("the hole free square is not fully covered")
    put("a", "hole free square cells flagged v2;self conflict;a2 cluster rule", os.path.relpath(MASKS, RUNS),
        "v2c | v2j; self_conflict; a2_rule",
        "%d;%d;%d" % (int((hf & (k["v2c"] | k["v2j"])).sum()), int((hf & k["self_conflict"]).sum()),
                      int((hf & k["a2_rule"]).sum())))

    # ---- the main panel: the texture CSV, checked against the sheet and the raw chunks
    trel = os.path.relpath(TEXTURE, RUNS)
    put("a", "texture file sha256", trel, "", RL.sha256(TEXTURE))
    t = np.genfromtxt(TEXTURE, delimiter=",", skip_header=2, dtype=np.float64)
    ti, tj = t[:, 0].astype(np.int64), t[:, 1].astype(np.int64)
    a0, b0 = 0, 0
    head = open(TEXTURE).readline()
    import re
    m = re.search(r"rows (\d+) to (\d+) and columns (\d+) to (\d+) of the (\d+) by (\d+) lattice", head)
    if not m:
        raise SystemExit("%s: no window in the header" % TEXTURE)
    a0, a1, b0, b1 = int(m.group(1)), int(m.group(2)) + 1, int(m.group(3)), int(m.group(4)) + 1
    if (int(m.group(5)), int(m.group(6))) != (ni, nj):
        raise SystemExit("%s: lattice in the header differs" % TEXTURE)
    mi, mj = a1 - a0, b1 - b0
    put("a", "window rows a0;a1 and columns b0;b1 of the lattice (end excluded)", trel, "header",
        "%d;%d;%d;%d" % (a0, a1, b0, b1))
    gi, gj = ti + a0, tj + b0
    win = mask[a0:a1, b0:b1]
    if len(t) != int(win.sum()) or not mask[gi, gj].all():
        raise SystemExit("the texture rows are not the covered cells of the window")
    dpos = max(float(np.abs(t[:, 2] - px[gi, gj]).max()), float(np.abs(t[:, 3] - py[gi, gj]).max()),
               float(np.abs(t[:, 4] - pz[gi, gj]).max()))
    put("a", "cells of the window drawn (covered)", trel, "rows", len(t), key="window_cells")
    put("a", "largest difference of the texture's px;py;pz from the sheet file; voxels", trel, "x; y; z",
        "%.3f" % dpos)
    if dpos > 0.001:
        raise SystemExit("texture positions differ from the sheet by %.4f voxels" % dpos)
    ch = Chunks()
    again = ch.nearest(px[gi, gj].astype(np.float64), py[gi, gj].astype(np.float64), pz[gi, gj].astype(np.float64))
    val = t[:, 5]
    eq = int(np.sum((again == val) | (np.isnan(again) & np.isnan(val))))
    put("a", "texture grey recomputed here at the nearest voxel of the sheet file's px;py;pz; equal cells;of cells", trel, "value",
        "%d;%d" % (eq, len(t)))
    if eq != len(t):
        raise SystemExit("the texture's grey differs from the raw chunks on %d cells" % (len(t) - eq))
    pool = val[~np.isnan(val) & (val > 0)]
    lo, hi = float(np.percentile(pool, 1)), float(np.percentile(pool, 99))
    put("a", "grey window of the main panel; p1;p99 of its nonzero samples", trel, "value", "%.1f;%.1f" % (lo, hi))
    put("a", "cells stored 0 (masked scan)", trel, "value", int((val == 0).sum()))
    G = np.full((mi, mj), np.nan)
    G[ti, tj] = val
    img = np.full((mi, mj, 3), 255, np.uint8)
    g8 = stretch_u8(np.nan_to_num(G), lo, hi)
    img[win] = np.stack([g8] * 3, -1)[win]
    img[win & (np.nan_to_num(G) == 0)] = (0, 0, 0)
    put("a", "empty cells drawn", "", "", "white; a cell stored 0 black")
    put("a", "pixels of the main panel; one per cell", "", "", "%d;%d" % (mj, mi))
    RL.save_png(png, img)
    put("a", "main panel asset sha256 of its pixels", "paper/figures/assets/%s-texture.png (default --png)" % FIGURE, "", RL.plane_sha(img))

    # ---- the zoom window
    zc = int(round(a.zoom_mm / step))
    put("b", "zoom side; mm (display choice)", "argument --zoom-mm", "", "%g" % a.zoom_mm)
    put("b", "zoom side; cells", "zoom mm over the cell step; rounded", "", zc)
    put("b", "zoom side as drawn; mm", "cells times the cell step", "", "%.2f" % (zc * step), key="zoom_mm")
    DJ, DI = np.abs(np.diff(G, axis=1)), np.abs(np.diff(G, axis=0))   # nan where a neighbour is empty
    best, where = -1.0, None
    for i in range(ci0, ci0 + cs - zc + 1, a.zoom_stride):
        for j in range(cj0, cj0 + cs - zc + 1, a.zoom_stride):
            s = float(np.mean(DJ[i - a0:i - a0 + zc, j - b0:j - b0 + zc - 1])
                      + np.mean(DI[i - a0:i - a0 + zc - 1, j - b0:j - b0 + zc]))
            if s > best:
                best, where = s, (i, j)
    zi0, zj0 = where
    put("b", "rule for the zoom window", "argument --zoom-stride", "",
        "largest local contrast (mean absolute grey difference between neighbouring cells along i plus along j; "
        "texture_best.py's grey) among windows wholly inside the certified square with the corner on a stride of %d "
        "cells from the certified corner; first in row order on a tie" % a.zoom_stride)
    put("b", "zoom corner i;j on the lattice", "", "", "%d;%d" % (zi0, zj0))
    put("b", "zoom window local contrast; grey levels", trel, "value", "%.3f" % best)
    n = a.zoom_samples
    put("b", "samples per cell side in the zoom", "argument --zoom-samples", "", n, key="zoom_samples")
    fi = zi0 + np.arange(zc * n) / n
    fj = zj0 + np.arange(zc * n) / n
    FI, FJ = np.meshgrid(fi, fj, indexing="ij")
    i0f, j0f = np.floor(FI).astype(np.int64), np.floor(FJ).astype(np.int64)
    wi, wj = FI - i0f, FJ - j0f
    if not (mask[i0f, j0f] & mask[i0f + 1, j0f] & mask[i0f, j0f + 1] & mask[i0f + 1, j0f + 1]).all():
        raise SystemExit("a cell around the zoom is not covered")

    def bil(P):
        return ((1 - wi) * (1 - wj) * P[i0f, j0f] + wi * (1 - wj) * P[i0f + 1, j0f]
                + (1 - wi) * wj * P[i0f, j0f + 1] + wi * wj * P[i0f + 1, j0f + 1])
    X, Y, Z = bil(px.astype(np.float64)), bil(py.astype(np.float64)), bil(pz.astype(np.float64))
    V = ch.trilinear(X.ravel(), Y.ravel(), Z.ravel()).reshape(X.shape)
    put("b", "sampling of the zoom", "raw masked scan level 0; local chunk caches of texture_best.py", "",
        "position bilinear between the four covered cells; grey trilinear between the eight voxels around it")
    put("b", "zoom samples not measurable", "", "", int(np.isnan(V).sum()))
    zpool = V[~np.isnan(V) & (V > 0)]
    zlo, zhi = float(np.percentile(zpool, 1)), float(np.percentile(zpool, 99))
    put("b", "grey window of the zoom; p1;p99 of its nonzero samples", "", "", "%.1f;%.1f" % (zlo, zhi))
    zimg = np.stack([stretch_u8(np.nan_to_num(V), zlo, zhi)] * 3, -1)
    put("b", "pixels of the zoom", "", "", "%d;%d" % (zimg.shape[1], zimg.shape[0]))
    put("b", "magnification of the zoom against the main panel", "panel side over window side", "",
        "%.1f" % (mi / zc), key="zoom_magnification")
    RL.save_png(png_zoom, zimg)
    put("b", "zoom asset sha256 of its pixels", "paper/figures/assets/%s-zoom.png (default --png)" % FIGURE, "", RL.plane_sha(zimg))
    put("a", "scale bar; mm (display choice)", "argument --bar-mm", "", "%g" % a.bar_mm, key="scale_bar_mm")
    put("b", "scale bar; mm (display choice)", "argument --zoom-bar-mm", "", "%g" % a.zoom_bar_mm, key="zoom_bar_mm")
    put("a;b", "chunks of the raw scan read", "local caches", "", ch.read)

    comment = ("figure C16, what the raster drew, written by src/tools/%s.py at %s (cores busy %s): the certified "
               "square of %s sheet %s (C40) and its hole free square on raw scan texture, NO INK DETECTOR; panel a "
               "one lattice cell per pixel from texture_best.py's CSV, panel b a zoom resampled from the raw chunks. "
               "Not for a public repository without the owner's word."
               % (FIGURE, figlib.utc_now(), "not checked" if busy is None else "%.1f" % busy, SEED, SHEET))
    figlib.write_plotted(out, comment, FIELDS, rows)

    # ---- the TikZ body, from the rows
    W = PANEL_CM
    u = W / mi                       # cm per cell, the window is square
    if mi != mj:
        raise SystemExit("the texture window is not square")

    def box(i, j, s):                # lattice corner and side -> x0, y0, x1, y1 in cm, y upwards
        return ((j - b0) * u, W - (i - a0 + s) * u, (j - b0 + s) * u, W - (i - a0) * u)
    c = box(ci0, cj0, cs)
    h = box(hi0, hj0, hs)
    z = box(zi0, zj0, zc)
    X0 = W + GAP_CM
    bar = a.bar_mm / step * u
    zbar = a.zoom_bar_mm / (zc * step) * W
    L = []
    L.append("%% Generated by src/tools/%s.py from evidence/figures/%s.csv. Do not edit." % (FIGURE, FIGURE))
    L.append(r"\node[anchor=south west, inner sep=0] at (0,0) {\includegraphics[width=%.4fcm,height=%.4fcm]{../paper/figures/assets/%s}};"
             % (W, W, os.path.basename(png)))
    L.append(r"\node[anchor=south west, inner sep=0] at (%.4f,0) {\includegraphics[width=%.4fcm,height=%.4fcm]{../paper/figures/assets/%s}};"
             % (X0, W, W, os.path.basename(png_zoom)))
    L.append(r"\draw[saorange, line width=1.1pt] (%.4f,%.4f) rectangle (%.4f,%.4f);" % h)
    L.append(r"\draw[sasky, line width=1.1pt] (%.4f,%.4f) rectangle (%.4f,%.4f);" % c)
    L.append(r"\draw[white, line width=1.6pt] (%.4f,%.4f) rectangle (%.4f,%.4f);" % z)
    L.append(r"\draw[black, line width=0.6pt] (%.4f,%.4f) rectangle (%.4f,%.4f);" % z)
    for col, wd in (("white", 1.3), ("black", 0.45)):
        L.append(r"\draw[%s, line width=%gpt] (%.4f,%.4f) -- (%.4f,%.4f);" % (col, wd, z[2], z[3], X0, W))
        L.append(r"\draw[%s, line width=%gpt] (%.4f,%.4f) -- (%.4f,0);" % (col, wd, z[2], z[1], X0))
    L.append(r"\draw[black, line width=0.6pt] (%.4f,0) rectangle (%.4f,%.4f);" % (X0, X0 + W, W))
    # scale bars, lower right of each panel, on a white ground
    for (x1, blen, lab) in ((W - 0.25, bar, "%g mm" % a.bar_mm), (X0 + W - 0.25, zbar, "%g mm" % a.zoom_bar_mm)):
        L.append(r"\fill[white, opacity=0.85] (%.4f,0.12) rectangle (%.4f,0.78);" % (x1 - blen - 0.15, x1 + 0.15))
        L.append(r"\fill[black] (%.4f,0.25) rectangle (%.4f,0.33);" % (x1 - blen, x1))
        L.append(r"\node[font=\footnotesize, anchor=south, inner sep=1pt] at (%.4f,0.34) {%s};" % (x1 - blen / 2, lab))
    # legend, upper left of the main panel
    L.append(r"\node[anchor=north west, fill=white, fill opacity=0.88, text opacity=1, font=\footnotesize, align=left, inner sep=3pt] at (0.18,%.4f) {"
             r"\tikz[baseline=-0.6ex]\draw[sasky, line width=1.1pt] (0,-0.1) rectangle (0.32,0.1); certified square, %s mm\\"
             r"\tikz[baseline=-0.6ex]\draw[saorange, line width=1.1pt] (0,-0.1) rectangle (0.32,0.1); hole free square, %s mm\\"
             r"\tikz[baseline=-0.6ex]\draw[black, line width=0.6pt] (0,-0.1) rectangle (0.32,0.1); window shown at right, %.2f mm};"
             % (W - 0.18, cr["certified_square_mm"], sq["square_mm_min_step"], zc * step))
    L.append(r"\node[anchor=south west, fill=white, fill opacity=0.88, text opacity=1, font=\footnotesize, inner sep=2pt] at (0.18,0.18) {raw scan, no ink detector};")
    L.append(r"\node[anchor=north west, fill=white, fill opacity=0.88, text opacity=1, font=\footnotesize, inner sep=2pt] at (%.4f,%.4f) {%.1f$\times$, resampled from the raw scan};"
             % (X0 + 0.18, W - 0.18, mi / zc))
    with open(body, "w") as fh:
        fh.write("\n".join(L) + "\n")
    sys.stderr.write("%s\n%s\n%s: %d rows; body %s; chunks %d\n" % (png, png_zoom, out, len(rows), body, ch.read))


if __name__ == "__main__":
    main()
