#!/usr/bin/env python3
"""render-routes-0826/tools/adjudicate.py ROUTE NAME: the director's ADJUDICATION rule for crossings between traced surfaces
(2026-09-29T23:59:34Z; DECLARATION addition 00:01Z, verbatim there). For the row X = (ROUTE, NAME) and every other traced crop Y
from a different start:
  crossing cells: sheet_cross_v2.pair_v2 + marks (area90 thresholds), both ways (X against Y marks X, Y against X marks Y), as
                  cert_article.py;
  region of each side: its crossing cells of the pair (union of both ways, mapped onto that side) and its cells within S.R voxels
                  (3D) of the other side's crossing cells (the neighbourhood v2 searches);
  share: of each side's region nodes, the fraction within 3 voxels (3D) of a node of our 800 delivered sheets (full patch
         lattices of the area90 index candidates around the region);
  verdict: the larger share is kept, the smaller flagged; equal to 4 decimals flags both.
certified_adjudicated(X) = largest square of V & ~v2_800 & ~self_conflict (a end) & ~a2_rule & ~(X's crossing cells of the pairs
where X is flagged). Rows: evidence/square-checks-adjudicated.csv (one per R2 row), evidence/crossing-pairs.csv (one per crossing
pair, written by the row whose key sorts first), a private axial cut per pair through the centroid of X's crossing cells."""
import csv, fcntl, json, os, shutil, subprocess, sys, time
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
H = "/data/scrollagent/runs/rev1/render-routes-0826"
R1D = "/data/scrollagent/runs/rev1"
sys.path.insert(0, H + "/tools")
import routes as RT, regrid_z as R  # noqa: E402
A, S, V2, PT, DK = RT.A, RT.S, RT.V2, RT.PT, RT.DK
PT.CACHE = H + "/scratch/raw-chunks"
ART = "/data/scrollagent/outputs/artifacts/render-routes-0826"
route, name = sys.argv[1:3]
KEYX = (route, name)
starts = {}
for f in ("r2-starts.csv", "r2d-starts.csv"):
    for r in RT.rows(H + "/evidence/" + f):
        starts[r["start"]] = (r["x"], r["y"], r["z"])
old = [r for r in RT.rows(H + "/evidence/square-checks.csv") if r["route"] == route and r["surface"] == name][-1]
art_rows = [r for r in RT.rows(H + "/evidence/square-checks-article.csv") if r["route"] == route and r["surface"] == name]
j = json.load(open(H + "/scratch/rows/%s-%s.json" % (route, name)))
step = min(float(j["step_i_mm"]), float(j["step_j_mm"]))
L2c, L2j, _ = A.thresholds()


def utc():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()


def work(rt, nm):
    P, V = RT.surface(rt, nm)[:2]
    px, py, pz = [np.where(V, P[..., k], 0.0) for k in range(3)]
    W = S.working(px, py, pz, V, "PHerc0826", nm)
    gi, gj = A.nearest_block(V.shape, W["s"], W["ok"].shape)
    return P, V, W, gi, gj


def marks_full(Wa, Wb, gi, gj, V):
    r = V2.pair_v2(Wa, Wb)
    if r is None:
        return np.zeros(V.shape, bool)
    c_, j_ = V2.marks(r, L2c, L2j)
    return (c_ | j_)[gi[:, None], gj[None, :]] & V


_SHEETS = {}


def sheet_points(Q):
    """full patch nodes of our 800 delivered sheets around the points Q (area90 index candidates)."""
    ks = np.unique(S.keys_of(Q.astype(np.float64)))
    idx = A.index(); cand = set()
    for q in S.dilate_keys(ks):
        for M in idx.get(int(q), ()):
            cand.add(M)
    pts, labs = [], []
    lo, hi = Q.min(0) - 6, Q.max(0) + 6
    for M in sorted(cand):
        Wm = A.load_work(M)
        wp = Wm["P"][Wm["ok"]]
        if not np.all((wp >= lo) & (wp <= hi), 1).any():     # working grid (stride 2) nowhere near: the full lattice is not read
            continue
        if M not in _SHEETS:
            seed, k = M.rsplit("-S", 1)
            Pf, Vf = R.read_patch(RT.patch_of("C40-%s-S%s" % (seed, k)))
            _SHEETS[M] = Pf[Vf].astype(np.float32)
        pts.append(_SHEETS[M]); labs.append(M)
    return pts, labs


def share(Q):
    if len(Q) == 0:
        return float("nan"), ""
    pts, labs = sheet_points(Q)
    hit = np.zeros(len(Q), bool); best = ("", 0)
    for p, l in zip(pts, labs):
        lo, hi = Q.min(0) - 3, Q.max(0) + 3
        sel = np.all((p >= lo) & (p <= hi), 1)
        if not sel.any():
            continue
        d, _ = cKDTree(p[sel]).query(Q, distance_upper_bound=3.0)
        h = np.isfinite(d)
        hit |= h
        if h.sum() > best[1]:
            best = (l, int(h.sum()))
    return float(hit.mean()), best[0]


def cut(PX, VX, cx, PY, VY, png):
    zc = float(np.rint(cx[2])); HALF, MAG = 320, 2
    xs = np.arange(int(cx[0]) - HALF, int(cx[0]) + HALF + 1); ys = np.arange(int(cx[1]) - HALF, int(cx[1]) + HALF + 1)
    X, Y = np.meshgrid(xs, ys); Z = np.full(X.shape, zc)
    rec = np.zeros(X.size, PT.POINT); rec["px"], rec["py"], rec["pz"] = X.ravel(), Y.ravel(), Z.ravel()
    lk = open(H + "/scratch/cache.lock", "a"); fcntl.flock(lk, fcntl.LOCK_SH)
    need = DK.chunks_of(rec); todo = sorted(q for q in need if not PT.have(q))
    w_ = 0
    while shutil.disk_usage("/data").free - len(todo) * PT.NBYTES <= 35e9:
        if w_ >= 6 * 3600:
            raise SystemExit("fetch refused: disk")
        time.sleep(60); w_ += 60; todo = sorted(q for q in need if not PT.have(q))
    if todo:
        tally, got = DK.fetch(todo)
        open(H + "/scratch/fetched-adjudicate-%s-%s.txt" % (route, name), "a").writelines(g + "\n" for g in got)
    img = PT.Raw2().sample(X.ravel().astype(float), Y.ravel().astype(float), Z.ravel()).reshape(X.shape)
    fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
    g = img[np.isfinite(img) & (img > 0)]; lo, hi = np.percentile(g, [1, 99.5])
    gray = (np.clip((np.nan_to_num(img) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(np.stack([gray] * 3, -1)).resize((X.shape[1] * MAG, X.shape[0] * MAG), Image.NEAREST)
    cv = Image.new("RGB", (im.size[0], im.size[1] + 70), "white"); cv.paste(im, (0, 0)); dr = ImageDraw.Draw(cv)
    box = np.array([xs[0], ys[0], zc - 1.0]), np.array([xs[-1], ys[-1], zc + 1.0])
    pts, labs = sheet_points(np.array([[cx[0], cx[1], zc]]))
    for p in pts:
        s_ = p[np.all((p >= box[0]) & (p <= box[1]), 1)]
        for q in s_:
            dr.rectangle([(q[0] - xs[0]) * MAG, (q[1] - ys[0]) * MAG, (q[0] - xs[0]) * MAG + 2, (q[1] - ys[0]) * MAG + 2], fill=(230, 0, 230))
    for PP, VV, col in ((PX, VX, (0, 220, 220)), (PY, VY, (230, 40, 0))):
        q = PP[VV & (np.abs(PP[..., 2] - zc) <= 1.0)]
        for p in q:
            x, y = p[0] - xs[0], p[1] - ys[0]
            if 0 <= x < len(xs) and 0 <= y < len(ys):
                dr.rectangle([x * MAG, y * MAG, x * MAG + 3, y * MAG + 3], fill=col)
    L1 = int(round(1.0 / 0.009362 * MAG))
    dr.rectangle([10, im.size[1] + 8, 10 + L1, im.size[1] + 14], fill="black"); dr.text((16 + L1, im.size[1] + 4), "1 mm", fill="black")
    dr.text((10, im.size[1] + 22), "axial cut z %d at (%d, %d): cyan %s %s, red the crossing surface, magenta our 800 sheets" % (
        zc, cx[0], cx[1], route, name), fill="black")
    cv.save(png)


PX, VX, WX, giX, gjX = work(route, name)
M, meta = RT.checks(PX, VX, (), ())
crops = [("R2bnative", r["start"]) for r in RT.rows(H + "/evidence/r2-starts.csv")]
crops += [("R2cnative", n) for n in ("PHerc0826-seed6273-squarecentre", "PHerc0826-seed5364-squarecentre")]
crops += [("R2dnative", r["start"]) for r in RT.rows(H + "/evidence/r2d-starts.csv")]
FLAG = np.zeros(VX.shape, bool)
pairs = []
for rt, o in crops:
    if starts.get(o) == starts[name]:
        continue
    try:
        PY, VY, WY, giY, gjY = work(rt, o)
    except SystemExit:
        continue
    mX = marks_full(WX, WY, giX, gjX, VX)
    mY = marks_full(WY, WX, giY, gjY, VY)
    if not mX.any() and not mY.any():
        continue
    # map each side's marks onto the other through the S.R neighbourhood, union both ways
    qX, qY = PX[VX], PY[VY]
    iX = np.flatnonzero(VX.ravel()); iY = np.flatnonzero(VY.ravel())
    mXf, mYf = mX.ravel()[iX], mY.ravel()[iY]
    tX, tY = cKDTree(qX), cKDTree(qY)
    regX = mXf.copy(); regY = mYf.copy()
    if mYf.any():
        for lst in tX.query_ball_point(qY[mYf], S.R):
            regX[lst] = True
    if mXf.any():
        for lst in tY.query_ball_point(qX[mXf], S.R):
            regY[lst] = True
    shX, bestX = share(qX[regX]); shY, bestY = share(qY[regY])
    if round(shX, 4) == round(shY, 4):
        kept, flagged = "none (tie)", "both"
    elif shX > shY:
        kept, flagged = "%s %s" % KEYX, "%s %s" % (rt, o)
    else:
        kept, flagged = "%s %s" % (rt, o), "%s %s" % KEYX
    xflag = flagged in ("both", "%s %s" % KEYX)
    # X's cells to flag when X loses: its crossing cells of this pair, both ways (regX holds X's own marks and the cells
    # near Y's marks); the declaration names the crossing cells: X's marks and X's cells within S.R of Y's marks
    if xflag:
        f = np.zeros(VX.size, bool); f[iX[regX]] = True
        FLAG |= f.reshape(VX.shape)
    cen = qX[regX].mean(0) if regX.any() else qY[regY].mean(0)
    png = ART + "/cross-%s-%s-vs-%s-%s.png" % (route, name.replace("PHerc0826-", ""), rt, o.replace("PHerc0826-", ""))
    first = (route, name) < (rt, o)
    if first:
        cut(PX, VX, cen, PY, VY, png)
        pairs.append(dict(utc=utc(), surface_1="%s %s" % KEYX, surface_2="%s %s" % (rt, o), crossing_cells_1=int(mXf.sum()),
                          crossing_cells_2=int(mYf.sum()), region_nodes_1=int(regX.sum()), region_nodes_2=int(regY.sum()),
                          share_800_within_3vox_1="%.4f" % shX, share_800_within_3vox_2="%.4f" % shY, best_sheet_1=bestX, best_sheet_2=bestY,
                          kept=kept, flagged=flagged, centroid_xyz="%.0f %.0f %.0f" % tuple(cen), cut_png=png))
    print("pair", rt, o, int(mXf.sum()), int(mYf.sum()), "%.4f %.4f" % (shX, shY), "kept", kept, flush=True)
adj = VX & ~M["v2"] & ~M["self_conflict"] & ~M["a2_rule"] & ~FLAG
b, ci, cj = RT.SQ.largest_square(adj)
sl = (slice(ci, ci + b), slice(cj, cj + b))
row = dict(utc=utc(), route=route, surface=name, certified_this_study_mm=old["square_mm"],
           certified_article_mm=art_rows[-1]["certified_article_mm"] if art_rows else "not measurable: no article row",
           certified_adjudicated_mm="%.4f" % (b * step), certified_adjudicated_cells=int(b), certified_adjudicated_corner="%d %d" % (ci, cj),
           in_square_holes=int((~VX[sl]).sum()), in_square_v2_800=int(M["v2"][sl].sum()), in_square_flagged_crossing=int(FLAG[sl].sum()),
           in_square_self_conflict_a=int(M["self_conflict"][sl].sum()), in_square_self_conflict_b=int(M["b_end"][sl].sum()),
           in_square_a2_rule=int(M["a2_rule"][sl].sum()), flagged_crossing_cells_on_surface=int(FLAG.sum()),
           exceeds_29_8961="yes" if b * step > 29.8961 else "no", step_mm="%.6f" % step)
for p, rs, cols in ((H + "/evidence/square-checks-adjudicated.csv", [row], list(row)),
                    (H + "/evidence/crossing-pairs.csv", pairs, list(pairs[0]) if pairs else None)):
    if not rs:
        continue
    with open(p, "a", newline="") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        new = os.path.getsize(p) == 0
        if new:
            f.write("# written by render-routes-0826/tools/adjudicate.py: the director's adjudication rule of 2026-09-29T23:59:34Z "
                    "(DECLARATION addition 00:01Z): in each crossing pair of traced surfaces the one with the larger share of its crossing "
                    "region within 3 voxels of our 800 sheets is kept, the other flagged, ties flag both\n")
        w = csv.DictWriter(f, cols, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerows(rs)
print(row)
