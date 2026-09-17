#!/usr/bin/env python3
"""Write out what a run produced, so the numbers can be checked without rerunning it.

    python export_results.py

  results/estimates/<scroll>-<estimator>.json   the control points each rule produced, in the same
                                                shape as a published umbilicus.json
  results/errors.csv                            one row per scroll, estimator and published point
"""
import csv
import json
from pathlib import Path

import numpy as np

import bench
import data
import estimators as est

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"


def main():
    (OUT / "estimates").mkdir(parents=True, exist_ok=True)
    rows = []
    for scroll in data.GROUND_TRUTH:
        truth = data.published_umbilicus(scroll)
        lines = bench.polylines(scroll, est.ESTIMATORS)
        lines["argmax+hampel"] = est.hampel_reject(lines["argmax"])[0]
        lines["fake_axis"] = bench.fake_axis(scroll)
        grid = np.array([z * data.scale_to_reference(scroll, 3)
                         for z in data.slice_heights(scroll, 3, 46)], float)
        common = truth[(truth[:, 2] >= grid.min()) & (truth[:, 2] <= grid.max())]
        for name, p in lines.items():
            json.dump({"control_points": [{"x": int(x), "y": int(y), "z": int(z), "score": 60}
                                          for x, y, z in p],
                       "metadata": {"scroll": scroll, "estimator": name,
                                    "source": "umbilicus-bench", "level": 3, "heights": 46}},
                      open(OUT / "estimates" / f"{scroll}-{name}.json", "w"), indent=1)
            e, scored = bench.errors(common, p, data.mm_per_voxel(scroll))
            for (x, y, z), mm in zip(scored, e):
                rows.append({"scroll": scroll, "estimator": name, "z": int(z),
                             "published_x": int(x), "published_y": int(y),
                             "error_mm": round(float(mm), 3)})
        print(f"{scroll}: {len(lines)} estimates written, {len(common)} published points scored")
    with open(OUT / "errors.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"written {OUT / 'errors.csv'}, {len(rows)} rows")


if __name__ == "__main__":
    main()
