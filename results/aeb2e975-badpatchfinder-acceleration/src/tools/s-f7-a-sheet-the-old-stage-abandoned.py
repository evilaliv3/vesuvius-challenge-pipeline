#!/usr/bin/env python3
"""Figure S7, a raster: a sheet the untouched c stage never delivered, drawn on the scroll it was grown in.

The specification (director, 2026-09-28T06:27:33Z): «S, a delivered sheet that the old stage abandoned», shown
with papyrus.

Which trees the old stage abandoned is read, not remembered: seed-search-1447's runner rows
(seed-search-1447/evidence/runs/<attempt>.csv) whose quantity downstream_return_code_v2 is 124 with the words
«the stage 'c' returned it», that is the c stage stopped by the runner's cap. Those trees were delivered
afterwards, uncapped and with the changed stage, byte for byte the same. Of their sheets, the one drawn is the
largest square_mm_min_step over every measured row of their squares files, recomputed here.

For contrast, the sheet with the largest square over the seeds that grew on papyrus (per-seed.csv, column
on_papyrus_or_in_air = «on papyrus»), drawn the same way.

Each panel is ONE z plane of the raw masked scan 20250521151220-8.640um-1.2m-116keV-masked.zarr at its level 3,
one pixel = 8 voxels on a side (the zarr's own multiscales scale 8), through the median z of the sheet's cells.
The sheet's cells whose z falls in that plane (z // 8 equal to the plane) are drawn in orange at (y // 8, x // 8).
A chunk the bucket does not hold (the scan is masked, whole chunks outside the mask are absent) and a stored 0
(the mask value) are drawn dark blue: that is outside the scroll, not papyrus. Nothing is fetched here: the chunks
come from the home's shared raw chunk cache, put there by papyrus-figures-2026-09-28/tools/fetch_level_slice.py,
and a chunk not in it stops the figure. No ink detector runs.

Grey window: the 1st and 99th percentiles of the nonzero stored values of each panel, written into the plotted
table. The sheet files are checked against the sha256 their squares rows recorded.

Reconstructed volume data of PHerc. 1447. Kept in the article by the owner's decision of 2026-09-30, which suspends the rule against surface texture of this scroll.
"""
import argparse
import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/data/scrollagent/pipeline/datasets")
sys.path.insert(0, "/data/scrollagent/tools")
import figlib  # noqa: E402

DEFAULT_RUNS = "/data/scrollagent/runs/rev1"
LEVEL = 3
CH = 128
FIELDS = ["panel", "what", "source_file", "source_column", "value"]
BLANK = (25, 35, 70)
ORANGE = (255, 120, 20)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def plane(zl, shape):
    """One z plane of level LEVEL from the shared cache; NaN where the chunk is absent."""
    import raw_chunk_cache as RC
    out = np.full((shape[1], shape[2]), np.nan, dtype=np.float32)
    cz = zl // CH
    for cy in range((shape[1] + CH - 1) // CH):
        for cx in range((shape[2] + CH - 1) // CH):
            hit = RC.lookup("PHerc1447", None, LEVEL, cz, cy, cx)
            if hit is None:
                raise SystemExit("chunk %d/%d/%d/%d not in the shared cache: run "
                                 "papyrus-figures-2026-09-28/tools/fetch_level_slice.py first" % (LEVEL, cz, cy, cx))
            if hit[0] != "bin":
                continue
            blk = np.fromfile(hit[1], dtype=np.uint8).reshape(CH, CH, CH)[zl % CH]
            ys, xs = cy * CH, cx * CH
            ye, xe = min(shape[1], ys + CH), min(shape[2], xs + CH)
            out[ys:ye, xs:xe] = blk[:ye - ys, :xe - xs]
    return out


def panel_image(grey, py, px, pz, zl):
    v = grey[np.isfinite(grey) & (grey > 0)]
    lo, hi = float(np.percentile(v, 1)), float(np.percentile(v, 99))
    g = np.clip((np.nan_to_num(grey) - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)
    rgb = np.stack([g] * 3, axis=-1)
    blank = ~np.isfinite(grey) | (grey == 0)
    rgb[blank] = BLANK
    on = (np.floor(pz / 2 ** LEVEL).astype(np.int64) == zl)
    ii = np.floor(py[on] / 2 ** LEVEL).astype(np.int64)
    jj = np.floor(px[on] / 2 ** LEVEL).astype(np.int64)
    keep = (ii >= 0) & (ii < rgb.shape[0]) & (jj >= 0) & (jj < rgb.shape[1])
    for di in (-1, 0, 1):  # three pixels wide, so a line of cells reads at print size
        for dj in (-1, 0, 1):
            a = np.clip(ii[keep] + di, 0, rgb.shape[0] - 1)
            b = np.clip(jj[keep] + dj, 0, rgb.shape[1] - 1)
            rgb[a, b] = ORANGE
    covered = float(np.mean(~blank))
    # crop to the scroll and the sheet with a margin of 24 pixels; nothing is resampled
    show = ~blank
    show[ii[keep], jj[keep]] = True
    rr, cc = np.nonzero(show)
    r0, r1 = max(0, rr.min() - 24), min(rgb.shape[0], rr.max() + 25)
    c0, c1 = max(0, cc.min() - 24), min(rgb.shape[1], cc.max() + 25)
    return rgb[r0:r1, c0:c1], lo, hi, int(on.sum()), covered, (r0, r1, c0, c1)


PRINT_IN = 0.9 * 516 / 72


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=DEFAULT_RUNS)
    ap.add_argument("--out", default=None)
    ap.add_argument("--table", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "paper/figures/s-f7-a-sheet-the-old-stage-abandoned.png")
    table = a.table or os.path.join(here, "evidence/figures/s-f7-a-sheet-the-old-stage-abandoned.csv")
    ev = os.path.join(a.runs, "seed-search-1447/evidence")
    rows = []

    def put(panel, what, source_file, source_column, value):
        rows.append(dict(panel=panel, what=what, source_file=source_file, source_column=source_column, value=value))

    # the trees whose untouched c stage the runner's cap stopped
    abandoned = []
    for f in sorted(os.listdir(os.path.join(ev, "runs"))):
        _, _, rr = figlib.read_study_csv(os.path.join(ev, "runs", f))
        for r in rr:
            if r.get("quantity") == "downstream_return_code_v2" and r.get("value") == "124" \
                    and "stage 'c'" in (r.get("what_it_is") or ""):
                abandoned.append(r["attempt"])
    abandoned = sorted(set(abandoned))
    if not abandoned:
        raise SystemExit("no tree whose c stage the cap stopped")
    put("a", "trees whose untouched c stage the runner's cap stopped", "seed-search-1447/evidence/runs/*.csv",
        "quantity downstream_return_code_v2 = 124, the stage 'c' returned it", "; ".join(abandoned))
    _, _, per = figlib.read_study_csv(os.path.join(ev, "per-seed.csv"))
    where = {r["attempt"]: r["on_papyrus_or_in_air"] for r in per}
    put("a", "where those trees grew", "seed-search-1447/evidence/per-seed.csv", "on_papyrus_or_in_air",
        "; ".join("%s %s" % (t, where.get(t, figlib.NOT_MEASURABLE)) for t in abandoned))
    papyrus = sorted(t for t, w in where.items() if w == "on papyrus")

    def best_of(attempts):
        best, bpath, n = None, None, 0
        for t in attempts:
            p = os.path.join(ev, "squares-%s.csv" % t)
            _, _, rr = figlib.read_study_csv(p)
            for r in rr:
                v = figlib.number(r.get("square_mm_min_step"))
                if v is None or r.get("status") != "measured":
                    continue
                n += 1
                if best is None or v > figlib.number(best["square_mm_min_step"]):
                    best, bpath = r, p
        return best, bpath, n

    import json
    import urllib.request
    zarray = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1447/volumes/" \
             "20250521151220-8.640um-1.2m-116keV-masked.zarr/%d/.zarray" % LEVEL
    shape = json.load(urllib.request.urlopen(zarray, timeout=60))["shape"]
    vox, vox_src = figlib_voxel()
    panels, titles = [], []
    for name, attempts, label in (("a", abandoned, "abandoned"), ("b", papyrus, "on papyrus")):
        best, bpath, n = best_of(attempts)
        attempt = best["point"]
        sheet = os.path.join(a.runs, "seed-search-1447/out", attempt, "C40", best["file"])
        got = sha256(sheet)
        if got != best["sha256"]:
            raise SystemExit("%s: sha256 %s is not the %s its squares row recorded" % (sheet, got, best["sha256"]))
        mask, px, py, pz, _ = figlib.read_sheet(sheet)
        z0 = int(round(float(np.median(pz[mask]))))
        zl = z0 // 2 ** LEVEL
        grey = plane(zl, shape)
        rgb, lo, hi, drawn, covered, crop = panel_image(grey, py[mask], px[mask], pz[mask], zl)
        panels.append(rgb)
        put(name, "crop of the level 3 plane; rows r0;r1 and columns c0;c1", "the plane itself",
            "pixels inside the mask or on the sheet, plus 24", ";".join(str(v) for v in crop))
        put(name, "which set the superlative covers", "seed-search-1447/evidence/squares-<attempt>.csv",
            "square_mm_min_step, status measured", "%s: %s, %d sheets" % (label, "; ".join(attempts), n))
        put(name, "sheet drawn", os.path.relpath(bpath, a.runs), "point; sheet", "%s; %s" % (attempt, best["sheet"]))
        put(name, "its largest fully covered square; mm", os.path.relpath(bpath, a.runs), "square_mm_min_step",
            best["square_mm_min_step"])
        put(name, "sheet file", os.path.relpath(sheet, a.runs), "sha256", got)
        put(name, "z plane; level 0 voxels and level 3 plane", os.path.relpath(sheet, a.runs),
            "median pz of the sheet's cells", "%d; %d" % (z0, zl))
        put(name, "sheet cells drawn on the plane", os.path.relpath(sheet, a.runs), "cells with pz // 8 = plane", drawn)
        put(name, "share of the plane inside the scan's mask", "the plane itself",
            "pixels with a stored nonzero value over all pixels", "%.4f" % covered)
        put(name, "display window, low and high grey", "the plane itself",
            "1st and 99th percentile of its nonzero values", "%.0f;%.0f" % (lo, hi))
        put(name, "mm per pixel", "pipeline/datasets/manifests/PHerc1447.json",
            "voxel_um through pipeline/datasets/voxel.py, times 8", "%.5f" % (vox * 8e-3))
        titles.append("%s  %s, sheet %s: %s" % (name, attempt.replace("PHerc1447-", ""), best["sheet"],
                                                  "its c stage was abandoned" if name == "a" else "grown on papyrus"))
    put("all", "where the voxel comes from", "pipeline/datasets/manifests/PHerc1447.json", "voxel_um_source", vox_src)
    put("all", "level shape z;y;x", "the zarr's level 3 .zarray", "shape", ";".join(str(s) for s in shape))
    # Added 2026-09-30 (figure pass of the lean S): body.tex prints this figure at 0.9 of the IEEE text
    # width, PRINT_IN inches. Every level 3 pixel is repeated k by k (nearest neighbour, an integer
    # factor, so no grey value is invented) with k the smallest integer giving at least 300 dpi there,
    # and the titles and the scale bar's label are set in the series serif at 8 pt of that size.
    width0 = sum(p.shape[1] for p in panels) + 12 * (len(panels) - 1)
    k = max(1, -(-int(300 * PRINT_IN) // width0))
    panels = [np.repeat(np.repeat(p, k, axis=0), k, axis=1) for p in panels]
    width_px = sum(p.shape[1] for p in panels) + 12 * k * (len(panels) - 1)
    title_px = int(round(8 / 72 * width_px / PRINT_IN))
    boxes = figlib.grey_png(out, panels, gap=12 * k, titles=titles, title_px=title_px)
    # the bar in the upper left of each panel (2026-09-30: in the lower left it ran beside the sheet's line)
    for name, n in zip("ab", figlib.scale_bars(out, [(b, vox * 8e-3 / k, 10) for b in boxes], title_px, corner="upper left")):
        put(name, "scale bar; pixels for its millimetres", os.path.relpath(out, here), "10 mm over the mm per pixel of the png", "%d px for %g mm" % n)
    put("all", "png pixels per level 3 pixel, each axis", "", "smallest integer giving 300 dpi at %.3f in" % PRINT_IN, k)
    put("all", "title and scale bar label size; pixels", "", "8 pt at the printed width of %.3f in" % PRINT_IN, title_px)
    for name, t, box in zip("ab", titles, boxes):
        put(name, "caption drawn inside the figure", os.path.relpath(out, here), "titles", t)
        put(name, "panel box in the png; x;y;w;h", os.path.relpath(out, here), "layout", ";".join(str(v) for v in box))
    comment = ("figure S7, what the raster drew. One row per quantity, with the file and the column it was read from. "
               "Two z planes of the raw masked scan of PHerc. 1447 at level 3, one pixel = 8 voxels; dark blue = outside "
               "the scan's mask. Kept in the article by the owner's decision of 2026-09-30, which suspends the rule against surface texture of this scroll. Written " + figlib.utc_now() + ".")
    figlib.write_plotted(table, comment, FIELDS, rows)
    sys.stderr.write("%s\n%s: %d rows\n" % (out, table, len(rows)))


def figlib_voxel():
    import voxel as voxel_module
    return voxel_module.voxel_um("PHerc1447")


def add_scale_bar(path, boxes, mm_per_px, font_px=None):
    """A 10 mm bar in the lower left of every panel, its length in pixels from the voxel, never typed."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    n = int(round(10.0 / mm_per_px))
    if not font_px:
        for (x, y, w, h) in boxes:
            x0, y0 = x + 12, y + h - 16
            d.rectangle((x0, y0, x0 + n, y0 + 4), fill=(255, 255, 255))
            d.text((x0, y0 - 12), "10 mm", fill=(255, 255, 255))
        im.save(path)
        return
    f = ImageFont.truetype(figlib.TITLE_FONT, int(font_px))
    t = max(4, int(font_px) // 4)
    for (x, y, w, h) in boxes:
        x0, y1 = x + int(font_px), y + h - int(font_px)
        d.rectangle((x0, y1 - t, x0 + n, y1), fill=(255, 255, 255))
        d.text((x0, y1 - t - int(font_px) // 4), "10 mm", fill=(255, 255, 255), font=f, anchor="ls")
    im.save(path)

if __name__ == "__main__":
    main()
