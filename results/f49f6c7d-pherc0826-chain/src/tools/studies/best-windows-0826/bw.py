#!/usr/bin/env python3
"""bw.py: best-windows-0826 (DECLARATION.md 2026-09-29T06:14:07Z, director's order of 06:11:47Z). New file, coordinator agent,
2026-09-29T06:2xZ. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran. Imports certified-piece-0826's fibre.py, fibre2.py (sheet loader and mask check),
piece_texture.py (Raw2 sampler, constants) and dark.py (chunks_of) unchanged; writes only under best-windows-0826.

    bw.py selftest              S1 S2 S3 -> evidence/selftest.csv
    bw.py scan <label>          summed area tables over every window position -> scratch/cands/<label>.npz and .json
    bw.py order                 fetch order of the sheets -> scratch/order.txt
    bw.py one <label>           fibre attempts -> scratch/sheet/<label>.json, values in scratch/values/
    bw.py drop <label>          ledger row listing this sheet's fetched chunks, then their deletion
    bw.py combine               -> evidence/windows.csv, evidence/attempts.csv
"""
import csv, fcntl, json, math, os, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import requests

HERE = "/data/scrollagent/runs/rev1/best-windows-0826"
CP = "/data/scrollagent/runs/rev1/certified-piece-0826"
sys.path.insert(0, CP + "/tools")
import fibre as F  # noqa: E402
import fibre2 as F2  # noqa: E402  (its main does not run; it sets fibre.OUT in this process only)
PT = F.PT
DK = F.DK

TOOL = "best-windows-0826/tools/bw.py"
LEDGER = "/data/scrollagent/ledger/ledger.csv"
CACHE = HERE + "/scratch/raw-chunks"
CAND = HERE + "/scratch/cands"
SHEET = HERE + "/scratch/sheet"
VALS = HERE + "/scratch/values"
NM = "not measurable"
WMM, COV, FLAG, BAR = 20.0, 0.95, 0.01, 0.0680
TN, TSTEP, MINTILES, ATTEMPTS, SEP_MM = 128, 64, 8, 3, 10.0
MINFREE = 35e9
WAIT_S = 1800


def now():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()


def rows(p):
    return list(csv.DictReader(l for l in open(p) if not l.startswith("#")))


def population():
    R = rows(CP + "/evidence/fibre-ranking.csv")
    return [r for r in R if r["passes_bar"] == "yes" and not r["label"].startswith("LARGEST")]


def masks(label):
    p2 = CP + "/scratch/piece2/%s.npz" % label
    src = p2 if os.path.isfile(p2) else CP + "/scratch/piece/%s.npz" % label
    z = np.load(src)
    for k in ("valid", "v2", "self_conflict", "b_end", "a2_rule"):
        if k not in z.files:
            raise SystemExit("npz lacks %s" % k)
    j = json.load(open(CP + "/scratch/piece2/%s.json" % label))
    return z, src, float(j["step_i_mm"]), float(j["step_j_mm"])


def flag_of(z):
    v = z["valid"]
    return v & (z["v2"] | z["self_conflict"] | z["b_end"] | z["a2_rule"])


def sat(m):
    S = np.zeros((m.shape[0] + 1, m.shape[1] + 1), np.int64)
    S[1:, 1:] = m.astype(np.int64).cumsum(0).cumsum(1)
    return S


def boxsum(S, ci, cj):
    return S[ci:, cj:] - S[:-ci, cj:] - S[ci:, :-cj] + S[:-ci, :-cj]


def window_cells(si, sj):
    return int(math.ceil(WMM / si)), int(math.ceil(WMM / sj))


def candidates(valid, flag, ci, cj):
    """All positions: covered and flagged counts; candidate indices sorted by flag, hole, i0, j0."""
    n = ci * cj
    if valid.shape[0] < ci or valid.shape[1] < cj:
        return None
    cov = boxsum(sat(valid), ci, cj)
    fl = boxsum(sat(flag), ci, cj)
    ok = (cov >= COV * n) & (fl <= FLAG * n)
    I, J = np.nonzero(ok)
    c, f = cov[I, J], fl[I, J]
    o = np.lexsort((J, I, -c, f))  # flag asc, hole asc (= covered desc), i0, j0
    return I[o].astype(np.int32), J[o].astype(np.int32), c[o].astype(np.int32), f[o].astype(np.int32), cov, fl


def tile_corners(n):
    return sorted(set(list(range(0, n - TN + 1, TSTEP)) + [n - TN]))


def selftest():
    rows_ = []
    rng = np.random.default_rng(1)
    valid = rng.random((900, 900)) > 0.3
    valid[200:760, 300:860] = True
    flag = np.zeros_like(valid)
    r = candidates(valid, flag, 535, 535)
    ok1 = len(r[0]) > 0 and int(r[2][0]) == 535 * 535 and int(r[3][0]) == 0 and 200 <= r[0][0] <= 225 and 300 <= r[1][0] <= 325
    rows_.append(["S1", "synthetic 900 x 900 lattice, 30 per cent holes except a clean 560 x 560 block at (200, 300): first "
                  "candidate of a 535 cell window lies inside the block, covered 1, flagged 0", "inside, 1, 0",
                  "(%d, %d), %.4f, %d" % (r[0][0], r[1][0], r[2][0] / 535.0 ** 2, r[3][0]), "yes" if ok1 else "no"])
    valid2 = np.ones((535, 535), bool); flag2 = np.zeros_like(valid2)
    nfl = int(0.01 * 535 * 535) + 1
    flag2.ravel()[rng.choice(535 * 535, nfl, replace=False)] = True
    r2 = candidates(valid2, flag2, 535, 535)
    flag2.ravel()[np.flatnonzero(flag2.ravel())[0]] = False
    r3 = candidates(valid2, flag2, 535, 535)
    ok2 = len(r2[0]) == 0 and len(r3[0]) == 1
    rows_.append(["S2", "one window of 535 x 535, %d flagged cells (over 1 per cent) rejected; one fewer (at 1 per cent) accepted"
                  % nfl, "0 / 1", "%d / %d" % (len(r2[0]), len(r3[0])), "yes" if ok2 else "no"])
    tc = tile_corners(535)
    ok3 = len(tc) == 8 and tc[-1] + TN == 535 and tc[0] == 0
    rows_.append(["S3", "tile corners for n = 535: 8 per axis (64 tiles), last tile ends at the window edge",
                  "8, ends at 535", "%d, ends at %d" % (len(tc), tc[-1] + TN), "yes" if ok3 else "no"])
    p = HERE + "/evidence/selftest.csv"
    new = not os.path.isfile(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write("# written by %s selftest at %s; bars in DECLARATION.md (Checks)\n" % (TOOL, now()))
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(["test", "what", "bar", "got", "passes"])
        w.writerows(rows_)
    for x in rows_:
        print(x)
    ok = all(x[4] == "yes" for x in rows_)
    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


def scan(label):
    os.makedirs(CAND, exist_ok=True)
    out = CAND + "/%s.json" % label
    if os.path.isfile(out):
        return
    t0 = time.time()
    info = dict(label=label)
    try:
        z, src, si, sj = masks(label)
    except SystemExit as e:
        info.update(status=NM + ": %s" % e)
        json.dump(info, open(out, "w")); return
    # the mask check of fibre2.py: the npz's piece cell count equals certified-pieces.csv
    want = {L: c for L, _, c in F2.population()}.get(label)
    pc = int(z["piece"].sum())
    info.update(mask_src=src.replace("/data/scrollagent/runs/rev1/", ""), step_i_mm=si, step_j_mm=sj,
                piece_cells=pc, piece_cells_csv=want, mask_check="yes" if want == pc else "no")
    if want != pc:
        info.update(status=NM + ": mask differs")
        json.dump(info, open(out, "w")); return
    valid = z["valid"]; flag = flag_of(z)
    ci, cj = window_cells(si, sj)
    info.update(cells_i=ci, cells_j=cj, lattice=list(valid.shape), positions=0, candidates=0)
    r = candidates(valid, flag, ci, cj)
    if r is None:
        info.update(status="no candidate: lattice smaller than the window")
    else:
        I, J, c, f, cov, fl = r
        n = ci * cj
        info.update(positions=int(cov.size), candidates=int(len(I)),
                    best_covered_share_any="%.6f" % (cov.max() / n), min_flagged_share_any="%.6f" % (fl.min() / n))
        if len(I):
            info.update(status="candidates", first=dict(i0=int(I[0]), j0=int(J[0]), covered_share="%.6f" % (c[0] / n),
                                                        flagged_share="%.6f" % (f[0] / n)))
            np.savez_compressed(CAND + "/%s.npz" % label, I=I, J=J, C=c, Fl=f)
        else:
            info.update(status="no candidate")
    info["seconds"] = round(time.time() - t0, 1)
    json.dump(info, open(out + ".part", "w")); os.replace(out + ".part", out)
    print(label, info["status"], info.get("candidates"), info.get("first"), flush=True)


def order():
    L = []
    for r in population():
        j = json.load(open(CAND + "/%s.json" % r["label"]))
        if j.get("status") == "candidates":
            L.append((float(j["first"]["flagged_share"]), -float(j["first"]["covered_share"]), r["label"]))
    L.sort()
    with open(HERE + "/scratch/order.txt", "w") as f:
        f.writelines(x[2] + "\n" for x in L)
    print(len(L), "sheets with candidates")


# ---- fetch: own cache first, then the shared caches read only
DIRS = [CACHE, PT.CACHE, PT.CACHEP, PT.CACHE0, PT.OTHER]


def have(c):
    return any(os.path.exists("%s/%d_%d_%d%s" % ((d,) + c + (e,))) for d in DIRS for e in (".bin", ".absent"))


class Raw3(PT.Raw2):
    def chunk(self, c):
        if c in self.cache:
            return self.cache[c]
        for d in DIRS:
            base = "%s/%d_%d_%d" % ((d,) + c)
            if os.path.exists(base + ".bin"):
                try:
                    a = np.fromfile(base + ".bin", dtype=np.uint8).reshape(PT.CH, PT.CH, PT.CH)
                except (OSError, ValueError):
                    continue
                break
            if os.path.exists(base + ".absent"):
                a = None
                break
        else:
            raise SystemExit("chunk %r neither fetched nor recorded absent" % (c,))
        if len(self.cache) > 400:
            self.cache.clear()
        self.cache[c] = a
        return a


def fetch_raw(todo):
    """dark.py's request loop (copied), writing into this study's cache."""
    tally = {"ok": 0, "absent": 0, "failed": 0}
    lock = threading.Lock(); local = threading.local()
    got = []

    def one(c):
        ss = getattr(local, "s", None)
        if ss is None:
            ss = local.s = requests.Session()
        url = "%s/%s/%d/%d/%d" % ((PT.BUCKET, PT.ARRAY) + c)
        base = "%s/%d_%d_%d" % ((CACHE,) + c)
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
    os.makedirs(CACHE, exist_ok=True)
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(one, todo))
    return tally, got


def plan_row(r):
    p = HERE + "/evidence/fetch-plan.csv"
    new = not os.path.isfile(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write("# written by %s: one row per fetch check; chunks of the raw masked scan 20250821151701 level 0 under the "
                    "cells (nearest voxel); fetch only if /data free minus other workers' reservations minus this fetch stays "
                    "above 35 GB\n" % TOOL)
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(["time", "label", "what", "chunks_needed", "chunks_cached", "chunks_to_fetch", "fetch_gb", "data_free_gb",
                        "reserved_by_others_gb", "decision"])
        w.writerow(r)


def fetch_chunks(label, need, what):
    """Returns (ok, gb, free_gb)."""
    t_end = time.time() + WAIT_S
    os.makedirs(HERE + "/scratch/lock", exist_ok=True)
    while True:
        lk = open(HERE + "/scratch/lock/fetch.lock", "a"); fcntl.flock(lk, fcntl.LOCK_EX)
        todo = sorted(c for c in need if not have(c))
        by = len(todo) * PT.NBYTES
        free = shutil.disk_usage("/data").free
        resv = 0
        for f_ in os.listdir(HERE + "/scratch/lock"):
            if f_.startswith("resv-") and f_ != "resv-%s" % label:
                try:
                    resv += int(open(HERE + "/scratch/lock/" + f_).read() or 0)
                except ValueError:
                    pass
        allowed = free - resv - by > MINFREE
        if allowed:
            open(HERE + "/scratch/lock/resv-%s" % label, "w").write(str(by))
        plan_row([now(), label, what, len(need), len(need) - len(todo), len(todo), "%.3f" % (by / 1e9), "%.1f" % (free / 1e9),
                  "%.2f" % (resv / 1e9), "fetch" if allowed else ("wait" if time.time() < t_end else "refused")])
        fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
        if allowed:
            break
        if time.time() >= t_end:
            return False, by / 1e9, free / 1e9
        time.sleep(60)
    try:
        tally, got = fetch_raw(todo) if todo else ({"ok": 0, "absent": 0, "failed": 0}, [])
        with open(HERE + "/scratch/sheet/fetched-%s.txt" % label, "a") as f:
            f.writelines(g + "\n" for g in got)
    finally:
        os.remove(HERE + "/scratch/lock/resv-%s" % label)
    print("%s %s: %d chunks, %d fetched, %d absent, %d failed (%.2f GB), free %.1f GB" % (
        label, what, len(need), tally["ok"], tally["absent"], tally["failed"], by / 1e9, free / 1e9), flush=True)
    return tally["failed"] == 0, by / 1e9, free / 1e9


def window_fibre(VAL, ok, si, sj):
    band, nondc, desc, white = F.bands(si, sj)
    sc = []
    for a in tile_corners(VAL.shape[0]):
        for b in tile_corners(VAL.shape[1]):
            if not ok[a:a + TN, b:b + TN].all():
                continue
            w = VAL[a:a + TN, b:b + TN]
            if np.isnan(w).any() or (w == 0).any():
                continue
            sc.append(F.wscore(w, band, nondc))
    ntiles = len(tile_corners(VAL.shape[0])) * len(tile_corners(VAL.shape[1]))
    return sc, ntiles, desc


def one(label):
    os.makedirs(SHEET, exist_ok=True); os.makedirs(VALS, exist_ok=True)
    out = SHEET + "/%s.json" % label
    if os.path.isfile(out):
        return
    t0 = time.time()
    cj_ = json.load(open(CAND + "/%s.json" % label))
    z, src, si, sj = masks(label)
    valid = z["valid"]; flag = flag_of(z)
    rec, IDX, piece, si2, sj2, bbox, msrc, CI, CJ = F2.load_sheet(label)
    ci, cj = cj_["cells_i"], cj_["cells_j"]
    cd = np.load(CAND + "/%s.npz" % label)
    I, J, C, Fl = cd["I"], cd["J"], cd["C"], cd["Fl"]
    n = ci * cj
    raw = Raw3()
    tried, att = [], []
    info = dict(label=label, cells_i=ci, cells_j=cj, step_i_mm=si, step_j_mm=sj, candidates=int(len(I)), fetch_gb=0.0)
    k = 0
    while len(att) < ATTEMPTS and k < len(I):
        i0, j0 = int(I[k]), int(J[k])
        cen = ((i0 + ci / 2.0) * si, (j0 + cj / 2.0) * sj)
        if any((cen[0] - t[0]) ** 2 + (cen[1] - t[1]) ** 2 < SEP_MM ** 2 for t in tried):
            k += 1; continue
        tried.append(cen)
        a = dict(attempt=len(att) + 1, cand_index=k, i0=i0, j0=j0, covered_share="%.6f" % (C[k] / n),
                 flagged_share="%.6f" % (Fl[k] / n), hole_share="%.6f" % (1 - C[k] / n))
        wv = valid[i0:i0 + ci, j0:j0 + cj]; wf = flag[i0:i0 + ci, j0:j0 + cj]
        a["sat_equals_direct"] = "yes" if (int(wv.sum()) == int(C[k]) and int(wf.sum()) == int(Fl[k])) else "no"
        cells = IDX[i0:i0 + ci, j0:j0 + cj][wv]
        cells = cells[cells >= 0]
        need = DK.chunks_of(rec[cells])
        okf, gb, free = fetch_chunks(label, need, "window %d (%d, %d)" % (len(att) + 1, i0, j0))
        info["fetch_gb"] += gb
        a["fetch_gb"] = "%.3f" % gb; a["data_free_gb"] = "%.1f" % free; a["chunks"] = len(need)
        if not okf:
            a.update(status=NM + ": fetch refused or failed (free %.1f GB)" % free, passes_fibre="no")
            att.append(a); k += 1
            continue
        VAL = np.full((ci, cj), np.nan, np.float32)
        v = raw.sample(*(rec[cells][c].astype(np.float64) for c in ("px", "py", "pz")))
        VAL[CI[cells] - i0, CJ[cells] - j0] = v
        okm = wv & ~wf
        sc, ntiles, desc = window_fibre(VAL, okm, si, sj)
        a.update(tiles=ntiles, tiles_accepted=len(sc), bands=desc)
        if len(sc) >= MINTILES:
            q = np.percentile(sc, [25, 50, 75])
            a.update(window_fibre="%.4f" % q[1], iqr="%.4f" % (q[2] - q[0]), passes_fibre="yes" if q[1] >= BAR else "no",
                     status="measured")
        else:
            a.update(window_fibre=NM, iqr=NM, passes_fibre="no", status=NM + ": %d tiles accepted, fewer than %d" % (len(sc), MINTILES))
        # per flag shares, direct
        for nm_, key in (("v2", "v2"), ("self_conflict_a", "self_conflict"), ("self_conflict_b", "b_end"), ("a2_rule", "a2_rule")):
            a[nm_ + "_share"] = "%.6f" % ((z[key][i0:i0 + ci, j0:j0 + cj] & wv).sum() / n)
        a["zero_or_nm_covered_share"] = "%.6f" % ((np.isnan(VAL) | (VAL == 0))[wv].sum() / float(wv.sum()))
        np.savez_compressed(VALS + "/%s-%d-%d.npz" % (label, i0, j0), val=VAL, valid=wv, flag=wf,
                            v2=z["v2"][i0:i0 + ci, j0:j0 + cj] & wv,
                            sc=(z["self_conflict"][i0:i0 + ci, j0:j0 + cj] | z["b_end"][i0:i0 + ci, j0:j0 + cj]) & wv,
                            a2r=z["a2_rule"][i0:i0 + ci, j0:j0 + cj] & wv, i0=i0, j0=j0)
        att.append(a); k += 1
        print(label, json.dumps({x: a.get(x) for x in ("attempt", "i0", "j0", "covered_share", "flagged_share", "window_fibre",
                                                      "tiles_accepted", "passes_fibre")}), flush=True)
        if a["passes_fibre"] == "yes":
            break
    win = next((a for a in att if a.get("passes_fibre") == "yes"), None)
    info.update(attempts=att, status="clean window" if win else ("no clean window" if att else "no candidate"),
                window=win, fetch_gb="%.3f" % info["fetch_gb"], seconds=round(time.time() - t0, 1))
    json.dump(info, open(out + ".part", "w")); os.replace(out + ".part", out)
    print(label, info["status"], "%.0f s" % info["seconds"], flush=True)


def drop(label, keep=False):
    p = HERE + "/scratch/sheet/fetched-%s.txt" % label
    files = [x.strip() for x in open(p) if x.strip()] if os.path.isfile(p) else []
    files = sorted(set(x for x in files if x.startswith(CACHE + "/") and os.path.exists(x)))
    gb = sum(os.path.getsize(x) for x in files) / 1e9
    with open(LEDGER, "a", newline="") as f:
        csv.writer(f).writerow([now(), "rev1", "coordinator-agent", "best-windows-0826-chunks-removal-listed-%s" % label,
                                "DECLARATION.md (Disk): after the window attempts of %s were written, the %d chunk files (%.2f GB) "
                                "fetched into best-windows-0826/scratch/raw-chunks, listed in %s, are deleted now" % (
                                    label, len(files), gb, p.replace("/data/scrollagent/", "")),
                                "tools/bw.py drop %s" % label, "", "", 0, p.replace("/data/scrollagent/", "")])
    for x in files:
        os.remove(x)
    os.replace(p, p + ".dropped")
    print("removed %d files, %.2f GB" % (len(files), gb))


def combine():
    head = ["rank", "label", "source", "seed", "sheet", "piece_strict_cm2", "piece_fibre", "status", "step_i_mm", "step_j_mm",
            "cells_i", "cells_j", "window_mm_i", "window_mm_j", "i0", "j0", "i1", "j1", "covered_share", "hole_share",
            "flagged_share", "v2_share", "self_conflict_a_share", "self_conflict_b_share", "a2_rule_share", "window_fibre", "iqr",
            "tiles_accepted", "tiles", "passes_fibre", "zero_or_nm_covered_share", "sat_equals_direct", "candidates", "attempts",
            "fetch_gb", "best3"]
    R, A = [], []
    for r in population():
        L = r["label"]
        cj_ = json.load(open(CAND + "/%s.json" % L)) if os.path.isfile(CAND + "/%s.json" % L) else dict(status="not run")
        sj_ = json.load(open(SHEET + "/%s.json" % L)) if os.path.isfile(SHEET + "/%s.json" % L) else None
        st = sj_["status"] if sj_ else (cj_["status"] if cj_.get("status") != "candidates" else "not reached")
        w = (sj_ or {}).get("window") or {}
        ci, cj = cj_.get("cells_i"), cj_.get("cells_j")
        si, sj = cj_.get("step_i_mm"), cj_.get("step_j_mm")
        row = dict(label=L, source=r["source"], seed=r["seed"], sheet=r["sheet"], piece_strict_cm2=r["strict_piece_cm2"],
                   piece_fibre=r["fibre_score"], status=st, step_i_mm=si, step_j_mm=sj, cells_i=ci, cells_j=cj,
                   window_mm_i="%.4f" % (ci * si) if ci else NM, window_mm_j="%.4f" % (cj * sj) if cj else NM,
                   candidates=cj_.get("candidates", NM), attempts=len((sj_ or {}).get("attempts", [])),
                   fetch_gb=(sj_ or {}).get("fetch_gb", "0.000"))
        if w:
            row.update({k: w.get(k) for k in ("i0", "j0", "covered_share", "hole_share", "flagged_share", "v2_share",
                                               "self_conflict_a_share", "self_conflict_b_share", "a2_rule_share", "window_fibre",
                                               "iqr", "tiles_accepted", "tiles", "passes_fibre", "zero_or_nm_covered_share",
                                               "sat_equals_direct")})
            row.update(i1=w["i0"] + ci - 1, j1=w["j0"] + cj - 1)
        R.append(row)
        for a in (sj_ or {}).get("attempts", []):
            A.append(dict(label=L, **a))
    clean = [x for x in R if x["status"] == "clean window"]
    clean.sort(key=lambda x: (float(x["flagged_share"]), float(x["hole_share"]), x["label"]))
    seeds = set(); nb = 0
    for n, x in enumerate(clean):
        x["rank"] = n + 1
        if x["seed"] not in seeds and nb < 3:
            seeds.add(x["seed"]); nb += 1; x["best3"] = "best %d" % nb
        else:
            x["best3"] = ""
    rest = [x for x in R if x["status"] != "clean window"]
    for x in rest:
        x["rank"] = ""; x["best3"] = ""
    t = now()
    with open(HERE + "/evidence/windows.csv.part", "w", newline="") as f:
        f.write("# written by %s combine at %s: one row per sheet of certified-piece-0826 fibre-ranking.csv with passes_bar yes; "
                "window = ceil(20 / step) cells per axis; candidate: covered_share >= %.2f and flagged_share <= %.2f (flagged = v2 or "
                "self conflict either end or a2 cluster rule, shares over all window cells); window_fibre = median of fibre.py's "
                "score over accepted 128 x 128 tiles (stride 64, all cells covered, unflagged, nonzero), passes at >= %.4f; clean "
                "windows ranked by flagged_share then hole_share; best3 = first three clean windows on different seeds; "
                "DECLARATION.md 2026-09-29T06:14:07Z\n" % (TOOL, t, COV, FLAG, BAR))
        w = csv.DictWriter(f, head, lineterminator="\n", restval=""); w.writeheader(); w.writerows(clean + rest)
    os.replace(HERE + "/evidence/windows.csv.part", HERE + "/evidence/windows.csv")
    ah = ["label", "attempt", "cand_index", "i0", "j0", "covered_share", "hole_share", "flagged_share", "v2_share",
          "self_conflict_a_share", "self_conflict_b_share", "a2_rule_share", "chunks", "fetch_gb", "data_free_gb", "tiles",
          "tiles_accepted", "window_fibre", "iqr", "passes_fibre", "zero_or_nm_covered_share", "sat_equals_direct", "status"]
    with open(HERE + "/evidence/attempts.csv", "w", newline="") as f:
        f.write("# written by %s combine at %s: every fibre attempt (at most %d per sheet, centres at least %.0f mm apart)"
                "\n" % (TOOL, t, ATTEMPTS, SEP_MM))
        w = csv.DictWriter(f, ah, lineterminator="\n", restval="", extrasaction="ignore"); w.writeheader(); w.writerows(A)
    print("rows %d, clean %d, attempts %d" % (len(R), len(clean), len(A)))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "selftest":
        sys.exit(0 if selftest() else 1)
    elif a[0] == "scan":
        scan(a[1])
    elif a[0] == "order":
        order()
    elif a[0] == "one":
        one(a[1])
    elif a[0] == "drop":
        drop(a[1])
    elif a[0] == "combine":
        combine()
    elif a[0] == "labels":
        for r in population():
            print(r["label"])
