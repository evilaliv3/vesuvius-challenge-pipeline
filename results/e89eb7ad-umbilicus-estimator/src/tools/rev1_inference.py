"""The inference of Section V-B, recomputed on the twenty-seed medians instead of single seeds.

The frozen paper ran Friedman, pairwise Wilcoxon with Holm, Nemenyi and the two one sided tests on
the medians of one seed per slice, because that is what the tables held. The revision has twenty
seeds per slice (evidence/fifteen-k20.csv), so the same tests are run again on the median over the
twenty, and the limits of agreement between the corrected estimate and its reference are rebuilt
from the same estimates. The criteria are unchanged; this replaces the input, not the test.

Also recomputed here, from the same file: which scrolls the constant axis wins on, and the worst
row of each block.

Output: evidence/inference-refit.json, bland-altman-refit.csv.
"""
import json
import os
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L  # noqa: E402

RULES = ["as-is", "no-division", "centroid", "fake_axis"]


def nemenyi_cd(k, n, q=2.569):     # q for k = 4 at alpha 0.05, as the frozen run used
    return q * np.sqrt(k * (k + 1) / (6.0 * n))


def holm(pairs):
    out, m = {}, len(pairs)
    for i, (name, p) in enumerate(sorted(pairs.items(), key=lambda kv: kv[1])):
        out[name] = min(1.0, max((m - i) * p, max(out.values(), default=0.0)))
    return out


def main():
    rows = L.read_csv(os.path.join(L.EV, "fifteen-k20.csv"))
    nd = {r["scroll"]: r for r in rows if r["variant"] == "no-division"}
    ai = {r["scroll"]: r for r in rows if r["variant"] == "as-is"}
    scrolls = list(nd)
    M = np.array([[float(ai[s]["median_mm"]), float(nd[s]["median_mm"]),
                   float(nd[s]["centroid_mm"]), float(nd[s]["fake_axis_mm"])] for s in scrolls])
    chi, p = stats.friedmanchisquare(*M.T)
    ranks = stats.rankdata(M, axis=1).mean(0)
    pairs = {}
    for i in range(4):
        for j in range(i + 1, 4):
            pairs[f"{RULES[i]} vs {RULES[j]}"] = stats.wilcoxon(M[:, i], M[:, j]).pvalue
    hp = holm(pairs)
    cd = nemenyi_cd(4, len(scrolls))
    gap = abs(ranks[1] - ranks[2])
    d = M[:, 1] - M[:, 2]
    bound = 0.30
    tost_p = max(stats.ttest_1samp(d, bound, alternative="less").pvalue,
                 stats.ttest_1samp(d, -bound, alternative="greater").pvalue)
    out = dict(
        source="evidence/fifteen-k20.csv, median over 20 seeds per slice",
        n_scrolls=len(scrolls), k_methods=4, rules=RULES,
        friedman=dict(chi2=round(float(chi), 3), p=float(p),
                      mean_ranks={RULES[i]: round(float(ranks[i]), 3) for i in range(4)}),
        wilcoxon_holm={k: dict(p_raw=float(v), p_holm=round(float(hp[k]), 5)) for k, v in pairs.items()},
        nemenyi=dict(critical_difference=round(float(cd), 3), gap_fixed_vs_centroid=round(float(gap), 3),
                     separates=bool(gap > cd)),
        tost=dict(bound_mm=bound, p=round(float(tost_p), 4), equivalent=bool(tost_p < 0.05), n=len(scrolls)),
        non_discriminating=[s for s in scrolls if float(nd[s]["fake_axis_mm"]) <= float(nd[s]["median_mm"])],
        worst=dict(primary=min((s for s in scrolls if nd[s]["block"] == "primary"),
                               key=lambda s: float(nd[s]["margin_vs_centroid_mm"])),
                   confirmation=min((s for s in scrolls if nd[s]["block"] == "confirmation"),
                                    key=lambda s: float(nd[s]["margin_vs_centroid_mm"]))))
    json.dump(out, open(os.path.join(L.EV, "inference-refit.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("friedman", "nemenyi", "tost", "non_discriminating", "worst")}, indent=1))

    # limits of agreement of the corrected estimate against its reference, from the same estimates
    raw = L.read_csv(os.path.join(L.EV, "k20-estimates.csv"))
    ba = []
    for scroll in scrolls:
        cfg = L.CFG[scroll]
        sc, mm = cfg["grid_scale"], cfg["voxel_um"] / 1000.0
        est = [r for r in raw if r["scroll"] == scroll and r["variant"] == "no-division"]
        zs = sorted({int(r["z"]) for r in est})
        pl = np.array([[np.median([float(r["x"]) for r in est if int(r["z"]) == z]) * sc,
                        np.median([float(r["y"]) for r in est if int(r["z"]) == z]) * sc, z * sc] for z in zs])
        ref = L.reference(scroll)
        q = nd[scroll]
        common = ref[(ref[:, 2] >= float(q["z_lo"])) & (ref[:, 2] <= float(q["z_hi"]))]
        for axis, i in (("x", 0), ("y", 1)):
            d = np.array([(np.interp(z, pl[:, 2], pl[:, i]) - v) * mm for v, z in zip(common[:, i], common[:, 2])])
            ba.append(dict(comparison="corrected estimate against reference", scroll=scroll, axis=axis,
                           n=len(d), bias_mm=round(float(d.mean()), 3),
                           loa_low_mm=round(float(d.mean() - 1.96 * d.std(ddof=1)), 2),
                           loa_high_mm=round(float(d.mean() + 1.96 * d.std(ddof=1)), 2)))
    L.write_csv(os.path.join(L.EV, "bland-altman-refit.csv"), list(ba[0]), ba)


if __name__ == "__main__":
    main()
