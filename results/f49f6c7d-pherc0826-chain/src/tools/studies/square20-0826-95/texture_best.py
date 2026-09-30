#!/usr/bin/env python3
"""texture_best.py <label> <out_prefix> <seed> <patch_bin> <squares_csv> <sheet> <what> <masks_npz> [cert]: the raw texture of one
delivered PHerc0826 sheet's square region, Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.

Parameterized copy of tools/texture95.py, written 2026-09-28T17:4xZ by a coordinator agent on the director's order of
17:39:46Z (the best squares). The sampler, the grey window, the factor rule max(1, 900 // max(mi, mj)), MARGIN 60, the fetch
plan and budget test (stop under 40 GB free), the fetch loop, the colours (v2 red, self conflict magenta, both yellow, orange
outline) and the text are texture95.py's. Changes, and no others:
  1. seed, sheet file, squares CSV, sheet number, label and the «what» text are arguments (texture95.py's TARGETS dict and
     SEED constant are gone);
  2. the marks come from <masks_npz> (tools/check_best.py, cert.py's method) instead of scratch/check95/<tag>.npz, and a third
     flag, the a2 cluster rule holes, is drawn in green where present;
  3. with the optional argument «cert», the certified square of evidence/certified-squares.csv (C40 row of the seed and sheet;
     cells and corner on the full lattice, as cert.py writes them) is outlined in cyan beside the orange hole free square,
     after checking that every one of its cells is covered and unflagged in the masks (counts in the summary CSV); without
     it, the text says whether certified-squares.csv holds a row («not certified yet» if not);
  4. the two PNGs go to <out_prefix>-grey.png and <out_prefix>-marks.png, the CSVs to evidence/texture_best-<label>-*.csv and
     scratch/texture_best/<label>.csv; the text is split over more lines, wrapped at 80 characters, so that it fits the width.
"""
import csv, os, re, shutil, subprocess, sys, textwrap, threading, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from PIL import Image, ImageDraw

sys.path.insert(0, "/data/scrollagent/runs/rev1/villa-tracer-build/tools")
import render_surface as rs  # noqa: E402

TOOL = "square20-0826-95/tools/texture_best.py (parameterized copy of texture95.py)"
ST = "/data/scrollagent/runs/rev1/square20-0826-95"
C = "/data/scrollagent/runs/rev1/chain-0826"
CACHE = ST + "/scratch/raw-chunks"
OTHER = C + "/scratch/raw-chunks-20250821151701"
BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
ARRAY = "PHerc0826/volumes/20250821151701-9.362um-1.2m-113keV-masked.zarr/0"
SHAPE, CH = (16920, 8169, 8169), 128
rs.SHAPE, rs.CH = SHAPE, CH
NBYTES = CH ** 3
POINT = np.dtype([("x", "<f4"), ("y", "<f4"), ("px", "<f4"), ("py", "<f4"), ("pz", "<f4")])
NM = rs.NM
MARGIN = 60
CERT_CSV = ST + "/evidence/certified-squares.csv"


class Raw2(rs.Raw):
    def chunk(self, c):
        if c in self.cache:
            return self.cache[c]
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
    return any(os.path.exists("%s/%d_%d_%d%s" % ((d,) + c + (e,))) for d in (CACHE, OTHER) for e in (".bin", ".absent"))


def budget():
    line = subprocess.run(["bash", "/data/scrollagent/tools/machine.sh"], capture_output=True, text=True).stdout.splitlines()[0]
    m = re.search(r"our disk (\d+) GB / (\d+)", line)
    if not m:
        raise SystemExit("machine.sh budget line not readable: %r" % line)
    st = shutil.disk_usage("/data")
    return int(m.group(1)), int(m.group(2)), st.used / st.total * 100.0, st.free, line


def main():
    tag, prefix, SEED, sheet, squares, K, what, masks = sys.argv[1:9]
    want_cert = len(sys.argv) > 9 and sys.argv[9] == "cert"
    label = tag
    ev = ST + "/evidence"
    os.makedirs(CACHE, exist_ok=True); os.makedirs(ST + "/scratch/texture_best", exist_ok=True)
    rec = np.fromfile(sheet, dtype=POINT)
    u, v = rec["x"].astype(np.float64), rec["y"].astype(np.float64)
    ci, cj = np.rint(u - u.min()).astype(np.int64), np.rint(v - v.min()).astype(np.int64)
    ni, nj = int(ci.max()) + 1, int(cj.max()) + 1
    L = [l for l in open(squares, newline="") if not l.lstrip('"').startswith("#")]
    sq = [r for r in csv.DictReader(L) if r["sheet"] == K]
    if len(sq) != 1:
        raise SystemExit("%s: %d rows for sheet %s" % (squares, len(sq), K))
    sq = sq[0]
    if (int(sq["cells_i"]), int(sq["cells_j"]), int(sq["points"])) != (ni, nj, len(rec)):
        raise SystemExit("lattice %dx%d with %d points differs from the squares row" % (ni, nj, len(rec)))
    s, i0, j0 = int(sq["square_cells"]), int(sq["square_corner_i"]), int(sq["square_corner_j"])
    a0, a1 = max(0, i0 - MARGIN), min(ni, i0 + s + MARGIN)
    b0, b1 = max(0, j0 - MARGIN), min(nj, j0 + s + MARGIN)
    keep = (ci >= a0) & (ci < a1) & (cj >= b0) & (cj < b1)
    rec, ci, cj = rec[keep], ci[keep] - a0, cj[keep] - b0
    mi, mj = a1 - a0, b1 - b0
    px, py, pz = rec["px"].astype(np.float64), rec["py"].astype(np.float64), rec["pz"].astype(np.float64)
    xi, yi, zi = np.rint(px).astype(int), np.rint(py).astype(int), np.rint(pz).astype(int)
    ins = (xi >= 0) & (yi >= 0) & (zi >= 0) & (zi < SHAPE[0]) & (yi < SHAPE[1]) & (xi < SHAPE[2])
    need = set(zip((zi[ins] // CH).tolist(), (yi[ins] // CH).tolist(), (xi[ins] // CH).tolist()))
    todo = sorted(c for c in need if not have(c))
    n_gb, b_gb, pct, free, line = budget()
    fetch_gb = len(todo) * NBYTES / 1e9
    ok = (n_gb + fetch_gb < b_gb) and (pct < 98.0) and (free - len(todo) * NBYTES > 6e9) and (free - len(todo) * NBYTES > 40e9)
    with open(ev + "/texture_best-%s-fetch-plan.csv" % tag, "w", newline="") as fh:
        fh.write("# written by %s. the cells of the square and %d cells around it; chunks_nearest: chunks of the raw masked scan "
                 "under them rounded to the nearest voxel; chunks_to_fetch: those in neither cache; fetch only when our_disk_gb + "
                 "fetch_gb < budget_gb, /data under 98 per cent and more than 40 GB free after it (item 95's stop).\n" % (TOOL, MARGIN))
        w = csv.writer(fh)
        w.writerow(["label", "sheet", "cells", "cells_outside_volume", "chunks_nearest", "chunks_cached", "chunks_to_fetch",
                    "fetch_gb", "our_disk_gb", "budget_gb", "data_used_pct", "fetch_allowed", "machine_sh_line"])
        w.writerow([label, sheet, len(rec), int((~ins).sum()), len(need), len(need) - len(todo), len(todo), "%.3f" % fetch_gb,
                    n_gb, b_gb, "%.1f" % pct, "yes" if ok else "no", line])
    print("plan: %d chunks, %d to fetch (%.2f GB); fetch %s" % (len(need), len(todo), fetch_gb, "allowed" if ok else "REFUSED"), flush=True)
    if not ok:
        raise SystemExit("fetch refused by the budget")

    tally = {"bytes": 0, "ok": 0, "absent": 0, "failed": 0}
    lock = threading.Lock()
    local = threading.local()

    def one(c):
        ss = getattr(local, "s", None)
        if ss is None:
            ss = local.s = requests.Session()
        url = "%s/%s/%d/%d/%d" % ((BUCKET, ARRAY) + c)
        base = "%s/%d_%d_%d" % ((CACHE,) + c)
        for attempt in range(5):
            try:
                r = ss.get(url, timeout=60)
            except requests.RequestException:
                time.sleep(1 + attempt); continue
            if r.status_code == 404:
                open(base + ".absent", "w").close()
                with lock:
                    tally["absent"] += 1
                return
            if r.status_code == 200 and len(r.content) == NBYTES:
                with open(base + ".part", "wb") as f:
                    f.write(r.content)
                os.replace(base + ".part", base + ".bin")
                with lock:
                    tally["bytes"] += len(r.content); tally["ok"] += 1
                return
            time.sleep(1 + attempt)
        with lock:
            tally["failed"] += 1

    t0 = time.time()
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(one, todo))
    el = time.time() - t0
    with open(ev + "/texture_best-%s-fetch-summary.csv" % tag, "w", newline="") as fh:
        fh.write("# written by %s. chunks_needed = cached + fetched + absent + failed, checked in the last column.\n" % TOOL)
        w = csv.writer(fh)
        w.writerow(["chunks_needed", "chunks_already_cached", "chunks_fetched", "chunks_absent_404", "chunks_failed",
                    "bytes_over_wire", "wall_seconds", "counts_add_up"])
        add = len(need) == (len(need) - len(todo)) + tally["ok"] + tally["absent"] + tally["failed"]
        w.writerow([len(need), len(need) - len(todo), tally["ok"], tally["absent"], tally["failed"], tally["bytes"],
                    "%.2f" % el, "yes" if add else "no"])
    if tally["failed"]:
        raise SystemExit("%d chunks failed to arrive" % tally["failed"])

    raw = Raw2()
    vals_flat = raw.sample(px, py, pz)
    X = np.full((mi, mj), -1.0); Y = X.copy(); Z = X.copy(); VAL = np.full((mi, mj), np.nan)
    V = np.zeros((mi, mj), dtype=bool)
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
    vox, _ = rs.voxel_um("PHerc0826")
    header = ("%s (%s), rows %d to %d and columns %d to %d of the %d by %d lattice (the square and %d cells around it). Nearest "
              "voxel of the RAW masked PHerc0826 scan 20250821151701 level 0 (voxel %s um). %s: p1 = %.1f, p99 = %.1f. Cells not "
              "measurable: %d of %d; stored 0 (mask): %d. Columns x, y, z are px, py, pz."
              % (label, what, a0, a1 - 1, b0, b1 - 1, ni, nj, MARGIN, vox, win, lo, hi, n_nm, n_valid, n_zero))
    out_csv = ST + "/scratch/texture_best/%s.csv" % tag
    rs.TOOL = TOOL + " (with villa-tracer-build/tools/render_surface.py's write_csv)"
    rs.write_csv(out_csv, header, X, Y, Z, V, VAL)
    g = rs.to_grey(VAL, 0.0 if not pool.size else lo, 255.0 if not pool.size else hi)
    g[~V] = (255, 255, 255)
    factor = max(1, 900 // max(mi, mj))
    si0, sj0 = i0 - a0, j0 - b0
    k = np.load(masks)
    if k["valid"].shape != (ni, nj) or int(k["valid"].sum()) != int(sq["points"]):
        raise SystemExit("masks %s do not match the lattice" % masks)
    v2 = (k["v2c"] | k["v2j"])[a0:a1, b0:b1]; sc = k["self_conflict"][a0:a1, b0:b1]; a2r = k["a2_rule"][a0:a1, b0:b1]
    crow = [r for r in csv.DictReader([l for l in open(CERT_CSV, newline="") if not l.startswith("#")])
            if r["source"] == "C40" and r["seed"] == SEED and r["sheet"] == K]
    ver = {}
    if want_cert:
        if len(crow) != 1 or crow[0]["status"] != "measured":
            raise SystemExit("no measured certified row for %s sheet %s" % (SEED, K))
        cr = crow[0]
        cs_, ci0, cj0 = int(cr["certified_square_cells"]), int(cr["certified_corner_i"]), int(cr["certified_corner_j"])
        full = np.zeros((ni, nj), bool); full[ci0:ci0 + cs_, cj0:cj0 + cs_] = True
        flag = (k["v2c"] | k["v2j"] | k["self_conflict"] | k["a2_rule"])
        ver = dict(cert_square_cells_total=cs_ * cs_, cert_square_cells_covered=int((full & k["valid"]).sum()),
                   cert_square_cells_flagged=int((full & flag).sum()),
                   cert_square_inside_lattice="yes" if ci0 + cs_ <= ni and cj0 + cs_ <= nj else "no",
                   cert_square_mm_recomputed="%.4f" % (cs_ * step_mm), cert_square_mm_csv=cr["certified_square_mm"],
                   cert_square_inside_margin_window="yes" if ci0 >= a0 and cj0 >= b0 and ci0 + cs_ <= a1 and cj0 + cs_ <= b1 else "no")
        if ver["cert_square_cells_covered"] != cs_ * cs_ or ver["cert_square_cells_flagged"] or ver["cert_square_inside_margin_window"] != "yes":
            raise SystemExit("certified square check failed: %r" % ver)
        cert_txt = "cyan = the certified square, %d cells, %s mm (certified-squares.csv)" % (cs_, cr["certified_square_mm"])
    else:
        cert_txt = ("certified-squares.csv: certified square %s mm (not outlined)" % crow[0]["certified_square_mm"]) if crow \
            else ("not certified yet (no row in certified-squares.csv); cert.py's method run by check_best.py gives %.4f mm"
                  % (int(k["certified"][0]) * step_mm))
    pngs = []
    for name, marks in (("grey", False), ("marks", True)):
        gg = g.copy()
        if marks:
            gg[a2r] = (0, 170, 0)
            gg[v2] = (230, 30, 30); gg[sc] = (230, 0, 230); gg[v2 & sc] = (255, 200, 0)
        im = Image.fromarray(gg).resize((mj * factor, mi * factor), Image.NEAREST)
        d = ImageDraw.Draw(im)
        d.rectangle((sj0 * factor, si0 * factor, (sj0 + s) * factor - 1, (si0 + s) * factor - 1), outline=(255, 120, 20), width=3)
        if want_cert:
            c0i, c0j = ci0 - a0, cj0 - b0
            d.rectangle((c0j * factor, c0i * factor, (c0j + cs_) * factor - 1, (c0i + cs_) * factor - 1), outline=(0, 220, 255), width=3)
        lines = ["%s, sheet %s (%s): the square and %d cells around it, rows i, columns j" % (SEED, K, what, MARGIN),
                 "nearest voxel, raw %s um scan; %s; no ink detector" % (vox, win),
                 "one pixel = one lattice cell of %.4f mm; orange = the hole free square, %d cells, %s mm" % (step_mm, s, sq["square_mm_min_step"]),
                 cert_txt]
        if marks:
            lines += ["red = v2 crossed or jumped cells, magenta = self conflict at one pitch, yellow = both, green = a2 cluster",
                      "rule holes (tools/check_best.py, cert.py's method); inside the orange square: v2 %d, self conflict %d, a2 rule %d"
                      % (int(v2[si0:si0 + s, sj0:sj0 + s].sum()), int(sc[si0:si0 + s, sj0:sj0 + s].sum()), int(a2r[si0:si0 + s, sj0:sj0 + s].sum()))]
        else:
            lines += ["white = empty cell, dark blue = masked (0) or not measurable"]
        lines += ["Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."]
        lines = [x for t in lines for x in textwrap.wrap(t, 80)]
        p = "%s-%s.png" % (prefix, name)
        rs.add_bar_and_title(im, step_mm / factor, "%s sheet %s, raw texture" % (SEED, K), lines).save(p)
        pngs.append(p)
    with open(ev + "/texture_best-%s-summary.csv" % tag, "w", newline="") as fh:
        fh.write("# written by %s. valid_cells = cells_with_raw_grey + cells_masked_value_0 + cells_not_measurable.\n" % TOOL)
        w = csv.writer(fh)
        w.writerow(["label", "valid_cells", "cells_with_raw_grey", "cells_masked_value_0", "cells_not_measurable", "grey_p1",
                    "grey_p99", "step_mm", "square_cells", "square_corner_i", "square_corner_j", "square_mm", "certified_row",
                    "v2_in_square", "self_conflict_in_square", "a2_rule_in_square"] + sorted(ver) + ["masks", "png_grey", "png_marks", "csv"])
        w.writerow([label, n_valid, n_valid - n_nm - n_zero, n_zero, n_nm, NM if not pool.size else "%.1f" % lo,
                    NM if not pool.size else "%.1f" % hi, "%.6f" % step_mm, s, i0, j0, sq["square_mm_min_step"],
                    "yes" if crow else "absent", int(v2[si0:si0 + s, sj0:sj0 + s].sum()), int(sc[si0:si0 + s, sj0:sj0 + s].sum()),
                    int(a2r[si0:si0 + s, sj0:sj0 + s].sum())] + [ver[x] for x in sorted(ver)] + [masks, pngs[0], pngs[1], out_csv])
    print("texture written: %s" % ", ".join(pngs), flush=True)


if __name__ == "__main__":
    main()
