# This file is a copy of tools/cpp_gen24_score.py of the working tree and differs from it in two
# ways: the estimates of the compiled function are read from evidence/ here beside everything
# else, and the docstring and what it prints are in English. Nothing that computes is changed.
"""The per scroll summary of the twenty four scroll run, from the C++ estimates.

Writes evidence/cpp-twentyfour.csv with the same schema as evidence/twentythree-refit.csv, so that
the generator of the article's macros can read the one in place of the other with nothing
else changing.

Two columns are NOT recomputed and stay the transcription's, declared here and in the paper:
`interior_max` and `interior_max_as_is` are a probe of the SHAPE of the objective on a lattice
around the estimate, not an estimate, and are measured on the transcription's samples like the
rest of the far field analysis.

    python3 tools/cpp_gen24_score.py
"""
import collections
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L          # noqa: E402

EV = L.EV
SEEDS24 = (20260915, 7, 123456)
COLS = ["scroll", "width", "slices", "inside_as_is", "inside_fixed",
        "jump_med_as_is_pct", "jump_med_fixed_pct", "jump_max_fixed_pct",
        "seed_spread_pct", "centroid_med_pct", "interior_max", "interior_max_as_is"]


def main():
    raw = L.read_csv(os.path.join(EV, "cpp-positions-24.csv"))
    guarded = [r for r in raw if int(r["guard"])]
    if guarded:
        print(f"WARNING: {len(guarded)} estimates met the guard, rows that do not reproduce")
        for r in guarded:
            print(f"  {r['scroll']} z {r['z']} {r['variant']} seed {r['seed']}")
    rows = [r for r in raw if not int(r["guard"])]
    old = {r["scroll"]: r for r in L.read_csv(os.path.join(L.EV, "twentythree-refit.csv"))}

    by = collections.defaultdict(dict)
    for r in rows:
        by[r["scroll"]].setdefault(r["role"], {}).setdefault(r["variant"], {})[int(r["z"])] = r

    out = []
    for scroll in sorted(by):
        pos = by[scroll].get("position", {})
        if "as-is" not in pos or "no-division" not in pos:
            continue
        zs = sorted(pos["no-division"])
        W = float(pos["no-division"][zs[0]]["width"])

        def xy(variant):
            return np.array([[float(pos[variant][z]["x"]), float(pos[variant][z]["y"])]
                             for z in zs])

        def jumps(a):
            return np.hypot(*np.diff(a, axis=0).T)

        a, b = xy("as-is"), xy("no-division")
        ja, jb = jumps(a), jumps(b)
        # the spread between the three declared seeds, on the weighted sum, exactly as the
        # transcription measured it: the median over slices of the median distance of the three
        # estimates from their own median
        spread_rows = collections.defaultdict(list)
        for r in rows:
            if r["scroll"] == scroll and r["variant"] == "no-division":
                spread_rows[int(r["z"])].append((int(r["seed"]), float(r["x"]), float(r["y"])))
        spread = []
        for z in zs:
            trio = np.array([[x, y] for _, x, y in sorted(spread_rows[z])])
            if len(trio) < 2:
                continue
            spread.append(float(np.median(np.hypot(*(trio - np.median(trio, 0)).T))))

        o = old.get(scroll, {})
        out.append(dict(
            scroll=scroll, width=W, slices=len(zs),
            inside_as_is=sum(int(pos["as-is"][z]["inside"]) for z in zs),
            inside_fixed=sum(int(pos["no-division"][z]["inside"]) for z in zs),
            jump_med_as_is_pct=100.0 * float(np.median(ja)) / W,
            jump_med_fixed_pct=100.0 * float(np.median(jb)) / W,
            jump_max_fixed_pct=100.0 * float(jb.max()) / W,
            seed_spread_pct=100.0 * float(np.median(spread)) / W if spread else "",
            # the centroid distance and the interior probe are measured on the objective's shape
            # and on the segments, not on the estimate, and are carried over unchanged
            centroid_med_pct=o.get("centroid_med_pct", ""),
            interior_max=o.get("interior_max", ""),
            interior_max_as_is=o.get("interior_max_as_is", "")))

    with open(os.path.join(EV, "cpp-twentyfour.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, COLS)
        w.writeheader()
        w.writerows(out)
    tot_a = sum(r["inside_as_is"] for r in out)
    tot_b = sum(r["inside_fixed"] for r in out)
    n = sum(r["slices"] for r in out)
    print(f"written cpp-twentyfour.csv: {len(out)} scrolls, {n} slices")
    print(f"  weighted mean, as published: inside {tot_a} of {n}")
    print(f"  weighted sum, this patch:    inside {tot_b} of {n}")
    oa = sum(int(r["inside_as_is"]) for r in old.values())
    ob = sum(int(r["inside_fixed"]) for r in old.values())
    print(f"  the transcription, for comparison: {oa} of {n} and {ob} of {n}")


if __name__ == "__main__":
    main()
