"""One palette for the three papers of the series, as roles rather than as a list of hex.

Every value in this module comes from one place, the GlobaLeaks visual identity guidelines of
October 2024, v2.0, which `data/brand/palette.md` transcribes and `data/brand/globaleaks-brand-
guidelines.pdf` is. The whole palette is a blue ramp of ten steps, a red ramp of ten, a grey ramp of
ten, one yellow with no ramp, white, and a near black. Nothing else may be drawn, and a value that
is not one of those thirty two is a bug.

A role survives a change of value and a hex does not: if the blue is ever darkened, every figure
that asks for `OURS` follows, and every figure that hard coded `#3679BB` does not. Import the
roles, never the values.

    import palette as P
    ax.plot(x, y, color=P.OURS)               # our result, the thing being aimed at
    ax.plot(x, y, color=P.REFERENCE)          # what comes from the reference or the published label
    ax.plot(x, y, color=P.BAD)                # an outcome we do not want
    ax.imshow(field, cmap=P.FIELD_CMAP)       # a continuous quantity
    ax.plot(cx, cy, "x", color=P.OVER_FIELD)  # a mark laid over that quantity
    ax.text(x, y, "5 mm", color=P.label_colour(fill))   # a word, on whatever it lies on

THE RULE, which is the part worth not rediscovering
---------------------------------------------------
A colour in these papers carries a MEANING and not an identity. Three meanings, and no figure is
allowed to invent a fourth.

    red     `BAD`        an outcome we do not want: ink no surface reaches, a correction that does
                         harm, an estimate that leaves the volume, a band declared ineffective
    yellow  `REFERENCE`  what comes from the reference or from the published label: a hand
                         annotation, a published umbilicus, ground truth, the thing being matched
    blue    `OURS`       our result, and the thing being aimed at: the recovered ink, the repaired
                         objective, the corrected chain, the band declared good

Everything else in a figure is neutral and is drawn in the structure greys: the implementation as
published, which is the subject of the measurement and not a verdict on it; the apparatus, meaning
axes, rules, bands and declared thresholds; and a control, which additionally carries a dash.

Five things follow from that, and they are the rest of this docstring.

1. **A continuous field is drawn in one of the two ramps built below**, and which one is decided
   by the quantity and never by taste. A quantity that only grows takes `FIELD_CMAP`, the blue ramp.
   A quantity that has a sign and a meaningful zero takes `DIVERGING_CMAP`, which runs from the blue
   end through white to the red end. Putting a diverging ramp on a one sided quantity is the
   commonest way to make a field lie, because it invents a middle the data does not have. As of
   today every field in the three papers is one sided and `DIVERGING_CMAP` is drawn by nothing.
   The three meanings are for CATEGORIES. They are not a colormap and a field never carries one.

2. **A category is drawn in the roles above.** Ours against the reference, a loss against what was
   recovered, one fate of a segment against another. Categories in viridis cannot be told apart:
   the ramp is built so that neighbouring values look alike, which is exactly wrong when the values
   are not neighbours but different kinds of thing.

3. **A mark laid over a field is white ON A DARK CASING** (`OVER_FIELD` with `stroke`), never a bare
   colour of any kind. The casing is not decoration here, it is the whole of what makes the mark
   work, and this is the rule that changed most when the fields left viridis. Viridis ran from a
   dark purple to a bright yellow, so a bare white mark stayed 29.8 clear of it in CIEDE2000 and a
   bare black one 26.4, and the old rule could simply say "white or black, whichever suits the
   region". The blue ramp runs from a near white to a dark navy, so bare white falls to 4.6 at the
   low end and bare black to 13.6 at the high end: neither works alone any more, and the blue itself
   falls to 0.09, because the ramp IS the blue. Drawn together, white on a dark casing, the worst
   point of the ramp is 39.0, which is better than viridis ever gave a bare mark.
   The one hue that does stand clear of the blue field by itself is the reference yellow, at 33.7,
   where under viridis it was the worst of all at 6.6. So the published label outlined over a field,
   which is the one mark in the series that has to carry a meaning, is better off now than it was;
   it keeps its casing anyway, because it also has to survive a grey printout.
   The red stands clear of the blue field too, at 46.3, and is never used as a mark for that reason:
   it would say the mark is an outcome we do not want, and a grid bound is not one.

4. **Text on a figure is black or white and nothing else, and the role goes under the word**
   (`TEXT`, `OVER_FIELD`, `label_colour`, `rule_under`). Never a coloured label, a coloured tick or
   a coloured legend entry. A glyph is a thin stroke and shows far less of a hue than a filled
   shape, so it is the first thing to fail under colour blindness, in grey and at the size a figure
   label is actually printed; the rule under the word is a filled shape and carries the hue
   properly, while the glyph gets its contrast back.
   **White on colour, black on white, whichever of the two reads better against what is under the
   word, and a word is never in two tones**: no casing, no outline, no plate of a second colour
   inside the letter. `label_colour` is that sentence as code, measuring the WCAG ratio of black
   against the fill and answering with a colour, so the answer follows the palette when a value
   moves instead of being a list of names somebody keeps up to date.
   This replaces the rule of 2026-09-18, which said the word stays black wherever it lands and
   takes a light casing where the fill is dark. The casing made the ratio arithmetic come out well
   and the page come out worse: on a scale bar the outlined letter read as worse than the plain
   white it replaced, and a two toned glyph at 7 pt is a shape before it is a word. Rule 3 is
   untouched by this: a MARK is a shape, not a word, and a mark over a field still takes its dark
   casing.
   Where a legend already shows a swatch or a line sample beside the words, the swatch carries the
   role and there is NO underline: one carrier each, never two.

5. **When a figure needs more categories than there are meanings, extend by LIGHTNESS within the
   meaning** (`RAMP_BAD`, `RAMP_REFERENCE`, `RAMP_OURS`, `RAMP_NEUTRAL`), never by a new hue. Four
   losses are four steps of the red, because all four are losses. Two runs of one configuration are
   two steps of the blue, because both are ours and neither is better than the other: that case,
   which has no verdict in it at all, is what the lightness ramps are for.

WHAT THE THREE COLOURS COST, measured rather than assumed
----------------------------------------------------------
`tools/palette_check.py` measures the scheme and prints numbers. Run it after touching this file.
Three of its results are worth carrying here, because they decide what a figure may do.

  * red against yellow, the pair most at risk, holds up: 52.1 in CIEDE2000 to normal vision and
    27.4 to the worst of the three simulated forms, deuteranopia. The pair is safe.
  * red against blue, in a printed grey copy, does NOT hold up: 47.5 against 49.6 in L*, a
    difference of 2.1 where 15 is asked for. Nor does blue against the structure grey: 1.7. Both
    pairs are common in these papers. The difference between the two is carried by hue alone, so a
    reader with a black and white printout cannot sort them. This is on record as a known cost of
    the chosen blue and not as an oversight; the smallest fix, should it be taken, is one line,
    `OURS = RAMP_OURS[2]`, which is `#1f4e79` and takes both pairs to 15.4 and 19.1.
  * the yellow is a light colour, L* 86.9. It is 13.1 in L* from the white of an axes and 10.0 from
    the pale grey a paper 02 map is painted on, so it is weak as a bare stroke on the page and weak
    as a large area fill on the pale backgrounds. It is strong against everything else in the
    scheme. Where the yellow has to be a stroke it takes the dark casing of `stroke`, and that is
    the whole remedy, because the palette has no second yellow to darken it with.

WHICH FIGURES ARE WHICH, from the figures that exist
----------------------------------------------------
Fields, and so `FIELD_CMAP`. There are three of them in the whole series, all one sided, all drawn
from two code sites:
  paper 01  `normalgrid-score-field`     the refinement score over a real slice, two panels
  paper 01  `normalgrid-hill-climb`      the same field with the walk drawn on it
  paper 01  `exponent-score-field`       the same score at five exponents (evidence, not the paper)
Categorical, and so the roles:
  paper 01  `normalgrid-mechanism`       two objectives against distance
  paper 01  `f11-sensitivity-c`, `f12-fifteen-k20`, `normalgrid-small-multiples`
  paper 01  `normalgrid-axis-along-z`, `normalgrid-two-annotations`
  paper 02  the four fates of ink, the fate of a component, the arms of the chain, the detector
  paper 03  `figure_fitter.py`, the fitter's runs against each other
Marks over a structure, which is the third case and neither of the other two:
  paper 01  `umbilicus-gallery-24`       estimates and a reference over grey segments
In the one place where a field and a mark meet, the score field, the field is the blue ramp and
every mark on it is white on a dark casing: that figure is the worked example of rule 3.

One exception is on record rather than hidden: paper 02 draws its ink map on `GREY_CMAP` and says
so in its own comment. Ink is a photographic quantity and a reader expects it dark on light, so the
exception is defensible; it is named here so that the next author knows it is an exception and not
the rule, and it is paper 02's call and not this module's. The grey ramp separates half as many
levels as the blue one, 12 against 24, so it suits an image a reader looks at and not a field a
reader has to read values off.

WHAT LEAVING VIRIDIS COST, measured on the ramps themselves
-----------------------------------------------------------
Until 18 September 2026 every field in the series was viridis, and viridis was chosen because it is
perceptually uniform. The brand palette has no green and no ramp of that kind, so the fields moved
to the blue ramp. The loss is real and it is this, in CIEDE2000 over 256 samples:

                        total path   step max/min   L* range   equal steps still separated
  viridis                    120.5           1.79      15..91                          37
  brand blue, ten stops       68.6           2.07      20..96                          24
  brand grey to the black     68.8           5.37      12..97                          12
  diverging blue to red      165.6           2.36     15..100                          53

"Equal steps still separated" is the largest number of equal steps of the DATA at which every
neighbouring pair is still 2.0 apart in CIEDE2000, which is a conservative reading of what survives
print. So the blue ramp resolves about two thirds of the levels viridis did, 24 against 37, and its
worst step is 2.07 times its best against viridis's 1.79, so it is a little less even as well as
shorter. Both ramps are monotone in lightness, so neither loses anything in a grey printout; what is
lost is the number of levels a reader can tell apart in colour. The blue ramp is the better of the
two the palette offers: the grey one separates 12.

Measured on the data of one real figure rather than on the ramp, the loss is larger, because a
panel does not use the whole scale. On `normalgrid-score-field` the published panel occupies 0.44
to 1.00 of the scale, where viridis separates 29 levels and the blue ramp 14; the corrected panel
occupies 0.09 to 0.91, where viridis separates 36 and the blue 20. The mean CIEDE2000 between
neighbouring cells of the field falls from 0.145 to 0.077 and from 0.132 to 0.073, so about half
the local contrast goes. That figure is where the loss bites hardest, because its published panel
sits in the upper half of the scale and the brand blue crowds its dark end: Blue_70 to Blue_100 is
40 per cent of the ramp and only 22 of its 76 in L*. If that figure ever has to read as it did, the
one remedy inside the palette is `DIVERGING_CMAP` centred on 1, which the quantity would carry
honestly, because 1 is the score at the published control point and it is a meaningful middle. That
would separate 53 levels. It is not done here, because it would also say that the field above 1 is
an outcome we do not want, which is true of the published panel and misleading of the other.

WHAT WAS TRIED BEFORE, AND WHY IT CHANGED, 18 September 2026
------------------------------------------------------------
Two things changed on this date, in this order, and both were the decision of the person
responsible: the scheme stopped being about identity and became about meaning, and then the values
stopped being ours and became the GlobaLeaks brand palette. The second settled several questions
the first had left open, because the three colours they had already chosen are exactly that
palette's Blue_60, Yellow and Red_60.

Until this date the module was built on two house hues, an ochre `#b5651d` for the thing as
published and a blue `#1f4e79` for the thing with our change, and it said in this docstring that no
third hue was admitted: a figure needing four categories took four steps of those two, so that it
read as two kinds of thing with a shade each rather than as four unrelated colours. Paper 02's four
fates of ink were derived that way, and that in turn replaced a redder orange `#c1440e` the paper
had carried on its own.

That rule was about IDENTITY: a colour said whose the thing was. It was coherent and it is the
reason the ramps below exist. It was changed on the decision of the person responsible, who asked
for a scheme about MEANING instead: red for an outcome we do not want, yellow for what comes from
the reference, blue for our result and the optimum, in all three papers. The case for the change is
that a reader of one of these papers wants to know whether a thing is good, bad or somebody else's
before they want to know whose code produced it, and under the old rule the largest loss in paper
02, the ink no surface of the chain ever reaches, was a pale ochre and read as a footnote.

What the change cost, so that a later author can weigh reverting it:

  * the ochre is retired as a role. Its two jobs were never one job. Where it meant the published
    LABEL or a hand annotation it is now the reference yellow; where it meant the published
    IMPLEMENTATION it is now the structure grey, which is what paper 03 had always drawn it in.
    A measurement made the retirement unavoidable in any case: the ochre against the new red is
    1.5 in CIEDE2000 under deuteranopia, so a figure carrying both would be legible to some readers
    and not to others. The brand palette then settled it a second time, by not containing it.
  * the old blue `#1f4e79` and the new blue `#3679BB` have the same job, ours and the optimum, so
    the new one replaces the old one everywhere and there is one blue. The old value is not in the
    brand palette at all, so it is gone rather than demoted: where a second step of the blue was
    wanted, as in paper 03's slice figure with its two runs, the step is `RAMP_OURS[2]`, Blue_80.
  * `REFERENCE` was black and is now the yellow, because the reference now has a meaning and a hue
    to carry it. Black did not lose a job: over a field it is still `OVER_FIELD_DARK` by rule 3,
    and it is the casing under a yellow mark. It is no longer pure black either, because the brand
    palette's black is `#1D1F24`.
  * the reference has no ramp and cannot get one, because the palette holds exactly one yellow.
    Where two things of equal standing are both references, as in paper 01's two hand annotations,
    they are both drawn in the one yellow and told apart by their marker, not by a second value.
  * the warm neutrals the papers used for a background, `#f4f2ef` and `#c9c4bc`, are not in the
    palette either. They are now Gray_10 and Gray_50, which are cooler and further apart, 22 in L*
    against the 16 they had.

THE ROLES
---------
"""
from matplotlib.colors import LinearSegmentedColormap, to_rgb

# ---- the palette itself, as the guidelines publish it -------------------------------------------
# data/brand/palette.md, from data/brand/globaleaks-brand-guidelines.pdf, pages 7, 8 and 10. Read
# out of the PDF by a tool and checked against it a second time on 2026-09-18. These four lists and
# the two values under them are the whole palette: every role below is one of these, and a figure
# that draws anything else is drawing outside the brand.
BLUE = ["#EEF5FC", "#C4DEF8", "#9FC9F1", "#79B0E6", "#5797D5",
        "#3679BB", "#2866A2", "#205282", "#1F4365", "#103253"]   # Blue_10 to Blue_100
RED = ["#FAF0F0", "#FAD4D4", "#FAB6B6", "#FA8E8E", "#F55353",
       "#DE1B1B", "#B80D0D", "#8F0E0E", "#661414", "#451717"]    # Red_10 to Red_100
GRAY = ["#F5F7FA", "#EBEFF5", "#DDE3ED", "#C8D1E0", "#AFBACC",
        "#8E99AB", "#707A8A", "#58606E", "#434A54", "#333840"]   # Gray_10 to Gray_100
YELLOW = "#FFD644"   # the only yellow in the palette, and so the only colour with no gradation
WHITE = "#FFFFFF"
BLACK = "#1D1F24"    # the brand near black, which stands in for pure black everywhere

# ---- the three meanings ------------------------------------------------------------------------
# These three are the whole scheme. A fourth hue in a figure of this series is a bug, and a role
# hue used for something that is neither good, bad nor the reference is a worse one, because it
# tells the reader something untrue rather than something unclear. They are the three colours the
# guidelines lead with: Blue_60 is the brand colour, and Yellow and Red_60 sit beside it.
BAD = RED[5]           # Red_60, an outcome we do not want
REFERENCE = YELLOW     # what comes from the reference, or from the published label
OURS = BLUE[5]         # Blue_60, our result, and the thing being aimed at

# The red and the blue by lightness, for when a figure orders several things WITHIN one meaning:
# four losses that are all losses, two runs that are both ours. Light to dark, the second step being
# the role itself. Extending a figure this way is allowed; adding a hue is not. There is no ramp of
# the reference, because the palette holds one yellow: several references in one figure are told
# apart by their marker and never by a second value.
RAMP_BAD = [RED[2], BAD, RED[7], RED[9]]       # Red_30, Red_60, Red_80, Red_100
RAMP_OURS = [BLUE[2], OURS, BLUE[7], BLUE[9]]  # Blue_30, Blue_60, Blue_80, Blue_100
BAD_LIGHT, BAD_DARK, BAD_DARKER = RAMP_BAD[0], RAMP_BAD[2], RAMP_BAD[3]
OURS_LIGHT, OURS_DARK, OURS_DARKER = RAMP_OURS[0], RAMP_OURS[2], RAMP_OURS[3]

# ---- the neutrals, which is everything that carries no verdict ----------------------------------
# The grey ramp is a real scale, so the three neutral jobs are three of its steps about thirty in L*
# apart, and not three greys picked by hand. Ordered by how much of the reader's attention the thing
# deserves, darkest first:
#   STRUCTURE_DARK   Gray_100, L* 23: data that carries no verdict, in-figure text, scale bars
#   STRUCTURE        Gray_70,  L* 51: a control, a yardstick, a null model, present and not competing
#   STRUCTURE_LIGHT  Gray_40,  L* 84: the apparatus, spines, gridlines, declared rules, a cloud
STRUCTURE = GRAY[6]        # Gray_70, the control grey, and anything there to be outranked
STRUCTURE_LIGHT = GRAY[3]  # Gray_40, the apparatus
STRUCTURE_DARK = GRAY[9]   # Gray_100, neutral data, a caption inside a figure, a scale bar
RAMP_NEUTRAL = [GRAY[1], STRUCTURE_LIGHT, STRUCTURE, STRUCTURE_DARK]

# UPSTREAM is the name to reach for when what is meant is "the code as it is published". It is a
# neutral on purpose, and the darkest one, because it is a data series and a reader has to be able
# to follow it. The published implementation is the thing these papers measure, and painting the
# subject of a measurement in the colour of a verdict argues the case before the numbers are read;
# these papers are also sent to the people who wrote that code. Where the published code genuinely
# produces an outcome we do not want, it is that OUTCOME that is drawn in the red and not the code:
# an estimate that left the grid, a correction that halved the satisfied area.
# It holds against all three meanings, in normal vision, in each simulated form and in grey.
UPSTREAM = STRUCTURE_DARK

# ---- the backgrounds that carry a meaning ------------------------------------------------------
# These are not decoration. On the bench of paper 02 the two of them are the difference between
# "we looked here and there was nothing" and "we never looked here", which a reader must be able
# to tell apart at a glance. Neither is a fate, so neither takes one of the three. They are two
# steps of the grey ramp far enough apart to survive a grey printout, 22 in L*.
PAPER = GRAY[0]    # Gray_10, seen and empty: the field a detector did look at
ABSENT = GRAY[4]   # Gray_50, not seen at all: no data, outside the volume, no surface

# ---- fields, and what goes on top of them ------------------------------------------------------
# Two ramps and no more, because the palette has no third. FIELD_CMAP is the blue ramp and carries
# every quantity that only grows. DIVERGING_CMAP runs from the blue end through white to the red end
# and carries a quantity that has a sign and a meaningful zero; nothing in the series draws it
# today, and putting it on a one sided quantity would invent a middle the data does not have.
# GREY_CMAP is the grey ramp, for the one declared exception, paper 02's photographic ink map.
FIELD_CMAP = LinearSegmentedColormap.from_list("brand_blue", BLUE, N=256)
GREY_CMAP = LinearSegmentedColormap.from_list("brand_grey", GRAY + [BLACK], N=256)
DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "brand_diverging", [BLUE[9], BLUE[5], BLUE[2], WHITE, RED[2], RED[5], RED[9]], N=256)
OVER_FIELD = WHITE       # a mark over a field, on the dark end of the ramp
OVER_FIELD_DARK = BLACK  # a mark over a field, on the light end of the ramp, and every casing

# ---- text, which by rule 4 is black or white and never a hue ------------------------------------
# TEXT is the word on the page and on any light fill, which is nearly every word in the series:
# labels, ticks, titles, annotations, legend entries and the numbers written inside a pale bar. It
# is the brand near black and not pure black, because the palette holds no pure black. RC carries it
# into matplotlib in one line, and it also takes the tick marks and the spines off pure black, which
# were the last two places the figures drew a colour that is not in the palette.
# A word that lies on a dark fill takes OVER_FIELD, the plain white, and takes it bare. Which of the
# two a given fill asks for is label_colour's answer and not a judgement.
TEXT = BLACK
RC = {
    "text.color": TEXT, "axes.labelcolor": TEXT, "axes.titlecolor": TEXT,
    "axes.edgecolor": TEXT, "xtick.color": TEXT, "ytick.color": TEXT,
    "xtick.labelcolor": TEXT, "ytick.labelcolor": TEXT, "legend.labelcolor": TEXT,
}


def label_colour(colour, minimum=4.5):
    """The colour a word takes on this fill: black on a light fill, white on a coloured one.

    Rule 4, as code. The rule is white on colour and black on white, whichever reads better, and a
    word is never two toned: no casing, no outline. The measure is the WCAG contrast ratio of the
    brand near black against the fill and not a list of names, so that it follows the palette when
    a value moves, and the threshold is the 4.5 to 1 that the standard asks of small text. Where
    black clears it the word is black; where it does not, white is what the fill leaves.

    Bare black is 3.36 to 1 on Red_60, 1.76 on Red_80, 3.62 on Blue_60, 1.40 on Gray_100, 1.26 on
    the dark end of the field ramp and 1.00 on the dark end of the ink map. Every one of those is a
    fill on which this returns OVER_FIELD.

        ax.text(x, y, "5 mm", color=P.label_colour(P.BLUE[9]))
    """
    r, g, b = to_rgb(colour)
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    black = 0.2126 * 0.0118 + 0.7152 * 0.0129 + 0.0722 * 0.0157   # the brand near black, linear
    ratio = (max(y, black) + 0.05) / (min(y, black) + 0.05)
    return OVER_FIELD if ratio < minimum else TEXT


def text_over_field(width=1.6):
    """The light casing, which NO WORD takes any more. Kept for marks, and named for a job it lost.

    Between 2026-09-18 and 2026-09-19 a word on a dark fill stayed black and took this casing. Rule
    4 now says a word is one colour, so `label_colour` answers that question and nothing in these
    papers passes this to an `ax.text`. What is left is a light casing for a MARK that lies on the
    light end of a ramp, which is rule 3 read the other way round and is a real job, so the
    function stays; the name is wrong for it and is worth changing in all three papers at once
    rather than in one.
    """
    return stroke(width, over_field=True)


def _too_pale_for_the_page(colour, minimum=15.0):
    """Whether a shape of this colour would fade into the page once the colour is gone.

    The lightness of the grey a colour prints as, against the lightness of the paper. Written out
    here rather than imported, because this module has no dependency beyond matplotlib's colormaps
    and tools/palette_check.py is the thing that checks it, not the thing it leans on.
    """
    rgb = [int(colour.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    star = 116 * (y ** (1 / 3)) - 16 if y > (6 / 29) ** 3 else y * (29 / 3) ** 3 / 100.0
    return (100.0 - star) < minimum


def rule_under(fig, text, colour, lw=3.2, pad=0.005, zorder=6):
    """Draw the coloured rule that carries a label's role, under the word, in figure coordinates.

    The rule is the role and the word is the word. It is 3.2 pt and as long as the text it sits
    under, which is what makes it a filled shape a reader can take a hue off rather than the thin
    stroke the glyph would have been. Figure coordinates, so it cannot be clipped by the axes, and
    it is placed after the layout is settled: call this immediately before saving.

    Use it only where nothing else beside the word already carries the role. Where a legend has a
    swatch, or the label sits on its own coloured bar or band, that shape is the carrier and the
    underline would be a second one, which rule 4 forbids.

    A rule light enough to fade into the page in a grey printout gets a thin dark casing of its own,
    decided by measurement and not by name. Only the yellow needs it: as a rule on the page the red
    is 52.5 apart in L* and the blue 50.5, and the yellow is 13.1 against the 15 asked for. Nothing
    draws a yellow rule today, and the day something does it will already be right.
    """
    from matplotlib.lines import Line2D
    fig.canvas.draw()
    box = text.get_window_extent().transformed(fig.transFigure.inverted())
    y = box.y0 - pad
    effects = stroke(lw + 1.2) if _too_pale_for_the_page(colour) else None
    line = Line2D([box.x0, box.x1], [y, y], color=colour, lw=lw, solid_capstyle="butt",
                  transform=fig.transFigure, zorder=zorder, path_effects=effects)
    fig.add_artist(line)
    return line


def casing(colour, over_field=False):
    """The two colours of a mark that has to carry a meaning AND survive what lies under it.

    Rule 3 says a mark over a field is white or black, because a role hue disappears somewhere along
    the ramp. A published label outlined over an ink map is the case where that is not good enough:
    the label is the reference and a reader is entitled to see it in the reference colour. The
    remedy is to draw both, the hue over a dark casing one step wider, so that the mark reads as
    yellow in colour and as a dark line in a grey printout. Returns (casing, mark).

    The same remedy covers the reference drawn as a plain line on the white of an axes, which needs
    it for a different reason: the yellow is a light colour, L* 86.9, and it is only 13.1 in L* from
    the page, so it survives in colour and fades in a grey printout. There is no darker yellow to
    reach for instead, because the palette has exactly one.
    """
    return (OVER_FIELD if over_field else OVER_FIELD_DARK), colour


def stroke(width=2.6, over_field=False):
    """matplotlib path_effects that put the casing of `casing` under a line or a marker.

        ax.plot(x, y, color=P.REFERENCE, path_effects=P.stroke())

    The width is the total width of the casing, so it is set a little wider than the line it backs.
    """
    from matplotlib import patheffects
    return [patheffects.withStroke(linewidth=width,
                                   foreground=OVER_FIELD if over_field else OVER_FIELD_DARK)]


# ---- a control is none of the three -------------------------------------------------------------
# A control is a line drawn to show that the comparison can fail: the constant axis at the centre
# of the field in paper 01, which on one scroll beats every real rule and so says that scroll ranks
# nothing, and the CPU arms of paper 03, which are a perturbation and not a repair. Giving a control
# one of the three meanings would read as a claim, and giving it a hue of its own would say the
# figure has a fourth kind of thing in it when it has three and a yardstick. So a control is drawn
# in the middle grey of the ramp and dashed, and the dash is what tells a reader at a glance that
# the line is not competing. Colour and dash are both here, because a control drawn solid is the
# mistake this role exists to prevent. Where a control is a marker and not a line, and a dash is
# impossible, the same job is done by an open marker of its own shape: that is CONTROL_MARKER.
CONTROL = STRUCTURE
CONTROL_LIGHT = STRUCTURE_LIGHT   # when several controls would otherwise crowd the figure
CONTROL_DASH = (0, (4, 2))        # matplotlib linestyle: the dash every control carries
CONTROL_MARKER = dict(marker="D", mfc="none", mew=1.4)  # the caller gives the colour

# ---- the names the figure tools already used ---------------------------------------------------
# The three papers' scripts were written with these names before the roles existed, and then before
# the scheme changed. They are kept as aliases so that adopting a change is a one line edit in each
# tool and not a rewrite. New code uses the roles above. Two of these aliases now point somewhere
# else than they did, and that is the point of the change rather than an accident of it:
#   PUBLISHED and AS_IS were the ochre and are now the dark grey, because the implementation as
#   published is a neutral subject and not a verdict;
#   REPAIRED and FIXED were #1f4e79 and are now Blue_60, the one blue.
PUBLISHED = UPSTREAM
REPAIRED = OURS
RAMP_PUBLISHED = RAMP_NEUTRAL
RAMP_REPAIRED = RAMP_OURS
AS_IS = UPSTREAM
FIXED = OURS
BASE = STRUCTURE
REF = REFERENCE

# Two values of the old scheme, kept so that a reader of an old figure script finds them here and so
# that the change is legible rather than silent. Neither is in the brand palette and nothing draws
# them: the ochre meant "as published" and the orange was paper 02's own label line.
RETIRED_OCHRE = "#b5651d"
RETIRED_ORANGE = "#c1440e"

ROLES = {
    "bad": BAD, "bad_light": BAD_LIGHT, "bad_dark": BAD_DARK, "bad_darker": BAD_DARKER,
    "reference": REFERENCE,
    "ours": OURS, "ours_light": OURS_LIGHT, "ours_dark": OURS_DARK, "ours_darker": OURS_DARKER,
    "upstream": UPSTREAM,
    "structure": STRUCTURE, "structure_light": STRUCTURE_LIGHT, "structure_dark": STRUCTURE_DARK,
    "paper": PAPER, "absent": ABSENT,
    "over_field": OVER_FIELD, "over_field_dark": OVER_FIELD_DARK, "text": TEXT,
}


def show():
    """Print the roles and their values, for a reader who wants the hex after all."""
    for name, value in ROLES.items():
        print(f"  {name:18s} {value}")
    # The control is not in ROLES because its colour is the middle grey and listing the same hex
    # twice reads as two roles. What makes it a control is the dash, so print that instead.
    print(f"  {'control':18s} {CONTROL} dashed {CONTROL_DASH}")
    print(f"  {'field ramp':18s} {FIELD_CMAP.name}, {BLUE[0]} to {BLUE[-1]}")
    print(f"  {'grey ramp':18s} {GREY_CMAP.name}, {GRAY[0]} to {BLACK}")
    print(f"  {'diverging ramp':18s} {DIVERGING_CMAP.name}, drawn by nothing today")
    print(f"  {'retired':18s} {RETIRED_OCHRE} and {RETIRED_ORANGE}, outside the palette")


if __name__ == "__main__":
    show()
