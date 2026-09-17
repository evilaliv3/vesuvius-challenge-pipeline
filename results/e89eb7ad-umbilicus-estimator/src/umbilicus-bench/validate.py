#!/usr/bin/env python3
"""The checks that decide whether the difference bench.py prints is worth believing.

    python validate.py
    python validate.py --scroll PHerc0125 --scroll PHerc0211 --scroll PHerc0826 \
                       --out results/validate.three-scrolls.json

Three of them, and they are the reason this is a repository and not a table in a comment:

  1. a paired Wilcoxon test per scroll, because a lower median over forty-odd points can be luck;
  2. leave one scroll out, because the plateau threshold was chosen after seeing the bench, and a
     threshold chosen on the scrolls it is then measured on is not a result;
  3. the default number of heights, because an improvement that exists only at a sampling density
     nobody runs is not an improvement.

One pass over the slices per scroll: every rule under test reads the same section.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

import bench
import data
import estimators as est

HERE = Path(__file__).resolve().parent
THRESHOLDS = (0.7, 0.8, 0.9)


def rules():
    r = {"argmax": est.argmax, "centroid": est.centroid}
    for q in THRESHOLDS:
        r[f"plateau{int(q * 100)}"] = lambda m, d, q=q: est.plateau_nearest_centroid(m, d, q)
    return r


def scored(scroll, heights):
    """Every rule's errors on the same published points, one pass over the slices."""
    truth = data.published_umbilicus(scroll)
    lines = bench.polylines(scroll, rules(), heights=heights)
    grid = np.array([z * data.scale_to_reference(scroll, 3)
                     for z in data.slice_heights(scroll, 3, heights)], float)
    common = truth[(truth[:, 2] >= grid.min()) & (truth[:, 2] <= grid.max())]
    mm = data.mm_per_voxel(scroll)
    return {name: bench.errors(common, p, mm)[0] for name, p in lines.items()}, len(common)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scroll", action="append", choices=data.GROUND_TRUTH, default=None,
                    help="restrict the checks to these scrolls; repeat the flag. The README quotes "
                         "a three-scroll run, and this is how it is reproduced.")
    ap.add_argument("--out", default=str(HERE / "results" / "validate.json"))
    args = ap.parse_args()
    scrolls = args.scroll or data.GROUND_TRUTH
    out, full = {"scrolls": list(scrolls)}, {}
    for scroll in scrolls:
        full[scroll], n = scored(scroll, 46)
        out.setdefault("scored_on", {})[scroll] = n

    print("1. paired test: the published argmax against the plateau reading")
    pa, pb = [], []
    for scroll, e in full.items():
        a, b = e["argmax"], e["plateau90"]
        pa += list(a); pb += list(b)
        p = wilcoxon(a, b).pvalue
        out.setdefault("paired", {})[scroll] = {
            "argmax_median_mm": round(float(np.median(a)), 2),
            "plateau_median_mm": round(float(np.median(b)), 2),
            "closer_on": int((b < a).sum()), "n": len(a), "wilcoxon_p": float(p)}
        print(f"   {scroll}: {np.median(a):.2f} -> {np.median(b):.2f} mm, closer on "
              f"{int((b < a).sum())} of {len(a)}, p {p:.2e}")
    pa, pb = np.array(pa), np.array(pb)
    out["paired_pooled"] = {"argmax_median_mm": round(float(np.median(pa)), 2),
                            "plateau_median_mm": round(float(np.median(pb)), 2),
                            "n": len(pa), "wilcoxon_p": float(wilcoxon(pa, pb).pvalue)}
    print(f"   pooled: {np.median(pa):.2f} -> {np.median(pb):.2f} mm over {len(pa)} points, "
          f"p {wilcoxon(pa, pb).pvalue:.2e}")

    print("\n2. leave one scroll out: the threshold is fixed on the other scrolls, measured on the held-out one")
    # Iterate over the scrolls scored above, not over data.SCROLLS: that dictionary also holds the
    # scrolls with no published umbilicus, which have no reference to be scored against.
    for held in scrolls:
        others = [s for s in scrolls if s != held]
        med = {q: float(np.median(np.concatenate([full[s][f"plateau{int(q * 100)}"] for s in others])))
               for q in THRESHOLDS}
        q = min(med, key=med.get)
        e = full[held][f"plateau{int(q * 100)}"]
        out.setdefault("leave_one_out", {})[held] = {"threshold": q, "median_mm": round(float(np.median(e)), 2)}
        print(f"   held out {held}: threshold from the other {len(others)} = {q}, median {np.median(e):.2f} mm")

    print("\n3. at the default number of heights")
    for scroll in scrolls:
        e, n = scored(scroll, 12)
        out.setdefault("twelve_heights", {})[scroll] = {
            "argmax_median_mm": round(float(np.median(e["argmax"])), 2),
            "plateau_median_mm": round(float(np.median(e["plateau90"])), 2), "n": n}
        print(f"   {scroll}: {np.median(e['argmax']):.2f} -> {np.median(e['plateau90']):.2f} mm")

    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(f"\nwritten {p}")


if __name__ == "__main__":
    main()
