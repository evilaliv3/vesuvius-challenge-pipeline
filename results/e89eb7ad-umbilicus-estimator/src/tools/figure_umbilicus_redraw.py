# This file is a copy of tools/figure_umbilicus_rev1.py of the working tree and differs from it
# in one way only: the absolute paths of the machine the measurements ran on are replaced by
# paths inside this folder, resolved from the file's own location, and the declared epoch is
# the constant below rather than a reading of the build script, which is not in this folder.
# Nothing else is changed.
#!/usr/bin/env python3
"""Redraw the normal-grid figures for the revision, with the legend the revision uses.

The frozen run under inputs/ is read, never written: its drawing script is loaded as
text, two things are changed in it, and the result is executed against a figure directory of our
own. The two changes are

  1. the in-image legend "line 116 removed", which names a line number that means nothing to a
     reader of the paper, becomes "division removed", the phrase the paper itself uses;
  2. the draw runs with the faithful sampler of tools/rev1_lib.py, so the figures are made by the
     same estimator as every number in the revision (villa_estimator.sample capped the draw at the
     pool size; the C++ always draws N_SAMPLES with replacement).

Usage: figure_umbilicus_redraw.py [f1 f2 ...]   (default: all nine)
Output: SVG and PNG in build/figures-umbilicus, then PDF in build/figures.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# The epoch the figures are drawn at. It is the date the article prints on its title page and
# the date its /CreationDate carries, declared here because the build that declares it is not
# in this folder: the article is delivered as ../article.pdf and a reader who redraws a figure
# has to reach the same bytes. Bump it only together with the article.
DECLARED_EPOCH = "1789776000"          # 2026-09-19T00:00:00Z
RUN = os.path.join(ROOT, "inputs")
SRC = os.path.join(RUN, "figure_umbilicus.py")
FIG = os.path.join(ROOT, "build", "figures-umbilicus")
PDF = os.path.join(ROOT, "build", "figures")
OLD, NEW = "line 116 removed", "division removed"
NAMES = {"f1-mechanism": "normalgrid-mechanism", "f2-score-field": "normalgrid-score-field",
         "f3-fifteen": "normalgrid-fifteen", "f4-inside-volume": "normalgrid-inside-volume",
         "f5-two-annotations": "normalgrid-two-annotations",
         "f6-small-multiples": "normalgrid-small-multiples",
         "f7-hill-climb": "normalgrid-hill-climb", "f8-run-spread": "normalgrid-run-spread",
         "f9-axis-along-z": "normalgrid-axis-along-z"}


def load():
    sys.path.insert(0, HERE)
    import rev1_lib
    import villa_estimator as ve
    ve.sample = rev1_lib.sample          # the faithful draw, for the figures too
    src = open(SRC).read()
    n = src.count(OLD)
    if n == 0:
        raise SystemExit(f"{SRC}: the legend {OLD!r} is not there any more, check before drawing")
    src = src.replace(OLD, NEW).replace(
        'FIG = os.path.join(HERE, "figures")', f'FIG = {FIG!r}')
    # The third change: the frozen script carries the palette as three hex literals, written
    # before tools/palette.py existed. They are swapped for the roles, so that a later change to
    # the series palette reaches these figures as it reaches the others.
    palette_line = 'AS_IS, FIXED, BASE = "#b5651d", "#1f4e79", "#7a7a7a"'
    if palette_line not in src:
        raise SystemExit(f"{SRC}: the palette line is not there any more, check before drawing")
    src = src.replace(palette_line,
                      "import palette as _P\n"
                      "AS_IS, FIXED, BASE = _P.UPSTREAM, _P.OURS, _P.STRUCTURE\n"
                      "plt.rcParams.update(_P.RC)")
    src = src.replace('s.set_color("#cfcfcf")', 's.set_color(_P.STRUCTURE_LIGHT)')
    src = src.replace('cmap="viridis"', 'cmap=_P.FIELD_CMAP')
    # The fourth change, 2026-09-18, and the reason this list grew: the palette now says what a
    # colour MEANS rather than whose the thing is, so three places in the frozen script are drawing
    # the wrong meaning and no change of value in palette.py can reach them.
    #
    #  1. f5 draws the two umbilici of one scroll in the two hues that everywhere
    #     else in this paper mean "the published implementation" and "ours". Both are references,
    #     neither is ours, and they are of equal standing, so both become the reference yellow.
    #     (Their standing is equal, their kind is not: one is a hand annotation and the other a
    #     per slice centroid of the papyrus mask. The figure has always said so in its caption;
    #     the word "annotations" was corrected out of this comment on 2026-09-19.) The
    #     palette holds exactly one yellow and no ramp of it, so they are told apart by their
    #     markers, which the script already draws differently, and not by a second value. Both carry
    #     the casing of palette.stroke, because a yellow line on a white page fades in a grey
    #     printout.
    #  2. f9 draws the published umbilicus, which is the reference of the whole paper, in black.
    #     Black was the reference role until today and is now only the casing, so the curve takes
    #     the reference yellow on its casing.
    #  3. f6 draws the bounds of each normal grid in black, which is apparatus and not a reference,
    #     so it takes the structure grey.
    #
    # The estimates that fall outside a grid, the triangles clipped to the border of f6, were
    # considered for the red and deliberately left in their arm's colour: that figure's claim is
    # WHICH arm leaves the volume, so the arm has to stay identifiable, and the triangle already
    # says "outside" without spending a hue on it.
    changes = [
        ('ax.plot(A[:, 2], A[:, i], "-o", ms=3, lw=1, color=AS_IS,',
         'ax.plot(A[:, 2], A[:, i], "-o", ms=3, lw=1, color=_P.REFERENCE,\n'
         '                path_effects=_P.stroke(2.6),'),
        ('ax.plot(B[:, 2], B[:, i], "-", lw=1, color=FIXED,',
         'ax.plot(B[:, 2], B[:, i], "-", lw=1.8, color=_P.REFERENCE,\n'
         '                path_effects=_P.stroke(3.4),'),
        ('axes[1].plot(A[:, 2], d, "-o", ms=3, lw=1, color="k")',
         'axes[1].plot(A[:, 2], d, "-o", ms=3, lw=1, color=_P.STRUCTURE_DARK)'),
        ('plt.Rectangle((0, 0), 1, H / W, fill=False, ec="k", lw=.9)',
         'plt.Rectangle((0, 0), 1, H / W, fill=False, ec=_P.STRUCTURE, lw=.9)'),
        ('ax.plot(a[:, 2] * mm_voxel, a[:, i] * mm_voxel, "-", color="k", lw=1.4,',
         'ax.plot(a[:, 2] * mm_voxel, a[:, i] * mm_voxel, "-", color=_P.REFERENCE, lw=1.4,\n'
         '                path_effects=_P.stroke(3.2),'),
    ]
    for before, after in changes:
        if before not in src:
            raise SystemExit(f"{SRC}: {before[:48]!r} is not there any more, check before drawing")
        src = src.replace(before, after)
    # The fifth change, 2026-09-18, and the one the brand palette forced: the two field figures lay
    # every mark on the score field in bare white, which was right while the field was viridis,
    # because white stayed 29.8 in CIEDE2000 from every point of that ramp. The field is now the
    # brand blue ramp, which starts at a near white, and bare white falls to 4.6 at its low end. So
    # every white mark takes the dark casing of palette.stroke, which puts the worst point of the
    # ramp at 39.0, better than viridis ever gave a bare mark. See rule 3 of tools/palette.py.
    # The sixth change: the two labels that lie on the score field are words and not marks, so
    # they take the palette's white and take it BARE. The rule is white on colour and black on
    # white, whichever of the two reads better, and a word is never in two tones: no casing, no
    # outline. Both of these lie on the dark end of the ramp, where black is 1.26 to 1 and white
    # is what is left, so the colour is the whole of the answer and nothing goes under the glyph.
    #
    # It is written as a substitution and not left to the blanket rewrite below because the two
    # are not the same change: that rewrite gives every white MARK the dark casing rule 3 asks
    # for, and a word must not pick it up on the way past. These therefore go first, so that the
    # blanket rewrite sees only the marks.
    #
    # Between 2026-09-18 and 2026-09-19 these two lines put the labels in black on a light casing,
    # under the older rule that a word is black wherever it lands. That rule is gone and so is the
    # casing. The check below is the one that would have caught the state in between: a black word
    # on the dark end of the field stops the draw rather than reaching a figure.
    labels = [
        ('ax.text(x + n / 2, y + 0.022 * (y1 - y0), label or f"{length_mm:.0f} mm",\n'
         '            color="w", fontsize=7, ha="center", va="bottom")',
         'ax.text(x + n / 2, y + 0.022 * (y1 - y0), label or f"{length_mm:.0f} mm",\n'
         '            color=_P.OVER_FIELD, fontsize=7, ha="center", va="bottom")'),
        ('ax.text(.03, .955, f"score at the cross {denom[divide]:.3f}", transform=ax.transAxes,\n'
         '                color="w", fontsize=7, va="top")',
         'ax.text(.03, .955, f"score at the cross {denom[divide]:.3f}", transform=ax.transAxes,\n'
         '                color=_P.OVER_FIELD, fontsize=7, va="top")'),
    ]
    for before, after in labels:
        if before not in src:
            raise SystemExit(f"{SRC}: a label over the field moved, check before drawing")
        src = src.replace(before, after)
    dark = [ln for ln in src.split("\n")
            if "ax.text" in ln and ("_P.TEXT" in ln or "P.TEXT" in ln or 'color="k"' in ln)]
    if dark:
        raise SystemExit(f"{SRC}: a word on the score field is black, which on the dark end of "
                         f"this ramp is 1.26 to 1: {dark[0].strip()[:80]}")
    if any("text_over_field" in ln for ln in src.split("\n")):
        raise SystemExit(f"{SRC}: a word on the score field carries a casing, and a word is never "
                         "in two tones")
    n_white = src.count('color="w"') + src.count('mec="w"')
    if n_white < 8:
        raise SystemExit(f"{SRC}: only {n_white} white marks found, check before drawing")
    src = src.replace('color="w"', 'color=_P.OVER_FIELD, path_effects=_P.stroke(3.0)')
    src = src.replace('mec="w"', 'mec=_P.OVER_FIELD, path_effects=_P.stroke(3.0)')
    print(f"  {len(labels)} labels over the field turned bare white, "
          f"{n_white} white marks given a dark casing")
    ns = {"__file__": SRC, "__name__": "figure_umbilicus_redraw"}
    exec(compile(src, SRC, "exec"), ns)
    print(f"loaded {SRC}, legend replaced {n} times, figures to {FIG}")
    return ns


def fix_the_clock():
    """Put the paper's declared epoch in the environment, if the caller has not.

    Two steps of this tool read the clock if nothing stops them: matplotlib stamps a date into the
    metadata of every SVG it writes, and rsvg-convert stamps /CreationDate into every PDF, which
    moves by a second between two runs of the same input. Both obey SOURCE_DATE_EPOCH. The value is
    the date the article prints on its own title page, so it is DECLARED_EPOCH above and never a
    reading of the clock: two runs of the same input have to give the same bytes.
    """
    os.environ.setdefault("SOURCE_DATE_EPOCH", DECLARED_EPOCH)
    return os.environ["SOURCE_DATE_EPOCH"]


def main():
    print(f"  SOURCE_DATE_EPOCH={fix_the_clock()}")
    ns = load()
    want = sys.argv[1:] or ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9"]
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(PDF, exist_ok=True)
    for name in want:
        ns[name]()
    for stem, out in NAMES.items():
        svg = os.path.join(FIG, f"{stem}.svg")
        if not os.path.exists(svg):
            continue
        subprocess.run(["rsvg-convert", "-f", "pdf", svg, "-o",
                        os.path.join(PDF, f"{out}.pdf")], check=True)
        print(f"  {stem}.svg -> build/figures/{out}.pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
