#!/usr/bin/env python3
"""Run the rules on the scrolls that have no published umbilicus, and report the shift.

    python unknown_scrolls.py

There is no ground truth here, so nothing in this file is an error: it is how far apart two
estimators are, and how each compares with an axis that knows nothing about the scroll. That last
column is the one to read first. Where a constant axis at the centre of the field sits as close to
an estimate as the estimates sit to each other, the difference between them is not evidence of
anything on that scroll.
"""
import json
from pathlib import Path

import numpy as np

import bench
import data
import estimators as est

HERE = Path(__file__).resolve().parent


def distance(a, b, voxel_um):
    """Median xy distance between two polylines, over the heights they share."""
    lo, hi = max(a[:, 2].min(), b[:, 2].min()), min(a[:, 2].max(), b[:, 2].max())
    d = [np.hypot(x - np.interp(z, b[:, 2], b[:, 0]), y - np.interp(z, b[:, 2], b[:, 1]))
         * voxel_um / 1000.0 for x, y, z in a if lo <= z <= hi]
    return np.array(d)


def main():
    out = {}
    for scroll in data.UNKNOWN:
        voxel = data.SCROLLS[scroll].get("voxel_um", data.VOXEL_UM)
        lines = bench.polylines(scroll, {"argmax": est.argmax,
                                         "plateau": est.plateau_nearest_centroid})
        lines["fake"] = bench.fake_axis(scroll)
        shift = distance(lines["plateau"], lines["argmax"], voxel)
        to_fake_a = distance(lines["argmax"], lines["fake"], voxel)
        to_fake_p = distance(lines["plateau"], lines["fake"], voxel)
        out[scroll] = {"heights": len(lines["argmax"]),
                       "shift_median_mm": round(float(np.median(shift)), 2),
                       "shift_p90_mm": round(float(np.percentile(shift, 90)), 2),
                       "argmax_to_fake_axis_mm": round(float(np.median(to_fake_a)), 2),
                       "plateau_to_fake_axis_mm": round(float(np.median(to_fake_p)), 2),
                       "voxel_um": voxel}
        r = out[scroll]
        print(f"{scroll}: the two rules are {r['shift_median_mm']} mm apart (p90 {r['shift_p90_mm']}), "
              f"and a constant axis is {r['argmax_to_fake_axis_mm']} / {r['plateau_to_fake_axis_mm']} mm "
              f"from them")
    p = HERE / "results" / "unknown-scrolls.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(f"\nwritten {p}")
    print("No ground truth on these three: these are discrepancies, not errors.")


if __name__ == "__main__":
    main()
