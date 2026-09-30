#!/usr/bin/env python3
"""w016.py (selftrain-v8in-0826, DECLARATION «Guard (a)»): v8-in heads read on w016's clean held out region, scored as
positive-control-0139/tools/score.py scores (score_ink_0139.ba_auc: ba at uint8 >= 128, AUC ties one half).

  w016.py order     both orders with the base head -> evidence/order-0139.csv (and the chosen order, carried to A and Bx)
  w016.py guard     the chosen order, base and tuned (scratch/head/0139-round3.pt) on the same features -> evidence/guard-a.csv

Pixels: labels-9362.npz clean points matched to a pixel of the theirs lattice render within 4 voxels by score.py's
matched('theirs', 'lattice', ...), inside a stride 64 tile of his coverage rule on the base render (layers 2..25). A pixel's
prediction is the raw sigmoid of its tile, as uint8 round(255 p)."""
import csv, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import st_common as C  # noqa: E402
import engine as E  # noqa: E402
import score_ink_0139 as SC  # noqa: E402

PC = C.R1 + "/positive-control-0139"
sys.path.insert(0, PC + "/tools")
import score as PS  # noqa: E402

RENDER = PC + "/scratch/theirs/lattice/r/base.zarr"
ORIENT = PC + "/evidence/orient-rule.csv"
TOOL = "selftrain-v8in-0826/tools/w016.py"


def pixels():
    L = np.load(PC + "/scratch/labels-9362.npz")
    q = L["p"].astype(np.float64); ink = L["ink"].astype(bool)
    _, dist, pi, pj = PS.matched("theirs", "lattice", q)
    own = dist <= 4
    st = C.stack_in_order(RENDER, "normal")
    cov, pts = C.tile_grid(st)
    H, W = st.shape[:2]
    tid = np.full((H, W), -1, np.int64)
    for k, (x, y) in enumerate(pts):
        tid[y:y + 64, x:x + 64] = k
    t_of = np.full(len(q), -1, np.int64)
    t_of[own] = tid[pi[own], pj[own]]
    use = own & (t_of >= 0)
    keep_tiles = np.unique(t_of[use])
    remap = {int(t): i for i, t in enumerate(keep_tiles)}
    sel_pts = np.array([pts[t] for t in keep_tiles], np.int64)
    ti = np.array([remap[int(t)] for t in t_of[use]], np.int64)
    ry = pi[use] - sel_pts[ti, 1]; rx = pj[use] - sel_pts[ti, 0]
    return sel_pts, ti, ry, rx, ink[use], int(own.sum())


def score(probs, ti, ry, rx, ink):
    u8 = np.round(probs[ti, ry, rx] * 255).astype(np.uint8)
    return SC.ba_auc(u8, ink)


def side_signs():
    out = {}
    for r in csv.reader(open(ORIENT)):
        if len(r) > 3 and r[3] == "published 0139 umbilicus mapped by the label affine":
            out[r[2]] = int(r[6])
    return out


def main():
    mode = sys.argv[1]
    C.assert_input(RENDER); C.assert_input(PC + "/scratch/labels-9362.npz")
    pts, ti, ry, rx, ink, n_own = pixels()
    C.log(f"w016: {len(pts)} tiles, {len(ti)} scored pixels ({int(ink.sum())} ink) of {n_own} matched at k 4")
    m = C.load_model()
    runner = "w016-" + mode
    try:
        if mode == "order":
            HDR = ["tool", "time", "render", "order", "head", "tiles", "pixels", "pixels_ink", "pixels_noink", "ba", "auc", "chosen",
                   "side_sign_theirs", "side_sign_A", "side_sign_Bx", "order_A", "order_Bx"]
            res = {}
            for order in ("normal", "reverse"):
                p = E.run_eval(runner, f"w016 {order} base", m, RENDER, order, pts, ["base"])["base"]
                np.save(C.S + f"/scratch/w016-{order}-base.npy", p.astype(np.float16))
                res[order] = score(p, ti, ry, rx, ink)
            ok = [o for o in res if res[o][0] != "not measurable"]
            if not ok:
                raise SystemExit("STOP: w016 not measurable in both orders")
            best = max(ok, key=lambda o: float(res[o][0]))
            sg = side_signs()
            other = {"normal": "reverse", "reverse": "normal"}
            oA = best if sg["ours-A-S0"] == sg["theirs"] else other[best]
            oB = best if sg["ours-Bx-S0"] == sg["theirs"] else other[best]
            rows = [[TOOL, C.now(), RENDER, o, "base", len(pts), len(ti), int(ink.sum()), int((~ink).sum()), res[o][0], res[o][1],
                     "yes" if o == best else "no", sg["theirs"], sg["ours-A-S0"], sg["ours-Bx-S0"], oA, oB] for o in ("normal", "reverse")]
            C.append_csv(C.S + "/evidence/order-0139.csv", HDR, rows,
                         "written by " + TOOL + " order; base v8-in on w016 clean held out pixels matched at k 4 and under a stride 64 tile; "
                         "the chosen order has the higher ba and is carried to the label free windows by the side sign (orient-rule.csv, published umbilicus rows)")
            for r in rows:
                print(r)
        elif mode == "guard":
            import csv as _c
            rows = [r for r in _c.reader(open(C.S + "/evidence/order-0139.csv")) if len(r) > 11 and r[11] == "yes"]
            order = rows[-1][3]; base_order_ba = rows[-1][9]
            tuned = C.S + "/scratch/head/0139-round3.pt"
            C.assert_input(tuned)
            r = E.run_eval(runner, f"w016 {order} base+tuned", m, RENDER, order, pts, ["base", tuned])
            bb = score(r["base"], ti, ry, rx, ink); tt = score(r[tuned], ti, ry, rx, ink)
            if "not measurable" in (bb[0], tt[0]):
                verdict = "STOP: not measurable"
            else:
                verdict = "PASS" if float(tt[0]) >= float(bb[0]) else "FAIL: tuned below base, study stops"
            HDR = ["tool", "time", "order", "tiles", "pixels", "pixels_ink", "pixels_noink", "ba_base", "auc_base", "ba_tuned", "auc_tuned",
                   "ba_tuned_minus_base", "ba_base_in_order_row", "base_equals_order_row", "verdict"]
            diff = "" if "not measurable" in (bb[0], tt[0]) else "%.4f" % (float(tt[0]) - float(bb[0]))
            row = [TOOL, C.now(), order, len(pts), len(ti), int(ink.sum()), int((~ink).sum()), bb[0], bb[1], tt[0], tt[1], diff,
                   base_order_ba, "yes" if bb[0] == base_order_ba else "no", verdict]
            C.append_csv(C.S + "/evidence/guard-a.csv", HDR, [row],
                         "written by " + TOOL + " guard; same encoder features, same pixels; bar ba_tuned >= ba_base (DECLARATION.md guard a)")
            print(row)
    finally:
        C.release_threads(runner)


if __name__ == "__main__":
    main()
