#!/usr/bin/env python3
"""render-routes-0826/tools/old_square.py: the R2b 30 mm square of seed6273 square centre (801 cells, 30.0063 mm, the whole
R2b crop) measured on the R2c 60 mm surface with the same check code (director 14:53:12Z). R2c equals R2b node for node inside
the old crop (evidence/r2c-vs-r2b.csv), so the old square sits in the R2c crop at the offset of the two crops' native boxes,
times 5. Per check, which old square cells are flagged and where the cause lies:
  v2 (against our 800 and against the other R2b crops): per partner sheet, the marked old square cells, and the marked line's
      cells inside and outside the old crop (a crossing line becomes long enough to mark only when it extends outside);
  self conflict (a end and b end, pairwise.py's conflict_pairs, the pairs of lamina.conflicts): flagged old square cells and
      whether their partner cell lies inside or outside the old crop;
  a2 cluster rule: flagged old square cells, and the size of their clusters inside and outside the old crop;
  holes.
-> evidence/old-square-on-r2c.csv, one row per check (and per v2 partner)."""
import csv, json, subprocess, sys
import numpy as np
H = "/data/scrollagent/runs/rev1/render-routes-0826"
R1D = "/data/scrollagent/runs/rev1"
sys.path.insert(0, H + "/tools")
import routes as RT  # noqa: E402
sys.path.insert(0, R1D + "/pairwise-cert-0826/tools")
import pairwise as PWM  # noqa: E402
A, LA, S, MC, CRL, V2 = RT.A, RT.LA, RT.S, RT.MC, RT.CRL, RT.V2
N = "PHerc0826-seed6273-squarecentre"
jb = json.load(open(H + "/scratch/rows/R2bnative-%s.json" % N)); jc = json.load(open(H + "/scratch/rows/R2cnative-%s.json" % N))
cb = list(map(int, jb["crop_native"].split())); cc = list(map(int, jc["crop_native"].split()))
b = int(jb["largest_certified_square_cells"]); bi0, bj0 = map(int, jb["largest_certified_square_corner"].split())
# node grids differ between the runs (322 against 402 nodes a side): the same node is at the same offset from the node nearest
# the start (evidence/r2c-vs-r2b.csv); the start node is at crop start + 80 (R2b) and + 160 (R2c), both crops unclipped here
assert cb[1] - cb[0] == 160 and cb[3] - cb[2] == 160 and cc[1] - cc[0] == 320 and cc[3] - cc[2] == 320, "a crop is clipped"
oi, oj = (160 - 80) * 5 + bi0, (160 - 80) * 5 + bj0
P, V = RT.surface("R2cnative", N)[:2]
OLD = np.zeros(V.shape, bool); OLD[oi:oi + b, oj:oj + b] = True
Pb_, Vb_ = RT.surface("R2bnative", N)[:2]
same = float(np.nanmax(np.abs(P[oi:oi + b, oj:oj + b] - Pb_[bi0:bi0 + b, bj0:bj0 + b]))) if b else float("nan")
same_valid = bool((V[oi:oi + b, oj:oj + b] == Vb_[bi0:bi0 + b, bj0:bj0 + b]).all())
CROP = np.zeros(V.shape, bool)
CROP[400:400 + 801, 400:400 + 801] = True   # the old R2b crop (161 native nodes, 801 upsampled cells) on the R2c crop
px, py, pz = [np.where(V, P[..., k], 0.0) for k in range(3)]
W = S.working(px, py, pz, V, "PHerc0826", "r2c")
s = W["s"]
gi, gj = A.nearest_block(V.shape, s, W["ok"].shape)


def full(m):
    return m[gi[:, None], gj[None, :]] & V


rows = []
t = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
base = dict(utc=t, surface=N, old_square="corner %d %d, %d cells on the R2c crop (R2b corner %d %d); check: max |R2c - R2b| %.4f vox, valid masks equal %s" % (
    oi, oj, b, bi0, bj0, same, "yes" if same_valid else "no"))
# holes
rows.append(dict(base, check="holes", partner="", flagged_old_square_cells=int((OLD & ~V).sum()), cause_inside_old_crop="", cause_outside_old_crop="",
                 note="uncovered cells of the old square"))
# v2 per partner
L2c, L2j, _ = A.thresholds()
ks = np.unique(S.keys_of(W["P"][W["ok"]].astype(np.float64)))
idx = A.index(); cand = set()
for q in S.dilate_keys(ks):
    for M in idx.get(int(q), ()):
        cand.add(M)
parts = [(M, A.load_work(M)) for M in sorted(cand)]
for r_ in RT.rows(H + "/evidence/r2-starts.csv"):
    if r_["start"] == N:
        continue
    Po, Vo = RT.surface("R2bnative", r_["start"])[:2]
    qx, qy, qz = [np.where(Vo, Po[..., k], 0.0) for k in range(3)]
    parts.append(("R2b " + r_["start"], S.working(qx, qy, qz, Vo, "PHerc0826", r_["start"])))
tot = 0
for M, B in parts:
    r = V2.pair_v2(W, B)
    if r is None:
        continue
    c_, j_ = V2.marks(r, L2c, L2j)
    m = full(c_ | j_)
    n_old = int((m & OLD).sum())
    if n_old == 0:
        continue
    tot += n_old
    rows.append(dict(base, check="v2 (crossed or jumped)", partner=M, flagged_old_square_cells=n_old,
                     cause_inside_old_crop=int((m & CROP).sum()), cause_outside_old_crop=int((m & ~CROP).sum()),
                     note="cells of the marked lines of this partner, inside and outside the old crop (full lattice)"))
rows.append(dict(base, check="v2 total", partner="%d partners" % len(parts), flagged_old_square_cells=tot, cause_inside_old_crop="",
                 cause_outside_old_crop="", note="sum over partners (a cell may count under two partners)"))
# self conflict pairs
ia, ja, flag, a, bb = PWM.conflict_pairs(W, LA.pitch())
Wa = np.zeros(W["ok"].shape, bool); Wb = Wa.copy()
fa = full(np.zeros(W["ok"].shape, bool))
OLDw = OLD[::s, ::s][:W["ok"].shape[0], :W["ok"].shape[1]]
CROPw = CROP[::s, ::s][:W["ok"].shape[0], :W["ok"].shape[1]]
end_in = OLDw[ia[a], ja[a]]; oth_in_crop = CROPw[ia[bb], ja[bb]]
for lab, e_in, o_crop in (("self conflict (a end in the old square)", OLDw[ia[a], ja[a]], CROPw[ia[bb], ja[bb]]),
                          ("self conflict (b end in the old square)", OLDw[ia[bb], ja[bb]], CROPw[ia[a], ja[a]])):
    sel = e_in
    Wm = np.zeros(W["ok"].shape, bool)
    Wm[(ia[a] if "a end" in lab else ia[bb])[sel], (ja[a] if "a end" in lab else ja[bb])[sel]] = True
    rows.append(dict(base, check=lab, partner="pairs %d" % int(sel.sum()), flagged_old_square_cells=int((full(Wm) & OLD).sum()),
                     cause_inside_old_crop=int((sel & o_crop).sum()), cause_outside_old_crop=int((sel & ~o_crop).sum()),
                     note="pairs of lamina.conflicts with this end in the old square; cause columns count pairs whose other end is inside or outside the old crop (working grid)"))
# a2 cluster rule
A.D.selftest_passed(); MC.selftest_ok()
T, _ = MC.verdict_row("a2")
Sd, _ = CRL.read_S()
gflag, meas, fl = A.a2_grid(px, py, pz, V, T)
gsize, _ = CRL.clusters(gflag)
hS, kept = CRL.rule_holes(gsize, Sd["a2"], V)
a2r = hS & V
from scipy import ndimage  # noqa: E402
lab_, n_ = ndimage.label(a2r)
ids = np.unique(lab_[a2r & OLD]); ids = ids[ids > 0]
inside = int(sum((lab_ == k).sum() for k in ids if ((lab_ == k) & CROP).any())) if len(ids) else 0
outside = int(sum(((lab_ == k) & ~CROP).sum() for k in ids)) if len(ids) else 0
rows.append(dict(base, check="a2 cluster rule", partner="%d clusters" % len(ids), flagged_old_square_cells=int((a2r & OLD).sum()),
                 cause_inside_old_crop=inside, cause_outside_old_crop=outside,
                 note="rule hole cells in the old square; cause columns: cells of their clusters in and outside the old crop"))
cols = ["utc", "surface", "old_square", "check", "partner", "flagged_old_square_cells", "cause_inside_old_crop", "cause_outside_old_crop", "note"]
with open(H + "/evidence/old-square-on-r2c.csv", "w", newline="") as f:
    f.write("# written by render-routes-0826/tools/old_square.py: the R2b 30.0063 mm square of seed6273 square centre measured on the R2c "
            "60 mm surface with the same check code (routes.checks' calls, pairwise.conflict_pairs); one row per check and per v2 partner\n")
    w = csv.writer(f, lineterminator="\n"); w.writerow(cols); w.writerows([[r.get(c, "") for c in cols] for r in rows])
print(open(H + "/evidence/old-square-on-r2c.csv").read())
