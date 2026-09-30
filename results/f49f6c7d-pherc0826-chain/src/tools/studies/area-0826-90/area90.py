#!/usr/bin/env python3
"""area-0826-90/tools/area90.py: unique clean area of the delivered PHerc0826 sheets and their stitching (PLAN item 90).

Declared in ../DECLARATION.md before any number. House functions are imported unchanged:
  certified_region.lattice_from_patch (reader), union_area.local_area / union_of (cell area, bin-max union),
  sheet_cross.working / keys_of / dilate_keys / components and sheet_cross_v2.pair_v2 / marks (v2 crossing lines),
  map_crossing / detect / cluster_rule (arm a2, the calls of a2_after.a2_measure), square.py (steps, squares),
  pipeline/tools/traced_area.py (the traced area reference).

    area90.py selftest                 synthetic cases -> evidence/selftest.csv (every other mode runs it first, unwritten)
    area90.py traced <seed>            traced area reference of one seed -> scratch/traced/<seed>.json
    area90.py prep <seed> <k>          sheet: sha check, a2 flags (reference against a2-cluster), working lattice
    area90.py map <seed> <k>           v2 map of one sheet against its candidate partners, coinciding cells, |d| histogram
    area90.py coinref                  coinciding cells here against sheet_cross.pair on 20 ordered pairs
    area90.py combine                  union (three rules), pieces, pitch, stitching -> evidence/*.csv
    area90.py sheets                   print "<seed> <k>" for every sheet
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"
import csv, glob, hashlib, json, math, subprocess, sys, time

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

HOME = "/data/scrollagent"
R1 = HOME + "/runs/rev1"
STUDY = R1 + "/area-0826-90"
EV = STUDY + "/evidence"
SCR = STUDY + "/scratch"
CHAIN = R1 + "/chain-0826"
TOOL = "area-0826-90/tools/area90.py"
SCROLL = "PHerc0826"
NM = "not measurable"

sys.path.insert(0, R1 + "/certified-area/tools")
sys.path.insert(0, R1 + "/coverage-union-1447/tools")
sys.path.insert(0, R1 + "/sheet-crossing-map-1447/tools")
sys.path.insert(0, R1 + "/lamina-crossing-map-1447/tools")
sys.path.insert(0, HOME + "/pipeline/tools")
sys.path.insert(0, HOME + "/pipeline/datasets")
import certified_region as CR  # noqa: E402
import union_area as UA  # noqa: E402
import sheet_cross as S  # noqa: E402
import sheet_cross_v2 as V2  # noqa: E402
import map_crossing as MC  # noqa: E402
import cluster_rule as CRL  # noqa: E402
import traced_area as TA  # noqa: E402
from voxel import voxel_um  # noqa: E402

D = MC.D
SQ = UA.SQ
MC.SCROLL = SCROLL                       # as chain-0826/tools/a2_cluster_seed.py use_scroll does
MC.SAS = CHAIN
VOX_UM = voxel_um(SCROLL)[0]
MM = VOX_UM * 1e-3
UA.VOX_UM = VOX_UM                       # union_area.local_area reads its module MM: the PHerc0826 voxel
UA.MM = MM
UA.SCROLL = SCROLL


def utc():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()


def read_rows(path):
    return UA.read_rows(path)


def write_csv(path, comment, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".part", "w", newline="") as fh:
        fh.write('"# written by %s at %s: %s"\n' % (TOOL, utc(), comment.replace('"', "'")))
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] if isinstance(r, dict) else r[i] for i, c in enumerate(cols)])
    os.replace(path + ".part", path)


def check_voxel():
    rows = [r for r in read_rows(R1 + "/ink-input-form/evidence/catalog-orientation.csv") if r["scroll"] == SCROLL]
    vals = {float(r["pixel_size_um"]) for r in rows}
    if vals != {VOX_UM}:
        raise SystemExit("REFUSED: voxel.py %s against catalogue %s" % (VOX_UM, vals))
    return VOX_UM


# ------------------------------------------------------------------------------------------ inputs
def seeds():
    out = []
    for r in read_rows(CHAIN + "/evidence/per-seed-queue.csv"):
        try:
            float(r["traced_area_mm2"])
        except ValueError:
            continue
        out.append((r["attempt"], int(r["delivered_sheets"]), float(r["traced_area_mm2"])))
    return out


def seeds_frozen():
    """the seeds of the union run: those with a traced reference json (80, written 15:30Z); addition of 2026-09-27"""
    return [x for x in seeds() if os.path.isfile(SCR + "/traced/%s.json" % x[0])]


def sheets():
    return [(a, k) for a, n, _ in seeds_frozen() for k in range(n)]


def label(a, k):
    return "%s-S%d" % (a, k)


def patch(a, k):
    return "%s/out/%s/C40/patch_%d.bin" % (CHAIN, a, k)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------ core functions
def dup_flags(Ps, earlier, rs):
    """Ps (n, 3) voxels; earlier: list of (m, 3) arrays; rs: radii. A cell of Ps is a duplicate under radius r when a
    cell of any earlier array lies within r (<=) in 3D. Returns one bool array per radius."""
    out = [np.zeros(len(Ps), bool) for _ in rs]
    if len(Ps) == 0:
        return out
    rmax = max(rs)
    lo, hi = Ps.min(0) - rmax, Ps.max(0) + rmax
    near = [Pt[np.all((Pt >= lo) & (Pt <= hi), 1)] for Pt in earlier if len(Pt)]
    near = [q for q in near if len(q)]
    if not near:
        return out
    tree = cKDTree(np.concatenate(near).astype(np.float64))
    d, _ = tree.query(Ps.astype(np.float64), k=1, distance_upper_bound=rmax * (1 + 1e-9))
    for o, r in zip(out, rs):
        o[d <= r] = True
    return out


def nearest_block(shape, stride, gshape):
    """For every lattice cell, the index of its nearest stride point: rint(i / stride), clipped to the grid."""
    gi = np.clip(np.rint(np.arange(shape[0]) / stride).astype(np.int64), 0, gshape[0] - 1)
    gj = np.clip(np.rint(np.arange(shape[1]) / stride).astype(np.int64), 0, gshape[1] - 1)
    return gi, gj


def block_mask(flag_grid, shape, stride):
    gi, gj = nearest_block(shape, stride, flag_grid.shape)
    return flag_grid[gi[:, None], gj[None, :]]


def largest_piece(mask, area):
    """Largest 4 neighbour component of mask: (cells, area sum)."""
    if not mask.any():
        return 0, 0.0
    lab, n = ndimage.label(mask)
    cnt = np.bincount(lab.ravel(), minlength=n + 1); cnt[0] = 0
    ar = np.bincount(lab.ravel(), weights=np.where(mask, np.nan_to_num(area), 0.0).ravel(), minlength=n + 1); ar[0] = 0
    b = int(np.argmax(ar))
    return int(cnt[b]), float(ar[b])


def coin_from(A, B, r):
    """sheet_cross.pair's coinciding cells, computed from pair_v2's arrays with pair's own lines."""
    D_, BI, BJ, O, DS = r["D"], r["BI"], r["BJ"], r["O"], r["DS"]
    FOOT = np.isfinite(D_)
    sh = FOOT.shape
    DOT = np.zeros(sh)
    ai, aj = np.nonzero(FOOT)
    DOT[ai, aj] = (A["N"][ai, aj].astype(np.float64) * B["N"][BI[ai, aj], BJ[ai, aj]].astype(np.float64)).sum(1)
    c = 2 + math.ceil(max(A["si"], A["sj"]) / min(B["si"], B["sj"]))
    e0 = FOOT[:-1] & FOOT[1:] & (np.abs(BI[:-1] - BI[1:]) <= c) & (np.abs(BJ[:-1] - BJ[1:]) <= c)
    e1 = FOOT[:, :-1] & FOOT[:, 1:] & (np.abs(BI[:, :-1] - BI[:, 1:]) <= c) & (np.abs(BJ[:, :-1] - BJ[:, 1:]) <= c)
    absds = np.where(O, np.abs(np.nan_to_num(DS)), np.inf)
    C = O & (absds <= S.D_CO) & (np.abs(DOT) >= S.COS_CO)
    COIN = np.zeros(sh, bool)
    cell = A["si"] * A["sj"]
    if C.any():
        nc, lab = S.components(C, e0, e1)
        cnt = np.bincount(lab[C], minlength=nc)
        big = np.flatnonzero(cnt * cell >= S.A_CO)
        if len(big):
            COIN = C & np.isin(lab, big)
    return COIN, cell


# ------------------------------------------------------------------------------------------ self test
def selftest(write=False):
    rows, ok_all = [], True

    def check(case, q, exp, got, ok):
        nonlocal ok_all
        rows.append([case, q, exp, got, "yes" if ok else "no"]); ok_all &= bool(ok)

    os.makedirs(SCR, exist_ok=True)
    tmp = SCR + "/selftest_patch_%d.bin" % os.getpid()
    A = UA.as_sheet(UA.plane(100, 100), via_file=tmp)
    try:
        os.remove(tmp)
    except OSError:
        pass
    ea = float(A[1].sum())
    step = 4.0
    rs = [0.5 * step, 1.0 * step]

    def rules(parts):
        """parts: list of (P, a). Returns half, one, binmax areas."""
        tot = [0.0, 0.0]
        for n, (P, a) in enumerate(parts):
            fl = dup_flags(P, [q[0] for q in parts[:n]], rs)
            for x in range(2):
                tot[x] += float(a[~fl[x]].sum())
        u, _, _, _ = UA.union_of(parts)
        return tot[0], tot[1], u

    def rel(x, y):
        return abs(x - y) / y

    h, o, u = rules([A[:2]])
    check("s1", "one sheet: half, one, bin-max equal its area", "%.9f" % ea, "%.9f %.9f %.9f" % (h, o, u),
          max(rel(h, ea), rel(o, ea), rel(u, ea)) <= 1e-6)
    h, o, u = rules([A[:2], A[:2]])
    check("s2", "two identical copies count once", "%.9f" % ea, "%.9f %.9f %.9f" % (h, o, u),
          max(rel(h, ea), rel(o, ea), rel(u, ea)) <= 1e-6)
    B = UA.as_sheet(UA.plane(100, 100, normal_shift=0.6 * step))
    h, o, u = rules([A[:2], B[:2]])
    check("s3", "copy 0.6 step along the normal: half twice, one once", "%.9f; %.9f" % (2 * ea, ea),
          "%.9f; %.9f" % (h, o), rel(h, 2 * ea) <= 1e-6 and rel(o, ea) <= 1e-6)
    B = UA.as_sheet(UA.plane(100, 100, normal_shift=1.2 * step))
    h, o, u = rules([A[:2], B[:2]])
    check("s4", "copy 1.2 steps along the normal: half and one twice", "%.9f" % (2 * ea), "%.9f %.9f" % (h, o),
          rel(h, 2 * ea) <= 1e-6 and rel(o, 2 * ea) <= 1e-6)
    B = UA.as_sheet(UA.plane(100, 100, normal_shift=14.0))
    h, o, u = rules([A[:2], B[:2]])
    check("s5", "copy 14 voxels away: every rule twice", "%.9f" % (2 * ea), "%.9f %.9f %.9f" % (h, o, u),
          max(rel(h, 2 * ea), rel(o, 2 * ea), rel(u, 2 * ea)) <= 1e-6)
    B = UA.as_sheet(UA.plane(100, 100, j0=50))
    h, o, u = rules([A[:2], B[:2]])
    ec = 1.5 * ea
    check("s6", "half overlap: every rule within [0.98, 1.0] of 1.5 areas", "%.9f" % ec, "%.9f %.9f %.9f" % (h, o, u),
          all(0.98 * ec <= x <= ec * (1 + 1e-6) for x in (h, o, u)))
    check("s6", "direction: half >= one", "yes", "yes" if h >= o - 1e-9 else "no", h >= o - 1e-9)
    g = np.zeros((3, 4), bool); g[1, 2] = True
    m = block_mask(g, (20, 30), 8)
    exp = np.zeros((20, 30), bool)
    for i in range(20):
        for j in range(30):
            gi, gj = min(int(np.rint(i / 8)), 2), min(int(np.rint(j / 8)), 3)
            exp[i, j] = g[gi, gj]
    check("s7", "a2 block rule: cells nearest the flagged stride point (8, 16)", int(exp.sum()), int(m.sum()),
          bool((m == exp).all()) and m[8, 16] and not m[0, 0] and m[5, 13] and not m[4, 12])
    mk = np.ones((10, 10), bool); mk[:, 4] = False
    c, a = largest_piece(mk, np.ones((10, 10)))
    check("s8", "connected piece split by a removed column (pieces of 40 and 50 cells)", "50 cells", "%d cells" % c,
          c == 50 and a == 50.0)
    if os.environ.get("SA_SELFTEST_BREAK") == "1":
        check("break", "planted failure", "yes", "no", False)
    if write:
        write_csv(EV + "/selftest.csv", "synthetic tilted planes at step 4 voxels through the patch file format "
                  "(DECLARATION.md, Self test); voxel %s um; union_area.py plane/as_sheet/union_of imported" % VOX_UM,
                  ["case", "quantity", "expected", "got", "passed"], rows + [["all", "every case", "yes",
                                                                           "yes" if ok_all else "no",
                                                                           "yes" if ok_all else "no"]])
    return ok_all, rows


def require_selftest():
    ok, rows = selftest(False)
    if not ok:
        for r in rows:
            if r[-1] != "yes":
                print("SELF TEST FAILED:", r, file=sys.stderr)
        raise SystemExit("REFUSED: self test failed")


# ------------------------------------------------------------------------------------------ traced reference
def traced(seed):
    run = "%s/out/%s/sheets" % (CHAIN, seed)
    files = TA.patch_files(run)
    pts = sum(os.path.getsize(f) for f in files) // TA.POINT.itemsize
    sp = TA.spacing(files)
    n = TA.union_cells(files, sp)
    mm2 = round(n * sp * sp * MM * MM, 1)
    ref = {r["quantity"]: r["value"] for r in read_rows("%s/evidence/area-%s.csv" % (CHAIN, seed))}
    d = dict(seed=seed, files=len(files), points=pts, spacing=round(sp, 4), traced_area_mm2=mm2,
             area_csv_traced_area_mm2=ref["traced_area_mm2"], area_csv_points=ref["points"],
             equal="yes" if ("%.1f" % mm2 == ref["traced_area_mm2"] and str(pts) == ref["points"]) else "no")
    os.makedirs(SCR + "/traced", exist_ok=True)
    json.dump(d, open(SCR + "/traced/%s.json" % seed, "w"))
    print(d, flush=True)


# ------------------------------------------------------------------------------------------ prep
_VOL = {}


def a2_grid(px, py, pz, valid, T):
    """The calls of a2_after.a2_measure, in its order, keeping the flag grid."""
    if "v" not in _VOL:
        _VOL["v"] = D.PredVol(MC.SCROLL, cap=64)
    vol = _VOL["v"]
    ii, jj = MC.eval_points(valid)
    C = vol.ch
    key = (np.rint(pz[ii, jj]).astype(np.int64) // C) * 10 ** 8 + (np.rint(py[ii, jj]).astype(np.int64) // C) * 10 ** 4 \
        + (np.rint(px[ii, jj]).astype(np.int64) // C)
    order = np.argsort(key, kind="stable")
    gi, gj = (valid.shape[0] + MC.STRIDE - 1) // MC.STRIDE, (valid.shape[1] + MC.STRIDE - 1) // MC.STRIDE
    gflag = np.zeros((gi, gj), bool)
    meas = fl = 0
    for i, j in zip(ii[order], jj[order]):
        ns = D.surface_normal(px, py, pz, valid, i, j)
        if ns is None:
            continue
        nt, _, st = D.tensor_normal(vol, float(px[i, j]), float(py[i, j]), float(pz[i, j]), "pred")
        if nt is None:
            continue
        meas += 1
        if D.angle_deg(ns, nt) > T:
            fl += 1; gflag[i // MC.STRIDE, j // MC.STRIDE] = True
    return gflag, meas, fl


def prep(a, k):
    L = label(a, k)
    done = SCR + "/sheets/%s.json" % L
    if os.path.isfile(done):
        return
    check_voxel()
    p = patch(a, k)
    h = sha(p)
    sq = {int(r["sheet"]): r for r in read_rows("%s/evidence/squares-%s.csv" % (CHAIN, a))}
    if sq[k]["sha256"] != h:
        raise SystemExit("REFUSED: %s sha256 differs from its squares row" % L)
    ref = {int(r["sheet"]): r for r in read_rows("%s/evidence/a2-cluster/%s.csv" % (CHAIN, a))}[k]
    if ref["sha256"] != h:
        raise SystemExit("REFUSED: %s sha256 differs from its a2-cluster row" % L)
    D.selftest_passed(); MC.selftest_ok()
    T, _ = MC.verdict_row("a2")
    Sd, _ = CRL.read_S(); Sv = Sd["a2"]
    if float(ref["a2_T_star"]) != float(T) or int(ref["a2_S"]) != int(Sv):
        raise SystemExit("REFUSED: %s T* or S differ from the a2-cluster row" % L)
    px, py, pz, valid, coll = CR.lattice_from_patch(p)
    t0 = time.time()
    gflag, meas, fl = a2_grid(px, py, pz, valid, T)
    gsize, _ = CRL.clusters(gflag)
    hS, kept = CRL.rule_holes(gsize, Sv, valid)
    ta2 = time.time() - t0
    a2cell = (block_mask(gflag, valid.shape, MC.STRIDE) | hS) & valid
    ref_ok = (str(meas) == ref["a2_measurable"] and str(fl) == ref["a2_flagged"]
              and str(int(kept.sum())) == ref["a2_kept_points"])
    W = S.working(px, py, pz, valid, SCROLL, L)
    os.makedirs(SCR + "/work", exist_ok=True); os.makedirs(SCR + "/a2", exist_ok=True)
    np.savez_compressed(SCR + "/work/%s.tmp.npz" % L, P=W["P"], N=W["N"], ok=W["ok"], inter=W["inter"], si=W["si"], sj=W["sj"],
             s=W["s"])
    os.replace(SCR + "/work/%s.tmp.npz" % L, SCR + "/work/%s.npz" % L)
    np.savez_compressed(SCR + "/a2/%s.tmp.npz" % L, a2cell=a2cell, gflag=gflag, holes=hS)
    os.replace(SCR + "/a2/%s.tmp.npz" % L, SCR + "/a2/%s.npz" % L)
    ukeys = np.unique(S.keys_of(W["P"][W["ok"]].astype(np.float64)))
    np.save(SCR + "/work/%s.keys.npy" % L, ukeys)
    info = dict(label=L, attempt=a, sheet=k, sha256=h, cells=int(valid.sum()), lattice_collisions=coll,
                a2_measurable=meas, a2_flagged=fl, a2_kept_points=int(kept.sum()),
                ref_a2_measurable=ref["a2_measurable"], ref_a2_flagged=ref["a2_flagged"],
                ref_a2_kept_points=ref["a2_kept_points"], a2_equal="yes" if ref_ok else "no",
                a2_cells=int(a2cell.sum()), a2_block_cells=int((block_mask(gflag, valid.shape, MC.STRIDE) & valid).sum()),
                a2_hole_cells=int(hS.sum()), working_stride=int(W["s"]), a2_seconds=round(ta2, 1))
    os.makedirs(SCR + "/sheets", exist_ok=True)
    json.dump(info, open(done + ".part", "w")); os.replace(done + ".part", done)
    print("prep %s: cells %d, a2 %d/%d (ref %s/%s) %s, a2 cells %d, stride %d, %.0f s" % (
        L, info["cells"], fl, meas, ref["a2_flagged"], ref["a2_measurable"], info["a2_equal"], info["a2_cells"],
        W["s"], ta2), flush=True)
    if not ref_ok:
        raise SystemExit("REFUSED: %s a2 differs from chain-0826/evidence/a2-cluster" % L)


# ------------------------------------------------------------------------------------------ map
def load_work(L):
    z = np.load(SCR + "/work/%s.npz" % L)
    return dict(P=z["P"], N=z["N"], ok=z["ok"], inter=z["inter"], si=float(z["si"]), sj=float(z["sj"]), s=int(z["s"]),
                scroll=SCROLL, label=L, vox=VOX_UM)


def thresholds():
    out, fac = {}, {}
    for r in read_rows(R1 + "/sheet-crossing-map-1447/evidence/v2-thresholds.csv"):
        sc = r["set_by_pair"].split("|")[0]
        f = voxel_um(sc)[0] / VOX_UM
        out[r["threshold"]] = float(r["voxels"]) * f
        fac[r["threshold"]] = (sc, f)
    rows = {r["test"]: r for r in read_rows(R1 + "/sheet-crossing-map-1447/evidence/calibration-v2-verdict.csv")}
    if rows["bar"]["passed"] != "yes":
        raise SystemExit("REFUSED: v2 calibration not passed")
    return out["L2_cross"], out["L2_jump"], fac


_IDX = {}


def index():
    if "k" not in _IDX:
        idx = {}
        for a, k in sheets():
            L = label(a, k)
            for q in np.load(SCR + "/work/%s.keys.npy" % L):
                idx.setdefault(int(q), []).append(L)
        _IDX["k"] = idx
    return _IDX["k"]


def candidates(L):
    ks = np.load(SCR + "/work/%s.keys.npy" % L)
    idx = index()
    got = set()
    for q in S.dilate_keys(ks):
        for M in idx.get(int(q), ()):
            got.add(M)
    got.discard(L)
    return sorted(got)


HBINS = np.arange(0.0, 24.25, 0.25)
MAP_COLS = ["sheet", "partner", "overlap_cells", "v2_crossing_cells", "v2_jump_cells", "longest_consistent_cross_vox",
            "longest_jump_vox", "coinciding_cells", "coinciding_vox2", "coinciding_median_abs_ds_vox", "foot_cells"]


def map_one(a, k):
    L = label(a, k)
    out = EV + "/v2/%s.csv" % L
    if os.path.isfile(out):
        return
    L2c, L2j, fac = thresholds()
    A = load_work(L)
    cand = candidates(L)
    sh = A["ok"].shape
    CROSS = np.zeros(sh, bool); JUMP = np.zeros(sh, bool)
    hist = np.zeros(len(HBINS) - 1)
    rows = []
    for M in cand:
        B = load_work(M)
        r = V2.pair_v2(A, B)
        if r is None:
            rows.append([L, M, 0, 0, 0, "0.000", "0.000", 0, "0.0", NM, 0])
            continue
        c_, j_ = V2.marks(r, L2c, L2j)
        CROSS |= c_; JUMP |= j_
        COIN, cell = coin_from(A, B, r)
        fin = np.isfinite(r["D"])
        hist += np.histogram(np.abs(r["D"][fin]), bins=HBINS)[0]
        med = "%.3f" % float(np.median(np.abs(r["DS"][COIN]))) if COIN.any() else NM
        rows.append([L, M, r["n_overlap"], int(c_.sum()), int(j_.sum()), "%.3f" % V2.longest(r, "cross"),
                     "%.3f" % V2.longest(r, "jump"), int(COIN.sum()), "%.1f" % (COIN.sum() * cell), med, int(fin.sum())])
    os.makedirs(SCR + "/v2", exist_ok=True)
    np.savez_compressed(SCR + "/v2/%s.tmp.npz" % L, crossed=CROSS, jumped=JUMP, stride=A["s"], hist=hist)
    os.replace(SCR + "/v2/%s.tmp.npz" % L, SCR + "/v2/%s.npz" % L)
    write_csv(out, "one PHerc0826 sheet against every candidate partner (64 voxel bin keys meeting its dilated keys), v2 "
              "lines of sheet_cross_v2.pair_v2 and marks with L2_cross %.3f, L2_jump %.3f voxels (factor %s), coinciding "
              "cells by sheet_cross.pair's rule (coin_from); all partners %d" % (L2c, L2j, fac, len(cand)), MAP_COLS, rows)
    print("map %s: %d partners, crossed %d, jumped %d, coinciding partners %d" % (
        L, len(cand), CROSS.sum(), JUMP.sum(), sum(1 for r in rows if r[7] > 0)), flush=True)


def coinref():
    require_selftest()
    got, n = [], 0
    for a, k in sheets():
        L = label(a, k)
        for r in read_rows(EV + "/v2/%s.csv" % L):
            if int(r["overlap_cells"]) > 0 and (int(r["coinciding_cells"]) > 0 or n % 3 == 0):
                got.append((L, r["partner"], int(r["coinciding_cells"])))
            n += 1
            if len(got) >= 20:
                break
        if len(got) >= 20:
            break
    rows, bad = [], 0
    for L, M, mine in got:
        A, B = load_work(L), load_work(M)
        r = S.pair(A, B)
        ref = 0 if r is None else r["n_coin"]
        rows.append([L, M, mine, ref, "yes" if mine == ref else "no"])
        bad += mine != ref
    write_csv(EV + "/coin-reference.csv", "coinciding cells of coin_from (this tool, from pair_v2's arrays) against "
              "sheet_cross.pair's n_coin on 20 ordered pairs with overlap, the first found in sheet order",
              ["sheet", "partner", "coinciding_cells_here", "sheet_cross_pair_n_coin", "equal"], rows)
    print("coin reference: %d of %d equal" % (len(rows) - bad, len(rows)))
    if bad:
        raise SystemExit("REFUSED: coinciding cells differ from sheet_cross.pair")


# ------------------------------------------------------------------------------------------ combine
def load_sheet(args):
    a, k = args
    L = label(a, k)
    px, py, pz, valid, _ = CR.lattice_from_patch(patch(a, k))
    area, fb = UA.local_area(px, py, pz, valid)
    si, _ = SQ.median_step(valid, px, py, pz, 0)
    sj, _ = SQ.median_step(valid, px, py, pz, 1)
    a2 = np.load(SCR + "/a2/%s.npz" % L)["a2cell"]
    z = np.load(SCR + "/v2/%s.npz" % L)
    mark = z["crossed"] | z["jumped"]
    v2 = block_mask(mark, valid.shape, int(z["stride"])) & valid
    clean = valid & ~a2 & ~v2
    pc, pa = largest_piece(clean, area)
    s2, _, _ = SQ.largest_square(clean)
    s_all, _, _ = SQ.largest_square(valid)
    stp = min(si, sj)
    P = np.stack([px[clean], py[clean], pz[clean]], 1).astype(np.float32)
    info = dict(label=L, attempt=a, sheet=k, cells=int(valid.sum()), sum_a_mm2=float(area[valid].sum()),
                fallback_cells=fb, step_i_vox=si, step_j_vox=sj, a2_cells=int(a2.sum()), v2_cells=int(v2.sum()),
                both_cells=int((a2 & v2).sum()), clean_cells=int(clean.sum()), clean_mm2=float(area[clean].sum()),
                piece_cells=pc, piece_mm2=pa, square_clean_mm=s2 * stp * MM, square_all_mm=s_all * stp * MM,
                hist=z["hist"])
    return info, P, area[clean].astype(np.float64)


def gate():
    while glob.glob(R1 + "/*/scratch/CLOCK.lock"):
        print("paused: CLOCK.lock", flush=True); time.sleep(60)
    st = os.statvfs("/data")
    if st.f_bavail * st.f_frsize < 50 * 2 ** 30:
        raise SystemExit("STOP: /data free under 50 GB")


G = {}


def dedup_task(n):
    """Duplicates of sheet n against the earlier sheets in G['earlier'][n] (indices)."""
    L, Ps, st = G["labels"][n], G["P"][n], G["step"][n]
    fl = dup_flags(Ps, [G["P"][m] for m in G["earlier"][n]], [0.5 * st, 1.0 * st])
    return n, fl[0], fl[1]


def run_dedup(order, earlier, procs=6):
    import multiprocessing as mp
    G["earlier"] = earlier
    res = {}
    with mp.get_context("fork").Pool(procs) as pool:
        for n, h, o in pool.imap_unordered(dedup_task, order, chunksize=1):
            res[n] = (h, o)
    return res


def main_combine():
    import multiprocessing as mp
    require_selftest()
    check_voxel()
    SL = sheets()
    labels = [label(a, k) for a, k in SL]
    pos = {L: i for i, L in enumerate(labels)}
    seed_of = {label(a, k): a for a, k in SL}
    for L in labels:
        for f in (SCR + "/sheets/%s.json" % L, SCR + "/v2/%s.npz" % L, EV + "/v2/%s.csv" % L):
            if not os.path.isfile(f):
                raise SystemExit("REFUSED: %s missing" % f)
    t0 = time.time()
    with mp.get_context("fork").Pool(6) as pool:
        got = pool.map(load_sheet, SL, chunksize=4)
    infos = [g[0] for g in got]; G["P"] = [g[1] for g in got]; AR = [g[2] for g in got]
    del got
    G["labels"] = labels
    G["step"] = [min(i["step_i_vox"], i["step_j_vox"]) for i in infos]
    print("loaded %d sheets in %.0f s" % (len(infos), time.time() - t0), flush=True)
    # partners from the map CSVs
    part = {L: [r["partner"] for r in read_rows(EV + "/v2/%s.csv" % L)] for L in labels}
    earlier = {pos[L]: sorted(pos[M] for M in part[L] if pos[M] < pos[L]) for L in labels}
    t0 = time.time()
    res = run_dedup(list(range(len(labels))), earlier)
    print("dedup in %.0f s" % (time.time() - t0), flush=True)
    half = sum(float(AR[n][~res[n][0]].sum()) for n in res)
    one = sum(float(AR[n][~res[n][1]].sum()) for n in res)
    sheets_pa = list(zip(G["P"], AR))
    binmax, clean_sum, bins, _ = UA.union_of(sheets_pa)
    binmax_shift, _, _, _ = UA.union_of(sheets_pa, UA.BIN, UA.BIN / 2)
    binmax8, _, _, _ = UA.union_of(sheets_pa, 2 * UA.BIN, 0.0)
    # the same bin-max on every covered cell (no a2, no v2 removal), beside
    total_sum = sum(i["sum_a_mm2"] for i in infos)
    # pitch
    hist = np.sum([i["hist"] for i in infos], 0)
    mids = 0.5 * (HBINS[:-1] + HBINS[1:])
    win = (mids > 6.0) & (mids <= 24.0)
    pitch = float(mids[win][np.argmax(hist[win])])
    zero_peak = float(mids[np.argmax(hist)])
    write_csv(EV + "/pitch.csv", "summed histogram of |d| (pair_v2 D on foot cells, radius 24 voxels) over every ordered "
              "pair of the v2 map; pitch = bin centre of the maximum between 6 and 24 voxels; voxel %s um" % VOX_UM,
              ["bin_lo_vox", "bin_hi_vox", "foot_cells"],
              [["%.2f" % HBINS[i], "%.2f" % HBINS[i + 1], int(hist[i])] for i in range(len(hist))]
              + [["pitch_vox", "%.3f" % pitch, "pitch_um %.1f" % (pitch * VOX_UM)],
                 ["global_max_vox", "%.3f" % zero_peak, ""],
                 ["coincide_under_half_pitch", "%.1f < %.3f" % (S.D_CO, pitch / 2), "yes" if S.D_CO < pitch / 2 else "no"]])
    # per sheet
    per = []
    for n, i in enumerate(infos):
        per.append(dict(i, dup_half_cells=int(res[n][0].sum()), dup_one_cells=int(res[n][1].sum()),
                        kept_half_mm2=float(AR[n][~res[n][0]].sum()), kept_one_mm2=float(AR[n][~res[n][1]].sum())))
    pcols = ["label", "cells", "sum_a_mm2", "fallback_cells", "step_i_vox", "step_j_vox", "a2_cells", "v2_cells",
             "both_cells", "clean_cells", "clean_mm2", "dup_half_cells", "dup_one_cells", "kept_half_mm2", "kept_one_mm2",
             "piece_cells", "piece_mm2", "square_clean_mm", "square_all_mm"]
    write_csv(EV + "/per-sheet.csv", "one row per delivered PHerc0826 sheet in dedup order; areas in mm2 from "
              "union_area.local_area at %s um; clean = covered minus a2 flagged minus v2 crossing cells; dup_* = clean "
              "cells within 0.5 or 1.0 smaller median step of a clean cell of an earlier sheet; piece = largest 4 neighbour "
              "component of clean cells on the sheet's lattice; squares by square.py times the smaller step" % VOX_UM,
              pcols, [{c: (("%.6f" % r[c]) if isinstance(r[c], float) else r[c]) for c in pcols} for r in per])
    quote, snum, spage, ssha = UA.stevens()
    best = max(per, key=lambda r: r["piece_mm2"])
    rules = [("half-step", half), ("one-step", one), ("bin-max", binmax)]
    head = min(rules, key=lambda x: x[1])[0]
    urows = []
    for name, v in rules:
        urows.append([name, "yes" if name == head else "no", len(seeds()), len(labels),
                      "%.4f" % (v / 100), "%.4f" % (clean_sum / 100), "%.4f" % (total_sum / 100),
                      "%.4f" % (v / 100 / snum), "%.4f" % (binmax_shift / 100), "%.4f" % (binmax8 / 100),
                      best["label"], "%.4f" % (best["piece_mm2"] / 100), quote, "%g" % snum, spage])
    write_csv(EV + "/union.csv", "unique clean area of the delivered PHerc0826 sheets (DECLARATION.md): clean cells "
              "(covered, not a2 flagged, not on v2 crossing lines), deduplicated by three rules, the smallest is the "
              "headline; Stevens' number is his, on PHerc1667, a sum of ten flattened components, not deduplicated or "
              "cleaned by us. largest piece = one sheet's largest 4 neighbour clean component, no join across sheets",
              ["rule", "headline", "seeds", "sheets", "unique_clean_cm2", "clean_summed_cm2", "all_cells_summed_cm2",
               "over_stevens", "binmax_half_bin_shift_cm2", "binmax_8_voxel_cm2", "largest_piece_sheet",
               "largest_piece_cm2", "stevens_quote", "stevens_cm2", "stevens_page"], urows)
    print("union: half %.2f one %.2f binmax %.2f cm2; clean summed %.2f, all %.2f; piece %s %.3f cm2; pitch %.2f" % (
        half / 100, one / 100, binmax / 100, clean_sum / 100, total_sum / 100, best["label"], best["piece_mm2"] / 100,
        pitch), flush=True)
    if not S.D_CO < pitch / 2:
        print("pitch bar failed: stitching not run"); return
    stitch(labels, pos, seed_of, infos, AR, per, snum, pitch)


def comps(labels, edges):
    par = list(range(len(labels)))

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in edges:
        ra, rb = f(a), f(b)
        if ra != rb:
            par[max(ra, rb)] = min(ra, rb)
    C = {}
    for i in range(len(labels)):
        C.setdefault(f(i), []).append(i)
    return list(C.values())


def stitch(labels, pos, seed_of, infos, AR, per, snum, pitch):
    rows = {}
    for L in labels:
        for r in read_rows(EV + "/v2/%s.csv" % L):
            rows[(L, r["partner"])] = r
    edges_any, edges_diff, pairs = [], [], []
    for (L, M), r in rows.items():
        if pos[L] >= pos[M]:
            continue
        q = rows.get((M, L))
        if q is None:
            continue
        coin = int(r["coinciding_cells"]) > 0 and int(q["coinciding_cells"]) > 0
        marks = sum(int(x[c]) for x in (r, q) for c in ("v2_crossing_cells", "v2_jump_cells"))
        if coin and marks == 0:
            edges_any.append((pos[L], pos[M]))
            if seed_of[L] != seed_of[M]:
                edges_diff.append((pos[L], pos[M]))
        if coin:
            pairs.append((L, M, marks))
    out = []
    for variant, E in (("any two sheets", edges_any), ("different seeds only", edges_diff)):
        C = comps(labels, E)
        C.sort(key=lambda m: -sum(per[i]["clean_mm2"] for i in m))
        for rank, m in enumerate(C[:5]):
            ms = sorted(m)
            if len(ms) > 1:
                G["earlier"] = {n: [x for x in ms if x < n] for n in ms}
                res = run_dedup(ms, G["earlier"])
                half = sum(float(AR[n][~res[n][0]].sum()) for n in ms)
                one = sum(float(AR[n][~res[n][1]].sum()) for n in ms)
            else:
                half = one = float(AR[ms[0]].sum())
            bm, cs, _, _ = UA.union_of([(G["P"][n], AR[n]) for n in ms])
            v = min(half, one, bm)
            sqb = max(ms, key=lambda n: per[n]["square_clean_mm"])
            out.append([variant, rank + 1, len(ms), len({seed_of[labels[n]] for n in ms}), "%.4f" % (cs / 100),
                        "%.4f" % (half / 100), "%.4f" % (one / 100), "%.4f" % (bm / 100), "%.4f" % (v / 100),
                        "%.4f" % (v / 100 / snum), "%.4f" % per[sqb]["square_clean_mm"], labels[sqb],
                        len(E), "%.3f" % pitch, " ".join(labels[n] for n in ms[:60]) + (" ..." if len(ms) > 60 else "")])
            print("stitch %s #%d: %d sheets, clean unique %.2f cm2" % (variant, rank + 1, len(ms), v / 100), flush=True)
    write_csv(EV + "/stitch.csv", "stitched sheets: two sheets joined when coinciding cells (sheet_cross.pair's rule: "
              "smoothed |d| <= 3 voxels, normals within 20 degrees, connected area >= 16384 square voxels) exist in both "
              "orders and no counted v2 crossing or jump line in either order; components of that graph, the 5 largest "
              "by summed clean area per variant; clean unique = the smallest of the three dedup rules over the members; "
              "square = the largest member square on its clean cells (no square crosses a seam); no counted v2 line "
              "between joined sheets, never one lamina", ["variant", "rank", "sheets", "seeds", "clean_summed_cm2",
                                                          "half_step_cm2", "one_step_cm2", "binmax_cm2",
                                                          "clean_unique_cm2", "over_stevens", "square_mm",
                                                          "square_on_sheet", "edges_in_variant", "pitch_vox", "members"],
              out)
    write_csv(EV + "/stitch-pairs.csv", "every unordered pair with coinciding cells in both orders; marks = v2 crossing "
              "plus jump cells in both orders (a pair with marks is not joined)", ["sheet_a", "sheet_b", "v2_marks"],
              [list(p) for p in pairs])


def main():
    a = sys.argv[1:]
    if a[0] == "selftest":
        ok, _ = selftest(True); print("self test", "passed" if ok else "FAILED"); sys.exit(0 if ok else 1)
    if a[0] == "sheets":
        for x, k in sheets():
            print(x, k)
        return
    if a[0] == "seeds":
        for x, _, _ in seeds():
            print(x)
        return
    if a[0] == "traced":
        traced(a[1]); return
    require_selftest()
    gate()
    if a[0] == "prep":
        prep(a[1], int(a[2]))
    elif a[0] == "map":
        map_one(a[1], int(a[2]))
    elif a[0] == "coinref":
        coinref()
    elif a[0] == "combine":
        main_combine()


if __name__ == "__main__":
    main()
