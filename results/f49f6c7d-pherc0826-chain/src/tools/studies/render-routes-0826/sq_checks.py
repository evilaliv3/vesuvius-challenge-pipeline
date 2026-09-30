#!/usr/bin/env python3
"""render-routes-0826/tools/sq_checks.py ROUTE NAME: the extra checks the coordinator asked (2026-09-29, after the first R2b rows)
on the largest certified square of one row (scratch/rows/<ROUTE>-<NAME>.json) -> one row of evidence/square-checks.csv.

 (a) inside the certified square: v2 cells, self conflict cells (a end, b end), a2 cluster rule cells, holes (each must be 0);
 (b) the strict certified square: largest square avoiding v2, self conflict (a end) and every a2 flagged block (cert.py's
     certified_strict);
 (c) the pairwise one lamina square: pairwise-cert-0826/tools/pairwise.py's rule (conflict_pairs, build, Pairwise.largest,
     imported unchanged): hole free, no v2, no a2 rule cell, no conflict pair with both ends inside;
 (d) straightened sections through the certified square's centre i and j lines: best-windows-0826/tools/straight.py's
     tangent() and line() copied unchanged (the module cannot be imported); raw scan (nearest voxel, 20250821151701 level 0) along each point's smoothed normal, -60..+60
     voxels; statistic as straight.py: median |offset| of the brightest voxel within +-15 of the middle, q25, q75, share
     within 3 voxels;
 (e) the square's radius about the published umbilicus (median, p5, p95 of its cells) and its overlap with our 800 sheets:
     per candidate sheet (area90 index keys), the share of the square's cells with a sheet point within 2 voxels (3D); the
     best sheet named. Winding: no per sheet winding index exists in the house files, so «not measurable».
 The same tool on L S5364sq is the known reference for (d): best-windows-0826 evidence/straight.csv rows cert5364.
"""
import csv, json, os, subprocess, sys, fcntl, shutil
import numpy as np
from scipy.spatial import cKDTree

H = "/data/scrollagent/runs/rev1/render-routes-0826"
R1D = "/data/scrollagent/runs/rev1"
sys.path.insert(0, H + "/tools")
import routes as RT  # noqa: E402
import regrid_z as R  # noqa: E402
sys.path.insert(0, R1D + "/pairwise-cert-0826/tools")
import pairwise as PWM  # noqa: E402


class ST:
    """best-windows-0826/tools/straight.py's constants and its tangent() and line(), COPIED (that module cannot be imported:
    its line 18 reads TOOL before defining it, and its «import panels» would meet this study's panels.py)."""
    T_HALF, PEAK = 60, 15


def _tangent(P, V, a, b, da, db):
    def nv(s):
        for k in range(0, 4):
            x, y = a + s * (2 + k) * da, b + s * (2 + k) * db
            if 0 <= x < V.shape[0] and 0 <= y < V.shape[1] and V[x, y]:
                return P[x, y]
        return None
    p, q = nv(1), nv(-1)
    return None if p is None or q is None else p - q


def _line(P, V, T, axis):
    ci, cj, i0, j0 = T["ci"], T["cj"], T["i0"], T["j0"]
    ic, jc = i0 + ci // 2, j0 + cj // 2
    if not V[ic, jc]:
        ii, jj = np.nonzero(V[i0:i0 + ci, j0:j0 + cj]); k = np.argmin((ii + i0 - ic) ** 2 + (jj + j0 - jc) ** 2)
        ic, jc = int(ii[k] + i0), int(jj[k] + j0)
    cells = [(i, jc) for i in range(i0, i0 + ci)] if axis == "i" else [(ic, j) for j in range(j0, j0 + cj)]
    pts = np.full((len(cells), 3), np.nan); nrm = np.full((len(cells), 3), np.nan)
    for n, (a, b) in enumerate(cells):
        if not V[a, b]:
            continue
        pts[n] = P[a, b]
        ti, tj = _tangent(P, V, a, b, 1, 0), _tangent(P, V, a, b, 0, 1)
        if ti is not None and tj is not None:
            c = np.cross(ti, tj); nrm[n] = c / np.linalg.norm(c)
    n0 = np.cross(_tangent(P, V, ic, jc, 1, 0), _tangent(P, V, ic, jc, 0, 1)); n0 /= np.linalg.norm(n0)
    ok = np.isfinite(nrm).all(1)
    nrm[ok] *= np.sign(nrm[ok] @ n0)[:, None]
    # moving mean over 9 points along the line (valid ones), renormalised
    sm = np.full_like(nrm, np.nan)
    for n in range(len(cells)):
        if not np.isfinite(pts[n]).all():
            continue
        w = nrm[max(0, n - 4):n + 5]; w = w[np.isfinite(w).all(1)]
        if len(w):
            m = w.mean(0); sm[n] = m / np.linalg.norm(m)
    return pts, sm, (ic, jc)



ST.line = staticmethod(_line)
A, LA, S, SQ, PT, DK = RT.A, RT.LA, RT.S, RT.SQ, RT.PT, RT.DK
PT.CACHE = H + "/scratch/raw-chunks"
NM = "not measurable"


def main(route, name):
    j = json.load(open(H + "/scratch/rows/%s-%s.json" % (route, name)))
    P, V, box, masks, info, Rg = RT.surface(route, name)
    b = int(j["largest_certified_square_cells"]); i0, j0 = map(int, j["largest_certified_square_corner"].split())
    if route == "L":
        M = {k: masks[k] & V for k in masks}
        z = np.load(RT.mask_npz(Rg["label"]))
        M["a2_all"] = z["a2"].astype(bool) & V if "a2" in z.files else None
        px, py, pz = [np.where(V, P[..., k], 0.0) for k in range(3)]
        W = S.working(px, py, pz, V, "PHerc0826", "route")
    else:
        excl = (A.label(Rg["seed"], Rg["k"]),) if route == "R1" else ()
        M, _ = RT.checks(P, V, excl, ())
        px, py, pz = [np.where(V, P[..., k], 0.0) for k in range(3)]
        W = S.working(px, py, pz, V, "PHerc0826", "route")
    sl = (slice(i0, i0 + b), slice(j0, j0 + b))
    # v2 against the other R2b crops (same pair_v2 and marks, their working grids)
    v2r = NM
    if route in ("R2bnative", "R2cnative"):     # R2c: against the 9 R2b crops of the OTHER starts
        L2c, L2j, _ = A.thresholds()
        CR_ = np.zeros(W["ok"].shape, bool)
        others = [r["start"] for r in RT.rows(H + "/evidence/r2-starts.csv") if r["start"] != name]
        for o in others:
            try:
                Po, Vo = RT.surface("R2bnative", o)[:2]
            except SystemExit:
                continue
            qx, qy, qz = [np.where(Vo, Po[..., k], 0.0) for k in range(3)]
            Wo = S.working(qx, qy, qz, Vo, "PHerc0826", o)
            rr = RT.V2.pair_v2(W, Wo)
            if rr is None:
                continue
            c_, j_ = RT.V2.marks(rr, L2c, L2j)
            CR_ |= c_ | j_
        gi0, gj0 = A.nearest_block(V.shape, W["s"], CR_.shape)
        v2r = int((CR_[gi0[:, None], gj0[None, :]] & V)[sl].sum())
    row = dict(route=route, surface=name, square_cells=b, square_corner="%d %d" % (i0, j0),
               square_mm=j["largest_certified_square_mm"],
               in_square_v2=int(M["v2"][sl].sum()), in_square_v2_other_r2b=v2r, in_square_self_conflict_a=int(M["self_conflict"][sl].sum()),
               in_square_self_conflict_b=int(M["b_end"][sl].sum()) if "b_end" in M else NM,
               in_square_a2_rule=int(M["a2_rule"][sl].sum()), in_square_holes=int((~V[sl]).sum()))
    step = min(float(j["step_i_mm"]), float(j["step_j_mm"]))
    if M.get("a2_all") is not None:
        st = SQ.largest_square(V & ~M["v2"] & ~M["self_conflict"] & ~M["a2_all"])
        row.update(strict_square_mm="%.4f" % (st[0] * step), strict_square_cells=int(st[0]), strict_corner="%d %d" % (st[1], st[2]))
    else:
        row.update(strict_square_mm=NM)
    # (c) pairwise
    pit = LA.pitch()
    s = W["s"]
    gi, gj = A.nearest_block(V.shape, s, W["ok"].shape)
    allowed = V & ~M["v2"] & ~M["a2_rule"]
    PW, flag, npairs = PWM.build(allowed, W, gi, gj, pit)
    cert = V & ~M["v2"] & ~M["self_conflict"] & ~M["a2_rule"]
    cq = SQ.largest_square(cert); up = SQ.largest_square(allowed)
    side, ci, cj = PW.largest(cq[0], up[0])
    row.update(pairwise_square_mm="%.4f" % (side * step), pairwise_square_cells=int(side), pairwise_corner="%d %d" % (ci, cj),
               pairs_inside_pairwise_square=PW.inside(side, ci, cj), conflict_pairs=int(npairs))
    # (d) straightened sections
    T = dict(ci=b, cj=b, i0=i0, j0=j0)
    ts = np.arange(-ST.T_HALF, ST.T_HALF + 1)
    geo = {}
    allX = []
    for ax in ("i", "j"):
        pts, nrm, cen = ST.line(P, V, T, ax)
        X = pts[:, None, :] + ts[None, :, None] * nrm[:, None, :]
        geo[ax] = (pts, X, cen)
        f = np.isfinite(X).all(-1)
        allX.append(X[f])
    Xa = np.concatenate(allX)
    rec = np.zeros(len(Xa), PT.POINT); rec["px"], rec["py"], rec["pz"] = Xa[:, 0], Xa[:, 1], Xa[:, 2]
    lk = open(H + "/scratch/cache.lock", "a"); fcntl.flock(lk, fcntl.LOCK_SH)
    need = DK.chunks_of(rec); todo = sorted(c for c in need if not PT.have(c))
    if shutil.disk_usage("/data").free - len(todo) * PT.NBYTES <= 35e9:
        raise SystemExit("fetch refused: disk")
    if todo:
        tally, got = DK.fetch(todo)
        open(H + "/scratch/fetched-sqcheck-%s-%s.txt" % (route, name), "a").writelines(g + "\n" for g in got)
    raw = PT.Raw2()
    secs = {}
    for ax, (pts, X, cen) in geo.items():
        f = np.isfinite(X).all(-1)
        Sm = np.full(X.shape[:2], np.nan)
        Sm[f] = raw.sample(X[..., 0][f], X[..., 1][f], X[..., 2][f])
        win = Sm[:, ST.T_HALF - ST.PEAK:ST.T_HALF + ST.PEAK + 1]
        colok = np.isfinite(win).all(1) & (np.nan_to_num(win) > 0).any(1)
        tstar = np.abs(np.argmax(np.where(np.isfinite(win), win, -1), axis=1) - ST.PEAK)[colok]
        q = np.percentile(tstar, [25, 50, 75])
        secs["%s_img" % ax] = Sm.astype(np.float32); secs["%s_pt_ok" % ax] = np.isfinite(pts).all(1)
        secs["%s_colmm" % ax] = float(np.nanmedian(np.linalg.norm(np.diff(pts, axis=0), axis=1))) * 0.009362
        row["section_%s_centre" % ax] = "%d %d" % cen
        row["section_%s_columns_scored" % ax] = int(colok.sum())
        row["section_%s_peak_offset_median_vox" % ax] = "%.1f" % q[1]
        row["section_%s_peak_offset_q25_q75_vox" % ax] = "%.1f %.1f" % (q[0], q[2])
        row["section_%s_share_within_3_vox" % ax] = "%.4f" % float((tstar <= 3).mean())
    fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
    np.savez_compressed(H + "/scratch/sections-%s-%s.npz" % (route, name), **secs)   # for the figure
    # (e) radius and overlap with our 800
    U = R.umbilicus(RT.UMB)
    Q = P[sl][V[sl]]
    cx, cy = R.centre(U, Q[:, 2]); rr = np.hypot(Q[:, 0] - cx, Q[:, 1] - cy)
    row.update(radius_median_vox="%.0f" % np.median(rr), radius_p5_p95_vox="%.0f %.0f" % tuple(np.percentile(rr, [5, 95])))
    ks = np.unique(S.keys_of(Q.astype(np.float64)))
    idx = A.index(); cand = set()
    for qk in S.dilate_keys(ks):
        for Mn in idx.get(int(qk), ()):
            cand.add(Mn)
    tq = cKDTree(Q)
    best = []
    for Mn in sorted(cand):
        Wm = A.load_work(Mn)
        pts = Wm["P"][Wm["ok"]].astype(np.float64)
        d, _ = cKDTree(pts).query(Q, distance_upper_bound=6.0)
        best.append((float(np.isfinite(d).mean()), Mn))
    best.sort(reverse=True)
    full3 = []
    for sh_, Mn in best[:3]:
        seed_, k_ = Mn.rsplit("-S", 1)
        Pf, Vf = R.read_patch(RT.patch_of("C40-%s-S%s" % (seed_, k_)))
        d3, _ = cKDTree(Pf[Vf]).query(Q, distance_upper_bound=3.0)
        mnp = RT.mask_npz("C40-%s-S%s" % (seed_, k_))
        if os.path.isfile(mnp):
            pc = np.load(mnp)["piece"].astype(bool)
            d3c, _ = cKDTree(Pf[Vf & pc]).query(Q, distance_upper_bound=3.0) if (Vf & pc).any() else (np.full(len(Q), np.inf), None)
            cs_ = "%.4f" % float(np.isfinite(d3c).mean())
        else:
            cs_ = NM + ": no piece npz"
        full3.append((float(np.isfinite(d3).mean()), Mn, cs_))
    full3.sort(key=lambda x: -x[0])
    row.update(within3_best_sheet=full3[0][1] if full3 else "none", within3_share_all_cells="%.4f" % full3[0][0] if full3 else "0",
               within3_share_certified_piece=full3[0][2] if full3 else "", within3_others=" ".join("%s %.4f" % (m_, s_) for s_, m_, _ in full3[1:]))
    row.update(overlap_candidates=len(cand), overlap_best_sheet=best[0][1] if best else "none",
               overlap_best_share_within_6vox_working="%.4f" % best[0][0] if best else "0",
               overlap_second="%s %.4f" % (best[1][1], best[1][0]) if len(best) > 1 else "none",
               overlap_sheets_over_1pct=sum(1 for s_, _ in best if s_ > 0.01), winding=NM + ": no per sheet winding index in the house files")
    row["utc"] = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
    out = H + "/evidence/square-checks.csv"
    cols = ["utc", "route", "surface", "square_mm", "square_cells", "square_corner", "in_square_v2", "in_square_v2_other_r2b", "in_square_self_conflict_a",
            "in_square_self_conflict_b", "in_square_a2_rule", "in_square_holes", "strict_square_mm", "strict_square_cells", "strict_corner",
            "pairwise_square_mm", "pairwise_square_cells", "pairwise_corner", "pairs_inside_pairwise_square", "conflict_pairs",
            "section_i_centre", "section_i_columns_scored", "section_i_peak_offset_median_vox", "section_i_peak_offset_q25_q75_vox",
            "section_i_share_within_3_vox", "section_j_centre", "section_j_columns_scored", "section_j_peak_offset_median_vox",
            "section_j_peak_offset_q25_q75_vox", "section_j_share_within_3_vox", "radius_median_vox", "radius_p5_p95_vox",
            "within3_best_sheet", "within3_share_all_cells", "within3_share_certified_piece", "within3_others",
            "overlap_candidates", "overlap_best_sheet", "overlap_best_share_within_6vox_working", "overlap_second", "overlap_sheets_over_1pct",
            "winding"]
    new = not os.path.isfile(out)
    with open(out, "a", newline="") as f:
        if new:
            f.write("# written by render-routes-0826/tools/sq_checks.py: checks on a row's largest certified square (docstring of the tool): "
                    "flags inside it, strict and pairwise squares, straightened sections (best-windows straight.py's line and statistic), "
                    "radius about the published umbilicus, share of the square's nodes within 3 voxels of our best sheet (full lattice; certified piece), candidates ranked within 6 voxels on working grids\n")
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(cols)
        w.writerow([row.get(c, "") for c in cols])
    print(json.dumps(row))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
