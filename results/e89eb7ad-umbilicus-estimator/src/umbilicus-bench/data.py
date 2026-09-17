"""Open data: the scrolls that have a published umbilicus, their surface predictions, and a slice cache.

Everything here reads the Vesuvius Challenge open-data bucket over plain HTTP. Slices are cached on
disk under cache/, so a bench run costs the network once.
"""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import numcodecs
import numpy as np

BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com/"
CACHE = Path(__file__).resolve().parent / "cache"
VOXEL_UM = 9.362                      # level 0 voxel size of these scans, in micrometres
MM_PER_VOXEL = VOXEL_UM / 1000.0

# The scrolls with an umbilicus published by the organizers and a surface prediction of the same
# family: the three competition scrolls first, then PHerc0332. They are the ground truth this bench
# scores against, and the bench is only as good as they are.
SCROLLS = {
    "PHerc0125": {
        "prediction": "PHerc0125/representations/predictions/surfaces/"
                      "20250821151825-surface-20260413222639-surface-m7-L0-th0.2.zarr/",
        "umbilicus": "PHerc0125/representations/umbilicus/20250821151825-umbilicus-20260808111524.json",
        "field_px": 8387,
    },
    "PHerc0211": {
        "prediction": "PHerc0211/representations/predictions/surfaces/"
                      "20250821151803-surface-20260413222639-surface-m7-L0-th0.2.zarr/",
        "umbilicus": "PHerc0211/representations/umbilicus/20250821151803-umbilicus-20260808112626.json",
        "field_px": 7948,
    },
    "PHerc0826": {
        "prediction": "PHerc0826/representations/predictions/surfaces/"
                      "20250821151701-surface-20260413222639-surface-m7-L0-th0.2.zarr/",
        "umbilicus": "PHerc0826/representations/umbilicus/20250821151701-umbilicus-20260808113303.json",
        "field_px": 8169,
    },
    # The fourth one is the interesting one. PHerc0332 was scanned once, at 2.399 um, and the only
    # surface prediction published for it is an L2 store: its own level 0 is already four times
    # coarser than the frame the umbilicus is annotated in. `store_scale` is that factor, and it is
    # exactly why a hardcoded 2 ** level is not enough: here it would be wrong by four.
    "PHerc0332": {
        "prediction": "PHerc0332/representations/predictions/surfaces/"
                      "20251211183505-surface-20260413222639-surface-m7-L2-th0.2.zarr/",
        "umbilicus": "PHerc0332/representations/umbilicus/20251211183505-umbilicus-20260828110920.json",
        "field_px": 15764, "voxel_um": 2.399, "store_scale": 4,
    },
}

# PHerc0139 also has a published umbilicus and is not here: it is annotated on the 2.399 um scan
# while its surface prediction lives on the 9.362 um one, and the transform between two different
# scans of the same scroll is not published anywhere (the catalog's volume_transforms is null and
# transform.json is a 404), nor is it rigid. Scoring against a registration we invented ourselves
# would put our own error into the metric, so that scroll stays out until the transform exists.

# Scrolls with no published umbilicus, which are the ones an estimator exists for. There is no
# ground truth here: two estimators disagreeing is a discrepancy, not an error, and this bench
# cannot say which is right. They are listed so that a rule validated on the three above can be run
# on the scrolls that matter, and the shift reported honestly.
UNKNOWN = {
    "PHerc1203": {"prediction": "PHerc1203/representations/predictions/surfaces/"
                                "20250820131727-surface-20260413222639-surface-m7-L0-th0.2.zarr/",
                  "field_px": 6844},
    "PHerc1545": {"prediction": "PHerc1545/representations/predictions/surfaces/"
                                "20250821151648-surface-20260413222639-surface-m7-L0-th0.2.zarr/",
                  "field_px": 7506},
    "PHerc0268": {"prediction": "PHerc0268/representations/predictions/surfaces/"
                                "20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr/",
                  "field_px": 12145, "voxel_um": 8.640},
}
SCROLLS.update(UNKNOWN)

# The scrolls the bench can actually score: the ones with a published umbilicus.
GROUND_TRUTH = [s for s, v in SCROLLS.items() if "umbilicus" in v]


def _get(url, timeout=60, attempts=5):
    """One object from the bucket, retried on a transient failure.

    A cold run makes a few thousand requests over the better part of an hour, so a connection reset
    somewhere in the middle is not unlikely: it happened on the first cold run we timed, after 26
    minutes. Without a retry that ends the run and the reader starts again. A 404 is not transient
    and is raised immediately, because read_slice reads it as a chunk that is empty by design.
    """
    for i in range(attempts):
        try:
            return urllib.request.urlopen(url, timeout=timeout).read()
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, OSError):
            if i == attempts - 1:
                raise
            time.sleep(2 ** i)


# The chunks of one z plane, kept while that plane is being read. The slice grid is ascending and a
# chunk is 192 voxels tall, so without this every chunk is downloaded once per slice that falls in
# it: about four times each, which was 1.1 GB of transfer for the 265 MB the run actually needs.
_plane = {"key": None, "chunks": {}}


def _chunk(base, iz, iy, ix, key):
    if _plane["key"] != key:
        _plane["key"], _plane["chunks"] = key, {}
    got = _plane["chunks"]
    if (iy, ix) not in got:
        try:
            got[(iy, ix)] = _get(base + f"{iz}/{iy}/{ix}")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            got[(iy, ix)] = None          # a chunk that 404s is empty by design
    return got[(iy, ix)]


def scale_to_reference(scroll, level):
    """Voxels of the reference frame per pixel of this store at this level."""
    return 2 ** level * SCROLLS[scroll].get("store_scale", 1)


def mm_per_voxel(scroll):
    """Millimetres per voxel of the frame this scroll's umbilicus is annotated in."""
    return SCROLLS[scroll].get("voxel_um", VOXEL_UM) / 1000.0


class MissingData(Exception):
    """An input the bench needs is not there. Raised before anything is written."""


def zarray(scroll, level):
    """The store metadata, cached next to the slices.

    It is cached because otherwise a run with a full slice cache still needs the network, and the
    bench would be neither reproducible offline nor stable against the store being moved.
    """
    p = CACHE / scroll / f"level{level}" / ".zarray"
    if p.exists():
        return json.loads(p.read_text())
    url = BUCKET + SCROLLS[scroll]["prediction"] + f"{level}/.zarray"
    meta = json.loads(_get(url).decode())
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta))
    return meta


def read_slice(scroll, level, z):
    """One xy slice of the surface prediction at a pyramid level, assembled chunk by chunk.

    A chunk that 404s is empty by design and stays zero; any other failure is raised, because a
    silent hole moves the estimate without saying so.
    """
    base = BUCKET + SCROLLS[scroll]["prediction"] + f"{level}/"
    meta = zarray(scroll, level)
    shape, chunks = meta["shape"], meta["chunks"]
    codec = numcodecs.get_codec(meta["compressor"]) if meta["compressor"] else None
    cz, cy, cx = chunks
    iz = z // cz
    out = np.zeros((shape[1], shape[2]), np.uint8)
    for iy in range((shape[1] + cy - 1) // cy):
        for ix in range((shape[2] + cx - 1) // cx):
            buf = _chunk(base, iz, iy, ix, (scroll, level, iz))
            if buf is None:
                continue
            arr = np.frombuffer(codec.decode(buf) if codec else buf,
                                np.dtype(meta["dtype"])).reshape(chunks)
            y1, x1 = min(shape[1], (iy + 1) * cy), min(shape[2], (ix + 1) * cx)
            out[iy * cy:y1, ix * cx:x1] = arr[z % cz, :y1 - iy * cy, :x1 - ix * cx]
    return out


def slice_heights(scroll, level, n):
    """The heights the estimator under test is scored on: the same rule the estimators use."""
    Z = zarray(scroll, level)["shape"][0]
    return [int(f * Z) for f in np.linspace(0.08, 0.92, n)]


def cached_slice(scroll, level, z):
    p = CACHE / scroll / f"level{level}" / f"z{z}.npy"
    if p.exists():
        return np.load(p)
    sl = read_slice(scroll, level, z)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, sl)
    return sl


REFERENCE = Path(__file__).resolve().parent / "reference"


def published_umbilicus(scroll):
    """The published control points, sorted by z, in level 0 voxels.

    Read from reference/ when it is there, which is the copy this repository was measured against,
    so a run reproduces without a network round trip. Downloaded otherwise.
    """
    p = REFERENCE / f"{scroll}-umbilicus.json"
    if not p.exists():
        p = CACHE / scroll / "umbilicus.json"
    if p.exists():
        d = json.loads(p.read_text())
    else:
        d = json.loads(_get(BUCKET + SCROLLS[scroll]["umbilicus"]).decode())
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d))
    pts = d["control_points"] if isinstance(d, dict) else d
    a = np.array([[q["x"], q["y"], q["z"]] for q in pts if not q.get("rejected")], float)
    return a[np.argsort(a[:, 2])]
