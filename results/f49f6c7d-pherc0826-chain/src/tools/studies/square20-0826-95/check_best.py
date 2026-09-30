#!/usr/bin/env python3
"""check_best.py <seed> <source_dir> <squares_csv> <a2_cluster_csv> <sheet> <label>: the flag masks of one delivered PHerc0826
sheet, computed with tools/cert.py's own method, for tools/texture_best.py. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.

New file, written 2026-09-28T17:4xZ by a coordinator agent on the director's order of 17:39:46Z (best squares for the owner).
It is cert.py one()'s «computed here» branch, parameterized, with these changes and no others:
  1. the sheet is named by arguments (seed, folder of patch_<k>.bin, squares CSV, a2 cluster CSV, sheet, label) instead of
     cert.py's <C40|C80> naming;
  2. the working lattice cache is scratch/check_best/work (cert.py's scratch/cert/work is read if it holds the sheet, never
     written); nothing is written under scratch/cert, chain-0826 or area-0826-90;
  3. the full lattice masks (covered, v2 crossed, v2 jumped, self conflict, a2 flagged, a2 cluster rule holes, certified) are
     saved to scratch/check_best/<label>.npz, and the counts and squares to evidence/check_best-<label>.csv;
  4. when evidence/certified-squares.csv holds a row for (C40, seed, sheet), every count and the certified square are
     compared with it, one column each (equal yes/no).
The check95.py method (v2 against the 800 of area-0826-90 by keys plus the siblings, lamina.conflicts at one pitch, nearest
working cell) is the same as cert.py's; cert.py adds the a2 masks.
"""
import csv, os, subprocess, sys, time
import numpy as np

R1 = "/data/scrollagent/runs/rev1"
sys.path.insert(0, R1 + "/area-0826-90/tools")
sys.path.insert(0, R1 + "/square20-0826-95/tools")
import area90 as A  # noqa: E402
import lamina as LA  # noqa: E402
import cert as CE  # noqa: E402  (imported for rows and sq_mm only; its main does not run)

ST = R1 + "/square20-0826-95"
OUT = ST + "/scratch/check_best"
WORK = OUT + "/work"
TOOL = "square20-0826-95/tools/check_best.py (cert.py one(), computed branch, parameterized)"
S, V2, CR, SQ, MC, CRL = A.S, A.V2, A.CR, A.SQ, A.MC, A.CRL


def working(d, k, sqrow, seed):
    """W of a sheet as cert.py.working names it (C40-<seed>-S<k>): read from cert.py's cache or ours, else built here."""
    L = "C40-%s-S%d" % (seed, k)
    for f in (CE.WORK + "/%s.npz" % L, WORK + "/%s.npz" % L):
        if os.path.isfile(f):
            z = np.load(f)
            return dict(P=z["P"], N=z["N"], ok=z["ok"], inter=z["inter"], si=float(z["si"]), sj=float(z["sj"]), s=int(z["s"]),
                        scroll="PHerc0826", label=L, vox=A.VOX_UM)
    p = d + "/patch_%d.bin" % k
    if A.sha(p) != sqrow["sha256"]:
        raise SystemExit("REFUSED: %s sha256 differs from its squares row" % p)
    px, py, pz, valid, _ = CR.lattice_from_patch(p)
    W = S.working(px, py, pz, valid, "PHerc0826", L)
    os.makedirs(WORK, exist_ok=True)
    tmp = WORK + "/%s.%d.tmp.npz" % (L, os.getpid())
    np.savez_compressed(tmp, P=W["P"], N=W["N"], ok=W["ok"], inter=W["inter"], si=W["si"], sj=W["sj"], s=W["s"])
    os.replace(tmp, WORK + "/%s.npz" % L)
    return W


def main():
    seed, d, sqp, a2p, k, label = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), sys.argv[6]
    t0 = time.time()
    A.check_voxel()
    sqr = {int(r["sheet"]): r for r in CE.rows(sqp)}
    r0 = sqr[k]
    p = d + "/patch_%d.bin" % k
    h = A.sha(p)
    if h != r0["sha256"]:
        raise SystemExit("REFUSED: %s sha256 differs from its squares row" % p)
    px, py, pz, valid, coll = CR.lattice_from_patch(p)
    step = min(float(r0["step_i_mm"]), float(r0["step_j_mm"]))
    hole = CE.sq_mm(valid, step)
    W = working(d, k, r0, seed)
    s = W["s"]
    A.D.selftest_passed(); MC.selftest_ok()
    T, _ = MC.verdict_row("a2")
    Sd, _ = CRL.read_S(); Sv = Sd["a2"]
    gflag, meas, fl = A.a2_grid(px, py, pz, valid, T)
    gsize, _ = CRL.clusters(gflag)
    hS, kept = CRL.rule_holes(gsize, Sv, valid)
    a2cell = (A.block_mask(gflag, valid.shape, MC.STRIDE) | hS) & valid
    ref = {int(r["sheet"]): r for r in CE.rows(a2p)}.get(k)
    a2ok = bool(ref) and ref.get("sha256") == h and str(meas) == ref["a2_measurable"] and str(fl) == ref["a2_flagged"] \
        and str(int(kept.sum())) == ref["a2_kept_points"]
    L2c, L2j, _ = A.thresholds()
    ks = np.unique(S.keys_of(W["P"][W["ok"]].astype(np.float64)))
    idx = A.index()
    cand = set()
    for q in S.dilate_keys(ks):
        for M in idx.get(int(q), ()):
            cand.add(M)
    sh = W["ok"].shape
    CROSS = np.zeros(sh, bool); JUMP = np.zeros(sh, bool)
    parts = [A.load_work(M) for M in sorted(cand)]
    n800 = len(parts)
    for kk in sorted(sqr):
        if kk != k and sqr[kk].get("status") == "measured" and os.path.isfile(d + "/patch_%d.bin" % kk):
            parts.append(working(d, kk, sqr[kk], seed))
    for B in parts:
        r = V2.pair_v2(W, B)
        if r is None:
            continue
        c_, j_ = V2.marks(r, L2c, L2j)
        CROSS |= c_; JUMP |= j_
    cs, ia, ja = LA.conflicts(W, W, LA.pitch(), True)
    SELF = np.zeros(sh, bool); SELF[ia[cs], ja[cs]] = True
    gi, gj = A.nearest_block(valid.shape, s, CROSS.shape)

    def full(m):
        return m[gi[:, None], gj[None, :]] & valid
    v2c, v2j = full(CROSS), full(JUMP)
    v2 = v2c | v2j; sc = full(SELF); a2 = a2cell & valid; a2r = hS & valid
    cert = valid & ~v2 & ~sc & ~a2r
    cq = CE.sq_mm(cert, step)
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(OUT + "/%s.npz" % label, valid=valid, v2c=v2c, v2j=v2j, self_conflict=sc, a2=a2, a2_rule=a2r, cert=cert,
                        hole_free=np.array(hole[:1] + hole[2:]), certified=np.array(cq[:1] + cq[2:]))
    got = dict(cells=int(valid.sum()), v2_cells=int(v2.sum()), v2_crossed_cells=int(v2c.sum()), v2_jumped_cells=int(v2j.sum()),
               self_conflict_cells=int(sc.sum()), a2_rule_cells=int(a2r.sum()), a2_all_flagged_cells=int(a2.sum()),
               certified_cells=int(cert.sum()), certified_square_cells=cq[0], certified_corner_i=cq[2], certified_corner_j=cq[3],
               certified_square_mm=cq[1], hole_free_square_mm=hole[1], working_stride=s)
    crow = [r for r in CE.rows(ST + "/evidence/certified-squares.csv")
            if r["source"] == "C40" and r["seed"] == seed and r["sheet"] == str(k)]
    tt = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(ST + "/evidence/check_best-%s.csv" % label, "w", newline="") as f:
        f.write('"# written by %s at %s: %s sheet %d (%s, sha256 %s); masks by cert.py one()\'s computed branch (partners %d of the 800 '
                'and %d siblings; a2 reference equal %s); every count on the full lattice; certified_squares_csv is the value of '
                'evidence/certified-squares.csv (C40 row) or absent; %d s"\n'
                % (TOOL, tt, seed, k, d, h[:16], n800, len(parts) - n800, "yes" if a2ok else "no", time.time() - t0))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["label", "quantity", "computed_here", "certified_squares_csv", "equal"])
        for q, v in got.items():
            cv = crow[0][q] if crow else "absent"
            w.writerow([label, q, v, cv, ("yes" if str(v) == cv else "no") if crow else "no row"])
        w.writerow([label, "a2_reference_equal", "yes" if a2ok else "no", crow[0]["a2_reference_equal"] if crow else "absent", ""])
    print(label, got, "cert row" if crow else "no cert row", flush=True)


if __name__ == "__main__":
    main()
