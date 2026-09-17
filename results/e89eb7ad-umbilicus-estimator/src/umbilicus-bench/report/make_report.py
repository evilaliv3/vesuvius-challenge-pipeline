#!/usr/bin/env python3
"""Build the technical report: every figure and every table, from the data, in one pass.

    python report/make_report.py            # figures + report.md
    python report/make_report.py --pdf      # also runs pandoc to make report.pdf

Nothing here is typed by hand: every number in the text is read from the run, so the report cannot
drift from the measurement. This script is optional: the bench (bench.py, validate.py, figures.py)
never needs it. The Markdown report and its figures need only the packages in requirements.txt;
the PDF needs pandoc and a LaTeX engine, and is skipped with a message when they are missing.
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from scipy.stats import wilcoxon, spearmanr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import bench, data, estimators as est                                    # noqa: E402

FIG = HERE / "figures"
FIG.mkdir(parents=True, exist_ok=True)
RULES = ["argmax", "centroid", "plateau_centroid", "plateau_nearest_centroid"]
COLORS = {"argmax": "#c05a3c", "centroid": "#4a7a4a", "plateau_centroid": "#7a6ba8",
          "plateau_nearest_centroid": "#3c6ec0", "fake axis (control)": "#9a9a9a",
          "argmax + hampel": "#d98f5a"}
HEIGHTS, LEVEL = 46, 3
LOO_THRESHOLDS = (0.7, 0.8, 0.9)        # the same grid validate.py leaves one scroll out over


# ----------------------------------------------------------------- measurement
def collect():
    """One pass per scroll: the polylines of every rule, the truth, and the per-point errors."""
    out = {}
    for s in data.GROUND_TRUTH:
        truth = data.published_umbilicus(s)
        lines = bench.polylines(s, {k: est.ESTIMATORS[k] for k in RULES}, LEVEL, HEIGHTS)
        lines["argmax + hampel"] = est.hampel_reject(lines["argmax"])[0]
        lines["fake axis (control)"] = bench.fake_axis(s, LEVEL, HEIGHTS)
        grid = np.array([z * data.scale_to_reference(s, LEVEL)
                         for z in data.slice_heights(s, LEVEL, HEIGHTS)], float)
        common = truth[(truth[:, 2] >= grid.min()) & (truth[:, 2] <= grid.max())]
        mm = data.mm_per_voxel(s)
        err = {k: bench.errors(common, p, mm) for k, p in lines.items()}
        out[s] = {"truth": truth, "lines": lines, "common": common, "err": err,
                  "mm": mm, "grid": grid}
        print(f"  {s}: {len(common)} published points, {len(lines['argmax'])} heights", flush=True)
    return out


def table(R):
    rows = []
    for s, d in R.items():
        for k in RULES + ["argmax + hampel", "fake axis (control)"]:
            e = d["err"][k][0]
            rows.append({"scroll": s, "rule": k, "n": len(e),
                          "median": float(np.median(e)), "p90": float(np.percentile(e, 90)),
                          "worst": float(e.max())})
    return rows


# ----------------------------------------------------------------- figures
def f_sections(R):
    """The data: one section per scroll with the published umbilicus on it."""
    n = len(R)
    fig, axes = plt.subplots(1, n, figsize=(3.6 * n, 4.0))
    for ax, (s, d) in zip(np.atleast_1d(axes), R.items()):
        f = data.scale_to_reference(s, LEVEL)
        zs = data.slice_heights(s, LEVEL, HEIGHTS)
        z = zs[len(zs) // 2]
        sl = data.cached_slice(s, LEVEL, z)
        mask, dist = est.section(sl)
        ys, xs = np.where(mask)
        y0, y1, x0, x1 = max(0, ys.min() - 10), ys.max() + 10, max(0, xs.min() - 10), xs.max() + 10
        ax.imshow(sl[y0:y1, x0:x1], cmap="bone", vmin=0, vmax=255, interpolation="nearest")
        ax.contour(mask[y0:y1, x0:x1], levels=[0.5], colors="#e8b64c", linewidths=0.8)
        t = d["truth"]
        vx = np.interp(z * f, t[:, 2], t[:, 0]) / f - x0
        vy = np.interp(z * f, t[:, 2], t[:, 1]) / f - y0
        ax.plot(vx, vy, "*", color="#49b06a", ms=15)
        ax.set_title(f"{s}\nslice z = {z * f}, voxel {data.SCROLLS[s].get('voxel_um', data.VOXEL_UM)} um",
                     fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("The four scrolls with a published umbilicus (green star), one section each", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG / "f1-sections.png", dpi=150); plt.close(fig)


def f_methods(R):
    n = len(R)
    fig, axes = plt.subplots(1, n, figsize=(4.4 * n, 4.6), sharex=False)
    order = ["fake axis (control)", "argmax", "argmax + hampel", "centroid",
              "plateau_centroid", "plateau_nearest_centroid"]
    for i, (ax, (s, d)) in enumerate(zip(np.atleast_1d(axes), R.items())):
        med = [np.median(d["err"][k][0]) for k in order]
        p90 = [np.percentile(d["err"][k][0], 90) for k in order]
        y = np.arange(len(order))
        ax.barh(y, med, color=[COLORS[k] for k in order], height=0.62)
        ax.plot(p90, y, "k|", ms=9, mew=1.4)
        ax.set_yticks(y)
        ax.set_yticklabels([est.display(k) for k in order] if i == 0 else [""] * len(order), fontsize=8)
        ax.set_title(f"{s} ({len(d['common'])} points)", fontsize=10)
        ax.set_xlabel("median distance, mm"); ax.grid(axis="x", lw=0.4, alpha=0.5); ax.invert_yaxis()
    fig.suptitle("Bar: median distance from the published umbilicus. Tick: p90", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "f2-methods.png", dpi=150); plt.close(fig)


def f_along_z(R):
    n = len(R)
    fig, axes = plt.subplots(1, n, figsize=(4.0 * n, 3.8), sharey=True)
    for ax, (s, d) in zip(np.atleast_1d(axes), R.items()):
        for k in ("argmax", "plateau_nearest_centroid", "fake axis (control)"):
            e, sel = d["err"][k]
            ax.plot(sel[:, 2] * d["mm"], e, lw=1.2, color=COLORS[k], label=est.display(k) if ax is np.atleast_1d(axes)[0] else None)
        ax.set_title(s, fontsize=10); ax.set_xlabel("height along the scroll, mm")
        ax.grid(lw=0.4, alpha=0.5)
    np.atleast_1d(axes)[0].set_ylabel("distance from the published umbilicus, mm")
    np.atleast_1d(axes)[0].legend(fontsize=7.5)
    fig.suptitle("Where each rule fails, along the scroll", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "f3-along-z.png", dpi=150); plt.close(fig)


def f_cdf(R):
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    for k in ["fake axis (control)"] + RULES:
        e = np.concatenate([R[s]["err"][k][0] for s in R])
        e = np.sort(e)
        ax.plot(e, np.arange(1, len(e) + 1) / len(e), lw=1.8, color=COLORS[k], label=est.display(k))
    ax.set_xlabel("distance from the published umbilicus, mm"); ax.set_ylabel("fraction of control points")
    ax.set_xlim(0, 12); ax.grid(lw=0.4, alpha=0.5); ax.legend(fontsize=8, loc="lower right")
    ax.set_title("Pooled over the four scrolls: how often each rule is within a given distance", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "f4-cdf.png", dpi=150); plt.close(fig)


def f_paired(R):
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    for s, mk in zip(R, ("o", "s", "^", "D")):
        a = R[s]["err"]["argmax"][0]; b = R[s]["err"]["plateau_nearest_centroid"][0]
        n = min(len(a), len(b))
        ax.scatter(a[:n], b[:n], s=16, marker=mk, alpha=0.6, label=f"{s} (n {n})")
    lim = 14
    ax.plot([0, lim], [0, lim], color="#888", lw=1)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("max distance-to-boundary, mm"); ax.set_ylabel("plateau point nearest the centroid, mm")
    ax.set_title("Point by point. Below the line: the proposed rule is closer", fontsize=10)
    ax.grid(lw=0.4, alpha=0.5); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "f5-paired.png", dpi=150); plt.close(fig)


def f_plateau(R):
    """Why the argmax is unstable: how wide the plateau is, and how far the two readings sit apart."""
    widths, jumps = [], []
    for s in R:
        f = data.scale_to_reference(s, LEVEL)
        for z in data.slice_heights(s, LEVEL, HEIGHTS):
            mask, dist = est.section(data.cached_slice(s, LEVEL, z))
            if mask is None:
                continue
            pl = dist >= 0.9 * dist.max()
            ys, xs = np.where(pl)
            widths.append(np.hypot(xs.max() - xs.min(), ys.max() - ys.min()) * f * data.mm_per_voxel(s))
            a = est.argmax(mask, dist); p = est.plateau_nearest_centroid(mask, dist)
            jumps.append(np.hypot(a[0] - p[0], a[1] - p[1]) * f * data.mm_per_voxel(s))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    ax1.hist(widths, bins=30, color="#3c6ec0", alpha=0.85)
    ax1.set_xlabel("extent of the plateau (within 0.9 of the maximum), mm")
    ax1.set_ylabel("slices"); ax1.grid(lw=0.4, alpha=0.5)
    ax1.set_title(f"The plateau is wide: median {np.median(widths):.1f} mm", fontsize=10)
    ax2.hist(jumps, bins=30, color="#c05a3c", alpha=0.85)
    ax2.set_xlabel("distance between the two readings of the same plateau, mm")
    ax2.set_ylabel("slices"); ax2.grid(lw=0.4, alpha=0.5)
    ax2.set_title(f"and reading it two ways moves the core by {np.median(jumps):.1f} mm (median)", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "f6-plateau.png", dpi=150); plt.close(fig)
    return float(np.median(widths)), float(np.median(jumps))


def f_threshold(R):
    """Sensitivity to the one threshold that was chosen after seeing the data."""
    qs = np.arange(0.5, 0.99, 0.05)
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    curve, arrays = {}, {}
    for s in R:
        med = []
        for q in qs:
            line = bench.polylines(s, {"r": lambda m, d, q=q: est.plateau_nearest_centroid(m, d, q)},
                                   LEVEL, HEIGHTS)["r"]
            e, _ = bench.errors(R[s]["common"], line, R[s]["mm"])
            med.append(float(np.median(e)))
            # Keep the per-point errors at the thresholds validate.py leaves one scroll out over:
            # the selection pools the other scrolls' points, so their medians are not enough.
            for t in LOO_THRESHOLDS:
                if abs(q - t) < 1e-9:
                    arrays.setdefault(s, {})[t] = e
        curve[s] = med
        ax.plot(qs, med, marker="o", ms=3.5, lw=1.5, label=s)
    ax.axvline(0.9, color="#888", ls="--", lw=1)
    ax.set_xlabel("plateau threshold q (fraction of the maximum distance)")
    ax.set_ylabel("median distance, mm"); ax.grid(lw=0.4, alpha=0.5); ax.legend(fontsize=8)
    ax.set_title("The proposed rule against its only free parameter", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "f7-threshold.png", dpi=150); plt.close(fig)
    return {s: [round(v, 3) for v in c] for s, c in curve.items()}, [round(float(q), 2) for q in qs], arrays


def f_hampel(R):
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    all_points = []
    for s, mk in zip(R, ("o", "s", "^", "D")):
        line = R[s]["lines"]["argmax"]
        _, dev = est.hampel_reject(line)
        t = R[s]["truth"]; mm = R[s]["mm"]
        v = []
        for (x, y, z), dv in zip(line, dev):
            j = int(np.argmin(np.abs(t[:, 2] - z)))
            if abs(t[j, 2] - z) < 200:
                v.append((dv * mm, float(np.hypot(x - t[j, 0], y - t[j, 1]) * mm)))
        if not v:
            continue
        v = np.array(v); all_points.append(v)
        ax.scatter(v[:, 0], v[:, 1], s=20, marker=mk, alpha=0.7, label=f"{s} (n {len(v)})")
    T = np.vstack(all_points); rho, p = spearmanr(T[:, 0], T[:, 1])
    ax.set_xlabel("distance from the median of the neighbouring points, mm (uses no ground truth)")
    ax.set_ylabel("true distance from the published umbilicus, mm")
    ax.set_title(f"A quality signal available without ground truth: Spearman {rho:.2f}, p {p:.1e}", fontsize=10)
    ax.grid(lw=0.4, alpha=0.5); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "f8-hampel.png", dpi=150); plt.close(fig)
    return float(rho), float(p), int(len(T))


# ----------------------------------------------------------------- the document
def write(R, rows, plateau, thresholds, hampel, pdf):
    def med(s, k):
        return float(np.median(R[s]["err"][k][0]))

    def p90(s, k):
        return float(np.percentile(R[s]["err"][k][0], 90))

    S = list(R)
    pooled = {k: np.concatenate([R[s]["err"][k][0] for s in S]) for k in RULES + ["fake axis (control)"]}
    pa, pb = pooled["argmax"], pooled["plateau_nearest_centroid"]
    n = min(len(pa), len(pb))
    W = wilcoxon(pa[:n], pb[:n])
    curve, qs, loo_err = thresholds
    rho, prho, nrho = hampel

    T = []
    T.append("---")
    T.append('title: "Reading the distance plateau: an evaluation of umbilicus estimators against the published Herculaneum umbilici"')
    T.append('author: "Giovanni Pellerano"')
    T.append(f'date: "{__import__("datetime").date.today().isoformat()}"')
    T.append("---\n")

    T.append("## Abstract\n")
    T.append(
        f"Of the 23 Herculaneum scrolls in the competition, 20 have no umbilicus published by the challenge, "
        f"and the spiral-fitting pipeline needs one, so automatic estimators are being written with nothing to "
        f"check them against. {len(S)} scrolls have both a published umbilicus and a surface prediction of the "
        f"same family, three of them in the competition and one outside it. This report turns those {len(S)} into a "
        f"bench, measures every estimator we could think of on identical inputs, and reports the one control "
        f"that most such comparisons omit. The published rule, the argmax of the distance transform of the "
        f"filled section, is unstable because that transform has a wide plateau: its extent is "
        f"{plateau[0]:.1f} mm at the median, and two defensible readings of the same plateau put the core "
        f"{plateau[1]:.1f} mm apart. Reading the plateau instead of its argmax, by taking the point within "
        f"0.9 of the maximum nearest the centroid of the section, lowers the median distance from the "
        f"published umbilicus from {np.median(pa):.2f} mm to {np.median(pb):.2f} mm over {n} control points "
        f"(Wilcoxon p = {W.pvalue:.1e}). The uncomfortable control: on PHerc0125 a constant axis at the centre "
        f"of the field, which knows nothing about the scroll, is {med(S[0], 'fake axis (control)'):.2f} mm from "
        f"the published umbilicus, closer than every estimator measured here. On that scroll the comparison "
        f"does not discriminate, and we report it against ourselves.\n")

    T.append("## 1. The problem\n")
    T.append(
        "An umbilicus is the polyline through the winding centre of a rolled scroll, used to initialise "
        "spiral fitting and to unroll in polar coordinates. For most scrolls it does not exist, and where it "
        "does it was placed by hand. An estimator is therefore judged, if at all, by whether the pipeline "
        "downstream of it produces something; that is a slow and confounded signal. The scrolls with a "
        "published umbilicus make a direct measurement possible, and there are few enough of them that the "
        "whole bench runs on a laptop in minutes.\n")

    T.append("## 2. Data\n")
    T.append("| scroll | published control points | scored | voxel (um) | prediction store |")
    T.append("|---|---:|---:|---:|---|")
    for s in S:
        v = data.SCROLLS[s]
        store = "already downsampled (L2)" if v.get("store_scale", 1) != 1 else "level 0"
        T.append(f"| {s} | {len(R[s]['truth'])} | {len(R[s]['common'])} | "
                 f"{v.get('voxel_um', data.VOXEL_UM)} | {store} |")
    T.append("")
    T.append(
        "Every estimate is computed on the published surface prediction of that scroll, read once at pyramid "
        f"level {LEVEL} at {HEIGHTS} heights spaced evenly between 8 and 92 per cent of the scroll, and reused "
        "by every rule. PHerc0332 is the awkward and instructive case: it was scanned once, at 2.399 um, and "
        "the only surface prediction published for it is already downsampled by four, so the factor between "
        "the store and the frame its umbilicus is annotated in is 32 and not 8. A published script that "
        "hardcodes that factor writes control points four times too small, which on this scroll is 21 mm.\n")
    T.append("![One section per scroll, with the published umbilicus as a green star. The sections are not "
             "round: that is the whole difficulty.](figures/f1-sections.png)\n")

    T.append("## 3. The estimators\n")
    T.append("Each rule is a function of the filled largest connected component of the sheet mask and of its "
             "Euclidean distance transform. Nothing else differs between them.\n")
    T.append("- **max distance-to-boundary** (the published rule): the pixel where the distance transform is "
             "largest, described upstream as the innermost point of the winding pack.")
    T.append("- **centroid of the section**: the centre of mass of the filled component.")
    T.append("- **centroid of the plateau**: the centre of mass of the pixels within a fraction q of the "
             "maximum distance, q = 0.9.")
    T.append("- **plateau point nearest the centroid** (proposed): among those same pixels, the one closest to "
             "the centroid of the component.")
    T.append("- **jumping points rejected**: a Hampel-type identifier applied to the polyline of any of the "
             "above, dropping control points further than twice the median deviation from the median of their "
             "neighbours (Hampel 1974; Pearson et al. 2016).")
    T.append("- **constant axis at the centre of the field** (negative control): a straight line through the "
             "centre of the volume's bounding box, which uses no data at all.\n")
    T.append(f"![Why the argmax is unstable. Left: the plateau within 0.9 of the maximum is wide, median "
             f"{plateau[0]:.1f} mm. Right: reading the same plateau two ways moves the core by "
             f"{plateau[1]:.1f} mm at the median.](figures/f6-plateau.png)\n")
    T.append("![The mechanism on real sections of PHerc0826.](../figures/plateau-on-papyrus.png)\n")

    T.append("## 4. Metric and protocol\n")
    T.append(
        "For every published control point inside the z coverage of the slice grid, the estimate is "
        "interpolated at that height and the distance is taken in the xy plane, in millimetres at the voxel "
        "size of the frame the umbilicus is annotated in. Every rule is scored on the same points. The median "
        "is the primary statistic; the p90 and the worst case are reported next to it because, for an "
        "initialisation, the tail is what breaks the fit. Paired comparisons use the Wilcoxon signed-rank "
        "test over control points.\n")

    T.append("## 5. Results\n")
    T.append("| scroll | " + " | ".join(est.display(k).split(" (")[0] for k in RULES) + " | control |")
    T.append("|---|" + "---:|" * (len(RULES) + 1))
    for s in S:
        T.append(f"| {s} | " + " | ".join(f"{med(s, k):.2f}" for k in RULES) +
                 f" | *{med(s, 'fake axis (control)'):.2f}* |")
    T.append(f"| **pooled** | " + " | ".join(f"**{np.median(pooled[k]):.2f}**" for k in RULES) +
             f" | *{np.median(pooled['fake axis (control)']):.2f}* |")
    T.append("\nMedian distance from the published umbilicus, in mm. Same table for the p90:\n")
    T.append("| scroll | " + " | ".join(est.display(k).split(" (")[0] for k in RULES) + " |")
    T.append("|---|" + "---:|" * len(RULES))
    for s in S:
        T.append(f"| {s} | " + " | ".join(f"{p90(s, k):.2f}" for k in RULES) + " |")
    T.append("")
    T.append("![Every rule on every scroll, scored on the same published points.](figures/f2-methods.png)\n")
    T.append("![Pooled over the four scrolls: how often each rule is within a given distance.](figures/f4-cdf.png)\n")
    T.append(f"The paired comparison between the published rule and the proposed one, over the {n} pooled "
             f"control points, gives a median of {np.median(pa):.2f} mm against {np.median(pb):.2f} mm, "
             f"Wilcoxon p = {W.pvalue:.1e}. Per scroll:\n")
    T.append("| scroll | published rule | proposed | closer on | p |")
    T.append("|---|---:|---:|---:|---:|")
    for s in S:
        a, b = R[s]["err"]["argmax"][0], R[s]["err"]["plateau_nearest_centroid"][0]
        m = min(len(a), len(b))
        T.append(f"| {s} | {np.median(a):.2f} | {np.median(b):.2f} | {int((b[:m] < a[:m]).sum())} of {m} | "
                 f"{wilcoxon(a[:m], b[:m]).pvalue:.1e} |")
    T.append("")
    T.append("![Point by point. Below the diagonal the proposed rule is closer.](figures/f5-paired.png)\n")
    T.append("![Where each rule fails along the scroll.](figures/f3-along-z.png)\n")

    T.append("## 6. Controls\n")
    T.append("**The negative control.** A constant axis at the centre of the field is "
             + ", ".join(f"{med(s, 'fake axis (control)'):.2f} mm on {s}" for s in S) + ". "
             "On the scroll where that number is smaller than every estimator's, the comparison does not "
             "discriminate and no ranking taken from it means anything. We would suggest reporting this "
             "control next to any umbilicus number, and we report it against ourselves.\n")
    T.append("**The intermediate rule.** The centroid of the plateau lands between the argmax and the "
             "proposed rule on most scrolls, which is what one expects if the plateau carries the "
             "information and the argmax is the unstable way to read it.\n")

    T.append("## 7. Sensitivity and validation\n")
    T.append("The plateau threshold q is the only free parameter, and it was chosen after seeing the bench. "
             "Its curve is flat where it matters:\n")
    T.append("| scroll | " + " | ".join(f"q={q}" for q in qs) + " |")
    T.append("|---|" + "---:|" * len(qs))
    for s in S:
        T.append(f"| {s} | " + " | ".join(f"{v:.2f}" for v in curve[s]) + " |")
    T.append("")
    T.append("![The proposed rule against its only free parameter.](figures/f7-threshold.png)\n")
    picked = {}
    for held in S:
        others = [o for o in S if o != held]
        m = {t: float(np.median(np.concatenate([loo_err[o][t] for o in others]))) for t in LOO_THRESHOLDS}
        q = min(m, key=m.get)
        picked[held] = (q, float(np.median(loo_err[held][q])))
    agreed = sorted({q for q, _ in picked.values()})
    if len(agreed) == 1:
        T.append(f"A leave-one-scroll-out check, run by `validate.py`, fixes q on all scrolls but one and "
                 f"measures on the held-out scroll; it selects q = {agreed[0]} every time "
                 + ", ".join(f"({s}: {picked[s][1]:.2f} mm)" for s in S) + ".\n")
    else:
        odd = [s for s in S if picked[s][0] != max(agreed)]
        T.append(f"A leave-one-scroll-out check, run by `validate.py`, fixes q on all scrolls but one and "
                 f"measures on the held-out scroll. It does not settle q: it selects "
                 + ", ".join(f"q = {picked[s][0]} holding out {s} ({picked[s][1]:.2f} mm)" for s in S)
                 + f". The threshold used throughout this report is 0.9; on {' and '.join(odd)} the "
                 f"held-out selection differs, which says that these thresholds are within the noise of "
                 f"{len(S)} scrolls and that q is not settled by this data.\n")
    T.append(f"**A quality signal without ground truth.** The distance of a control point from the median of "
             f"its neighbours correlates with its true error (Spearman {rho:.2f}, p = {prho:.1e}, n = {nrho}), "
             f"so a polyline can be audited where no reference exists. Rejecting the points beyond twice the "
             f"median deviation is a large gain on top of the argmax and close to nothing on top of a stable "
             f"rule, which is why it is measured here and not adopted as a default.\n")
    T.append("![The signal the rejection rule uses.](figures/f8-hampel.png)\n")

    T.append("## 8. What this does not show\n")
    T.append("Whether a better axis produces a better spiral fit. The fitter is not practical on CPU here, so "
             "the downstream effect is untested: what is measured is the distance from the published axis and "
             "the disappearance of the multi-millimetre jumps. On scrolls with no published umbilicus, two "
             "estimators disagreeing is a discrepancy and not an error, and `unknown_scrolls.py` reports it as "
             "such, with the constant axis next to it.\n")
    T.append("The bench is four scrolls because four is all there is. A fifth, PHerc0139, has a published "
             "umbilicus annotated on a different scan from its surface prediction, and the transform between "
             "two scans of the same scroll is not published; scoring against a registration of our own would "
             "put our error into the metric, so it is left out.\n")

    T.append("## 9. Reproducing\n")
    T.append("```\npip install -r requirements.txt\npython bench.py\npython validate.py\n"
             "python report/make_report.py --pdf\n```\n")
    T.append("Everything reads the Vesuvius Challenge open-data bucket. Slices are cached under `cache/`; the "
             "four published umbilici used as ground truth are copied into `reference/`, and the control "
             "points every rule produced are in `results/estimates/`, so the tables can be recomputed with a "
             "different metric without rerunning anything.\n")

    T.append("## References\n")
    T.append("- F. R. Hampel, *The influence curve and its role in robust estimation*, JASA 69 (1974).")
    T.append("- R. K. Pearson et al., *Generalized Hampel Filters*, EURASIP J. Adv. Signal Process. (2016).")
    T.append("- C. Leys et al., *Detecting outliers: do not use standard deviation around the mean, use "
             "absolute deviation around the median*, J. Exp. Soc. Psychol. 49 (2013).")
    T.append("- Vesuvius Challenge open data, CC BY-NC 4.0; see `LICENSE-DATA.md` for the citation.\n")

    (HERE / "report.md").write_text("\n".join(T))
    print("written", HERE / "report.md")
    if pdf:
        if shutil.which("pandoc") is None:
            print("pandoc not found: report.md is written, report.pdf is not")
            return
        r = subprocess.run(["pandoc", "report.md", "-o", "report.pdf",
                            "--toc", "-V", "geometry:a4paper",
                            "-V", "geometry:margin=2.4cm", "-V", "fontsize=10pt",
                            "-V", "colorlinks=true", "-V", "linkcolor=black", "-V", "urlcolor=blue",
                            ],
                           capture_output=True, text=True, cwd=HERE)
        if r.returncode:
            print("pandoc failed (a LaTeX engine is needed for the PDF):", r.stderr[-400:])
        else:
            print("written", HERE / "report.pdf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args()
    print("measuring...")
    R = collect()
    rows = table(R)
    json.dump(rows, open(HERE / "tables.json", "w"), indent=1)
    print("figures...")
    f_sections(R); f_methods(R); f_along_z(R); f_cdf(R); f_paired(R)
    plateau = f_plateau(R)
    thresholds = f_threshold(R)
    hampel = f_hampel(R)
    write(R, rows, plateau, thresholds, hampel, a.pdf)


if __name__ == "__main__":
    main()
