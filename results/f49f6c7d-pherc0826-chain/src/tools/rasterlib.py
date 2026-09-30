#!/usr/bin/env python3
"""What the raster figures c-f10 and up share: reading the raw scan of PHerc. 0826 by chunks, cutting a
sheet by a plane, and drawing on a grey panel.

Why it is a file of its own and not part of figlib.py. figlib.py belongs to the text of the work and its
figures C1 and C2 read only CSV rows. The raster figures read volume data and sheet files, and the few
pieces they have in common are written once here so that two figures cannot cut the same sheet in two
different ways.

THE RULE, NO INK. PHerc. 0826 is a competition scroll. Nothing in this file renders the scan along a
sheet surface: the only grey these helpers read is a plane of the scan (an axial slice at one z), and a
sheet is only ever drawn as its geometry, the line where it crosses that plane or its coverage mask in
its own grid. There is no function here that samples the volume at a sheet's points, on purpose.

Where the grey comes from. The raw masked scan on the open data bucket (compressor null, 128 cubed uint8
chunks, C order), read chunk by chunk through the home's shared chunk cache
/data/scrollagent/tools/raw_chunk_cache.py, so a chunk fetched once is never fetched again. That cache
was written for PHerc. 1447 and 0139 and has no entry for PHerc. 0826; this module adds one at run time
(the zarr name below, no VC3D directory exists for this volume) and changes nothing in that file. Before
fetching, a chunk is also looked up in chain-0826's own flat cache of seed chunks (read only; its bytes
are the bucket object's bytes, and a hit is stored into the shared cache by hard copy).
"""
import concurrent.futures as cf
import os
import shutil
import sys
import urllib.request

import numpy as np

sys.path.insert(0, "/data/scrollagent/tools")
sys.path.insert(0, "/data/scrollagent/pipeline/datasets")
import raw_chunk_cache as RCC  # noqa: E402

SCROLL = "PHerc0826"
ZARR = "20250821151701-9.362um-1.2m-113keV-masked.zarr"
BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
RAW_URL = BUCKET + "/PHerc0826/volumes/" + ZARR
FLAT = "/data/scrollagent/runs/rev1/chain-0826/scratch/raw-chunks-20250821151701"
MANIFEST = "/data/scrollagent/pipeline/datasets/manifests/PHerc0826.json"
# The series serif (results/figstyle.py: TeX Gyre Termes, the Times of the vector figures), owner's order of 2026-09-30.
FONT = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-regular.otf"
FONT_BOLD = FONT          # one weight, as in the vector figures
# Text size at print (owner's order of 2026-09-30: 7 to 9 pt): a tool that knows its canvas width in pixels and the width
# the article prints it at calls print_size() once; every label, key and scale bar label is then drawn at TEXT_PT.
TEXT_PT = 8.0
TEXT_PX = None


def print_size(canvas_px, print_bp, pt=TEXT_PT):
    """Set the text size so that it prints at pt points when a canvas canvas_px wide prints print_bp big points wide."""
    global TEXT_PX
    TEXT_PX = int(round(pt * canvas_px / float(print_bp)))
    return TEXT_PX


TEXTWIDTH_BP = 516.0 * 72 / 72.27      # IEEEtran 10pt journal: \textwidth 516pt, \columnwidth 252pt
COLUMNWIDTH_BP = 252.0 * 72 / 72.27

RCC.VOLUMES.setdefault(SCROLL, (ZARR, None))


def zarray(level):
    """The .zarray of one level, fetched (a few hundred bytes) so shape and chunks are read, not typed."""
    import json
    with urllib.request.urlopen("%s/%d/.zarray" % (RAW_URL, level), timeout=60) as r:
        meta = json.loads(r.read())
    if meta.get("compressor") is not None or meta.get("dtype") != "|u1" or meta.get("order") != "C":
        raise SystemExit("raw level %d is not uncompressed uint8 C order: %s" % (level, meta))
    return meta


def level_scale(level):
    """The (z, y, x) scale of one level against level 0, read from the zarr's own .zattrs multiscales."""
    import json
    with urllib.request.urlopen(RAW_URL + "/.zattrs", timeout=60) as r:
        attrs = json.loads(r.read())
    for d in attrs["multiscales"][0]["datasets"]:
        if d["path"] == str(level):
            for t in d["coordinateTransformations"]:
                if t["type"] == "scale":
                    return [float(v) for v in t["scale"]]
    raise SystemExit("no scale for level %d in %s/.zattrs" % (level, RAW_URL))


class RawReader:
    """Axial planes of the raw scan at one level, chunk by chunk, every chunk through the shared cache."""

    def __init__(self, level, threads=4):
        self.level = level
        self.meta = zarray(level)
        self.shape = self.meta["shape"]
        self.C = self.meta["chunks"][0]
        if self.meta["chunks"] != [self.C] * 3:
            raise SystemExit("raw level %d chunks are not cubes: %s" % (level, self.meta["chunks"]))
        self.threads = threads
        self.counts = {"shared cache": 0, "chain-0826 flat cache": 0, "fetched": 0, "absent": 0}

    def chunk(self, cz, cy, cx):
        hit = RCC.lookup(SCROLL, ZARR, self.level, cz, cy, cx)
        if hit and hit[0] == "absent":
            self.counts["absent"] += 1
            return None
        if hit:
            self.counts["shared cache"] += 1
            return hit[1]
        if self.level == 0:
            flat = os.path.join(FLAT, "%d_%d_%d.bin" % (cz, cy, cx))
            if os.path.isfile(flat) and os.path.getsize(flat) == self.C ** 3:
                with open(flat, "rb") as fh:
                    data = fh.read()
                self.counts["chain-0826 flat cache"] += 1
                return RCC.store(SCROLL, ZARR, self.level, cz, cy, cx, data)
        url = "%s/%d/%d/%d/%d" % (RAW_URL, self.level, cz, cy, cx)
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                data = r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                RCC.store_absent(SCROLL, ZARR, self.level, cz, cy, cx)
                self.counts["absent"] += 1
                return None
            raise
        if len(data) != self.C ** 3:
            raise SystemExit("%s: %d bytes, expected %d" % (url, len(data), self.C ** 3))
        self.counts["fetched"] += 1
        return RCC.store(SCROLL, ZARR, self.level, cz, cy, cx, data)

    def plane(self, z, y0, y1, x0, x1):
        """uint8 plane z of the level, rows y0:y1 and columns x0:x1; a chunk the bucket lacks is zero."""
        C = self.C
        out = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        cz, kz = divmod(z, C)
        jobs = [(cy, cx) for cy in range(y0 // C, (y1 - 1) // C + 1) for cx in range(x0 // C, (x1 - 1) // C + 1)]
        with cf.ThreadPoolExecutor(self.threads) as ex:
            paths = list(ex.map(lambda t: self.chunk(cz, t[0], t[1]), jobs))
        for (cy, cx), p in zip(jobs, paths):
            if p is None:
                continue
            with open(p, "rb") as fh:
                fh.seek(kz * C * C)
                page = np.frombuffer(fh.read(C * C), dtype=np.uint8).reshape(C, C)
            ys, xs = max(y0, cy * C), max(x0, cx * C)
            ye, xe = min(y1, (cy + 1) * C), min(x1, (cx + 1) * C)
            out[ys - y0:ye - y0, xs - x0:xe - x0] = page[ys - cy * C:ye - cy * C, xs - cx * C:xe - cx * C]
        return out, len(jobs)


def pred_plane(z, y0, y1, x0, x1):
    """The m7 surface prediction (local zarr the manifest names) on the same plane; returns (plane, path, model)."""
    import json
    import zarr
    m = json.load(open(MANIFEST))
    arr = zarr.open(m["local"]["path"], mode="r")
    return np.asarray(arr[z, y0:y1, x0:x1], dtype=np.uint8), m["local"]["path"], m["model"], m["source"]


def voxel():
    import voxel as V
    return V.voxel_um(SCROLL)


def plane_crossings(mask, px, py, pz, z):
    """Where the sheet's lattice crosses the plane at height z, as arrays (y, x, i, j) in voxels.

    Along every edge between two covered neighbouring cells of the sheet's grid (step one in i or in
    j), where the two cells' pz lie on the two sides of z or one is on it, the crossing point is the
    linear interpolation of the two cells' positions. The sheet's cells are about four voxels apart,
    so the cells that happen to lie within half a voxel of the plane draw a dotted line; the edge
    crossings draw the line itself. i and j are the grid cell the crossing starts from, so a caller
    can tell which crossings belong to a region of the grid, such as a square.
    """
    ys, xs, iis, jjs = [], [], [], []
    for di, dj in ((1, 0), (0, 1)):
        a = mask[:mask.shape[0] - di, :mask.shape[1] - dj] & mask[di:, dj:]
        za = pz[:pz.shape[0] - di, :pz.shape[1] - dj].astype(np.float64) - z
        zb = pz[di:, dj:].astype(np.float64) - z
        hit = a & (za * zb <= 0) & ~((za == 0) & (zb == 0))
        ii, jj = np.nonzero(hit)
        fa, fb = za[ii, jj], zb[ii, jj]
        t = fa / (fa - fb)
        for plane, out in ((py, ys), (px, xs)):
            pa = plane[ii, jj].astype(np.float64)
            pb = plane[ii + di, jj + dj].astype(np.float64)
            out.append(pa + t * (pb - pa))
        iis.append(ii)
        jjs.append(jj)
    cat = lambda v: np.concatenate(v) if v else np.zeros(0)
    return cat(ys), cat(xs), cat(iis), cat(jjs)


def block_mean(img, f):
    """Mean over f by f blocks, the display sampling a caller declares; f 1 returns the image."""
    if f == 1:
        return img
    h, w = (img.shape[0] // f) * f, (img.shape[1] // f) * f
    v = img[:h, :w].astype(np.float32).reshape(h // f, f, w // f, f).mean(axis=(1, 3))
    return np.rint(v).astype(np.uint8)


def rgb(grey):
    return np.stack([grey] * 3, axis=-1).copy()


def dots(img, y, x, colour, r=1):
    """Paint square dots of half side r at display coordinates (y, x), rounded; returns how many landed."""
    yy = np.rint(y).astype(np.int64)
    xx = np.rint(x).astype(np.int64)
    keep = (yy >= 0) & (yy < img.shape[0]) & (xx >= 0) & (xx < img.shape[1])
    yy, xx = yy[keep], xx[keep]
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            a = np.clip(yy + dy, 0, img.shape[0] - 1)
            b = np.clip(xx + dx, 0, img.shape[1] - 1)
            img[a, b] = colour
    return int(keep.sum())


def tint(img, where, colour, alpha):
    """Blend a colour into the pixels where a mask is true."""
    c = np.array(colour, dtype=np.float32)
    v = img[where].astype(np.float32)
    img[where] = np.rint((1 - alpha) * v + alpha * c).astype(np.uint8)
    return img


def outline(img, i0, j0, side, colour, width=2):
    """A square outline, top left (i0, j0) and side in pixels, clipped to the image."""
    h, w = img.shape[:2]
    for k in range(width):
        a0, b0 = i0 + k, j0 + k
        a1, b1 = i0 + side - 1 - k, j0 + side - 1 - k
        ra, rb = max(a0, 0), min(a1, h - 1)
        ca, cb = max(b0, 0), min(b1, w - 1)
        for r in (a0, a1):
            if 0 <= r < h:
                img[r, ca:cb + 1] = colour
        for c in (b0, b1):
            if 0 <= c < w:
                img[ra:rb + 1, c] = colour
    return img


def font(size, bold=False):
    from PIL import ImageFont
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def scale_bar(img, mm, mm_per_px, label, where="bottom-left", margin=24, height=8, colour=(255, 255, 255),
              size=26, box=(0, 0, 0)):
    """Draw a bar of mm millimetres and its label on a uint8 RGB array; returns (image, bar length px)."""
    from PIL import Image, ImageDraw
    n = int(round(mm / mm_per_px))
    pil = Image.fromarray(img)
    d = ImageDraw.Draw(pil)
    size = TEXT_PX or size
    height = max(height, size // 4) if TEXT_PX else height
    f = font(size, bold=True)
    h, w = img.shape[:2]
    x0 = margin if where.endswith("left") else w - margin - n
    y0 = h - margin - height
    tw = d.textlength(label, font=f)
    tx = max(x0 + (n - tw) / 2, 4)           # a label wider than a short bar starts at the panel's edge, not outside it
    if box is not None:
        d.rectangle([min(x0, tx) - 4, y0 - size - 12, max(x0 + n, tx + tw) + 4, y0 + height + 4], fill=box)
    d.rectangle([x0, y0, x0 + n, y0 + height], fill=colour)
    d.text((tx, y0 - size - 8), label, fill=colour, font=f)
    return np.asarray(pil).copy(), n


def label(img, text, xy=(14, 10), size=34, colour=(255, 255, 255), box=(0, 0, 0)):
    """A panel letter or a short word in a corner of the panel, on a dark box so it reads on any grey."""
    from PIL import Image, ImageDraw
    pil = Image.fromarray(img)
    d = ImageDraw.Draw(pil)
    size = TEXT_PX or size
    f = font(size, bold=True)
    l, t, r, b = d.textbbox(xy, text, font=f)
    if box is not None:
        d.rectangle([l - 6, t - 6, r + 6, b + 6], fill=box)
    d.text(xy, text, fill=colour, font=f)
    return np.asarray(pil).copy()


def legend(img, items, xy=(14, 60), size=22, box=(0, 0, 0), text=(255, 255, 255)):
    """A key: a list of (colour, text) drawn as swatches with words, top left of the panel."""
    from PIL import Image, ImageDraw
    pil = Image.fromarray(img)
    d = ImageDraw.Draw(pil)
    size = TEXT_PX or size
    f = font(size)
    x, y = xy
    if TEXT_PX and y >= 40:                   # a key under a panel label: keep it clear of the label at print size
        y = max(y, 10 + int(1.5 * TEXT_PX) + 14)
    wmax = max(d.textlength(t, font=f) for _, t in items)
    step = size + 10
    if box is not None:
        d.rectangle([x - 8, y - 8, x + size + 12 + wmax + 8, y + step * len(items) - 2], fill=box)
    for k, (c, t) in enumerate(items):
        yy = y + k * step
        d.rectangle([x, yy + 3, x + size - 4, yy + size - 1], fill=tuple(c))
        d.text((x + size + 8, yy), t, fill=text, font=f)
    return np.asarray(pil).copy()


def side_by_side(panels, gap=16, background=255):
    """Panels of equal height laid out left to right; nothing is resampled."""
    h = max(p.shape[0] for p in panels)
    w = sum(p.shape[1] for p in panels) + gap * (len(panels) - 1)
    canvas = np.full((h, w, 3), background, dtype=np.uint8)
    x, boxes = 0, []
    for p in panels:
        top = (h - p.shape[0]) // 2
        canvas[top:top + p.shape[0], x:x + p.shape[1]] = p
        boxes.append((x, top, p.shape[1], p.shape[0]))
        x += p.shape[1] + gap
    return canvas, boxes


def save_png(path, img):
    from PIL import Image
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part.png"
    Image.fromarray(img).save(tmp, optimize=True)
    os.replace(tmp, path)
    return path


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def plane_sha(arr):
    """sha256 of the bytes of an array, so the plotted table pins the grey a raster rests on."""
    import hashlib
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()


def stacked(panels, gap=16, background=255):
    """Panels laid out top to bottom, left aligned; nothing is resampled. Boxes are x;y;w;h."""
    w = max(p.shape[1] for p in panels)
    h = sum(p.shape[0] for p in panels) + gap * (len(panels) - 1)
    canvas = np.full((h, w, 3), background, dtype=np.uint8)
    y, boxes = 0, []
    for p in panels:
        canvas[y:y + p.shape[0], :p.shape[1]] = p
        boxes.append((0, y, p.shape[1], p.shape[0]))
        y += p.shape[0] + gap
    return canvas, boxes
