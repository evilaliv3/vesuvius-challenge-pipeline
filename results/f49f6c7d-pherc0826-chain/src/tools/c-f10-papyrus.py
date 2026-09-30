#!/usr/bin/env python3
"""Figure C10, a raster: papyrus. One axial slice of the raw scan of PHerc. 0826 through the largest
square of the chain, with the delivered sheets of that seed drawn where they cross the slice, and beside
it the same crop with the m7 surface prediction laid over the grey.

Which sheet, and the superlative. The largest square is recomputed here over every row of every
evidence/studies/chain-0826/squares-<seed>.csv (the snapshot this work ships, so the figure and the
article read the same bytes) (figlib.largest_delivered_sheet, column square_mm_min_step,
status measured), never taken from a sentence; the ties, the runner up and the number of seeds and
sheets the word covers go into the plotted table. The sheet file is checked against the sha256 its
squares row recorded before a pixel is drawn.

The slice. z is the median pz of the square's cells, rounded. The crop is --width-mm wide and high,
centred on the median position of the square's crossings of that slice, and is read from the raw
masked scan at level 0 (open data bucket, URL in the table) through the shared chunk cache; the m7
panel reads the same rows and columns of the local prediction zarr the PHerc0826 manifest names.

The traces. For each of the seed's delivered sheets, the points where its grid crosses the plane
(rasterlib.plane_crossings: along every edge between two covered neighbouring cells whose heights lie
on the two sides of z, the interpolated position). The crossings of the best sheet are red, and those
that start from a cell inside its largest square are yellow; the other sheets of the seed are cyan.

Display. The slice is contrast stretched (figlib.stretch, both ends in the table) and shown at one
pixel per --bin by --bin voxels (block mean); the millimetres per pixel are that factor times the
voxel read from the manifest through pipeline/datasets/voxel.py, and the scale bar is drawn from them.

NO INK. Only a plane of the scan and the sheets' geometry are drawn; nothing is sampled along a sheet.
Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.

Usage: c-f10-papyrus.py [--out CSV] [--png PNG]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f10-papyrus"
RUNS = "/data/scrollagent/runs/rev1"
CHAIN = RUNS + "/chain-0826"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
STUDIES_REL = "evidence/studies/chain-0826"
GLOB = STUDIES_REL + "/squares-PHerc0826-seed*.csv"
RED, YELLOW, CYAN, GREEN = (235, 40, 40), (255, 215, 0), (0, 200, 255), (40, 230, 90)

# Locations withheld (director 2026-09-30, the owner's decision): a scan position (a height, a crop box in scan voxels, a
# point) is computed and checked here as before, and the plotted table says «withheld» in its place.
WITHHELD = "withheld"


def slice_height(here):
    """The height of the cut, as main() takes it: the median pz of the cells of the largest square of the chain, on its
    sheet, checked as main() checks it. Figure C11 cuts at this height; neither table writes it."""
    found = figlib.largest_delivered_sheet(os.path.join(here, STUDIES_REL), pattern="squares-PHerc0826-seed*.csv")
    best = found["row"]
    sheet = os.path.join(CHAIN, "out", found["point"], "C40", best["file"])
    if RL.sha256(sheet) != best["sha256"]:
        raise SystemExit("%s: sha256 is not the %s its squares row measured" % (sheet, best["sha256"]))
    what = "figure C10, %s sheet %s" % (found["point"], best["sheet"])
    side = int(figlib.required_number(best, "square_cells", what))
    ci = int(figlib.required_number(best, "square_corner_i", what))
    cj = int(figlib.required_number(best, "square_corner_j", what))
    mask, px, py, pz, _ = figlib.read_sheet(sheet)
    if mask.shape != (int(best["cells_i"]), int(best["cells_j"])):
        raise SystemExit("%s: grid %s is not the cells_i by cells_j of its squares row" % (sheet, mask.shape))
    sub = np.zeros_like(mask)
    sub[ci:ci + side, cj:cj + side] = True
    sub &= mask
    if sub.sum() != side * side:
        raise SystemExit("%s: the square is not fully covered on this grid" % sheet)
    return int(round(float(np.median(pz[sub]))))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    ap.add_argument("--width-mm", type=float, default=6.0)   # 6 mm since 2026-09-30: no roll boundary in the crop (referee)
    ap.add_argument("--bin", type=int, default=1)
    ap.add_argument("--bar-mm", type=float, default=1.0)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    png = a.png or os.path.join(here, "paper/figures/%s.png" % FIGURE)
    busy = figlib.require_free_machine(2.0)
    rows = []

    def put(panel, what, source_file, source_column, value, key=""):
        rows.append(dict(key=key, panel=panel, what=what, source_file=source_file, source_column=source_column,
                         value=value))

    found = figlib.largest_delivered_sheet(os.path.join(here, STUDIES_REL), pattern="squares-PHerc0826-seed*.csv")
    best = found["row"]
    seed = found["point"]
    sq_rel = os.path.relpath(found["csv_path"], here)
    sheet_dir = os.path.join(CHAIN, "out", seed, "C40")
    sheet = os.path.join(sheet_dir, best["file"])
    got = RL.sha256(sheet)
    if got != best["sha256"]:
        raise SystemExit("%s: sha256 %s is not the %s its squares row measured" % (sheet, got, best["sha256"]))
    put("a", "seed drawn", sq_rel, "point", seed)
    put("a", "seed number", sq_rel, "point", seed.replace("PHerc0826-seed", ""), key="seed")
    put("a", "sheet with the largest square", sq_rel, "sheet", best["sheet"], key="sheet")
    put("a", "sheet file", os.path.relpath(sheet, RUNS), "sha256", got)
    put("a", "largest square over every delivered sheet of the chain; mm",
        GLOB, "square_mm_min_step", best["square_mm_min_step"], key="largest_square_mm")
    put("a", "seeds tied at that value", GLOB, "point",
        "; ".join(found["ties"]))
    put("a", "next distinct value below it; mm", GLOB,
        "square_mm_min_step", "%.4f" % found["runner_up"] if found["runner_up"] is not None else figlib.NOT_MEASURABLE,
        key="runner_up_mm")
    put("a", "seeds the superlative was recomputed over", GLOB,
        "point", found["arms"], key="seeds_compared")
    import glob as _g
    put("a", "squares files read", GLOB, "files", len(_g.glob(os.path.join(here, GLOB))), key="squares_files")
    put("a", "measured sheets the superlative was recomputed over",
        GLOB, "square_mm_min_step", found["sheets"], key="sheets_compared")

    what = "figure C10, %s sheet %s" % (seed, best["sheet"])
    side = int(figlib.required_number(best, "square_cells", what))
    ci = int(figlib.required_number(best, "square_corner_i", what))
    cj = int(figlib.required_number(best, "square_corner_j", what))
    mask, px, py, pz, _ = figlib.read_sheet(sheet)
    if mask.shape != (int(best["cells_i"]), int(best["cells_j"])):
        raise SystemExit("%s: grid %s is not the cells_i by cells_j of its squares row" % (sheet, mask.shape))
    sub = np.zeros_like(mask)
    sub[ci:ci + side, cj:cj + side] = True
    sub &= mask
    if sub.sum() != side * side:
        raise SystemExit("%s: the square is not fully covered on this grid" % sheet)
    z = int(round(float(np.median(pz[sub]))))
    if z != slice_height(here):
        raise SystemExit("the cut's height is not slice_height()'s, which figure C11 cuts at")
    put("a", "z slice (level 0 voxels)", os.path.relpath(sheet, RUNS), "pz of the square's cells; median rounded", WITHHELD)
    put("a", "square side; cells", sq_rel, "square_cells", side)
    put("a", "square top left corner i;j", sq_rel, "square_corner_i; square_corner_j", "%d;%d" % (ci, cj))

    vox, vox_src = RL.voxel()
    n = int(round(a.width_mm * 1000.0 / vox))
    n -= n % a.bin
    ys, xs, ii, jj = RL.plane_crossings(mask, px, py, pz, z)
    insq = (ii >= ci) & (ii < ci + side) & (jj >= cj) & (jj < cj + side)
    if not insq.any():
        raise SystemExit("the square does not cross the slice it was chosen from")
    cy, cx = float(np.median(ys[insq])), float(np.median(xs[insq]))
    y0, x0 = int(round(cy)) - n // 2, int(round(cx)) - n // 2
    y0, x0 = max(y0, 0), max(x0, 0)
    y1, x1 = y0 + n, x0 + n
    if not (y1 - y0 == x1 - x0 == n):
        raise SystemExit("the crop is not %d voxels square" % n)
    put("a", "crop y0;y1;x0;x1 (level 0 voxels)", os.path.relpath(sheet, RUNS),
        "median py and px of the square's crossings of the slice; plus and minus half the width", WITHHELD)
    put("a", "crop width; mm (display choice)", "argument --width-mm", "", "%g" % a.width_mm, key="crop_mm")
    put("a", "crop width; voxels", "width in mm over the voxel; rounded to a multiple of the display bin", "", n)
    put("a", "voxel; um", "pipeline/datasets/manifests/PHerc0826.json", "voxel_um through pipeline/datasets/voxel.py", "%g" % vox)
    put("a", "where that voxel comes from", "pipeline/datasets/manifests/PHerc0826.json", "voxel_um_source", vox_src)
    put("a", "display bin; voxels per pixel side (block mean)", "argument --bin", "", a.bin)
    mmpp = a.bin * vox / 1000.0
    put("a", "mm per pixel", "display bin times the voxel", "", "%.6f" % mmpp)

    reader = RL.RawReader(0)
    grey, nchunks = reader.plane(z, y0, y1, x0, x1)
    put("a", "grey source", RL.RAW_URL + "/0", "raw masked scan level 0; uint8; compressor null", "open data bucket")
    put("a", "raw level 0 shape z;y;x", RL.RAW_URL + "/0/.zarray", "shape", ";".join(str(v) for v in reader.shape))
    put("a", "chunks covering the crop", RL.RAW_URL + "/0", "one z layer of chunks", nchunks)
    put("a", "sha256 of the crop's grey bytes before the stretch", RL.RAW_URL + "/0", "plane z; rows y0:y1; columns x0:x1",
        RL.plane_sha(grey))
    put("a", "share of crop voxels that are zero (masked or absent)", RL.RAW_URL + "/0", "", "%.4f" % float((grey == 0).mean()))
    g2 = RL.block_mean(grey, a.bin)
    g2, lo, hi = figlib.stretch(g2)
    put("a", "display window; low and high grey", "the binned slice itself",
        "1st and 99.5th percentile of its non zero pixels (figlib.stretch)", "%.0f;%.0f" % (lo, hi))

    pa = RL.rgb(g2)
    drawn_other = 0
    per_sheet = []
    files = sorted((f for f in os.listdir(sheet_dir) if f.startswith("patch_") and f.endswith(".bin")),
                   key=lambda f: int(f[6:-4]))
    for f in files:
        if f == best["file"]:
            continue
        m2, px2, py2, pz2, _ = figlib.read_sheet(os.path.join(sheet_dir, f))
        y2, x2, _, _ = RL.plane_crossings(m2, px2, py2, pz2, z)
        k = RL.dots(pa, (y2 - y0) / a.bin, (x2 - x0) / a.bin, CYAN, r=1)
        per_sheet.append("%s:%d" % (f, k))
        drawn_other += k
    kb = RL.dots(pa, (ys[~insq] - y0) / a.bin, (xs[~insq] - x0) / a.bin, RED, r=1)
    ks = RL.dots(pa, (ys[insq] - y0) / a.bin, (xs[insq] - x0) / a.bin, YELLOW, r=1)
    put("a", "sheet files of the seed", os.path.relpath(sheet_dir, RUNS), "patch_<n>.bin", len(files), key="sheets_of_seed")
    ncross = sum(1 for x in per_sheet if int(x.split(":")[1]) > 0) + (1 if kb + ks > 0 else 0)
    put("a", "sheets of the seed that cross the crop (the best sheet included)", os.path.relpath(sheet_dir, RUNS),
        "rasterlib.plane_crossings, files with at least one crossing drawn", ncross, key="sheets_crossing")
    put("a", "crossings of the best sheet drawn inside the crop; outside its square", os.path.relpath(sheet, RUNS),
        "rasterlib.plane_crossings", kb)
    put("a", "crossings of the best sheet drawn inside the crop; from cells of its square", os.path.relpath(sheet, RUNS),
        "rasterlib.plane_crossings", ks)
    put("a", "crossings of the other sheets drawn inside the crop; per file", os.path.relpath(sheet_dir, RUNS),
        "rasterlib.plane_crossings", "; ".join(per_sheet))
    put("a", "crossings of the other sheets drawn inside the crop; total", os.path.relpath(sheet_dir, RUNS),
        "rasterlib.plane_crossings", drawn_other)
    put("a", "cells of the best sheet within half a voxel of the slice (the cells themselves)", os.path.relpath(sheet, RUNS),
        "abs(pz - z) <= 0.5", int((mask & (np.abs(pz - z) <= 0.5)).sum()))

    pred, ppath, model, psrc = RL.pred_plane(z, y0, y1, x0, x1)
    ppath = "local copy of the published prediction (%s)" % "/".join(ppath.rstrip("/").split("/")[-3:])  # no absolute path of this machine
    put("b", "prediction", ppath, "model (manifest)", model)
    put("b", "prediction published at", "pipeline/datasets/manifests/PHerc0826.json", "source", psrc)
    put("b", "sha256 of the crop's prediction bytes", ppath, "plane z; rows y0:y1; columns x0:x1", RL.plane_sha(pred))
    put("b", "prediction values present", ppath, "unique values of the crop", ";".join(str(int(v)) for v in np.unique(pred)))
    put("b", "share of crop voxels predicted surface (value 255)", ppath, "", "%.4f" % float((pred == 255).mean()))
    p2 = RL.block_mean((pred == 255).astype(np.uint8) * 255, a.bin) >= 128
    pb = RL.tint(RL.rgb(g2), p2, GREEN, 0.55)
    put("b", "overlay rule", ppath, "binned share of 255 at least one half", "green at alpha 0.55")

    label_bar = "%g mm" % a.bar_mm
    put("a;b", "text size; pixels (8 pt at the column width)", "rasterlib.print_size", "", RL.print_size(pa.shape[1] + pb.shape[1] + 16, RL.COLUMNWIDTH_BP))
    pa, nbar = RL.scale_bar(pa, a.bar_mm, mmpp, label_bar)
    pb, _ = RL.scale_bar(pb, a.bar_mm, mmpp, label_bar)
    pa = RL.label(pa, "a")
    pb = RL.label(pb, "b")
    pa = RL.legend(pa, ([(RED, "best sheet")] if kb else []) + [(YELLOW, "its largest square"), (CYAN, "other sheets of the seed")],
                   xy=(14, 64))
    pb = RL.legend(pb, [(GREEN, "m7 surface prediction")], xy=(14, 64))
    put("a;b", "scale bar; mm (display choice)", "argument --bar-mm", "", "%g" % a.bar_mm, key="scale_bar_mm")
    put("a;b", "scale bar; pixels", "bar mm over mm per pixel; rounded", "", nbar)
    canvas, boxes = RL.side_by_side([pa, pb])
    for name, box in zip("ab", boxes):
        put(name, "panel box in the png; x;y;w;h", "paper/figures/%s.png" % FIGURE, "rasterlib.side_by_side", ";".join(str(v) for v in box))
    RL.save_png(png, canvas)

    comment = ("figure C10, what the raster drew, written by src/tools/%s.py at %s (cores busy %s): one row per "
               "quantity with the file and column it was read from. Panel a is one axial slice of the raw scan of "
               "PHerc0826 with the delivered sheets of the seed with the chain's largest square crossing it; panel b "
               "is the same crop with the m7 surface prediction over it. Chunks this run: %s. NO INK: a plane of the "
               "scan and sheet geometry only. Not for a public repository without the owner's word."
               % (FIGURE, figlib.utc_now(), "not checked" if busy is None else "%.1f" % busy,
                  "; ".join("%s %d" % kv for kv in reader.counts.items())))
    figlib.write_plotted(out, comment, FIELDS, rows)
    sys.stderr.write("%s\n%s: %d rows; chunks %s\n" % (png, out, len(rows), reader.counts))


if __name__ == "__main__":
    main()
