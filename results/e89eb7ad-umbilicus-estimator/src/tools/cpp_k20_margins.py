"""The margins of Tables III and IV before rounding, and the verdicts taken on them.

Written 2026-09-30 on the referee's finding 3: cpp_k20.py scores rounded each margin over the
centroid to two decimals before fifteen_k20.verdict compared it with the threshold of 0.30 mm, so a
margin that rounds to 0.30 was counted as reaching it. This recomputes, from the same compiled
estimates (evidence/cpp-k20-estimates.csv) and by the same code as fifteen_k20.score (metric, common
z range, centroid baseline, constant axis), the medians and the margin at full precision, and takes
the verdicts again with fifteen_k20.verdict, which now tests the unrounded margin.

The bootstrap is not redrawn: the intervals of cpp-k20.csv stay as they are. The width of the
field the baselines need is read from the header of a slice of the scroll's published normal grid,
the cut slices of inputs/grid15/ not being carried: from inputs/grid23/ where the scroll is there
(PRIVATE_GRID23 or this folder), else from the published grid on the open data bucket. Every row
carries, as columns, whether rounding its unrounded values gives back the centroid, the median, the
margin and the constant axis of cpp-k20.csv; the tool refuses to write verdicts when any does not.

    python3 tools/cpp_k20_margins.py [--workers N]

Writes evidence/cpp-k20-margins.csv and evidence/cpp-k20-verdicts.json.
"""
import argparse
import csv
import json
import os
import sys
import urllib.request
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L            # noqa: E402
import fifteen_k20 as F         # noqa: E402

RAW = os.path.join(L.EV, "cpp-k20-estimates.csv")
TABLE = os.path.join(L.EV, "cpp-k20.csv")
OUT = os.path.join(L.EV, "cpp-k20-margins.csv")
VERDICTS = os.path.join(L.EV, "cpp-k20-verdicts.json")
GRID23 = [os.path.join(L.NG, "grid23"),
          os.environ.get("PRIVATE_GRID23", "/data/repositories/vesuvius-challenge-pipeline-private/"
                         "results/e89eb7ad-umbilicus-estimator/src/inputs/grid23")]
VARIANTS = ("as-is", "no-division")
COLS = ["scroll", "block", "variant", "field_width", "field_width_source",
        "median_unrounded_mm", "centroid_unrounded_mm", "fake_axis_unrounded_mm",
        "margin_unrounded_mm", "margin_vs_centroid_mm",
        "median_reproduces", "centroid_reproduces", "fake_axis_reproduces", "margin_reproduces"]


def field_width(scroll, z0):
    for d in GRID23:
        p = os.path.join(d, scroll)
        if os.path.isdir(p):
            f = sorted(x for x in os.listdir(p) if x.endswith(".grid"))[0]
            h, _, _ = L.read_grid(os.path.join(p, f))
            return float(h["bounds"][2]), "grid23/%s/%s" % (scroll, f)
    url = L.CFG[scroll]["grids"] + "xy/%06d.grid" % z0
    tmp = os.path.join(os.environ.get("TMPDIR", "/data/tmp"), "cpp_k20_margins_%s.grid" % scroll)
    urllib.request.urlretrieve(url, tmp)
    h, _, _ = L.read_grid(tmp)
    os.remove(tmp)
    return float(h["bounds"][2]), url


def one(scroll):
    raw = []
    with open(RAW) as fh:
        for r in csv.DictReader(fh):
            if r["scroll"] != scroll or int(r["guard"]):
                continue
            raw.append(dict(z=int(r["z"]), k=int(r["k"]), variant=r["variant"],
                            x=float(r["x"]), y=float(r["y"])))
    have = {}
    for r in raw:
        have[(r["z"], r["variant"])] = have.get((r["z"], r["variant"]), 0) + 1
    full = {z for z in {r["z"] for r in raw} if all(have.get((z, v), 0) == F.K for v in VARIANTS)}
    raw = [r for r in raw if r["z"] in full]
    cfg = L.CFG[scroll]
    sc, mm = cfg["grid_scale"], cfg["voxel_um"] / 1000.0
    ref = L.reference(scroll)
    zs = sorted({r["z"] for r in raw})
    W, src = field_width(scroll, zs[0])
    base = L.baselines(scroll, W)
    poly = {}
    for v in VARIANTS:
        poly[v] = np.zeros((F.K, len(zs), 3))
        for r in raw:
            if r["variant"] == v:
                poly[v][r["k"], zs.index(r["z"])] = (r["x"] * sc, r["y"] * sc, r["z"] * sc)
    zlo = max([base["centroid"][:, 2].min(), base["fake_axis"][:, 2].min()] +
              [poly[v][0][:, 2].min() for v in poly])
    zhi = min([base["centroid"][:, 2].max(), base["fake_axis"][:, 2].max()] +
              [poly[v][0][:, 2].max() for v in poly])
    common = ref[(ref[:, 2] >= zlo) & (ref[:, 2] <= zhi)]
    cen = float(np.median(L.errors(common, base["centroid"], mm)[0]))
    fake = float(np.median(L.errors(common, base["fake_axis"], mm)[0]))
    out = []
    for v in VARIANTS:
        med = float(np.median([np.median(L.errors(common, poly[v][k], mm)[0]) for k in range(F.K)]))
        out.append(dict(scroll=scroll, block=cfg["block"], variant=v, field_width=W,
                        field_width_source=src, median_unrounded_mm=med,
                        centroid_unrounded_mm=cen, fake_axis_unrounded_mm=fake,
                        margin_unrounded_mm=cen - med))
    print("  %s done" % scroll, flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=5)
    a = ap.parse_args()
    table = {(r["scroll"], r["variant"]): r for r in L.read_csv(TABLE)}
    scrolls = list(dict.fromkeys(r["scroll"] for r in table.values()))
    with ProcessPoolExecutor(a.workers) as ex:
        rows = [q for part in ex.map(one, scrolls) for q in part]
    bad = []
    for q in rows:
        t = table[(q["scroll"], q["variant"])]
        q["margin_vs_centroid_mm"] = t["margin_vs_centroid_mm"]
        for col, mine in (("median", "median_unrounded_mm"), ("centroid", "centroid_unrounded_mm"),
                          ("fake_axis", "fake_axis_unrounded_mm"),
                          ("margin", "margin_unrounded_mm")):
            tcol = {"median": "median_mm", "centroid": "centroid_mm", "fake_axis": "fake_axis_mm",
                    "margin": "margin_vs_centroid_mm"}[col]
            ok = abs(round(q[mine], 2) - float(t[tcol])) < 1e-9
            q[col + "_reproduces"] = int(ok)
            if not ok:
                bad.append((q["scroll"], q["variant"], col, q[mine], t[tcol]))
    L.write_csv(OUT, COLS, rows)
    print("expected %d rows, got %d" % (2 * len(scrolls), len(rows)))
    if bad or len(rows) != 2 * len(scrolls):
        print("REFUSED: rounded values that do not give back cpp-k20.csv:", bad)
        return 1
    # the verdicts, from the rows of cpp-k20.csv with their numbers as numbers and the margin
    # unrounded, by the same verdict function
    un = {(q["scroll"], q["variant"]): q["margin_unrounded_mm"] for q in rows}
    vr = []
    for (s, v), t in table.items():
        vr.append(dict(scroll=s, block=t["block"], variant=v, median_mm=float(t["median_mm"]),
                       centroid_mm=float(t["centroid_mm"]), inside=int(t["inside"]),
                       inside_of=int(t["inside_of"]),
                       margin_ci_includes_zero=int(t["margin_ci_includes_zero"]),
                       margin_unrounded_mm=un[(s, v)]))
    verdicts = {"primary": F.verdict(vr, "primary", 4, 3),
                "confirmation": F.verdict(vr, "confirmation", 8, 6),
                "written_by": "tools/cpp_k20_margins.py, on the unrounded margins of "
                              "evidence/cpp-k20-margins.csv"}
    with open(VERDICTS, "w") as fh:
        json.dump(verdicts, fh, indent=1)
    print("written", VERDICTS)
    print(json.dumps({b: {k: verdicts[b][k] for k in ("beats", "beat", "repair",
                     "margins_with_interval_including_zero")} for b in ("primary", "confirmation")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
