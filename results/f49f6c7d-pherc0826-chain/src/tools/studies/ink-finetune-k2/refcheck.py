#!/usr/bin/env python3
"""refcheck.py (ink-finetune-k2): the known reference check of DECLARATION.md. Our base render of a segment's cut
(28 layers, zarr from vc_render_tifxyz) against the organisers' native9 surface volume of the same segment (28 layers,
fetched over HTTP for the crop only, uncompressed chunks), on a 512 by 512 crop at the centre of the labelled box.
Layer means (all 28 layers, pixels where both are non zero) compared by normalised cross correlation over the 8
orientations (numpy rot90 k on the plane, then fliplr if m) and integer offsets in [-8, 8] on both axes; then, at the
best alignment, the correlation of each of their layers with each of ours (the depth correspondence).
  refcheck.py SEG BASE.zarr ROW0 COL0 SEGDIR_URL
ROW0, COL0: the label (= organisers' render) pixel of the cut's render pixel (0, 0). Appends evidence/refcheck.csv and
evidence/refcheck-depth.csv; exit 1 unless the best is k0m0 at (0, 0) with NCC >= 0.5."""
import csv, json, os, subprocess, sys, urllib.request

import numpy as np
import zarr

S = "/data/scrollagent/runs/rev1/ink-finetune-k2"
C, R = 512, 8


def now():
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()


def fetch(url, y0, x0, h, w):
    za = json.load(urllib.request.urlopen(url + "/0/.zarray", timeout=60))
    assert za["compressor"] is None and za["dtype"] == "|u1" and za.get("dimension_separator", ".") == "/", za
    cz, cy, cx = za["chunks"]
    out = np.zeros((za["shape"][0], h, w), np.uint8)
    for by in range(y0 // cy, (y0 + h - 1) // cy + 1):
        for bx in range(x0 // cx, (x0 + w - 1) // cx + 1):
            try:
                raw = urllib.request.urlopen("%s/0/0/%d/%d" % (url, by, bx), timeout=120).read()
                a = np.frombuffer(raw, np.uint8).reshape(cz, cy, cx)
            except urllib.error.HTTPError:
                a = np.zeros((cz, cy, cx), np.uint8)
            ys, xs = by * cy, bx * cx
            sy0, sy1 = max(y0, ys), min(y0 + h, ys + cy); sx0, sx1 = max(x0, xs), min(x0 + w, xs + cx)
            out[:, sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = a[:, sy0 - ys:sy1 - ys, sx0 - xs:sx1 - xs]
    return out, za["shape"]


def ncc(a, b):
    m = (a > 0) & (b > 0)
    if m.sum() < 1000:
        return np.nan, int(m.sum())
    x = a[m].astype(np.float64); y = b[m].astype(np.float64)
    x -= x.mean(); y -= y.mean()
    return float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum() + 1e-12)), int(m.sum())


def orient(a, k, m):
    a = np.rot90(a, k, axes=(-2, -1))
    return a[..., ::-1] if m else a


def main(seg, base, row0, col0, url):
    row0, col0 = int(row0), int(col0)
    B = zarr.open(base, mode="r")["0"]
    H, W = B.shape[1:]
    cy, cx = H // 2 - C // 2, W // 2 - C // 2           # crop in our render pixels
    ours = np.asarray(B[:, cy - R:cy + C + R, cx - R:cx + C + R])
    theirs, tshape = fetch(url, row0 + cy, col0 + cx, C, C)
    tm = theirs.astype(np.float32).mean(0); om = ours.astype(np.float32).mean(0)
    res = []
    for k in range(4):
        for m in (0, 1):
            o = orient(om, k, m)                         # square window, turned about its centre
            for dy in range(-R, R + 1):
                for dx in range(-R, R + 1):
                    v, n = ncc(tm, o[R + dy:R + dy + C, R + dx:R + dx + C])
                    res.append((v, k, m, dy, dx, n))
    res = [r for r in res if np.isfinite(r[0])]
    res.sort(key=lambda r: -r[0])
    best = res[0]
    at0 = [r for r in res if r[1:5] == (0, 0, 0, 0)]
    ok = best[1:5] == (0, 0, 0, 0) and best[0] >= 0.5
    t = now()
    p = S + "/evidence/refcheck.csv"; new = not os.path.exists(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write('"# written by ink-finetune-k2/tools/refcheck.py; our base render (vc_render_tifxyz, 28 layers) against the organisers\' native9 '
                    'surface volume, 512 px crop at the centre of the labelled box, layer means, NCC over 8 orientations and offsets in [-8, 8]"\n')
            csv.writer(f).writerow(["time", "segment", "crop_row_label", "crop_col_label", "their_shape", "best_ncc", "best_k", "best_m", "best_dy", "best_dx",
                                    "pixels", "ncc_at_k0m0_00", "second_ncc", "second_alignment", "verdict"])
        sec = res[1]
        csv.writer(f).writerow([t, seg, row0 + cy, col0 + cx, "x".join(map(str, tshape)), "%.4f" % best[0], best[1], best[2], best[3], best[4], best[5],
                                "%.4f" % at0[0][0] if at0 else "", "%.4f" % sec[0], "k%dm%d (%d, %d)" % sec[1:5], "pass" if ok else "FAIL"])
    # depth correspondence at identity
    oc = ours[:, R:R + C, R:R + C].astype(np.float32)
    p = S + "/evidence/refcheck-depth.csv"; new = not os.path.exists(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write('"# written by ink-finetune-k2/tools/refcheck.py; per organisers\' layer, the best matching layer of our base render at k0m0 (0, 0) by NCC"\n')
            csv.writer(f).writerow(["time", "segment", "their_layer", "best_our_layer", "ncc", "ncc_same_index"])
        for i in range(theirs.shape[0]):
            v = [ncc(theirs[i].astype(np.float32), oc[j])[0] for j in range(oc.shape[0])]
            j = int(np.nanargmax(v))
            csv.writer(f).writerow([t, seg, i, j, "%.4f" % v[j], "%.4f" % v[i] if i < len(v) else ""])
    print(json.dumps(dict(seg=seg, best=best[:5], ncc_identity=at0[0][0] if at0 else None, verdict="pass" if ok else "FAIL")))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(*sys.argv[1:])
