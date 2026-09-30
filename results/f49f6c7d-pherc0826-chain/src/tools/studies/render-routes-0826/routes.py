#!/usr/bin/env python3
"""routes.py: the rows of render-routes-0826 (DECLARATION.md): one surface of one route -> scratch/rows/<route>-<surface>.json,
private texture PNG; combine -> evidence/routes.csv. New file, coordinator agent, 2026-09-29. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.

    routes.py r1 <region>                      R1: regrid_z.py --fit spline on the region's certified piece -> scratch/r1/<region>
    routes.py measure L <region>               row of our lattice as delivered over the region
    routes.py measure R1 <region>              row of the R1 grid of the region
    routes.py measure R2native <start>         row of a tracer surface on its own grid (bilinear to our step)
    routes.py measure R2regrid <start>         row of a tracer surface regridded (regrid_z.py --fit none)
    routes.py measure R2bnative <start>        row of an R2b tracer surface (normal grids, sparse 2) on its own grid
    routes.py combine                          -> evidence/routes.csv

Imported unchanged: area-0826-90 area90.py and lamina.py (a2, v2 against the 800, pitch), sheet_cross_v2 (pair_v2, marks),
square.py largest_square, certified-piece-0826 fibre.py (bands, wscore), piece_texture.py Raw2 and dark.py fetch (their CACHE
redirected, in this process only, to this study's scratch/raw-chunks: the fetch writes only here; the other caches are read).
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "4")
import csv, glob, json, shutil, subprocess, sys, time
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

R1D = "/data/scrollagent/runs/rev1"
HERE = R1D + "/render-routes-0826"
sys.path.insert(0, HERE + "/tools")
sys.path.insert(0, R1D + "/area-0826-90/tools")
sys.path.insert(0, R1D + "/certified-piece-0826/tools")
import regrid_z as RZ  # noqa: E402
import area90 as A  # noqa: E402
import lamina as LA  # noqa: E402
import fibre as F  # noqa: E402
PT, DK = F.PT, F.DK
PT.CACHE = HERE + "/scratch/raw-chunks"          # this process only: fetches land in this study

S, V2, CR, SQ, MC, CRL = A.S, A.V2, A.CR, A.SQ, A.MC, A.CRL
TOOL = "render-routes-0826/tools/routes.py"
NM = "not measurable"
VOX = 9.362
MM = VOX * 1e-3
UMB = R1D + "/field-0826-0800/scratch/20250821151701-umbilicus-20260808113303.json"
ART = "/data/scrollagent/outputs/artifacts/render-routes-0826"
ROWS = HERE + "/scratch/rows"
MINFREE = 35e9
BW = R1D + "/best-windows-0826/evidence/windows.csv"
PIECE = R1D + "/certified-piece-0826/scratch/piece2"


def utc():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()


def rows(p):
    return list(csv.DictReader(l for l in open(p) if not l.lstrip('"').startswith("#")))


# ------------------------------------------------------------------------------------------------ regions
def regions():
    R = {}
    for r in rows(R1D + "/square20-0826-95/evidence/certified-squares.csv"):
        if r["source"] == "C40" and r["seed"] == "PHerc0826-seed5364" and r["sheet"] == "0":
            n, i0, j0 = int(r["certified_square_cells"]), int(r["certified_corner_i"]), int(r["certified_corner_j"])
            R["S5364sq"] = dict(label="C40-PHerc0826-seed5364-S0", seed="PHerc0826-seed5364", k=0, box=(i0, i0 + n - 1, j0, j0 + n - 1),
                                what="certified square %d cells" % n)
    head = open(BW).readline().strip()
    for r in rows(BW):
        b = r.get("best3", "")
        if b.startswith("best "):
            R["bw" + b.split()[1]] = dict(label=r["label"], seed=r["seed"], k=int(r["sheet"]),
                                          box=(int(r["i0"]), int(r["i1"]), int(r["j0"]), int(r["j1"])),
                                          what="best-windows %s (windows.csv header: %s)" % (b, head[:90]))
    return R


def patch_of(label):
    src, rest = label.split("-", 1)
    seed, k = rest.rsplit("-S", 1)
    base = R1D + "/chain-0826/out/%s/C40" % seed if src == "C40" else R1D + "/square20-0826-95/out/%s/C80" % seed
    return base + "/patch_%d.bin" % int(k)


def mask_npz(label):
    """certified-piece-0826's rule (fibre2.py, best-windows-0826): piece2/<label>.npz where it exists, else piece/<label>.npz."""
    p2 = PIECE + "/%s.npz" % label
    return p2 if os.path.isfile(p2) else R1D + "/certified-piece-0826/scratch/piece/%s.npz" % label


def step_of(label):
    j = json.load(open(PIECE + "/%s.json" % label))
    return float(j["step_i_mm"]), float(j["step_j_mm"])


# ------------------------------------------------------------------------------------------------ R1
def cmd_r1(region):
    R = regions()[region]
    out = HERE + "/scratch/r1/%s" % region
    if os.path.exists(out):
        print("exists", out); return
    os.makedirs(HERE + "/scratch/r1", exist_ok=True)
    i0, i1, j0, j1 = R["box"]
    side = max(i1 - i0 + 1, j1 - j0 + 1) + 128
    # fit box: the output grid's footprint (side cells about the centre, rotated: side x sqrt 2 / 2 each way) plus 32 cells
    ci, cj = (i0 + i1) / 2.0, (j0 + j1) / 2.0
    half = int(np.ceil(side * 0.7072)) + 32
    P, V = RZ.read_patch(patch_of(R["label"]))
    fb = (max(0, int(ci) - half), min(V.shape[0] - 1, int(ci) + half), max(0, int(cj) - half), min(V.shape[1] - 1, int(cj) + half))
    subprocess.check_call([sys.executable, HERE + "/tools/regrid_z.py", "run", "--input", patch_of(R["label"]), "--umbilicus", UMB,
                           "--out", out, "--box"] + [str(x) for x in fb] + ["--mask", mask_npz(R["label"]) + ":piece",
                           "--fit", "spline", "--knot-mm", "0.5", "--side", str(side), "--centre", str(ci), str(cj),
                           "--label", "R1-%s" % region])


# ------------------------------------------------------------------------------------------------ surfaces
def upsample(P, ok, f):
    """bilinear upsampling of a node grid by f (a new node valid only when its four corners are)."""
    n0, n1 = P.shape[:2]
    gi = np.arange(0, n0 - 1 + 1e-9, 1.0 / f); gj = np.arange(0, n1 - 1 + 1e-9, 1.0 / f)
    I0 = np.minimum(np.floor(gi).astype(int), n0 - 2); J0 = np.minimum(np.floor(gj).astype(int), n1 - 2)
    fi = (gi - I0)[:, None, None]; fj = (gj - J0)[None, :, None]
    Q = np.where(ok[..., None], P, 0.0)
    out = (Q[I0][:, J0] * (1 - fi) * (1 - fj) + Q[I0 + 1][:, J0] * fi * (1 - fj) + Q[I0][:, J0 + 1] * (1 - fi) * fj
           + Q[I0 + 1][:, J0 + 1] * fi * fj)
    v = ok[I0][:, J0] & ok[I0 + 1][:, J0] & ok[I0][:, J0 + 1] & ok[I0 + 1][:, J0 + 1]
    out[~v] = np.nan
    return out, v


def tracer_dir(start, root="r2"):
    xs = glob.glob(HERE + "/scratch/%s/%s/*/x.tif" % (root, start))
    if not xs:
        raise SystemExit("no tracer surface for %s" % start)
    return os.path.dirname(xs[0])


def r2_crop(name, P, V, half=80):
    """DECLARATION addition: tracer nodes within `half` native nodes of the node nearest the start point (80: 30 x 30 mm;
    R2c, addition 11:54Z: 160, 60 x 60 mm)."""
    st = {r["start"]: r for r in rows(HERE + "/evidence/r2-starts.csv")}[name]
    q = np.array([float(st["x"]), float(st["y"]), float(st["z"])])
    d = np.linalg.norm(np.where(V[..., None], P, 1e9) - q, axis=-1)
    a, b = np.unravel_index(np.argmin(d), d.shape)
    return (max(0, a - half), min(V.shape[0] - 1, a + half), max(0, b - half), min(V.shape[1] - 1, b + half), int(a), int(b))


def surface(route, name):
    """P (n, m, 3), ok, eval box (i0, i1, j0, j1) or None, masks for L, info."""
    info = {}
    if route == "L":
        R = regions()[name]
        P, V = RZ.read_patch(patch_of(R["label"]))
        z = np.load(mask_npz(R["label"]))
        masks = {k: z[k].astype(bool) for k in ("v2", "self_conflict", "b_end", "a2_rule") if k in z.files}
        info.update(label=R["label"], region_what=R["what"])
        return P, V, R["box"], masks, info, R
    if route == "R1":
        R = regions()[name]
        d = HERE + "/scratch/r1/%s" % name
        P, V = RZ.read_tifxyz(d)
        n = P.shape[0]; i0, i1, j0, j1 = R["box"]
        s = max(i1 - i0 + 1, j1 - j0 + 1)
        a = n // 2 - s // 2
        info.update(label=R["label"], region_what=R["what"], grid=d)
        return P, V, (a, a + s - 1, a, a + s - 1), None, info, R
    if route in ("R2native", "R2bnative", "R2cnative"):
        d = tracer_dir(name, {"R2native": "r2", "R2bnative": "r2b", "R2cnative": "r2c"}[route])
        P, V = RZ.read_tifxyz(d)
        c = r2_crop(name, P, V, 160 if route == "R2cnative" else 80)
        P, V = P[c[0]:c[1] + 1, c[2]:c[3] + 1], V[c[0]:c[1] + 1, c[2]:c[3] + 1]
        info["crop_native"] = " ".join(map(str, c[:4]))
        f = 20.0 / 4.0
        meta = json.load(open(d + "/meta.json"))
        P, V = upsample(P, V, int(round(f)))
        info.update(grid=d, native_scale=meta.get("scale"), upsample=int(round(f)), area_cm2_meta=meta.get("area_cm2"))
        return P, V, None, None, info, None
    if route == "R2regrid":
        d = tracer_dir(name)
        out = HERE + "/scratch/r2regrid/%s" % name
        if not os.path.exists(out):
            os.makedirs(HERE + "/scratch/r2regrid", exist_ok=True)
            Pn, Vn = RZ.read_tifxyz(d)
            c = r2_crop(name, Pn, Vn)
            subprocess.check_call([sys.executable, HERE + "/tools/regrid_z.py", "run", "--input", d, "--umbilicus", UMB, "--out", out,
                                   "--box"] + [str(x) for x in c[:4]] + ["--fit", "none", "--h", "4.0", "--side", "801",
                                   "--centre", str(c[4]), str(c[5]), "--label", "R2regrid-%s" % name])
        P, V = RZ.read_tifxyz(out)
        # crop to the valid bounding box
        ii, jj = np.nonzero(V)
        P, V = P[ii.min():ii.max() + 1, jj.min():jj.max() + 1], V[ii.min():ii.max() + 1, jj.min():jj.max() + 1]
        info.update(grid=out, source=d)
        return P, V, None, None, info, None
    raise SystemExit("route?")


# ------------------------------------------------------------------------------------------------ checks
def conflicts_ab(W, p):
    """lamina.conflicts(W, W, p, True)'s rule, both ends (a end as cert.py, b end as pairwise.py's conflict_pairs)."""
    ia, ja, Pa, Na = LA.cells(W)
    a_end = np.zeros(W["ok"].shape, bool); b_end = a_end.copy()
    if len(Pa) == 0:
        return a_end, b_end
    r = 1.5 * p
    t = cKDTree(Pa)
    M = t.sparse_distance_matrix(t, r, output_type="ndarray")
    a = M["i"]; b = M["j"]
    v = Pa[b] - Pa[a]; na = Na[a]
    along = (v * na).sum(1)
    lat = np.linalg.norm(v - along[:, None] * na, axis=1)
    ok = (np.abs(along) >= 0.5 * p) & (np.abs(along) <= 1.5 * p) & (lat <= max(W["si"], W["sj"])) & \
         (np.abs((na * Na[b]).sum(1)) >= S.COS_CO)
    geo = np.hypot((ia[a] - ia[b]) * W["si"], (ja[a] - ja[b]) * W["sj"])
    ok &= geo > 3 * p
    a_end[ia[a[ok]], ja[a[ok]]] = True; b_end[ia[b[ok]], ja[b[ok]]] = True
    return a_end, b_end


def checks(P, V, exclude=(), siblings=()):
    px, py, pz = [np.where(V, P[..., k], 0.0) for k in range(3)]
    W = S.working(px, py, pz, V, "PHerc0826", "route")
    s = W["s"]
    A.D.selftest_passed(); MC.selftest_ok()
    T, _ = MC.verdict_row("a2")
    Sd, _ = CRL.read_S(); Sv = Sd["a2"]
    gflag, meas, fl = A.a2_grid(px, py, pz, V, T)
    gsize, _ = CRL.clusters(gflag)
    hS, kept = CRL.rule_holes(gsize, Sv, V)
    a2cell = (A.block_mask(gflag, V.shape, MC.STRIDE) | hS) & V
    L2c, L2j, _ = A.thresholds()
    ks = np.unique(S.keys_of(W["P"][W["ok"]].astype(np.float64)))
    idx = A.index()
    cand = set()
    for q in S.dilate_keys(ks):
        for M in idx.get(int(q), ()):
            cand.add(M)
    cand -= set(exclude)
    sh = W["ok"].shape
    CROSS = np.zeros(sh, bool); JUMP = np.zeros(sh, bool)
    parts = [A.load_work(M) for M in sorted(cand)]
    n800 = len(parts)
    for sp in siblings:
        Ps, Vs = RZ.read_patch(sp)
        qx, qy, qz = [np.where(Vs, Ps[..., k], 0.0) for k in range(3)]
        parts.append(S.working(qx, qy, qz, Vs, "PHerc0826", os.path.basename(sp)))
    for B in parts:
        r = V2.pair_v2(W, B)
        if r is None:
            continue
        c_, j_ = V2.marks(r, L2c, L2j)
        CROSS |= c_; JUMP |= j_
    a_end, b_end = conflicts_ab(W, LA.pitch())
    gi, gj = A.nearest_block(V.shape, s, CROSS.shape)

    def full(m):
        return m[gi[:, None], gj[None, :]] & V
    return dict(v2=full(CROSS | JUMP), self_conflict=full(a_end), b_end=full(b_end), a2_rule=hS & V, a2_all=a2cell), \
        dict(partners="%d of the 800 and %d siblings (excluded: %s)" % (n800, len(parts) - n800, " ".join(sorted(exclude)) or "none"),
             a2_measurable=meas, a2_flagged=fl, working_stride=s)


# ------------------------------------------------------------------------------------------------ values
def values(P, V, tag):
    """holds a SHARED lock on scratch/cache.lock from the cache check to the end of sampling; tools/drop.py takes it EXCLUSIVE."""
    import fcntl
    lk = open(HERE + "/scratch/cache.lock", "a")
    fcntl.flock(lk, fcntl.LOCK_SH)
    try:
        return _values(P, V, tag)
    finally:
        fcntl.flock(lk, fcntl.LOCK_UN); lk.close()


def _values(P, V, tag):
    rec = np.zeros(int(V.sum()), PT.POINT)
    rec["px"], rec["py"], rec["pz"] = P[V, 0], P[V, 1], P[V, 2]
    need = DK.chunks_of(rec)
    todo = sorted(c for c in need if not PT.have(c))
    free = shutil.disk_usage("/data").free
    plan = dict(chunks_needed=len(need), chunks_to_fetch=len(todo), fetch_gb="%.3f" % (len(todo) * PT.NBYTES / 1e9),
                data_free_gb="%.1f" % (free / 1e9))
    p = HERE + "/evidence/fetch-plan.csv"
    new = not os.path.isfile(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write("# written by %s: one row per sampling; raw masked scan 20250821151701 level 0 chunks (128 cubed, uncompressed) "
                    "under the surface's valid nodes (nearest voxel); fetched into this study's scratch/raw-chunks only when /data "
                    "stays above 35 GB free after it\n" % TOOL)
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(["utc", "surface", "chunks_needed", "chunks_to_fetch", "fetch_gb", "data_free_gb", "allowed"])
        ok = free - len(todo) * PT.NBYTES > MINFREE
        w.writerow([utc(), tag, len(need), len(todo), plan["fetch_gb"], plan["data_free_gb"], "yes" if ok else "no"])
    if not ok:
        return None, dict(plan, fetch="refused")
    if todo:
        tally, got = DK.fetch(todo)
        with open(HERE + "/scratch/fetched-%s.txt" % tag, "a") as f:
            f.writelines(g + "\n" for g in got)
        if tally["failed"]:
            return None, dict(plan, fetch="failed %d" % tally["failed"])
    raw = PT.Raw2()
    VAL = np.full(V.shape, np.nan)
    VAL[V] = raw.sample(P[V, 0], P[V, 1], P[V, 2])
    return VAL, dict(plan, fetch="ok")


# ------------------------------------------------------------------------------------------------ measures
def spacing(P, V, axis):
    D = np.diff(P, axis=axis)
    m = (V[1:] & V[:-1]) if axis == 0 else (V[:, 1:] & V[:, :-1])
    return float(np.median(np.linalg.norm(D, axis=-1)[m]))


def roughness(P, V, box):
    N = RZ.normals(P, V)
    ang = []
    for ax in (0, 1):
        if ax == 0:
            d = (N[1:] * N[:-1]).sum(-1); m = np.isfinite(d)
            d = np.where(m, d, np.nan); full = np.full(V.shape, np.nan); full[:-1] = d
        else:
            d = (N[:, 1:] * N[:, :-1]).sum(-1); full = np.full(V.shape, np.nan); full[:, :-1] = d
        ang.append(np.degrees(np.arccos(np.clip(np.abs(full), 0, 1))))   # unsigned normals
    i0, i1, j0, j1 = box
    a = np.concatenate([x[i0:i1 + 1, j0:j1 + 1].ravel() for x in ang])
    a = a[np.isfinite(a)]
    if a.size == 0:
        return NM, NM
    return "%.3f" % np.median(a), "%.3f" % np.percentile(a, 90)


def angles(P, V, box):
    i0, i1, j0, j1 = box
    out = {}
    for ax, nm in ((0, "i"), (1, "j")):
        a3, ai = RZ.step_angles(P, V, ax)
        for arr, kind in ((a3, "3d"), (ai, "inplane")):
            x = arr[i0:i1 + 1, j0:j1 + 1] if ax == 0 else arr[i0:i1 + 1, j0:j1 + 1]
            x = x[np.isfinite(x)]
            out["angle_%s_to_z_%s_median" % (nm, kind)] = "%.2f" % np.median(x) if x.size else NM
            out["angle_%s_to_z_%s_iqr" % (nm, kind)] = "%.2f" % (np.percentile(x, 75) - np.percentile(x, 25)) if x.size else NM
    return out


def tiles_fibre(VAL, good, box, si, sj):
    try:
        band, nondc, desc, _ = F.bands(si, sj)
    except ValueError:      # a step so long that a fibre band holds no frequency bin (e.g. a horizontal surface on v = z)
        return NM, NM, 0, 0
    i0, i1, j0, j1 = box
    n = F.N
    def offs(a, b):
        L = b - a + 1
        if L < n:
            return []
        o = list(range(a, b - n + 2, 64))
        if o[-1] != b - n + 1:
            o.append(b - n + 1)
        return o
    sc, tot = [], 0
    for a in offs(i0, i1):
        for b in offs(j0, j1):
            tot += 1
            w = VAL[a:a + n, b:b + n]; g = good[a:a + n, b:b + n]
            if not g.all() or not np.isfinite(w).all() or (w == 0).any():
                continue
            sc.append(F.wscore(w, band, nondc))
    if len(sc) < 8:
        return NM, NM, len(sc), tot
    return "%.4f" % np.median(sc), "%.4f" % (np.percentile(sc, 75) - np.percentile(sc, 25)), len(sc), tot


def best_window(V, flagged, VAL, si, sj):
    ci, cj = int(np.ceil(20 / si)), int(np.ceil(20 / sj))
    n0, n1 = V.shape
    if n0 < ci or n1 < cj:
        return dict(window="no room: grid %dx%d, window %dx%d" % (n0, n1, ci, cj))
    def sat(m):
        Sx = np.zeros((n0 + 1, n1 + 1), np.int64); Sx[1:, 1:] = m.astype(np.int64).cumsum(0).cumsum(1)
        return Sx[ci:, cj:] - Sx[:-ci, cj:] - Sx[ci:, :-cj] + Sx[:-ci, :-cj]
    cov = sat(V) / float(ci * cj); fl = sat(flagged & V) / float(ci * cj)
    cand = np.argwhere((cov >= 0.95) & (fl <= 0.01))
    if len(cand) == 0:
        return dict(window="no candidate", window_candidates=0)
    key = np.lexsort((cand[:, 1], cand[:, 0], 1 - cov[cand[:, 0], cand[:, 1]], fl[cand[:, 0], cand[:, 1]]))
    tried = []
    good = V & ~flagged
    for kk in key:
        a, b = cand[kk]
        c = (a + ci / 2.0, b + cj / 2.0)
        if any(np.hypot((c[0] - t[0]) * si, (c[1] - t[1]) * sj) < 10.0 for t in tried):
            continue
        tried.append(c)
        f, iq, na, nt = tiles_fibre(VAL, good, (a, a + ci - 1, b, b + cj - 1), si, sj)
        if f != NM and float(f) >= 0.0680:
            return dict(window="clean window", window_i0=int(a), window_j0=int(b), window_cells="%dx%d" % (ci, cj),
                        window_covered=round(float(cov[a, b]), 6), window_flagged=round(float(fl[a, b]), 6), window_fibre=f,
                        window_tiles=na, window_attempts=len(tried), window_candidates=len(cand))
        if len(tried) >= 3:
            break
    return dict(window="no clean window (fibre)", window_attempts=len(tried), window_candidates=len(cand))


def png(VAL, V, flagged, box, title, path, h_mm):
    from PIL import Image, ImageDraw
    i0, i1, j0, j1 = box
    v = VAL[i0:i1 + 1, j0:j1 + 1]
    good = np.isfinite(v) & (v > 0)
    lo, hi = (np.percentile(v[good], 1), np.percentile(v[good], 99)) if good.any() else (0, 1)
    g = np.clip((np.nan_to_num(v) - lo) / max(1e-9, hi - lo), 0, 1) * 255
    rgb = np.stack([g] * 3, -1).astype(np.uint8)
    rgb[~V[i0:i1 + 1, j0:j1 + 1]] = 255
    im = Image.new("RGB", (rgb.shape[1], rgb.shape[0] + 40), "white")
    im.paste(Image.fromarray(rgb), (0, 0))
    d = ImageDraw.Draw(im)
    L = int(round(5.0 / h_mm))
    d.rectangle([10, rgb.shape[0] + 8, 10 + L, rgb.shape[0] + 14], fill="black")
    d.text((16 + L, rgb.shape[0] + 4), "5 mm", fill="black")
    d.text((10, rgb.shape[0] + 20), title[:120], fill="black")
    os.makedirs(ART, exist_ok=True)
    im.save(path)


def cmd_measure(route, name):
    os.makedirs(ROWS, exist_ok=True)
    out = ROWS + "/%s-%s.json" % (route, name)
    t0 = time.time()
    P, V, box, masks, info, R = surface(route, name)
    h = 0.5 * (spacing(P, V, 0) + spacing(P, V, 1))
    si, sj = spacing(P, V, 0) * MM, spacing(P, V, 1) * MM
    if route == "L":
        si, sj = step_of(R["label"])
        M = {k: masks[k] & V for k in masks}
        meta = dict(partners="masks of certified-piece-0826 piece2 npz", a2_measurable="", a2_flagged="", working_stride="")
    else:
        excl, sib = (), ()
        if route == "R1":
            seed, k = R["seed"], R["k"]
            excl = (A.label(seed, k),)
            sib = tuple(p for p in sorted(glob.glob(R1D + "/chain-0826/out/%s/C40/patch_*.bin" % seed))
                        if not p.endswith("patch_%d.bin" % k))
        M, meta = checks(P, V, excl, sib)
    flagged = M["v2"] | M["self_conflict"] | M.get("b_end", np.zeros_like(V)) | M["a2_rule"]
    cert = V & ~M["v2"] & ~M["self_conflict"] & ~M["a2_rule"]
    b, ci0, cj0 = SQ.largest_square(cert)
    stepmm = min(si, sj)
    VAL, vinfo = values(P, V, "%s-%s" % (route, name))
    if box is None:
        # the tracer: evaluated on its largest certified square (the 4 cm2 window, when found, is a separate column)
        box = (ci0, ci0 + b - 1, cj0, cj0 + b - 1) if b > 0 else (0, V.shape[0] - 1, 0, V.shape[1] - 1)
        info["eval"] = "largest certified square"
    else:
        info["eval"] = "region square"
    edge = (ci0 == 0 or cj0 == 0 or ci0 + b >= V.shape[0] or cj0 + b >= V.shape[1]) if b > 0 else False
    row = dict(route=route, surface=name, utc=utc(), square_touches_crop_edge="yes" if edge else "no", cells_valid=int(V.sum()), grid="%dx%d" % V.shape,
               step_i_mm="%.6f" % si, step_j_mm="%.6f" % sj, eval_box=" ".join(map(str, box)),
               largest_certified_square_mm="%.4f" % (b * stepmm), largest_certified_square_cells=int(b),
               largest_certified_square_corner="%d %d" % (ci0, cj0),
               v2_cells=int(M["v2"].sum()), self_conflict_cells=int(M["self_conflict"].sum()),
               b_end_cells=int(M["b_end"].sum()) if "b_end" in M else NM, a2_rule_cells=int(M["a2_rule"].sum()))
    row.update(meta); row.update(info); row.update(vinfo)
    rg = roughness(P, V, box)
    row["roughness_native_median_deg"], row["roughness_native_p90_deg"] = rg
    nsub = max(1, int(round(20.0 / h)))
    Ps, Vs = P[::nsub, ::nsub], V[::nsub, ::nsub]
    bs = (box[0] // nsub, box[1] // nsub, box[2] // nsub, box[3] // nsub)
    row["roughness_20vox_median_deg"], row["roughness_20vox_p90_deg"] = roughness(Ps, Vs, bs)
    row["roughness_20vox_every_n"] = nsub
    row.update(angles(P, V, box))
    if VAL is None:
        row.update(fibre=NM, fibre_iqr=NM, fibre_tiles=0, window="not measurable: raw values not sampled")
    else:
        f, iq, na, nt = tiles_fibre(VAL, V & ~flagged, box, si, sj)
        row.update(fibre=f, fibre_iqr=iq, fibre_tiles=na, fibre_tiles_total=nt)
        row.update(best_window(V, flagged, VAL, si, sj))
        p = ART + "/%s-%s-texture.png" % (name, route)
        png(VAL, V, flagged, box, "%s %s h %.4f mm" % (route, name, stepmm), p, stepmm)
        row["png"] = p
        np.savez_compressed(HERE + "/scratch/values-%s-%s.npz" % (route, name), VAL=VAL.astype(np.float32), V=V, flagged=flagged)
    row["seconds"] = round(time.time() - t0, 1)
    json.dump(row, open(out + ".part", "w"), indent=1, default=str); os.replace(out + ".part", out)
    print(json.dumps(row, default=str))


COLS = ["route", "surface", "utc", "label", "region_what", "grid", "cells_valid", "step_i_mm", "step_j_mm", "eval", "eval_box",
        "fibre", "fibre_iqr", "fibre_tiles", "fibre_tiles_total",
        "roughness_native_median_deg", "roughness_native_p90_deg", "roughness_20vox_median_deg", "roughness_20vox_p90_deg",
        "roughness_20vox_every_n",
        "angle_i_to_z_3d_median", "angle_i_to_z_3d_iqr", "angle_i_to_z_inplane_median", "angle_i_to_z_inplane_iqr",
        "angle_j_to_z_3d_median", "angle_j_to_z_3d_iqr", "angle_j_to_z_inplane_median", "angle_j_to_z_inplane_iqr",
        "rotation_inplane_median", "rotation_inplane_iqr",
        "largest_certified_square_mm", "largest_certified_square_cells", "square_touches_crop_edge", "largest_certified_square_corner",
        "window", "window_i0", "window_j0", "window_cells", "window_covered", "window_flagged", "window_fibre", "window_tiles",
        "window_attempts", "window_candidates",
        "v2_cells", "self_conflict_cells", "b_end_cells", "a2_rule_cells", "a2_measurable", "a2_flagged", "partners",
        "regrid_fold_share", "regrid_resid_median_vox", "regrid_resid_p95_vox", "regrid_r_med_vox", "regrid_theta_span_deg",
        "w016_balanced_accuracy", "chunks_needed", "chunks_to_fetch", "fetch_gb", "fetch", "png", "seconds"]


def cmd_combine():
    R = []
    reg = {r["label"]: r for r in rows(HERE + "/evidence/regrid.csv")} if os.path.isfile(HERE + "/evidence/regrid.csv") else {}
    rot = {(r["route"], r["surface"]): r for r in rows(HERE + "/evidence/rotation.csv")} if os.path.isfile(HERE + "/evidence/rotation.csv") else {}
    for f in sorted(glob.glob(ROWS + "/*.json")):
        j = json.load(open(f))
        ro = rot.get((j["route"], j["surface"]), {})
        j["rotation_inplane_median"] = ro.get("rotation_inplane_median", "not run yet")
        j["rotation_inplane_iqr"] = ro.get("rotation_inplane_iqr", "not run yet")
        g = reg.get("%s-%s" % (j["route"], j["surface"]))
        for k in ("fold_share", "resid_median_vox", "resid_p95_vox", "r_med_vox", "theta_span_deg"):
            j["regrid_" + k] = g[k] if g else "not applicable: not regridded"
        j.setdefault("w016_balanced_accuracy", "not applicable: no labels on PHerc0826")
        R.append([j.get(c, "") for c in COLS])
    extra = HERE + "/scratch/w016-rows.csv"
    if os.path.isfile(extra):
        for r in rows(extra):
            R.append([r.get(c, "") for c in COLS])
    with open(HERE + "/evidence/routes.csv.part", "w", newline="") as f:
        f.write("# written by %s combine at %s: one row per route x surface (DECLARATION.md). L = our lattice as delivered, R1 = "
                "height field r(theta, z) spline with 0.5 mm knots regridded to v = z, u = arc length at constant z, R2native = the "
                "organisers' tracer on its own grid (bilinear to 4 voxels), R2regrid = the same regridded (fit none). fibre = median "
                "fibre.py wscore over accepted 128 cell tiles of the eval box; roughness = angle between neighbouring unit normals "
                "(native grid and every n cells, about 20 voxels); regrid_* = the row's regrid_z.py run (evidence/regrid.csv: fold_share, the model residual |r_model - r| at the input nodes, median radius and theta span about the published umbilicus); angle_*_to_z_3d = arccos(|dz|/|d|) (best-windows' definition, "
                "holds the sheet's inclination), *_inplane = against z projected on the tangent plane; certified square and window "
                "on the row's own grid with cert.py's checks recomputed (L: certified-piece-0826 masks)\n" % (TOOL, utc()))
        w = csv.writer(f, lineterminator="\n"); w.writerow(COLS); w.writerows(R)
    os.replace(HERE + "/evidence/routes.csv.part", HERE + "/evidence/routes.csv")
    print("rows", len(R))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "r1":
        cmd_r1(a[1])
    elif a[0] == "measure":
        cmd_measure(a[1], a[2])
    elif a[0] == "combine":
        cmd_combine()
    elif a[0] == "regions":
        for k, v in regions().items():
            print(k, v)
