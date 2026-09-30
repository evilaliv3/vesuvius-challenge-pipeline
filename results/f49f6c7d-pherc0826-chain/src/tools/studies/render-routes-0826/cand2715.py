#!/usr/bin/env python3
"""render-routes-0826/tools/cand2715.py MODE: the checks on R2d seed2715 S0 before any record (DECLARATION addition 23:56Z,
director 23:55:12Z). Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.
    cand2715.py cuts        (4) axial cuts at the p5 and p95 z of the existing certified square -> evidence/axial-cut-z.csv, PNGs
    cand2715.py dark_a2     (2) dark share (certified-piece-0826/tools/dark.py lines 159 to 166, copied unchanged: not measurable
                            counted 0, T = 0.5 x median over the square's cells, dark = under T or not measurable) and the largest
                            square of certified_article's mask without dark cells; (3) a2 flagged blocks inside the square (area90
                            a2_grid, the calls of routes.checks) and a map PNG -> evidence/candidate-2715.csv
"""
import csv, fcntl, json, os, shutil, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw
H = "/data/scrollagent/runs/rev1/render-routes-0826"
sys.path.insert(0, H + "/tools")
import routes as RT, regrid_z as R  # noqa: E402
A, MC, CRL, PT, DK = RT.A, RT.MC, RT.CRL, RT.PT, RT.DK
PT.CACHE = H + "/scratch/raw-chunks"
ART = "/data/scrollagent/outputs/artifacts/render-routes-0826"
ROUTE, NAME = "R2dnative", "PHerc0826-seed2715-S0-sq"
sc = [r for r in RT.rows(H + "/evidence/square-checks.csv") if r["route"] == ROUTE and r["surface"] == NAME][-1]
b = int(sc["square_cells"]); i0, j0 = map(int, sc["square_corner"].split())
P, V = RT.surface(ROUTE, NAME)[:2]
SQ_ = (slice(i0, i0 + b), slice(j0, j0 + b))
j = json.load(open(H + "/scratch/rows/%s-%s.json" % (ROUTE, NAME)))
step = min(float(j["step_i_mm"]), float(j["step_j_mm"]))


def utc():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()


def put(p, head, row):
    with open(p, "a", newline="") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        new = os.path.getsize(p) == 0
        if new:
            f.write(head + "\n")
        w = csv.DictWriter(f, list(row), lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow(row)


def cuts():
    best = sc["within3_best_sheet"]
    sd, sk = best.rsplit("-S", 1)
    Pf, Vf = R.read_patch(RT.patch_of("C40-%s-S%s" % (sd, sk)))
    Zs = P[SQ_][..., 2][V[SQ_]]
    for tag, zt in (("bottom p5", float(np.percentile(Zs, 5))), ("top p95", float(np.percentile(Zs, 95)))):
        zc = float(np.rint(zt))
        ii, jj = np.nonzero(V[SQ_] & (np.abs(P[SQ_][..., 2] - zc) <= 1.0))
        if len(ii) == 0:
            raise SystemExit("refuse: no square node at z %d" % zc)
        k = np.argmin(np.abs(jj - b / 2.0))
        c = P[i0 + ii[k], j0 + jj[k]]
        HALF, MAG = 320, 2
        xs = np.arange(int(c[0]) - HALF, int(c[0]) + HALF + 1); ys = np.arange(int(c[1]) - HALF, int(c[1]) + HALF + 1)
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
            open(H + "/scratch/fetched-cand2715-cuts.txt", "a").writelines(g + "\n" for g in got)
        img = PT.Raw2().sample(X.ravel().astype(float), Y.ravel().astype(float), Z.ravel()).reshape(X.shape)
        fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
        g = img[np.isfinite(img) & (img > 0)]; lo, hi = np.percentile(g, [1, 99.5])
        gray = (np.clip((np.nan_to_num(img) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
        im = Image.fromarray(np.stack([gray] * 3, -1)).resize((X.shape[1] * MAG, X.shape[0] * MAG), Image.NEAREST)
        cv = Image.new("RGB", (im.size[0], im.size[1] + 70), "white"); cv.paste(im, (0, 0)); dr = ImageDraw.Draw(cv)
        cnt = {}
        SQM = np.zeros(V.shape, bool); SQM[SQ_] = True
        for key, pts, col in (("our_sheet", Pf[Vf & (np.abs(Pf[..., 2] - zc) <= 1.0)], (230, 0, 230)),
                              ("surface", P[V & ~SQM & (np.abs(P[..., 2] - zc) <= 1.0)], (0, 220, 220)),
                              ("square", P[V & SQM & (np.abs(P[..., 2] - zc) <= 1.0)], (255, 220, 0))):
            n = 0
            for p in pts:
                x, y = p[0] - xs[0], p[1] - ys[0]
                if 0 <= x < len(xs) and 0 <= y < len(ys):
                    dr.rectangle([x * MAG, y * MAG, x * MAG + 3, y * MAG + 3], fill=col); n += 1
            cnt[key] = n
        L1 = int(round(1.0 / 0.009362 * MAG))
        dr.rectangle([10, im.size[1] + 8, 10 + L1, im.size[1] + 14], fill="black"); dr.text((16 + L1, im.size[1] + 4), "1 mm", fill="black")
        dr.text((10, im.size[1] + 22), "%s %s: axial cut at the square's %s z %d, centre (%d, %d); cyan surface, yellow the square, magenta our "
                "sheet %s" % (ROUTE, NAME, tag, zc, c[0], c[1], best), fill="black")
        png = ART + "/%s-%s-axial-%s.png" % (NAME, ROUTE, tag.split()[0])
        cv.save(png)
        put(H + "/evidence/axial-cut-z.csv", "# written by render-routes-0826/tools/cand2715.py cuts: axial cuts at the p5 and p95 z of the "
            "existing certified square of R2d seed2715 S0 (DECLARATION addition 23:56Z); counts of marked nodes; judgement in the queue item",
            dict(utc=utc(), route=ROUTE, surface=NAME, where=tag, z=int(zc), x="%.0f" % c[0], y="%.0f" % c[1], surface_nodes=cnt["surface"],
                 square_nodes=cnt["square"], our_sheet=best, our_sheet_nodes=cnt["our_sheet"], png=png))
        print(tag, zc, cnt, png)


def dark_a2():
    za = np.load(H + "/scratch/article-%s-%s.npz" % (ROUTE, NAME))
    art = za["art"]
    zv = np.load(H + "/scratch/values-%s-%s.npz" % (ROUTE, NAME))
    VAL = zv["VAL"].astype(np.float64)
    # dark.py lines 159 to 166, copied unchanged in substance: v0 = value with not measurable as 0; T = 0.5 x median; dark = v0 < T or nan
    v0 = np.where(np.isnan(VAL), 0.0, VAL)
    sel = V[SQ_]
    med = float(np.median(v0[SQ_][sel]))
    T = 0.5 * med
    dark = ((v0 < T) | np.isnan(VAL)) & V
    dsq = dark[SQ_][sel]
    nd = art & ~dark
    bb, bi, bj = RT.SQ.largest_square(nd)
    ba, ai, aj = RT.SQ.largest_square(art)
    # (3) a2 flag grid (area90.a2_grid, as routes.checks calls it)
    px, py, pz = [np.where(V, P[..., k], 0.0) for k in range(3)]
    A.D.selftest_passed(); MC.selftest_ok()
    Tt, _ = MC.verdict_row("a2")
    gflag, meas, fl = A.a2_grid(px, py, pz, V, Tt)
    blk = A.block_mask(gflag, V.shape, MC.STRIDE) & V
    s = MC.STRIDE
    gi0, gi1 = i0 // s, (i0 + b - 1) // s; gj0, gj1 = j0 // s, (j0 + b - 1) // s
    G = gflag[gi0:gi1 + 1, gj0:gj1 + 1]
    gi, gj = np.nonzero(G)
    row = dict(utc=utc(), route=ROUTE, surface=NAME, square_mm=sc["square_mm"], square_cells=b, square_corner="%d %d" % (i0, j0),
               dark_rule="certified-piece-0826/tools/dark.py lines 159 to 166 (T = 0.5 x median over the square, not measurable as 0)",
               square_median="%.1f" % med, dark_threshold="%.1f" % T, dark_cells_in_square=int(dsq.sum()), dark_share_in_square="%.4f" % dsq.mean(),
               certified_article_mm="%.4f" % (ba * step), certified_article_corner="%d %d" % (ai, aj),
               certified_article_no_dark_mm="%.4f" % (bb * step), certified_article_no_dark_cells=int(bb),
               certified_article_no_dark_corner="%d %d" % (bi, bj),
               a2_stride_cells=s, a2_measurable=meas, a2_flagged=fl, a2_flag_blocks_in_square=int(G.sum()),
               a2_flagged_cells_in_square=int(blk[SQ_].sum()),
               a2_blocks_bbox_in_square="%s" % ("rows %d..%d cols %d..%d (cells from the square's corner)" % (
                   gi.min() * s + gi0 * s - i0, (gi.max() + 1) * s + gi0 * s - i0 - 1, gj.min() * s + gj0 * s - j0, (gj.max() + 1) * s + gj0 * s - j0 - 1)
                   if len(gi) else "none"), strict_square_mm_existing=sc["strict_square_mm"])
    put(H + "/evidence/candidate-2715.csv", "# written by render-routes-0826/tools/cand2715.py dark_a2: seed2715 S0 R2d candidate checks (2) and (3) "
        "(DECLARATION addition 23:56Z)", row)
    # map PNG: the square, a2 flagged blocks red, dark blue, the no dark article square cyan outline
    img = np.full((b, b, 3), 235, np.uint8)
    img[dark[SQ_]] = (40, 110, 255)
    img[blk[SQ_]] = (213, 94, 0)
    img[~V[SQ_]] = 255
    im = Image.fromarray(img); dr = ImageDraw.Draw(im)
    if bb:
        dr.rectangle([bj - j0, bi - i0, bj - j0 + bb - 1, bi - i0 + bb - 1], outline=(0, 160, 220), width=3)
    cv = Image.new("RGB", (b, b + 50), "white"); cv.paste(im, (0, 0)); d2 = ImageDraw.Draw(cv)
    d2.text((5, b + 5), "seed2715 S0 R2d square %s mm: red a2 flagged blocks, blue dark (T %.1f), cyan the largest square with no flag and no "
            "dark cell (%.2f mm)" % (sc["square_mm"], T, bb * step), fill="black")
    cv.save(ART + "/%s-%s-flags-dark-map.png" % (NAME, ROUTE))
    print(row)


if __name__ == "__main__":
    {"cuts": cuts, "dark_a2": dark_a2}[sys.argv[1]]()
