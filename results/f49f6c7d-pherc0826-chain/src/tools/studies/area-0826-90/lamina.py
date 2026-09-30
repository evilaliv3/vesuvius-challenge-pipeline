#!/usr/bin/env python3
"""lamina.py: one lamina by pitch conflicts (DECLARATION.md addition on the director's follow ups of 2026-09-27T18:12:07Z).

    lamina.py selftest          synthetic: a flat sheet has no self conflict; a sheet with a parallel copy 15 voxels away
                                conflicts with it; a coincident copy does not; a folded sheet has self conflicts
    lamina.py sheet <seed> <k>  self conflict and conflicts against every partner with foot cells (map CSV)
    lamina.py combine           evidence/self-conflicts.csv, conflicts.csv, one-lamina.csv
"""
import csv, glob, json, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import area90 as A
A.TOOL = "area-0826-90/tools/lamina.py"  # the CSV header names this tool
import numpy as np
from scipy.spatial import cKDTree

S = A.S
TOOL = "area-0826-90/tools/lamina.py"
OUTD = A.SCR + "/lamina"


def pitch():
    for r in A.read_rows(A.EV + "/pitch.csv"):
        if r["bin_lo_vox"] == "pitch_vox":
            return float(r["bin_hi_vox"])
    raise SystemExit("REFUSED: no pitch row")


def cells(W):
    ii, jj = np.nonzero(W["ok"])
    return ii, jj, W["P"][ii, jj].astype(np.float64), W["N"][ii, jj].astype(np.float64)


def conflicts(Wa, Wb, p, same):
    """bool over Wa's ok cells: in pitch conflict with some cell of Wb."""
    ia, ja, Pa, Na = cells(Wa)
    ib, jb, Pb, Nb = cells(Wb)
    out = np.zeros(len(Pa), bool)
    if len(Pa) == 0 or len(Pb) == 0:
        return out, ia, ja
    r = 1.5 * p
    lo, hi = Pb.min(0) - r, Pb.max(0) + r
    sel = np.flatnonzero(np.all((Pa >= lo) & (Pa <= hi), 1))
    if len(sel) == 0:
        return out, ia, ja
    ta = cKDTree(Pa[sel]); tb = cKDTree(Pb)
    M = ta.sparse_distance_matrix(tb, r, output_type="ndarray")
    if len(M) == 0:
        return out, ia, ja
    a = sel[M["i"]]; b = M["j"]
    v = Pb[b] - Pa[a]
    na = Na[a]
    along = (v * na).sum(1)
    lat = np.linalg.norm(v - along[:, None] * na, axis=1)
    ok = (np.abs(along) >= 0.5 * p) & (np.abs(along) <= 1.5 * p) & (lat <= max(Wa["si"], Wa["sj"])) & \
         (np.abs((na * Nb[b]).sum(1)) >= S.COS_CO)
    if same:
        geo = np.hypot((ia[a] - ib[b]) * Wa["si"], (ja[a] - jb[b]) * Wa["sj"])
        ok &= geo > 3 * p
    out[a[ok]] = True
    return out, ia, ja


def selftest():
    rows, allok = [], True

    def W_of(P, ok=None):
        ni, nj = P.shape[:2]
        ok = np.ones((ni, nj), bool) if ok is None else ok
        return S.working(P[..., 0], P[..., 1], P[..., 2], ok, "PHerc0826", "t")

    p = 15.125
    Pa = A.UA.plane(80, 80)
    Wa = W_of(Pa)
    Wc = W_of(A.UA.plane(80, 80, normal_shift=15.0))
    Wd = W_of(A.UA.plane(80, 80))
    c1, _, _ = conflicts(Wa, Wa, p, True)
    c2, _, _ = conflicts(Wa, Wc, p, False)
    c3, _, _ = conflicts(Wa, Wd, p, False)
    # a folded sheet: rows 0..79 on the plane, rows 80..159 back over it 15 voxels away (a hairpin)
    n = np.array([1.0, 0.7, 0.4]); n /= np.linalg.norm(n)
    top = A.UA.plane(80, 80, normal_shift=15.0)[::-1]
    F = np.concatenate([Pa, top], 0)
    Wf = W_of(F)
    c4, _, _ = conflicts(Wf, Wf, p, True)
    for case, got, want in (("flat sheet, self", c1.sum(), 0), ("parallel copy 15 voxels", c2.mean(), "> 0.9"),
                            ("coincident copy", c3.sum(), 0), ("hairpin fold, self", c4.mean(), "> 0.5")):
        ok = (got == want) if isinstance(want, int) else (got > float(want[2:]))
        rows.append([case, want, "%s" % got, "yes" if ok else "no"]); allok &= bool(ok)
    return allok, rows


def sheet(a, k):
    L = A.label(a, k)
    out = OUTD + "/%s.json" % L
    if os.path.isfile(out):
        return
    p = pitch()
    Wa = A.load_work(L)
    cs, ia, ja = conflicts(Wa, Wa, p, True)
    cell = Wa["si"] * Wa["sj"]
    part = {}
    for r in A.read_rows(A.EV + "/v2/%s.csv" % L):
        if int(r["foot_cells"]) == 0:
            continue
        c, _, _ = conflicts(Wa, A.load_work(r["partner"]), p, False)
        if c.any():
            part[r["partner"]] = int(c.sum())
    os.makedirs(OUTD, exist_ok=True)
    m = np.zeros(Wa["ok"].shape, bool); m[ia[cs], ja[cs]] = True
    np.savez_compressed(OUTD + "/%s.tmp.npz" % L, self_conflict=m)
    os.replace(OUTD + "/%s.tmp.npz" % L, OUTD + "/%s.npz" % L)
    json.dump(dict(label=L, working_cells=int(len(cs)), self_conflict_cells=int(cs.sum()), cell_vox2=cell,
                   partners=part), open(out + ".part", "w"))
    os.replace(out + ".part", out)
    print("lamina %s: self %d of %d, conflicting partners %d" % (L, cs.sum(), len(cs), len(part)), flush=True)


def combine():
    import multiprocessing as mp
    ok, _ = selftest()
    if not ok:
        raise SystemExit("REFUSED: self test")
    p = pitch()
    SL = A.sheets()
    labels = [A.label(a, k) for a, k in SL]
    pos = {L: i for i, L in enumerate(labels)}
    seed_of = {A.label(a, k): a for a, k in SL}
    J = {L: json.load(open(OUTD + "/%s.json" % L)) for L in labels}
    AMIN = S.A_CO
    wrap = {L for L in labels if J[L]["self_conflict_cells"] * J[L]["cell_vox2"] >= AMIN}
    conf = {L: set() for L in labels}
    crow = []
    for L in labels:
        for M, c in J[L]["partners"].items():
            area = c * J[L]["cell_vox2"]
            crow.append([L, M, c, "%.1f" % area, "yes" if area >= AMIN else "no"])
            if area >= AMIN:
                conf[L].add(M); conf[M].add(L)
    A.write_csv(A.EV + "/conflicts.csv", "pitch conflicts of each sheet against each partner with foot cells: cells of the "
                "sheet (working lattice) with a partner cell at 0.5 to 1.5 pitch (%.3f voxels) along its normal, lateral "
                "within one working step, normals within 20 degrees; conflicting when the area is at least %g square voxels"
                % (p, AMIN), ["sheet", "partner", "conflict_cells", "conflict_vox2", "conflicting"], crow)
    A.write_csv(A.EV + "/self-conflicts.csv", "self conflicts (the same test within one sheet, cells more than 3 pitches "
                "apart on its lattice); wrapping when the area is at least %g square voxels" % AMIN,
                ["sheet", "working_cells", "self_conflict_cells", "self_conflict_vox2", "wrapping"],
                [[L, J[L]["working_cells"], J[L]["self_conflict_cells"],
                  "%.1f" % (J[L]["self_conflict_cells"] * J[L]["cell_vox2"]), "yes" if L in wrap else "no"]
                 for L in labels])
    # join edges of stitch: coinciding both orders, no v2 marks
    rows = {}
    for L in labels:
        for r in A.read_rows(A.EV + "/v2/%s.csv" % L):
            rows[(L, r["partner"])] = r
    edges = []
    for (L, M), r in rows.items():
        if pos[L] >= pos[M] or (M, L) not in rows:
            continue
        q = rows[(M, L)]
        if int(r["coinciding_cells"]) > 0 and int(q["coinciding_cells"]) > 0 and \
                sum(int(x[c]) for x in (r, q) for c in ("v2_crossing_cells", "v2_jump_cells")) == 0:
            edges.append((min(float(r["coinciding_vox2"]), float(q["coinciding_vox2"])), L, M))
    edges.sort(key=lambda e: (-e[0], e[1], e[2]))
    grp = {L: {L} for L in labels if L not in wrap}
    gof = {L: L for L in grp}
    gconf = {L: set(conf[L]) for L in grp}
    refused = 0
    for _, L, M in edges:
        if L in wrap or M in wrap:
            continue
        g1, g2 = gof[L], gof[M]
        if g1 == g2:
            continue
        if gconf[g1] & grp[g2]:
            refused += 1
            continue
        if len(grp[g1]) < len(grp[g2]):
            g1, g2 = g2, g1
        grp[g1] |= grp[g2]; gconf[g1] |= gconf[g2]
        for x in grp[g2]:
            gof[x] = g1
        del grp[g2]; del gconf[g2]
    # areas: load clean cells as combine does, for the members of the top groups and every sheet for (3)
    with mp.get_context("fork").Pool(6) as pool:
        got = pool.map(A.load_sheet, SL, chunksize=4)
    infos = [g[0] for g in got]; A.G["P"] = [g[1] for g in got]; AR = [g[2] for g in got]
    A.G["labels"] = labels
    A.G["step"] = [min(i["step_i_vox"], i["step_j_vox"]) for i in infos]
    del got
    per = {i["label"]: i for i in infos}
    G = sorted(grp.values(), key=lambda m: -sum(per[x]["clean_mm2"] for x in m))
    out = []
    best_v = 0.0
    for rank, m in enumerate(G):
        if rank >= 5 and sum(per[x]["clean_mm2"] for x in m) < best_v:
            break
        ms = sorted(pos[x] for x in m)
        if len(ms) > 1:
            earlier = {n: [x for x in ms if x < n] for n in ms}
            res = A.run_dedup(ms, earlier)
            half = sum(float(AR[n][~res[n][0]].sum()) for n in ms)
            one = sum(float(AR[n][~res[n][1]].sum()) for n in ms)
        else:
            half = one = float(AR[ms[0]].sum())
        bm, cs, _, _ = A.UA.union_of([(A.G["P"][n], AR[n]) for n in ms])
        v = min(half, one, bm)
        best_v = max(best_v, v)
        inside = sum(1 for x in m for y in conf[x] if y in m) // 2
        same = sum(1 for x in m for y in m if x < y and seed_of[x] == seed_of[y])
        sq = max(m, key=lambda x: per[x]["square_clean_mm"])
        seeds = sorted({seed_of[x] for x in m})
        out.append(["group", rank + 1, len(m), len(seeds), "%.4f" % (cs / 100), "%.4f" % (half / 100),
                    "%.4f" % (one / 100), "%.4f" % (bm / 100), "%.4f" % (v / 100), "%.4f" % (v / 100 / 365.0),
                    "%.4f" % per[sq]["square_clean_mm"], sq, inside, same,
                    " ".join(s.replace("PHerc0826-", "") for s in seeds), " ".join(sorted(m))])
        print("group %d: %d sheets, %d seeds, %.2f cm2, conflicts inside %d, same seed pairs %d" % (
            rank + 1, len(m), len(seeds), v / 100, inside, same), flush=True)
    # (3) one lamina piece
    best = None
    for n, (a, k) in enumerate(SL):
        L = labels[n]
        px, py, pz, valid, _ = A.CR.lattice_from_patch(A.patch(a, k))
        area, _ = A.UA.local_area(px, py, pz, valid)
        a2 = np.load(A.SCR + "/a2/%s.npz" % L)["a2cell"]
        z = np.load(A.SCR + "/v2/%s.npz" % L)
        s = int(z["stride"])
        v2 = A.block_mask(z["crossed"] | z["jumped"], valid.shape, s) & valid
        sc = A.block_mask(np.load(OUTD + "/%s.npz" % L)["self_conflict"], valid.shape, s) & valid
        clean = valid & ~a2 & ~v2 & ~sc
        c, ar = A.largest_piece(clean, area)
        if best is None or ar > best[2]:
            best = (L, c, ar, int(sc.sum()), L in wrap)
    out.append(["piece", 1, 1, 1, "", "", "", "", "%.4f" % (best[2] / 100), "%.4f" % (best[2] / 100 / 365.0), "",
                best[0], 0, 0, "", "%s: %d cells; self conflict cells removed on the sheet %d; sheet wrapping %s" % (
                    best[0], best[1], best[3], "yes" if best[4] else "no")])
    A.write_csv(A.EV + "/one-lamina.csv", "one lamina by pitch conflicts (pitch %.3f voxels, pitch.csv): groups = sheets "
                "joined by the stitch edges (coinciding both orders, no v2 line) in decreasing coinciding area, a merge "
                "refused when any member of one conflicts with any member of the other (%d refusals), wrapping sheets (%d) "
                "left out; clean unique = smallest of three dedup rules; conflicts_inside must be 0; piece = largest 4 "
                "neighbour clean component of one sheet after removing its self conflict cells. One lamina only up to what "
                "a conflict over %g square voxels within 1.5 pitch can see; Stevens' 365 is a sum of flattened components "
                "that span windings; groups are listed in decreasing summed clean area until the summed area falls under the best unique area found, so no unlisted group can exceed it" % (p, refused, len(wrap), AMIN),
                ["kind", "rank", "sheets", "seeds", "clean_summed_cm2", "half_step_cm2", "one_step_cm2", "binmax_cm2",
                 "clean_unique_cm2", "over_365", "square_mm", "square_or_piece_sheet", "conflicts_inside",
                 "same_seed_pairs", "seed_list", "members"], out)
    print("piece %s %.4f cm2; wrapping sheets %d; refused merges %d" % (best[0], best[2] / 100, len(wrap), refused))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "selftest":
        ok, rows = selftest()
        A.write_csv(A.EV + "/lamina-selftest.csv", "self test of lamina.py conflicts on synthetic working lattices, pitch "
                    "15.125", ["case", "expected", "got", "passed"], rows + [["all", "yes", "yes" if ok else "no",
                                                                               "yes" if ok else "no"]])
        print(rows, ok); sys.exit(0 if ok else 1)
    A.gate()
    if a[0] == "sheet":
        sheet(a[1], int(a[2]))
    elif a[0] == "combine":
        combine()
