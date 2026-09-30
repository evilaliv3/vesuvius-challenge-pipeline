#!/usr/bin/env python3
"""The three things every figure script of this work needs, and nothing else.

Why it exists. Each figure is one script, and each script reads the study CSV the figure
specification names and writes two files: the picture and the table of the numbers that were
plotted. Three pieces of that job are identical in every script and are written once here: reading
a study CSV whose first line or lines are a prose comment, writing the plotted table back in the
same form, and refusing to run heavy work on a machine that is not free.

The rule this file enforces and does not decorate. A number is read from a column of a file, or it
is not drawn. There is no default, no fallback value and no constant of the world in this module:
the voxel size, the pitch and the thresholds come from the dataset manifests through
pipeline/datasets/voxel.py or from the study CSV that recorded them, because a tool that carries a
constant of its own is the defect that made every millimetre of this laboratory 4.02 per cent short
on 2026-09-20.

A cell that a study wrote as "not measurable" stays "not measurable": it is never turned into a
zero, never dropped in silence, and the count of the rows it removed from a panel is written into
the plotted table so a reader can see what the picture does not show.
"""

import csv
import os
import subprocess
import sys
import time

NOT_MEASURABLE = "not measurable"


def read_study_csv(path):
    """Return (comment_lines, fieldnames, rows) of a study CSV.

    A study CSV of this laboratory opens with one or more comment lines: either a bare line
    beginning with a hash, which may contain commas, or a single quoted field beginning with a
    hash. Both forms are recognised by the same test, on the first cell, so neither has to be
    special cased by a caller.
    """
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    comment = []
    i = 0
    while i < len(rows) and rows[i] and rows[i][0].lstrip().startswith("#"):
        comment.append(",".join(rows[i]) if len(rows[i]) > 1 else rows[i][0])
        i += 1
    if i >= len(rows):
        raise SystemExit(f"{path}: comment lines and no header")
    fieldnames = rows[i]
    out = [dict(zip(fieldnames, r)) for r in rows[i + 1:] if r]
    return comment, fieldnames, out


def number(cell):
    """The float in a cell, or None when the study wrote something that is not a number.

    "not measurable" and the empty cell both give None. They are different things and the caller
    says which it found; what they are never allowed to become is a zero.
    """
    if cell is None:
        return None
    s = cell.strip()
    if s == "" or s.lower().startswith("not measurable"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def write_plotted(path, comment, fieldnames, rows):
    """Write the table of the numbers a figure plotted, in the form the study CSVs use.

    One line of prose, then the header, then the rows. The comment is folded onto one physical
    line so that a reader of the file and pgfplotstable, told to skip one line, see the same
    table.

    Commas inside a cell become semicolons, and the comment says so. The reason is mechanical and
    is the point of this whole arrangement: the picture is drawn by pgfplotstable reading this
    very file, pgfplotstable splits on the separator and does not honour quoting, and a quoted
    provenance sentence with a comma in it would silently shift every column to its right. Only
    text cells are ever touched: a numeric cell with a comma in it would be a defect, and the
    check below refuses the file rather than write one.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    def cell(v):
        s = "" if v is None else str(v)
        return s.replace(",", ";").replace("\n", " ").strip()

    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_NONE, escapechar="\\")
        w.writerow([cell("# " + " ".join(comment.split())
                         + " Commas inside a cell were written as semicolons so that"
                         + " pgfplotstable reads the columns this header names.")])
        w.writerow([cell(f) for f in fieldnames])
        for r in rows:
            w.writerow([cell(r.get(k, "")) for k in fieldnames])
    return path


def _ticks():
    with open("/proc/stat") as fh:
        f = fh.readline().split()[1:]
    v = [int(x) for x in f]
    idle = v[3] + v[4]
    return sum(v), idle


def cores_busy(seconds=5.0):
    """Cores busy over a window, from the difference of /proc/stat ticks.

    Never ps -o pcpu, which reports a lifetime average and reads a finished burst as work in
    progress. The number is comparable with the one tools/machine.sh prints.
    """
    t0, i0 = _ticks()
    time.sleep(seconds)
    t1, i1 = _ticks()
    dt = t1 - t0
    if dt <= 0:
        raise SystemExit("/proc/stat did not move: cannot read the load")
    ncpu = os.cpu_count()
    return (1.0 - (i1 - i0) / dt) * ncpu


def require_free_machine(limit=2.0, seconds=5.0):
    """Stop rather than measure or read gigabytes beside somebody else's timing run.

    Every raster figure of this work reads volume data, and a timing bench that shares the disk
    and the last level cache with such a read writes seconds that are not the seconds it claims.
    A figure is worth less than a bench, so the figure yields.
    """
    if os.environ.get("SA_FIGURES_IGNORE_LOAD") == "1":
        sys.stderr.write("load check skipped by SA_FIGURES_IGNORE_LOAD\n")
        return None
    busy = cores_busy(seconds)
    if busy > limit:
        raise SystemExit(
            f"cores busy {busy:.1f} of {os.cpu_count()} over {seconds:.0f} s, above the bar of "
            f"{limit:.1f}: this figure reads volume data and is not drawn beside other work. "
            f"Set SA_FIGURES_IGNORE_LOAD=1 to override, and say in the caption that it was."
        )
    return busy


def utc_now():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()


# ------------------------------------------------------------------------------------------
# The two readers the raster figures share. Both hand back the same thing: a boolean coverage
# mask on a lattice, and the volume coordinates of the covered cells. Neither carries a voxel
# size, a threshold or an axis order of its own.
# ------------------------------------------------------------------------------------------

SHEET_POINT = [("x", "<f4"), ("y", "<f4"), ("px", "<f4"), ("py", "<f4"), ("pz", "<f4")]


def read_sheet(path):
    """One delivered sheet, patch_<n>.bin, as a coverage mask and three coordinate planes.

    The record layout and the lattice are the ones tools/square.py of this laboratory declares
    and the ones bin2tifxyz.cpp writes: a flat sequence of five little endian float32, x and y
    the sheet's own parametrisation coordinates and px, py, pz the volume coordinates in voxels;
    the lattice site of a point is the rounded offset of its parametrisation coordinate from the
    minimum, at step one. A cell holds the last point that landed on it, which is what
    bin2tifxyz does.

    Returns (mask, px, py, pz, origin) with mask of shape (cells_i, cells_j) and the three
    coordinate planes filled only where mask is true. origin is the pair of minima the lattice
    was measured from, so a cell index can be turned back into the sheet's own coordinate.
    """
    import numpy as np
    pts = np.fromfile(path, dtype=np.dtype(SHEET_POINT))
    if pts.size == 0:
        raise SystemExit(f"{path}: no point in the file")
    xmin, ymin = float(pts["x"].min()), float(pts["y"].min())
    i = np.rint(pts["x"].astype(np.float64) - xmin).astype(np.int64)
    j = np.rint(pts["y"].astype(np.float64) - ymin).astype(np.int64)
    ni, nj = int(i.max()) + 1, int(j.max()) + 1
    mask = np.zeros((ni, nj), dtype=bool)
    px = np.zeros((ni, nj), dtype=np.float32)
    py = np.zeros((ni, nj), dtype=np.float32)
    pz = np.zeros((ni, nj), dtype=np.float32)
    mask[i, j] = True
    px[i, j] = pts["px"]
    py[i, j] = pts["py"]
    pz[i, j] = pts["pz"]
    return mask, px, py, pz, (xmin, ymin)


def read_tifxyz_mask(folder, stride=1):
    """A tifxyz grid as a coverage mask, subsampled by stride.

    The covered test is the one measure_grids.py of finished-sheet-0139 declares and its header
    records: a cell is covered when its three values are neither all zero nor all minus one and
    are all finite. Both markers are in use in this laboratory's data, the delivered grids write
    zero and the published meshes write minus one, and a reader that knows only one of them
    calls every cell of the other kind covered.

    stride subsamples both axes. A 1537 by 440582 mask is 677 MB on disk and is read through a
    memory map, so a stride of ten reads a hundredth of the pages.
    """
    import numpy as np
    import tifffile
    xs = tifffile.memmap(os.path.join(folder, "x.tif"), mode="r")[::stride, ::stride]
    ys = tifffile.memmap(os.path.join(folder, "y.tif"), mode="r")[::stride, ::stride]
    zs = tifffile.memmap(os.path.join(folder, "z.tif"), mode="r")[::stride, ::stride]
    xs = np.asarray(xs, dtype=np.float32)
    ys = np.asarray(ys, dtype=np.float32)
    zs = np.asarray(zs, dtype=np.float32)
    finite = np.isfinite(xs) & np.isfinite(ys) & np.isfinite(zs)
    all_zero = (xs == 0) & (ys == 0) & (zs == 0)
    all_minus = (xs == -1) & (ys == -1) & (zs == -1)
    return finite & ~all_zero & ~all_minus


def stretch(grey, lo_pct=1.0, hi_pct=99.5):
    """Map a grey panel onto the full range between two percentiles of its own non zero voxels.

    A raw slice of this scroll is dark: the first panel of figure S5 came out almost black and
    unreadable, which the owner saw on 2026-09-22T06:44Z. Nothing about the geometry changes; a
    display window is chosen and the two values are returned so the caption can state them,
    because a picture whose window is not declared is a picture that can be tuned to taste.
    Voxels that are exactly zero are the parts of the slice no cube covered and are left out of
    the percentiles so that a missing cube cannot darken the rest.
    """
    import numpy as np
    v = grey[grey > 0]
    if v.size == 0:
        return grey, 0, 0
    lo = float(np.percentile(v, lo_pct))
    hi = float(np.percentile(v, hi_pct))
    if hi <= lo:
        return grey, lo, hi
    out = np.clip((grey.astype("float32") - lo) * (255.0 / (hi - lo)), 0, 255)
    return out.astype("uint8"), lo, hi


TITLE_FONT = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-regular.otf"


def grey_png(path, panels, gap=12, background=255, label_height=0, titles=None, title_px=None):
    """Write several uint8 panels side by side into one greyscale or colour PNG.

    Panels are numpy arrays, either two dimensional uint8 or three dimensional uint8 with three
    channels; they are padded to the tallest and laid out left to right with a gap. Nothing is
    rescaled: the caller has already decided the sampling, and an image that silently resamples
    is an image whose scale bar lies.
    """
    import numpy as np
    from PIL import Image
    panels = [p if p.ndim == 3 else np.stack([p] * 3, axis=-1) for p in panels]
    # Every panel gets a box of the SAME height and is centred in it, so three slices of
    # different depth do not come out as a ragged row. Nothing is resampled: a short panel is
    # padded, never stretched, because an image that silently resamples is an image whose
    # scale bar lies.
    # title_px, added 2026-09-30: the panel titles in the serif of figstyle.py at a pixel size the
    # caller computes from the width the figure is printed at, so that they print at about 8 pt like
    # the text of the vector figures; each title is wrapped to its own panel. Without it the titles
    # are PIL's bitmap font in an 18 pixel strip, as before.
    font, lines_of = None, None
    if titles and title_px:
        from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
        font = _F.truetype(TITLE_FONT, int(title_px))
        _m = _D.Draw(_I.new("RGB", (1, 1)))
        def lines_of(t, width):
            out, cur = [], ""
            for word in t.split(" "):
                trial = (cur + " " + word) if cur else word
                if cur and _m.textlength(trial, font=font) > width:
                    out.append(cur)
                    cur = word
                else:
                    cur = trial
            return out + ([cur] if cur else [])
        wrapped = [lines_of(t or "", p.shape[1]) for t, p in zip(titles, panels)]
        strip = int(max(len(w) for w in wrapped) * title_px * 1.25 + title_px * 0.8)
    else:
        strip = 18 if titles else 0
    body = max(p.shape[0] for p in panels)
    h = body + label_height + strip
    w = sum(p.shape[1] for p in panels) + gap * (len(panels) - 1)
    canvas = np.full((h, w, 3), background, dtype=np.uint8)
    x = 0
    boxes = []
    for p in panels:
        top = (body - p.shape[0]) // 2
        canvas[top:top + p.shape[0], x:x + p.shape[1]] = p
        boxes.append((x, top, p.shape[1], p.shape[0]))
        x += p.shape[1] + gap
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.fromarray(canvas)
    if titles:
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        for k, ((bx, _, bw, _), t) in enumerate(zip(boxes, titles)):
            if not t:
                continue
            if font is None:
                tw = d.textlength(t)
                d.text((bx + max(0, (bw - tw) / 2), body + label_height + 4), t, fill=(0, 0, 0))
                continue
            for n, line in enumerate(wrapped[k]):
                tw = d.textlength(line, font=font)
                d.text((bx + max(0, (bw - tw) / 2), body + label_height + int(title_px * (0.4 + 1.25 * n))),
                       line, fill=(0, 0, 0), font=font)
    img.save(path)
    return boxes


# ------------------------------------------------------------------------------------------
# The wide form, and why the plotted tables are written in it.
#
# A figure of this work is drawn by pgfplotstable reading the CSV that the figure's data script
# wrote. pgfplotstable parses every cell of a column an \addplot names, and its read time row
# filter does not see column values, so a long table with one row per series cannot be split
# inside the figure source: the rows of the other series are parsed too and the words "not
# measurable" stop the run. That was measured, not assumed: the first render of figure S2 failed
# on exactly that cell.
#
# So a plotted table has one row per position on the abscissa and one column per series. A
# series with no value at a position carries nan, which pgfplots discards with its default
# unbounded coords setting, and never a zero. The words the study used are kept in a text column
# beside the number, so "not measurable" is still in the file where a reader looks, and only the
# column the figure plots is numeric.
# ------------------------------------------------------------------------------------------

NAN = "nan"


def num_or_nan(value, fmt="%s"):
    """The number, or nan when the study wrote something that is not one.

    nan is not zero and does not pretend to be: pgfplots drops the coordinate, so the panel has
    a gap exactly where the measurement has one. The word the study used belongs in the text
    column beside this one, which is why every caller passes both.
    """
    v = number(value) if isinstance(value, str) else value
    if v is None:
        return NAN
    return fmt % v


def wide_rows(n):
    """n empty rows, ready to be filled column by column by each panel of a figure."""
    return [{"i": k} for k in range(n)]


def resolve(here, runs, relpath):
    """Where a study file is read from, and a warning when the two copies differ.

    A work of this laboratory ships the CSVs its numbers come from under evidence/studies/, one
    folder per closed study, with the study's own evidence/ level dropped. The live study tree
    is under the --runs argument. This function prefers the LIVE tree, because a study that is
    still running writes rows after its copy was taken and a frozen snapshot would draw a figure
    of yesterday without saying so; the shipped copy is the fallback for a study the live tree no
    longer has.

    When both exist and their bytes differ, the caller is told. A copy that has drifted from its
    original is the failure that cost this laboratory three points of a scatter on 2026-09-22,
    and a figure that reads one while the article reads the other is the same failure with a
    longer fuse.

    relpath is always written the way the study names it, <study>/evidence/<file>, because that
    is the form the specification and every caption use. Returns (path, how, warning or None).
    """
    import hashlib

    parts = relpath.split("/")
    shipped = None
    if len(parts) >= 3 and parts[1] == "evidence":
        shipped = os.path.join(here, "evidence", "studies", parts[0], *parts[2:])
    live = os.path.join(runs, relpath)

    def digest(p):
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    warning = None
    if os.path.exists(live):
        if shipped and os.path.exists(shipped) and digest(live) != digest(shipped):
            warning = (relpath + ": the copy shipped under evidence/studies differs from the "
                       "live study. The figure read the live one; the article must be rebuilt "
                       "from the same bytes or the two will state different numbers")
        return live, "read from the live study tree under " + runs, warning
    if shipped and os.path.exists(shipped):
        return shipped, "shipped with this work under evidence/studies", warning
    return live, "not on disk in either tree", warning


class Studies:
    """Every study file a figure reads, resolved once and accounted for.

    A figure script makes one of these and asks it for each file by the name the study gives it,
    <study>/evidence/<file>. The object remembers which tree each one came from and every
    disagreement it found between the shipped copy and the live study, and hands both back for
    the comment of the plotted table. A figure that read a stale copy then says so in the file
    a reader opens, instead of being a picture nobody can date.
    """

    def __init__(self, here, runs):
        self.here = here
        self.runs = runs
        self.used = {}
        self.warnings = []

    def path(self, relpath):
        p, how, warning = resolve(self.here, self.runs, relpath)
        self.used[relpath] = how
        if warning and warning not in self.warnings:
            self.warnings.append(warning)
        return p

    def report(self):
        """One sentence for the comment of the plotted table."""
        trees = sorted(set(self.used.values()))
        out = "Files read: " + "; ".join(f"{k} ({v})" for k, v in sorted(self.used.items()))
        if len(trees) > 1:
            out += ". More than one tree was read and each file says which."
        if self.warnings:
            out += " Copies that disagree with the live study: " + "; ".join(self.warnings) + "."
        return out


def largest_delivered_sheet(folder, prefer_point=None, pattern="squares-*.csv"):
    """The largest fully covered square over EVERY delivered arm of one study, with its ties.

    Why this exists rather than an arm named in an argument. A figure that draws "the largest
    delivered sheet of the scroll" makes a superlative claim, and a superlative is recomputed
    over every row the word covers, never taken from a sentence. So this reads every arm file of
    the study, takes the maximum of column square_mm_min_step over every row whose status is
    measured, and hands back the ties and the runner up with it. On 2026-09-22 a figure of this
    laboratory nearly went out with a larger number lifted from a prose table and attributed to a
    CSV that does not contain it; this function is what makes that impossible here.

    The unit trap, which cost two readers in ten minutes on the same table. A study of this home
    may carry the same quantity at two voxels in adjacent columns, such as
    largest_square_mm_at_9_0 beside largest_square_mm_at_9_362, and nothing in a row says which
    one a reader wants. This function reads one column, square_mm_min_step, whose file header
    states its voxel, and it returns that column's name so every caller writes it beside the
    number.

    The tie break is declared here and not left to the filesystem: among the arms that reach the
    maximum, the one whose point equals prefer_point, and otherwise the first in file name order.

    Returns a dict: row, csv_path, point, value, column, ties, runner_up, arms, sheets.
    """
    import glob

    rows = []
    for path in sorted(glob.glob(os.path.join(folder, pattern))):
        _, _, rs = read_study_csv(path)
        for r in rs:
            if r.get("status") != "measured":
                continue
            v = number(r.get("square_mm_min_step"))
            if v is None:
                continue
            rows.append((v, r, path))
    if not rows:
        raise SystemExit(f"{folder}: no measured sheet in any {pattern}")

    top = max(v for v, _, _ in rows)
    at_top = [(v, r, p) for v, r, p in rows if v == top]
    chosen = None
    if prefer_point:
        for v, r, p in at_top:
            if r.get("point") == prefer_point:
                chosen = (v, r, p)
                break
    if chosen is None:
        chosen = sorted(at_top, key=lambda t: t[2])[0]

    below = sorted({v for v, _, _ in rows if v < top}, reverse=True)
    return {
        "row": chosen[1],
        "csv_path": chosen[2],
        "point": chosen[1].get("point"),
        "value": top,
        "column": "square_mm_min_step",
        "ties": sorted({r.get("point") for v, r, _ in at_top}),
        "runner_up": (below[0] if below else None),
        "arms": len({r.get("point") for _, r, _ in rows}),
        "sheets": len(rows),
    }


# ------------------------------------------------------------------------------------------
# A missing key is not a zero. Added 2026-09-22 on the coordinator's rule of 01:5xZ, after the
# fifth stated cause of the night turned out not to have been reproduced.
#
# What happened: a reader of cube-stages.csv wrote named.get("RESIDUE", 0) against a table whose
# key is "RESIDUE inferred by subtraction, total minus the stage lines minus dump". The lookup
# missed and handed back its default, and a default of 0 is indistinguishable from a measurement
# of zero. This home already refuses a zero where a CSV cell says nothing; the rule is the same
# for the lookup, and the way to keep it in a tool is to let the lookup raise. A default is a
# measurement nobody wrote.
#
# Where an absence is legitimate, the caller tests membership and records it. Where a value must
# be there for the figure to mean anything, the caller uses these and the script stops with the
# reason rather than drawing something plausible.
# ------------------------------------------------------------------------------------------

def required_number(row, column, what):
    """The number in a column that must be there, or a stop naming what was being drawn.

    Used for the geometry a raster draws: a square's side and its corner. A side of zero is a
    sheet with no square, which is a real and different thing from a side the file does not
    carry, and a figure that silently draws the first when the second is true is the failure
    this function exists to prevent.
    """
    if column not in row:
        raise SystemExit(
            f"{what}: the row has no column {column}. Columns present: "
            + "; ".join(sorted(row)) + ". Refusing to draw rather than assume a value.")
    value = number(row[column])
    if value is None:
        raise SystemExit(
            f"{what}: column {column} reads {row[column]!r}, which is not a number. Refusing "
            f"to draw rather than treat it as zero.")
    return value


def required(mapping, key, what):
    """The value at a key that must be there, or a stop naming the keys that are.

    The message prints the keys because the failure it is written for is a key that nearly
    matches: a long stage name looked up by its first word.
    """
    if key not in mapping:
        keys = sorted(str(k) for k in mapping)
        raise SystemExit(
            f"{what}: no entry for {key!r}. Entries present: " + "; ".join(keys[:20])
            + (" and more" if len(keys) > 20 else "")
            + ". Refusing to continue rather than take a default.")
    return mapping[key]

def scale_bars(path, bars, font_px, corner="lower left", fg=(255, 255, 255), bg=(0, 0, 0)):
    """Draw one scale bar per panel into a PNG already written: bars is [(box, mm_per_px, length_mm)].

    Added 2026-09-30 (the referee's figure notes on the lean S): the length in pixels is the length
    in millimetres over the panel's own millimetres per pixel, which the caller reads from the same
    manifest or table it writes into the plotted table, and never a typed number of pixels. The bar
    and its label sit on a small backing box so that they read on papyrus and on air alike, in the
    series serif at font_px.
    """
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(TITLE_FONT, int(font_px))
    out = []
    for (x, y, w, h), mmpp, length in bars:
        n = int(round(length / mmpp))
        t = max(4, int(font_px) // 4)
        pad = int(font_px) // 2
        label = ("%g mm" % length)
        tw = d.textlength(label, font=f)
        bw, bh = max(n, tw) + 2 * pad, int(font_px) + t + 3 * pad
        if corner == "upper left":
            x0, y0 = x + pad, y + pad
        else:
            x0, y0 = x + pad, y + h - pad - bh
        d.rectangle((x0, y0, x0 + bw, y0 + bh), fill=bg)
        d.text((x0 + pad, y0 + pad + int(font_px)), label, fill=fg, font=f, anchor="ls")
        yb = y0 + bh - pad - t
        d.rectangle((x0 + pad, yb, x0 + pad + n, yb + t), fill=fg)
        out.append((n, length))
    im.save(path)
    return out
