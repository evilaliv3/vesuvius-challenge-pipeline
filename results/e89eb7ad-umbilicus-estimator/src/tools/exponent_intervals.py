# This file is a copy of tools/exponent_intervals.py of the working tree and differs from it in
# one way only: the estimates of the compiled function, which the working tree keeps in the
# folder of the driver run, are read from evidence/ here beside everything else, and the file it
# writes is named as it is named here. Nothing else is changed.
"""An interval on the aggregate row of the exponent table, and the paired count that decides it.

The exponent table reports, for each exponent p, the median over the fifteen scrolls of the per
scroll median distance from the reference. A referee asked on 2026-09-18 what supports p = 1 over
p = 1.5 or p = 0.5, and the answer was a point estimate with nothing beside it. This adds two
things, both from the run that is already on disk, with no new estimate computed:

  1. a 95 per cent percentile bootstrap interval on that aggregate. The unit resampled is the
     SCROLL and not the control point, because the quantity is a median over scrolls; the number
     of resamples and the generator seed are those of every other interval in the paper, so the
     arithmetic is the same and only the unit differs. That difference is stated in the caption.
  2. the paired count against p = 1, scroll by scroll, on the pre-registered threshold: on how
     many of the fifteen an exponent is better than p = 1 by at least the threshold, and on how
     many it is worse. This is the rule the paper uses to decide everything else, and unlike the
     aggregate it does not throw away the pairing.

The published weighted mean is carried as the control row, read from fifteen-k20.csv, with an
interval computed the same way.

Output: evidence/cpp-exponent-aggregate.csv when the estimates of the compiled function are
there, which they are here, and evidence/exponent-ablation-aggregate.csv otherwise.
"""
import os
import statistics
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L  # noqa: E402

B, BOOT_SEED = 1000, 20260916


def interval(values, rng):
    """Percentile bootstrap of the median of a list of per scroll medians."""
    v = np.asarray(values, dtype=float)
    boot = np.array([np.median(rng.choice(v, len(v))) for _ in range(B)])
    return float(np.median(v)), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


# The per scroll file and the control come from the same instrument as the table they feed. Since
# 2026-09-18 that is the shipped function, called through vc_gen_umbilicus; the transcription's
# files stay beside them and are used when the C++ ones are absent.
CPP = L.EV


def _pick(cpp_name, fallback):
    cand = os.path.join(CPP, cpp_name)
    return cand if os.path.exists(cand) else os.path.join(L.EV, fallback)


def main():
    ek = L.read_csv(_pick("cpp-exponent-fifteen-k20.csv", "exponent-ablation-fifteen-k20.csv"))
    k20 = L.read_csv(_pick("cpp-k20.csv", "fifteen-k20.csv"))
    ps = sorted({float(r["p"]) for r in ek})
    by = {pv: {r["scroll"]: float(r["median_mm"]) for r in ek if abs(float(r["p"]) - pv) < 1e-12}
          for pv in ps}
    one = by[1.0]
    rows = []
    for pv in ps:
        rng = np.random.default_rng(BOOT_SEED)          # one stream per row, as in the k20 tables
        med, lo, hi = interval(list(by[pv].values()), rng)
        better = sum(one[s] - by[pv][s] >= L.THRESHOLD_MM for s in by[pv])
        worse = sum(by[pv][s] - one[s] >= L.THRESHOLD_MM for s in by[pv])
        rows.append(dict(row=f"{pv:g}", scrolls=len(by[pv]), median_mm=round(med, 2),
                         ci_lo_mm=round(lo, 2), ci_hi_mm=round(hi, 2),
                         better_than_p1=better, worse_than_p1=worse,
                         bootstrap_unit="scroll", bootstrap_resamples=B,
                         bootstrap_seed=BOOT_SEED))
    # the control: the published weighted mean, the same fifteen scrolls, the same arithmetic
    asis = {r["scroll"]: float(r["median_mm"]) for r in k20 if r["variant"] == "as-is"}
    rng = np.random.default_rng(BOOT_SEED)
    med, lo, hi = interval(list(asis.values()), rng)
    rows.append(dict(row="mean", scrolls=len(asis), median_mm=round(med, 2), ci_lo_mm=round(lo, 2),
                     ci_hi_mm=round(hi, 2),
                     better_than_p1=sum(one[s] - asis[s] >= L.THRESHOLD_MM for s in asis),
                     worse_than_p1=sum(asis[s] - one[s] >= L.THRESHOLD_MM for s in asis),
                     bootstrap_unit="scroll", bootstrap_resamples=B, bootstrap_seed=BOOT_SEED))

    # known reference: the point estimate of each row must equal the median this paper already
    # prints, which the generator of the article's macros computes straight from the per scroll
    # file
    bad = [(r["row"], r["median_mm"], m) for r in rows if r["row"] != "mean"
           for m in [round(statistics.median(by[float(r["row"])].values()), 2)]
           if abs(r["median_mm"] - m) > 0.005]
    print("  known reference (the aggregate medians against the per scroll file):",
          "reproduced" if not bad else f"NOT: {bad}")
    for r in rows:
        print(f"  p {r['row']:>4s}  {r['median_mm']:5.2f} [{r['ci_lo_mm']:.2f}, {r['ci_hi_mm']:.2f}]"
              f"   against p=1: better on {r['better_than_p1']}, worse on {r['worse_than_p1']}")
    if bad:
        raise SystemExit("exponent_intervals: the aggregate does not reproduce")
    out = (os.path.join(CPP, "cpp-exponent-aggregate.csv") if os.path.exists(
        os.path.join(CPP, "cpp-exponent-fifteen-k20.csv"))
        else os.path.join(L.EV, "exponent-ablation-aggregate.csv"))
    L.write_csv(out, list(rows[0]), rows)


if __name__ == "__main__":
    main()
