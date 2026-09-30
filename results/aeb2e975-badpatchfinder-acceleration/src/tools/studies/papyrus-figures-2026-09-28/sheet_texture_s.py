#!/usr/bin/env python3
"""sheet_texture_v2.py: sheet_texture.py with ONE change, in a new file, written 2026-09-24T12:1xZ on the director's
order of 2026-09-24T11:55:23Z point (1): a chunk is read from, and fetched into, the home's shared raw chunk cache
/data/scrollagent/data/cache/raw-chunks (tools/raw_chunk_cache.py, keyed by the bucket path; the VC3D remote cache
ink-detector-0139 renders through) first; the two flat caches below stay as read only fallbacks and nothing new is
written into them. Everything else is unchanged.

The raw texture of ONE delivered sheet, one sample per cell, for the owner's eye.

Written 2026-09-23T23:2xZ on the director's addition of 2026-09-23T23:01:57Z item 1 (seed169, sheet 0, the bar
17.2954 mm). NOT A MEASUREMENT OF INK: no detector runs.
Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.

The way villa-tracer-build/tools/render_surface.py made the V01 textures, and with its own functions (imported, not
copied): the RAW masked scan 20250521151220-8.640um-1.2m-116keV-masked.zarr level 0, NEAREST voxel (np.rint), one
value per cell; a cell in a chunk the bucket answers 404 for, or outside the volume, is «not measurable» (dark blue,
the words in the CSV, never a zero); a stored 0 is the mask value, kept as 0 in the CSV, drawn dark blue and left out
of the grey window; grey window = 1st and 99th percentiles of the nonzero samples; scale bar in mm.

What differs, because the input is a delivered sheet and not a tifxyz: the sheet is a patch_<n>.bin of packed records
of five float32 (x, y, px, py, pz), and its lattice is seed-search-1447/tools/square.py's: i = rint(x - min x),
j = rint(y - min y), image rows i and columns j, so the square of squares-<attempt>.csv (square_corner_i,
square_corner_j, square_cells) is drawn on it in orange, one cell wide, at those very cells. The grid step in mm is
read from that squares row (step_i_mm, step_j_mm), not recomputed.

FETCH. Only the chunks under the sheet's cells (nearest voxel), counted first; the count times 2,097,152 bytes is set
against the budget line of /data/scrollagent/tools/machine.sh (our disk N GB of B GB) and /data under 98 per cent
before a byte is fetched, and the plan is a CSV with its numbers. The cache is seeds-at-scale-1447/scratch/raw-chunks;
a chunk already in villa-tracer-build/scratch/raw-chunks (same array, same naming) is read from there, not refetched.

    sheet_texture.py <patch_n.bin> <label> <squares csv> <sheet number> <out png> [--streams 8] [--plan-only]
The per cell CSV is <out png> with .csv; the plan and fetch summary go to evidence/<label>-texture-*.csv.
"""
import argparse, csv, os, re, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from PIL import Image, ImageDraw

sys.path.insert(0, "/data/scrollagent/runs/rev1/villa-tracer-build/tools")
import render_surface as rs  # noqa: E402
sys.path.insert(0, "/data/scrollagent/tools")
import raw_chunk_cache as RC  # noqa: E402  (the shared cache: lookup, store, store_absent)

TOOL = "papyrus-figures-2026-09-28/tools/sheet_texture_s.py (squares-ink-1447/tools/sheet_texture_v2_squares.py with only this string changed)"
STUDY = "/data/scrollagent/runs/rev1/seeds-at-scale-1447"
CACHE = STUDY + "/scratch/raw-chunks"
OTHER = "/data/scrollagent/runs/rev1/villa-tracer-build/scratch/raw-chunks"
BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
ARRAY = "PHerc1447/volumes/20250521151220-8.640um-1.2m-116keV-masked.zarr/0"
SHAPE, CH = rs.SHAPE, rs.CH
NBYTES = CH ** 3
POINT = np.dtype([("x", "<f4"), ("y", "<f4"), ("px", "<f4"), ("py", "<f4"), ("pz", "<f4")])
NM = rs.NM


class Raw2(rs.Raw):
    def chunk(self, c):
        if c in self.cache:
            return self.cache[c]
        hit = RC.lookup("PHerc1447", None, 0, *c)
        if hit:
            a = np.fromfile(hit[1], dtype=np.uint8).reshape(CH, CH, CH) if hit[0] == "bin" else None
            if len(self.cache) > 600:
                self.cache.clear()
            self.cache[c] = a
            return a
        for base in ("%s/%d_%d_%d" % ((CACHE,) + c), "%s/%d_%d_%d" % ((OTHER,) + c)):
            if os.path.exists(base + ".bin"):
                a = np.fromfile(base + ".bin", dtype=np.uint8).reshape(CH, CH, CH)
                break
            if os.path.exists(base + ".absent"):
                a = None
                break
        else:
            raise SystemExit("chunk %r neither fetched nor recorded absent: run the fetch first" % (c,))
        if len(self.cache) > 600:
            self.cache.clear()
        self.cache[c] = a
        return a


def have(c):
    if RC.lookup("PHerc1447", None, 0, *c):
        return True
    return any(os.path.exists("%s/%d_%d_%d%s" % ((d,) + c + (e,))) for d in (CACHE, OTHER) for e in (".bin", ".absent"))


def budget():
    line = subprocess.run(["bash", "/data/scrollagent/tools/machine.sh"], capture_output=True, text=True).stdout.splitlines()[0]
    m = re.search(r"our disk (\d+) GB / (\d+)", line)
    if not m:
        raise SystemExit("machine.sh budget line not readable: %r" % line)
    st = shutil.disk_usage("/data")
    return int(m.group(1)), int(m.group(2)), st.used / st.total * 100.0, st.free, line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet"); ap.add_argument("label"); ap.add_argument("squares"); ap.add_argument("sheet_no", type=int)
    ap.add_argument("png")
    ap.add_argument("--streams", type=int, default=8)
    ap.add_argument("--plan-only", action="store_true")
    a = ap.parse_args()
    ev = os.environ["SA_EVIDENCE"]  # squares-ink-1447: the sheet's evidence directory

    rec = np.fromfile(a.sheet, dtype=POINT)
    u, v = rec["x"].astype(np.float64), rec["y"].astype(np.float64)
    ci, cj = np.rint(u - u.min()).astype(np.int64), np.rint(v - v.min()).astype(np.int64)
    ni, nj = int(ci.max()) + 1, int(cj.max()) + 1
    L = [l for l in open(a.squares, newline="") if not l.startswith('"#')]
    sq = [r for r in csv.DictReader(L) if r["sheet"] == str(a.sheet_no)]
    if len(sq) != 1:
        raise SystemExit("%s: %d rows for sheet %d" % (a.squares, len(sq), a.sheet_no))
    sq = sq[0]
    if (int(sq["cells_i"]), int(sq["cells_j"]), int(sq["points"])) != (ni, nj, len(rec)):
        raise SystemExit("lattice %dx%d with %d points differs from the squares row %sx%s with %s"
                         % (ni, nj, len(rec), sq["cells_i"], sq["cells_j"], sq["points"]))

    px, py, pz = rec["px"].astype(np.float64), rec["py"].astype(np.float64), rec["pz"].astype(np.float64)
    xi, yi, zi = np.rint(px).astype(int), np.rint(py).astype(int), np.rint(pz).astype(int)
    ins = (xi >= 0) & (yi >= 0) & (zi >= 0) & (zi < SHAPE[0]) & (yi < SHAPE[1]) & (xi < SHAPE[2])
    need = set(zip((zi[ins] // CH).tolist(), (yi[ins] // CH).tolist(), (xi[ins] // CH).tolist()))
    todo = sorted(c for c in need if not have(c))
    n_gb, b_gb, pct, free, line = budget()
    fetch_gb = len(todo) * NBYTES / 1e9
    ok = (n_gb + fetch_gb < b_gb) and (pct < 98.0) and (free - len(todo) * NBYTES > 6e9)
    with open(ev + "/%s-texture-fetch-plan.csv" % a.label, "w", newline="") as fh:
        fh.write("# written by %s. chunks_nearest: chunks of the raw masked scan under the sheet's cells rounded to the "
                 "nearest voxel; chunks_to_fetch: those in neither cache; the budget is machine.sh's first line, "
                 "read at plan time, and the fetch goes ahead only when our_disk_gb + fetch_gb < budget_gb, /data "
                 "under 98 per cent and more than 6 GB free after it.\n" % TOOL)
        w = csv.writer(fh)
        w.writerow(["label", "sheet", "cells", "cells_outside_volume", "chunks_nearest", "chunks_cached",
                    "chunks_to_fetch", "fetch_gb", "our_disk_gb", "budget_gb", "data_used_pct", "fetch_allowed",
                    "machine_sh_line"])
        w.writerow([a.label, a.sheet, len(rec), int((~ins).sum()), len(need), len(need) - len(todo), len(todo),
                    "%.3f" % fetch_gb, n_gb, b_gb, "%.1f" % pct, "yes" if ok else "no", line])
    print("plan: %d chunks under the sheet, %d to fetch (%.2f GB); our disk %d of %d GB; fetch %s"
          % (len(need), len(todo), fetch_gb, n_gb, b_gb, "allowed" if ok else "REFUSED"), flush=True)
    if not ok:
        raise SystemExit("fetch refused by the budget")
    if a.plan_only:
        return

    tally = {"bytes": 0, "ok": 0, "absent": 0, "failed": 0}
    lock = threading.Lock()
    local = threading.local()

    def one(c):
        s = getattr(local, "s", None)
        if s is None:
            s = local.s = requests.Session()
        url = "%s/%s/%d/%d/%d" % ((BUCKET, ARRAY) + c)
        if RC.lookup("PHerc1447", None, 0, *c):  # fetched by another tool since the plan
            with lock:
                tally["ok"] += 1
            return
        for attempt in range(5):
            try:
                r = s.get(url, timeout=60)
            except requests.RequestException:
                time.sleep(1 + attempt); continue
            if r.status_code == 404:
                RC.store_absent("PHerc1447", None, 0, *c)
                with lock:
                    tally["absent"] += 1
                return
            if r.status_code == 200 and len(r.content) == NBYTES:
                RC.store("PHerc1447", None, 0, *c, r.content)
                with lock:
                    tally["bytes"] += len(r.content); tally["ok"] += 1
                return
            time.sleep(1 + attempt)
        with lock:
            tally["failed"] += 1

    t0 = time.time()
    with ThreadPoolExecutor(a.streams) as ex:
        for n, _ in enumerate(ex.map(one, todo), 1):
            if n % 500 == 0:
                print("%d/%d %.1f MB/s" % (n, len(todo), tally["bytes"] / (time.time() - t0) / 1e6), flush=True)
    el = time.time() - t0
    with open(ev + "/%s-texture-fetch-summary.csv" % a.label, "w", newline="") as fh:
        fh.write("# written by %s. mb_per_s = bytes_over_wire / wall_seconds / 1e6. chunks_needed = cached + "
                 "fetched + absent + failed is checked in the last column.\n" % TOOL)
        w = csv.writer(fh)
        w.writerow(["chunks_needed", "chunks_already_cached", "chunks_fetched", "chunks_absent_404", "chunks_failed",
                    "bytes_over_wire", "wall_seconds", "mb_per_s", "streams", "counts_add_up"])
        add = len(need) == (len(need) - len(todo)) + tally["ok"] + tally["absent"] + tally["failed"]
        w.writerow([len(need), len(need) - len(todo), tally["ok"], tally["absent"], tally["failed"], tally["bytes"],
                    "%.2f" % el, "%.2f" % (tally["bytes"] / max(el, 1e-9) / 1e6), a.streams, "yes" if add else "no"])
    if tally["failed"]:
        raise SystemExit("%d chunks failed to arrive" % tally["failed"])

    raw = Raw2()
    vals_flat = raw.sample(px, py, pz)
    X = np.full((ni, nj), -1.0); Y = X.copy(); Z = X.copy(); VAL = np.full((ni, nj), np.nan)
    V = np.zeros((ni, nj), dtype=bool)
    X[ci, cj], Y[ci, cj], Z[ci, cj], VAL[ci, cj], V[ci, cj] = px, py, pz, vals_flat, True
    n_valid = int(V.sum()); n_nm = int(np.isnan(VAL[V]).sum()); n_zero = int((VAL[V] == 0).sum())
    pool = VAL[V]; pool = pool[~np.isnan(pool) & (pool > 0)]
    if pool.size:
        lo, hi = float(np.percentile(pool, 1)), float(np.percentile(pool, 99))
        win = "grey window p1 %.0f, p99 %.0f of the nonzero samples" % (lo, hi)
    else:
        lo, hi = float("nan"), float("nan")
        win = "NO nonzero raw sample: grey window not measurable"
    step_mm = min(float(sq["step_i_mm"]), float(sq["step_j_mm"]))
    vox, _ = rs.voxel_um("PHerc1447")
    header = ("%s sheet %d (%s): %d records on a %d by %d lattice (square.py's). Sampler nearest voxel of the RAW masked "
              "scan 20250521151220 level 0 (px, py, pz in voxels = raw voxels, voxel %s um). %s: p1 = %.1f, p99 = %.1f "
              "(nan = no such sample). Cells not measurable (outside the volume or absent chunk): %d of %d; cells whose "
              "stored value is 0, the mask value: %d. Columns x, y, z are px, py, pz."
              % (a.label, a.sheet_no, a.sheet, len(rec), ni, nj, vox, win, lo, hi, n_nm, n_valid, n_zero))
    out_csv = os.path.splitext(a.png)[0] + ".csv"
    rs.TOOL = TOOL + " (with villa-tracer-build/tools/render_surface.py's write_csv)"
    rs.write_csv(out_csv, header, X, Y, Z, V, VAL)
    g = rs.to_grey(VAL, 0.0 if not pool.size else lo, 255.0 if not pool.size else hi)
    g[~V] = (255, 255, 255)
    factor = max(1, 900 // max(ni, nj))
    im = Image.fromarray(g).resize((nj * factor, ni * factor), Image.NEAREST)
    d = ImageDraw.Draw(im)
    s, i0, j0 = int(sq["square_cells"]), int(sq["square_corner_i"]), int(sq["square_corner_j"])
    d.rectangle((j0 * factor, i0 * factor, (j0 + s) * factor - 1, (i0 + s) * factor - 1), outline=(255, 120, 20), width=3)
    lines = ["%s, sheet %d as delivered, %d cells on a %d by %d lattice (rows i, columns j)" % (a.label, a.sheet_no, n_valid, ni, nj),
             "nearest voxel, raw 8.64 um scan; " + win,
             "one pixel = one lattice cell of %.4f mm (step_i_mm, step_j_mm of the squares row, smaller)" % step_mm,
             "white = empty cell, dark blue = masked (0) or not measurable; orange = the largest square, %d cells, %s mm"
             % (s, sq["square_mm_min_step"]),
             "cells %d: raw grey %d, masked 0 %d, no chunk or outside %d" % (n_valid, n_valid - n_nm - n_zero, n_zero, n_nm)]
    rs.add_bar_and_title(im, step_mm / factor, "%s sheet %d, raw texture" % (a.label, a.sheet_no), lines).save(a.png)
    with open(ev + "/%s-texture-summary.csv" % a.label, "w", newline="") as fh:
        fh.write("# written by %s. valid_cells = cells_with_raw_grey + cells_masked_value_0 + cells_not_measurable, "
                 "checked in adds_up.\n" % TOOL)
        w = csv.writer(fh)
        w.writerow(["label", "sheet", "valid_cells", "cells_with_raw_grey", "cells_masked_value_0", "cells_not_measurable",
                    "grey_p1", "grey_p99", "step_mm", "square_cells", "square_corner_i", "square_corner_j", "png", "csv",
                    "adds_up"])
        w.writerow([a.label, a.sheet_no, n_valid, n_valid - n_nm - n_zero, n_zero, n_nm,
                    NM if not pool.size else "%.1f" % lo, NM if not pool.size else "%.1f" % hi, "%.6f" % step_mm,
                    s, i0, j0, a.png, out_csv, "yes"])
    print("texture written: %s, %s" % (a.png, out_csv), flush=True)


if __name__ == "__main__":
    main()
