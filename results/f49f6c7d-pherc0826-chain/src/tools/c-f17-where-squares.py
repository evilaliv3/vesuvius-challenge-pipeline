#!/usr/bin/env python3
"""Figure C17: where the best squares of PHerc. 0826 sit. One whole axial slice of the raw scan, the
published umbilicus at that height, the crossings of the delivered sheets of the marked seeds with the
slice, and the centre of each best square, labelled with its side.

Which squares, by rules stated here and recomputed on every run, never typed.
  hole free: the HOLE_FREE seeds of the chain as run with the largest square_mm_min_step over every
     measured row of evidence/studies/chain-0826/squares-PHerc0826-seed*.csv, one per seed (its best
     sheet), in descending order; the first is figlib.largest_delivered_sheet's answer and the tool
     stops if the ranking disagrees with it. A tie at the last place is recorded in a row.
  certified: the CERTIFIED seeds with the largest best_certified_mm of the article's frozen
     evidence/studies/search-yield-0826/yield-seeds.csv, one per seed, ties recorded; the live
     certified-squares.csv is read only for each chosen seed's C40 row, which must carry that value. The certified square is outlined by
     certified_square_cells and certified_corner_i, certified_corner_j on the sheet's full lattice.
  longer growth: the largest square over evidence/studies/square20-0826-95/squares-PHerc0826-seed*.csv
     (figlib.largest_delivered_sheet), the regrowths of the capped seeds. It is hole free and is not
     certified one lamina; the article's text says so.
Every sheet file is checked against the sha256 its squares row recorded before a pixel is drawn, and
every square is checked to be fully covered on its sheet's grid (for a certified square: covered; the
flags are cert.py's, whose counts that file carries).

Where a square is. The median px, py and pz of its cells (level 0 voxels). The slice is taken at the
median pz of the cells of the first certified square, rounded (rule SLICE_RULE); squares at other
heights are drawn at their px, py, that is projected along z onto the slice, and their own z is written
beside them and in the table.

The slice. The raw masked scan at --level (default 3; scale against level 0 from the zarr's .zattrs)
through the shared chunk cache, one whole axial plane, contrast stretched (figlib.stretch), cropped to
its non zero pixels plus a margin. The published umbilicus is the json figure C11 reads, interpolated
linearly in z. The sheets: for every delivered sheet file of every marked seed (the chain's C40 folder,
or the regrowth's C80 folder for the longer growth), rasterlib.plane_crossings at the slice height,
drawn one pixel wide into the raster in the colour of the traced sheets.

What it writes. The plotted table (--out), the raster (--png) and, beside the table's default place,
tools/c-f17-where-squares-body.tex, the TikZ overlay (markers, labels, scale bar, key) made from the
rows of the table; c-f17-where-squares.tex inputs it. With --out elsewhere the body goes next to --out.

NO INK: a plane of the scan and sheet geometry only; nothing is sampled along a sheet. Not for a public
repository without the owner's word (volume data of a competition scroll).

LOCATIONS WITHHELD (director 2026-09-30, the owner's decision: no locations on the scroll, every image kept). The
figure is the framed part around the squares only (what was panel b): the whole slice with the scroll's outline is no
longer read or drawn, the labels give each square's side and not its height, and the table writes «withheld» in
place of every scan position (the slice's height, the squares' centres and heights, the umbilicus point, the crop),
each still computed and checked here.

Usage: c-f17-where-squares.py [--out CSV] [--png PNG] [--level L]
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f17-where-squares"
RUNS = "/data/scrollagent/runs/rev1"
CHAIN_OUT = RUNS + "/chain-0826/out"
SQ20 = RUNS + "/square20-0826-95"
CERT = SQ20 + "/evidence/certified-squares.csv"
UMB = RUNS + "/field-0826-0800/scratch/20250821151701-umbilicus-20260808113303.json"
UMB_URL = RL.BUCKET + "/PHerc0826/representations/umbilicus/20250821151701-umbilicus-20260808113303.json"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
HOLE_FREE, CERTIFIED = 5, 3
SLICE_RULE = "median pz of the cells of the first certified square; rounded"
WITHHELD = "withheld"               # a scan position computed and checked here, not written (2026-09-30)
SHEET_RGB = (0, 158, 115)          # sagreen of figpreamble.tex: the traced sheets
WIDTH_CM = 8.6                      # display choice: one IEEE column


def interp(points, z):
    zs = np.array([p["z"] for p in points], dtype=np.float64)
    if np.any(np.diff(zs) <= 0):
        raise SystemExit("umbilicus control points are not strictly increasing in z")
    if z < zs.min() or z > zs.max():
        return None
    xs = np.array([p["x"] for p in points], dtype=np.float64)
    ys = np.array([p["y"] for p in points], dtype=np.float64)
    return float(np.interp(z, zs, xs)), float(np.interp(z, zs, ys))


def seed_no(point):
    return point.replace("PHerc0826-seed", "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    ap.add_argument("--level", type=int, default=3)
    ap.add_argument("--bar-mm", type=float, default=10.0)
    ap.add_argument("--margin", type=int, default=12)
    ap.add_argument("--zoom-level", type=int, default=1)
    ap.add_argument("--zoom-margin-mm", type=float, default=3.0)
    ap.add_argument("--zoom-bar-mm", type=float, default=5.0)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_out = os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    out = a.out or default_out
    png = a.png or os.path.join(here, "paper/figures/assets/%s-slice.png" % FIGURE)
    body = (os.path.join(here, "tools/%s-body.tex" % FIGURE) if os.path.abspath(out) == default_out
            else os.path.join(os.path.dirname(os.path.abspath(out)), "%s-body.tex" % FIGURE))
    busy = figlib.require_free_machine(2.0)
    rows = []

    def put(what, source_file, source_column, value, key="", panel="a"):
        rows.append(dict(key=key, panel=panel, what=what, source_file=source_file, source_column=source_column,
                         value=value))

    # ---- the squares -------------------------------------------------------------------------------
    chain_rel = "evidence/studies/chain-0826"
    chain_glob = chain_rel + "/squares-PHerc0826-seed*.csv"
    by_seed = {}
    rows_of = {}
    for p in sorted(glob.glob(os.path.join(here, chain_glob))):
        _, _, rs = figlib.read_study_csv(p)
        for r in rs:
            if r.get("status") != "measured":
                continue
            v = figlib.number(r.get("square_mm_min_step"))
            if v is None:
                continue
            rows_of[(r["point"], r["sheet"])] = (r, p)
            if r["point"] not in by_seed or v > by_seed[r["point"]][0]:
                by_seed[r["point"]] = (v, r, p)
    ranked = sorted(by_seed.values(), key=lambda t: (-t[0], t[1]["point"]))
    top = figlib.largest_delivered_sheet(os.path.join(here, chain_rel), pattern="squares-PHerc0826-seed*.csv")
    if ranked[0][1]["point"] != top["point"] or ranked[0][0] != top["value"]:
        raise SystemExit("the ranking's first seed is not figlib.largest_delivered_sheet's")
    put("rule for the hole free squares", chain_glob, "square_mm_min_step; status measured",
        "the %d seeds with the largest best square; one per seed" % HOLE_FREE)
    put("hole free squares marked", chain_glob, "square_mm_min_step", HOLE_FREE, key="n_hole_free")
    put("seeds ranked", chain_glob, "point", len(ranked), key="seeds_ranked")
    cut = ranked[HOLE_FREE - 1][0]
    ties = [t[1]["point"] for t in ranked[HOLE_FREE:] if t[0] == cut]
    put("seeds tied with the last one marked", chain_glob, "square_mm_min_step", "; ".join(ties) or "none")
    put("next value below the last one marked; mm", chain_glob, "square_mm_min_step",
        "%.4f" % ranked[HOLE_FREE][0] if len(ranked) > HOLE_FREE else figlib.NOT_MEASURABLE)

    marks = []   # dict: kind, point, sheet, file, sheet_dir, side, ci, cj, mm, source
    for v, r, p in ranked[:HOLE_FREE]:
        marks.append(dict(kind="hole free", point=r["point"], sheet=r["sheet"], file=r["file"], sha=r["sha256"],
                          sheet_dir=os.path.join(CHAIN_OUT, r["point"], "C40"), side=int(r["square_cells"]),
                          ci=int(r["square_corner_i"]), cj=int(r["square_corner_j"]), mm=r["square_mm_min_step"],
                          cells=(int(r["cells_i"]), int(r["cells_j"])),
                          source="%s; square_mm_min_step" % os.path.relpath(p, here)))

    # The ranking of the certified squares comes from the article's FROZEN yield-seeds.csv (column
    # best_certified_mm, one row per delivered seed of the chain as run), never from the live
    # certified-squares.csv, which cert_watch.sh still rewrites. From the live file only the C40 row of
    # each chosen seed is read, for its sheet, corner and cells, and it must carry the frozen value.
    ys_rel = "evidence/studies/search-yield-0826/yield-seeds.csv"
    _, _, yrs = figlib.read_study_csv(os.path.join(here, ys_rel))
    ranked_c = []
    for r in yrs:
        v = figlib.number(r["best_certified_mm"])
        if v is not None:
            ranked_c.append((v, r["seed"], r["best_certified_mm"]))
    ranked_c.sort(key=lambda t: (-t[0], t[1]))
    put("rule for the certified squares", ys_rel, "best_certified_mm",
        "the %d seeds with the largest best certified square; one per seed" % CERTIFIED)
    put("certified squares marked", ys_rel, "best_certified_mm", CERTIFIED, key="n_certified")
    put("seeds with a best certified square", ys_rel, "seed", len(ranked_c))
    cutc = ranked_c[CERTIFIED - 1][0]
    put("seeds tied with the last certified one marked", ys_rel, "best_certified_mm",
        "; ".join(t[1] for t in ranked_c[CERTIFIED:] if t[0] == cutc) or "none")
    put("next certified value below the last one marked; mm", ys_rel, "best_certified_mm",
        ranked_c[CERTIFIED][2] if len(ranked_c) > CERTIFIED else figlib.NOT_MEASURABLE)
    _, cfields, crs = figlib.read_study_csv(CERT)
    cert_rel = os.path.relpath(CERT, RUNS)
    import hashlib
    for v, seed, cell in ranked_c[:CERTIFIED]:
        hit = sorted((r for r in crs if r["source"] == "C40" and r["seed"] == seed and r["status"] == "measured"
                      and figlib.number(r["certified_square_mm"]) == v), key=lambda r: int(r["sheet"]))
        if not hit:
            raise SystemExit("%s: no measured C40 row of certified-squares.csv carries the frozen %s mm" % (seed, cell))
        r = hit[0]
        if r["certified_square_mm"] != cell:
            raise SystemExit("%s: certified_square_mm %s is not yield-seeds.csv's %s" % (seed, r["certified_square_mm"], cell))
        put("%s; C40 sheets carrying the frozen certified value" % seed, cert_rel, "certified_square_mm",
            "; ".join(x["sheet"] for x in hit) + " (the lowest sheet is used)")
        put("%s; sha256 of the certified-squares.csv row used" % seed, cert_rel, "the row's cells joined by commas",
            hashlib.sha256(",".join(r[f] for f in cfields).encode()).hexdigest())
        k = (r["seed"], r["sheet"])
        if k not in rows_of:
            raise SystemExit("certified row %s sheet %s has no squares row in the chain snapshot" % k)
        sr, sp = rows_of[k]
        if int(r["cells"]) != int(sr["points"]):
            raise SystemExit("%s sheet %s: certified cells %s is not the squares row's points %s"
                             % (k + (r["cells"], sr["points"])))
        marks.append(dict(kind="certified", point=r["seed"], sheet=r["sheet"], file=sr["file"], sha=sr["sha256"],
                          sheet_dir=os.path.join(CHAIN_OUT, r["seed"], "C40"), side=int(r["certified_square_cells"]),
                          ci=int(r["certified_corner_i"]), cj=int(r["certified_corner_j"]), mm=cell,
                          cells=(int(sr["cells_i"]), int(sr["cells_j"])),
                          source="%s; best_certified_mm" % ys_rel))

    rg_rel = "evidence/studies/square20-0826-95"
    rg = figlib.largest_delivered_sheet(os.path.join(here, rg_rel), pattern="squares-PHerc0826-seed*.csv")
    r = rg["row"]
    put("rule for the longer growth", rg_rel + "/squares-PHerc0826-seed*.csv", "square_mm_min_step",
        "the largest square over the regrowths (figlib.largest_delivered_sheet)")
    put("seeds regrown", rg_rel + "/squares-PHerc0826-seed*.csv", "point", rg["arms"])
    marks.append(dict(kind="longer growth", point=r["point"], sheet=r["sheet"], file=r["file"], sha=r["sha256"],
                      sheet_dir=os.path.join(SQ20, "out", r["point"], "C80"), side=int(r["square_cells"]),
                      ci=int(r["square_corner_i"]), cj=int(r["square_corner_j"]), mm=r["square_mm_min_step"],
                      cells=(int(r["cells_i"]), int(r["cells_j"])),
                      source="%s; square_mm_min_step" % os.path.relpath(rg["csv_path"], here)))

    # ---- each square's cells, centre and height ------------------------------------------------------
    for m in marks:
        f = os.path.join(m["sheet_dir"], m["file"])
        got = RL.sha256(f)
        if got != m["sha"]:
            raise SystemExit("%s: sha256 %s is not the %s its squares row measured" % (f, got, m["sha"]))
        mask, px, py, pz, _ = figlib.read_sheet(f)
        if mask.shape != m["cells"]:
            raise SystemExit("%s: grid %s is not the cells_i by cells_j of its squares row" % (f, mask.shape))
        sub = np.zeros_like(mask)
        sub[m["ci"]:m["ci"] + m["side"], m["cj"]:m["cj"] + m["side"]] = True
        sub &= mask
        if int(sub.sum()) != m["side"] ** 2:
            raise SystemExit("%s: the %s square is not fully covered on its grid" % (f, m["kind"]))
        m["x"], m["y"], m["z"] = (float(np.median(px[sub])), float(np.median(py[sub])), float(np.median(pz[sub])))
        m["zmin"], m["zmax"] = float(pz[sub].min()), float(pz[sub].max())
        m["sheet_rel"] = os.path.relpath(f, RUNS)

    first_cert = [m for m in marks if m["kind"] == "certified"][0]
    z0 = int(round(first_cert["z"]))
    if not first_cert["zmin"] <= z0 <= first_cert["zmax"] + 0.5:
        raise SystemExit("the slice's height is not inside the first certified square's heights")
    put("height of the slice; level 0 voxels", first_cert["sheet_rel"], SLICE_RULE, WITHHELD)
    put("seed of the first certified square", cert_rel, "seed", seed_no(first_cert["point"]), key="slice_seed")
    put("squares away from the slice", "", "", "drawn at their own median px and py: projected along z onto the slice")

    for n, m in enumerate(marks, 1):
        tag = "square %d, %s, %s sheet %s" % (n, m["kind"], m["point"], m["sheet"])
        put(tag + "; side mm", m["source"].split("; ")[0], m["source"].split("; ")[1], m["mm"])
        put(tag + "; cells and corner i;j", m["source"].split("; ")[0], "", "%d;%d;%d" % (m["side"], m["ci"], m["cj"]))
        put(tag + "; sheet file sha256", m["sheet_rel"], "sha256 of the squares row", m["sha"])
        put(tag + "; centre x;y;z; level 0 voxels", m["sheet_rel"], "median px; py; pz of the square's cells", WITHHELD)
        put(tag + "; z range of its cells", m["sheet_rel"], "min and max pz of the square's cells", WITHHELD)
    for k in ("hole free", "certified", "longer growth"):
        mm = [m for m in marks if m["kind"] == k]
        put("largest %s square marked; mm" % k, mm[0]["source"].split("; ")[0], mm[0]["source"].split("; ")[1],
            mm[0]["mm"], key="%s_top_mm" % k.replace(" ", "_"))
    zs = [m["z"] for m in marks]
    if not all(m["zmin"] <= m["z"] <= m["zmax"] for m in marks):
        raise SystemExit("a square's centre height is outside its cells' heights")
    put("lowest centre height of the squares marked; level 0 voxels", "", "", WITHHELD)
    put("highest centre height of the squares marked; level 0 voxels", "", "", WITHHELD)

    # ---- the slice -------------------------------------------------------------------------------------
    # Since 2026-09-30 (director, the release dry run) the published umbilicus is not drawn: with it and a scale bar the
    # squares' relative positions would turn into a radius and an angle about the scroll's axis.
    put("published umbilicus", "", "", "not drawn (locations withheld, 2026-09-30)")
    put("whole slice", "", "", "not read and not drawn (locations withheld, 2026-09-30)")
    vox, _ = RL.voxel()
    put("voxel; um", "pipeline/datasets/manifests/PHerc0826.json", "voxel_um through pipeline/datasets/voxel.py", "%g" % vox)

    # ---- panel b: the zoom, at a finer level --------------------------------------------------------
    # The rule: the bounding box of every marked square's centre, plus --zoom-margin-mm on each side,
    # read at --zoom-level. Panel a is the whole slice with that box outlined.
    zm = a.zoom_margin_mm * 1000.0 / vox
    zx0, zx1 = min(m["x"] for m in marks) - zm, max(m["x"] for m in marks) + zm
    zy0, zy1 = min(m["y"] for m in marks) - zm, max(m["y"] for m in marks) + zm
    scale_b = RL.level_scale(a.zoom_level)
    if scale_b[1] != scale_b[2]:
        raise SystemExit("level %d is not isotropic in y and x: %s" % (a.zoom_level, scale_b))
    fb = scale_b[1]
    mmpp_b = fb * vox / 1000.0
    rb = RL.RawReader(a.zoom_level)
    zlb = int(round(z0 / scale_b[0]))
    by0b, by1b = int(np.floor(zy0 / fb)), int(np.ceil(zy1 / fb))
    bx0b, bx1b = int(np.floor(zx0 / fb)), int(np.ceil(zx1 / fb))
    greyb, nchb = rb.plane(zlb, by0b, by1b, bx0b, bx1b)
    put("zoom rule", "", "", "bounding box of the squares' centres plus the margin on each side", panel="b")
    put("zoom margin; mm (display choice)", "argument --zoom-margin-mm", "", "%g" % a.zoom_margin_mm, panel="b",
        key="zoom_margin_mm")
    put("zoom level", "argument --zoom-level", "", a.zoom_level, panel="b", key="zoom_level")
    put("zoom level scale z;y;x against level 0", RL.RAW_URL + "/.zattrs", "multiscales scale",
        ";".join("%g" % v for v in scale_b), panel="b")
    put("zoom mm per pixel", "level scale times the voxel", "", "%.6f" % mmpp_b, panel="b")
    if not (0 <= zlb < rb.shape[0] and by1b > by0b and bx1b > bx0b):
        raise SystemExit("the zoom's slice or crop is empty or outside the volume")
    put("zoom slice at this level", "height over the level's z scale; rounded", "", WITHHELD, panel="b")
    put("zoom crop y0;y1;x0;x1 at this level", "the squares' centres", "zoom rule", WITHHELD, panel="b")
    put("zoom chunks read", "%s/%d" % (RL.RAW_URL, a.zoom_level), "one z layer", nchb, panel="b")
    put("sha256 of the zoom's grey bytes before the stretch", "%s/%d" % (RL.RAW_URL, a.zoom_level), "the crop",
        RL.plane_sha(greyb), panel="b")
    gb, lob, hib = figlib.stretch(greyb)
    put("zoom display window; low and high grey", "the zoom itself", "figlib.stretch 1st and 99.5th percentile",
        "%.0f;%.0f" % (lob, hib), panel="b")
    imgb = RL.rgb(gb)

    # ---- the traced sheets, in both panels -----------------------------------------------------------
    dirs = []
    for m in marks:
        if m["sheet_dir"] not in dirs:
            dirs.append(m["sheet_dir"])
    total = 0
    for d in dirs:
        files = sorted((x for x in os.listdir(d) if x.startswith("patch_") and x.endswith(".bin")),
                       key=lambda x: int(x[6:-4]))
        n_cross = 0
        for x in files:
            mk, px, py, pz, _ = figlib.read_sheet(os.path.join(d, x))
            ys, xs, _, _ = RL.plane_crossings(mk, px, py, pz, z0)
            RL.dots(imgb, ys / fb - by0b, xs / fb - bx0b, SHEET_RGB, r=1)
            n_cross += len(ys)
        total += n_cross
        put("sheet crossings with the slice; %s" % os.path.relpath(d, RUNS), os.path.relpath(d, RUNS),
            "rasterlib.plane_crossings of every patch_<n>.bin", "%d sheets; %d crossings" % (len(files), n_cross),
            panel="a;b")
    put("sheet folders traced", "", "", len(dirs), key="sheet_folders", panel="a;b")
    put("sheet crossings with the slice; total", "", "rasterlib.plane_crossings", total, key="crossings", panel="a;b")

    png_b = png[:-4] + "-zoom.png"
    RL.save_png(png_b, imgb)
    hb, wb = imgb.shape[:2]
    put("zoom raster; width;height in pixels", "paper/figures/assets/%s-slice-zoom.png (or --png with -zoom)" % FIGURE, "", "%d;%d" % (wb, hb), panel="b")
    put("scale bar", "", "", "not drawn (locations withheld, 2026-09-30)", panel="b")
    put("figure width; cm (display choice)", "", "", "%g" % WIDTH_CM, panel="a;b")

    # ---- the overlay, in cm on the page -----------------------------------------------------------------
    sb = WIDTH_CM / wb                 # cm per pixel of the zoom, the one panel
    top_b = 0.0
    Hb = hb * sb

    def cm_b(xv, yv):
        return (xv / fb - bx0b) * sb, top_b - (yv / fb - by0b) * sb

    style = {"hole free": "hf", "certified": "ct", "longer growth": "lg"}
    L = ["%% Generated by src/tools/%s.py from evidence/figures/%s.csv. Do not edit." % (FIGURE, FIGURE)]
    L.append("\\node[anchor=north west, inner sep=0] at (0,%.4f) {\\includegraphics[width=%.4fcm]{../paper/figures/assets/%s}};"
             % (top_b, WIDTH_CM, os.path.basename(png_b)))
    # panel b: the umbilicus if inside, every square, one label per seed placed where it overlaps no
    # other label, no mark and no fixed box, searched on rings of offsets; leader lines to its marks.
    boxes = []
    groups = {}
    for n, m in enumerate(marks):
        m["bx"], m["by"] = cm_b(m["x"], m["y"])
        groups.setdefault(m["point"], []).append(m)
        L.append("\\node[%s] (m%d) at (%.3f,%.3f) {};" % (style[m["kind"]], n, m["bx"], m["by"]))
        boxes.append((m["bx"] - 0.1, m["by"] - 0.1, m["bx"] + 0.1, m["by"] + 0.1))
    # fixed boxes of panel b: key top left, note bottom left, bar bottom right, letter
    # the key goes in the first of these corners that holds no mark: top right, top left under the panel
    # letter, bottom right over the scale bar, bottom left over the note
    key_w, key_h = 3.05, 2.0
    corners = [(WIDTH_CM - key_w - 0.08, top_b - 0.08), (0.08, top_b - 0.55),
               (WIDTH_CM - key_w - 0.08, top_b - Hb + 0.75 + key_h), (0.08, top_b - Hb + 0.45 + key_h)]
    key_at = None
    for kx, ky in corners:
        kb = (kx, ky - key_h, kx + key_w, ky)
        if not any(not (kb[2] < o[0] or kb[0] > o[2] or kb[3] < o[1] or kb[1] > o[3]) for o in boxes):
            key_at = (kx, ky)
            break
    if key_at is None:
        raise SystemExit("no corner of panel b is free of marks for the key")
    put("key corner of panel b; cm from its top left", "", "first corner free of marks", "%.2f;%.2f"
        % (key_at[0], key_at[1] - top_b), panel="b")
    boxes.append((key_at[0], key_at[1] - key_h, key_at[0] + key_w, key_at[1]))
    boxes.append((0.0, top_b - 0.5, 0.5, top_b))
    boxes.append((0.0, top_b - Hb, 2.6, top_b - Hb + 0.4))
    boxes.append((WIDTH_CM - 2.0, top_b - Hb, WIDTH_CM, top_b - Hb + 0.7))
    order = sorted(groups, key=lambda k: -max(float(x["mm"]) for x in groups[k]))
    for pt in order:
        ms = groups[pt]
        cx = sum(x["bx"] for x in ms) / len(ms)
        cy = sum(x["by"] for x in ms) / len(ms)
        texts = ["seed %s" % seed_no(pt)] + ["\\%skey{} %s mm" % (style[x["kind"]], x["mm"]) for x in ms]
        bw = 0.125 * max(len("seed %s" % seed_no(pt)), max(len("%s mm" % x["mm"]) + 3 for x in ms))
        bh = 0.33 * len(texts) + 0.1
        best = None
        for rad in (0.45, 0.6, 0.75, 1.0, 1.3, 1.7, 2.2, 2.8):
            for ang in range(0, 360, 15):
                t = np.deg2rad(ang)
                lx, ly = cx + rad * np.cos(t), cy + rad * np.sin(t)
                x0 = lx - bw / 2 if abs(np.cos(t)) < 0.3 else (lx if np.cos(t) > 0 else lx - bw)
                y1 = ly + bh / 2 if abs(np.sin(t)) < 0.3 else (ly + bh if np.sin(t) > 0 else ly)
                bb = (x0, y1 - bh, x0 + bw, y1)
                if bb[0] < 0.05 or bb[2] > WIDTH_CM - 0.05 or bb[1] < top_b - Hb + 0.05 or bb[3] > top_b - 0.05:
                    continue
                if any(not (bb[2] < o[0] or bb[0] > o[2] or bb[3] < o[1] or bb[1] > o[3]) for o in boxes):
                    continue
                best = bb
                break
            if best:
                break
        if best is None:
            raise SystemExit("no free place for the label of %s" % pt)
        boxes.append(best)
        L.append("\\node[lab, anchor=north west] (l%s) at (%.3f,%.3f) {%s};"
                 % (seed_no(pt), best[0], best[3], "\\\\".join(texts)))
        for x in ms:
            L.append("\\draw[lead] (m%d) -- (l%s);" % (marks.index(x), seed_no(pt)))
    L.append("\\node[note, anchor=south west] at (0.08,%.3f) {raw scan, no ink detector};" % (top_b - Hb + 0.08))
    L.append("\\node[key, anchor=north west] at (%.3f,%.3f) {%s};" % (key_at[0], key_at[1], "\\\\".join([
        "\\sheetkey{} sheets of these seeds",
        "\\ctkey{} certified square",
        "\\hfkey{} hole free square",
        "\\lgkey{} hole free, longer growth"])))
    with open(body, "w") as fh:
        fh.write("\n".join(L) + "\n")

    comment = ("figure C17, what the raster and its overlay drew, written by src/tools/%s.py at %s (cores busy %s): "
               "the part of one axial slice of the raw scan of PHerc0826 around the squares at level %d, with "
               "the crossings of the delivered sheets of the marked seeds and the centres of the best squares; "
               "every scan position withheld, no umbilicus and no scale bar (2026-09-30); ranking of certified squares from yield-seeds.csv. Chunks this "
               "run: %s. NO INK. Not for a public repository without the owner's word."
               % (FIGURE, figlib.utc_now(), "not checked" if busy is None else "%.1f" % busy, a.zoom_level,
                  "; ".join("%s %d" % kv for kv in rb.counts.items())))
    figlib.write_plotted(out, comment, FIELDS, rows)
    sys.stderr.write("%s\n%s\n%s: %d rows; chunks %s\n" % (png_b, body, out, len(rows), rb.counts))


if __name__ == "__main__":
    main()
