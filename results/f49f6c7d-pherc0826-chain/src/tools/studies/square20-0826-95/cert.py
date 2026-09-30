#!/usr/bin/env python3
"""cert.py: the CERTIFIED square of a delivered PHerc0826 sheet (DECLARATION.md addition on the certified square,
2026-09-28, director 15:08:01Z). New file, written 2026-09-28T15:2xZ by a coordinator agent. Imports area-0826-90's
area90.py and lamina.py unchanged, never writes under area-0826-90 or chain-0826.

    cert.py one <C40|C80> <seed> <k>   one sheet -> scratch/cert/<C40|C80>-<seed>-S<k>.json (skipped if present)
    cert.py list                        prints «source seed k» for every delivered sheet (C40 of every seed with a squares
                                        file, C80 of this study's regrowths) that has no json yet
    cert.py combine                     every json -> evidence/certified-squares.csv and evidence/certified-ranking.csv

A certified cell is covered and none of: v2 (crossed or jumped, nearest working cell), self conflict at one pitch
(nearest working cell), a2 flagged (area90.prep's a2cell). Every count and square is on the full lattice; mm by the smaller
of step_i_mm, step_j_mm of the sheet's squares row.
"""
import csv, glob, json, os, subprocess, sys, time
import numpy as np

R1 = "/data/scrollagent/runs/rev1"
sys.path.insert(0, R1 + "/area-0826-90/tools")
import area90 as A  # noqa: E402
import lamina as LA  # noqa: E402

ST = R1 + "/square20-0826-95"
CH = A.CHAIN
AREA = R1 + "/area-0826-90"
OUT = ST + "/scratch/cert"
WORK = OUT + "/work"
TOOL = "square20-0826-95/tools/cert.py"
S, V2, CR, SQ, MC, CRL = A.S, A.V2, A.CR, A.SQ, A.MC, A.CRL
NM = "not measurable"


def rows(p):
    if not os.path.exists(p):
        return []
    return list(csv.DictReader([l for l in open(p, newline="") if not l.lstrip('"').startswith("#")]))


def where(src, seed):
    if src == "C40":
        return CH + "/out/%s/C40" % seed, CH + "/evidence/squares-%s.csv" % seed, CH + "/evidence/a2-cluster/%s.csv" % seed
    return ST + "/out/%s/C80" % seed, ST + "/evidence/squares-%s.csv" % seed, ST + "/evidence/a2-cluster/%s.csv" % seed


def lab(src, seed, k):
    return "%s-%s-S%d" % (src, seed, k)


def working(src, seed, k, sqrow):
    """W of a sheet, cached in scratch/cert/work (tmp then replace), after its sha256 check."""
    L = lab(src, seed, k)
    f = WORK + "/%s.npz" % L
    if os.path.isfile(f):
        z = np.load(f)
        return dict(P=z["P"], N=z["N"], ok=z["ok"], inter=z["inter"], si=float(z["si"]), sj=float(z["sj"]), s=int(z["s"]),
                    scroll="PHerc0826", label=L, vox=A.VOX_UM)
    p = where(src, seed)[0] + "/patch_%d.bin" % k
    if A.sha(p) != sqrow["sha256"]:
        raise SystemExit("REFUSED: %s sha256 differs from its squares row" % p)
    px, py, pz, valid, _ = CR.lattice_from_patch(p)
    W = S.working(px, py, pz, valid, "PHerc0826", L)
    os.makedirs(WORK, exist_ok=True)
    tmp = WORK + "/%s.%d.tmp.npz" % (L, os.getpid())
    np.savez_compressed(tmp, P=W["P"], N=W["N"], ok=W["ok"], inter=W["inter"], si=W["si"], sj=W["sj"], s=W["s"])
    os.replace(tmp, f)
    return W


def sq_mm(mask, step):
    b, i, j = SQ.largest_square(mask)
    return [int(b), "%.4f" % (b * step), int(i), int(j)]


def one(src, seed, k):
    L = lab(src, seed, k)
    out = OUT + "/%s.json" % L
    if os.path.isfile(out):
        return
    t0 = time.time()
    d, sqp, a2p = where(src, seed)
    info = dict(source=src, seed=seed, sheet=k, label=L)
    sqr = {int(r["sheet"]): r for r in rows(sqp)}
    p = d + "/patch_%d.bin" % k

    def nm(why):
        info.update(status=NM, why=why, seconds=round(time.time() - t0, 1))
        os.makedirs(OUT, exist_ok=True)
        json.dump(info, open(out + ".part", "w")); os.replace(out + ".part", out)
        print("cert %s: not measurable: %s" % (L, why), flush=True)

    if k not in sqr or sqr[k].get("status") != "measured":
        return nm("squares row absent or not measured")
    r0 = sqr[k]
    if not os.path.isfile(p):
        return nm("patch file absent")
    h = A.sha(p)
    if h != r0["sha256"]:
        return nm("sha256 differs from the squares row")
    px, py, pz, valid, coll = CR.lattice_from_patch(p)
    step = min(float(r0["step_i_mm"]), float(r0["step_j_mm"]))
    hole = sq_mm(valid, step)
    info.update(sha256=h, cells=int(valid.sum()), step_mm="%.6f" % step, squares_row_mm=r0["square_mm_min_step"],
                hole_free_equal_squares_row="yes" if (hole[0], hole[2], hole[3]) == (int(r0["square_cells"]),
                int(r0["square_corner_i"]), int(r0["square_corner_j"])) else "no")
    aj = AREA + "/scratch/sheets/%s.json" % A.label(seed, k)
    reuse = src == "C40" and os.path.isfile(aj) and json.load(open(aj))["sha256"] == h
    a2ok = True
    if reuse:
        La = A.label(seed, k)
        za = np.load(AREA + "/scratch/a2/%s.npz" % La)
        a2cell, hS = za["a2cell"], za["holes"]
        zv = np.load(AREA + "/scratch/v2/%s.npz" % La)
        CROSS, JUMP, s = zv["crossed"], zv["jumped"], int(zv["stride"])
        SELF = np.load(AREA + "/scratch/lamina/%s.npz" % La)["self_conflict"]
        a2ok = json.load(open(aj)).get("a2_equal") == "yes"
        npart = "area-0826-90"
        if a2cell.shape != valid.shape or CROSS.shape != SELF.shape:
            return nm("area-0826-90 mask shapes differ from the lattice")
        mask_src = "reused from area-0826-90 (sha256 equal to its sheets json)"
    else:
        W = working(src, seed, k, r0)
        s = W["s"]
        # a2, area90.prep's calls
        A.D.selftest_passed(); MC.selftest_ok()
        T, _ = MC.verdict_row("a2")
        Sd, _ = CRL.read_S(); Sv = Sd["a2"]
        gflag, meas, fl = A.a2_grid(px, py, pz, valid, T)
        gsize, _ = CRL.clusters(gflag)
        hS, kept = CRL.rule_holes(gsize, Sv, valid)
        a2cell = (A.block_mask(gflag, valid.shape, MC.STRIDE) | hS) & valid
        ref = {int(r["sheet"]): r for r in rows(a2p)}.get(k)
        a2ok = bool(ref) and ref.get("sha256") == h and str(meas) == ref["a2_measurable"] and str(fl) == ref["a2_flagged"] \
            and str(int(kept.sum())) == ref["a2_kept_points"]
        info.update(a2_measurable=meas, a2_flagged=fl, a2_kept_points=int(kept.sum()),
                    a2_reference=("%s/%s/%s" % (ref["a2_measurable"], ref["a2_flagged"], ref["a2_kept_points"])) if ref else "absent")
        # v2 against the 800 by keys and the siblings
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
                parts.append(working(src, seed, kk, sqr[kk]))
        for B in parts:
            r = V2.pair_v2(W, B)
            if r is None:
                continue
            c_, j_ = V2.marks(r, L2c, L2j)
            CROSS |= c_; JUMP |= j_
        cs, ia, ja = LA.conflicts(W, W, LA.pitch(), True)
        SELF = np.zeros(sh, bool); SELF[ia[cs], ja[cs]] = True
        npart = "%d of the 800 and %d siblings" % (n800, len(parts) - n800)
        mask_src = "computed here"
    gi, gj = A.nearest_block(valid.shape, s, CROSS.shape)

    def full(m):
        return m[gi[:, None], gj[None, :]] & valid
    v2 = full(CROSS | JUMP); sc = full(SELF); a2 = a2cell & valid; a2r = hS & valid
    cert = valid & ~v2 & ~sc & ~a2r
    strict = valid & ~v2 & ~sc & ~a2
    ref2 = {int(r["sheet"]): r for r in rows(a2p)}.get(k, {})
    info.update(status="measured", masks=mask_src, partners=npart, working_stride=s,
                v2_cells=int(v2.sum()), v2_crossed_cells=int(full(CROSS).sum()), v2_jumped_cells=int(full(JUMP).sum()),
                self_conflict_cells=int(sc.sum()), a2_cells=int(a2.sum()), a2_rule_cells=int(a2r.sum()), certified_cells=int(cert.sum()),
                a2_house_rule_square_mm=ref2.get("a2_cluster_rule_square_mm", "absent"),
                a2_reference_equal="yes" if a2ok else "no",
                hole_free=hole, avoiding_v2=sq_mm(valid & ~v2, step), avoiding_self_conflict=sq_mm(valid & ~sc, step),
                avoiding_a2=sq_mm(valid & ~a2, step), avoiding_a2_rule=sq_mm(valid & ~a2r, step),
                certified=sq_mm(cert, step) if a2ok else [NM, NM, -1, -1],
                certified_strict=sq_mm(strict, step) if a2ok else [NM, NM, -1, -1],
                seconds=round(time.time() - t0, 1))
    os.makedirs(OUT, exist_ok=True)
    json.dump(info, open(out + ".part", "w")); os.replace(out + ".part", out)
    print("cert %s: hole-free %s, v2 %s, self %s, a2 rule %s (house %s), a2 all %s, certified %s, strict %s mm (%s, %.0f s)" % (
        L, hole[1], info["avoiding_v2"][1], info["avoiding_self_conflict"][1], info["avoiding_a2_rule"][1],
        info["a2_house_rule_square_mm"], info["avoiding_a2"][1], info["certified"][1], info["certified_strict"][1],
        "reused" if reuse else "computed", info["seconds"]), flush=True)


def sheets_all():
    out = []
    for p in sorted(glob.glob(CH + "/evidence/squares-PHerc0826-seed*.csv")):
        seed = os.path.basename(p)[len("squares-"):-4]
        for r in rows(p):
            out.append(("C40", seed, int(r["sheet"])))
    for p in sorted(glob.glob(ST + "/evidence/squares-PHerc0826-seed*.csv")):
        seed = os.path.basename(p)[len("squares-"):-4]
        for r in rows(p):
            out.append(("C80", seed, int(r["sheet"])))
    return out


COLS = ["source", "seed", "sheet", "status", "cells", "step_mm", "working_stride", "hole_free_square_mm", "hole_free_equal_squares_row",
        "v2_avoiding_square_mm", "self_conflict_avoiding_square_mm", "a2_rule_square_mm", "a2_rule_equal_house_column",
        "a2_all_flagged_avoiding_square_mm", "certified_square_mm", "certified_strict_square_mm",
        "certified_square_cells", "certified_corner_i", "certified_corner_j", "v2_cells", "v2_crossed_cells", "v2_jumped_cells",
        "self_conflict_cells", "a2_rule_cells", "a2_all_flagged_cells", "certified_cells", "a2_reference_equal", "masks", "partners", "why"]


def eqh(j):
    h = j.get("a2_house_rule_square_mm", "absent")
    try:
        return "yes" if abs(float(h) - float(j["avoiding_a2_rule"][1])) < 5e-4 else "no"   # the house mm uses the unrounded step
    except ValueError:
        return "no house row"


def combine():
    R = []
    for f in sorted(glob.glob(OUT + "/*.json")):
        j = json.load(open(f))
        if j["status"] != "measured":
            R.append([j["source"], j["seed"], j["sheet"], NM] + [""] * (len(COLS) - 5) + [j.get("why", "")])
            continue
        R.append([j["source"], j["seed"], j["sheet"], "measured", j["cells"], j["step_mm"], j["working_stride"], j["hole_free"][1],
                  j["hole_free_equal_squares_row"], j["avoiding_v2"][1], j["avoiding_self_conflict"][1], j["avoiding_a2_rule"][1],
                  eqh(j), j["avoiding_a2"][1],
                  j["certified"][1], j["certified_strict"][1], j["certified"][0], j["certified"][2], j["certified"][3], j["v2_cells"], j["v2_crossed_cells"],
                  j["v2_jumped_cells"], j["self_conflict_cells"], j["a2_rule_cells"], j["a2_cells"], j["certified_cells"], j["a2_reference_equal"],
                  j["masks"], j["partners"], ""])
    t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    head = ("# written by %s combine at %s: one row per delivered PHerc0826 sheet (chain-0826 C40, this study's C80 g 72000 "
            "regrowths); certified square = square.py largest_square on the cells that are covered and not v2 (crossed or jumped), "
            "not self conflict at one pitch, not an a2 cluster rule hole (certified_strict: not any a2 flagged block); every count and square on the full lattice, mm by the smaller step; "
            "definition in square20-0826-95/DECLARATION.md addition on the certified square\n" % (TOOL, t))
    with open(ST + "/evidence/certified-squares.csv.part", "w", newline="") as f:
        f.write(head)
        w = csv.writer(f, lineterminator="\n"); w.writerow(COLS); w.writerows(R)
    os.replace(ST + "/evidence/certified-squares.csv.part", ST + "/evidence/certified-squares.csv")
    m = [r for r in R if r[3] == "measured" and r[14] != NM]
    m.sort(key=lambda r: -float(r[14]))
    with open(ST + "/evidence/certified-ranking.csv.part", "w", newline="") as f:
        f.write("# written by %s combine at %s: the ten largest certified squares of evidence/certified-squares.csv, %d measured "
                "sheets of %d rows\n" % (TOOL, t, len(m), len(R)))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["rank", "source", "seed", "sheet", "certified_square_mm", "hole_free_square_mm", "v2_avoiding_square_mm",
                    "self_conflict_avoiding_square_mm", "a2_rule_square_mm", "certified_strict_square_mm"])
        for n, r in enumerate(m[:10], 1):
            w.writerow([n, r[0], r[1], r[2], r[14], r[7], r[9], r[10], r[11], r[15]])
    os.replace(ST + "/evidence/certified-ranking.csv.part", ST + "/evidence/certified-ranking.csv")
    print("combined %d rows, %d measured; best certified %s" % (len(R), len(m), m[0][:3] + [m[0][14]] if m else "none"))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "one":
        one(a[1], a[2], int(a[3]))
    elif a[0] == "list":
        for src, seed, k in sheets_all():
            if not os.path.isfile(OUT + "/%s.json" % lab(src, seed, k)):
                print(src, seed, k)
    elif a[0] == "combine":
        combine()
