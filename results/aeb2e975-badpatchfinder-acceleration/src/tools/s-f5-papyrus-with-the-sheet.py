#!/usr/bin/env python3
"""Figure S5, a raster: the delivered sheet drawn on the volume, on both scrolls.

The specification: "papyrus: the best delivered sheet of each scroll drawn on the volume. On
PHerc. 0139 the grayscale of the twelve cube window is on disk
(finished-sheet-0139/data/cubes_RAW): a z slice with the chain's best sheet (12.12 mm,
corrected-base) as a line of points on it, and the largest fully covered square drawn on the
sheet's coverage mask. On PHerc. 1447 the grayscale is not on disk: the sheet is drawn on the
prediction field instead, and the caption says so."

Three panels, left to right, and every one of them says in the plotted table which file it read:

  a  PHerc. 0139, one z slice of the reconstructed grayscale assembled from the 128 cube tif
     stacks of finished-sheet-0139/data/cubes_RAW, with the cells of one delivered sheet that
     fall on that slice drawn over it
  b  the coverage mask of that same sheet, with its largest fully covered square outlined
  c  PHerc. 1447, one z slice of the published surface prediction field read from the zarr the
     dataset manifest names, with the cells of that scroll's largest delivered sheet over it

Which sheet, and the superlative. "Best" is recomputed here over every row of the files this
script reads, never taken from a sentence. On PHerc. 1447 that is every sheet of every seed of
seed-search-1447 that has a square. On PHerc. 0139 it is every sheet of every delivered arm of
remeasure-at-9362, twelve arms and six hundred and ten measured sheets: the maximum of column
square_mm_min_step is 12.1230 mm, reached by three arms at once, C40, P40 and A500, all on their
sheet 1, and --arm-0139 only says which of the tied arms to draw. The plotted table carries the
tie, the runner up and the number of arms and sheets the word largest covers, so the caption can
say "of the scroll" and a reader can check it.

An earlier draft of this script did not do that. It took the arm on faith and its report quoted
17.0534 mm as a larger square of the same scroll, attributing it to
remeasure-at-9362/evidence/restated.csv, a file that does not contain it: 17.0534 is 16.3940
times 1.040222, the shipped work's raised-ceiling B40 restated at the published voxel, an arm on
a growth tree the old home took with it and which remeasure-1f330280 records as reproducible by
nothing on this disk. The B40 of restated.csv is a different arm and reads 11.0730. The rule that
was broken is not subtle: a number repeated from prose is a claim, and it is read back from the
column it names before it is used.

The unit trap of that same file, which caught two readers in ten minutes on the night this was
written: remeasure-at-9362/evidence/restated.csv carries largest_square_mm_at_9_0 beside
largest_square_mm_at_9_362 and nothing in a row says which one a reader wants; they differ by
4.02 per cent. This script does not read that file at all. It reads column square_mm_min_step of
the per sheet tables, whose header states the voxel, and it writes that column's name beside
every number it puts in the plotted table.

The sheet file is checked against the sha256 the squares CSV recorded for it before a pixel is
drawn. A figure of the wrong sheet is worse than no figure, and a directory argument is exactly
how that happens.

Scale. One pixel is one voxel in every panel. The millimetres per pixel are the scroll's own
voxel, read from the dataset manifest through pipeline/datasets/voxel.py, and are written into
the plotted table; nothing here carries a voxel of its own.

Panels a and c show reconstructed volume data with our own surface over it. Kept in the article by the owner's decision of 2026-09-30, which suspends the rule against surface texture of this scroll.
"""

import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/data/scrollagent/pipeline/datasets")
sys.path.insert(0, "/data/scrollagent/tools")
import raw_chunk_cache as RC  # noqa: E402
CACHE_READS = [0]
import figlib  # noqa: E402

DEFAULT_RUNS = "/data/scrollagent/runs/rev1"
CUBE = 128
FIELDS = ["panel", "scroll", "what", "source_file", "source_column", "value"]


def voxel_um(scroll):
    """The scroll's voxel and the sentence that says where it came from.

    pipeline/datasets/voxel.py returns both and raises when a manifest has none, which is the
    behaviour this figure wants: a panel whose scale bar cannot be justified is not drawn.
    """
    import voxel as voxel_module
    return voxel_module.voxel_um(scroll)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def largest_sheet(csv_paths):
    """The row with the largest square_mm_min_step over every row of every file given.

    Used for PHerc. 1447, where the files are one per seed. PHerc. 0139 goes through
    figlib.largest_delivered_sheet instead, which scans a whole study folder and reports the
    ties. Returns (row, csv_path, runner_up_value): the superlative is recomputed over all the
    rows the word covers, which is the whole of every file passed, and the second largest comes
    back with it so a caption can state the margin instead of implying one.
    """
    best, best_path, values = None, None, []
    for p in csv_paths:
        _, _, rows = figlib.read_study_csv(p)
        for r in rows:
            v = figlib.number(r.get("square_mm_min_step"))
            if v is None or r.get("status") != "measured":
                continue
            values.append(v)
            if best is None or v > figlib.number(best["square_mm_min_step"]):
                best, best_path = r, p
    if best is None:
        raise SystemExit("no measured sheet in " + "; ".join(csv_paths))
    values.sort(reverse=True)
    runner = values[1] if len(values) > 1 else None
    return best, best_path, runner


def grey_from_cubes(cubes_dir, z, y0, y1, x0, x1, notes):
    """One z slice of the window, assembled from the cube tif stacks that cover it."""
    import tifffile
    out = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    seen = 0
    from_cache = CACHE_READS
    zc = (z // CUBE) * CUBE
    for yc in range((y0 // CUBE) * CUBE, y1, CUBE):
        for xc in range((x0 // CUBE) * CUBE, x1, CUBE):
            name = f"z{zc:05d}_y{yc:05d}_x{xc:05d}.tif"
            path = os.path.join(cubes_dir, name)
            if os.path.exists(path):
                with tifffile.TiffFile(path) as tf:
                    page = tf.pages[z - zc].asarray()
            else:
                # Added 2026-09-30: a cube of finished-sheet-0139/data/cubes_RAW is one level 0 chunk of
                # the same zarr, stored uncompressed in (z, y, x) order (that study's DECLARATION.md), so
                # a cube not in the window is read from the shared raw chunk cache, the same bytes.
                hit = RC.lookup("PHerc0139", None, 0, zc // CUBE, yc // CUBE, xc // CUBE)
                if hit is None or hit[0] != "bin":
                    notes.append(f"cube {name} is neither on disk nor in the raw chunk cache: its part of the slice stays black")
                    continue
                page = np.fromfile(hit[1], dtype=np.uint8).reshape(CUBE, CUBE, CUBE)[z - zc]
                from_cache[0] += 1
            ys, xs = max(y0, yc), max(x0, xc)
            ye, xe = min(y1, yc + CUBE), min(x1, xc + CUBE)
            out[ys - y0:ye - y0, xs - x0:xe - x0] = page[ys - yc:ye - yc, xs - xc:xe - xc]
            seen += 1
    return out, seen


def grey_from_zarr(zarr_path, z, y0, y1, x0, x1):
    import zarr
    arr = zarr.open(zarr_path, mode="r")
    return np.asarray(arr[z, y0:y1, x0:x1], dtype=np.uint8)


def overlay_points(grey, py, px, y0, x0, colour=(255, 90, 0), radius=0):
    """The sheet's cells on the slice, each drawn as a disc of the given radius in pixels.

    radius, added 2026-09-30 (figure pass of the lean S): at radius 0 a cell is one pixel, which at
    the printed size of this figure is about a fourteenth of a point and was invisible on panel c.
    The caller sets the radius from the printed width and writes it into the plotted table.
    """
    rgb = np.stack([grey] * 3, axis=-1)
    ii = np.rint(py).astype(np.int64) - y0
    jj = np.rint(px).astype(np.int64) - x0
    keep = (ii >= 0) & (ii < rgb.shape[0]) & (jj >= 0) & (jj < rgb.shape[1])
    on = np.zeros(rgb.shape[:2], dtype=bool)
    for di in range(-radius, radius + 1):
        for dj in range(-radius, radius + 1):
            if di * di + dj * dj > radius * radius:
                continue
            a, b = ii[keep] + di, jj[keep] + dj
            ok = (a >= 0) & (a < on.shape[0]) & (b >= 0) & (b < on.shape[1])
            on[a[ok], b[ok]] = True
    rgb[on] = colour
    return rgb, int(keep.sum())


def mask_panel(mask, corner_i, corner_j, side, colour=(255, 90, 0), width=1):
    img = np.where(mask, np.uint8(60), np.uint8(245))
    rgb = np.stack([img] * 3, axis=-1)
    if side and side > 0:
        i0, j0 = corner_i, corner_j
        i1, j1 = min(i0 + side, mask.shape[0]) - 1, min(j0 + side, mask.shape[1]) - 1
        w = max(1, int(width))
        rgb[i0:i0 + w, j0:j1 + 1] = colour
        rgb[i1 - w + 1:i1 + 1, j0:j1 + 1] = colour
        rgb[i0:i1 + 1, j0:j0 + w] = colour
        rgb[i0:i1 + 1, j1 - w + 1:j1 + 1] = colour
    return rgb


# 1.2 pt at the printed width: 7583 px over 7.16 in is about 1059 px per inch, so 17.6 px; radius 9
MARK_RADIUS = 9
KEPT = "Kept in the article by the owner's decision of 2026-09-30, which suspends the rule against surface texture of this scroll."


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=DEFAULT_RUNS)
    ap.add_argument("--arm-0139", default="C40",
                    help="which of the arms tied at the largest square to draw; the maximum is "
                         "recomputed over every arm of remeasure-at-9362 whatever this says")
    ap.add_argument("--sheets-0139",
                    default="corrected-base/out/sheets-C40/patches")
    ap.add_argument("--margin", type=int, default=64, help="voxels around the sheet's bounding box")
    ap.add_argument("--out", default=None)
    ap.add_argument("--table", default=None)
    a = ap.parse_args()

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "paper/figures/s-f5-papyrus-with-the-sheet.png")
    table = a.table or os.path.join(here, "evidence/figures/s-f5-papyrus-with-the-sheet.csv")
    busy = figlib.require_free_machine(2.0)

    rows, notes = [], []

    def put(panel, scroll, what, source_file, source_column, value):
        rows.append(dict(panel=panel, scroll=scroll, what=what, source_file=source_file,
                         source_column=source_column, value=value))

    put("all", "", "cores busy when the figure was drawn", "/proc/stat",
        "difference of ticks over five seconds",
        "not checked" if busy is None else f"{busy:.2f}")

    # ---------------------------------------------------------------- PHerc. 0139, panels a, b
    found = figlib.largest_delivered_sheet(
        os.path.join(a.runs, "remeasure-at-9362/evidence"), prefer_point=a.arm_0139)
    best, runner = found["row"], found["runner_up"]
    sq0139 = found["csv_path"]
    sheet_path = os.path.join(a.runs, a.sheets_0139, best["file"])
    got = sha256(sheet_path)
    if got != best["sha256"]:
        raise SystemExit(f"{sheet_path}: sha256 {got} is not the {best['sha256']} that "
                         f"{os.path.basename(sq0139)} measured. Wrong sheets directory.")
    put("a", "PHerc0139", "arm drawn", os.path.relpath(sq0139, a.runs), "point", found["point"])
    put("a", "PHerc0139", "arms tied at the largest square",
        "remeasure-at-9362/evidence/squares-*.csv", "point", "; ".join(found["ties"]))
    put("a", "PHerc0139", "arms the superlative was recomputed over",
        "remeasure-at-9362/evidence/squares-*.csv", "point", found["arms"])
    put("a", "PHerc0139", "measured sheets the superlative was recomputed over",
        "remeasure-at-9362/evidence/squares-*.csv", "square_mm_min_step", found["sheets"])
    put("a", "PHerc0139", "sheet drawn", os.path.relpath(sq0139, a.runs), "sheet", best["sheet"])
    put("a", "PHerc0139", "sheet file", os.path.relpath(sheet_path, a.runs), "sha256", got)
    put("a", "PHerc0139", "largest square over every delivered arm of the scroll; mm",
        "remeasure-at-9362/evidence/squares-*.csv", "square_mm_min_step",
        best["square_mm_min_step"])
    put("a", "PHerc0139", "next distinct value below it; mm",
        "remeasure-at-9362/evidence/squares-*.csv", "square_mm_min_step",
        figlib.NOT_MEASURABLE if runner is None else f"{runner:.4f}")
    put("a", "PHerc0139", "a file this figure does not read; and why",
        "remeasure-at-9362/evidence/restated.csv",
        "largest_square_mm_at_9_0 beside largest_square_mm_at_9_362",
        "the two columns differ by 4.02 per cent and a row does not say which one a reader "
        "wants; every square here is column square_mm_min_step of a per sheet table whose "
        "header states its voxel")

    mask, px, py, pz, _ = figlib.read_sheet(sheet_path)
    what = f"figure S5 panel a, arm {found['point']} sheet {best['sheet']}"
    side = int(figlib.required_number(best, "square_cells", what))
    ci = int(figlib.required_number(best, "square_corner_i", what))
    cj = int(figlib.required_number(best, "square_corner_j", what))
    sub = np.zeros_like(mask)
    sub[ci:ci + side, cj:cj + side] = True
    sub &= mask
    z = int(round(float(np.median(pz[sub])))) if sub.any() else int(round(float(
        np.median(pz[mask]))))
    near = mask & (np.abs(pz - z) <= 0.5)
    if not near.any():
        raise SystemExit("no cell of the sheet lands on the chosen z slice")
    y0 = max(int(py[near].min()) - a.margin, 0)
    y1 = int(py[near].max()) + a.margin + 1
    x0 = max(int(px[near].min()) - a.margin, 0)
    x1 = int(px[near].max()) + a.margin + 1
    cubes = os.path.join(a.runs, "finished-sheet-0139/data/cubes_RAW")
    grey, ncubes = grey_from_cubes(cubes, z, y0, y1, x0, x1, notes)
    # The raw slice of this scroll is dark and panel a came out almost unreadable. The
    # display window is chosen from the slice's own non zero voxels and both ends are
    # written into the plotted table, so the picture cannot be tuned without saying so.
    grey, a_lo, a_hi = figlib.stretch(grey)
    panel_a, drawn = overlay_points(grey, py[near], px[near], y0, x0, radius=MARK_RADIUS)
    panel_b = mask_panel(mask, ci, cj, side, width=2 * MARK_RADIUS)

    v0139, v0139_src = voxel_um("PHerc0139")
    put("a", "PHerc0139", "z slice", os.path.relpath(sheet_path, a.runs),
        "pz of the cells of the square; median rounded", z)
    put("a", "PHerc0139", "bounding box y0;y1;x0;x1 in voxels",
        os.path.relpath(sheet_path, a.runs), "py and px of the cells on the slice",
        f"{y0};{y1};{x0};{x1}")
    put("a", "PHerc0139", "cube stacks read", "finished-sheet-0139/data/cubes_RAW",
        "files covering the box", ncubes)
    put("a", "PHerc0139", "sheet cells drawn on the slice",
        os.path.relpath(sheet_path, a.runs), "cells within half a voxel of the slice", drawn)
    put("a", "PHerc0139", "mm per pixel", "pipeline/datasets/manifests/PHerc0139.json",
        "voxel_um through pipeline/datasets/voxel.py", f"{v0139 * 1e-3:.6f}")
    put("a", "PHerc0139", "where that voxel comes from",
        "pipeline/datasets/manifests/PHerc0139.json", "voxel_um_source", v0139_src)
    put("b", "PHerc0139", "coverage mask; cells i by j",
        os.path.relpath(sq0139, a.runs), "cells_i; cells_j",
        f"{mask.shape[0]};{mask.shape[1]}")
    put("b", "PHerc0139", "covered cells", os.path.relpath(sheet_path, a.runs),
        "cells of the lattice a point landed on", int(mask.sum()))
    put("b", "PHerc0139", "square side; cells", os.path.relpath(sq0139, a.runs),
        "square_cells", side)
    put("b", "PHerc0139", "square top left corner i;j", os.path.relpath(sq0139, a.runs),
        "square_corner_i; square_corner_j", f"{ci};{cj}")

    # ------------------------------------------------------------------- PHerc. 1447, panel c
    seeds = sorted(
        os.path.join(a.runs, "seed-search-1447/evidence", f)
        for f in os.listdir(os.path.join(a.runs, "seed-search-1447/evidence"))
        if f.startswith("squares-PHerc1447-seed") and f.endswith(".csv"))
    best1, path1, runner1 = largest_sheet(seeds)
    seed = os.path.basename(path1)[len("squares-"):-len(".csv")]
    sheet1 = os.path.join(a.runs, "seed-search-1447/out", seed, "sheets/patches", best1["file"])
    got1 = sha256(sheet1)
    if got1 != best1["sha256"]:
        raise SystemExit(f"{sheet1}: sha256 {got1} is not the {best1['sha256']} that "
                         f"{os.path.basename(path1)} measured")
    put("c", "PHerc1447", "seed drawn", os.path.relpath(path1, a.runs), "point", seed)
    put("c", "PHerc1447", "sheet drawn", os.path.relpath(path1, a.runs), "sheet", best1["sheet"])
    put("c", "PHerc1447", "sheet file", os.path.relpath(sheet1, a.runs), "sha256", got1)
    put("c", "PHerc1447", "largest square over every sheet of every seed; mm",
        "seed-search-1447/evidence/squares-PHerc1447-seed*.csv", "square_mm_min_step",
        best1["square_mm_min_step"])
    put("c", "PHerc1447", "second largest over the same rows; mm",
        "seed-search-1447/evidence/squares-PHerc1447-seed*.csv", "square_mm_min_step",
        figlib.NOT_MEASURABLE if runner1 is None else f"{runner1:.4f}")
    put("c", "PHerc1447", "rows the superlative was recomputed over",
        "seed-search-1447/evidence/squares-PHerc1447-seed*.csv", "files", len(seeds))

    mask1, px1, py1, pz1, _ = figlib.read_sheet(sheet1)
    what1 = f"figure S5 panel c, {seed} sheet {best1['sheet']}"
    side1 = int(figlib.required_number(best1, "square_cells", what1))
    ci1 = int(figlib.required_number(best1, "square_corner_i", what1))
    cj1 = int(figlib.required_number(best1, "square_corner_j", what1))
    sub1 = np.zeros_like(mask1)
    sub1[ci1:ci1 + side1, cj1:cj1 + side1] = True
    sub1 &= mask1
    z1 = int(round(float(np.median(pz1[sub1])))) if sub1.any() else int(round(float(
        np.median(pz1[mask1]))))
    near1 = mask1 & (np.abs(pz1 - z1) <= 0.5)
    if not near1.any():
        raise SystemExit("no cell of the PHerc. 1447 sheet lands on the chosen z slice")
    y0b = max(int(py1[near1].min()) - a.margin, 0)
    y1b = int(py1[near1].max()) + a.margin + 1
    x0b = max(int(px1[near1].min()) - a.margin, 0)
    x1b = int(px1[near1].max()) + a.margin + 1
    manifest = json.load(open("/data/scrollagent/pipeline/datasets/manifests/PHerc1447.json"))
    field = manifest["local"]["path"]
    grey1 = grey_from_zarr(field, z1, y0b, y1b, x0b, x1b)
    grey1, c_lo, c_hi = figlib.stretch(grey1)
    panel_c, drawn1 = overlay_points(grey1, py1[near1], px1[near1], y0b, x0b, radius=MARK_RADIUS)

    v1447, v1447_src = voxel_um("PHerc1447")
    put("c", "PHerc1447", "what the greyscale is", "pipeline/datasets/manifests/PHerc1447.json",
        "model", manifest["model"])
    put("c", "PHerc1447", "why it is not papyrus",
        "pipeline/datasets/manifests/PHerc1447.json", "source",
        "the reconstructed grayscale of this scroll is not on this disk; the panel shows the "
        "published surface prediction field named above and not the volume")
    put("c", "PHerc1447", "z slice", os.path.relpath(sheet1, a.runs),
        "pz of the cells of the square; median rounded", z1)
    put("c", "PHerc1447", "bounding box y0;y1;x0;x1 in voxels",
        os.path.relpath(sheet1, a.runs), "py and px of the cells on the slice",
        f"{y0b};{y1b};{x0b};{x1b}")
    put("c", "PHerc1447", "sheet cells drawn on the slice", os.path.relpath(sheet1, a.runs),
        "cells within half a voxel of the slice", drawn1)
    put("c", "PHerc1447", "mm per pixel", "pipeline/datasets/manifests/PHerc1447.json",
        "voxel_um through pipeline/datasets/voxel.py", f"{v1447 * 1e-3:.6f}")
    put("c", "PHerc1447", "where that voxel comes from",
        "pipeline/datasets/manifests/PHerc1447.json", "voxel_um_source", v1447_src)

    put("a", "PHerc0139", "display window, low and high grey", "the slice itself",
        "1st and 99.5th percentile of its non zero voxels", f"{a_lo:.0f};{a_hi:.0f}")
    put("c", "PHerc1447", "display window, low and high grey", "the slice itself",
        "1st and 99.5th percentile of its non zero voxels", f"{c_lo:.0f};{c_hi:.0f}")
    titles = [
        "a  PHerc. 0139, one z slice, the delivered sheet in orange",
        "b  the same sheet's coverage mask, orange square = the largest fully covered square",
        "c  PHerc. 1447, the prediction field, the best sheet in orange",
    ]
    # body.tex prints this figure at the IEEE text width of 7.16 in; the titles are set at 8 pt of
    # that printed size and wrapped to their panels (added 2026-09-30, figure pass of the lean S)
    width_px = sum(p.shape[1] for p in (panel_a, panel_b, panel_c)) + 12 * 2
    title_px = int(round(8 / 72 * width_px / 7.16))
    boxes = figlib.grey_png(out, [panel_a, panel_b, panel_c], titles=titles, title_px=title_px)
    # a 5 mm bar on each panel of papyrus, from that scroll's voxel (added 2026-09-30)
    for name, n in zip("ac", figlib.scale_bars(out, [(boxes[0], v0139 * 1e-3, 5), (boxes[2], v1447 * 1e-3, 5)], title_px)):
        put(name, "", "scale bar; pixels for its millimetres", os.path.relpath(out, here),
            "length in mm over the mm per pixel row of this panel", "%d px for %g mm" % n)
    put("all", "", "title size; pixels", "", "8 pt at the printed width of 7.16 in", title_px)
    put("all", "", "display rule", "", "",
        "each greyscale panel is stretched linearly between the 1st and 99.5th percentile of its own "
        "non zero voxels (the two values are the display window rows); the sheet's cells are discs of "
        "radius %d pixels and the square's outline is %d pixels wide, in orange (255, 90, 0), which is "
        "about 1.2 pt at the printed width of 7.16 in" % (MARK_RADIUS, 2 * MARK_RADIUS))
    put("a", "PHerc0139", "cubes read from the shared raw chunk cache", "tools/raw_chunk_cache.py",
        "level 0 chunks of 20250728140407-9.362um-1.2m-113keV-masked.zarr", CACHE_READS[0])
    for name, t in zip("abc", titles):
        put(name, "", "caption drawn inside the figure", os.path.relpath(out, here),
            "titles of tools/figlib.py grey_png", t)
    for name, box in zip("abc", boxes):
        put(name, "", "panel box in the png; x;y;w;h", os.path.relpath(out, here),
            "layout of tools/figlib.py grey_png", ";".join(str(v) for v in box))
    for n in notes:
        put("all", "", "note", "", "", n)

    comment = (
        "figure S5, what the raster drew. One row per quantity, with the file and the column it "
        "was read from. Panels a and b are PHerc. 0139 and panel c is PHerc. 1447; one pixel is "
        "one voxel in each, at that scroll's own voxel from its manifest. The superlative in "
        "panel c was recomputed over every sheet of every seed file named in its rows, and the "
        "second largest is beside it. Panel a's superlative was recomputed over every delivered "
        "arm of remeasure-at-9362, and its rows carry the arms tied at the maximum, the arms "
        "and sheets the word covers, and the next value below. Every square is column "
        "square_mm_min_step, named in each row, never a column of restated.csv, whose two "
        "voxels sit side by side. " + KEPT + " Written "
        + figlib.utc_now() + "."
    )
    figlib.write_plotted(table, comment, FIELDS, rows)
    sys.stderr.write(f"{out}\n{table}: {len(rows)} rows\n")


if __name__ == "__main__":
    main()
