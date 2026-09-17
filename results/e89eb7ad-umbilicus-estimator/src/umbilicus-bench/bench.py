#!/usr/bin/env python3
"""Score umbilicus estimators against the three published umbilici.

    python bench.py                     # every estimator, every scroll, 46 heights
    python bench.py --heights 12        # what estimate_umbilicus.py runs by default
    python bench.py --scroll PHerc0826

The metric: for every published control point inside the estimate's z coverage, interpolate the
estimate at that height and take the distance in the xy plane, in millimetres. Median first, p90 and
worst case next to it, because for an initialization the tail is what hurts.

Read the fake-axis row before reading anything else. A constant axis at the centre of the field
knows nothing about the scroll, and on PHerc0125 it beats every estimator here: on that scroll this
comparison does not discriminate, and no ranking taken from it means anything.
"""
import argparse
import json
from pathlib import Path

import numpy as np

import data
import estimators as est

HERE = Path(__file__).resolve().parent


def polylines(scroll, which, level=3, heights=46):
    """Run several estimators over the same slices, in one pass.

    The section is computed once per slice and handed to every estimator, so nothing but the reading
    of it differs between them. That is what makes the comparison like for like, and it also keeps a
    whole bench run to one pass over the cache.

    `which` maps a name to a function of (mask, dist). Returns name -> Nx3 control points in level 0
    voxels. Raises data.MissingData if any requested height holds no section, rather than returning a
    short polyline: everything downstream is a statistic, and a short sample prints as a confident one.
    """
    f = data.scale_to_reference(scroll, level)
    pts = {name: [] for name in which}
    empty = []
    for z in data.slice_heights(scroll, level, heights):
        mask, dist = est.section(data.cached_slice(scroll, level, z))
        if mask is None:
            empty.append(z)
            continue
        for name, fn in which.items():
            x, y = fn(mask, dist)
            pts[name].append((x * f + f // 2, y * f + f // 2, z * f))
    # Every row this feeds is a statistic over control points, so a sample that quietly lost part of
    # the scroll is worse than no answer: the median still prints, the ranking still looks confident,
    # and nothing says the estimator saw a third of the heights. A slice with no section means the
    # chunks behind it were missing, and read_slice treats a missing chunk as empty by design, so the
    # only place that absence can be caught is here. Refuse, before anything is written.
    if empty:
        raise data.MissingData(
            f"{scroll}: {len(empty)} of {heights} slices at level {level} hold no section "
            f"(heights {empty[:6]}{' ...' if len(empty) > 6 else ''}). The surface prediction behind "
            f"them is missing or empty: check that {data.SCROLLS[scroll]['prediction']} is still "
            f"published, and delete the cached slices for this scroll before retrying.")
    return {name: np.array(sorted(v, key=lambda r: r[2]), float) for name, v in pts.items()}


def polyline(scroll, estimator, level=3, heights=46, reject=False):
    """One estimator, for callers that want only one."""
    p = polylines(scroll, {"one": estimator}, level, heights)["one"]
    return est.hampel_reject(p)[0] if reject else p


def fake_axis(scroll, level=3, heights=46):
    """Negative control: a constant axis at the centre of the field."""
    c = data.SCROLLS[scroll]["field_px"] / 2.0
    f = data.scale_to_reference(scroll, level)
    return np.array([(c, c, z * f) for z in data.slice_heights(scroll, level, heights)], float)


def errors(truth, estimate, mm_per_voxel=data.MM_PER_VOXEL):
    """Millimetres between each published control point and the estimate interpolated at its height."""
    if len(estimate) < 2:
        return np.array([]), truth[:0]
    lo, hi = estimate[:, 2].min(), estimate[:, 2].max()
    inside = truth[(truth[:, 2] >= lo) & (truth[:, 2] <= hi)]
    e = [np.hypot(x - np.interp(z, estimate[:, 2], estimate[:, 0]),
                  y - np.interp(z, estimate[:, 2], estimate[:, 1])) * mm_per_voxel
         for x, y, z in inside]
    return np.array(e), inside


def run(scrolls, heights, level):
    out = {}
    for scroll in scrolls:
        truth = data.published_umbilicus(scroll)
        lines = polylines(scroll, est.ESTIMATORS, level, heights)
        lines["argmax + hampel"] = est.hampel_reject(lines["argmax"])[0]
        lines["fake axis (control)"] = fake_axis(scroll, level, heights)

        # Score every estimator on the same published points: the ones inside the z range of the
        # slice grid, which is the same for every rule that keeps all its slices. A rule that drops
        # slices, like the Hampel filter, is scored on what its own coverage reaches, and its point
        # count is printed next to it, so a shorter polyline cannot look better by quietly skipping
        # the hard end of the scroll.
        grid = np.array([z * data.scale_to_reference(scroll, level)
                         for z in data.slice_heights(scroll, level, heights)], float)
        common = truth[(truth[:, 2] >= grid.min()) & (truth[:, 2] <= grid.max())]

        rows = {}
        for name, p in lines.items():
            e, scored_points = errors(common, p, data.mm_per_voxel(scroll))
            rows[name] = {"median_mm": round(float(np.median(e)), 2),
                          "p90_mm": round(float(np.percentile(e, 90)), 2),
                          "worst_mm": round(float(e.max()), 2),
                          "scored_on": len(scored_points),
                          "control_points": len(p)}
        out[scroll] = {"scored_on": len(common), "heights": heights, "level": level, "rows": rows}

        print(f"\n{scroll}: {len(common)} published control points, {heights} heights, level {level}")
        print(f"  {'estimator':<26} {'median':>8} {'p90':>8} {'worst':>8} {'points':>7}")
        for name, r in sorted(rows.items(), key=lambda kv: kv[1]["median_mm"]):
            print(f"  {name:<26} {r['median_mm']:>8.2f} {r['p90_mm']:>8.2f} {r['worst_mm']:>8.2f}"
                  f" {r['scored_on']:>7}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scroll", action="append", choices=data.GROUND_TRUTH, default=None)
    ap.add_argument("--heights", type=int, default=46)
    ap.add_argument("--level", type=int, default=3)
    ap.add_argument("--out", default=str(HERE / "results" / "bench.json"))
    a = ap.parse_args()
    out = run(a.scroll or data.GROUND_TRUTH, a.heights, a.level)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(f"\nwritten {a.out}")


if __name__ == "__main__":
    main()
