#!/usr/bin/env python3
"""Figure C24, a raster: the other v8-in reads of PHerc. 0826, in the style of Figure C23 (owner's order of 2026-09-30:
show the image of every read, although none found anything).

  (a) and (b): the square of seed 5364 (route R2c, as it stood before the adjudication), the sheet read in the order measured
      on w016 and in the other order: ink-v8in-0826 scratch/pred/s5364/base-sheet-read-{reverse-w016-order,
      normal-not-w016-order}.npy, cut to the square in the window's render pixels as Figure C23 cuts the seed 6273 square
      (ink-v8in-0826 scratch/r5364/window.json and window.tifxyz/meta.json), rows turned to follow the grid's first axis;
  (c) and (d): the whole surface the organisers' tracer grew on route R2d from sheet 0 of seed 2715, in the order measured on
      w016 and in the other order: ink-v8in-0826-r2d scratch/pred/r2d-s2715-S0-sheet-{normal,reverse}.npy, in the surface
      render's own pixel grid (one pixel per voxel of 9.362 um: vc_render_tifxyz --scale 1 --voxel-size 9.362, the study's
      declaration), pixels no tile covered drawn white.

Each panel in its own grid, probability 0 black to 1 white on every panel, block means for display, a 5 mm bar on each.
Shown by the owner's decision of 2026-09-30: ink detector maps of PHerc0826 may be published without location cues. No
coordinate, no height, no seed or square centre position is drawn or written; the table holds grid cells, display factors and
file digests only. The numbers of these reads are in the table of the article (derived/v8in-reads.csv), not here.

Usage: c-f24-v8in-more.py [--out CSV] [--png PNG]
"""
import argparse, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f24-v8in-more"
RUNS = "/data/scrollagent/runs/rev1"
P5 = RUNS + "/ink-v8in-0826/scratch/pred/s5364"
W5 = RUNS + "/ink-v8in-0826/scratch/r5364"
PR = RUNS + "/ink-v8in-0826-r2d/scratch/pred"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
BAR_MM = 5.0
VOXEL_MM = 0.009362
PANEL_PX = 1000            # about this many pixels a side for each panel on the canvas
GAP = 24


def display(P, bin_):
    """Block mean over covered pixels (value above 0); a block with none is white. Returns an RGB uint8 array."""
    h, w = (P.shape[0] // bin_) * bin_, (P.shape[1] // bin_) * bin_
    Q = P[:h, :w].reshape(h // bin_, bin_, w // bin_, bin_)
    cov = (Q > 0)
    n = cov.sum(axis=(1, 3))
    s = np.where(cov, Q, 0).sum(axis=(1, 3), dtype=np.float64)
    m = np.where(n > 0, s / np.maximum(n, 1), 0.0)
    g = (np.clip(m, 0, 1) * 255).astype(np.uint8)
    img = RL.rgb(g)
    img[n == 0] = 255
    return img


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

    # the seed 5364 square in the window's render pixels, as Figure C23 cuts the seed 6273 square
    wj = json.load(open(os.path.join(W5, "window.json")))
    s = float(json.load(open(os.path.join(W5, "window.tifxyz", "meta.json")))["scale"][0])
    i0, j0, ci, cj, side, step = int(wj["i0"]), int(wj["j0"]), int(wj["I0"]), int(wj["J0"]), int(wj["S"]), float(wj["STEP"])
    r0, r1 = int(round((cj - j0) / s)), int(round((cj + side - j0) / s))
    c0, c1 = int(round((ci - i0) / s)), int(round((ci + side - i0) / s))
    put("a;b", "square of seed 5364 in the window's render pixels, rows and columns", "ink-v8in-0826 scratch/r5364 window.json; meta.json",
        "I0; J0; S; i0; j0; scale", "%d:%d;%d:%d" % (r0, r1, c0, c1))
    put("a;b", "the square's side before the adjudication; mm", "ink-v8in-0826 scratch/r5364 window.json", "MM", wj["MM"])
    panels = []
    for letter, stem, words in (("a", "reverse-w016-order", "seed 5364 square, w016 order"),
                                ("b", "normal-not-w016-order", "seed 5364 square, other order")):
        f = os.path.join(P5, "base-sheet-read-%s.npy" % stem)
        P = np.load(f, mmap_mode="r")
        if P.shape[0] < r1 or P.shape[1] < c1:
            raise SystemExit("%s: map %s smaller than the square's pixels" % (f, P.shape))
        crop = np.asarray(P[r0:r1, c0:c1]).astype(np.float32).T
        bin_ = max(1, int(round(max(crop.shape) / PANEL_PX)))
        put(letter, "%s: map read (sha256)" % words, "ink-v8in-0826/scratch/pred/s5364/" + os.path.basename(f), "", RL.sha256(f))
        put(letter, "%s: display bin, render pixels per side" % words, "", "", bin_)
        panels.append((letter, words, display(crop, bin_), step * s * bin_))
    for letter, order, words in (("c", "normal", "seed 2715 whole surface, w016 order"),
                                 ("d", "reverse", "seed 2715 whole surface, other order")):
        f = os.path.join(PR, "r2d-s2715-S0-sheet-%s.npy" % order)
        P = np.load(f, mmap_mode="r")
        arr = np.asarray(P).astype(np.float32)
        bin_ = max(1, int(round(max(arr.shape) / PANEL_PX)))
        put(letter, "%s: map read (sha256)" % words, "ink-v8in-0826-r2d/scratch/pred/" + os.path.basename(f), "", RL.sha256(f))
        put(letter, "%s: render pixels high and wide; display bin" % words, "", "", "%d;%d; %d" % (arr.shape + (bin_,)))
        put(letter, "%s: pixels no tile covered (drawn white)" % words, "", "", int((arr <= 0).sum()))
        panels.append((letter, words, display(arr, bin_), VOXEL_MM * bin_))
    # one row of four panels at the text width (a taller figure held the float queue back to the end of the article)
    top, bot = panels, []
    width = sum(p[2].shape[1] for p in top) + GAP * (len(top) - 1)
    put("a;b;c;d", "text size; pixels (8 pt at the text width)", "rasterlib.print_size", "", RL.print_size(width, RL.TEXTWIDTH_BP))
    rows_img = []
    for row in (top,):
        imgs = []
        for letter, words, img, mmpp in row:
            img, nbar = RL.scale_bar(img, BAR_MM, mmpp, "%g mm" % BAR_MM, colour=(255, 255, 255), box=(0, 0, 0))
            put(letter, "scale bar; pixels", "", "", nbar)
            short = words.replace("seed ", "").replace(" square", "").replace(" whole surface", "")   # fits the panel at 8 pt
            imgs.append(RL.label(img, "(%s) %s" % (letter, short)))
        rows_img.append(RL.side_by_side(imgs, gap=GAP)[0])
    canvas = RL.stacked(rows_img, gap=GAP)[0]
    put("a;b;c;d", "scale bar; mm (display choice)", "", "", "%g" % BAR_MM, key="bar_mm")
    put("a;b;c;d", "labelled region the depth order was measured on", "", "", "w016", key="region")
    put("a;b", "seed of the square's start", "ink-v8in-0826/evidence/describe-v2.csv", "square", "5364", key="seed_1")
    put("c;d", "route, sheet and seed of the whole surface", "ink-v8in-0826-r2d/evidence/describe.csv", "header", "R2d", key="route")
    put("c;d", "sheet of the seed the route started from", "ink-v8in-0826-r2d/evidence/describe.csv", "header", "0", key="sheet")
    put("c;d", "seed the route started from", "ink-v8in-0826-r2d/evidence/describe.csv", "header", "2715", key="seed_2")
    put("a;b;c;d", "model", "hf-files.csv of ink-v8in-0826", "repo YoussefMoNader/ink-8um-v8in", "v8-in", key="model")
    RL.save_png(png, canvas)
    figlib.write_plotted(out, "figure C24, written by src/tools/%s.py at %s: v8-in on the seed 5364 square (R2c, before the "
                         "adjudication) and on the whole R2d surface of seed 2715, both depth orders, sheet only, each in its own grid; "
                         "NO POSITION: grid cells, display factors and digests only. Owner's decision of 2026-09-30: ink detector maps of "
                         "PHerc0826 may be published without location cues; this figure carries none."
                         % (FIGURE, figlib.utc_now()), FIELDS, rows)
    sys.stderr.write("%s\n%s: %d rows\n" % (png, out, len(rows)))


if __name__ == "__main__":
    main()
