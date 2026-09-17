#!/usr/bin/env python3
"""Try a rule of your own on a real section, with no network.

    python example_estimator.py

Reads the example slices in examples/, runs the published rule, the one this repository proposes,
and a deliberately naive one written here, and prints how far each lands from the published
umbilicus at that height. Then do the same with your own: an estimator is any function of the
filled section and its distance transform that returns a point.

To score your rule properly, put it in `estimators.ESTIMATORS` and run `bench.py`: one slice says
nothing, the bench is 46 of them on four scrolls with the controls.
"""
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

import data
import estimators as est

HERE = Path(__file__).resolve().parent


def bounding_box_centre(mask, dist):
    """A rule of your own goes here. This one is naive on purpose: the centre of the section's
    bounding box, which knows nothing about where the windings are."""
    ys, xs = np.where(mask)
    return float((xs.min() + xs.max()) / 2), float((ys.min() + ys.max()) / 2)


RULES = {
    "argmax (as published upstream)": est.argmax,
    "plateau nearest centroid (proposed here)": est.plateau_nearest_centroid,
    "bounding box centre (naive, yours to replace)": bounding_box_centre,
}


def main():
    for f in sorted((HERE / "examples").glob("*.npz")):
        scroll = f.name.split("-")[0]
        d = np.load(f)
        sl, z, level = d["slice"], int(d["z"]), int(d["level"])
        # Ask data.py for the factor and the voxel size rather than assuming 2 ** level and the
        # 9.362 um scan. The three example scrolls happen to agree with both assumptions; PHerc0332
        # does not, and a rule of your own tried on it would be wrong by four without saying so.
        factor = data.scale_to_reference(scroll, level)
        mm = data.mm_per_voxel(scroll)
        z0 = z * factor

        truth = data.published_umbilicus(scroll)
        tx = np.interp(z0, truth[:, 2], truth[:, 0])
        ty = np.interp(z0, truth[:, 2], truth[:, 1])

        mask, dist = est.section(sl)
        print(f"\n{scroll}, level {level}, z {z0}: section {int(mask.sum())} px, "
              f"largest inscribed radius {dist.max() * factor * mm:.1f} mm")
        for name, rule in RULES.items():
            x, y = rule(mask, dist)
            d_mm = np.hypot(x * factor + factor // 2 - tx,
                            y * factor + factor // 2 - ty) * mm
            print(f"   {name:<46} {d_mm:6.2f} mm from the published umbilicus")

    print("\nOne slice each, and the ranking is different on all three: the published rule wins the\n"
          "first, the rule proposed here wins the second, the naive one wins the third. That is the\n"
          "whole reason for bench.py, and for the negative control inside it.")


if __name__ == "__main__":
    main()
