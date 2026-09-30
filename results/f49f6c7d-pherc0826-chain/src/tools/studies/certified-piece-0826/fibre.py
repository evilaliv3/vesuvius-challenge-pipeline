#!/usr/bin/env python3
"""fibre.py: fibre score of certified pieces and 20 x 20 mm crops (certified-piece-0826 DECLARATION.md addition
2026-09-29T01:24:25Z, director's order of 01:21:47Z). New file, 2026-09-29T01:2xZ, coordinator agent. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.

    fibre.py selftest                 rows F1 F2 F3 appended to evidence/selftest.csv
    fibre.py one <label> [crop]       score of one sheet -> scratch/fibre/<label>.json; with «crop» also the 20 x 20 mm crop
                                      png into outputs/artifacts/square-0826-seed2604/crop-<seed>.png; fetched chunks listed
                                      in scratch/fibre/fetched-<label>.txt (deleted by «fibre.py drop» after a ledger row)
    fibre.py drop <label>             ledger row listing the fetched chunks of <label>, then their deletion
    fibre.py combine                  -> evidence/fibre-score.csv and evidence/fibre-crops.csv

Draws: rng = numpy default_rng(20260929) restarted per sheet; i = rng.integers(bi0, bi1 - 126, 200000), then
j = rng.integers(bj0, bj1 - 126, 200000) (upper bound exclusive, so i in [bi0, bi1 - 127]); draw n is (i[n], j[n]).
Sampling: piece_texture.py's Raw2 (nearest voxel, raw masked scan 20250821151701 level 0), imported unchanged; fetch loop is
dark.py's fetch (writes only into this study's scratch/raw-chunks).
"""
import csv, glob, json, os, re, shutil, subprocess, sys
import numpy as np

HERE = "/data/scrollagent/runs/rev1/certified-piece-0826"
sys.path.insert(0, HERE + "/tools")
import piece_texture as PT  # noqa: E402
import dark as DK  # noqa: E402  (its main does not run)
rs = PT.rs

TOOL = "certified-piece-0826/tools/fibre.py"
OUT = HERE + "/scratch/fibre"
ART = "/data/scrollagent/outputs/artifacts/square-0826-seed2604"
SHEETS = ["C40-PHerc0826-seed3648-S0", "C40-PHerc0826-seed2427-S0", "C40-PHerc0826-seed4391-S0",
          "C40-PHerc0826-seed6206-S0", "C40-PHerc0826-seed3412-S0", "C40-PHerc0826-seed5364-S0"]
FROM_CSV = {"C40-PHerc0826-seed3648-S0", "C40-PHerc0826-seed2427-S0"}
N, NW, MAXDRAW, HW, RSEED = 128, 64, 200000, 2, 20260929
PMIN, PMAX = 0.15, 0.6
MINFREE = 35e9
CROP_MM, CROP_SHARE, CROP_MAX_GB = 20.0, 0.75, 1.0
NM = "not measurable"
HANN = np.outer(np.hanning(N), np.hanning(N))
LEDGER = "/data/scrollagent/ledger/ledger.csv"


def now():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()


def bands(si, sj):
    k = np.rint(np.fft.fftfreq(N) * N).astype(int)
    KI, KJ = np.meshgrid(k, k, indexing="ij")
    li, hi_ = N * si / PMAX, N * si / PMIN
    lj, hj = N * sj / PMAX, N * sj / PMIN
    bi = (np.abs(KI) >= li) & (np.abs(KI) <= hi_) & (np.abs(KJ) <= HW)
    bj = (np.abs(KJ) >= lj) & (np.abs(KJ) <= hj) & (np.abs(KI) <= HW)
    band = bi | bj
    nondc = ~((KI == 0) & (KJ == 0))
    ki = np.unique(np.abs(KI[bi])); kj = np.unique(np.abs(KJ[bj]))
    desc = "band I |ki| %d..%d with |kj| <= %d; band J |kj| %d..%d with |ki| <= %d; %d of %d non DC bins" % (
        ki.min(), ki.max(), HW, kj.min(), kj.max(), HW, int(band.sum()), int(nondc.sum()))
    return band, nondc, desc, band.sum() / nondc.sum()


def wscore(win, band, nondc):
    v = (win - win.mean()) * HANN
    P = np.abs(np.fft.fft2(v)) ** 2
    return float(P[band].sum() / P[nondc].sum())


def draws(piece, bbox):
    bi0, bi1, bj0, bj1 = bbox
    rng = np.random.default_rng(RSEED)
    if bi1 - bi0 + 1 < N or bj1 - bj0 + 1 < N:
        return np.zeros(0, int), np.zeros(0, int), np.zeros(0, bool)
    I = rng.integers(bi0, bi1 - N + 2, MAXDRAW)
    J = rng.integers(bj0, bj1 - N + 2, MAXDRAW)
    S = np.zeros((piece.shape[0] + 1, piece.shape[1] + 1), np.int64)
    S[1:, 1:] = piece.astype(np.int64).cumsum(0).cumsum(1)
    full = (S[I + N, J + N] - S[I, J + N] - S[I + N, J] + S[I, J]) == N * N
    return I, J, full


def pick(I, J, full, VAL, band, nondc):
    """Walk the draws in order; accept mask accepted windows whose values are all measurable and nonzero.
    Returns (scores, drawn, mask_accepted, accepted, pending) where pending = index of the first mask accepted draw whose
    values are not all sampled yet (None if the walk ended)."""
    sc, drawn, macc = [], 0, 0
    for n in range(len(I)):
        drawn = n + 1
        if not full[n]:
            continue
        w = VAL[I[n]:I[n] + N, J[n]:J[n] + N]
        if np.isinf(w).any():
            return sc, drawn - 1, macc, len(sc), n
        macc += 1
        if np.isnan(w).any() or (w == 0).any():
            continue
        sc.append(wscore(w, band, nondc))
        if len(sc) == NW:
            break
    return sc, drawn, macc, len(sc), None


def load_sheet(label):
    rec, ci, cj = DK.lattice(label)
    ni, nj = int(ci.max()) + 1, int(cj.max()) + 1
    p2 = HERE + "/scratch/piece2/%s.npz" % label
    src = p2 if os.path.isfile(p2) else HERE + "/scratch/piece/%s.npz" % label
    piece = np.load(src)["piece"]
    if piece.shape != (ni, nj):
        raise SystemExit("mask shape differs from the lattice")
    j = json.load(open(HERE + "/scratch/piece2/%s.json" % label))
    si, sj = float(j["step_i_mm"]), float(j["step_j_mm"])
    ii, jj = np.nonzero(piece)
    bbox = (int(ii.min()), int(ii.max()), int(jj.min()), int(jj.max()))
    IDX = np.full((ni, nj), -1, np.int64); IDX[ci, cj] = np.arange(len(rec))
    return rec, IDX, piece, si, sj, bbox, src, ci, cj


def values_from_csv(label, shape):
    """+inf = not sampled; NaN = not measurable."""
    p = HERE + "/scratch/texture/%s.csv" % label
    VAL = np.full(shape, np.inf)
    with open(p) as f:
        head = f.readline()
        m = re.search(r"rows (\d+) to (\d+) and columns (\d+) to (\d+)", head)
        a0, b0 = int(m.group(1)), int(m.group(3))
        r = csv.reader(f); next(r)
        ii, jj, vv = [], [], []
        for row in r:
            ii.append(int(row[0])); jj.append(int(row[1])); vv.append(float("nan") if row[5] == NM else float(row[5]))
    VAL[np.array(ii) + a0, np.array(jj) + b0] = np.array(vv)
    return VAL, p


def crop_place(piece, si, sj, bbox):
    ci_n, cj_n = int(round(CROP_MM / si)), int(round(CROP_MM / sj))
    ni, nj = piece.shape
    S = np.zeros((ni + 1, nj + 1), np.int64); S[1:, 1:] = piece.astype(np.int64).cumsum(0).cumsum(1)
    T = S[ci_n:, cj_n:] - S[:-ci_n, cj_n:] - S[ci_n:, :-cj_n] + S[:-ci_n, :-cj_n]
    share = T / float(ci_n * cj_n)
    ti, tj = np.meshgrid(np.arange(share.shape[0]), np.arange(share.shape[1]), indexing="ij")
    c0i, c0j = (bbox[0] + bbox[1]) / 2.0, (bbox[2] + bbox[3]) / 2.0
    d = (ti + ci_n // 2 - c0i) ** 2 + (tj + cj_n // 2 - c0j) ** 2
    ok = share >= CROP_SHARE
    if ok.any():
        dd = np.where(ok, d, np.inf); k = np.unravel_index(np.argmin(dd), dd.shape)
        rule = "at the bbox centre" if dd[k] <= 1.0 else "moved %.0f cells from the bbox centre" % np.sqrt(dd[k])
    else:
        k = np.unravel_index(np.argmax(share), share.shape); rule = "no place reaches %.2f: largest share" % CROP_SHARE
    return int(k[0]), int(k[1]), ci_n, cj_n, float(share[k]), rule


def fetch_cells(label, rec, idx_cells, tag):
    """Plan row and fetch for the given record indices; returns (ok, info)."""
    need = DK.chunks_of(rec[idx_cells])
    todo = sorted(c for c in need if not PT.have(c))
    gb = len(todo) * PT.NBYTES / 1e9
    free = shutil.disk_usage("/data").free / 1e9
    allowed = free * 1e9 - len(todo) * PT.NBYTES > MINFREE
    p = HERE + "/evidence/fibre-fetch-plan.csv"
    new = not os.path.isfile(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write("# written by %s: one row per fetch step; chunks of the raw masked scan under the cells (nearest voxel), cached "
                    "in any of the four caches or to fetch into this study's scratch/raw-chunks; fetch only if /data stays above 35 GB "
                    "free after it\n" % TOOL)
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(["time", "label", "step", "cells", "chunks_needed", "chunks_cached", "chunks_to_fetch", "fetch_gb",
                        "data_free_gb", "fetch_allowed"])
        w.writerow([now(), label, tag, len(idx_cells), len(need), len(need) - len(todo), len(todo), "%.3f" % gb, "%.1f" % free,
                    "yes" if allowed else "no"])
    print("%s %s: %d chunks, %d to fetch (%.2f GB), free %.1f GB, %s" % (label, tag, len(need), len(todo), gb, free,
          "allowed" if allowed else "REFUSED"), flush=True)
    if not allowed:
        return False, dict(gb=gb, free=free)
    got, tally = [], {"ok": 0, "absent": 0, "failed": 0}
    if todo:
        tally, got = DK.fetch(todo)
        with open(OUT + "/fetched-%s.txt" % label, "a") as f:
            f.writelines(g + "\n" for g in got)
    return tally["failed"] == 0, dict(gb=gb, free=free, fetched=tally["ok"], absent=tally["absent"], failed=tally["failed"])


def one(label, want_crop):
    os.makedirs(OUT, exist_ok=True)
    rec, IDX, piece, si, sj, bbox, src, CI, CJ = load_sheet(label)
    band, nondc, desc, white = bands(si, sj)
    I, J, full = draws(piece, bbox)
    info = dict(label=label, strict_mask=src, step_i_mm=si, step_j_mm=sj, bbox=list(bbox), bands=desc,
                white_noise_share="%.4f" % white, fetch_gb=0.0, fetched_chunks=0)
    raw = PT.Raw2()
    if label in FROM_CSV:
        VAL, p = values_from_csv(label, piece.shape)
        info["values"] = "scratch/texture csv of piece_texture.py (same sampler), no fetch"
    else:
        VAL = np.full(piece.shape, np.inf)
        info["values"] = "sampled here (piece_texture.py Raw2)"
    crop = None
    if want_crop:
        crop = crop_place(piece, si, sj, bbox)
    step = 0
    while True:
        sc, drawn, macc, acc, pend = pick(I, J, full, VAL, band, nondc)
        if pend is None:
            break
        # cells of the next mask accepted windows still unsampled (as many as are still missing), plus the crop once
        want = []
        k, n = 0, pend
        while n < len(I) and k < NW - acc:
            if full[n] and np.isinf(VAL[I[n]:I[n] + N, J[n]:J[n] + N]).any():
                want.append(IDX[I[n]:I[n] + N, J[n]:J[n] + N].ravel()); k += 1
            n += 1
        tag = "windows round %d (%d windows)" % (step, k)
        if crop is not None and step == 0:
            a, b, ci_n, cj_n, _, _ = crop
            cc = IDX[a:a + ci_n, b:b + cj_n][piece[a:a + ci_n, b:b + cj_n]]
            cchunks = DK.chunks_of(rec[cc]); ctodo = [c for c in cchunks if not PT.have(c)]
            info["crop_fetch_gb"] = "%.3f" % (len(ctodo) * PT.NBYTES / 1e9)
            if len(ctodo) * PT.NBYTES / 1e9 < CROP_MAX_GB:
                want.append(cc); tag += " and the crop"
            else:
                info["crop_status"] = "refused: crop fetch %.2f GB over 1 GB" % (len(ctodo) * PT.NBYTES / 1e9); crop = None
        cells = np.unique(np.concatenate(want)); cells = cells[cells >= 0]
        ok, fi = fetch_cells(label, rec, cells, tag)
        info["fetch_gb"] += fi["gb"]; info["fetched_chunks"] += fi.get("fetched", 0); info["data_free_gb"] = "%.1f" % fi["free"]
        if not ok:
            info["status"] = ("not measurable: fetch refused (free %.1f GB)" % fi["free"]) if "failed" not in fi else \
                "not measurable: %d chunks failed" % fi["failed"]
            break
        v = raw.sample(*(rec[cells][c].astype(np.float64) for c in ("px", "py", "pz")))
        VAL[CI[cells], CJ[cells]] = v
        step += 1
        if step > 20:
            info["status"] = "stopped after 20 fetch rounds"; break
    info.update(windows_drawn=drawn, windows_mask_accepted=macc, windows_accepted=acc, fetch_gb="%.3f" % info["fetch_gb"])
    if "status" not in info:
        if acc:
            q = np.percentile(sc, [25, 50, 75])
            info.update(status="measured" if acc == NW else "measured on %d windows (fewer than %d)" % (acc, NW),
                        fibre_score="%.4f" % q[1], iqr="%.4f" % (q[2] - q[0]), q25="%.4f" % q[0], q75="%.4f" % q[2],
                        window_scores=["%.4f" % s for s in sc])
        else:
            info.update(status=NM + ": no window accepted")
    if crop is not None and not str(info.get("status", "")).startswith(NM):
        info.update(render_crop(label, rec, IDX, piece, VAL, si, sj, crop))
    json.dump(info, open(OUT + "/%s.json.part" % label, "w")); os.replace(OUT + "/%s.json.part" % label, OUT + "/%s.json" % label)
    print(json.dumps({k: v for k, v in info.items() if k != "window_scores"}), flush=True)


def render_crop(label, rec, IDX, piece, VAL, si, sj, crop):
    from PIL import Image
    a, b, ci_n, cj_n, share, rule = crop
    seed = label.split("-")[2]
    V = VAL[a:a + ci_n, b:b + cj_n].copy(); pc = piece[a:a + ci_n, b:b + cj_n]
    if np.isinf(V[pc]).any():
        return dict(crop_status="not measurable: crop cells not sampled")
    pool = V[pc]; pool = pool[~np.isnan(pool) & (pool > 0)]
    lo, hi = float(np.percentile(pool, 1)), float(np.percentile(pool, 99))
    V[~pc] = 0
    g = rs.to_grey(V, lo, hi); g[~pc] = (255, 255, 255)
    im = Image.fromarray(g)
    step = min(si, sj)
    lines = ["rows %d to %d, columns %d to %d of the lattice (%d by %d cells, %.2f by %.2f mm); centre rule: %s" % (
             a, a + ci_n - 1, b, b + cj_n - 1, ci_n, cj_n, ci_n * si, cj_n * sj, rule),
             "piece cells %.1f per cent of the crop; white = not in the certified piece; dark blue = masked or not measurable" % (100 * share),
             "one pixel = one lattice cell (%.4f by %.4f mm); nearest voxel, raw 9.362 um scan; grey p1 %.0f to p99 %.0f" % (si, sj, lo, hi),
             "Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."]
    import textwrap
    lines = [x for t in lines for x in textwrap.wrap(t, 80)]
    p = ART + "/crop-%s.png" % seed
    rs.add_bar_and_title(im, step, "%s C40 sheet 0, 20 x 20 mm crop of the certified piece, raw texture" % seed, lines).save(p)
    return dict(crop_png=p, crop_i0=a, crop_j0=b, crop_cells_i=ci_n, crop_cells_j=cj_n, crop_piece_share="%.4f" % share,
                crop_rule=rule, crop_grey_p1="%.0f" % lo, crop_grey_p99="%.0f" % hi, crop_status="rendered")


def selftest():
    from scipy import ndimage
    from PIL import Image, ImageDraw
    rng = np.random.default_rng(1)
    n, st = 600, 0.0373
    ii, jj = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    grid = (((ii * st) % 0.3) < 0.1) | (((jj * st) % 0.3) < 0.1)
    F1 = 100 + 40 * grid + rng.normal(0, 10, (n, n))
    F2 = 128 + rng.normal(0, 30, (n, n))
    sm = ndimage.gaussian_filter(rng.normal(0, 1, (n, n)), 1.0 / st)
    F3 = 128 + 10 * sm / sm.std()
    im = Image.new("L", (n, n), 0); d = ImageDraw.Draw(im)
    for _ in range(25):
        cx, cy, r = rng.uniform(0, n), rng.uniform(0, n), rng.uniform(0.5, 1.5) / st
        m, th = int(rng.integers(3, 7)), rng.uniform(0, 2 * np.pi)
        d.polygon([(cx + r * np.cos(th + 2 * np.pi * q / m), cy + r * np.sin(th + 2 * np.pi * q / m)) for q in range(m)], fill=255)
    F3[np.array(im) > 0] = 20
    band, nondc, desc, white = bands(st, st)
    piece = np.ones((n, n), bool)
    I, J, full = draws(piece, (0, n - 1, 0, n - 1))
    res = {}
    for name, F in (("F1", F1), ("F2", F2), ("F3", F3)):
        sc, drawn, macc, acc, pend = pick(I, J, full, np.clip(F, 1, 255), band, nondc)
        res[name] = (float(np.median(sc)), acc)
    t = now()
    with open(HERE + "/evidence/selftest.csv", "a", newline="") as f:
        f.write("# written by %s selftest at %s: F1 F2 F3 synthetic 600 x 600 at step 0.0373 mm, all piece, same windows and "
                "spectrum as the measure (%s); bars in DECLARATION.md addition 2026-09-29T01:24:25Z\n" % (TOOL, t, desc))
        w = csv.writer(f, lineterminator="\n")
        f1 = res["F1"][0]
        w.writerow(["F1", "grid 0.3 mm period plus noise, fibre_score (windows %d)" % res["F1"][1],
                    "> 2 x F2 and > 2 x F3", "%.4f" % f1, "yes" if f1 > 2 * res["F2"][0] and f1 > 2 * res["F3"][0] else "no"])
        w.writerow(["F2", "white noise, fibre_score (windows %d; white share %.4f)" % (res["F2"][1], white), "< F1 / 2",
                    "%.4f" % res["F2"][0], "yes" if res["F2"][0] < f1 / 2 else "no"])
        w.writerow(["F3", "smooth field sigma 1 mm with polygonal holes, fibre_score (windows %d)" % res["F3"][1], "< F1 / 2",
                    "%.4f" % res["F3"][0], "yes" if res["F3"][0] < f1 / 2 else "no"])
    print(res, desc)


def drop(label):
    p = OUT + "/fetched-%s.txt" % label
    files = [x.strip() for x in open(p) if x.strip()] if os.path.isfile(p) else []
    files = [x for x in files if x.startswith(PT.CACHE + "/") and os.path.exists(x)]
    gb = sum(os.path.getsize(x) for x in files) / 1e9
    with open(LEDGER, "a", newline="") as f:
        csv.writer(f).writerow([now(), "coordinator", "coordinator-agent", "fibre-score-0826-chunks-removal-listed-%s" % label.split("-")[2],
                                "DECLARATION.md addition 2026-09-29T01:24:25Z: after the values of %s were written, the %d chunk files "
                                "(%.2f GB) this measure fetched into certified-piece-0826/scratch/raw-chunks, listed in %s, are deleted "
                                "now" % (label, len(files), gb, p.replace("/data/scrollagent/", "")),
                                "tools/fibre.py drop %s" % label, "", "", "0", p.replace("/data/scrollagent/", "")])
    for x in files:
        os.remove(x)
    print("removed %d files, %.2f GB" % (len(files), gb))


def combine():
    head = ["label", "status", "fibre_score", "iqr", "q25", "q75", "windows_drawn", "windows_mask_accepted", "windows_accepted",
            "bands", "white_noise_share", "fetch_gb", "fetched_chunks", "values", "strict_mask", "step_i_mm", "step_j_mm", "bbox"]
    ch = ["label", "crop_status", "crop_png", "crop_i0", "crop_j0", "crop_cells_i", "crop_cells_j", "crop_piece_share", "crop_rule",
          "crop_grey_p1", "crop_grey_p99", "crop_fetch_gb"]
    R, C2 = [], []
    for L in SHEETS:
        f = OUT + "/%s.json" % L
        if not os.path.isfile(f):
            continue
        j = json.load(open(f))
        R.append([" ".join(map(str, j[c])) if c == "bbox" else j.get(c, NM) for c in head])
        if "crop_status" in j:
            C2.append([j.get(c, NM) for c in ch])
    t = now()
    with open(HERE + "/evidence/fibre-score.csv.part", "w", newline="") as f:
        f.write("# written by %s combine at %s: fibre_score = median over accepted 128 x 128 windows of the axis band power "
                "(periods 0.15 to 0.6 mm along i or j, half width %d bins) over non DC power, Hann window, mean removed; windows drawn "
                "with default_rng(%d) inside the strict piece's bbox, accepted when all cells are piece cells with a measurable "
                "nonzero raw value; iqr = q75 - q25; DECLARATION.md addition 2026-09-29T01:24:25Z\n" % (TOOL, t, HW, RSEED))
        w = csv.writer(f, lineterminator="\n"); w.writerow(head); w.writerows(R)
    os.replace(HERE + "/evidence/fibre-score.csv.part", HERE + "/evidence/fibre-score.csv")
    with open(HERE + "/evidence/fibre-crops.csv", "w", newline="") as f:
        f.write("# written by %s combine at %s: 20 x 20 mm crops, one cell per pixel; centre rule in DECLARATION.md addition "
                "2026-09-29T01:24:25Z (bbox centre, else the nearest place with at least 75 per cent piece cells)\n" % (TOOL, t))
        w = csv.writer(f, lineterminator="\n"); w.writerow(ch); w.writerows(C2)
    print("combined %d rows, %d crops" % (len(R), len(C2)))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "selftest":
        selftest()
    elif a[0] == "one":
        one(a[1], len(a) > 2 and a[2] == "crop")
    elif a[0] == "drop":
        drop(a[1])
    elif a[0] == "combine":
        combine()
