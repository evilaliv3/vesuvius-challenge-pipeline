#!/usr/bin/env python3
"""Figure S6, a raster: our coverage mask beside a published segment's, at the same scale.

The specification: "the coverage mask of seed26's best sheet with the 12.72 mm square, beside the
published segment's mask of the same scroll (published-segments-eligible), same scale".

Two panels, and the whole difficulty is in the last two words.

  left   the delivered sheet of PHerc. 1447 with the largest square, drawn from the sheet file
         the seed's squares CSV measured, with that CSV's own square outlined
  right  the published segment of the same scroll with the largest square, read as a tifxyz
         through the covered test measure_grids.py declares, with its own square outlined

Same scale, and why it cannot be the same pixel grid. A cell of our sheet is about four voxels
across and a cell of a published mesh is about twenty: laying the two masks side by side cell for
cell would show ours five times larger than it is and the picture would be an argument for the
wrong conclusion. So each mask is resampled by nearest neighbour onto one common millimetres per
pixel, taken from the coarser of the two grids so that nothing is invented by interpolation, and
the plotted table carries the millimetres per pixel, the two cell steps and the resampling factor
of each panel. The cell steps come from the study CSVs, columns step_i_mm and step_j_mm, which
were measured per sheet from the 3D positions; no step is assumed and no voxel is typed here.

Which sheet and which segment. Both superlatives are recomputed over every row of every file
read: ours over every sheet of every seed of seed-search-1447, theirs over every published
segment of PHerc. 1447 in segments-PHerc1447-with-ours.csv with source = published. The runner up
of each is written into the plotted table beside the winner.

Both panels are surfaces of PHerc. 1447. Kept in the article by the owner's decision of 2026-09-30, which suspends the rule against surface texture of this scroll.
"""

import argparse
import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/data/scrollagent/pipeline/datasets")
import figlib  # noqa: E402

DEFAULT_RUNS = "/data/scrollagent/runs/rev1"
FIELDS = ["panel", "what", "source_file", "source_column", "value"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def outline(mask, ci, cj, side, colour=(200, 60, 20), ink=60, paper=245, what="a panel"):
    # The square is drawn where the CSV that measured it says it is, and if that does not fit
    # the mask this script read, the two are not the same grid and the figure refuses. It used
    # to walk off the end instead: index 258 on an axis of 212, an IndexError from numpy with
    # nothing said about which two readings disagreed. Clamping would be worse than the crash,
    # because a square drawn at the edge looks like a measurement.
    if side and side > 0:
        if not (0 <= ci and ci + side <= mask.shape[0]
                and 0 <= cj and cj + side <= mask.shape[1]):
            raise SystemExit(
                f"{what}: the square does not fit the mask this script read. The CSV puts its "
                f"corner at i {ci}, j {cj} with a side of {side} cells; the mask is "
                f"{mask.shape[0]} by {mask.shape[1]}. The two are not the same grid, and a "
                f"square drawn anyway would be a picture of nothing. Reconcile the grids "
                f"rather than drawing this.")
    img = np.where(mask, np.uint8(ink), np.uint8(paper))
    rgb = np.stack([img] * 3, axis=-1)
    if side and side > 0:
        i1 = min(ci + side, mask.shape[0]) - 1
        j1 = min(cj + side, mask.shape[1]) - 1
        rgb[ci, cj:j1 + 1] = colour
        rgb[i1, cj:j1 + 1] = colour
        rgb[ci:i1 + 1, cj] = colour
        rgb[ci:i1 + 1, j1] = colour
    return rgb


def to_common_scale(rgb, step_i_mm, step_j_mm, mm_per_pixel):
    """Nearest neighbour onto a common millimetres per pixel, both axes independently."""
    h = max(int(round(rgb.shape[0] * step_i_mm / mm_per_pixel)), 1)
    w = max(int(round(rgb.shape[1] * step_j_mm / mm_per_pixel)), 1)
    yi = np.clip((np.arange(h) * (rgb.shape[0] / h)).astype(np.int64), 0, rgb.shape[0] - 1)
    xi = np.clip((np.arange(w) * (rgb.shape[1] / w)).astype(np.int64), 0, rgb.shape[1] - 1)
    return rgb[yi][:, xi]


def best_row(paths, predicate=lambda r: True):
    best, best_path, values = None, None, []
    for p in paths:
        _, _, rows = figlib.read_study_csv(p)
        for r in rows:
            if not predicate(r):
                continue
            v = figlib.number(r.get("square_mm_min_step"))
            if v is None or r.get("status") != "measured":
                continue
            values.append(v)
            if best is None or v > figlib.number(best["square_mm_min_step"]):
                best, best_path = r, p
    if best is None:
        raise SystemExit("no measured row in " + "; ".join(paths))
    values.sort(reverse=True)
    return best, best_path, (values[1] if len(values) > 1 else None), len(values)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=DEFAULT_RUNS)
    ap.add_argument("--stride", type=int, default=1,
                    help="subsampling of the published tifxyz before resampling; 1 reads it all")
    ap.add_argument("--out", default=None)
    ap.add_argument("--table", default=None)
    a = ap.parse_args()

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here,
                                "paper/figures/s-f6-coverage-beside-a-published-segment.png")
    table = a.table or os.path.join(
        here, "evidence/figures/s-f6-coverage-beside-a-published-segment.csv")
    busy = figlib.require_free_machine(2.0)

    rows = []

    def put(panel, what, source_file, source_column, value):
        rows.append(dict(panel=panel, what=what, source_file=source_file,
                         source_column=source_column, value=value))

    put("both", "cores busy when the figure was drawn", "/proc/stat",
        "difference of ticks over five seconds",
        "not checked" if busy is None else f"{busy:.2f}")

    # --------------------------------------------------------------------------- ours, left
    evid = os.path.join(a.runs, "seed-search-1447/evidence")
    seed_csvs = sorted(os.path.join(evid, f) for f in os.listdir(evid)
                       if f.startswith("squares-PHerc1447-seed") and f.endswith(".csv"))
    ours, ours_csv, ours_runner, ours_n = best_row(seed_csvs)
    seed = os.path.basename(ours_csv)[len("squares-"):-len(".csv")]
    sheet = os.path.join(a.runs, "seed-search-1447/out", seed, "sheets/patches", ours["file"])
    got = sha256(sheet)
    if got != ours["sha256"]:
        raise SystemExit(f"{sheet}: sha256 {got} is not the {ours['sha256']} that "
                         f"{os.path.basename(ours_csv)} measured")
    mask, _, _, _, _ = figlib.read_sheet(sheet)
    what = f"figure S6 left, {seed} sheet {ours['sheet']}"
    side = int(figlib.required_number(ours, "square_cells", what))
    ci = int(figlib.required_number(ours, "square_corner_i", what))
    cj = int(figlib.required_number(ours, "square_corner_j", what))
    ours_i_mm = figlib.number(ours["step_i_mm"])
    ours_j_mm = figlib.number(ours["step_j_mm"])
    left_raw = outline(mask, ci, cj, side, what="figure S6 left, our sheet")

    put("left", "seed drawn", os.path.relpath(ours_csv, a.runs), "point", seed)
    put("left", "sheet drawn", os.path.relpath(ours_csv, a.runs), "sheet", ours["sheet"])
    put("left", "sheet file", os.path.relpath(sheet, a.runs), "sha256", got)
    put("left", "square; mm", os.path.relpath(ours_csv, a.runs), "square_mm_min_step",
        ours["square_mm_min_step"])
    put("left", "second largest over every sheet of every seed; mm",
        "seed-search-1447/evidence/squares-PHerc1447-seed*.csv", "square_mm_min_step",
        figlib.NOT_MEASURABLE if ours_runner is None else f"{ours_runner:.4f}")
    put("left", "rows the superlative was recomputed over",
        "seed-search-1447/evidence/squares-PHerc1447-seed*.csv", "measured sheets", ours_n)
    put("left", "covered cells", os.path.relpath(sheet, a.runs),
        "cells of the lattice a point landed on", int(mask.sum()))
    put("left", "cell step i;j in mm", os.path.relpath(ours_csv, a.runs),
        "step_i_mm; step_j_mm", f"{ours_i_mm};{ours_j_mm}")

    # ---------------------------------------------------------------------- published, right
    seg_csv = os.path.join(a.runs,
                           "published-segments-eligible/evidence/segments-PHerc1447-with-ours.csv")
    theirs, _, theirs_runner, theirs_n = best_row(
        [seg_csv], predicate=lambda r: r.get("source") == "published")
    name = theirs["segment"]
    folder = os.path.join(a.runs, "published-segments-eligible/out/raw/PHerc1447",
                          name.split("-", 1)[1] if "-" in name else name)
    if not os.path.isdir(folder):
        raise SystemExit(f"{folder}: the tifxyz of segment {name} is not where this script "
                         f"looks. Pass the right tree rather than drawing another segment.")
    tmask = figlib.read_tifxyz_mask(folder, stride=a.stride)
    twhat = f"figure S6 right, published segment {name}"
    tside = int(figlib.required_number(theirs, "square_cells", twhat)) // max(a.stride, 1)
    tci = int(figlib.required_number(theirs, "square_corner_i", twhat)) // max(a.stride, 1)
    tcj = int(figlib.required_number(theirs, "square_corner_j", twhat)) // max(a.stride, 1)
    theirs_i_mm = figlib.number(theirs["step_i_mm"]) * a.stride
    theirs_j_mm = figlib.number(theirs["step_j_mm"]) * a.stride
    # Which grid is the segment's own: the one whose extent is the shape of its tifxyz. Read
    # the three shapes and put them in the plotted table side by side, because until this was
    # done the disagreement showed up only as an IndexError from numpy.
    import tifffile as _tf
    _x = _tf.memmap(os.path.join(folder, "x.tif"), mode="r")
    tif_shape = (int(_x.shape[0]), int(_x.shape[1]))
    csv_cells = (int(figlib.required_number(theirs, "cells_i", twhat)),
                 int(figlib.required_number(theirs, "cells_j", twhat)))
    put("right", "tifxyz shape of x.tif, i;j", os.path.relpath(folder, a.runs),
        "the segment's own grid", f"{tif_shape[0]};{tif_shape[1]}")
    put("right", "cells_i;cells_j as the segment CSV measured them",
        os.path.relpath(seg_csv, a.runs), "cells_i;cells_j",
        f"{csv_cells[0]};{csv_cells[1]}")
    put("right", "shape of the array this figure reads, i;j",
        os.path.relpath(folder, a.runs), f"read_tifxyz_mask at stride {a.stride}",
        f"{tmask.shape[0]};{tmask.shape[1]}")
    same = (csv_cells[0] == tif_shape[0] and csv_cells[1] == tif_shape[1])
    put("right", "the CSV's grid is the tifxyz's grid", "the three rows above",
        "cells_i;cells_j against the shape of x.tif", "yes" if same else "no")
    if same:
        right_raw = outline(tmask, tci, tcj, tside,
                            what="figure S6 right, the published segment")
    else:
        # The square is not drawn, and the panel is. A square placed on a grid that is not the
        # one it was measured on would be a red rectangle that looks like a measurement.
        right_raw = outline(tmask, 0, 0, 0)
        put("right", "the square is not drawn, and why", os.path.relpath(seg_csv, a.runs),
            "square_corner_i;square_corner_j;square_cells",
            f"the CSV measured the square at {tci};{tcj} with a side of {tside} on a grid of "
            f"{csv_cells[0]} by {csv_cells[1]} cells, and the segment's own tifxyz is "
            f"{tif_shape[0]} by {tif_shape[1]}: the two are not the same grid, so the square "
            f"has no place on this panel")

    put("right", "segment drawn", os.path.relpath(seg_csv, a.runs), "segment", name)
    put("right", "mesh read", os.path.relpath(seg_csv, a.runs), "mesh_name",
        theirs["mesh_name"])
    put("right", "tifxyz folder", os.path.relpath(folder, a.runs), "x.tif; y.tif; z.tif",
        "covered where the three are neither all zero nor all minus one and all finite")
    put("right", "square; mm", os.path.relpath(seg_csv, a.runs), "square_mm_min_step",
        theirs["square_mm_min_step"])
    put("right", "second largest over the published segments of this scroll; mm",
        os.path.relpath(seg_csv, a.runs), "square_mm_min_step",
        figlib.NOT_MEASURABLE if theirs_runner is None else f"{theirs_runner:.4f}")
    put("right", "rows the superlative was recomputed over", os.path.relpath(seg_csv, a.runs),
        "published segments with a measured square", theirs_n)
    put("right", "covered cells", os.path.relpath(folder, a.runs), "the covered test above",
        int(tmask.sum()))
    put("right", "subsampling stride applied before resampling", "argument --stride",
        "both axes", a.stride)
    put("right", "cell step i;j in mm after the stride", os.path.relpath(seg_csv, a.runs),
        "step_i_mm; step_j_mm times the stride", f"{theirs_i_mm};{theirs_j_mm}")

    # ------------------------------------------------------------------------- common scale
    mm_per_pixel = max(ours_i_mm, ours_j_mm, theirs_i_mm, theirs_j_mm)
    left = to_common_scale(left_raw, ours_i_mm, ours_j_mm, mm_per_pixel)
    right = to_common_scale(right_raw, theirs_i_mm, theirs_j_mm, mm_per_pixel)
    put("both", "mm per pixel of both panels after resampling",
        "the four cell steps in the rows above", "the largest of them",
        f"{mm_per_pixel:.6f}")
    put("left", "panel size after resampling; pixels", "", "rows; columns",
        f"{left.shape[0]};{left.shape[1]}")
    put("right", "panel size after resampling; pixels", "", "rows; columns",
        f"{right.shape[0]};{right.shape[1]}")

    boxes = figlib.grey_png(out, [left, right])
    # Added 2026-09-30, figure pass of the lean S: body.tex prints this figure at the IEEE column
    # width of 3.5 in, and the drawn canvas is one pixel per resampled cell. Every pixel is repeated
    # k by k (nearest neighbour, an integer factor, so no value is invented and the millimetres per
    # cell stay exact) with k the smallest integer that gives at least 300 dpi at that width.
    from PIL import Image as _Image
    _im = _Image.open(out)
    k = max(1, -(-int(300 * 3.5) // _im.width))
    if k > 1:
        _im.resize((_im.width * k, _im.height * k), _Image.NEAREST).save(out)
        boxes = [tuple(v * k for v in b) for b in boxes]
    put("both", "integer upscale for print, pixels per resampled cell", "", "smallest k giving 300 dpi at 3.5 in", k)
    put("both", "png size after the upscale; pixels", "", "width;height", f"{_im.width * k};{_im.height * k}")
    # a 10 mm bar on each panel, from the common millimetres per pixel above over the upscale
    # (added 2026-09-30); the label at 8 pt of the printed 3.5 in
    fpx = int(round(8 / 72 * _im.width * k / 3.5))
    for panel, n in zip(("left", "right"), figlib.scale_bars(out, [(b, mm_per_pixel / k, 10) for b in boxes], fpx)):
        put(panel, "scale bar; pixels for its millimetres", os.path.relpath(out, here),
            "length in mm over the mm per pixel of both panels, divided by the upscale", "%d px for %g mm" % n)
    for panel, box in zip(("left", "right"), boxes):
        put(panel, "panel box in the png; x;y;w;h", os.path.relpath(out, here),
            "layout of tools/figlib.py grey_png", ";".join(str(v) for v in box))

    comment = (
        "figure S6, what the raster drew. Left, the delivered sheet of PHerc. 1447 with the "
        "largest square over every sheet of every seed of seed-search-1447; right, the "
        "published segment of the same scroll with the largest square over the rows of "
        "published-segments-eligible/evidence/segments-PHerc1447-with-ours.csv whose source is "
        "published. Both squares are the square_cells and the two corner columns of those same "
        "rows; neither was recomputed here. The two masks are resampled by nearest neighbour "
        "onto the coarser of the four measured cell steps so the panels share one millimetre "
        "per pixel, and every step, factor and panel size is a row of this table. Kept in the article by the owner's decision of 2026-09-30, which suspends the rule against surface texture of this scroll. Written "
        + figlib.utc_now() + "."
    )
    figlib.write_plotted(table, comment, FIELDS, rows)
    sys.stderr.write(f"{out}\n{table}: {len(rows)} rows\n")


if __name__ == "__main__":
    main()
