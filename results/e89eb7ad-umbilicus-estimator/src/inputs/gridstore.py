"""Read a villa GridStore `.grid` file (VCGS v1-v3) and return its paths.

Format transcribed from villa/volume-cartographer:
  core/src/GridStore.cpp:477-585   header, big-endian uint32
  core/src/GridStore.cpp:603-646   one seglist: start_x, start_y, num_offsets, then the bytes
  core/include/vc/core/util/LineSegList.hpp:41-54   the bytes are int8 delta pairs

Only reading is implemented, and only the paths region: the bucket index is a spatial
accelerator we do not need when we want every path.
"""
import json
import struct

MAGIC = 0x56434753  # "VCGS"


def read_header(buf):
    if len(buf) < 44:
        raise ValueError("too small for a VCGS header")
    f = struct.unpack_from(">11I", buf, 0)
    magic, version = f[0], f[1]
    if magic != MAGIC:
        raise ValueError(f"not a GridStore file: magic {magic:#x}")
    h = {
        "version": version,
        "bounds": (f[2], f[3], f[4], f[5]),   # x, y, width, height
        "cell_size": f[6],
        "num_buckets": f[7],
        "num_paths": f[8],
        "buckets_offset": f[9],
        "paths_offset": f[10],
    }
    if version >= 2:
        h["json_meta_offset"], h["json_meta_size"] = struct.unpack_from(">2I", buf, 44)
    else:
        h["json_meta_offset"] = h["json_meta_size"] = 0
    return h


def read_grid(path):
    """Return (header, [path, ...]) where each path is a list of (x, y) int pairs."""
    with open(path, "rb") as fh:
        buf = fh.read()
    h = read_header(buf)
    off = h["paths_offset"]
    end = h["json_meta_offset"] or len(buf)
    paths = []
    for _ in range(h["num_paths"]):
        if off + 12 > end:
            break
        sx, sy, n = struct.unpack_from(">3I", buf, off)
        # start_x / start_y are written from a cv::Point, so they are signed values
        # reinterpreted as u32 (GridStore.cpp:605-607); undo that.
        sx = sx - (1 << 32) if sx >= (1 << 31) else sx
        sy = sy - (1 << 32) if sy >= (1 << 31) else sy
        off += 12
        deltas = struct.unpack_from(f"{n}b", buf, off)
        off += n
        x, y = sx, sy
        pts = [(x, y)]
        for i in range(0, n - 1, 2):
            x += deltas[i]
            y += deltas[i + 1]
            pts.append((x, y))
        paths.append(pts)
    meta = {}
    if h["json_meta_size"]:
        meta = json.loads(buf[h["json_meta_offset"]:
                              h["json_meta_offset"] + h["json_meta_size"]] or b"{}")
    return h, paths, meta


def count_segments(path):
    """How many SegmentInfo align_and_filter_segments would build from this grid.

    normalgridtools.cpp:157-166 skips paths with fewer than two points and adds one segment per
    consecutive pair, so the answer is the sum over paths of (points - 1). A seglist stores
    `num_offsets` delta bytes for (1 + num_offsets / 2) points, so points - 1 is num_offsets // 2
    and the deltas never have to be decoded: this walks the path headers only.
    """
    with open(path, "rb") as fh:
        buf = fh.read()
    h = read_header(buf)
    off = h["paths_offset"]
    end = h["json_meta_offset"] or len(buf)
    total = paths = 0
    for _ in range(h["num_paths"]):
        if off + 12 > end:
            break
        n = struct.unpack_from(">I", buf, off + 8)[0]
        off += 12 + n
        if n >= 2:
            total += n // 2
            paths += 1
    return total, paths


def segments(paths):
    """Midpoints and normals of every line segment, the way
    align_and_extract_umbilicus builds them (normalgridtools.cpp:33-39, 59-63)."""
    import numpy as np
    mids, nrms = [], []
    for p in paths:
        if len(p) < 2:
            continue
        a = np.asarray(p[:-1], float)
        b = np.asarray(p[1:], float)
        t = b - a
        ln = np.hypot(t[:, 0], t[:, 1])
        ok = ln > 0
        a, b, t, ln = a[ok], b[ok], t[ok], ln[ok]
        if len(a) == 0:
            continue
        t = t / ln[:, None]
        mids.append((a + b) * 0.5)
        nrms.append(np.stack([-t[:, 1], t[:, 0]], 1))
    if not mids:
        return np.zeros((0, 2)), np.zeros((0, 2))
    return np.concatenate(mids), np.concatenate(nrms)


if __name__ == "__main__":
    import sys
    h, paths, meta = read_grid(sys.argv[1])
    print(h)
    print("meta:", meta)
    print("paths:", len(paths), "points:", sum(len(p) for p in paths))
    if paths:
        print("first path:", paths[0][:4], "...", len(paths[0]), "points")
        xs = [q[0] for p in paths for q in p]
        ys = [q[1] for p in paths for q in p]
        print(f"extent x [{min(xs)},{max(xs)}]  y [{min(ys)},{max(ys)}]")
