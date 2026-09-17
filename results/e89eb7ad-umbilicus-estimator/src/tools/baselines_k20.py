# This file is a copy of tools/baselines_k20.py of the working tree and differs from it in one
# way only: the evidence file it writes and the tool it quotes are named as they are named
# here. The rules themselves come from the umbilicus bench, whose frozen copy is archived in
# this folder at umbilicus-bench/ and is found there with nothing set. Nothing else is changed.
"""Two more rules on the same slices as the twenty-seed tables: the plateau point nearest the
centroid and the argmax of the distance transform, both from umbilicus-bench.

Post hoc with respect to every pre-registration of the umbilicus paper, and declared so where its
numbers appear: the responsible person asked on 2026-09-16, after the frozen tables were known,
whether the corrected villa estimator is the closest of all the rules tried. The two rules are
deterministic (no seeds); their interval is a percentile bootstrap over the control points, 1000
resamples, generator seed 20260916. The metric, the heights, the common z range and the mask
cache are those of fifteen_k20.py, so the rows are comparable with fifteen-k20.csv row for row.

The 0.9 threshold of the plateau rule was chosen after seeing PHerc0125, 0211 and 0826, so on
those three the rule is tuned and not tested; the other twelve scrolls never saw it.

Output: evidence/baselines-k20.csv.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L  # noqa: E402

B, BOOT_SEED = 1000, 20260916
TUNED_ON = {"PHerc0125", "PHerc0211", "PHerc0826"}


def main():
    import bench
    import data
    import estimators as est
    k20 = {(q["scroll"], q["variant"]): q for q in L.read_csv(os.path.join(L.EV, "fifteen-k20.csv"))} \
        if os.path.exists(os.path.join(L.EV, "fifteen-k20.csv")) else {}
    rows = []
    for scroll in L.CFG:
        cfg = L.CFG[scroll]
        sc, mm = cfg["grid_scale"], cfg["voxel_um"] / 1000.0
        W = next(L.grid15_slice(scroll, z)[2] for z in L.heights(scroll) if L.grid15_slice(scroll, z))
        data.SCROLLS[scroll] = {"prediction": cfg["mask_pred"], "field_px": W * sc,
                                "voxel_um": cfg["voxel_um"], "store_scale": cfg["mask_scale"]}
        lines = bench.polylines(scroll, {"plateau_nearest_centroid": est.plateau_nearest_centroid,
                                         "argmax": est.argmax, "centroid": est.centroid},
                                3, L.N_HEIGHTS)
        ref = L.reference(scroll)
        q = k20.get((scroll, "no-division"))
        if q:
            zlo, zhi = float(q["z_lo"]), float(q["z_hi"])
        else:
            zlo = max(v[:, 2].min() for v in lines.values())
            zhi = min(v[:, 2].max() for v in lines.values())
        common = ref[(ref[:, 2] >= zlo) & (ref[:, 2] <= zhi)]
        rng = np.random.default_rng(BOOT_SEED)
        for rule in ("plateau_nearest_centroid", "argmax", "centroid"):
            e, _ = L.errors(common, lines[rule], mm)
            boot = np.array([np.median(rng.choice(e, len(e))) for _ in range(B)])
            rows.append(dict(scroll=scroll, block=cfg["block"], rule=rule, control_points=len(e),
                             slices=L.N_HEIGHTS, z_lo=round(zlo), z_hi=round(zhi),
                             median_mm=round(float(np.median(e)), 2),
                             ci_lo_mm=round(float(np.percentile(boot, 2.5)), 2),
                             ci_hi_mm=round(float(np.percentile(boot, 97.5)), 2),
                             p90_mm=round(float(np.percentile(e, 90)), 2),
                             tuned_on_this_scroll=int(scroll in TUNED_ON and rule == "plateau_nearest_centroid"),
                             centroid_k20_mm=q["centroid_mm"] if q else "",
                             no_division_k20_mm=q["median_mm"] if q else "",
                             bootstrap_resamples=B, bootstrap_seed=BOOT_SEED))
            r = rows[-1]
            print(f"  {scroll:12s} {rule:26s} {r['median_mm']:6.2f} [{r['ci_lo_mm']:.2f}, {r['ci_hi_mm']:.2f}]"
                  f"   villa k20 {r['no_division_k20_mm']}  centroid k20 {r['centroid_k20_mm']}", flush=True)
    L.write_csv(os.path.join(L.EV, "baselines-k20.csv"), list(rows[0]), rows)
    # the centroid here must equal the centroid of fifteen-k20.csv: same rule, same heights
    bad = [(r["scroll"], r["median_mm"], r["centroid_k20_mm"]) for r in rows
           if r["rule"] == "centroid" and r["centroid_k20_mm"] and abs(float(r["centroid_k20_mm"]) - r["median_mm"]) > 0.011]
    print("  known reference (centroid against fifteen-k20.csv):", "reproduced" if not bad else f"NOT: {bad}")


if __name__ == "__main__":
    main()
