# This file is a copy of tools/figure_umbilicus_gallery.py of the working tree and differs from it in one way
# only: the absolute paths of the machine the measurements ran on are replaced by paths
# inside this folder, resolved from the file's own location, the positions of the compiled
# function are read from evidence/ beside everything else, and the message it prints when the
# grid slices are not on disk names them the way this folder names them. Nothing else is changed.
#!/usr/bin/env python3
"""A gallery of the generalisation run: one section per scroll, 24 panels, three markers.

Every panel is one xy slice of one scroll's normal grid, drawn as the segments the estimator
consumes, with the axis estimate of the published estimator (weighted mean), the estimate with
the division removed (weighted sum), and, where a manual or published reference exists, the
reference. The reference is drawn only to be looked at: nothing here is chosen with it.

Nothing is estimated here. The estimates are read from the positions of the shipped function,
evidence/cpp-positions-24.csv, the file the paper draws from since
2026-09-18, or from evidence/positions-24-refit.csv, the transcription's, only when the
first is absent; the caption names whichever was used. The grids are the cached slices of that run under
inputs/grid23/, read and never written; the references and the voxel sizes come
from fifteen-config.json through tools/rev1_lib.py. The counts in the caption are the per scroll
summary of the same run, evidence/cpp-twentyfour.csv, summed the way the article's macros sum
it, and the tool stops if the positions file and the summary disagree.

Slice rule, fixed before drawing: of the 24 sampled slices of a scroll in order of z, the panel
shows the twelfth, the lower of the two that straddle the middle of the sampled band. No slice is
chosen by looking at it.

    figure_umbilicus_gallery.py            # writes the PDF, the PNG and the caption

Output: build/figures/umbilicus-gallery-24.{pdf,png,caption.txt}
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.collections import LineCollection     # noqa: E402
import numpy as np                                    # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L                                  # noqa: E402
from gridstore import read_grid                       # noqa: E402

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID23 = os.path.join(L.NG, "grid23")
# The figure must be drawn from whatever the text beside it claims. Since 2026-09-18 the
# twenty four scroll run is the shipped function called through vc_gen_umbilicus, so the gallery
# reads its positions; the transcription's file stays as the fallback and as the record.
_CPP24 = os.path.join(L.EV, "cpp-positions-24.csv")
POSITIONS = _CPP24 if os.path.exists(_CPP24) else os.path.join(L.EV, "positions-24-refit.csv")
# The per scroll summary of the same twenty four scroll run. Its inside counts are what the
# article prints, so they are what the drawn panels are checked against: two files under one
# name is the defect this catches.
_CPP24_SUMMARY = os.path.join(L.EV, "cpp-twentyfour.csv")
SUMMARY = _CPP24_SUMMARY if os.path.exists(_CPP24_SUMMARY) else os.path.join(
    L.EV, "twentythree-refit.csv")
OUT_DIR = L.FIGURES
STEM = "umbilicus-gallery-24"
import palette as P  # noqa: E402
# The meanings of tools/palette.py: the estimator as it is published, which is a neutral because
# the published code is the subject of the measurement and not a verdict on it; ours; the structure
# grey of the normal grid under both; and the reference, which since 2026-09-18 carries the
# reference yellow rather than black. The reference cross lies over the grey segments, so it is
# drawn on the dark casing of palette.stroke: yellow to a reader in colour, a dark cross in a
# printed grey copy, which is the same remedy rule 3 of the palette gives any coloured mark.
plt.rcParams.update(P.RC)   # rule 4: a word is black or white and never a hue, and black is
                            # what every label, tick and legend entry on the page takes
AS_IS, FIXED, BASE = P.UPSTREAM, P.OURS, P.STRUCTURE
REF = P.REFERENCE
REF_MARK = dict(ms=8, mew=1.6, path_effects=P.stroke(3.4))
PAD = 0.08            # the window is the grid plus this fraction of its width on every side
COLS = 6
SLICE_INDEX = L.N_HEIGHTS // 2 - 1     # the twelfth of 24, in order of z


def summary(column):
    """The sum of one integer column of the run's per scroll summary.

    This is the arithmetic the article's macros do on the same file, kept here rather than read
    back out of a macro file, so that the figure and the sentence beside it are two readings of
    one evidence file and not two readings of each other.
    """
    with open(SUMMARY) as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"{SUMMARY}: no rows")
    if column not in rows[0]:
        raise SystemExit(f"{SUMMARY}: no column {column}")
    return sum(int(r[column]) for r in rows)


def positions():
    """positions-24-refit.csv as {scroll: {variant: {z: (x, y)}, width, height}}."""
    out = {}
    with open(POSITIONS) as fh:
        for q in csv.DictReader(fh):
            # The C++ file also carries the two extra seeds used only for the spread, and any
            # estimate that met the guard. Neither is a position of this run: counting them would
            # treble the in bounds count and draw a slice three times.
            if q.get("role", "position") != "position" or int(q.get("guard", 0)):
                continue
            d = out.setdefault(q["scroll"], {"width": float(q["width"]),
                                             "height": float(q["height"]),
                                             "as-is": {}, "no-division": {}, "inside": {}})
            d[q["variant"]][int(q["z"])] = (float(q["x"]), float(q["y"]))
            if int(q["capped"]):
                d.setdefault("capped", set()).add((q["variant"], int(q["z"])))
            d["inside"].setdefault(q["variant"], 0)
            d["inside"][q["variant"]] += int(q["inside"])
    return out


def chosen_slice(zs):
    """The slice rule: the twelfth of the sampled slices in order of z."""
    zs = sorted(zs)
    if len(zs) != L.N_HEIGHTS:
        raise SystemExit(f"expected {L.N_HEIGHTS} sampled slices, found {len(zs)}")
    return zs[SLICE_INDEX]


def reference_at(scroll, z):
    """The reference umbilicus at grid slice z, in grid units, or None with a reason.

    The reference is in level 0 voxels and the grid in its own units, grid_scale voxels each.
    The control points are interpolated along z and never extrapolated: outside the annotated
    band there is no reference.
    """
    if scroll not in L.CFG:
        return None, "no reference"
    a = L.reference(scroll)
    sc = L.CFG[scroll]["grid_scale"]
    z0 = z * sc
    if not (a[:, 2].min() <= z0 <= a[:, 2].max()):
        return None, f"reference ends at z {a[:, 2].min():.0f}..{a[:, 2].max():.0f}, slice at {z0}"
    return np.array([np.interp(z0, a[:, 2], a[:, 0]) / sc,
                     np.interp(z0, a[:, 2], a[:, 1]) / sc]), L.CFG[scroll]["source"]


def mm_per_unit(scroll):
    """Millimetres per grid unit where the voxel size is on record, else None."""
    c = L.CFG.get(scroll)
    if not c:
        return None
    return c["voxel_um"] / 1000.0 * c["grid_scale"]


def border_hit(a, b, lo_x, hi_x, lo_y, hi_y, inset=0.03):
    """Where the ray from `a` towards `b` crosses the border of the window (figure_umbilicus.py)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    ts = []
    for i, (lo, hi) in enumerate(((lo_x, hi_x), (lo_y, hi_y))):
        span = hi - lo
        if d[i] > 0:
            ts.append((hi - inset * span - a[i]) / d[i])
        elif d[i] < 0:
            ts.append((lo + inset * span - a[i]) / d[i])
    t = min([q for q in ts if q > 0] or [1.0])
    return a + t * d


def draw_grid(ax, paths):
    """The segments of the slice, as thin grey polylines."""
    segs = [np.asarray(p, float) for p in paths if len(p) >= 2]
    ax.add_collection(LineCollection(segs, colors=BASE, linewidths=0.25, alpha=0.55,
                                     rasterized=True))


def panel(ax, scroll, d, notes):
    W, H = d["width"], d["height"]
    z = chosen_slice(d["no-division"])
    lo_x, hi_x = -PAD * W, (1 + PAD) * W
    lo_y, hi_y = -PAD * W, H + PAD * W
    path = os.path.join(GRID23, scroll, f"{z:06d}.grid")
    if not os.path.exists(path) or not os.path.getsize(path):
        ax.text(.5, .5, "grid not on disk", transform=ax.transAxes, ha="center", va="center",
                fontsize=8, color=P.TEXT)
        notes.append((scroll, z, "grid not on disk"))
    else:
        h, paths, _ = read_grid(path)
        if (float(h["bounds"][2]), float(h["bounds"][3])) != (W, H):
            raise SystemExit(f"{scroll} z {z}: grid bounds {h['bounds']} differ from the "
                             f"evidence ({W}, {H})")
        draw_grid(ax, paths)
    ax.add_patch(plt.Rectangle((0, 0), W, H, fill=False, ec=P.STRUCTURE_DARK, lw=.7))

    fixed = np.array(d["no-division"][z])
    asis = np.array(d["as-is"][z])
    ref, why = reference_at(scroll, z)
    mm = mm_per_unit(scroll)

    # the reference first, under the estimates, so a coincident estimate stays visible
    if ref is not None:
        ax.plot(*ref, "x", color=REF, zorder=4, **REF_MARK)
    # The published estimate goes under the repaired one: where the two coincide within a marker
    # (three scrolls of the twenty four) the repaired one is the one on top, and the published one
    # is drawn a size larger so that its rim still shows around it.
    inside_win = lo_x <= asis[0] <= hi_x and lo_y <= asis[1] <= hi_y
    if inside_win:
        ax.plot(*asis, "o", color=AS_IS, ms=8.5, mec=P.OVER_FIELD, mew=.7, zorder=5)
    ax.plot(*fixed, "o", color=FIXED, ms=5.5, mec=P.OVER_FIELD, mew=.7, zorder=6)
    if not inside_win:
        # The published estimate lies beyond the window, and a window wide enough to hold it would
        # shrink the grid to nothing. The arrow leaves the weighted-sum estimate along the true
        # direction to the published one and stops at the border; the label is the distance
        # between the two estimates, in millimetres where the voxel size is on record.
        hit = border_hit(fixed, asis, lo_x, hi_x, lo_y, hi_y)
        ax.annotate("", xy=tuple(hit), xytext=tuple(fixed),
                    arrowprops=dict(arrowstyle="-|>", color=AS_IS, lw=1.3, shrinkA=4, shrinkB=0))
        dist = float(np.hypot(*(asis - fixed)))
        label = f"{dist * mm:,.0f} mm" if mm else f"{dist / W:.3g} grid widths"
        capped = ("as-is", z) in d.get("capped", set())
        # the label sits on the arrow, past its middle, in a white box over the shaft, so it
        # never lands on the border of the grid or on the title
        pos = fixed + 0.62 * (hit - fixed)
        # the arrow this label sits on is the swatch, so the word is black and bare
        ax.text(pos[0], pos[1], label, fontsize=6.2, color=P.TEXT, ha="center", va="center",
                zorder=7, bbox=dict(boxstyle="round,pad=0.15", fc=P.OVER_FIELD, ec="none", alpha=.9))
        notes.append((scroll, z, f"published estimate off panel, {label} from the weighted sum"
                      + (", walk stopped by the cap of the search" if capped else "")))
    if ref is None and scroll in L.CFG:
        notes.append((scroll, z, why))

    ax.set_xlim(lo_x, hi_x), ax.set_ylim(lo_y, hi_y)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([]), ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(P.STRUCTURE_LIGHT), s.set_linewidth(.6)
    ax.set_title(f"{scroll.replace('PHerc', 'PHerc. ')}, slice {z}", fontsize=7.6, pad=3)
    return z, ref is not None, why, not inside_win, ("as-is", z) in d.get("capped", set())


def caption(pos, drawn, inside_fixed, inside_asis, n_slices):
    with_ref = sorted(s for s, v in drawn.items() if v[1])
    off = sorted(s for s, v in drawn.items() if v[3])
    capped = sorted(s for s, v in drawn.items() if v[4])
    challenge = [s for s in with_ref if L.CFG[s]["source"] == "challenge"]
    third = [s for s in with_ref if L.CFG[s]["source"] != "challenge"]
    no_ref = sorted(s for s in pos if s not in with_ref)
    widths = sorted(int(d["width"]) for d in pos.values())
    # On the drawn slices, where the published estimate lies outside its grid: an in bounds fact
    # read from the positions, said as such and never as a cap event.
    outside_asis = sorted(s for s, v in drawn.items()
                          if not _inside(pos[s]["as-is"][v[0]], pos[s]))
    outside_fixed = sorted(s for s, v in drawn.items()
                           if not _inside(pos[s]["no-division"][v[0]], pos[s]))
    any_capped_in_file = any(d.get("capped") for d in pos.values())

    def fmt(xs):
        """A list of scroll names for a sentence. A sentence built on an empty list would print
        a blank in a published caption, which is the class of defect no build gate catches, so
        an empty list is a programming error here and the caption is not written."""
        if not xs:
            raise SystemExit("caption: a sentence was about to be built on an empty list")
        return ", ".join(x.replace("PHerc", "PHerc. ") for x in xs)

    # every clause that depends on a list is built only when that list has members
    ref_clause = (f"Yellow cross: the reference umbilicus at that slice, drawn only on the "
                  f"{len(with_ref)} scrolls that have one"
                  + (f", published by the challenge on {fmt(challenge)}" if challenge else "")
                  + (f" and annotated by a third party on {fmt(third)}" if third else "")
                  + "; the reference was used only to measure and never to choose anything"
                  + (f", and the {len(no_ref)} scrolls {fmt(no_ref)} have none" if no_ref else "")
                  + ". ") if with_ref else ""
    off_clause = (f"Dark grey arrow: the published estimate lies beyond the window, in the "
                  f"direction the arrow leaves the blue circle, at the labelled distance between "
                  f"the two estimates, in millimetres where the voxel size of the scan is on "
                  f"record and in grid widths otherwise; this happens on {len(off)} of the "
                  f"{len(pos)} panels. ") if off else ""
    bounds_clause = ((f"On the slices drawn, the published estimate lies outside its grid on "
                      f"{len(outside_asis)} panels, {fmt(outside_asis)}, ")
                     if outside_asis else
                     "On the slices drawn, the published estimate lies inside its grid on every "
                     "panel, ")
    bounds_clause += ((f"and the estimate with the division removed on {len(outside_fixed)}, "
                       f"{fmt(outside_fixed)}. ") if outside_fixed else
                      "and the estimate with the division removed lies inside on every panel. ")
    if any_capped_in_file:
        cap_clause = (f"On {fmt(capped)} the published walk of that slice did not stop by itself "
                      f"but was stopped by the cap of the search. ") if capped else ""
    else:
        cap_clause = ("No walk in this run was stopped by a cap: the estimates are those of the "
                      "compiled function, which has no iteration limit, and every walk stopped by "
                      "itself. ")
    return (
        f"One section of every scroll of the generalisation run, {len(pos)} panels sorted by "
        f"scroll id. Grey: the segments of that scroll's normal grid on the slice named in the "
        f"title, with the bounds of the grid as a dark grey square; each panel is drawn in the units "
        f"of its own grid, whose widths run from {widths[0]:,} to {widths[-1]:,} pixels, with a "
        f"margin of {100 * PAD:.0f} % of the width on every side. Dark grey circle: the estimate of "
        f"the published estimator, the weighted mean. Blue circle: the estimate with the division "
        f"removed, the weighted sum. "
        + ref_clause + off_clause + bounds_clause + cap_clause +
        f"Slice rule: of the {L.N_HEIGHTS} slices the run "
        f"sampled on each scroll, evenly spaced along z, the panel shows the twelfth in order of "
        f"z, the lower of the two that straddle the middle of the sampled band; no slice was "
        f"chosen by looking at it. Over the whole run, {inside_fixed} of {n_slices} estimates "
        f"fall inside the volume with the division removed, against {inside_asis} of "
        f"{n_slices} as published. Drawn by tools/figure_umbilicus_gallery.py from "
        f"evidence/{os.path.basename(POSITIONS)}, the cached grids of the run and the reference "
        f"files; no estimate was recomputed.\n")


def _inside(xy, d):
    return 0 <= xy[0] <= d["width"] and 0 <= xy[1] <= d["height"]


def main():
    pos = positions()
    names = sorted(pos)
    n_slices = sum(len(d["no-division"]) for d in pos.values())
    inside_fixed = sum(d["inside"]["no-division"] for d in pos.values())
    inside_asis = sum(d["inside"]["as-is"] for d in pos.values())
    want_fixed, want_asis = summary("inside_fixed"), summary("inside_as_is")
    if (inside_fixed, inside_asis) != (want_fixed, want_asis):
        raise SystemExit(f"{os.path.basename(POSITIONS)} gives {inside_fixed} and {inside_asis} inside, "
                         f"{os.path.basename(SUMMARY)} says {want_fixed} and {want_asis}: "
                         "two runs under one name")

    rows = (len(names) + COLS - 1) // COLS
    fig, axes = plt.subplots(rows, COLS, figsize=(12.0, 2.15 * rows + 0.5))
    notes, drawn = [], {}
    for ax, scroll in zip(axes.ravel(), names):
        drawn[scroll] = panel(ax, scroll, pos[scroll], notes)
        print(f"  {scroll}: slice {drawn[scroll][0]}, reference "
              f"{'drawn' if drawn[scroll][1] else 'none: ' + drawn[scroll][2]}", flush=True)
    for ax in axes.ravel()[len(names):]:
        ax.set_visible(False)

    a0 = axes.ravel()[0]
    a0.plot([], [], "o", color=AS_IS, ms=5.5, mec=P.OVER_FIELD, mew=.7, label="as published (weighted mean)")
    a0.plot([], [], "o", color=FIXED, ms=5.5, mec=P.OVER_FIELD, mew=.7, label="division removed (weighted sum)")
    a0.plot([], [], "x", color=REF, label="reference, where one exists (measurement only)",
            **REF_MARK)
    a0.plot([], [], "-", color=BASE, lw=1, alpha=.7, label="segments of the normal grid")
    fig.legend(*a0.get_legend_handles_labels(), frameon=False, fontsize=8.5, loc="lower center",
               ncol=4, bbox_to_anchor=(.5, .005))
    fig.subplots_adjust(left=.01, right=.99, top=.965, bottom=.05, hspace=.28, wspace=.06)

    # A reader who does not hold the cut grid slices used to get a gallery with empty panels
    # written straight over the good figure, silently, and the caption with it. The figure is
    # kept in the repository and the grids are not, so that reader had no way back. Refuse
    # instead, unless the partial gallery is asked for by name, and then write it beside the
    # real one rather than on top of it.
    missing = [scroll for scroll, _, note in notes if note == "grid not on disk"]
    partial = "--allow-missing" in sys.argv
    if missing and not partial:
        plt.close(fig)
        raise SystemExit(
            f"{len(missing)} of {len(names)} scrolls have no grid slice on disk "
            f"({', '.join(missing[:4])}{', ...' if len(missing) > 4 else ''}). "
            f"Cut the slices into inputs/grid23/ as section 3 of ../README.md says, or pass "
            f"--allow-missing to write a partial gallery as {STEM}-partial, which does not "
            f"overwrite {STEM}.")
    stem = f"{STEM}-partial" if missing else STEM

    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT_DIR, f"{stem}.{ext}"), dpi=200)
        print(f"written {OUT_DIR}/{stem}.{ext}")
    plt.close(fig)
    with open(os.path.join(OUT_DIR, f"{stem}.caption.txt"), "w") as fh:
        fh.write(caption(pos, drawn, want_fixed, want_asis, n_slices))
    print(f"written {OUT_DIR}/{stem}.caption.txt")
    for scroll, z, note in notes:
        print(f"  note: {scroll} z {z}: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
