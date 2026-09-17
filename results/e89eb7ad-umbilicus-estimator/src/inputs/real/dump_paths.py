# This file is a copy of the same script in the working tree and differs from it in one way only:
# the absolute paths of the machine the measurements ran on are replaced by paths inside
# this folder, resolved from the file's own location. Nothing else is changed.
"""Dump the paths of a published .grid into a flat file the C++ driver can read.

Keeps villa's own source untouched: the driver builds a GridStore from these paths and calls
the real align_and_extract_umbilicus. Format: int32 bounds_w, bounds_h, num_paths, then per
path int32 n followed by n pairs of int32 x, y.
"""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gridstore import read_grid

src, dst = sys.argv[1], sys.argv[2]
h, paths, _ = read_grid(src)
with open(dst, "wb") as fh:
    fh.write(struct.pack("<3i", h["bounds"][2], h["bounds"][3], len(paths)))
    for p in paths:
        fh.write(struct.pack("<i", len(p)))
        for x, y in p:
            fh.write(struct.pack("<2i", int(x), int(y)))
print(f"{dst}: bounds {h['bounds'][2]}x{h['bounds'][3]}, {len(paths)} paths, "
      f"{sum(len(p) for p in paths)} points")
