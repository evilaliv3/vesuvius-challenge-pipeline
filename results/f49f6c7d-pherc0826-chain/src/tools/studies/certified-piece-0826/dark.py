#!/usr/bin/env python3
"""dark.py: dark cells of the certified pieces (certified-piece-0826 DECLARATION.md addition 2026-09-29T00:22Z, director
00:21:25Z). New file, 2026-09-29T00:2xZ, coordinator agent. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.

    dark.py plan                   one row per sheet -> evidence/dark-fetch-plan.csv (chunks needed by the union of the strict and
                                   open piece cells, cached, to fetch, GB, /data free); also scratch/dark/need-<label>.txt
    dark.py one <label> <deadline> sample, fetch if allowed, -> scratch/dark/<label>.json
    dark.py combine                -> evidence/dark-pieces.csv
    dark.py prune <label> [<keep label> ...]   list of this study's cached chunks needed by <label> and by none of the keep
                                   labels -> scratch/dark/prune-<label>.txt (the deletion is done by the caller after a ledger row)

Sampling: piece_texture.py's Raw2 (nearest voxel, raw masked scan 20250821151701 level 0; caches of this study, pairwise-cert,
square20 and chain read), imported unchanged; the fetch writes only into this study's scratch/raw-chunks (piece_texture.CACHE),
with piece_texture.py's request loop (copied: 5 attempts, 404 recorded .absent, 128^3 bytes). Threshold T = 0.5 x median over the
piece's cells of the sampled value, not measurable and stored 0 counted as 0; dark: value < T or value not measurable.
"""
import csv, glob, json, os, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import requests

HERE = "/data/scrollagent/runs/rev1/certified-piece-0826"
sys.path.insert(0, HERE + "/tools")
import piece_texture as PT  # noqa: E402  (its main does not run)

TOOL = "certified-piece-0826/tools/dark.py"
OUT = HERE + "/scratch/dark"
C = "/data/scrollagent/runs/rev1/chain-0826"
SHEETS = ["C40-PHerc0826-seed3648-S0", "C40-PHerc0826-seed2427-S0", "C40-PHerc0826-seed4391-S0", "C40-PHerc0826-seed6206-S0"]
NM = "not measurable"
MINFREE = 35e9


def now():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()


def masks(label):
    """(strict piece, open piece, step_i, step_j, source of the strict mask)."""
    p2 = HERE + "/scratch/piece2/%s.npz" % label
    p1 = HERE + "/scratch/piece/%s.npz" % label
    src = p2 if os.path.isfile(p2) else p1
    strict = np.load(src)["piece"]
    op = np.load(HERE + "/scratch/piece2/%s-open.npz" % label)["piece"]
    j = json.load(open(HERE + "/scratch/piece2/%s.json" % label))
    return strict, op, float(j["step_i_mm"]), float(j["step_j_mm"]), src


def lattice(label):
    seed = label.split("-S")[0].split("C40-")[1]
    rec = np.fromfile(C + "/out/%s/C40/patch_0.bin" % seed, dtype=PT.POINT)
    u, v = rec["x"].astype(np.float64), rec["y"].astype(np.float64)
    ci, cj = np.rint(u - u.min()).astype(np.int64), np.rint(v - v.min()).astype(np.int64)
    return rec, ci, cj


def cells(label):
    strict, op, si, sj, src = masks(label)
    rec, ci, cj = lattice(label)
    if strict.shape != (int(ci.max()) + 1, int(cj.max()) + 1):
        raise SystemExit("mask shape differs from the lattice")
    use = strict[ci, cj] | op[ci, cj]
    return rec[use], ci[use], cj[use], strict, op, si, sj, src


def chunks_of(rec):
    xi, yi, zi = (np.rint(rec[c].astype(np.float64)).astype(int) for c in ("px", "py", "pz"))
    ins = (xi >= 0) & (yi >= 0) & (zi >= 0) & (zi < PT.SHAPE[0]) & (yi < PT.SHAPE[1]) & (xi < PT.SHAPE[2])
    return set(zip((zi[ins] // PT.CH).tolist(), (yi[ins] // PT.CH).tolist(), (xi[ins] // PT.CH).tolist()))


def plan():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for L in SHEETS:
        rec, _, _, _, _, _, _, _ = cells(L)
        need = chunks_of(rec)
        todo = sorted(c for c in need if not PT.have(c))
        with open(OUT + "/need-%s.txt" % L, "w") as f:
            f.writelines("%d_%d_%d\n" % c for c in sorted(need))
        rows.append([L, len(rec), len(need), len(need) - len(todo), len(todo), "%.2f" % (len(todo) * PT.NBYTES / 1e9)])
    free = shutil.disk_usage("/data").free / 1e9
    p = HERE + "/evidence/dark-fetch-plan.csv"
    with open(p, "w", newline="") as f:
        f.write("# written by %s plan at %s: chunks of the raw masked scan under the union of the strict and open piece cells "
                "(nearest voxel); cached in any of the four caches or to fetch into this study's scratch/raw-chunks; /data free "
                "now; a sheet is fetched only if /data stays above 35 GB free after it and it fits before 05:30Z\n" % (TOOL, now()))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["label", "cells_sampled", "chunks_needed", "chunks_cached", "chunks_to_fetch", "fetch_gb", "data_free_gb_at_plan"])
        for r in rows:
            w.writerow(r + ["%.1f" % free])
    for r in rows:
        print(r, "free %.1f" % free)


def fetch(todo):
    tally = {"ok": 0, "absent": 0, "failed": 0}
    lock = threading.Lock(); local = threading.local()
    got = []

    def one(c):
        ss = getattr(local, "s", None)
        if ss is None:
            ss = local.s = requests.Session()
        url = "%s/%s/%d/%d/%d" % ((PT.BUCKET, PT.ARRAY) + c)
        base = "%s/%d_%d_%d" % ((PT.CACHE,) + c)
        for attempt in range(5):
            try:
                r = ss.get(url, timeout=60)
            except requests.RequestException:
                time.sleep(1 + attempt); continue
            if r.status_code == 404:
                open(base + ".absent", "w").close()
                with lock:
                    tally["absent"] += 1; got.append(base + ".absent")
                return
            if r.status_code == 200 and len(r.content) == PT.NBYTES:
                with open(base + ".part", "wb") as f:
                    f.write(r.content)
                os.replace(base + ".part", base + ".bin")
                with lock:
                    tally["ok"] += 1; got.append(base + ".bin")
                return
            time.sleep(1 + attempt)
        with lock:
            tally["failed"] += 1
    os.makedirs(PT.CACHE, exist_ok=True)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(one, todo))
    return tally, got


def one(L, deadline):
    out = OUT + "/%s.json" % L
    if os.path.isfile(out):
        return
    t0 = time.time()
    rec, ci, cj, strict, op, si, sj, src = cells(L)
    need = chunks_of(rec)
    todo = sorted(c for c in need if not PT.have(c))
    gb = len(todo) * PT.NBYTES / 1e9
    free = shutil.disk_usage("/data").free / 1e9
    info = dict(label=L, strict_mask=src, cells_sampled=len(rec), chunks_needed=len(need), chunks_to_fetch=len(todo),
                fetch_gb="%.2f" % gb, data_free_gb="%.1f" % free)
    late = time.time() > deadline
    if todo and (free * 1e9 - len(todo) * PT.NBYTES <= MINFREE or late):
        info.update(status="not measurable: fetch refused (free %.1f GB%s)" % (free, ", past the deadline" if late else ""))
    else:
        if todo:
            tally, got = fetch(todo)
            with open(OUT + "/fetched-%s.txt" % L, "w") as f:
                f.writelines(g + "\n" for g in got)
            info.update(fetched=tally["ok"], absent=tally["absent"], failed=tally["failed"])
            if tally["failed"]:
                info.update(status="not measurable: %d chunks failed" % tally["failed"])
        if "status" not in info:
            raw = PT.Raw2()
            val = raw.sample(rec["px"].astype(np.float64), rec["py"].astype(np.float64), rec["pz"].astype(np.float64))
            v0 = np.where(np.isnan(val), 0.0, val)
            info["status"] = "measured"
            for name, m in (("strict", strict), ("open", op)):
                sel = m[ci, cj]
                v = v0[sel]; n = int(sel.sum())
                med = float(np.median(v)) if n else float("nan")
                T = 0.5 * med
                dark = (v < T) | np.isnan(val[sel])
                nd = int(dark.sum())
                info[name] = dict(cells=n, cm2="%.4f" % (n * si * sj / 100), median="%.1f" % med, threshold="%.1f" % T,
                                  dark_cells=nd, not_measurable_or_zero=int(((v == 0)).sum()),
                                  piece_dark_share="%.4f" % (nd / n if n else float("nan")),
                                  piece_bright_cm2="%.4f" % ((n - nd) * si * sj / 100))
    info["seconds"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(info, open(out + ".part", "w")); os.replace(out + ".part", out)
    print(json.dumps(info), flush=True)


def combine():
    cols = ["label", "status", "strict_mask", "cells_sampled", "chunks_needed", "chunks_to_fetch", "fetch_gb", "data_free_gb"]
    sub = ["cells", "cm2", "median", "threshold", "dark_cells", "not_measurable_or_zero", "piece_dark_share", "piece_bright_cm2"]
    head = cols + ["strict_" + s for s in sub] + ["open_" + s for s in sub]
    R = []
    for L in SHEETS:
        f = OUT + "/%s.json" % L
        if not os.path.isfile(f):
            continue
        j = json.load(open(f))
        R.append([j.get(c, "") for c in cols] + [j.get("strict", {}).get(s, NM) for s in sub] + [j.get("open", {}).get(s, NM) for s in sub])
    with open(HERE + "/evidence/dark-pieces.csv.part", "w", newline="") as f:
        f.write("# written by %s combine at %s: per sheet, the strict piece and the open piece of evidence/certified-pieces.csv, "
                "each piece cell sampled at the nearest voxel of the raw masked scan (piece_texture.py's sampler); threshold = 0.5 x "
                "median over the piece's cells (not measurable counted 0); dark = under the threshold or not measurable; "
                "piece_dark_share = dark / cells; piece_bright_cm2 = (cells - dark) x step_i x step_j / 100; DECLARATION.md "
                "addition 2026-09-29T00:22Z\n" % (TOOL, now()))
        w = csv.writer(f, lineterminator="\n"); w.writerow(head); w.writerows(R)
    os.replace(HERE + "/evidence/dark-pieces.csv.part", HERE + "/evidence/dark-pieces.csv")
    print("combined %d rows" % len(R))


def prune(L, keep):
    need = set(open(OUT + "/need-%s.txt" % L).read().split())
    for k in keep:
        need -= set(open(OUT + "/need-%s.txt" % k).read().split())
    files = []
    for c in sorted(need):
        for e in (".bin", ".absent"):
            p = "%s/%s%s" % (PT.CACHE, c, e)
            if os.path.exists(p):
                files.append(p)
    with open(OUT + "/prune-%s.txt" % L, "w") as f:
        f.writelines(p + "\n" for p in files)
    print(len(files), "files", "%.2f GB" % (sum(os.path.getsize(p) for p in files) / 1e9))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "plan":
        plan()
    elif a[0] == "one":
        one(a[1], float(a[2]))
    elif a[0] == "combine":
        combine()
    elif a[0] == "prune":
        prune(a[1], a[2:])
