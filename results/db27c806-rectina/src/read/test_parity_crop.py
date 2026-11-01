"""Parity of a CPU read of a small crop against the stored GPU map of the same unit (real weights, minutes on 6 CPU threads).
Usage: python3 test_parity_crop.py --stack STACK --reference-map MAP --checkpoint CKPT --villa-src DIR [--r0 640 --c0 640 --size 640 --inset 128]
The crop starts at a multiple of the patch stride, so every patch inside it is the patch the full read made; the compared area is the crop
minus an inset of one patch on every side, where the crop cuts patches that the full read saw whole. Tolerance: max abs 0.05,
mean abs 0.005, Pearson at least 0.995. Exit 0 within, 14 outside. Written for m1 (patch 128); for m2 (patch 384) a crop would need
more than 1100 pixels a side, which is hours on a CPU: use the GPU command of README.md. Not run when this file was written."""
import argparse, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rectina_read as R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack", required=True); ap.add_argument("--reference-map", required=True)
    ap.add_argument("--checkpoint", required=True); ap.add_argument("--villa-src", required=True)
    ap.add_argument("--r0", type=int, default=640); ap.add_argument("--c0", type=int, default=640)
    ap.add_argument("--size", type=int, default=640); ap.add_argument("--inset", type=int, default=128)
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args()
    m = R.RectinaModel(a.checkpoint, a.villa_src, "cpu", a.threads)
    if a.r0 % R.stride(m.patch) or a.c0 % R.stride(m.patch):
        raise SystemExit("REFUSED: crop origin must be a multiple of the stride %d" % R.stride(m.patch))
    st = R.open_stack(a.stack)
    div = R.default_divisor(st.dtype)
    crop = np.asarray(st[:, a.r0:a.r0 + a.size, a.c0:a.c0 + a.size])
    ref = np.load(a.reference_map, mmap_mode="r")[a.r0:a.r0 + a.size, a.c0:a.c0 + a.size]
    t0 = time.time()
    fin, rows = R.read_stack(m, crop, list(range(7)), R.VIEWS["2v"], div, True, False, 8)
    i = a.inset
    res = R.compare_maps(fin[i:-i, i:-i], np.asarray(ref)[i:-i, i:-i])
    res.update(seconds=round(time.time() - t0, 1), crop=[a.r0, a.c0, a.size], inset=i)
    print(json.dumps(res))
    return 0 if res["within"] else 14


if __name__ == "__main__":
    sys.exit(main())
