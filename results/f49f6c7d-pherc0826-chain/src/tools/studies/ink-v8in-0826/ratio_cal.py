#!/usr/bin/env python3
"""ratio_cal.py (ink-v8in-0826, DECLARATION addition 22:23Z): the sheet over null copy ratio of the share of pixels at v8-in
probability >= 0.5, on known ink (w016: theirs, our A, our Bx; the order measured on w016 by the side sign) and on 0826 seed6273
(the order measured on w016, --reverse, base set), all at stride 21. Writes evidence/ratio-calibration.csv. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran.

w016 pixel sets: «labelled» = clean held out label pixels matched to the render within 4 voxels (positive-control-0139
score.matched on the lattice window, k 4), covered by a tile on all three maps; «window» = every pixel covered on all three.
0826 pixel set: «square» = render pixels of the aligned square's lattice box (window pixels 241:3437 on both axes) covered on all
three maps; the describe-v2.csv value over the upright aligned square is quoted beside.
Layers shared with the sheet's 24: 24 - ceil(|offset|); more than 12 shared is written «NOT an independent null»."""
import csv, math, os, subprocess, sys
import numpy as np
S = "/data/scrollagent/runs/rev1/ink-v8in-0826"
PC = "/data/scrollagent/runs/rev1/positive-control-0139"
os.environ["SA_EVIDENCE"] = S + "/scratch/w016/evidence"
sys.path.insert(0, PC + "/tools")
sys.path.insert(0, S + "/tools")
from v8in_read import assert_input  # noqa: E402

W016 = S + "/scratch/pred/v8in-0826-w016cal"
P6273 = S + "/scratch/pred/s6273"
OFF = {"theirs": (-10.829, 5.316, "normal", "+1"), "A": (-4.838, 12.222, "reverse", "-1"), "Bx": (-3.971, 8.418, "reverse", "-1"),
       "s6273": (-4.796, 9.751, "reverse", "-1"), "s5364": (-4.550, 8.156, "reverse", "-1")}
ONLY = sys.argv[1] if len(sys.argv) > 1 else ""   # "s5364": only the seed5364 row (added 00:27Z)


def shared(o):
    return max(0, 24 - math.ceil(abs(o)))


def indep(o):
    return "NOT an independent null (%d of 24 layers shared)" % shared(o) if shared(o) > 12 else "independent by the 12 layer rule (%d shared)" % shared(o)


def share(p, m):
    return float((p[m] >= 0.5).mean())


def row(surface, pixset, n, ss, sp, sm, stride, note):
    lo, hi, order, side = OFF[surface]
    big = max(sp, sm)
    return [now, surface, "PHerc0826" if surface in ("s6273", "s5364") else "PHerc0139 w016", side, order,
            "the order measured on w016", stride, pixset, n, "%.5f" % ss, "%.5f" % sp, "%.5f" % sm,
            "%.4f" % (ss / big) if big > 0 else "not measurable", "%.4f" % (ss / sp) if sp > 0 else "not measurable",
            "%.4f" % (ss / sm) if sm > 0 else "not measurable", "%+.3f" % lo, indep(lo), "%+.3f" % hi, indep(hi), note]


now = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
rows = []
import score as PS  # noqa: E402
L = np.load(PC + "/scratch/labels-9362.npz")
q = L["p"].astype(np.float64)
for surf, pcs in ((() if ONLY else (("theirs", "theirs"), ("A", "ours-A-S0"), ("Bx", "ours-Bx-S0")))):
    order = OFF[surf][2]
    f = {k: "%s/%s-%s-read-%s-w016-order.npy" % (W016, surf, k, order) for k in ("sheet", "plus", "minus")}
    for v in f.values():
        assert_input(v)
    M = {k: np.load(v).astype(np.float32) for k, v in f.items()}
    cov = (M["sheet"] > 0) & (M["plus"] > 0) & (M["minus"] > 0)
    _, dist, pi, pj = PS.matched(pcs, "lattice", q)
    own = (dist <= 4) & (pi >= 0)
    lab = np.zeros(cov.shape, bool); lab[pi[own], pj[own]] = True
    lab &= cov
    for name, m in (("labelled (clean held out, k 4)", lab), ("window (all covered)", cov)):
        rows.append(row(surf, name, int(m.sum()), share(M["sheet"], m), share(M["plus"], m), share(M["minus"], m), 21,
                        "w016 known ink; sets as run_one_v2 builds them, centring %s" % {"theirs": "-1.2690 (forward)", "A": "+1.2045 (reverse)", "Bx": "-0.2640 (reverse)"}[surf]))
if ONLY == "s5364":
    import json
    sc = json.load(open(S + "/scratch/r5364/window.tifxyz/meta.json"))["scale"][0]
    a, b = int(round(60 / sc)), int(round((60 + 725) / sc))
    f = {k: "%s/base-%s-read-reverse-w016-order.npy" % (S + "/scratch/pred/s5364", k) for k in ("sheet", "plus", "minus")}
    for v in f.values():
        assert_input(v)
    M = {k: np.load(v).astype(np.float32) for k, v in f.items()}
    box = np.zeros(M["sheet"].shape, bool); box[a:b, a:b] = True
    cov = box & (M["sheet"] > 0) & (M["plus"] > 0) & (M["minus"] > 0)
    rows.append(row("s5364", "square (render pixels %d:%d)" % (a, b), int(cov.sum()), share(M["sheet"], cov), share(M["plus"], cov), share(M["minus"], cov), 21,
                    "0826 base set (no centring); describe-v2.csv over the upright aligned square: sheet 0.06831, plus 0.06347, minus 0.08129, ratio 0.8403"))
f = {k: "%s/base-%s-read-reverse-w016-order.npy" % (P6273, k) for k in ("sheet", "plus", "minus")}
for v in f.values():
    assert_input(v)
M = {k: np.load(v).astype(np.float32) for k, v in f.items()}
box = np.zeros(M["sheet"].shape, bool); box[241:3437, 241:3437] = True
cov = box & (M["sheet"] > 0) & (M["plus"] > 0) & (M["minus"] > 0)
if not ONLY: rows.append(row("s6273", "square (render pixels 241:3437)", int(cov.sum()), share(M["sheet"], cov), share(M["plus"], cov), share(M["minus"], cov), 21,
                "0826 base set (no centring); describe-v2.csv over the upright aligned square: sheet 0.08415, plus 0.05438, minus 0.05544, ratio 1.5179"))
out = S + "/evidence/ratio-calibration.csv"
new = not os.path.exists(out)
hdr = ["utc", "surface", "scroll", "side_sign", "read", "order_label", "stride", "pixel_set", "pixels", "share_ge_0.5_sheet", "share_ge_0.5_plus",
       "share_ge_0.5_minus", "ratio_to_larger_copy", "ratio_to_plus", "ratio_to_minus", "plus_offset_vox", "plus_independence", "minus_offset_vox",
       "minus_independence", "note"]
with open(out, "a", newline="") as fh:
    if new:
        fh.write("# written by ink-v8in-0826/tools/ratio_cal.py: share of v8-in probability >= 0.5 on the sheet over its gap minimum null copies, known ink (w016, PHerc0139) against PHerc0826 seed6273, stride 21, the order measured on w016\n")
        csv.writer(fh).writerow(hdr)
    csv.writer(fh).writerows(rows)
for r in rows:
    print(r[1], r[7], r[8], r[9:15])
