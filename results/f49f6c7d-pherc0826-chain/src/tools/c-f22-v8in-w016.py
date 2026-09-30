#!/usr/bin/env python3
"""Figure C22, a raster: Youssef Nader's v8-in ink model on the labelled region of PHerc0139 w016, the labelled scroll, on the
organisers' surface and on our sheet Bx, each in the depth order measured on w016, with the labelled ink outlined, and the
balanced accuracy of each on the clean held out label points.

What it reads (never written):
  - the v8-in maps of ink-v8in-0826's calibration kernel (stride 21), scratch/pred/v8in-0826-w016cal:
    theirs-sheet-read-normal-w016-order.npy and Bx-sheet-read-reverse-w016-order.npy (the order each surface's side sign
    gives, as ink-v8in-0826/tools/ratio_cal.py reads them), in each surface's lattice render grid;
  - the clean held out label points of w016 (positive-control-0139 scratch/labels-9362.npz, points p and flag ink), matched
    to each surface's render pixels within 4 voxels by positive-control-0139/tools/score.py matched, the same matching
    ratio_cal.py and the positive control use.
What it computes, and writes as rows: per surface, the matched points covered by a tile, the balanced accuracy at
probability >= 0.5 and the AUC (squares-ink-1447 score_ink_0139.ba_auc on the probability as uint8, the positive
control's own function). No other CSV holds the balanced accuracy of v8-in on our sheet Bx; this table is where it is written.
The drawing: each map cropped to the box of its matched label points plus a margin, probability 0 black to 1 white; the
matched ink points drawn as a sky blue outline; a 1 mm bar. No position of any scroll is written.

Usage: c-f22-v8in-w016.py [--out CSV] [--png PNG]
"""
import argparse, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f22-v8in-w016"
RUNS = "/data/scrollagent/runs/rev1"
PC = RUNS + "/positive-control-0139"
PRED = RUNS + "/ink-v8in-0826/scratch/pred/v8in-0826-w016cal"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
VOXEL_UM = 9.362        # the voxel of the PHerc0139 scan the w016 renders are made in (positive-control-0139 label-map.csv)
K_VOX = 4               # the matching distance of the positive control (score.py, k 4)
MARGIN = 40
SKY = (86, 180, 233)
SURF = (("a", "theirs", "theirs", "normal", "the organisers' surface"), ("b", "Bx", "ours-Bx-S0", "reverse", "our sheet Bx"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()
    here = os.path.dirname(HERE)
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    png = a.png or os.path.join(here, "paper/figures/%s.png" % FIGURE)
    sys.path.insert(0, PC + "/tools")
    os.environ.setdefault("SA_EVIDENCE", PC + "/evidence")
    import score as PS  # noqa: E402  positive-control-0139/tools/score.py (matched)
    import score_ink_0139 as SC  # noqa: E402  imported by score.py from squares-ink-1447/tools (ba_auc)
    rows = []

    def put(panel, what, sf, sc, value, key=""):
        rows.append(dict(key=key, panel=panel, what=what, source_file=sf, source_column=sc, value=value))

    L = np.load(PC + "/scratch/labels-9362.npz")
    q = L["p"].astype(np.float64)
    ink = L["ink"].astype(bool)
    put("a;b", "clean held out label points of w016", "positive-control-0139/scratch/labels-9362.npz", "p; ink", len(q), key="label_points")
    panels = []
    for letter, tag, pcs, order, words in SURF:
        f = os.path.join(PRED, "%s-sheet-read-%s-w016-order.npy" % (tag, order))
        if not os.path.exists(f):
            raise SystemExit("%s is missing" % f)
        P = np.load(f).astype(np.float32)
        _, dist, pi, pj = PS.matched(pcs, "lattice", q)
        own = (dist <= K_VOX) & (pi >= 0)
        cov = np.zeros(len(q), bool)
        cov[own] = P[pi[own], pj[own]] > 0
        pred = np.clip(np.rint(P[pi[cov], pj[cov]] * 255.0), 0, 255).astype(np.uint8)
        ba, auc = SC.ba_auc(pred, ink[cov])
        src = "ink-v8in-0826/scratch/pred/v8in-0826-w016cal/" + os.path.basename(f)
        put(letter, "%s: map read" % words, src, "sha256", RL.sha256(f))
        put(letter, "%s: depth order (the one measured on w016 by the side sign)" % words, src, "file name", order)
        put(letter, "%s: label points matched within %d voxels and covered by a tile" % (words, K_VOX), src, "score.py matched", int(cov.sum()),
            key="n_%s" % tag.lower())
        put(letter, "%s: of them ink" % words, "positive-control-0139/scratch/labels-9362.npz", "ink", int(ink[cov].sum()), key="n_ink_%s" % tag.lower())
        put(letter, "%s: balanced accuracy at probability >= 0.5" % words, src, "score_ink_0139.ba_auc", ba, key="ba_%s" % tag.lower())
        put(letter, "%s: AUC" % words, src, "score_ink_0139.ba_auc", auc, key="auc_%s" % tag.lower())
        I, J = pi[own], pj[own]
        r0, r1 = max(int(I.min()) - MARGIN, 0), min(int(I.max()) + MARGIN + 1, P.shape[0])
        c0, c1 = max(int(J.min()) - MARGIN, 0), min(int(J.max()) + MARGIN + 1, P.shape[1])
        crop = P[r0:r1, c0:c1]
        g = (np.clip(crop, 0, 1) * 255).astype(np.uint8)
        img = RL.rgb(g)
        m = np.zeros(crop.shape, bool)
        m[pi[own & ink] - r0, pj[own & ink] - c0] = True
        from scipy import ndimage
        m = ndimage.binary_closing(ndimage.binary_dilation(m, iterations=2), iterations=3)
        edge = m & ~ndimage.binary_erosion(m)
        edge = ndimage.binary_dilation(edge, iterations=1)
        img[edge] = SKY
        if img.shape[0] > img.shape[1]:          # both panels landscape, turned by a quarter turn only
            img = np.ascontiguousarray(np.rot90(img))
            put(letter, "%s: turned a quarter turn to lie landscape" % words, "", "", "yes")
        put(letter, "%s: crop, pixels high and wide" % words, "", "", "%d;%d" % crop.shape)
        panels.append((img, "(%s) %s, ba %s" % (letter, words, ba)))
    RL.print_size(max(p.shape[1] for p, _ in panels), RL.TEXTWIDTH_BP)      # the stacked canvas prints at the text width
    drawn = []
    for img, text in panels:
        img, nbar = RL.scale_bar(img, 1.0, VOXEL_UM / 1000.0, "1 mm")
        drawn.append(RL.label(img, text, size=26))
    panels = drawn
    put("a;b", "voxel of the w016 renders; um", "positive-control-0139/evidence/label-map.csv", "9.362 um nodes", "%g" % VOXEL_UM)
    put("a;b", "scale bar; mm", "", "", "1", key="bar_mm")
    put("a;b", "matching distance; voxels", "positive-control-0139/tools/score.py", "k", K_VOX, key="k_vox")
    put("a;b", "scroll", "", "", "PHerc. 0139", key="scroll")
    put("a;b;c" if "c-f23" in __file__ else "a;b", "model", "hf-files.csv of ink-v8in-0826", "repo YoussefMoNader/ink-8um-v8in", "v8-in", key="model")
    put("a;b", "labelled region", "", "", "w016", key="region")
    put("a;b", "outline", "", "", "sky blue: the matched clean ink label points, dilated 2 px and closed")
    w = max(p.shape[1] for p in panels)
    padded = [np.pad(p, ((0, 0), (0, w - p.shape[1]), (0, 0)), constant_values=255) for p in panels]
    canvas, boxes = RL.stacked(padded)
    RL.save_png(png, canvas)
    figlib.write_plotted(out, "figure C22, written by src/tools/%s.py at %s: v8-in on PHerc0139 w016, the labelled scroll, the "
                         "organisers' surface and our sheet Bx, each in the depth order measured on w016; balanced accuracy on the clean "
                         "held out label points matched within %d voxels; NO POSITION of any scroll." % (FIGURE, figlib.utc_now(), K_VOX),
                         FIELDS, rows)
    sys.stderr.write("%s\n%s: %d rows\n" % (png, out, len(rows)))


if __name__ == "__main__":
    main()
