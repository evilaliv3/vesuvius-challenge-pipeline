# This file is a frozen copy of the slice reader of the metamorphic battery of 2026-09-16, the
# run this folder's synthetic tables come from. It differs from the copy that produced them in
# one way only: the absolute path of that run is replaced by this folder, resolved from the
# file's own location. Nothing else is changed.
"""Where the slices come from, in one place, so no two tables read two different inputs.

Two sources, both already on disk:

  SAVED   the four dumps in inputs/real/*.bin. These are the exact inputs the real
          C++ ran on for evidence/cpp-runs.csv, so anything measured on them is comparable with
          twenty runs of villa's own compiled function.
  GRID15  inputs/grid15/<scroll>/<zzzzzz>.grid, 24 slices per scroll, the input of
          the fifteen-scroll table.

Both are read only. The folder belongs to another agent.
"""
import os
import struct
import sys

import numpy as np

NG = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, NG)
from gridstore import read_grid, segments  # noqa: E402

# scroll, z of the slice, dump, grid_scale, voxel in um. From fifteen-config.json.
SAVED = [
    ("PHerc0125", 2140, f"{NG}/real/d-0125-2140.bin", 1, 9.362),
    ("PHerc0125", 6891, f"{NG}/real/d-0125-6891.bin", 1, 9.362),
    ("PHerc0332", 4049, f"{NG}/real/d-0332-4049.bin", 4, 2.399),
    ("PHerc0826", 8000, f"{NG}/real/d-0826-8000.bin", 1, 9.362),
]

SCALE = {"PHerc0125": (1, 9.362), "PHerc0211": (1, 9.362),
         "PHerc0332": (4, 2.399), "PHerc0826": (1, 9.362)}


def mm_per_unit(scroll):
    sc, um = SCALE[scroll]
    return sc * um / 1000.0


def read_dump(path):
    """The format driver.cpp writes: w, h, npaths, then per path n and n int32 xy pairs."""
    with open(path, "rb") as fh:
        buf = fh.read()
    w, h, npaths = struct.unpack_from("<3i", buf, 0)
    off = 12
    paths = []
    for _ in range(npaths):
        n = struct.unpack_from("<i", buf, off)[0]
        off += 4
        a = np.frombuffer(buf, dtype="<i4", count=2 * n, offset=off).reshape(n, 2)
        off += 8 * n
        paths.append([tuple(map(int, p)) for p in a])
    return float(w), float(h), paths


def saved():
    """The four bench slices as (scroll, z, mid, nrm, W, H, mm_per_unit)."""
    out = []
    for scroll, z, dump, sc, um in SAVED:
        W, H, paths = read_dump(dump)
        mid, nrm = segments(paths)
        out.append((scroll, z, mid, nrm, W, H, sc * um / 1000.0))
    return out


def grid15(scroll):
    """All 24 cached slices of a scroll as (z, mid, nrm, W, H)."""
    d = os.path.join(NG, "grid15", scroll)
    out = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".grid") or not os.path.getsize(os.path.join(d, f)):
            continue
        h, paths, _ = read_grid(os.path.join(d, f))
        mid, nrm = segments(paths)
        if len(mid) < 100:
            continue
        out.append((int(f[:-5]), mid, nrm, float(h["bounds"][2]), float(h["bounds"][3])))
    return out
