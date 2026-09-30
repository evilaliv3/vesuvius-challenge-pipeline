#!/usr/bin/env python3
"""straight.py: straightened sections (DECLARATION.md addition 2026-09-29T06:46:40Z, director's look of 06:40:06Z). New file,
coordinator agent. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran. PNGs only into outputs/artifacts/best-windows-0826/.

    straight.py one <tag>     both centre lines of the target: fetch (bw.py lock and 35 GB rule), sample, draw, rows of
                              evidence/straight.csv, arrays in scratch/panel-data/straight-<tag>.npz; then bw.py drop
"""
import csv, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = "/data/scrollagent/runs/rev1/best-windows-0826"
sys.path.insert(0, HERE + "/tools")
import bw  # noqa: E402
import align as AL  # noqa: E402
import panels as PN  # noqa: E402
rs = PN.rs
PN.TOOL = TOOL + " (via panels.row_csv)"
TOOL = "best-windows-0826/tools/straight.py"
ART = PN.ART
VOX = 0.009362
T_HALF, PEAK, MAG = 60, 15, 2


def tangent(P, V, a, b, da, db):
    def nv(s):
        for k in range(0, 4):
            x, y = a + s * (2 + k) * da, b + s * (2 + k) * db
            if 0 <= x < V.shape[0] and 0 <= y < V.shape[1] and V[x, y]:
                return P[x, y]
        return None
    p, q = nv(1), nv(-1)
    return None if p is None or q is None else p - q


def line(P, V, T, axis):
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
        ti, tj = tangent(P, V, a, b, 1, 0), tangent(P, V, a, b, 0, 1)
        if ti is not None and tj is not None:
            c = np.cross(ti, tj); nrm[n] = c / np.linalg.norm(c)
    n0 = np.cross(tangent(P, V, ic, jc, 1, 0), tangent(P, V, ic, jc, 0, 1)); n0 /= np.linalg.norm(n0)
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


def one(tag):
    T = {t["tag"]: t for t in AL.targets(all_clean=True)}[tag]
    L = T["label"]
    P, V, si, sj = AL.sheet_points(L)
    ts = np.arange(-T_HALF, T_HALF + 1)
    geo = {}
    need = set()
    for ax in ("i", "j"):
        pts, nrm, cen = line(P, V, T, ax)
        X = pts[:, None, :] + ts[None, :, None] * nrm[:, None, :]
        geo[ax] = (pts, nrm, cen, X)
        f = np.isfinite(X).all(-1)
        need |= PN.chunk_keys(X[..., 0][f], X[..., 1][f], X[..., 2][f])
    okf, gb, free = bw.fetch_chunks("straight-" + tag, need, "straightened sections %s (%d chunks)" % (tag, len(need)))
    if not okf:
        raise SystemExit("fetch refused or failed (free %.1f GB)" % free)
    raw = bw.Raw3()
    save = {}
    lab = L + ("-cert" if tag == "cert5364" else "")
    what = "%s %s sheet %s" % (L.split("-")[2], L.split("-")[0], L.split("-S")[-1])
    for ax, (pts, nrm, cen, X) in geo.items():
        f = np.isfinite(X).all(-1)
        S = np.full(X.shape[:2], np.nan)
        S[f] = raw.sample(X[..., 0][f], X[..., 1][f], X[..., 2][f])
        img = S.T[::-1]  # rows: +t up; columns: points
        good = np.isfinite(S) & (S > 0)
        lo, hi = np.percentile(S[good], [1, 99.5])
        g = rs.to_grey(img, lo, hi)
        g[:, ~np.isfinite(pts).all(1)] = (255, 255, 255)
        mid = T_HALF  # row of t = 0 after the flip (121 rows, index 60)
        tr = g.copy()
        tr[mid] = (0.6 * tr[mid] + 0.4 * np.array([0, 230, 230])).astype(np.uint8)
        # peak offsets
        win = S[:, T_HALF - PEAK:T_HALF + PEAK + 1]
        colok = np.isfinite(win).all(1) & (np.nan_to_num(win) > 0).any(1)
        tstar = np.abs(np.argmax(np.where(np.isfinite(win), win, -1), axis=1) - PEAK)[colok]
        q = np.percentile(tstar, [25, 50, 75])
        d = np.linalg.norm(np.diff(pts, axis=0), axis=1); colmm = float(np.nanmedian(d)) * VOX
        stack = np.concatenate([g, np.full((6, g.shape[1], 3), 255, np.uint8), tr], 0)
        im = Image.fromarray(stack).resize((stack.shape[1] * MAG, stack.shape[0] * MAG), Image.NEAREST)
        # bars: 1 mm and 5 mm along the columns, 1 mm along the rows
        W_, H_ = im.size
        pad = 150
        cv = Image.new("RGB", (max(W_, 900), H_ + pad), (255, 255, 255)); cv.paste(im, (0, 0))
        dr = ImageDraw.Draw(cv)
        x = 10; yb = H_ + 18
        for mm in (1.0, 5.0):
            px = int(round(mm / colmm * MAG))
            dr.rectangle((x, yb, x + px, yb + 6), fill=(0, 0, 0)); dr.text((x, yb + 8), "%g mm along the line" % mm, fill=(0, 0, 0), font=PN.font(13))
            x += px + 160
        vpx = int(round(1.0 / VOX * MAG))
        dr.rectangle((W_ - 20, 0 + 4, W_ - 14, 4 + vpx), fill=(0, 0, 0)) if vpx < H_ else None
        lines = ["%s: %s, straightened section along the lattice %s line through the window centre (%d, %d); %s" % (
                     tag, what, ax, cen[0], cen[1], T["what"]),
                 "one column per grown point (%d points, median spacing %.4f mm); rows: the raw scan (20250821151701 level 0, nearest "
                 "voxel) along each point's own normal from -60 (bottom) to +60 voxels (top); middle row = the traced sheet, faint cyan "
                 "in the lower copy; white column = no grown point; shown magnified %d x; vertical bar at the right: 1 mm (107 voxels) "
                 "when it fits" % (len(pts), colmm, MAG),
                 "brightest voxel within +-15 of the middle: median |offset| %.0f voxels (q25 %.0f, q75 %.0f), %.3f of the columns within "
                 "3 voxels" % (q[1], q[0], q[2], float((tstar <= 3).mean()))]
        import textwrap
        yy = yb + 34
        for t in lines:
            for s_ in textwrap.wrap(t, 150):
                dr.text((10, yy), s_, fill=(40, 40, 40), font=PN.font(14)); yy += 18
        pth = ART + "/straight-%s-%s.png" % (lab, ax); cv.save(pth)
        PN.row_csv(HERE + "/evidence/straight.csv", dict(
            tag=tag, label=L, line=ax, centre_i=cen[0], centre_j=cen[1], points=int(np.isfinite(pts).all(1).sum()), columns=len(pts),
            columns_scored=int(colok.sum()), column_spacing_mm="%.5f" % colmm, peak_window_vox=PEAK,
            peak_offset_median_vox="%.1f" % q[1], peak_offset_q25_vox="%.1f" % q[0], peak_offset_q75_vox="%.1f" % q[2],
            share_within_3_vox="%.4f" % float((tstar <= 3).mean()), grey_p1="%.0f" % lo, grey_p995="%.0f" % hi,
            not_measurable_share="%.6f" % float((~np.isfinite(S)).mean()), png=os.path.basename(pth)),
            "one row per straightened section (DECLARATION.md addition 2026-09-29T06:46:40Z): raw scan along each grown point's "
            "smoothed lattice normal, -60..+60 voxels; peak_offset = |offset| of the brightest voxel within +-15 of the middle row")
        save["%s_img" % ax] = S.astype(np.float32); save["%s_lo" % ax] = lo; save["%s_hi" % ax] = hi; save["%s_colmm" % ax] = colmm
        save["%s_pt_ok" % ax] = np.isfinite(pts).all(1)
        print(tag, ax, "median |t*| %.1f, within 3: %.3f" % (q[1], float((tstar <= 3).mean())), flush=True)
    os.makedirs(HERE + "/scratch/panel-data", exist_ok=True)
    np.savez_compressed(HERE + "/scratch/panel-data/straight-%s.npz" % tag, **save)


if __name__ == "__main__":
    if sys.argv[1] == "one":
        one(sys.argv[2])
