# This file is a frozen copy of the figure script of the normal grid run of September, the run
# the figures of the finding were drawn in. It differs from the copy that drew them in the paths
# and in nothing that computes: the absolute paths of the machine the measurements ran on are
# replaced by paths inside this folder, resolved from the file's own location. One divergence
# beyond the paths is recorded rather than hidden, the f5 docstring, which said "two independent
# annotations of one scroll" and says here what the two umbilici are, the second being a per
# slice centroid of the papyrus mask.
#
# The two labels over the score field are white, and are meant to be. The rule for a word on a
# figure is white on colour and black on white, whichever of the two reads better, and never a
# word in two tones: no casing, no outline. Both of these lie on the dark end of the field, so
# white is what the rule leaves. They were briefly made black on a light casing on 2026-09-19 and
# put back the same day when the rule changed. The marks are white too, which is a separate
# question with the same answer here: this script draws the field in viridis, where a white mark
# reads, and tools/figure_umbilicus_redraw.py swaps the ramp and the marks together. A mark may
# carry a casing, a word may not.
"""The figures of the finding, drawn from the evidence files and from nothing else.

Plan and captions: FIGURE.md. The captions say what the panels are; the claim is carried by the
number, not by the picture.

    python figure_umbilicus.py            # every figure
    python figure_umbilicus.py f1 f4      # only those
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import villa_estimator as ve
from gridstore import read_grid, segments

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(os.path.dirname(HERE), "evidence")
FIG = os.path.join(HERE, "figures")
AS_IS, FIXED, BASE = "#b5651d", "#1f4e79", "#7a7a7a"


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"written {FIG}/{name}.svg")


def rows():
    with open(os.path.join(EV, "fifteen.csv")) as fh:
        return list(csv.DictReader(fh))


CFG = json.load(open(os.path.join(HERE, "fifteen-config.json")))


def reference(scroll):
    """That scroll's reference control points, level 0 voxels, sorted by z."""
    p = CFG[scroll]["reference"]
    d = json.load(open(p if os.path.isabs(p) else os.path.join(HERE, p)))
    pts = d["control_points"] if isinstance(d, dict) else d
    a = np.array([[q["x"], q["y"], q["z"]] for q in pts if not q.get("rejected")], float)
    return a[np.argsort(a[:, 2])]


def control_point(scroll, z):
    """The reference umbilicus of `scroll` at height z, in the units of its normal grid."""
    a = reference(scroll)
    sc = CFG[scroll]["grid_scale"]
    z0 = z * sc
    return np.array([np.interp(z0, a[:, 2], a[:, 0]) / sc,
                     np.interp(z0, a[:, 2], a[:, 1]) / sc])


def mm_per_unit(scroll):
    """Millimetres per unit of that scroll's normal grid."""
    return CFG[scroll]["voxel_um"] / 1000.0 * CFG[scroll]["grid_scale"]


def scale_bar(ax, mm_px, length_mm=10.0, label=None):
    """A bar of `length_mm` at the true resolution, drawn inside the axes."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    n = length_mm / mm_px
    x = x0 + 0.06 * (x1 - x0)
    y = y0 + 0.07 * (y1 - y0)
    ax.plot([x, x + n], [y, y], "-", color="w", lw=2.6, solid_capstyle="butt")
    ax.text(x + n / 2, y + 0.022 * (y1 - y0), label or f"{length_mm:.0f} mm",
            color="w", fontsize=7, ha="center", va="bottom")


def border_hit(a, b, lo, hi, inset=0.02):
    """Where the ray from `a` towards `b` crosses the border of the square window."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    span = hi - lo
    ts = []
    for i in (0, 1):
        if d[i] > 0:
            ts.append((hi - inset * span - a[i]) / d[i])
        elif d[i] < 0:
            ts.append((lo + inset * span - a[i]) / d[i])
    t = min([q for q in ts if q > 0] or [1.0])
    return a + t * d


def score_fields(mid, nrm, seed, lo, hi, n=200):
    """Both variants of the refinement score over one square window, on the same samples.

    Returns the sampled segments, the window edges and a dict variant -> field, so that the two
    panels of a figure can never come from two different draws of the same slice.
    """
    ms, ns, _ = ve.sample(mid, nrm, seed)
    g = np.linspace(lo, hi, n)
    GX, GY = np.meshgrid(g, g)
    L = np.stack([GX.ravel(), GY.ravel()], 1)
    return ms, ns, g, {d: ve.refine_score(L, ms, ns, d).reshape(GX.shape) for d in (True, False)}


def field_panels(axes, scroll, path, z, seed, pad=0.10, n=200, climb=False):
    """The two score fields of one slice, on one common dimensionless scale.

    A weighted mean and a weighted sum have different units, so an absolute colour scale shared
    between them would flatten one panel and compare nothing. Both panels are therefore divided
    by the score at the published control point, which is the same physical place in both, and
    the two denominators are printed in the panels. Neither panel is scaled to its own range.
    """
    h, paths, _ = read_grid(path)
    mid, nrm = segments(paths)
    W, H = float(h["bounds"][2]), float(h["bounds"][3])
    lo, hi = -pad * W, (1 + pad) * W
    ms, ns, g, fields = score_fields(mid, nrm, seed, lo, hi, n)
    cp = control_point(scroll, z)
    mm_px = mm_per_unit(scroll)

    ratio, denom, stop, trace = {}, {}, {}, {}
    for divide in (True, False):
        denom[divide] = float(ve.refine_score(np.array([cp]), ms, ns, divide)[0])
        ratio[divide] = fields[divide] / denom[divide]
        tr = [] if climb else None
        stop[divide], _ = ve.estimate(mid, nrm, W, H, seed, divide, trace=tr)
        trace[divide] = np.array(tr) if climb else None
    vmax = max(r.max() for r in ratio.values())

    im = None
    for ax, divide, title in ((axes[0], True, "as published"),
                              (axes[1], False, "line 116 removed")):
        im = ax.imshow(ratio[divide], origin="lower", extent=(lo, hi, lo, hi),
                       cmap="viridis", vmin=0.0, vmax=vmax)
        ax.plot([0, W, W, 0, 0], [0, 0, H, H, 0], "-", color="w", lw=.9, alpha=.75)
        ax.plot(mid[::80, 0], mid[::80, 1], ".", color="w", ms=.35, alpha=.45)
        if climb and len(trace[divide]) > 1:
            tr = trace[divide]
            ax.plot(tr[:, 0], tr[:, 1], "-", color="w", lw=1.1, alpha=.95)
            ax.plot(tr[0, 0], tr[0, 1], "s", mfc="none", mec="w", ms=7, mew=1.4)
            out = np.where((tr[:, 0] < lo) | (tr[:, 0] > hi) |
                           (tr[:, 1] < lo) | (tr[:, 1] > hi))[0]
            if len(out):
                a = tr[max(out[0] - 1, 0)]
                ax.annotate("", xy=tuple(border_hit(a, stop[divide], lo, hi)), xytext=tuple(a),
                            arrowprops=dict(arrowstyle="-|>", color="w", lw=1.3))
        ax.plot(*cp, "x", color="w", ms=11, mew=2.0)
        d_mm = float(np.hypot(*(stop[divide] - cp))) * mm_px
        if lo <= stop[divide][0] <= hi and lo <= stop[divide][1] <= hi:
            ax.plot(*stop[divide], "o", mfc="none", mec="w", ms=11, mew=1.8)
        elif not climb:
            # The stop is outside the drawn window, and widening the window until it fits would
            # leave nothing else visible. The arrow leaves the cross along the true direction to
            # the stop and ends where that direction crosses the border; the distance is in the
            # panel title.
            ax.annotate("", xy=tuple(border_hit(cp, stop[divide], lo, hi)), xytext=tuple(cp),
                        arrowprops=dict(arrowstyle="-|>", color="w", lw=1.4, alpha=.9))
        ax.set_title(f"{title}, stop at {d_mm:,.2f} mm from the cross", fontsize=9)
        ax.text(.03, .955, f"score at the cross {denom[divide]:.3f}", transform=ax.transAxes,
                color="w", fontsize=7, va="top")
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_xlim(lo, hi), ax.set_ylim(lo, hi)
        scale_bar(ax, mm_px)
        # A figure may not be the only place a number lives, so the two distances a reader takes
        # off these panels are written to evidence/ and reach the paper as macros like every other
        # figure. make_numbers.py reads this file.
        record_stop(scroll, z, divide, cp, stop[divide], denom[divide], mm_px)
    return im, vmax, mm_px


def record_stop(scroll, z, divide, cp, stop, denom, mm_px):
    path = os.path.join(EV, "field-stops.csv")
    cols = ["scroll", "slice_z", "variant", "control_x", "control_y", "stop_x", "stop_y",
            "stop_mm", "score_at_control"]
    rows = {}
    if os.path.exists(path):
        with open(path) as fh:
            for q in csv.DictReader(fh):
                rows[(q["scroll"], q["slice_z"], q["variant"])] = q
    key = (scroll, str(z), "as-is" if divide else "no-division")
    rows[key] = dict(scroll=scroll, slice_z=z, variant=key[2],
                     control_x=round(float(cp[0]), 1), control_y=round(float(cp[1]), 1),
                     stop_x=round(float(stop[0]), 1), stop_y=round(float(stop[1]), 1),
                     stop_mm=round(float(np.hypot(*(stop - cp))) * mm_px, 2),
                     score_at_control=round(denom, 4))
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows([rows[k] for k in sorted(rows)])



def f1():
    """The mechanism, on a synthetic section: the sum vanishes with distance, the mean does not."""
    th = np.linspace(0, 2 * np.pi, 4000, endpoint=False)
    r = 400 + 30 * th / (2 * np.pi) * 20
    mid = np.stack([r * np.cos(th), r * np.sin(th)], 1)
    t = np.gradient(mid, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    D = np.logspace(1, 6, 140)
    cand = np.stack([D, np.zeros_like(D)], 1)
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    ax.loglog(D, ve.refine_score(cand, mid, nrm, False), color=FIXED, lw=2,
              label="weighted sum (line 116 removed)")
    ax.loglog(D, ve.refine_score(cand, mid, nrm, True), color=AS_IS, lw=2,
              label="weighted mean (as published)")
    ax.set_xlabel("distance of the candidate from the centre of the section, pixels")
    ax.set_ylabel("refinement score")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=.25, which="both")
    save(fig, "f1-mechanism")


def f2(scroll="PHerc0826", z=8000,
       path=os.path.join(HERE, "cache", "pherc0826", "ngrid", "xy", "008000.grid")):
    """The slice FIGURE.md names, scored both ways, on one scale, with the control point marked."""
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.6))
    im, vmax, _ = field_panels(axes, scroll, path, z, 20260915 + z)
    fig.suptitle(f"{scroll.replace('PHerc', 'PHerc. ')} xy slice {z}, refinement score divided by "
                 f"the score at the published control point", fontsize=10)
    cb = fig.colorbar(im, ax=axes, fraction=.035, pad=.02)
    cb.set_label(f"score / score at the cross, 0.00 to {vmax:.2f}, same scale in both panels",
                 fontsize=8)
    cb.ax.tick_params(labelsize=7)
    save(fig, "f2-score-field")


def f3():
    """The fifteen scrolls, two blocks, never pooled."""
    r = rows()
    blocks = [("primary", "references published by the challenge"),
              ("confirmation", "manual references of a third party, MIT")]
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 8.2),
                             gridspec_kw={"height_ratios": [len([q for q in r if q["block"] == b]) + 1
                                                            for b, _ in blocks]})
    lo = min(float(q["no_division_mm"]) for q in r) * .6
    hi = max(float(q["published_mm"]) for q in r) * 1.6
    for ax, (block, title) in zip(axes, blocks):
        b = [q for q in r if q["block"] == block]
        y = np.arange(len(b))
        ax.plot([float(q["fake_axis_mm"]) for q in b], y, "x", color=BASE, ms=6,
                label="constant axis (control)")
        ax.plot([float(q["centroid_mm"]) for q in b], y, "s", mfc="none", color="k", ms=6,
                label="centroid of the filled mask")
        ax.plot([float(q["published_mm"]) for q in b], y, "o", color=AS_IS, ms=6,
                label="estimator as published")
        ax.plot([float(q["no_division_mm"]) for q in b], y, "o", color=FIXED, ms=7,
                label="estimator with line 116 removed")
        for i, q in enumerate(b):
            ax.plot([float(q["published_mm"]), float(q["no_division_mm"])], [i, i],
                    "-", color=FIXED, lw=.8, alpha=.5, zorder=0)
        ax.set_yticks(y, [q["scroll"] for q in b], fontsize=8)
        ax.set_xscale("log"), ax.set_xlim(lo, hi)
        ax.invert_yaxis(), ax.grid(axis="x", alpha=.25, which="both")
        ax.set_title(title, fontsize=9, loc="left")
    axes[0].legend(frameon=False, fontsize=7.5, loc="lower right")
    axes[-1].set_xlabel("median distance from the reference umbilicus, millimetres")
    save(fig, "f3-fifteen")


def f4():
    """Inside the volume, on every scroll, with no reference needed."""
    with open(os.path.join(EV, "twentythree.csv")) as fh:
        r = list(csv.DictReader(fh))
    y = np.arange(len(r))
    fig, ax = plt.subplots(figsize=(6.6, 7.4))
    ax.barh(y - .2, [int(q["inside_as_is"]) for q in r], .4, color=AS_IS, label="as published")
    ax.barh(y + .2, [int(q["inside_fixed"]) for q in r], .4, color=FIXED, label="line 116 removed")
    ax.set_yticks(y, [q["scroll"] for q in r], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("estimates inside the grid, of 24 slices")
    ax.set_xlim(0, 24.6), ax.grid(axis="x", alpha=.25)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    save(fig, "f4-inside-volume")


def f5():
    """The two umbilici of one scroll: a hand annotation and a mask centroid.

    Corrected on 2026-09-19, here and not in the working tree's frozen copy of this file: the
    two were called independent annotations, and the second is derived from sheet instance
    labels as the papyrus centroid of each slice. Nothing the function computes changes.
    """
    def load(n):
        d = json.load(open(os.path.join(HERE, "external-references", n)))
        p = d["control_points"] if isinstance(d, dict) else d
        a = np.array([[q["x"], q["y"], q["z"]] for q in p], float)
        return a[np.argsort(a[:, 2])]
    A, B = load("drobkov-PHerc1218-umbilicus.json"), load("dopico-PHerc1218-umbilicus.json")
    MM = 8.640 / 1000
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 6.0), sharex=True)
    for ax, i, lab in ((axes[0], 0, "x"), (axes[0], 1, "y")):   # both coordinates, same colours
        ax.plot(A[:, 2], A[:, i], "-o", ms=3, lw=1, color=AS_IS,
                label="clicked on level 3 images (36 points)" if i == 0 else None)
        ax.plot(B[:, 2], B[:, i], "-", lw=1, color=FIXED,
                label="derived from sheet instance labels (365 points)" if i == 0 else None)
    axes[0].set_ylabel("x and y, level 0 voxels")
    axes[0].legend(frameon=False, fontsize=7.5)
    d = np.array([np.hypot(*(p[:2] - np.array([np.interp(p[2], B[:, 2], B[:, 0]),
                                               np.interp(p[2], B[:, 2], B[:, 1])]))) * MM for p in A])
    axes[1].plot(A[:, 2], d, "-o", ms=3, lw=1, color="k")
    axes[1].set_ylabel("distance between the two, mm")
    axes[1].set_xlabel("z, level 0 voxels")
    for ax in axes:
        ax.axvspan(7500, 9500, color=BASE, alpha=.18, lw=0)
        ax.grid(alpha=.25)
    save(fig, "f5-two-annotations")


def positions():
    """evidence/positions-24.csv, grouped by scroll and variant, in the units of each grid."""
    with open(os.path.join(EV, "positions-24.csv")) as fh:
        r = list(csv.DictReader(fh))
    out = {}
    for q in r:
        d = out.setdefault(q["scroll"], {"width": float(q["width"]), "height": float(q["height"])})
        d.setdefault(q["variant"], []).append((int(q["z"]), float(q["x"]), float(q["y"])))
    for d in out.values():
        for v in ("as-is", "no-division"):
            d[v] = np.array(sorted(d.get(v, [])), float).reshape(-1, 3)
    return out


def f6():
    """Twenty-four scrolls at once, with no reference needed anywhere in the picture."""
    pos = positions()
    names = sorted(pos)
    cols, lo, hi = 6, -0.6, 1.6
    rows_n = (len(names) + cols - 1) // cols
    fig, axes = plt.subplots(rows_n, cols, figsize=(11.0, 1.95 * rows_n))
    for ax, scroll in zip(axes.ravel(), names):
        d = pos[scroll]
        W, H = d["width"], d["height"]
        ax.add_patch(plt.Rectangle((0, 0), 1, H / W, fill=False, ec="k", lw=.9))
        for variant, colour in (("as-is", AS_IS), ("no-division", FIXED)):
            p = d[variant]
            x, y = p[:, 1] / W, p[:, 2] / W
            inside = (x >= lo) & (x <= hi) & (y >= lo) & (y <= hi)
            ax.plot(x[inside], y[inside], "o", color=colour, ms=2.6, mew=0, alpha=.9)
            for xe, ye in zip(x[~inside], y[~inside]):
                cx, cy = np.clip(xe, lo + .04, hi - .04), np.clip(ye, lo + .04, hi - .04)
                ax.plot(cx, cy, "^", color=colour, ms=3.4, mew=0, alpha=.9)
        n_as = int(((d["as-is"][:, 1] >= 0) & (d["as-is"][:, 1] <= W) &
                    (d["as-is"][:, 2] >= 0) & (d["as-is"][:, 2] <= H)).sum())
        n_fx = len(d["no-division"])
        ax.set_title(f"{scroll.replace('PHerc', 'PHerc. ')}\n{n_as} and {n_fx} of {n_fx} inside",
                     fontsize=7.2, linespacing=1.35)
        ax.set_xlim(lo, hi), ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box"), ax.set_xticks([]), ax.set_yticks([])
        # A faint frame around each panel, so that an estimate drawn far outside one grid is not
        # read as belonging to the panel next to it.
        for s in ax.spines.values():
            s.set_color("#cfcfcf")
            s.set_linewidth(.6)
    for ax in axes.ravel()[len(names):]:
        ax.set_visible(False)
    axes.ravel()[0].plot([], [], "o", color=AS_IS, ms=4, label="as published")
    axes.ravel()[0].plot([], [], "o", color=FIXED, ms=4, label="line 116 removed")
    fig.legend(*axes.ravel()[0].get_legend_handles_labels(), frameon=False, fontsize=8.5,
               loc="lower center", ncol=2, bbox_to_anchor=(.5, -.012))
    fig.subplots_adjust(hspace=.42, wspace=.12)
    save(fig, "f6-small-multiples")


def f7(scroll="PHerc0125", z=6891):
    """The walk itself, from the seed the RANSAC selection picked to where it stops."""
    path = os.path.join(HERE, "gridcache", scroll, f"{z:06d}.grid")
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.6))
    im, vmax, _ = field_panels(axes, scroll, path, z, 20260915 + z, climb=True)
    fig.suptitle(f"{scroll.replace('PHerc', 'PHerc. ')} xy slice {z}, the hill climb of lines 119 "
                 f"to 142 over the same field", fontsize=10)
    cb = fig.colorbar(im, ax=axes, fraction=.035, pad=.02)
    cb.set_label(f"score / score at the cross, 0.00 to {vmax:.2f}, same scale in both panels",
                 fontsize=8)
    cb.ax.tick_params(labelsize=7)
    save(fig, "f7-hill-climb")


def f8():
    """Twenty runs of one binary on one slice, on one logarithmic axis for every row."""
    import re
    noise = {(q["scroll"], int(q["slice_z"]), q["variant"]): q
             for q in csv.DictReader(open(os.path.join(EV, "search-noise.csv")))}
    ref = {q["scroll"]: float(q["no_division_mm"]) for q in rows()}
    d = os.path.join(HERE, "real", "evidence")
    strips = []
    for name in sorted(os.listdir(d)):
        m = re.match(r"(as-is|no-division)-d-(\d+)-(\d+)\.txt$", name)
        if not m:
            continue
        variant, scroll, z = m.group(1), "PHerc" + m.group(2), int(m.group(3))
        key = (scroll, z, variant)
        if key not in noise:
            continue
        mm = float(noise[key]["mm_per_grid_unit"])
        pts = []
        for line in open(os.path.join(d, name)):
            q = re.match(r"run \d+: umbilicus \(([-\d.]+), ([-\d.]+)\)", line.strip())
            if q:
                pts.append((float(q.group(1)), float(q.group(2))))
        p = np.array(pts, float)
        med = np.median(p, axis=0)
        strips.append((scroll, z, variant, np.hypot(*(p - med).T) * mm))
    strips.sort(key=lambda s: (s[0], s[1], s[2]))

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    labels = []
    for i, (scroll, z, variant, dist) in enumerate(strips):
        colour = AS_IS if variant == "as-is" else FIXED
        y = len(strips) - 1 - i
        dist = np.maximum(dist, 1e-3)
        ax.plot(dist, np.full(len(dist), y) + np.linspace(-.13, .13, len(dist)), "o",
                color=colour, ms=3.4, mew=0, alpha=.85)
        ax.plot(np.median(dist), y, "|", color="k", ms=13, mew=1.4)
        if variant == "no-division" and scroll in ref:
            ax.plot([ref[scroll], ref[scroll]], [y - .38, y + .38], "-", color=BASE, lw=1.6)
        labels.append((y, f"{scroll.replace('PHerc', 'PHerc. ')} z {z}, "
                          f"{'as published' if variant == 'as-is' else 'line 116 removed'}"))
    ax.set_yticks([q[0] for q in labels], [q[1] for q in labels], fontsize=7.5)
    ax.set_xscale("log")
    ax.set_xlabel("distance of one run from the median of its own twenty, millimetres")
    ax.grid(axis="x", alpha=.25, which="both")
    ax.plot([], [], "|", color="k", ms=10, mew=1.4, label="median of the twenty")
    ax.plot([], [], "-", color=BASE, lw=1.6, label="median distance from the reference")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    save(fig, "f8-run-spread")


def f9(scroll="PHerc0826"):
    """The umbilicus is a curve along the scroll, and one of the two curves leaves the grid."""
    pos = positions()[scroll]
    W, H = pos["width"], pos["height"]
    # Two units meet here and must not be confused: the reference is in level 0 voxels, the
    # estimates are in units of the normal grid, and a grid unit is grid_scale level 0 voxels.
    mm_voxel = CFG[scroll]["voxel_um"] / 1000.0
    mm_grid = mm_per_unit(scroll)
    a = reference(scroll)
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.6), sharex=True)
    for ax, i, lab in ((axes[0], 0, "x"), (axes[1], 1, "y")):
        ax.axhspan(0, (W if i == 0 else H) * mm_grid, color=BASE, alpha=.13, lw=0)
        ax.plot(a[:, 2] * mm_voxel, a[:, i] * mm_voxel, "-", color="k", lw=1.4,
                label="published umbilicus" if i == 0 else None)
        for variant, colour, lab2 in (("as-is", AS_IS, "as published"),
                                      ("no-division", FIXED, "line 116 removed")):
            p = pos[variant]
            ax.plot(p[:, 0] * mm_grid, p[:, i + 1] * mm_grid, "-o", ms=3, lw=1.1, color=colour,
                    label=lab2 if i == 0 else None)
        ax.set_ylabel(f"{lab}, millimetres")
        ax.set_ylim(-0.12 * W * mm_grid, 1.12 * W * mm_grid)
        ax.grid(alpha=.25)
    axes[0].legend(frameon=False, fontsize=7.5, ncol=3, loc="upper center")
    axes[1].set_xlabel("z, millimetres")
    fig.suptitle(f"{scroll.replace('PHerc', 'PHerc. ')}, the umbilicus along the scroll. "
                 f"Shaded: the extent of the normal grid", fontsize=9.5)
    save(fig, "f9-axis-along-z")


if __name__ == "__main__":
    want = sys.argv[1:] or ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9"]
    for name in want:
        globals()[name]()
