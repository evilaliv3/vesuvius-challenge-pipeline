#!/usr/bin/env python3
"""fibre2.py: fibre score of every certified piece of 10 cm2 or more, and the ranking against the bar 0.0680
(certified-piece-0826 DECLARATION.md addition 2026-09-29T02:22:50Z, director's order of 02:21:36Z). New file, coordinator
agent. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran. fibre.py is imported unchanged; only its sheet loader and fetch step are replaced here:

  * the sheet file: C40 chain-0826/out/<seed>/C40/patch_<k>.bin, C80 square20-0826-95/out/<seed>/C80/patch_<k>.bin;
  * the mask's cell count is checked against certified-pieces.csv (recomputed_piece_cells or piece_cells);
  * the fetch step holds scratch/fibre2/fetch.lock while it checks /data: free minus the bytes other workers have reserved
    and not yet written must stay above 35 GB after this fetch; when it would not, but chunks of this study's cache or
    reservations are held by other workers, it waits (10 s steps, up to 40 min) for their deletion; otherwise it refuses.
  * (fix of 2026-09-29T02:27Z, after a race: a drop deleted chunks another worker had counted as cached and three sheets
    stopped with «neither fetched nor recorded absent»; no value was affected, the sampler refuses a missing chunk) a
    sheet holds a SHARED lock on scratch/fibre2/cache.lock from its first cached check until its row is written; drop
    takes it EXCLUSIVE, so no chunk is deleted while a sheet that may read it is running; a sheet waiting for disk
    releases it while it waits.

    fibre2.py list                 population -> scratch/fibre2/population.txt (label per line, largest first)
    fibre2.py one <label>          -> scratch/fibre2/<label>.json
    fibre2.py drop <label>         fibre.py drop (ledger row listing, then deletion)
    fibre2.py combine              -> evidence/fibre-ranking.csv
"""
import csv, fcntl, json, os, shutil, sys, time
import numpy as np

HERE = "/data/scrollagent/runs/rev1/certified-piece-0826"
sys.path.insert(0, HERE + "/tools")
import fibre as F  # noqa: E402
PT, DK = F.PT, F.DK

TOOL = "certified-piece-0826/tools/fibre2.py"
OUT = HERE + "/scratch/fibre2"
F.OUT = OUT
CH = "/data/scrollagent/runs/rev1/chain-0826"
ST = "/data/scrollagent/runs/rev1/square20-0826-95"
PAIR = "/data/scrollagent/runs/rev1/pairwise-cert-0826/evidence/pairwise-squares.csv"
REF, FACTOR = 0.0906, 0.75
BAR = 0.0680  # declared 02:22:50Z: 0.75 x 0.0906 = 0.06795, compared as 0.0680 (round() gave 0.0679 in binary floating point)
MINCM2 = 10.0
REUSED = {"C40-PHerc0826-seed%s-S0" % s for s in ("3648", "2427", "4391", "6206", "3412", "5364")}
NM = "not measurable"


def rows(p):
    return list(csv.DictReader(l for l in open(p) if not l.startswith("#")))


def strict(r):
    if r["piece_mask_status"].startswith("recomputed"):
        return float(r["recomputed_piece_cm2"]), int(r["recomputed_piece_cells"])
    return float(r["largest_certified_piece_cm2"]), int(r["piece_cells"])


def population():
    P = []
    for r in rows(HERE + "/evidence/certified-pieces.csv"):
        try:
            cm2, cells = strict(r)
        except ValueError:
            continue
        if cm2 >= MINCM2:
            P.append((-cm2, r["source"], r["seed"], int(r["sheet"]), r, cells))
    P.sort(key=lambda x: x[:4])
    return [("%s-%s-S%d" % (p[1], p[2], p[3]), p[4], p[5]) for p in P]


def load_sheet(label):
    src, rest = label.split("-", 1)
    seed, k = rest.rsplit("-S", 1)
    base = CH + "/out/%s/C40" % seed if src == "C40" else ST + "/out/%s/C80" % seed
    rec = np.fromfile(base + "/patch_%d.bin" % int(k), dtype=PT.POINT)
    u, v = rec["x"].astype(np.float64), rec["y"].astype(np.float64)
    ci, cj = np.rint(u - u.min()).astype(np.int64), np.rint(v - v.min()).astype(np.int64)
    ni, nj = int(ci.max()) + 1, int(cj.max()) + 1
    p2 = HERE + "/scratch/piece2/%s.npz" % label
    msrc = p2 if os.path.isfile(p2) else HERE + "/scratch/piece/%s.npz" % label
    piece = np.load(msrc)["piece"]
    if piece.shape != (ni, nj):
        raise SystemExit("mask shape differs from the lattice")
    want = {L: c for L, _, c in population()}.get(label)
    if want is not None and int(piece.sum()) != want:
        raise SystemExit("MASKDIFF: mask %d cells, certified-pieces.csv %d" % (int(piece.sum()), want))
    j = json.load(open(HERE + "/scratch/piece2/%s.json" % label))
    si, sj = float(j["step_i_mm"]), float(j["step_j_mm"])
    ii, jj = np.nonzero(piece)
    bbox = (int(ii.min()), int(ii.max()), int(jj.min()), int(jj.max()))
    IDX = np.full((ni, nj), -1, np.int64); IDX[ci, cj] = np.arange(len(rec))
    return rec, IDX, piece, si, sj, bbox, msrc, ci, cj


def held_by_others(label):
    n = 0
    for f in os.listdir(OUT):
        if f.startswith("resv-") and f != "resv-%s" % label:
            n += int(open(os.path.join(OUT, f)).read() or 0)
    cache = sum(e.stat().st_size for e in os.scandir(PT.CACHE)) if os.path.isdir(PT.CACHE) else 0
    return n, cache


CL = {"fh": None}


def cache_shared(on):
    if on and CL["fh"] is None:
        CL["fh"] = open(OUT + "/cache.lock", "a")
        fcntl.flock(CL["fh"], fcntl.LOCK_SH)
    elif not on and CL["fh"] is not None:
        fcntl.flock(CL["fh"], fcntl.LOCK_UN); CL["fh"].close(); CL["fh"] = None


def fetch_cells(label, rec, idx_cells, tag):
    need = DK.chunks_of(rec[idx_cells])
    t_end = time.time() + 2400
    while True:
        cache_shared(True)
        lk = open(OUT + "/fetch.lock", "a")
        fcntl.flock(lk, fcntl.LOCK_EX)
        todo = sorted(c for c in need if not PT.have(c))
        by = len(todo) * PT.NBYTES
        free = shutil.disk_usage("/data").free
        resv, cache = held_by_others(label)
        allowed = free - resv - by > F.MINFREE
        wait = (not allowed) and (resv + cache > 0) and time.time() < t_end
        if allowed:
            open(OUT + "/resv-%s" % label, "w").write(str(by))
        p = HERE + "/evidence/fibre-ranking-fetch-plan.csv"
        new = not os.path.isfile(p)
        with open(p, "a", newline="") as f:
            if new:
                f.write("# written by %s: one row per fetch attempt; fetch only if /data free minus other workers' reserved "
                        "bytes minus this fetch stays above 35 GB; «wait» when other workers hold chunks or reservations\n" % TOOL)
            w = csv.writer(f, lineterminator="\n")
            if new:
                w.writerow(["time", "label", "step", "cells", "chunks_needed", "chunks_cached", "chunks_to_fetch", "fetch_gb",
                            "data_free_gb", "reserved_by_others_gb", "study_cache_gb", "decision"])
            w.writerow([F.now(), label, tag, len(idx_cells), len(need), len(need) - len(todo), len(todo), "%.3f" % (by / 1e9),
                        "%.1f" % (free / 1e9), "%.2f" % (resv / 1e9), "%.2f" % (cache / 1e9),
                        "fetch" if allowed else ("wait" if wait else "refused")])
        fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
        if allowed:
            break
        if not wait:
            return False, dict(gb=by / 1e9, free=free / 1e9)
        cache_shared(False)
        time.sleep(10)
    got, tally = [], {"ok": 0, "absent": 0, "failed": 0}
    try:
        if todo:
            tally, got = DK.fetch(todo)
            with open(OUT + "/fetched-%s.txt" % label, "a") as f:
                f.writelines(g + "\n" for g in got)
    finally:
        os.remove(OUT + "/resv-%s" % label)
    print("%s %s: %d chunks, %d fetched (%.2f GB), free %.1f GB" % (label, tag, len(need), tally["ok"], by / 1e9, free / 1e9),
          flush=True)
    return tally["failed"] == 0, dict(gb=by / 1e9, free=free / 1e9, fetched=tally["ok"], absent=tally["absent"],
                                      failed=tally["failed"])


F.load_sheet = load_sheet
F.fetch_cells = fetch_cells


def one(label):
    if os.path.isfile(OUT + "/%s.json" % label):
        return
    try:
        F.one(label, False)
        cache_shared(False)
    except SystemExit as e:
        if str(e).startswith("MASKDIFF"):
            json.dump(dict(label=label, status=NM + ": mask differs (%s)" % e), open(OUT + "/%s.json" % label, "w"))
        else:
            raise


def combine():
    pieces = {("%s-%s-S%s" % (r["source"], r["seed"], r["sheet"])): r for r in rows(HERE + "/evidence/certified-pieces.csv")}
    dark = {r["label"]: r for r in rows(HERE + "/evidence/dark-pieces.csv")} if os.path.isfile(HERE + "/evidence/dark-pieces.csv") else {}
    pair = {("%s-%s-S%s" % (r["source"], r["seed"], r["sheet"])): r for r in rows(PAIR)}
    head = ["label", "source", "seed", "sheet", "strict_piece_cm2", "open_piece_cm2", "fibre_score", "iqr", "windows_drawn",
            "windows_accepted", "status", "passes_bar", "bright_cm2", "certified_square_mm", "certified_strict_square_mm",
            "pairwise_square_mm", "fetch_gb", "score_from"]
    R = []
    for L, r, _ in population():
        if L in REUSED:
            f, frm = HERE + "/scratch/fibre/%s.json" % L, "fibre.py (01:24:25Z)"
        else:
            f, frm = OUT + "/%s.json" % L, "fibre2.py"
        j = json.load(open(f)) if os.path.isfile(f) else dict(status=NM + ": not run")
        sc = j.get("fibre_score")
        ok = sc is not None and float(sc) >= BAR
        d = dark.get(L, {})
        br = d.get("strict_piece_bright_cm2") if d.get("status") == "measured" else None
        pr = pair.get(L, {})
        R.append([L, r["source"], r["seed"], r["sheet"], "%.4f" % strict(r)[0], r["largest_certified_piece_open_cm2"],
                  sc if sc else NM, j.get("iqr", NM), j.get("windows_drawn", NM), j.get("windows_accepted", NM), j.get("status"),
                  "yes" if ok else "no", br if br else "not measured", r["certified_square_mm"], r["certified_strict_square_mm"],
                  pr.get("certified_pairwise_square_mm") or "absent", j.get("fetch_gb", NM), frm])
    ok = [x for x in R if x[11] == "yes"]
    S = []
    if ok:
        a = max(ok, key=lambda x: float(x[4]))
        b = max(ok, key=lambda x: float(x[13]))
        S.append(["LARGEST_PIECE_PASSING"] + a[1:])
        S.append(["LARGEST_SQUARE_PASSING"] + b[1:])
    else:
        S.append(["LARGEST_PIECE_PASSING"] + ["none"] * (len(head) - 1))
    with open(HERE + "/evidence/fibre-ranking.csv.part", "w", newline="") as f:
        f.write("# written by %s combine at %s: every certified piece of 10 cm2 or more (strict: recomputed where recomputed), "
                "largest first; fibre_score as fibre.py (DECLARATION.md 01:24:25Z); bar %.4f = %.2f x reference %.4f (seed3648 C40 "
                "S0), passes when fibre_score >= bar; bright_cm2 = dark-pieces.csv strict_piece_bright_cm2; squares from "
                "certified-pieces.csv and pairwise-cert-0826 pairwise-squares.csv; %d rows, %d pass; last two rows are the "
                "summaries; DECLARATION.md addition 2026-09-29T02:22:50Z\n" % (TOOL, F.now(), BAR, FACTOR, REF, len(R), len(ok)))
        w = csv.writer(f, lineterminator="\n"); w.writerow(head); w.writerows(R); w.writerows(S)
    os.replace(HERE + "/evidence/fibre-ranking.csv.part", HERE + "/evidence/fibre-ranking.csv")
    print("rows %d, passing %d, bar %.4f" % (len(R), len(ok), BAR))
    for s in S:
        print(s)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    a = sys.argv[1:]
    if a[0] == "list":
        with open(OUT + "/population.txt", "w") as f:
            for L, r, c in population():
                if L not in REUSED:
                    f.write(L + "\n")
        print(len(population()), "rows;", sum(1 for _ in open(OUT + "/population.txt")), "to run")
    elif a[0] == "one":
        one(a[1])
    elif a[0] == "drop":
        lk = open(OUT + "/cache.lock", "a"); fcntl.flock(lk, fcntl.LOCK_EX)
        F.drop(a[1])
        fcntl.flock(lk, fcntl.LOCK_UN)
    elif a[0] == "combine":
        combine()
