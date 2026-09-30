"""figstyle.py: the one visual language of the works' figures, for matplotlib and for raster images.

THIS FILE IS SHARED, like results/figpreamble.tex, and for the same reason: each work carries a copy
in src/tools/ because a published folder has to stand on its own, and results/check_figpreamble.py
refuses a copy that has drifted. Written 2026-09-28 by the coordinator on the director's note of
18:29:38Z (owner's word): IEEE serif type, one colour blind safe palette, vector PDF, a scale bar on
every raster, legends inside the figure, no chart junk.

The palette is the Okabe and Ito set (Color Universal Design, 2002). The values are the ones of
results/figpreamble.tex, under the same names. A colour carries a ROLE, the rule of the umbilicus
work's palette.py: our result blue, the reference or published label orange, an outcome we do not
want vermillion; a second series of ours sky blue, a third bluish green; neutral grey. For squares
drawn on a sheet: the certified square sky blue (the director's «cyan»), the hole free square
orange, the flags vermillion (v2) and reddish purple (self conflict).

    import figstyle as F
    F.use()                                   # matplotlib: serif type, sizes, spines, vector output
    ax.plot(x, y, color=F.OURS)
    F.scale_bar_pil(img, mm_per_px, length_mm=5)   # a raster drawn with PIL
    F.scale_bar_mpl(ax, mm_per_unit, length_mm=5)  # a raster shown with imshow
"""

def _rgb(r, g, b):
    return "#%02x%02x%02x" % (r, g, b)


BLUE = _rgb(0, 114, 178)
ORANGE = _rgb(230, 159, 0)
GREY = _rgb(110, 110, 110)
GREEN = _rgb(0, 158, 115)
SKY = _rgb(86, 180, 233)
VERMILLION = _rgb(213, 94, 0)
PURPLE = _rgb(204, 121, 167)
YELLOW = _rgb(240, 228, 66)
BLACK = "#000000"

OURS, REFERENCE, BAD = BLUE, ORANGE, VERMILLION
SERIES = [BLUE, ORANGE, SKY, GREEN, VERMILLION, PURPLE, GREY]
CERTIFIED, HOLE_FREE, FLAG_V2, FLAG_SELF = SKY, ORANGE, VERMILLION, PURPLE

# IEEE two column page: one column 3.5 in, both 7.16 in; text 8 to 9 pt in figures.
COLUMN_IN, PAGE_IN = 3.5, 7.16
SERIF = ["TeX Gyre Termes", "Nimbus Roman", "Times New Roman", "Times", "DejaVu Serif"]


def use():
    """Set matplotlib to the house style. Import matplotlib only here, so raster tools need not."""
    import matplotlib
    from cycler import cycler
    matplotlib.rcParams.update({
        "font.family": "serif", "font.serif": SERIF, "mathtext.fontset": "stix",
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
        "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.prop_cycle": cycler(color=SERIES),
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": GREY, "axes.linewidth": 0.6, "axes.grid": False,
        "xtick.color": GREY, "ytick.color": GREY, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "legend.frameon": False, "figure.dpi": 150,
        "savefig.format": "pdf", "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def _nice(length_mm):
    for v in (0.5, 1, 2, 5, 10, 20, 50):
        if v >= length_mm:
            return v
    return length_mm


def scale_bar_pil(img, mm_per_px, length_mm=None, margin=None, colour=(0, 0, 0), halo=(255, 255, 255), font_px=None):
    """Draw a scale bar in the lower right corner of a PIL image, inside the image. Returns the length in mm.

    The label follows the image width (font_px = width / 40, at least 14), so it prints at about 8 pt
    whatever the image is scaled to at page width; a fixed 14 px printed at about 4 pt on work A's
    figure A4 (coordinator, 2026-09-28T18:52Z, from the work A agent's report)."""
    from PIL import ImageDraw, ImageFont
    w, h = img.size
    font_px = font_px or max(14, w // 40)
    margin = margin if margin is not None else max(12, font_px)
    L = length_mm or _nice(0.2 * w * mm_per_px)
    n = max(1, int(round(L / mm_per_px)))
    d = ImageDraw.Draw(img)
    x1, y1 = w - margin, h - margin
    x0 = x1 - n
    t = max(4, font_px // 4)
    d.rectangle((x0 - 3, y1 - t - font_px - 6, x1 + 3, y1 + 3), fill=halo)
    d.rectangle((x0, y1 - t, x1, y1), fill=colour)
    label = ("%g mm" % L)
    try:
        font = ImageFont.truetype("/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-regular.otf", font_px)
    except OSError:
        font = ImageFont.load_default()
    d.text(((x0 + x1) / 2, y1 - t - 3), label, fill=colour, anchor="ms", font=font)
    return L


def scale_bar_mpl(ax, mm_per_unit, length_mm=None, loc="lower right", colour="black"):
    """A scale bar inside a matplotlib image axis. Returns the length in mm."""
    from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
    x0, x1 = ax.get_xlim()
    L = length_mm or _nice(0.2 * abs(x1 - x0) * mm_per_unit)
    ax.add_artist(AnchoredSizeBar(ax.transData, L / mm_per_unit, "%g mm" % L, loc, pad=0.3, color=colour,
                                  frameon=True, size_vertical=abs(x1 - x0) * 0.006, borderpad=0.4))
    return L
