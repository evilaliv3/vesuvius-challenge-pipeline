#!/usr/bin/env python3
"""Figure C23, a raster: Youssef Nader's v8-in ink model on the certified square of seed 6273 of PHerc. 0826 (route R2c, the
square with crossings between traced surfaces adjudicated), in the depth order measured on PHerc0139 w016, on the sheet
and on its two null copies, in the square's own grid, with a mm scale bar only.

Shown by the owner's decision of 2026-09-30 «on condition that there are no clear indications of where they are»: no
coordinate, no height, no seed or square centre position, no umbilicus, no axis in scan voxels. The table writes grid cells
and file digests only.

What it reads (never written):
  - ink-v8in-0826's maps of the seed6273 window, stride 21, the order measured on w016 (--reverse on this surface by the side
    sign): scratch/pred/s6273/base-{sheet,plus,minus}-read-reverse-w016-order.npy, in the window's render pixel grid;
  - the window (ink-square-0826-seed2604 scratch/rr-seed6273-squarecentre-R2cnative): window.json (the window's first cell
    on each axis of the route's grid) and window.tifxyz/meta.json (its scale, cells per render pixel);
  - this work's copy of render-routes-0826 square-checks-adjudicated.csv (src/inputs/render-routes-0826): the certified
    square's side in cells, its corner and the cell step in mm.
The window's render rows follow the grid's second axis and its columns the first (checked when this tool was written: the
texture of the render's middle layer against the route's values grid, correlation 0.89 against 0.01 the other way); the
square is cut in render pixels and turned so that rows follow the grid's first axis, as Figure C21 panel (a) draws it.
Probability 0 black to 1 white, the same stretch on the three panels; a 5 mm bar.

Usage: c-f23-v8in-0826.py [--out CSV] [--png PNG]
"""
import argparse, csv, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f23-v8in-0826"
RUNS = "/data/scrollagent/runs/rev1"
PRED = RUNS + "/ink-v8in-0826/scratch/pred/s6273"
WIN = RUNS + "/ink-square-0826-seed2604/scratch/rr-seed6273-squarecentre-R2cnative"
SURFACE = "PHerc0826-seed6273-squarecentre"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
BAR_MM = 5.0
BIN = 3                 # display bin: block mean of 3 by 3 render pixels, so that the PNG stays a few megabytes
PANELS = (("a", "sheet", "the sheet"), ("b", "plus", "null copy, one gap"), ("c", "minus", "null copy, the other gap"))
# Both depth orders (owner's order of 2026-09-30): the top row in the order measured on w016, the bottom row in the other
# order, the same pixels, the same stretch (probability 0 black to 1 white) on every panel.
ORDERS = (("", "reverse-w016-order", "the order measured on w016"), ("2", "normal-not-w016-order", "the other order"))
SHORT = {"sheet": "sheet", "plus": "copy, one gap", "minus": "copy, other gap"}
OSHORT = {"reverse-w016-order": "w016 order", "normal-not-w016-order": "other order"}


def rd(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip('"').startswith("#")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()
    here = os.path.dirname(HERE)
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    png = a.png or os.path.join(here, "paper/figures/%s.png" % FIGURE)
    rows = []

    def put(panel, what, sf, sc, value, key=""):
        rows.append(dict(key=key, panel=panel, what=what, source_file=sf, source_column=sc, value=value))

    # Since 2026-09-30 (the referee): the square as it stood before the adjudication, the square whose shares the text
    # gives (ink-v8in-0826 ratio-calibration.csv, «square (render pixels 241:3437)»), so figure and text are one square.
    td = [r for r in rd(os.path.join(here, "inputs/render-routes-0826/square-three-definitions.csv"))
          if r["route"] == "R2cnative" and r["surface"] == SURFACE]
    ad = [r for r in rd(os.path.join(here, "inputs/render-routes-0826/square-checks-adjudicated.csv"))
          if r["route"] == "R2cnative" and r["surface"] == SURFACE]
    if len(td) != 1 or len(ad) != 1:
        raise SystemExit("square-three-definitions.csv or square-checks-adjudicated.csv: not one row of %s" % SURFACE)
    step = float(ad[0]["step_mm"])
    src = "inputs/render-routes-0826/square-three-definitions.csv"
    put("a;b;c", "square before the adjudication; mm", src, "a_certified_this_study_mm", td[0]["a_certified_this_study_mm"], key="square_mm")
    put("a;b;c", "seed of the start", src, "surface", SURFACE.split("-")[1].replace("seed", ""), key="seed")
    wj = json.load(open(os.path.join(WIN, "window.json")))
    s = float(json.load(open(os.path.join(WIN, "window.tifxyz", "meta.json")))["scale"][0])
    i0, j0, ci, cj, side = int(wj["i0"]), int(wj["j0"]), int(wj["I0"]), int(wj["J0"]), int(wj["S"])
    if abs(side * step - float(td[0]["a_certified_this_study_mm"])) > 5e-3:
        raise SystemExit("window.json's square (%d cells) is not column a's %s mm" % (side, td[0]["a_certified_this_study_mm"]))
    # render pixels: rows follow the grid's second axis (j), columns the first (i)
    r0, r1 = int(round((cj - j0) / s)), int(round((cj + side - j0) / s))
    c0, c1 = int(round((ci - i0) / s)), int(round((ci + side - i0) / s))
    mmpp = step * s
    put("a;b;c", "square in the window's render pixels, rows and columns (grid cells over the scale)", "window.json; window.tifxyz/meta.json",
        "I0; J0; S; i0; j0; scale", "%d:%d;%d:%d" % (r0, r1, c0, c1))
    put("a;b;c", "mm per render pixel", "square-checks-adjudicated.csv step_mm; window.tifxyz/meta.json", "step_mm times scale", "%.6f" % mmpp)
    def load(stem):
        mp = {}
        for letter, surf, words in PANELS:
            f = os.path.join(PRED, "base-%s-read-%s.npy" % (surf, stem))
            if not os.path.exists(f):
                raise SystemExit("%s is missing" % f)
            P = np.load(f, mmap_mode="r")
            if P.shape[0] < r1 or P.shape[1] < c1:
                raise SystemExit("%s: map %s smaller than the square's pixels" % (f, P.shape))
            mp[surf] = (f, np.asarray(P[r0:r1, c0:c1]).astype(np.float32).T)          # rows follow the grid's first axis
        return mp
    maps = load(ORDERS[0][1])
    other = load(ORDERS[1][1])
    common = np.logical_and.reduce([m > 0 for _, m in maps.values()])
    put("a;b;c", "pixels covered on all three maps (the shares' pixel set)", "", "", int(common.sum()))
    RC = os.path.join(here, "evidence/studies/ink-v8in-0826/ratio-calibration.csv")
    rc = [r for r in rd(RC) if r["surface"] == "s6273" and r["scroll"] == "PHerc0826"]
    if len(rc) != 1:
        raise SystemExit("ratio-calibration.csv: %d rows of s6273" % len(rc))
    shares = {}
    for letter, surf, words in PANELS:
        f, crop = maps[surf]
        shares[surf] = float((crop[common] >= 0.5).mean())
        same = abs(shares[surf] - float(rc[0]["share_ge_0.5_%s" % surf])) < 5e-6
        put(letter, "%s: share of the common pixels at probability >= 0.5, against ratio-calibration.csv" % words,
            "ink-v8in-0826/scratch/pred/s6273/" + os.path.basename(f), "probability; share_ge_0.5_%s" % surf,
            "%.5f (%s)" % (shares[surf], "equal" if same else "DIFFERENT"))
        if not same:
            raise SystemExit("%s: share %.5f is not ratio-calibration.csv's %s" % (surf, shares[surf], rc[0]["share_ge_0.5_%s" % surf]))
    common2 = np.logical_and.reduce([m > 0 for _, m in other.values()])
    put("d;e;f", "pixels covered on all three maps of the other order", "", "", int(common2.sum()))
    for letter, surf, words in PANELS:
        f, crop = other[surf]
        put(chr(ord(letter) + 3), "%s, the other order: share of those pixels at probability >= 0.5 (descriptive)" % words,
            "ink-v8in-0826/scratch/pred/s6273/" + os.path.basename(f), "probability", "%.5f" % float((crop[common2] >= 0.5).mean()))
    rows_img = []
    for (suffix, stem, oname), mp in zip(ORDERS, (maps, other)):
        imgs = []
        for letter, surf, words in PANELS:
            L = letter if not suffix else chr(ord(letter) + 3)
            f, crop = mp[surf]
            put(L, "%s, %s: map read (sha256)" % (words, oname), "ink-v8in-0826/scratch/pred/s6273/" + os.path.basename(f), "", RL.sha256(f))
            g = (np.clip(crop, 0, 1) * 255).astype(np.uint8)
            g = RL.block_mean(g, BIN)
            img = RL.rgb(g)
            RL.print_size(3 * img.shape[1] + 2 * 24, RL.TEXTWIDTH_BP)       # three panels a row at the text width
            if L == "a":
                img, nbar = RL.scale_bar(img, BAR_MM, mmpp * BIN, "%g mm" % BAR_MM, size=30, height=10)
                put("a", "scale bar; pixels", "", "", nbar)
            img = RL.label(img, "(%s) %s, %s" % (L, SHORT[surf], OSHORT[stem]), size=30)
            imgs.append(img)
        rows_img.append(RL.side_by_side(imgs, gap=24)[0])
    put("a;b;c", "scale bar; mm (display choice)", "", "", "%g" % BAR_MM, key="bar_mm")
    put("a;b;c", "depth order", "", "", "the order measured on w016 (--reverse on this surface)")
    put("d;e;f", "depth order", "", "", "the other order (normal on this surface)")
    put("a;b;c", "display bin; render pixels per side (block mean)", "", "", BIN)
    put("a;b;c", "labelled region the depth order was measured on", "", "", "w016", key="region")
    put("a;b;c" if "c-f23" in __file__ else "a;b", "model", "hf-files.csv of ink-v8in-0826", "repo YoussefMoNader/ink-8um-v8in", "v8-in", key="model")
    canvas = RL.stacked(rows_img, gap=24)[0]
    RL.save_png(png, canvas)
    figlib.write_plotted(out, "figure C23, written by src/tools/%s.py at %s: v8-in on the square of %s (R2c) as it stood before the "
                         "adjudication, in both depth orders (top the order measured on w016, bottom the other), sheet and two null copies, the square's own grid; NO POSITION: grid "
                         "cells and digests only. Owner's decision of 2026-09-30: ink detector maps of PHerc0826 may be published "
                         "without location cues; this figure carries none."
                         % (FIGURE, figlib.utc_now(), SURFACE), FIELDS, rows)
    sys.stderr.write("%s\n%s: %d rows\n" % (png, out, len(rows)))


if __name__ == "__main__":
    main()
