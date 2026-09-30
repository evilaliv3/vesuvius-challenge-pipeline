#!/usr/bin/env python3
"""upright_full.py SQUARE SET ORDER PREDDIR (ink-v8in-0826, DECLARATION additions of 19:26Z and 19:34Z): the Kaggle maps of one
square, one render set (base = centred on the traced surface; forward = shifted +3.965) and one order, turned upright.

Reads PREDDIR/<SET>-{sheet,plus,minus}-read-<ORDER>-<TAG>.npy (float16, window pixel grid; plus and minus may be missing: the
panel says «not read»). Each valid node of render-routes-0826's aligned grid takes the value of the covered window pixel
(prediction > 0, i.e. under a tile) whose 3D point (points_at on the window tifxyz) is nearest, within 2 voxels; the aligned
square (c0, S) is drawn, z up, holes white, 5 mm bar. PNG: raw texture | sheet | plus copy | minus copy, probability 0 black to
1 white. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran. Its maps went to scratch/png/ of this study only. Descriptive rows (decide nothing) to evidence/describe.csv: per surface, the
aligned square's matched nodes, mean probability, share >= 0.5, 99th percentile, and the sheet over the larger copy."""
import csv, json, os, subprocess, sys
import numpy as np, tifffile
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
S = "/data/scrollagent/runs/rev1/ink-v8in-0826"
sys.path.insert(0, S + "/tools")
from v8in_read import assert_input  # noqa: E402
SQ = {"s6273": ("/data/scrollagent/runs/rev1/ink-square-0826-seed2604/scratch/rr-seed6273-squarecentre-R2cnative/window.tifxyz",
                "/data/scrollagent/runs/rev1/render-routes-0826/scratch/aligned-R2cnative-PHerc0826-seed6273-squarecentre.npz", "29.8961"),
      "s5364": (S + "/scratch/r5364/window.tifxyz",
                "/data/scrollagent/runs/rev1/render-routes-0826/scratch/aligned-R2cnative-PHerc0826-seed5364-squarecentre.npz", "27.2369")}
LAB = {"normal": ("not-w016-order", "the order not measured on w016 (reverse on w016, ba 0.44)"), "reverse": ("w016-order", "the order measured on w016 (normal on w016, side +1; --reverse here, side -1)")}
OLDLAB = {"normal": "his order (inferred from villa's normal convention)", "reverse": "the other order"}  # superseded 22:11Z, kept as a column
SETLAB = {"base": "centred on the traced surface (no shift), layers -11.5..+11.5", "forward": "shifted +3.965 vox outwards",
          "faceplus5": "layer window moved +5 voxels (outwards face): -6.5..+16.5 about the traced surface",
          "faceminus5": "layer window moved -5 voxels (umbo face): -16.5..+6.5 about the traced surface"}
sq, rset, order, pdir = sys.argv[1:5]
tag, words = LAB[order]
win, al, mm = SQ[sq]
for p in (win, al):
    assert_input(p)


def load_grid(tdir):
    sc = json.load(open(os.path.join(tdir, "meta.json")))["scale"]
    P = np.stack([tifffile.imread(os.path.join(tdir, a + ".tif")).astype(np.float64) for a in "xyz"], -1)
    return P, np.all(np.isfinite(P), -1) & ~np.all(P == -1, -1), float(sc[0])


def points_at(P, valid, s, I, J):  # score_ink_0139.points_at, copied unchanged
    gy = s * (I + 0.5); gx = s * (J + 0.5)
    iy = np.clip(np.floor(gy).astype(np.int64), 0, P.shape[0] - 2)
    ix = np.clip(np.floor(gx).astype(np.int64), 0, P.shape[1] - 2)
    fy = (gy - iy)[:, None]; fx = (gx - ix)[:, None]
    ok = valid[iy, ix] & valid[iy + 1, ix] & valid[iy, ix + 1] & valid[iy + 1, ix + 1]
    ok &= (gy <= P.shape[0] - 1) & (gx <= P.shape[1] - 1)
    p = (P[iy, ix] * (1 - fy) * (1 - fx) + P[iy, ix + 1] * (1 - fy) * fx
         + P[iy + 1, ix] * fy * (1 - fx) + P[iy + 1, ix + 1] * fy * fx)
    return p, ok


P, V, s = load_grid(win)
A = np.load(al)
Q, val, VAL, c0, SS, h = A["Q"].astype(np.float64), A["valid"], A["VAL"], int(A["c0"]), int(A["S"]), float(A["h"])
sl = (slice(c0, c0 + SS), slice(c0, c0 + SS))
qi, qj = np.nonzero(val[sl]); qi += c0; qj += c0
maps, info = {}, {}
for surf in ("sheet", "plus", "minus"):
    f = os.path.join(pdir, "%s-%s-read-%s-%s.npy" % (rset, surf, order, tag))
    fc = f[:-4] + "-crop177.npy"
    if os.path.exists(fc):          # face maps: read on the 3324 px crop at 177, padded back into the window grid
        assert_input(fc); c = np.load(fc).astype(np.float32)
        WH = (int(round(P.shape[0] / s)), int(round(P.shape[1] / s)))
        pr = np.zeros(WH, np.float32); pr[177:177 + c.shape[0], 177:177 + c.shape[1]] = c[:WH[0] - 177, :WH[1] - 177]
    elif os.path.exists(f):
        assert_input(f); pr = np.load(f).astype(np.float32)
    else:
        maps[surf] = None; continue
    I, J = np.nonzero(pr > 0)
    pts, ok = points_at(P, V, s, I, J)
    I, J, pts = I[ok], J[ok], pts[ok]
    d, k = cKDTree(pts).query(Q[qi, qj], distance_upper_bound=2.0)
    hit = np.isfinite(d)
    M = np.full(val.shape, np.nan, np.float32); M[qi[hit], qj[hit]] = pr[I[k[hit]], J[k[hit]]]
    maps[surf] = M[sl]
    v = M[sl][np.isfinite(M[sl])]
    info[surf] = dict(nodes=int(val[sl].sum()), matched=int(hit.sum()), median_match_vox="%.4f" % float(np.median(d[hit])),
                      mean="%.5f" % float(v.mean()), share_ge_05="%.5f" % float((v >= 0.5).mean()), p99="%.4f" % float(np.percentile(v, 99)))
if maps["sheet"] is None:
    raise SystemExit("REFUSED: no sheet prediction for %s %s %s in %s" % (sq, rset, order, pdir))
t = VAL[sl].astype(float); tv = val[sl]
g = t[tv & np.isfinite(t) & (t > 0)]; lo, hi = np.percentile(g, [1, 99])
tex = (np.clip((np.nan_to_num(t) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8); tex = np.stack([tex] * 3, -1); tex[~tv] = 255
panels = [tex[::-1]]
for surf in ("sheet", "plus", "minus"):
    m = maps[surf]
    if m is None:
        im = np.full(tex.shape, 230, np.uint8)
    else:
        im = (np.clip(np.nan_to_num(m), 0, 1) * 255).astype(np.uint8); im = np.stack([im] * 3, -1); im[~np.isfinite(m)] = 255
    panels.append(im[::-1])
H_, W_ = tex.shape[:2]
cv = Image.new("RGB", (4 * W_ + 60, H_ + 116), "white")
for i, p in enumerate(panels):
    cv.paste(Image.fromarray(p), (i * (W_ + 20), 0))
dr = ImageDraw.Draw(cv)
L = int(round(5.0 / (h * 0.009362))); dr.rectangle([10, H_ + 8, 10 + L, H_ + 14], fill="black"); dr.text((16 + L, H_ + 4), "5 mm", fill="black")
dr.text((10, H_ + 24), "v8-in (YoussefMoNader/ink-8um-v8in d89166b4), stride 21, UNCALIBRATED, not a claim of ink or of no ink. PHerc0826 R2c %s, %s mm square." % (sq, mm), fill="black")
dr.text((10, H_ + 42), "Order: %s. Render: %s." % (words, SETLAB[rset]), fill="black")
dr.text((10, H_ + 60), "Panels: raw texture | sheet | plus copy (gap minimum towards the umbo) | minus copy (gap minimum outwards)%s; z up (best-windows-0826 align.py grid)"
        % ("".join("; %s not read" % k for k in ("plus", "minus") if maps[k] is None)), fill="black")
dr.text((10, H_ + 78), "Order rule: w016 is PHerc0139 at 9.362 um (v8-in normal ba 0.6798 vs reverse 0.4411, side +1); carried here by the side sign (-1): a rule, not a measurement on PHerc0826.", fill="black")
os.makedirs(S + "/scratch/png", exist_ok=True)
png = S + "/scratch/png/v8in-%s-R2c-%s-read-%s-%s.png" % (sq, rset, order, tag)
cv.save(png)
now = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
e = S + "/evidence/describe-v2.csv"  # v2: labels of the w016 order (22:11Z), old label as a column
new = not os.path.exists(e)
hdr = ["utc", "square", "render_set", "order", "order_label", "old_order_label", "surface", "square_nodes", "matched_within_2vox", "median_match_vox", "mean_prob",
       "share_prob_ge_0.5", "p99_prob", "sheet_mean_over_larger_copy_mean", "sheet_share_over_larger_copy_share", "png"]
with open(e, "a", newline="") as f:
    if new:
        f.write("# written by ink-v8in-0826/tools/upright_full.py (v2 labels, DECLARATION 22:11Z): descriptive numbers of each upright map over the aligned square; UNCALIBRATED, decide nothing\n")
        csv.writer(f).writerow(hdr)
    else:
        with open(e) as r:
            r.readline()
            if r.readline().strip().split(",") != hdr:
                raise SystemExit("REFUSED: describe.csv header differs")
    cps = [info[k] for k in ("plus", "minus") if k in info]
    for surf, d in info.items():
        rm = rs = ""
        if surf == "sheet" and len(cps) == 2:
            rm = "%.4f" % (float(d["mean"]) / max(float(c["mean"]) for c in cps))
            rs = "%.4f" % (float(d["share_ge_05"]) / max(1e-12, max(float(c["share_ge_05"]) for c in cps)))
        csv.writer(f).writerow([now, sq, rset, order, words, OLDLAB[order], surf, d["nodes"], d["matched"], d["median_match_vox"], d["mean"], d["share_ge_05"], d["p99"], rm, rs, png])
print(png, json.dumps(info))
