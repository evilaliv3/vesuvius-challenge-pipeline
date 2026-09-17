# This file is a copy of tools/figure_exponent.py of the working tree and differs from it in one
# way only: the absolute path of the one cached slice it reads is resolved inside this folder,
# from the file's own location. The figures go where rev1_lib puts them, which is build/figures
# here, a directory a run writes and the repository does not keep. Nothing else is changed.
"""The two figures of the exponent ablation, drawn from CSVs written by this tool and by nothing
else.

    figure_exponent.py                 # the numbers, then both figures
    figure_exponent.py --numbers       # only the CSVs
    figure_exponent.py fA fB           # only those figures

  fA  exponent-mechanism      the refinement score against the distance of the candidate from the
                              centre of the section, on the synthetic section the paper's Fig. 1
                              draws, one line per exponent of the weighted sum plus the weighted
                              mean as the published control, on one pair of axes
  fB  exponent-score-field    the score field of the same real slice the paper's Fig. 2 draws
                              (PHerc0826 xy 8000), one panel per exponent plus the published
                              control, all panels on one colour scale

Neither figure needs the stand in build: the field of Fig. 2 is computed by the transcription
tools/rev1_lib.py, which is what figure_umbilicus.f2 does too, and which reproduces the C++ to the
bit at p = 1, which is section 4 of the rule the ablation was declared under.

Colours are the paper's own: FIXED blue for the weighted sum, AS_IS orange for the weighted mean
as published, viridis for the field. The exponent is an ordered quantity and not a set of
categories, so the four sums take one hue from light to dark, with a line style each as a second
encoding, and p = 1 keeps the paper's exact blue and its full weight.

Outputs: evidence/exponent-ablation-mechanism-curve.csv,
evidence/exponent-ablation-score-field.csv, and PDF plus PNG in build/figures.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L              # noqa: E402

FIG = L.FIGURES
import palette as P  # noqa: E402
plt.rcParams.update(P.RC)   # rule 4: a word is black or white and never a hue, and black is
                            # what every label, tick and legend entry on the page takes
AS_IS, FIXED, BASE = P.PUBLISHED, P.REPAIRED, P.STRUCTURE
PS = [0.5, 1.0, 1.5, 2.0]
# one hue, light to dark, with p = 1 on the paper's own FIXED blue
# One ordered quantity within one kind of thing: four steps of the same hue, from
# palette.RAMP_REPAIRED, rather than four colours.
RAMP = dict(zip((0.5, 1.0, 1.5, 2.0), P.RAMP_REPAIRED))
# the same light to dark ordering in the paper's other colour, for the mean at each exponent
RAMP_MEAN = dict(zip((0.5, 1.0, 1.5, 2.0), P.RAMP_PUBLISHED))
DASH = {0.5: (0, (5, 2)), 1.0: "solid", 1.5: (0, (4, 1.6, 1, 1.6)), 2.0: (0, (1.4, 1.6))}
SLICE_SCROLL, SLICE_Z = "PHerc0826", 8000
SLICE_FILE = os.path.join(L.NG, "cache", "pherc0826", "ngrid", "xy", "008000.grid")
MECH = os.path.join(L.EV, "exponent-ablation-mechanism-curve.csv")
FIELD = os.path.join(L.EV, "exponent-ablation-score-field.csv")


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"written {FIG}/{name}.pdf and .png")


def f1_section():
    """The section figure_umbilicus.f1 draws: one turn of a spiral, 4000 points, centred at 0."""
    th = np.linspace(0, 2 * np.pi, 4000, endpoint=False)
    r = 400 + 30 * th / (2 * np.pi) * 20
    mid = np.stack([r * np.cos(th), r * np.sin(th)], 1)
    t = np.gradient(mid, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    return mid, np.stack([-t[:, 1], t[:, 0]], 1)


def control_point(scroll, z):
    a = L.reference(scroll)
    sc = L.CFG[scroll]["grid_scale"]
    z0 = z * sc
    return np.array([np.interp(z0, a[:, 2], a[:, 0]) / sc,
                     np.interp(z0, a[:, 2], a[:, 1]) / sc])


def mm_per_unit(scroll):
    return L.CFG[scroll]["voxel_um"] / 1000.0 * L.CFG[scroll]["grid_scale"]


def scale_bar(ax, mm_px, length_mm=10.0):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    n = length_mm / mm_px
    x, y = x0 + 0.06 * (x1 - x0), y0 + 0.07 * (y1 - y0)
    ax.plot([x, x + n], [y, y], "-", color=P.OVER_FIELD, path_effects=P.stroke(3.0), lw=2.6, solid_capstyle="butt")
    # rule 4: white on colour and black on white, whichever reads better, and the word is one
    # colour. This one lies on a field that runs to Blue_100, where bare black is 1.26 to 1, so it
    # is white, and bare: the bar under it is a mark and keeps its casing, the word does not take
    # one.
    ax.text(x + n / 2, y + 0.022 * (y1 - y0), f"{length_mm:.0f} mm", color=P.OVER_FIELD,
            fontsize=7, ha="center", va="bottom")


# ------------------------------------------------------------------ the numbers

def numbers():
    """The mechanism curve per exponent, and the per panel numbers of the field figure."""
    mid, nrm = f1_section()
    D = np.logspace(1, 6, 140)
    cand = np.stack([D, np.zeros_like(D)], 1)
    rows = []
    for p in PS:
        sm = L.refine_score(cand, mid, nrm, False, p=p)
        mn = L.refine_score(cand, mid, nrm, True, p=p)
        for d, a, b in zip(D, sm, mn):
            rows.append(dict(section="f1 spiral", p=f"{p:.1f}", distance_units=round(float(d), 3),
                             weighted_sum=float(a), weighted_mean=float(b)))
    L.write_csv(MECH, ["section", "p", "distance_units", "weighted_sum", "weighted_mean"], rows)
    # known reference: the p = 1 curve must reproduce the frozen mechanism-curve.csv
    old = [q for q in L.read_csv(os.path.join(L.EV, "mechanism-curve.csv"))
           if q["section"] == "f1 spiral"]
    new = [q for q in rows if q["p"] == "1.0"]
    bad = [(a["distance_units"], a["weighted_sum"], b["weighted_sum"])
           for a, b in zip(old, new)
           if a["weighted_sum"] != repr(b["weighted_sum"])
           or a["weighted_mean"] != repr(b["weighted_mean"])]
    print(f"  known reference (p = 1 against mechanism-curve.csv, {len(old)} points): "
          f"{'reproduced' if not bad else f'NOT reproduced, {len(bad)} points differ'}")

    # the field figure's per panel numbers, from the same fields the panels draw
    frows = []
    for name, ratio, extent, cp, stop, denom, mm_px in field_data():
        g = np.argmax(ratio)
        n = ratio.shape[0]
        x = extent[0] + (g % n) * (extent[1] - extent[0]) / (n - 1)
        y = extent[2] + (g // n) * (extent[3] - extent[2]) / (n - 1)
        frows.append(dict(panel=name, scroll=SLICE_SCROLL, z=SLICE_Z, grid=n,
                          score_at_control_point=round(denom, 6),
                          fieldmax_x=round(float(x), 1), fieldmax_y=round(float(y), 1),
                          fieldmax_dist_from_control_mm=round(
                              float(np.hypot(x - cp[0], y - cp[1])) * mm_px, 3),
                          fieldmax_over_control=round(float(ratio.max()), 4),
                          estimate_x=round(float(stop[0]), 1), estimate_y=round(float(stop[1]), 1),
                          estimate_dist_from_control_mm=round(
                              float(np.hypot(*(stop - cp))) * mm_px, 3)))
        print(f"  {name:28s} field max {frows[-1]['fieldmax_dist_from_control_mm']:8.2f} mm from "
              f"the cross, estimate {frows[-1]['estimate_dist_from_control_mm']:10.2f} mm",
              flush=True)
    L.write_csv(FIELD, list(frows[0]), frows)


_FIELD_CACHE = []


def field_data(pad=0.10, n=200):
    """The five fields of Fig. B, all on the same draw of the same slice.

    Each field is divided by the score at the published control point, which is the same physical
    place in every panel: a weighted sum at p = 0.5 and one at p = 2 do not share units, so an
    absolute scale shared between panels would flatten four of them and compare nothing. This is
    the convention of the paper's own Fig. 2 and it is stated in the caption.
    """
    if _FIELD_CACHE:
        return _FIELD_CACHE
    h, paths, _ = L.read_grid(SLICE_FILE)
    mid, nrm = L.segments(paths)
    W, H = float(h["bounds"][2]), float(h["bounds"][3])
    lo, hi = -pad * W, (1 + pad) * W
    seed = L.TABLE_SEED + SLICE_Z
    ms, ns, _ = L.sample(mid, nrm, seed)
    g = np.linspace(lo, hi, n)
    GX, GY = np.meshgrid(g, g)
    lat = np.stack([GX.ravel(), GY.ravel()], 1)
    cp = control_point(SLICE_SCROLL, SLICE_Z)
    mm_px = mm_per_unit(SLICE_SCROLL)
    panels = [(f"weighted sum, p = {p:.1f}", False, p) for p in PS]
    panels.append(("weighted mean, p = 1.0 (as published)", True, 1.0))
    for name, divide, p in panels:
        f = L.refine_score(lat, ms, ns, divide, p=p).reshape(GX.shape)
        denom = float(L.refine_score(cp, ms, ns, divide, p=p)[0])
        stop, _ = L.estimate(mid, nrm, W, H, seed, divide, p=p)
        _FIELD_CACHE.append((name, f / denom, (lo, hi, lo, hi), cp, stop, denom, mm_px))
        print(f"  field computed: {name}", flush=True)
    _FIELD_CACHE.append(("segments", mid, (lo, hi, lo, hi), cp, np.array([W, H]), 0.0, mm_px))
    return _FIELD_CACHE[:-1]


# ------------------------------------------------------------------ the figures

def fA():
    """The mechanism curve, one line per exponent, for the sum and for the mean.

    Both families are drawn because the figure answers two questions at once: whether a larger
    exponent changes where the sum turns over, and whether any exponent gives the MEAN a far field
    that falls. It does not: the four mean curves flatten onto the same plateau, which is
    lambda_max of the normals' covariance and does not depend on the exponent.
    """
    r = L.read_csv(MECH)
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    for p in PS:
        q = [x for x in r if x["p"] == f"{p:.1f}"]
        D = np.array([float(x["distance_units"]) for x in q])
        y = np.array([float(x["weighted_sum"]) for x in q])
        ax.loglog(D, y, color=RAMP[p], lw=2.4 if p == 1.0 else 1.8, ls=DASH[p],
                  label=f"weighted sum, p = {p:.1f}" + (" (the patch)" if p == 1.0 else ""))
        ax.plot(D[int(np.argmax(y))], y.max(), "o", color=RAMP[p], ms=5.5,
                mec=P.OVER_FIELD, path_effects=P.stroke(3.0), mew=1.0, zorder=5)
    for p in PS:
        q = [x for x in r if x["p"] == f"{p:.1f}"]
        D = np.array([float(x["distance_units"]) for x in q])
        ax.loglog(D, [float(x["weighted_mean"]) for x in q], color=RAMP_MEAN[p],
                  lw=2.4 if p == 1.0 else 1.8, ls=DASH[p],
                  label=f"weighted mean, p = {p:.1f}" + (" (as published)" if p == 1.0 else ""))
    ax.set_xlabel("distance of the candidate from the centre of the section, pixels", fontsize=9)
    ax.set_ylabel("refinement score", fontsize=9)
    ax.set_title("Every exponent of the sum falls away; no exponent makes the mean fall",
                 fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=7.4, loc="lower left", ncol=2, columnspacing=1.1)
    ax.grid(alpha=.22, which="both")
    ax.tick_params(labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    # the two notes go under the axes, where no curve can run through them
    fig.text(.5, -.02, "Filled circle: the largest value of each sum on the range drawn. The four "
             "means lie on one plateau, which is lambda_max of the\nnormals' covariance and does "
             "not depend on p; the four sums leave that plateau at a rate p, each on its own "
             "units.", ha="center", va="top", fontsize=7.4, color=P.TEXT)
    save(fig, "exponent-mechanism")


def fB():
    """The score field of the real slice, one panel per exponent, on one colour scale.

    Each panel is divided by its OWN largest value, so every panel runs from 0 to 1 and the five
    share that scale. Dividing them all by the score at the control point instead, which is what
    the paper's Fig. 2 can do with two panels of one objective, does not work here: a sum at
    p = 0.5 and a sum at p = 2 carry different units, the score at the cross falls from 172 to
    0.009 across the row, and the panel with the smallest denominator would take the whole colour
    range and turn the other four black. What a shared 0 to 1 scale compares is the SHAPE of the
    landscape, which is what the exponent is supposed to change: a larger p should concentrate the
    bright region. The number that says how far the cross is from the best place in its own panel
    is printed in each panel and written to exponent-ablation-score-field.csv.
    """
    data = field_data()
    segs = _FIELD_CACHE[-1][1]
    fig, axes = plt.subplots(1, 5, figsize=(15.2, 3.8))
    im = None
    for ax, (name, ratio, ext, cp, stop, denom, mm_px) in zip(axes, data):
        n = ratio.shape[0]
        g = int(np.argmax(ratio))
        fx = ext[0] + (g % n) * (ext[1] - ext[0]) / (n - 1)
        fy = ext[2] + (g // n) * (ext[3] - ext[2]) / (n - 1)
        im = ax.imshow(ratio / ratio.max(), origin="lower", extent=ext, cmap=P.FIELD_CMAP,
                       vmin=0.0, vmax=1.0)
        ax.plot(segs[::80, 0], segs[::80, 1], ".", color=P.OVER_FIELD, path_effects=P.stroke(3.0), ms=.35, alpha=.45)
        ax.plot(*cp, "x", color=P.OVER_FIELD, path_effects=P.stroke(3.0), ms=11, mew=2.0)
        ax.plot(fx, fy, "D", mfc="none", mec=P.OVER_FIELD, path_effects=P.stroke(3.0), ms=8, mew=1.5)
        d_mm = float(np.hypot(*(stop - cp))) * mm_px
        if ext[0] <= stop[0] <= ext[1] and ext[2] <= stop[1] <= ext[3]:
            ax.plot(*stop, "o", mfc="none", mec=P.OVER_FIELD, path_effects=P.stroke(3.0), ms=12, mew=1.8)
        ax.set_title(f"{name}\nsearch stops {d_mm:,.2f} mm from the cross", fontsize=8)
        ax.text(.03, .965, f"score at the cross {denom:.3f}\n"
                           f"the cross is at {1.0 / float(ratio.max()):.3f} of this panel's best\n"
                           f"best is {float(np.hypot(fx - cp[0], fy - cp[1])) * mm_px:,.2f} mm "
                           "from the cross",
                transform=ax.transAxes, color=P.OVER_FIELD,
                fontsize=6.6, va="top", linespacing=1.35)
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_xlim(ext[0], ext[1]), ax.set_ylim(ext[2], ext[3])
        scale_bar(ax, mm_px)
    fig.suptitle(f"{SLICE_SCROLL.replace('PHerc', 'PHerc. ')} xy slice {SLICE_Z}: the refinement "
                 "score over the slice, each panel divided by its own largest value", fontsize=10)
    cb = fig.colorbar(im, ax=axes, fraction=.012, pad=.012)
    cb.set_label("score / the best score in that panel, 0 to 1, same scale in all five",
                 fontsize=8)
    cb.ax.tick_params(labelsize=7)
    fig.text(.5, -.02, "Cross: the published control point. Diamond: the best score in the panel. "
             "Circle: where villa's own search stops.\nThe panels do not share units, so they "
             "share a shape and not a level; the levels are in the three lines inside each panel.",
             ha="center", va="top", fontsize=7.6, color=P.TEXT)
    save(fig, "exponent-score-field")


def main():
    want = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not want or "--numbers" in sys.argv:
        numbers()
    for name in (want or ["fA", "fB"]):
        globals()[name]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
