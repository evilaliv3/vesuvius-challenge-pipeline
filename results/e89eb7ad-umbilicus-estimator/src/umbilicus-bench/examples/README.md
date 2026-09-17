# examples

One slice of the published surface prediction per scroll, at pyramid level 3, saved compressed with
`numpy.savez_compressed` as `slice` (uint8), `z` and `level`. Each is the middle height of the
46-height grid the bench uses, which is `data.slice_heights(scroll, 3, 46)[23]`.

They are here so that `example_estimator.py` runs with no network at all: enough to see what an
estimator receives, to try a rule of your own on a real section, and to check that your environment
works before spending the download on the full bench.

## Where each one came from

Read on 2026-09-10 from the Vesuvius Challenge open-data bucket, whose root is

```
https://vesuvius-challenge-open-data.s3.amazonaws.com/
```

and each is byte for byte the slice that `data.cached_slice(scroll, 3, z)` writes into `cache/`.

| file | surface prediction in the bucket | z at level 3 | slice | bytes | sha256 |
|---|---|---:|---|---:|---|
| `PHerc0125-level3-z1326.npz` | `PHerc0125/representations/predictions/surfaces/20250821151825-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | 1326 | 1049 x 1049 uint8 | 35072 | `2ced888fcce9534863a205e734316d089e2671fab9b137f677dd7771142f9713` |
| `PHerc0211-level3-z1236.npz` | `PHerc0211/representations/predictions/surfaces/20250821151803-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | 1236 | 994 x 994 uint8 | 25292 | `ed850b3fd376d93147c779d40ef4862ae353f5946b0bf86c4f7c281aebfad3a7` |
| `PHerc0826-level3-z1077.npz` | `PHerc0826/representations/predictions/surfaces/20250821151701-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | 1077 | 1022 x 1022 uint8 | 33373 | `5ee82a06107b80d5d5118bbb56d34d06a7eabebbedcc8983589fc756f35f7886` |

To make one again from the bucket:

```
python -c "import data, numpy as np; z=data.slice_heights('PHerc0826',3,46)[23]; np.savez_compressed(f'PHerc0826-level3-z{z}.npz', slice=data.read_slice('PHerc0826',3,z), z=z, level=3)"
```

The fourth scroll in the bench, PHerc0332, has no example slice here on purpose: its store is
already downsampled by four, so the factor between it and the frame its umbilicus is annotated in
is 32 and not 8, and `example_estimator.py` asks `data.py` for that factor rather than assuming it.

## Licence

Open data under CC BY-NC 4.0: attribution required, non-commercial use only. The citation the
organizers ask for is in `../LICENSE-DATA.md`.
