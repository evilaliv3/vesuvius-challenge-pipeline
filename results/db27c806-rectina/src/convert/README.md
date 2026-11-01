# src/convert: Rectina maps as tif or OME-Zarr

A Rectina read gives one map per unit, map.npy: a 2D float32 array with one score per pixel of the rendered surface. The score is a ranking score:
larger means more ink like, it is not calibrated and not a probability. Typical values lie between 0 and 1 (observed range 0.0 to 0.86 on the maps
tested), and a pixel the reader had no patch for holds 0.0.

rectina_map_convert.py writes such a map as a tif or as OME-Zarr, and reads either back to check it against the npy.

Needs python 3 with numpy, tifffile and zarr. Tested with numpy 2.5.3, tifffile 2026.9.20 and zarr 3.4.0. Nothing else is imported.

## Commands

The commands below are the ones the test ran, word for word, in a folder holding map.npy and the script. 

```
python3 rectina_map_convert.py tif map.npy map_float32.tif
python3 rectina_map_convert.py tif map.npy map_uint16.tif --dtype uint16
python3 rectina_map_convert.py zarr map.npy map_v3.zarr
python3 rectina_map_convert.py zarr map.npy map_v2.zarr --zarr-format 2 --pixel-size-um 9.36
python3 rectina_map_convert.py check map.npy map_float32.tif
python3 rectina_map_convert.py check map.npy map_uint16.tif
python3 rectina_map_convert.py check map.npy map_v3.zarr
python3 rectina_map_convert.py check map.npy map_v2.zarr
```


## Formats

tif float32 (default): values stored as they are, zlib compressed. The round trip is bit exact.
tif uint16: v16 = rint(clip(v, 0, 1) * 65535), so a score of 1.0 becomes 65535. The scaling is written in the file's ImageDescription. Values outside
0 to 1 are clipped. The round trip is within 0.5 / 65535 (7.6e-6) of the clipped map, and the check says so as a number.
OME-Zarr: array 0 of shape (y, x), float32, chunks of at most 512 by 512, blosc zstd level 3, and the top level attribute multiscales with axes y and x,
one dataset 0 and a scale transform (the pixel size in micrometers if given, else 1). These are the attributes that fmb_fb_render.py of this project writes for
its render stacks, with version string 0.4. Zarr format 3 is the default, as in that tool. Zarr format 2 (--zarr-format 2) is the pairing that the
OME-NGFF 0.4 text describes; both read back bit exact. Strict OME-NGFF 0.5 puts the multiscales under attributes.ome in zarr v3, which this tool does not write.
No OME-Zarr validator was run.

## What was tested

test-result.csv: for each of 3 real maps (two control units and one held-out unit, 3.9 to 5.2 Mpx), all 4 conversions and all 4 round trip checks passed,
plus two known fail cases that must be refused (a unit's tif checked against another unit's map, and a tif with one value changed by one float32 step).
test-output.sha256 lists the sha256 of every converted file and of every file inside the zarr folders, so a second run can be compared byte for byte
(tif and zarr bytes depend on library versions; the check, not the hash, is the contract).
