#!/usr/bin/env python3
"""Figure C13, a raster: two sets of sheets grown from the same seed point of PHerc. 0826, drawn where they
cross the same axial slice of the raw scan, same crop, same scale.

Default pair: seed6365 as the chain delivered it (chain-0826/out/PHerc0826-seed6365/C40) against the
SetSeed run of the same seed (area-0826-90/scratch/coll/setseed-seed6365/C40: the same growth with patch
21 of the series, «start the five seed cells of a patch at rest», then the same downstream). --before and
--after take any other pair of sheet folders with their squares CSVs, so the same drawing serves item 91's
arms A and B when their sheets exist.

The place, declared before drawing and the same for both panels: the seed point of the run, read from
chain-0826's per-seed-queue.csv (seed_x, seed_y, seed_z): the slice is z = seed_z and the crop is
--width-mm on a side centred on (seed_y, seed_x). Both runs grow from that point, so both must cross
there, and neither run's best square chooses the place.

Every sheet file is checked against the sha256 its squares row recorded. The squares CSV of each run is
read from this work's snapshot under evidence/studies when it is there, else from the live study (the
table says which). In each panel the sheet holding the run's largest square is red and the others cyan;
a yellow ring marks the seed point.

NO INK: a plane of the scan and sheet geometry only. Not for a public repository without the owner's word.

Usage: c-f13-setseed.py [--out CSV] [--png PNG] [--seed PHerc0826-seed6365]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f13-setseed"
RUNS = "/data/scrollagent/runs/rev1"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
RED, CYAN, YELLOW = (235, 40, 40), (0, 200, 255), (255, 215, 0)


# Locations withheld (director 2026-09-30, the owner's decision): the seed point, the cut's height and the crop box
# are read and used as before, and the plotted table says «withheld» in their place.
WITHHELD = "withheld"


def ring(img, cy, cx, r, colour, width=3):
    h, w = img.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    d = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    img[(d >= r - width / 2) & (d <= r + width / 2)] = colour
    return img


def main(argv=None, figure=FIGURE, extra_rows=()):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    ap.add_argument("--seed", default="PHerc0826-seed6365")
    ap.add_argument("--before", default="chain-0826/out/{seed}/C40")
    ap.add_argument("--before-squares", default="chain-0826/evidence/squares-{seed}.csv")
    ap.add_argument("--before-name", default="as delivered")
    ap.add_argument("--after", default="area-0826-90/scratch/coll/setseed-{short}/C40")
    ap.add_argument("--after-squares", default="area-0826-90/evidence/squares-coll-setseed-{short}.csv")
    ap.add_argument("--after-name", default="SetSeed")
    ap.add_argument("--legend-best", default="sheet with the run's largest square")
    ap.add_argument("--width-mm", type=float, default=20.0)
    ap.add_argument("--bin", type=int, default=2)
    ap.add_argument("--bar-mm", type=float, default=5.0)
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % figure)
    png = a.png or os.path.join(here, "paper/figures/%s.png" % figure)
    busy = figlib.require_free_machine(2.0)
    rows = [dict(r) for r in extra_rows]
    used = {}

    def study_file(rel):
        """The snapshot this work ships under evidence/studies first, the live study only when it lacks the file."""
        parts = rel.split("/")
        shipped = os.path.join(here, "evidence", "studies", parts[0], *parts[2:])
        if os.path.exists(shipped):
            used[rel] = "snapshot " + os.path.relpath(shipped, here)
            return shipped
        live = os.path.join(RUNS, rel)
        if not os.path.exists(live):
            raise SystemExit("%s: in neither the snapshot nor the live study" % rel)
        used[rel] = "live study (not in the snapshot)"
        return live

    def put(panel, what, source_file, source_column, value, key=""):
        rows.append(dict(key=key, panel=panel, what=what, source_file=source_file, source_column=source_column,
                         value=value))

    short = a.seed.replace("PHerc0826-", "")
    q = study_file("chain-0826/evidence/per-seed-queue.csv")
    _, _, queue = figlib.read_study_csv(q)
    row = [r for r in queue if r["attempt"] == a.seed]
    if len(row) != 1:
        raise SystemExit("%s: %d rows in per-seed-queue.csv" % (a.seed, len(row)))
    row = row[0]
    # The snapshot withholds the seed point (copy_evidence.py DROP): it is read from the live study's queue, whose row
    # for this seed must agree with the snapshot's on every column the snapshot keeps that a later write cannot change.
    live = os.path.join(RUNS, "chain-0826/evidence/per-seed-queue.csv")
    _, _, lq = figlib.read_study_csv(live)
    lrow = [r for r in lq if r["attempt"] == a.seed]
    if len(lrow) != 1:
        raise SystemExit("%s: %d rows in the live per-seed-queue.csv" % (a.seed, len(lrow)))
    lrow = lrow[0]
    for c in ("seed_rule_group", "pred_chunk_share_255", "raw_at_seed", "passes_rule"):
        if c in row and lrow.get(c) != row[c]:
            raise SystemExit("%s: live %s %r is not the snapshot's %r" % (a.seed, c, lrow.get(c), row[c]))
    used["chain-0826/evidence/per-seed-queue.csv seed point"] = "live study (the snapshot withholds seed_x, seed_y, seed_z)"
    sx, sy, sz = (int(figlib.required_number(lrow, c, "seed point")) for c in ("seed_x", "seed_y", "seed_z"))
    put("a;b", "seed number", "chain-0826/evidence/per-seed-queue.csv", "attempt", short.replace("seed", ""), key="seed")
    put("a;b", "seed point x;y;z (level 0 voxels)", "chain-0826/evidence/per-seed-queue.csv", "seed_x; seed_y; seed_z",
        WITHHELD)

    vox, _ = RL.voxel()
    n = int(round(a.width_mm * 1000.0 / vox))
    n -= n % a.bin
    y0, x0 = max(sy - n // 2, 0), max(sx - n // 2, 0)
    y1, x1 = y0 + n, x0 + n
    mmpp = a.bin * vox / 1000.0
    if not (y1 - y0 == x1 - x0 == n):
        raise SystemExit("the crop is not %d voxels square" % n)
    put("a;b", "slice z (level 0 voxels)", "chain-0826/evidence/per-seed-queue.csv", "seed_z", WITHHELD)
    put("a;b", "crop y0;y1;x0;x1 (level 0 voxels)", "seed point plus and minus half the width", "", WITHHELD)
    put("a;b", "crop width; mm (display choice)", "argument --width-mm", "", "%g" % a.width_mm, key="crop_mm")
    put("a;b", "voxel; um", "pipeline/datasets/manifests/PHerc0826.json", "voxel_um through pipeline/datasets/voxel.py", "%g" % vox)
    put("a;b", "display bin; voxels per pixel side (block mean)", "argument --bin", "", a.bin)
    put("a;b", "mm per pixel", "display bin times the voxel", "", "%.6f" % mmpp)

    reader = RL.RawReader(0)
    grey, nch = reader.plane(sz, y0, y1, x0, x1)
    put("a;b", "grey source", RL.RAW_URL + "/0", "raw masked scan level 0; uint8; compressor null", "open data bucket")
    put("a;b", "chunks covering the crop", RL.RAW_URL + "/0", "one z layer of chunks", nch)
    put("a;b", "sha256 of the crop's grey bytes before the stretch", RL.RAW_URL + "/0", "plane z; rows y0:y1; columns x0:x1",
        RL.plane_sha(grey))
    g2 = RL.block_mean(grey, a.bin)
    g2, lo, hi = figlib.stretch(g2)
    put("a;b", "display window; low and high grey", "the binned slice itself", "figlib.stretch", "%.0f;%.0f" % (lo, hi))

    panels = []
    for name, folder, sqcsv, label in (("a", a.before, a.before_squares, a.before_name),
                                       ("b", a.after, a.after_squares, a.after_name)):
        folder = os.path.join(RUNS, folder.format(seed=a.seed, short=short))
        rel = sqcsv.format(seed=a.seed, short=short)
        sqp = study_file(rel)
        _, _, sq = figlib.read_study_csv(sqp)
        meas = [r for r in sq if r["status"] == "measured" and figlib.number(r["square_mm_min_step"]) is not None]
        if not meas:
            raise SystemExit("%s: no measured sheet" % rel)
        best = max(meas, key=lambda r: (float(r["square_mm_min_step"]), -int(r["sheet"])))
        put(name, "run", rel, "", label)
        put(name, "squares file read from", rel, "", used[rel])
        put(name, "sheets in the run", rel, "rows", len(sq), key="sheets_%s" % ("before" if name == "a" else "after"))
        put(name, "largest square of the run; mm", rel, "square_mm_min_step (max over sheets)", best["square_mm_min_step"],
            key="square_%s_mm" % ("before" if name == "a" else "after"))
        put(name, "sheet holding it", rel, "sheet", best["sheet"])
        img = RL.rgb(g2)
        per = []
        for r in sorted(sq, key=lambda r: int(r["sheet"])):
            path = os.path.join(folder, r["file"])
            h = RL.sha256(path)
            if h != r["sha256"]:
                raise SystemExit("%s: sha256 %s is not the %s of %s" % (path, h, r["sha256"], rel))
            m, px, py, pz, _ = figlib.read_sheet(path)
            ys, xs, _, _ = RL.plane_crossings(m, px, py, pz, sz)
            colour = RED if r["sheet"] == best["sheet"] else CYAN
            if colour == CYAN:
                k = RL.dots(img, (ys - y0) / a.bin, (xs - x0) / a.bin, colour, r=1)
                per.append((r["sheet"], k, colour))
            else:
                bys, bxs = ys, xs
        k = RL.dots(img, (bys - y0) / a.bin, (bxs - x0) / a.bin, RED, r=1)
        per.append((best["sheet"], k, RED))
        put(name, "the sheet with the run's largest square crosses the crop", os.path.relpath(folder, RUNS),
            "rasterlib.plane_crossings", "yes" if k > 0 else "no",
            key="best_crosses_%s" % ("before" if name == "a" else "after"))
        put(name, "sheet files checked against their squares row sha256", os.path.relpath(folder, RUNS), "sha256", "all %d equal" % len(sq))
        put(name, "crossings drawn per sheet (sheet:count)", os.path.relpath(folder, RUNS), "rasterlib.plane_crossings",
            "; ".join("%s:%d" % (s, k) for s, k, _ in sorted(per, key=lambda t: int(t[0]))))
        put(name, "sheets crossing the crop", os.path.relpath(folder, RUNS), "rasterlib.plane_crossings",
            sum(1 for _, k, _ in per if k > 0), key="crossing_%s" % ("before" if name == "a" else "after"))
        img = ring(img, (sy - y0) / a.bin, (sx - x0) / a.bin, 12, YELLOW, 3)
        RL.print_size(2 * img.shape[1] + 16, RL.COLUMNWIDTH_BP)          # two panels side by side at the column width
        img, nbar = RL.scale_bar(img, a.bar_mm, mmpp, "%g mm" % a.bar_mm)
        img = RL.label(img, "%s  %s" % (name, label))
        img = RL.legend(img, [(RED, a.legend_best), (CYAN, "other sheets of the run"),
                              (YELLOW, "seed point")], xy=(14, 64))
        panels.append(img)
    put("a;b", "scale bar; mm (display choice)", "argument --bar-mm", "", "%g" % a.bar_mm, key="scale_bar_mm")
    put("a;b", "scale bar; pixels", "bar mm over mm per pixel; rounded", "", nbar)
    canvas, boxes = RL.side_by_side(panels)
    for name, box in zip("ab", boxes):
        put(name, "panel box in the png; x;y;w;h", "paper/figures/%s.png" % figure, "rasterlib.side_by_side", ";".join(str(v) for v in box))
    RL.save_png(png, canvas)
    comment = ("figure %s, what the raster drew, written by src/tools/%s.py at %s (cores busy %s): the sheets of two runs "
               "from the same seed point on the same axial slice of the raw scan of PHerc0826, same crop and scale. %s "
               "Chunks this run: %s. NO INK. Not for a public repository without the owner's word."
               % (figure, figure, figlib.utc_now(), "not checked" if busy is None else "%.1f" % busy,
                  "Files: " + "; ".join("%s (%s)" % kv for kv in sorted(used.items())) + ".",
                  "; ".join("%s %d" % kv for kv in reader.counts.items())))
    figlib.write_plotted(out, comment, FIELDS, rows)
    sys.stderr.write("%s\n%s: %d rows; chunks %s\n" % (png, out, len(rows), reader.counts))


if __name__ == "__main__":
    main()
