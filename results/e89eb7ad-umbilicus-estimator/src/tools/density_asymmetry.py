"""How one-sided the segments are around the reference axis, on the slices of Table II.

Meta A, point 4 of the revision (prereg/note-density-bias.md). The synthetic sections show that
the weighted sum moves towards the side of the section that holds more segments. Whether that is
what happens on PHerc0826, the one scroll of the primary block where the centroid wins, is a
measurement on the real slices: the same 24 slices per scroll as the frozen tables, the segment
midpoints counted in 8 angular sectors centred on the reference control point at that height.

The reference is used only as the origin of the sectors. Nothing is chosen by looking at it.

Per slice: the sector ratio (most populated over least populated sector), the dominant half-plane
fraction (the largest share of segments in any half-plane made of 4 consecutive sectors), the
vector from the reference to the centroid of the midpoints, and the vector from the reference to
the estimate with the division removed (seed 20260915 + z, the seed of the tables), both in
millimetres, and the cosine between the two. Per scroll: medians, and the fraction of slices where
the estimate lies in the same half-plane as the density centroid.

Extended on 2026-09-17, reviewer's point 4 on the short paper, from the five primary scrolls to
all fifteen with a reference: the same sectors, the same seed, the confirmation block added. The
reference is still only the origin of the sectors, which is measuring, not choosing. Beside the
per scroll rows the tool now writes the Spearman correlation, over the fifteen scrolls and over the
five primary ones, between the median sector ratio and the estimator's median distance from the
reference in Tables I and II (fifteen-k20.csv, twenty seeds), and between the ratio and the margin
over the centroid, so that the paper can say whether the density bias of the synthetic sections
orders the real scrolls too.

Outputs: evidence/density-asymmetry-fifteen-slices.csv, density-asymmetry-fifteen.csv
and density-asymmetry-fifteen-summary.csv. The five row files of 2026-09-16,
density-asymmetry.csv and density-asymmetry-slices.csv, are kept as they were written and are
not rewritten by this version of the tool.
"""
import os
import sys
import time

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L        # noqa: E402
import villa_estimator as ve  # noqa: E402

SECTORS = 8


def control_point(scroll, z):
    a = L.reference(scroll)
    sc = L.CFG[scroll]["grid_scale"]
    z0 = z * sc
    return np.array([np.interp(z0, a[:, 2], a[:, 0]) / sc, np.interp(z0, a[:, 2], a[:, 1]) / sc])


def main():
    t0 = time.perf_counter()
    slices_rows, scroll_rows = [], []
    k20 = {q["scroll"]: q for q in L.read_csv(os.path.join(L.EV, "fifteen-k20.csv"))
           if q["variant"] == "no-division"}
    for scroll in L.PRIMARY + L.CONFIRM:
        cfg = L.CFG[scroll]
        mm = cfg["voxel_um"] / 1000.0 * cfg["grid_scale"]
        per = []
        for z in L.heights(scroll):
            s = L.grid15_slice(scroll, z)
            if s is None:
                continue
            mid, nrm, W, H = s
            ref = control_point(scroll, z)
            v = mid - ref
            ang = np.arctan2(v[:, 1], v[:, 0])
            k = ((ang + np.pi) / (2 * np.pi) * SECTORS).astype(int) % SECTORS
            counts = np.bincount(k, minlength=SECTORS)
            half = max(sum(counts[(i + j) % SECTORS] for j in range(SECTORS // 2))
                       for i in range(SECTORS)) / counts.sum()
            ratio = counts.max() / max(counts.min(), 1)
            cen = mid.mean(0) - ref
            est, _ = L.estimate(mid, nrm, W, H, L.TABLE_SEED + z, False)
            off = est - ref
            nc, no = np.linalg.norm(cen), np.linalg.norm(off)
            cos = float(cen @ off / (nc * no)) if nc > 0 and no > 0 else float("nan")
            row = dict(scroll=scroll, z=z, segments=len(mid),
                       sector_counts=" ".join(str(c) for c in counts),
                       sector_ratio=round(float(ratio), 2),
                       dominant_half_fraction=round(float(half), 3),
                       centroid_minus_ref_x_mm=round(float(cen[0]) * mm, 2),
                       centroid_minus_ref_y_mm=round(float(cen[1]) * mm, 2),
                       centroid_minus_ref_mm=round(float(nc) * mm, 2),
                       estimate_minus_ref_x_mm=round(float(off[0]) * mm, 2),
                       estimate_minus_ref_y_mm=round(float(off[1]) * mm, 2),
                       estimate_minus_ref_mm=round(float(no) * mm, 2),
                       cosine=round(cos, 3) if cos == cos else "",
                       same_half_plane=int(cos > 0) if cos == cos else "")
            per.append(row)
            slices_rows.append(row)
        cs = np.array([r["cosine"] for r in per if r["cosine"] != ""], float)
        scroll_rows.append(dict(
            scroll=scroll, slices=len(per),
            sector_ratio_median=round(float(np.median([r["sector_ratio"] for r in per])), 2),
            dominant_half_fraction_median=round(float(np.median([r["dominant_half_fraction"] for r in per])), 3),
            centroid_minus_ref_median_mm=round(float(np.median([r["centroid_minus_ref_mm"] for r in per])), 2),
            estimate_minus_ref_median_mm=round(float(np.median([r["estimate_minus_ref_mm"] for r in per])), 2),
            cosine_median=round(float(np.median(cs)), 3),
            same_half_plane_fraction=round(float((cs > 0).mean()), 3),
            block="primary" if scroll in L.PRIMARY else "confirmation",
            no_division_mm_table=float(k20[scroll]["median_mm"]),
            centroid_mm_table=float(k20[scroll]["centroid_mm"]),
            margin_vs_centroid_mm_table=float(k20[scroll]["margin_vs_centroid_mm"])))
        r = scroll_rows[-1]
        print(f"  {scroll:12s} ratio {r['sector_ratio_median']:6.2f}  half {r['dominant_half_fraction_median']:.3f}  "
              f"centroid-ref {r['centroid_minus_ref_median_mm']:5.2f} mm  cos {r['cosine_median']:6.3f}  "
              f"same half {r['same_half_plane_fraction']:.2f}  ({time.perf_counter() - t0:.0f}s)", flush=True)
    # WHY THIS GUARD EXISTS. A tool that destroys a paper's input and exits zero is the failure
    # nobody notices until the number is already published. Demonstrated on 2026-09-18 with one of
    # the fifteen scrolls on disk: this ran to the end, exited 0, and rewrote all three files below
    # from the one scroll it found. density-asymmetry-fifteen-slices.csv went from 360 rows to 24
    # and the summary kept its ten rows with every correlation turned to nan, so the damage looked
    # like a finished file. The three files are kept in this repository and the cut grid slices
    # are not, so the reader who reaches that state has no way back.
    #
    # The test is scrolls that yielded NO slice at all, not empty slices: a height with no
    # published grid is cut as a zero byte file on purpose and L.grid15_slice skips it, so a
    # complete cut legitimately has empty slices and a stricter test would refuse on good data.
    empty = [s for s in L.PRIMARY + L.CONFIRM if not any(r["scroll"] == s for r in slices_rows)]
    stem = "density-asymmetry-fifteen"
    if empty and "--allow-missing" not in sys.argv:
        raise SystemExit(
            f"{len(empty)} of {len(L.PRIMARY + L.CONFIRM)} scrolls have no grid slice on disk "
            f"({', '.join(empty[:4])}{', ...' if len(empty) > 4 else ''}). "
            f"Cut the slices into inputs/grid15/ as section 3 of ../README.md says, or pass "
            f"--allow-missing to write to {stem}-partial-*, which does not overwrite {stem}-*.")
    if empty:
        stem += "-partial"

    L.write_csv(os.path.join(L.EV, f"{stem}-slices.csv"), list(slices_rows[0]), slices_rows)
    L.write_csv(os.path.join(L.EV, f"{stem}.csv"), list(scroll_rows[0]), scroll_rows)
    # the correlations: does the sector ratio order the scrolls by the estimator's distance from
    # the reference, and by its margin over the centroid, on all fifteen and on the primary five
    summary = []
    for subset, rows_ in (("fifteen", scroll_rows), ("primary", [r for r in scroll_rows if r["block"] == "primary"]),
                          ("confirmation", [r for r in scroll_rows if r["block"] == "confirmation"])):
        ratio = [r["sector_ratio_median"] for r in rows_]
        for against, key in (("estimator distance from reference", "no_division_mm_table"),
                             ("margin over centroid", "margin_vs_centroid_mm_table"),
                             ("centroid distance from reference", "centroid_mm_table")):
            rho, p = spearmanr(ratio, [r[key] for r in rows_])
            summary.append(dict(subset=subset, n=len(rows_), against=against,
                                spearman_rho=round(float(rho), 3), p_value=round(float(p), 4)))
            print(f"  {subset:13s} n {len(rows_):2d}  ratio vs {against:36s} rho {rho:+.3f}  p {p:.4f}", flush=True)
    L.write_csv(os.path.join(L.EV, f"{stem}-summary.csv"), list(summary[0]), summary)


if __name__ == "__main__":
    main()
