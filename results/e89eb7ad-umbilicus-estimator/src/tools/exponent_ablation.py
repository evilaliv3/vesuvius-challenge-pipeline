# This file is a copy of tools/exponent_ablation.py of the working tree and differs from it in one
# way only: the absolute paths of the machine the measurements ran on are replaced by paths inside
# this folder, resolved from the file's own location, and the synthetic sections are imported
# under the name they carry here. Nothing else is changed.
"""Exponent ablation of the weighted sum of the umbilicus score.

Declared in full on 2026-09-18, before anything here ran.

The family is

    S_p(x) = sum_i cos^2(theta_i) / max(100, d_i)^p          (the sum, no normalisation)

with p in 0.5, 1.0, 1.5, 2.0. p = 1 is the patch as it stands, and the weighted mean at p = 1 is
the published control, read from the frozen evidence and never recomputed here. The constant 100
is not touched: it has its own section in the long paper.

Two reviews of 2026-09-17 are behind this. The first proposed a weighted MEAN with a faster
decaying weight, which would keep the mean's exactness and still have a finite maximum, and would
make the patch pointless. The second refuted it: in the far field every distance is nearly D, a
pure power weight cancels between numerator and denominator, and the limit of the mean is the
plain mean of cos^2 whatever the exponent. --cancellation measures that refutation. What survives
of the second review is the real objection this tool answers: once the division is gone the
exponent is a free parameter nobody explored.

Modes:

  --check          the four reproductions of section 4 of the declaration, none of which writes
                   into evidence/: p = 1 must reproduce the paper byte for byte
  --cancellation   the far field of the mean and of the sum at p = 0.5, 1, 1.5, 2, 4 against
                   lambda_max of the normals' covariance, on the slice of Fig. 2 and on two
                   synthetic sections           -> exponent-ablation-cancellation.csv
  --rate           the same at D = 1e6, 1e7, 1e8, 1e9, which measures the limit and not the
                   remainder at one D (addendum 1 of the declaration)
                                                -> exponent-ablation-cancellation-rate.csv
  --scrolls        the fifteen scrolls, 24 slices, 20 seeds, one estimate per p, resumable
                                                -> exponent-ablation-k20-estimates.csv
  --score          scores those estimates with the metric, the baselines and the threshold of the
                   frozen tables                -> exponent-ablation-fifteen-k20.csv
                                                -> exponent-ablation-seed-spread.csv
  --synthetic      the density bias on the sections with a centre known by construction, the same
                   sections and the same lattice as tools/synthetic_density.py
                                                -> exponent-ablation-synthetic-density.csv

No existing evidence file is written or overwritten by any mode.
"""
import argparse
import csv
import io
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "inputs"))
import rev1_lib as L                 # noqa: E402
import fifteen_k20 as F              # noqa: E402
import synthetic_density as SD       # noqa: E402
import synthetic_sections as S       # noqa: E402
import villa_estimator as ve         # noqa: E402

P_LIST = (0.5, 1.0, 1.5, 2.0)
P_CANCEL = (0.5, 1.0, 1.5, 2.0, 4.0)
FAR = 1.0e6
RAW = os.path.join(L.EV, "exponent-ablation-k20-estimates.csv")
RAW_COLS = ["scroll", "z", "k", "seed", "p", "x", "y", "inside", "capped"]


def ptag(p):
    """One spelling of the exponent, used in every file this tool writes."""
    return f"{p:.1f}"


def boot_index(p):
    """The third element of the bootstrap generator's seed, fixed in the declaration: 1 for p = 1,
    so that the p = 1 row reproduces the published no-division row of fifteen-k20.csv digit for
    digit, and 100 + round(10 p) for the others."""
    return 1 if p == 1.0 else 100 + int(round(10 * p))


# ------------------------------------------------------------------ the reproductions at p = 1

def check():
    """Section 4 of the declaration. Returns 0 only if all four reproductions hold."""
    bad = []
    scroll = list(L.CFG)[0]
    sl = L.grid15_slice(scroll, L.heights(scroll)[0])

    # 1. the default takes the original expression and not `** 1.0`
    d = np.array([50.0, 100.0, 137.3, 9999.7])
    same = all(a.tobytes() == b.tobytes() for a, b in
               [(L.weights(d), 1.0 / np.maximum(100.0, d))])
    print(f"  1. weight at p = 1 identical to 1/max(100, d): {same}")
    if not same:
        bad.append("weight at p = 1")

    # 2. rev1_selftest: equality to the bit with the frozen transcription
    st = L.rev1_selftest(*sl)
    print(f"  2. rev1_selftest on {scroll}: {'passed' if not st else st}")
    if st:
        bad.append("rev1_selftest")

    # 3. far-field-eigenvalue.csv byte for byte, into a scratch folder
    import tempfile
    import far_field_eigenvalue as FF
    tmp = tempfile.mkdtemp(prefix="expablation-")
    ev, L.EV = L.EV, tmp
    try:
        FF.main()
    finally:
        L.EV = ev
    a = open(os.path.join(tmp, "far-field-eigenvalue.csv"), "rb").read()
    b = open(os.path.join(ev, "far-field-eigenvalue.csv"), "rb").read()
    print(f"  3. far-field-eigenvalue.csv byte for byte: {a == b}")
    if a != b:
        bad.append("far-field-eigenvalue.csv")

    # 4. the search: every row of the first scroll of k20-estimates.csv, recomputed at p = 1
    t0 = time.perf_counter()
    rows = F.estimates_for(scroll)
    buf = io.StringIO()
    w = csv.DictWriter(buf, F.RAW_COLS, extrasaction="ignore", lineterminator="\r\n")
    w.writerows(rows)
    orig = "".join(l for l in open(os.path.join(ev, "k20-estimates.csv"), newline="")
                   if l.startswith(scroll + ","))
    ok = buf.getvalue() == orig
    print(f"  4. k20-estimates.csv rows of {scroll} byte for byte: {ok} "
          f"({len(rows)} estimates, {time.perf_counter() - t0:.0f}s)")
    if not ok:
        bad.append("k20-estimates.csv")
    print("  ALL FOUR REPRODUCED" if not bad else f"  NOT REPRODUCED: {bad}")
    return 1 if bad else 0


# ------------------------------------------------------------------ the cancellation

def _sections():
    """The three sections of the cancellation check: the slice of Fig. 2 and two synthetic ones."""
    out = []
    h, paths, _ = L.read_grid(
        os.path.join(L.NG, "cache", "pherc0826", "ngrid", "xy", "008000.grid"))   # figure_umbilicus.f2
    mid, nrm = L.segments(paths)
    ref = L.reference("PHerc0826")
    sc = L.CFG["PHerc0826"]["grid_scale"]
    z0 = 8000 * sc
    cp = np.array([np.interp(z0, ref[:, 2], ref[:, 0]) / sc,
                   np.interp(z0, ref[:, 2], ref[:, 1]) / sc])
    out.append(("PHerc0826 xy 8000", mid, nrm, cp, L.TABLE_SEED + 8000))
    for name, make in (("circle 1:1", lambda: S.circles(*SD.C)),
                       ("half circle", lambda: S.circles(*SD.C, frac=0.5))):
        m2, n2 = S.polyline_segments(make())
        out.append((name, m2, n2, SD.C, 60000))
    return out


def rate():
    """Addendum 1 of the declaration: the far field measured at D = 1e6, 1e7, 1e8, 1e9.

    One D measures the remainder, not the limit. The algebra says the mean's relative gap from
    lambda_max is O(p R / D) and the sum goes as D^-p, so a factor of ten in D must divide the
    first by about ten and the second by about 10^p. The bars are in the addendum, written before
    this ran: the gap of the mean divides by a factor between 5 and 20 (or falls below 1e-6), and
    the sum over its maximum divides by a factor between 10^p / 2 and 2 * 10^p.
    """
    DS = [1e6, 1e7, 1e8, 1e9]
    rows = []
    for name, mid, nrm, centre, seed in _sections():
        ms, ns, _ = L.sample(mid, nrm, seed)
        ns = ns / np.linalg.norm(ns, axis=1, keepdims=True)
        C = ns.T @ ns / len(ns)
        w, V = np.linalg.eigh(C)
        lam_max, e = float(w[1]), V[:, 1]
        for p in P_CANCEL:
            ray = centre + np.outer(np.logspace(1, 6, 140), e)
            smax = float(L.refine_score(ray, ms, ns, False, p=p).max())
            prev_g = prev_s = None
            for D in DS:
                x = centre + D * e
                mn = float(L.refine_score(x, ms, ns, True, p=p)[0])
                sm = float(L.refine_score(x, ms, ns, False, p=p)[0])
                g = abs(mn - lam_max) / lam_max
                so = sm / smax
                rows.append(dict(
                    section=name, p=ptag(p), distance_units=f"{D:.0e}",
                    lambda_max=round(lam_max, 6), mean=round(mn, 6),
                    mean_rel_gap=f"{g:.3e}",
                    mean_gap_divided_by=(f"{prev_g / g:.2f}" if prev_g and g > 0 else ""),
                    sum_over_max=f"{so:.3e}",
                    sum_divided_by=(f"{prev_s / so:.3e}" if prev_s and so > 0 else ""),
                    expected_sum_divided_by=f"{10 ** p:.3e}"))
                prev_g, prev_s = g, so
    L.write_csv(os.path.join(L.EV, "exponent-ablation-cancellation-rate.csv"), list(rows[0]), rows)
    bad = []
    for r in rows:
        if r["mean_gap_divided_by"]:
            f = float(r["mean_gap_divided_by"])
            if not (5 <= f <= 20 or float(r["mean_rel_gap"]) < 1e-6):
                bad.append(("mean", r["section"], r["p"], r["distance_units"], f))
        if r["sum_divided_by"]:
            f, want = float(r["sum_divided_by"]), 10 ** float(r["p"])
            if not (want / 2 <= f <= 2 * want):
                bad.append(("sum", r["section"], r["p"], r["distance_units"], f))
    for r in rows:
        print(f"  {r['section']:20s} p {r['p']}  D {r['distance_units']}  mean gap "
              f"{r['mean_rel_gap']} /{r['mean_gap_divided_by'] or '  -'}   sum/max "
              f"{r['sum_over_max']} /{r['sum_divided_by'] or '  -'} "
              f"(expected /{r['expected_sum_divided_by']})", flush=True)
    print("  RATE BAR PASSED" if not bad else f"  RATE BAR MISSED: {bad}", flush=True)
    return 0 if not bad else 1


def cancellation():
    """The far field of the mean and of the sum, exponent by exponent, against lambda_max.

    Analytically, for D larger than the section every max(100, d_i) is d_i and
    d_i = D (1 + O(R/D)), so w_i = D^-p (1 + O(p R/D)): the factor D^-p cancels between numerator
    and denominator of the mean and the limit is (1/N) sum_i (n_i . u)^2 = u^T C u for EVERY p,
    whose maximum over u is lambda_max(C). The sum keeps the factor and goes as N (u^T C u) / D^p,
    which vanishes for every p > 0. Measured here at D = 1e6 along the eigenvector of lambda_max.
    """
    sections = _sections()
    D = np.logspace(1, 6, 140)
    rows = []
    for name, mid, nrm, centre, seed in sections:
        ms, ns, _ = L.sample(mid, nrm, seed)
        ns = ns / np.linalg.norm(ns, axis=1, keepdims=True)
        C = ns.T @ ns / len(ns)
        w, V = np.linalg.eigh(C)
        lam_max, e = float(w[1]), V[:, 1]
        for p in P_CANCEL:
            ray = centre + np.outer(D, e)
            mean_ray = L.refine_score(ray, ms, ns, True, p=p)
            sum_ray = L.refine_score(ray, ms, ns, False, p=p)
            mean_far, sum_far = float(mean_ray[-1]), float(sum_ray[-1])
            rows.append(dict(
                section=name, p=ptag(p), n_samples=len(ms), seed=seed,
                lambda_max=round(lam_max, 6), lambda_min=round(float(w[0]), 6),
                mean_at_centre=round(float(L.refine_score(centre, ms, ns, True, p=p)[0]), 6),
                mean_far=round(mean_far, 6),
                mean_far_over_lambda_max=round(mean_far / lam_max, 6),
                mean_far_rel_gap=f"{abs(mean_far - lam_max) / lam_max:.3e}",
                sum_max_on_ray=f"{float(sum_ray.max()):.6e}",
                sum_at_max_distance_units=round(float(D[int(np.argmax(sum_ray))]), 1),
                sum_far=f"{sum_far:.6e}",
                sum_far_over_max=f"{sum_far / float(sum_ray.max()):.3e}",
                far_distance_units=FAR))
            r = rows[-1]
            print(f"  {name:20s} p {r['p']}  lambda_max {r['lambda_max']:.4f}  mean far "
                  f"{r['mean_far']:.4f}  rel gap {r['mean_far_rel_gap']}  sum far/max "
                  f"{r['sum_far_over_max']}", flush=True)
    L.write_csv(os.path.join(L.EV, "exponent-ablation-cancellation.csv"), list(rows[0]), rows)
    worst_mean = max(float(r["mean_far_rel_gap"]) for r in rows)
    worst_sum = max(float(r["sum_far_over_max"]) for r in rows if r["p"] != "0.0")
    print(f"  worst relative gap of the mean from lambda_max: {worst_mean:.3e} (bar 1e-3)")
    print(f"  worst far field of the sum over its maximum:    {worst_sum:.3e} (bar 1e-3)")
    return 0 if worst_mean < 1e-3 and worst_sum < 1e-3 else 1


# ------------------------------------------------------------------ the fifteen scrolls

def estimates_for(scroll):
    """Every estimate of one scroll: 24 slices, 20 seeds, one per exponent, grid units."""
    t0 = time.perf_counter()
    rows = []
    for z in L.heights(scroll):
        s = L.grid15_slice(scroll, z)
        if s is None:
            continue
        mid, nrm, W, H = s
        for k in range(F.K):
            for p in P_LIST:
                xy, cap = L.estimate(mid, nrm, W, H, F.seed_of(z, k), False, p=p)
                rows.append(dict(scroll=scroll, z=z, k=k, seed=F.seed_of(z, k), p=ptag(p),
                                 x=float(xy[0]), y=float(xy[1]),
                                 inside=int(0 <= xy[0] <= W and 0 <= xy[1] <= H),
                                 capped=int(cap)))
    print(f"  {scroll:12s} {len(rows)} estimates in {time.perf_counter() - t0:.0f}s", flush=True)
    return rows


def run_scrolls(workers):
    raw = []
    if os.path.exists(RAW):
        for r in L.read_csv(RAW):
            raw.append(dict(r, z=int(r["z"]), k=int(r["k"]), seed=int(r["seed"]),
                            x=float(r["x"]), y=float(r["y"]), inside=int(r["inside"]),
                            capped=int(r["capped"])))
    done = {r["scroll"] for r in raw}
    todo = [s for s in L.CFG if s not in done]
    if todo:
        with Pool(workers) as pool:
            for part in pool.imap_unordered(estimates_for, todo):
                raw.extend(part)
                L.write_csv(RAW, RAW_COLS, raw)       # written after each scroll, resumable
    return raw


def read_raw():
    rows = []
    for r in L.read_csv(RAW):
        rows.append(dict(r, z=int(r["z"]), k=int(r["k"]), x=float(r["x"]), y=float(r["y"]),
                         inside=int(r["inside"]), capped=int(r["capped"])))
    return rows


def score(scroll, raw):
    """fifteen_k20.score, one row per exponent instead of one row per variant.

    Same slices, same metric (bench.errors on the control points inside the common z range), same
    baselines, same threshold, same bootstrap: 1000 resamples, generator seeded
    [20260916, scroll index, boot_index(p)].
    """
    cfg = L.CFG[scroll]
    sc, mm = cfg["grid_scale"], cfg["voxel_um"] / 1000.0
    ref = L.reference(scroll)
    zs = sorted({r["z"] for r in raw})
    W = None
    for z in zs:
        s = L.grid15_slice(scroll, z)
        if s:
            W = s[2]
            break
    base = L.baselines(scroll, W)
    poly = {}
    for p in P_LIST:
        poly[p] = np.zeros((F.K, len(zs), 3))
        for r in raw:
            if r["p"] == ptag(p):
                poly[p][r["k"], zs.index(r["z"])] = (r["x"] * sc, r["y"] * sc, r["z"] * sc)
    zlo = max([base["centroid"][:, 2].min(), base["fake_axis"][:, 2].min()] +
              [poly[v][0][:, 2].min() for v in poly])
    zhi = min([base["centroid"][:, 2].max(), base["fake_axis"][:, 2].max()] +
              [poly[v][0][:, 2].max() for v in poly])
    common = ref[(ref[:, 2] >= zlo) & (ref[:, 2] <= zhi)]
    cen_e, _ = L.errors(common, base["centroid"], mm)
    cen_med = float(np.median(cen_e))
    scroll_i = list(L.CFG).index(scroll)
    out = []
    for p in P_LIST:
        P = poly[p]
        m_k = np.array([np.median(L.errors(common, P[k], mm)[0]) for k in range(F.K)])
        rng = np.random.default_rng([F.BOOT_SEED, scroll_i, boot_index(p)])
        boot = np.empty(F.B)
        for b in range(F.B):
            pick = rng.integers(0, F.K, len(zs))
            pl = P[pick, np.arange(len(zs))]
            e, _ = L.errors(common, pl, mm)
            boot[b] = np.median(rng.choice(e, len(e)))
        lo, hi = np.percentile(boot, [2.5, 97.5])
        med = float(np.median(m_k))
        n_in = sum(r["inside"] for r in raw if r["p"] == ptag(p))
        out.append(dict(
            scroll=scroll, block=cfg["block"], p=ptag(p), voxel_um=cfg["voxel_um"],
            slices=len(zs), seeds=F.K, control_points=len(common),
            median_k0_mm=round(float(m_k[0]), 2), median_mm=round(med, 2),
            iqr_mm=round(float(np.percentile(m_k, 75) - np.percentile(m_k, 25)), 2),
            min_mm=round(float(m_k.min()), 2), max_mm=round(float(m_k.max()), 2),
            ci_lo_mm=round(float(lo), 2), ci_hi_mm=round(float(hi), 2),
            inside=n_in, inside_of=F.K * len(zs), outside=F.K * len(zs) - n_in,
            capped=sum(r["capped"] for r in raw if r["p"] == ptag(p)),
            centroid_mm=round(cen_med, 2),
            margin_vs_centroid_mm=round(cen_med - med, 2),
            margin_ci_lo_mm=round(cen_med - float(hi), 2),
            margin_ci_hi_mm=round(cen_med - float(lo), 2),
            margin_ci_includes_zero=int(cen_med - hi <= 0 <= cen_med - lo),
            beats_threshold=int(cen_med - med >= L.THRESHOLD_MM),
            bootstrap_resamples=F.B, bootstrap_seed=F.BOOT_SEED,
            bootstrap_index=boot_index(p)))
    return out


def spread(scroll, raw):
    """Spread between seeds: distance of the twenty estimates of a slice from their median, mm."""
    mm = L.CFG[scroll]["voxel_um"] / 1000.0
    out = []
    for p in P_LIST:
        d = []
        for z in sorted({r["z"] for r in raw}):
            Pxy = np.array([[r["x"], r["y"]] for r in raw
                            if r["p"] == ptag(p) and r["z"] == z])
            med = np.median(Pxy, 0)
            d.extend(np.hypot(*(Pxy - med).T) * mm)
        d = np.sort(np.array(d))
        out.append(dict(scroll=scroll, block=L.CFG[scroll]["block"], p=ptag(p),
                        n=len(d), spread_median_mm=round(float(np.median(d)), 2),
                        spread_p90_mm=round(float(np.percentile(d, 90)), 2),
                        spread_worst_mm=round(float(d[-1]), 2)))
    return out


def run_score():
    raw = read_raw()
    rows, spr = [], []
    for scroll in L.CFG:
        part = [r for r in raw if r["scroll"] == scroll]
        rows.extend(score(scroll, part))
        spr.extend(spread(scroll, part))
        print(f"  scored {scroll}", flush=True)
    # known reference: the p = 1 row must reproduce the published no-division row
    old = {q["scroll"]: q for q in L.read_csv(os.path.join(L.EV, "fifteen-k20.csv"))
           if q["variant"] == "no-division"}
    bad = []
    for r in rows:
        if r["p"] != "1.0":
            continue
        q = old[r["scroll"]]
        for a, b in (("median_mm", "median_mm"), ("ci_lo_mm", "ci_lo_mm"),
                     ("ci_hi_mm", "ci_hi_mm"), ("inside", "inside"),
                     ("margin_vs_centroid_mm", "margin_vs_centroid_mm")):
            if str(r[a]) != str(q[b]):
                bad.append((r["scroll"], a, q[b], r[a]))
    print("  known reference (p = 1 against the no-division row of fifteen-k20.csv):",
          "reproduced" if not bad else f"NOT reproduced: {bad}", flush=True)
    L.write_csv(os.path.join(L.EV, "exponent-ablation-fifteen-k20.csv"), list(rows[0]), rows)
    L.write_csv(os.path.join(L.EV, "exponent-ablation-seed-spread.csv"), list(spr[0]), spr)
    return 1 if bad else 0


# ------------------------------------------------------------------ the synthetic sections

def synth_one(job):
    """One section, one seed, one exponent: the field maximum and the estimate, in grid units."""
    name, ratio, ci, p, s = job
    make = list(SD.configs())[ci][2]
    rng = np.random.default_rng(50000 + s)
    mid, nrm = S.polyline_segments(make(rng))
    mid, nrm = SD.thin(mid, nrm, ratio, rng)
    ms, ns, _ = L.sample(mid, nrm, 60000 + s)
    g = np.arange(-SD.HALF, SD.HALF + 1, SD.STEP)
    LX, LY = np.meshgrid(SD.C[0] + g, SD.C[1] + g)
    lattice = np.stack([LX.ravel(), LY.ravel()], 1)
    sm = L.refine_score(lattice, ms, ns, False, p=p)
    fmax = lattice[int(np.argmax(sm))]
    est = L.estimate(mid, nrm, SD.W, SD.H, 60000 + s, False, p=p)[0]
    return name, p, s, len(mid), int((mid[:, 0] < SD.C[0]).sum()), fmax, est


def run_synthetic(workers):
    cfgs = list(SD.configs())
    jobs = [(name, ratio, ci, p, s) for ci, (name, ratio, _) in enumerate(cfgs)
            for p in P_LIST for s in SD.SEEDS]
    t0 = time.perf_counter()
    acc = {}
    with Pool(workers) as pool:
        for i, (name, p, s, nseg, left, fmax, est) in enumerate(
                pool.imap_unordered(synth_one, jobs), 1):
            a = acc.setdefault((name, p), dict(fmax=[], est=[], nseg=nseg, left=left))
            a["fmax"].append(fmax)
            a["est"].append(est)
            if i % 40 == 0:
                print(f"  {i}/{len(jobs)} ({time.perf_counter() - t0:.0f}s)", flush=True)
    rows = []
    for name, ratio, _ in cfgs:
        for p in P_LIST:
            a = acc[(name, p)]
            row = dict(section=name, density_ratio=ratio, objective="sum", p=ptag(p),
                       n_seeds=len(SD.SEEDS), segments=a["nseg"], segments_sparse_side=a["left"],
                       lattice_step=SD.STEP, lattice_half=SD.HALF)
            row.update({f"fieldmax_{k}": v for k, v in SD.summarise(np.array(a["fmax"])).items()})
            row.update({f"estimate_{k}": v for k, v in SD.summarise(np.array(a["est"])).items()})
            rows.append(row)
            print(f"  {name:14s} p {ptag(p)}  field max err "
                  f"{row['fieldmax_err_median_units']:7.1f} dx {row['fieldmax_dx_median_units']:7.1f}"
                  f"   estimate err {row['estimate_err_median_units']:7.1f} "
                  f"dx {row['estimate_dx_median_units']:7.1f}", flush=True)
    # known reference: the p = 1 rows must reproduce the sum rows of synthetic-density.csv
    old = {(q["section"], q["objective"]): q
           for q in L.read_csv(os.path.join(L.EV, "synthetic-density.csv"))}
    bad = []
    for r in rows:
        if r["p"] != "1.0":
            continue
        q = old[(r["section"], "sum")]
        for k in ("fieldmax_err_median_units", "fieldmax_dx_median_units",
                  "estimate_err_median_units", "estimate_dx_median_units"):
            if str(r[k]) != str(q[k]):
                bad.append((r["section"], k, q[k], r[k]))
    print("  known reference (p = 1 against the sum rows of synthetic-density.csv):",
          "reproduced" if not bad else f"NOT reproduced: {bad}", flush=True)
    L.write_csv(os.path.join(L.EV, "exponent-ablation-synthetic-density.csv"), list(rows[0]), rows)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--cancellation", action="store_true")
    ap.add_argument("--rate", action="store_true")
    ap.add_argument("--scrolls", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--workers", type=int, default=15)
    a = ap.parse_args()
    rc = 0
    if a.check:
        rc |= check()
    if a.cancellation:
        rc |= cancellation()
    if a.rate:
        rc |= rate()
    if a.scrolls:
        run_scrolls(a.workers)
    if a.score:
        rc |= run_score()
    if a.synthetic:
        rc |= run_synthetic(a.workers)
    return rc


if __name__ == "__main__":
    sys.exit(main())
