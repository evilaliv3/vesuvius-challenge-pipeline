#!/usr/bin/env python3
"""stitch_r2d.py ORDER TAG (ink-v8in-0826-r2d): stitch the four piece maps scratch/pred/p<k>-read-ORDER-TAG.npy (float16, pulled from
the two kernels) into the full probability map in the surface render's own pixel grid (evidence/pieces.json: each piece's kept
rows), write scratch/pred/r2d-s2715-S0-sheet-ORDER.npy (float16), the PNGs scratch/png/r2d-s2715-S0-ORDER-full.png (probability
0..1 as 0..255 grey, full resolution) and -4x.png (mean over 4 x 4 blocks), and evidence/describe.csv (per region: pixels scored
= covered by at least one tile of the whole read, scratch/covered.npy from pack_r2d.py; mean probability and share at or above 0.5
over them; regions all, half-a, half-b, r<i>c<j> of a 4 x 4 grid). PRIVATE."""
import csv, json, os, subprocess, sys
import numpy as np
from PIL import Image
S = "/data/scrollagent/runs/rev1/ink-v8in-0826-r2d"
TOOL = "ink-v8in-0826-r2d/tools/stitch_r2d.py"
order, tag = sys.argv[1], sys.argv[2]
J = json.load(open(S + "/evidence/pieces.json"))
H, W = J["H"], J["W"]
m = np.zeros((H, W), np.float16)
filled = np.zeros(H, np.int32)
for p in J["pieces"]:
    f = S + "/scratch/pred/%s-read-%s-%s.npy" % (p["piece"], order, tag)
    if not os.path.exists(f) or os.path.getsize(f) == 0:
        raise SystemExit("REFUSED: missing %s" % f)
    a = np.load(f)
    if a.shape != (p["p1"] - p["p0"], W):
        raise SystemExit("REFUSED: %s shape %s, expected %s" % (f, a.shape, (p["p1"] - p["p0"], W)))
    m[p["keep0"]:p["keep1"]] = a[p["keep0"] - p["p0"]:p["keep1"] - p["p0"]]
    filled[p["keep0"]:p["keep1"]] += 1
if not (filled == 1).all():
    raise SystemExit("REFUSED: rows filled %s times" % sorted(set(filled.tolist())))
cov = np.unpackbits(np.load(S + "/scratch/covered.npy"), count=H * W).reshape(H, W).astype(bool)
os.makedirs(S + "/scratch/pred", exist_ok=True); os.makedirs(S + "/scratch/png", exist_ok=True)
np.save(S + "/scratch/pred/r2d-s2715-S0-sheet-%s.npy" % order, m)
m32 = m.astype(np.float32)
g = np.clip(np.round(m32 * 255), 0, 255).astype(np.uint8)
Image.fromarray(g).save(S + "/scratch/png/r2d-s2715-S0-%s-full.png" % order, optimize=False)
h4, w4 = H // 4, W // 4
d = m32[:h4 * 4, :w4 * 4].reshape(h4, 4, w4, 4).mean((1, 3))
Image.fromarray(np.clip(np.round(d * 255), 0, 255).astype(np.uint8)).save(S + "/scratch/png/r2d-s2715-S0-%s-4x.png" % order)
now = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
cut = J["cuts"][1]
regions = [("all", 0, H, 0, W), ("half-a", 0, cut, 0, W), ("half-b", cut, H, 0, W)]
for i in range(4):
    for j in range(4):
        regions.append(("r%dc%d" % (i, j), i * H // 4, (i + 1) * H // 4, j * W // 4, (j + 1) * W // 4))
rows = []
for name, r0, r1, c0, c1 in regions:
    c = cov[r0:r1, c0:c1]; v = m32[r0:r1, c0:c1][c]
    n = int(c.sum())
    if n == 0:
        rows.append([now, order, tag, name, r0, r1, c0, c1, 0, "not measurable", "not measurable", "not measurable"])
    else:
        rows.append([now, order, tag, name, r0, r1, c0, c1, n, "%.5f" % float(v.mean()), "%.5f" % float((v >= 0.5).mean()), int((v >= 0.5).sum())])
p = S + "/evidence/describe.csv"; new = not os.path.exists(p)
with open(p, "a", newline="") as f:
    if new:
        f.write("# written by %s: v8-in on the whole R2d seed2715 S0 surface, per region of the render's pixel grid (rows r0:r1, cols c0:c1); pixels_scored = covered by at least one tile of the whole read; share_ge_05 = share of scored pixels with probability at or above 0.5; uncalibrated, descriptive, decides nothing\n" % TOOL)
        csv.writer(f).writerow(["utc", "order", "order_label", "region", "r0", "r1", "c0", "c1", "pixels_scored", "mean_prob", "share_ge_05", "pixels_ge_05"])
    csv.writer(f).writerows(rows)
for r in rows:
    print(r)
