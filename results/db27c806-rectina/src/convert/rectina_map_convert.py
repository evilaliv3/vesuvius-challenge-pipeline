#!/usr/bin/env python3
"""rectina_map_convert.py: write a Rectina ink map (map.npy, 2D float32, one per unit) as a tif or an OME-Zarr, and check the round trip.

A map holds one ranking score per pixel of the rendered surface. The score is not calibrated: it is not a probability, only larger means
more ink like. Values are float32 in roughly 0 to 1. The converters never rescale unless you ask for uint16.

  python3 rectina_map_convert.py tif  MAP.npy OUT.tif  [--dtype float32|uint16]
  python3 rectina_map_convert.py zarr MAP.npy OUT.zarr [--zarr-format 3|2] [--pixel-size-um X]
  python3 rectina_map_convert.py check MAP.npy OUT.tif|OUT.zarr   (reads OUT back, compares to MAP, exits 3 on a mismatch)

tif, float32: values stored as they are; the round trip is bit exact.
tif, uint16: v16 = rint(clip(v, 0, 1) * 65535); the file records the scale in its ImageDescription ("rectina-map-uint16 v16=rint(clip(v,0,1)*65535)").
  The round trip is within 0.5 / 65535 of the clipped value (values outside 0 to 1 are clipped, which is declared, not hidden).
zarr: array "0" of shape (y, x), float32, chunks (512, 512), blosc zstd level 3; top level attribute "multiscales" with axes y and x and one
  dataset "0" with a scale transform, the attribute layout of the OME-NGFF 0.4 multiscales that fmb_fb_render.py of this project writes. Zarr
  format 3 is the default (as in that tool); format 2 is the pairing that the 0.4 text strictly describes. Round trip is bit exact.
Needs numpy, tifffile and zarr (tested with numpy 2.5.3, tifffile 2026.9.20, zarr 3.4.0). Nothing else is imported."""
import argparse, os, shutil, sys

DESC16 = "rectina-map-uint16 v16=rint(clip(v,0,1)*65535)"
TOL16 = 0.5 / 65535.0


def load_map(p):
    import numpy as np
    a = np.load(p)
    if a.ndim != 2 or a.dtype != np.float32:
        raise SystemExit("REFUSED: %s is %s %s, a Rectina map is a 2D float32 array" % (p, a.shape, a.dtype))
    if not np.isfinite(a).all():
        raise SystemExit("REFUSED: %s holds non finite values" % p)
    return a


def write_tif(a, out, dtype):
    import numpy as np, tifffile
    if dtype == "float32":
        tifffile.imwrite(out, a, compression="zlib", predictor=False, description="rectina-map-float32 raw score, not calibrated")
    else:
        v = np.rint(np.clip(a, 0.0, 1.0).astype(np.float64) * 65535.0).astype(np.uint16)
        tifffile.imwrite(out, v, compression="zlib", description=DESC16)


def write_zarr(a, out, fmt, px):
    import zarr, numcodecs
    from zarr.codecs import BloscCodec
    if os.path.exists(out):
        raise SystemExit("REFUSED: %s exists" % out)
    scale = [px, px] if px else [1.0, 1.0]
    axes = [{"name": n, "type": "space"} for n in "yx"]
    if px:
        for x in axes:
            x["unit"] = "micrometer"
    ms = [{"axes": axes, "datasets": [{"path": "0", "coordinateTransformations": [{"type": "scale", "scale": scale}]}], "name": "rectina-map", "version": "0.4"}]
    ch = (min(512, a.shape[0]), min(512, a.shape[1]))
    if fmt == 3:
        g = zarr.open_group(out, mode="w", zarr_format=3)
        g.attrs.update({"multiscales": ms, "note": "Rectina ink map, float32 ranking score, not calibrated"})
        arr = g.create_array("0", shape=a.shape, chunks=ch, dtype="float32", compressors=[BloscCodec(cname="zstd", clevel=3, shuffle="shuffle", typesize=4)], fill_value=0)
        arr[:] = a
    else:
        g = zarr.open_group(out, mode="w", zarr_format=2)
        g.attrs.update({"multiscales": ms, "note": "Rectina ink map, float32 ranking score, not calibrated"})
        arr = g.create_array("0", shape=a.shape, chunks=ch, dtype="float32", compressors=numcodecs.Blosc(cname="zstd", clevel=3, shuffle=1), fill_value=0)
        arr[:] = a


def read_back(out):
    """returns (array, kind) read from a tif or a zarr folder, with no knowledge of how it was written beyond the file itself"""
    import numpy as np, tifffile, zarr
    if os.path.isdir(out):
        g = zarr.open_group(out, mode="r")
        ms = g.attrs["multiscales"]
        assert [x["name"] for x in ms[0]["axes"]] == ["y", "x"] and ms[0]["datasets"][0]["path"] == "0"
        return np.asarray(g["0"][...]), "zarr"
    with tifffile.TiffFile(out) as t:
        d = t.pages[0].description
        return t.asarray(), ("tif-uint16" if d == DESC16 else "tif-float32")


def check(mp, out):
    import numpy as np
    a = load_map(mp)
    b, kind = read_back(out)
    if b.shape != a.shape:
        return 3, kind, "shape %s against %s" % (b.shape, a.shape), None
    if kind == "tif-uint16":
        ref = np.rint(np.clip(a, 0.0, 1.0).astype(np.float64) * 65535.0).astype(np.uint16)
        if b.dtype != np.uint16 or not np.array_equal(b, ref):
            return 3, kind, "uint16 values differ from rint(clip(v,0,1)*65535)", None
        err = float(np.abs(np.subtract(b.astype(np.float64) / 65535.0, np.clip(a, 0, 1).astype(np.float64))).max())
        return (0 if err <= TOL16 + 1e-12 else 3), kind, "max abs error %.3e against the clipped map, declared %.3e" % (err, TOL16), err
    if b.dtype != np.float32 or not np.array_equal(b.view(np.uint32), a.view(np.uint32)):
        return 3, kind, "float32 values are not bit equal", None
    return 0, kind, "bit equal, %d values" % a.size, 0.0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    t = sp.add_parser("tif"); t.add_argument("map"); t.add_argument("out"); t.add_argument("--dtype", choices=("float32", "uint16"), default="float32")
    z = sp.add_parser("zarr"); z.add_argument("map"); z.add_argument("out"); z.add_argument("--zarr-format", type=int, choices=(2, 3), default=3); z.add_argument("--pixel-size-um", type=float, default=None)
    c = sp.add_parser("check"); c.add_argument("map"); c.add_argument("out")
    n = ap.parse_args(argv)
    if n.cmd == "tif":
        write_tif(load_map(n.map), n.out, n.dtype); print("wrote", n.out)
    elif n.cmd == "zarr":
        write_zarr(load_map(n.map), n.out, n.zarr_format, n.pixel_size_um); print("wrote", n.out)
    else:
        rc, kind, msg, err = check(n.map, n.out)
        print("%s %s: %s" % ("PASS" if rc == 0 else "FAIL", kind, msg)); return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
