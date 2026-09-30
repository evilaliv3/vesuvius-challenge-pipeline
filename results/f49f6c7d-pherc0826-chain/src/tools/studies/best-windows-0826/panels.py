#!/usr/bin/env python3
"""panels.py: best-windows-0826 panels (DECLARATION.md 2026-09-29T06:14:07Z, sections (1) and (2); addition 06:23:23Z, the side by
side renders). New file, coordinator agent. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran. PNGs only into outputs/artifacts/best-windows-0826/.

    panels.py one <tag>     fetch the chunks the panels need (lock and 35 GB rule of bw.py), draw, write rows of
                            evidence/sections.csv and evidence/renders.csv; then bw.py's drop lists and deletes them

Renders use render_surface.to_grey (texture_best.py's and piece_texture.py's grey), nearest voxel of the raw masked scan
20250821151701 level 0 (bw.Raw3 = piece_texture.Raw2 reading this study's cache first). Bars: 5 mm and 10 mm.
"""
import csv, json, os, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw

HERE = "/data/scrollagent/runs/rev1/best-windows-0826"
sys.path.insert(0, HERE + "/tools")
import bw  # noqa: E402
import align as AL  # noqa: E402
rs = bw.F.rs
PT = bw.PT
TOOL = "best-windows-0826/tools/panels.py"
ART = "/data/scrollagent/outputs/artifacts/best-windows-0826"
VOX = 0.009362
MAG, RED, GREEN, CYAN, ORANGE = (255, 0, 255), (230, 0, 0), (0, 190, 0), (0, 230, 230), (255, 140, 0)
HALFN = 40


def font(n):
    return rs.font(n)


def caption(img, mm_per_px, title, lines, width=90):
    lines = [x for t in lines for x in textwrap.wrap(t, width)]
    w, h = img.size
    pad = 44 + 20 * len(lines) + 60
    cv = Image.new("RGB", (max(w, 760), h + pad), (255, 255, 255))
    cv.paste(img, (0, 0))
    d = ImageDraw.Draw(cv)
    d.text((10, h + 8), title, fill=(0, 0, 0), font=font(20))
    for n, t in enumerate(lines):
        d.text((10, h + 38 + 20 * n), t, fill=(40, 40, 40), font=font(15))
    yb = h + pad - 26; x = 10
    for mm in (5.0, 10.0):
        px = int(round(mm / mm_per_px))
        d.rectangle((x, yb, x + px, yb + 8), fill=(0, 0, 0))
        d.text((x, yb - 20), "%g mm" % mm if mm < 10 else "1 cm", fill=(0, 0, 0), font=font(15))
        x += px + 40
    return cv


def grey(V, ok):
    pool = V[ok & np.isfinite(V) & (V > 0)]
    lo, hi = (float(np.percentile(pool, 1)), float(np.percentile(pool, 99))) if pool.size else (0.0, 255.0)
    g = rs.to_grey(np.where(ok, V, np.nan), lo, hi)
    g[~ok] = (255, 255, 255)
    return g, lo, hi


def flags_rgb(g, ok, v2, sc, a2r):
    f = (g.astype(np.float32) * 0.5 + 127).astype(np.uint8)
    f[~ok] = (255, 255, 255)
    f[a2r] = GREEN; f[v2] = RED; f[sc] = MAG
    return f


def outline(mask):
    e = np.zeros_like(mask)
    e[1:-1, 1:-1] = mask[1:-1, 1:-1] & ~(mask[:-2, 1:-1] & mask[2:, 1:-1] & mask[1:-1, :-2] & mask[1:-1, 2:])
    return e


def row_csv(p, row, head_note):
    new = not os.path.isfile(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write("# written by %s: %s\n" % (TOOL, head_note))
        w = csv.DictWriter(f, list(row), lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow(row)


def chunk_keys(x, y, z):
    xi, yi, zi = (np.rint(a).astype(np.int64) for a in (x, y, z))
    ins = (xi >= 0) & (yi >= 0) & (zi >= 0) & (zi < PT.SHAPE[0]) & (yi < PT.SHAPE[1]) & (xi < PT.SHAPE[2])
    k = np.unique(np.stack([zi[ins] // PT.CH, yi[ins] // PT.CH, xi[ins] // PT.CH], 1), axis=0)
    return set(map(tuple, k.tolist()))


def nearest_valid(P, V, i, j, di, dj, n):
    for s in range(0, n):
        for sg in (1, -1):
            a, b = i + sg * s * di, j + sg * s * dj
            if 0 <= a < V.shape[0] and 0 <= b < V.shape[1] and V[a, b]:
                return P[a, b]
    return None


def section_geometry(P, V, T, axis):
    ci, cj, i0, j0 = T["ci"], T["cj"], T["i0"], T["j0"]
    ic, jc = i0 + ci // 2, j0 + cj // 2
    if not V[ic, jc]:
        ii, jj = np.nonzero(V[i0:i0 + ci, j0:j0 + cj]); k = np.argmin((ii + i0 - ic) ** 2 + (jj + j0 - jc) ** 2)
        ic, jc = int(ii[k] + i0), int(jj[k] + j0)
    c = P[ic, jc]
    ti = nearest_valid(P, V, ic + 8, jc, 1, 0, 8) - nearest_valid(P, V, ic - 8, jc, 1, 0, 8)
    tj = nearest_valid(P, V, ic, jc + 8, 0, 1, 8) - nearest_valid(P, V, ic, jc - 8, 0, 1, 8)
    n = np.cross(ti, tj); n /= np.linalg.norm(n)
    if axis == "i":
        idx = [(i, jc) for i in range(i0, i0 + ci) if V[i, jc]]
    else:
        idx = [(ic, j) for j in range(j0, j0 + cj) if V[ic, j]]
    L = np.array([P[a, b] for a, b in idx])
    # addition 06:34Z: the plane contains the local normal n; u = the first principal direction of the line's points projected
    # on the plane perpendicular to n (signed from the first to the last point), the plane of n that keeps the points closest
    X0 = L - c
    Xt = X0 - np.outer(X0 @ n, n)
    _, _, vt = np.linalg.svd(Xt - Xt.mean(0), full_matrices=False)
    u = vt[0] - (vt[0] @ n) * n; u /= np.linalg.norm(u); u *= np.sign(u @ (L[-1] - L[0]))
    n_ang = 0.0
    w = np.cross(u, n)
    A = (L - c) @ u; B = (L - c) @ n; D = (L - c) @ w
    a0, a1 = int(np.floor(A.min())) - HALFN, int(np.ceil(A.max())) + HALFN
    b0, b1 = int(np.floor(min(B.min(), 0))) - HALFN, int(np.ceil(max(B.max(), 0))) + HALFN
    aa, bb = np.meshgrid(np.arange(a0, a1 + 1), np.arange(b0, b1 + 1))
    X = c[None, None, :] + aa[..., None] * u + bb[..., None] * n
    return dict(c=c, n=n, u=u, w=w, A=A, B=B, D=D, a0=a0, a1=a1, b0=b0, b1=b1, X=X, centre=(ic, jc), npts=len(idx), normal_to_plane_deg=n_ang)


def one(tag):
    os.makedirs(ART, exist_ok=True)
    T = {t["tag"]: t for t in AL.targets(all_clean=True)}[tag]
    L = T["label"]
    rank = tag[2:] if tag.startswith("bw") else tag
    P, V, si, sj = AL.sheet_points(L)
    z, src, si, sj = bw.masks(L)
    flag = bw.flag_of(z)
    i0, j0, ci, cj = T["i0"], T["j0"], T["ci"], T["cj"]
    step = min(si, sj)
    A = np.load(AL.OUTA + "/%s.npz" % tag)
    Q, aval = A["Q"].astype(np.float64), A["valid"]
    half, S, c0 = int(A["half"]), int(A["S"]), int(A["c0"])
    sq = (slice(c0, c0 + S), slice(c0, c0 + S))
    Qs, avs = Q[sq], aval[sq]
    need = chunk_keys(Qs[..., 0][avs], Qs[..., 1][avs], Qs[..., 2][avs])
    vpath = bw.VALS + "/%s-%d-%d.npz" % (L, i0, j0)
    have_vals = os.path.isfile(vpath) and tag.startswith("bw")
    Wp = P[i0:i0 + ci, j0:j0 + cj]; Wv = V[i0:i0 + ci, j0:j0 + cj]
    if not have_vals:
        need |= chunk_keys(Wp[..., 0][Wv], Wp[..., 1][Wv], Wp[..., 2][Wv])
    secs = {}
    if tag.startswith("bw"):
        for ax in ("i", "j"):
            g = section_geometry(P, V, T, ax); secs[ax] = g
            need |= chunk_keys(g["X"][..., 0].ravel(), g["X"][..., 1].ravel(), g["X"][..., 2].ravel())
    okf, gb, free = bw.fetch_chunks("panels-" + tag, need, "panels %s (%d chunks)" % (tag, len(need)))
    if not okf:
        raise SystemExit("fetch refused or failed (free %.1f GB)" % free)
    raw = bw.Raw3()
    # ---- current render (lattice)
    if have_vals:
        Z = np.load(vpath); CV = Z["val"].astype(np.float64); cok = Z["valid"]
        cv2, csc, ca2 = Z["v2"], Z["sc"], Z["a2r"]
    else:
        CV = np.full((ci, cj), np.nan)
        CV[Wv] = raw.sample(Wp[..., 0][Wv], Wp[..., 1][Wv], Wp[..., 2][Wv]); cok = Wv
        cv2 = z["v2"][i0:i0 + ci, j0:j0 + cj] & Wv
        csc = (z["self_conflict"] | z["b_end"])[i0:i0 + ci, j0:j0 + cj] & Wv
        ca2 = z["a2_rule"][i0:i0 + ci, j0:j0 + cj] & Wv
    g, lo, hi = grey(CV, cok)
    what = "%s %s sheet %s" % (L.split("-")[2], L.split("-")[0], L.split("-S")[-1])
    base = ["lattice rows %d to %d (i, down), columns %d to %d (j, across), %d x %d cells, %.2f x %.2f mm; one pixel per cell "
            "(%.4f x %.4f mm); nearest voxel of the raw masked scan 20250821151701 level 0; grey p1 %.0f to p99 %.0f" % (
                i0, i0 + ci - 1, j0, j0 + cj - 1, ci, cj, ci * si, cj * sj, si, sj, lo, hi),
            "white = no grown point (hole); dark blue = masked or not measurable", "Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."]
    files = {}
    if tag.startswith("bw"):
        im = caption(Image.fromarray(g), step, "best window %s: %s, %s, raw texture" % (rank, what, T["what"]), base)
        files["texture"] = ART + "/%s-%s-texture.png" % (tag, L); im.save(files["texture"])
        fr = flags_rgb(g, cok, cv2, csc, ca2)
        im = caption(Image.fromarray(fr), step, "best window %s: %s, flags" % (rank, what),
                     ["self conflict (either end) magenta: %d cells; v2 red: %d; a2 cluster rule green: %d; holes white: %d" % (
                         int(csc.sum()), int(cv2.sum()), int(ca2.sum()), int((~cok).sum()))] + base)
        files["flags"] = ART + "/%s-%s-flags.png" % (tag, L); im.save(files["flags"])
    # ---- aligned render
    AV = np.full(avs.shape, np.nan)
    AV[avs] = raw.sample(Qs[..., 0][avs], Qs[..., 1][avs], Qs[..., 2][avs])
    ga, alo, ahi = grey(AV, avs)
    inw = A["inwin"][sq]
    ga = ga[::-1].copy(); inw_o = outline(inw[::-1])
    ga[inw_o] = ORANGE
    hvox = float(np.median(np.linalg.norm(Qs[:, 1:] - Qs[:, :-1], axis=-1)[avs[:, 1:] & avs[:, :-1]]))
    # ---- side by side
    gap = 30
    H = max(g.shape[0], ga.shape[0]); Wd = g.shape[1] + gap + ga.shape[1]
    sb = Image.new("RGB", (Wd, H + 30), (255, 255, 255))
    sb.paste(Image.fromarray(g), (0, 30)); sb.paste(Image.fromarray(ga), (g.shape[1] + gap, 30))
    d = ImageDraw.Draw(sb)
    d.text((4, 4), "current: sheet lattice (i down, j across)", fill=(0, 0, 0), font=font(16))
    d.text((g.shape[1] + gap + 4, 4), "axis aligned: z up, u = arc length at constant z", fill=(0, 0, 0), font=font(16))
    sq_in = inw.mean()
    im = caption(sb, step, "%s: %s, current and axis aligned renders" % (tag, what),
                 ["left: %s (%d x %d cells)." % (T["what"], ci, cj),
                  "right: the sheet resampled on rows of constant scan z (z up) and columns of 3D arc length at constant z, "
                  "u = 0 on the steepest ascent curve through the window centre; square of %d x %d points centred on the same cell, "
                  "median point spacing %.3f voxels (%.4f mm); grey p1 %.0f to p99 %.0f; orange: border of the lattice window "
                  "(%.1f per cent of the aligned square lies inside it); white: no covered lattice cell nearest" % (
                      S, S, hvox, hvox * VOX, alo, ahi, 100 * sq_in),
                  "same raw volume (20250821151701 level 0, nearest voxel), same grey rule; bars at the lattice step "
                  "(the aligned spacing is within 1 per cent of it)", "Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."])
    files["side_by_side"] = ART + "/%s-%s-current-vs-aligned.png" % (tag, L); im.save(files["side_by_side"])
    row_csv(HERE + "/evidence/renders.csv", dict(
        tag=tag, label=L, what=T["what"], i0=i0, j0=j0, cells_i=ci, cells_j=cj, current_grey_p1="%.0f" % lo,
        current_grey_p99="%.0f" % hi, current_covered_share="%.6f" % cok.mean(),
        current_nm_or_zero_share_of_covered="%.6f" % ((~np.isfinite(CV) | (CV == 0))[cok].mean()),
        aligned_side=S, aligned_grey_p1="%.0f" % alo, aligned_grey_p99="%.0f" % ahi, aligned_covered_share="%.6f" % avs.mean(),
        aligned_median_spacing_vox="%.4f" % hvox, aligned_in_lattice_window_share="%.6f" % sq_in,
        values_from="scratch/values (bw.py)" if have_vals else "sampled here", fetch_gb="%.3f" % gb,
        files=" ".join(os.path.basename(v) for v in files.values())),
        "one row per target: the current (lattice) and axis aligned renders; shares over the image cells")
    # ---- sections
    SECD = {}
    for ax, G in secs.items():
        X = G["X"]
        SV = raw.sample(X[..., 0].ravel(), X[..., 1].ravel(), X[..., 2].ravel()).reshape(X.shape[:2])
        pool = SV[np.isfinite(SV) & (SV > 0)]
        slo, shi = float(np.percentile(pool, 1)), float(np.percentile(pool, 99.5))
        img = rs.to_grey(SV, slo, shi)[::-1]  # b (along the normal) up
        tr = img.copy()
        pa = np.rint(G["A"] - G["a0"]).astype(int); pb = np.rint(G["B"] - G["b0"]).astype(int)
        hgt = img.shape[0]
        on = np.abs(G["D"]) <= 3
        for x, y, o in zip(pa, pb, on):
            yy = hgt - 1 - y
            if 1 <= yy < hgt - 1 and 1 <= x < img.shape[1] - 1:
                tr[yy - 1:yy + 2, x - 1:x + 2] = CYAN if o else ORANGE
        SECD[ax] = dict(img=SV.astype(np.float32), a=(G["A"] - G["a0"]).astype(np.float32), b=(G["B"] - G["b0"]).astype(np.float32),
                        d=G["D"].astype(np.float32), lo=slo, hi=shi)
        stack = np.concatenate([img, np.full((12, img.shape[1], 3), 255, np.uint8), tr], 0)
        sim = Image.fromarray(stack)
        nm = "i" if ax == "i" else "j"
        im = caption(sim, VOX, "%s: %s, cross section along the sheet's %s line through the window centre" % (tag, what, nm),
                     ["organisers' volume, raw masked scan 20250821151701 level 0 (9.362 um voxels), nearest voxel, one voxel per "
                      "pixel; plane through the centre cell (%d, %d) containing the local normal n (up) and u (across), the "
                      "principal direction of the %s line's points seen along n; grey p1 %.0f to p99.5 %.0f" % (
                          G["centre"][0], G["centre"][1], nm, slo, shi),
                      "top: the scan alone; bottom: the same with the sheet's trace, the grown points of the %s line projected "
                      "on the plane, cyan within 3 voxels of the plane, orange farther (out of the plane, not judged here)" % nm,
                      "%d points on the line, %d within 3 voxels; largest distance from the plane %.1f voxels" % (
                          G["npts"], int(on.sum()), float(np.abs(G["D"]).max())), "Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."],
                     width=150)
        p = ART + "/%s-%s-section-%s.png" % (tag, L, nm); im.save(p)
        row_csv(HERE + "/evidence/sections.csv", dict(
            tag=tag, label=L, line=nm, centre_i=G["centre"][0], centre_j=G["centre"][1],
            centre_xyz="%.1f %.1f %.1f" % tuple(G["c"]), normal="%.4f %.4f %.4f" % tuple(G["n"]), u="%.4f %.4f %.4f" % tuple(G["u"]),
            normal_out_of_plane_deg="%.2f" % G["normal_to_plane_deg"], points=G["npts"], points_within_3_vox=int(on.sum()), max_out_of_plane_vox="%.2f" % float(np.abs(G["D"]).max()),
            median_out_of_plane_vox="%.2f" % float(np.median(np.abs(G["D"]))),
            extent_a_vox="%d %d" % (G["a0"], G["a1"]), extent_b_vox="%d %d" % (G["b0"], G["b1"]),
            trace_b_range_vox="%.1f %.1f" % (G["B"].min(), G["B"].max()), grey_p1="%.0f" % slo, grey_p995="%.0f" % shi,
            not_measurable_share="%.6f" % (~np.isfinite(SV)).mean(), png=os.path.basename(p)),
            "one row per cross section: plane through the window centre containing the local normal and the principal direction "
            "of the line's points seen along it (addition 06:31:04Z); trace = the line's grown points projected; DECLARATION.md (2)")
    os.makedirs(HERE + "/scratch/panel-data", exist_ok=True)
    np.savez_compressed(HERE + "/scratch/panel-data/%s.npz" % tag, current=CV.astype(np.float32), current_ok=cok, cur_v2=cv2,
                        cur_sc=csc, cur_a2r=ca2, aligned=AV.astype(np.float32), aligned_ok=avs, aligned_inwin=inw, step=step,
                        **{"sec_%s_%s" % (ax, k): v for ax, d in SECD.items() for k, v in d.items()})
    print(tag, "done", json.dumps({k: os.path.basename(v) for k, v in files.items()}), flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "one":
        one(a[1])
