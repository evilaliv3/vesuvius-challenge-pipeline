# rectina_read

A reader for the Rectina ink checkpoints. It takes a rendered surface volume (a stack of layers sampled along the normal of a surface) and writes a map of ink scores, one value per surface pixel. The read recipe is the one that produced the maps of the Rectina article, cleaned of the study and cluster machinery it was run with.

The map is a ranking score between 0 and 1. It is not calibrated: do not threshold it at 0.5 (the stored m2 map of unit ag1 spans 0.23 to 0.84), compare pixels only with each other.

## What it does

Per start, 17 consecutive planes of the stack are cut out (starts 0 to 6 of a 23 plane stack, so planes s to s+16). A square lattice of patches covers the window with a stride of half a patch; the read is repeated on four lattices shifted by a quarter patch and the four maps are averaged. Each patch is normalised by villa's robust MAD normalisation (1st and 99th percentile) and read in two views, as it is and turned by 180 degrees, the second brought back before blending (`--views 2v`, the default; `1v` and `4v` exist). Patches are blended with a Hann window and divided by the summed window. The final map is the mean over the starts. The patch size follows the checkpoint: 128 for m1, 384 for m2. A uint16 stack is divided by 65280 (the rendered grey value times 256, 255 at full scale); other dtypes are read as stored (`--divisor` overrides). Patches that are entirely zero are skipped, so a pixel no patch covers stays 0.

## Requirements

- Python 3 with numpy; torch (the reads of the article used torch 2.12.1 with CUDA 12.9 on RTX 4090 pods; the CPU checks of this folder ran with torch 2.14.0 CPU); zarr 3 only if the stack is an OME-Zarr folder.
- The villa `vesuvius` package, which builds the network from the configuration embedded in the checkpoint (`vesuvius_unet_3d_stem_2d`, crop 17 x P x P, 508 tensors, `strict=True` load). The reads used these files of `ScrollPrize/villa`, folder `vesuvius/src/vesuvius/`: `ink_detection/config.py`, `ink_detection/models/*.py`, `ink_detection/inference/inference_runtime.py`, `image_proc/intensity/normalization.py`. They are byte identical to the files at villa commit `0bc2c241de7e289e36459468a9a0b32257679966` (2026-08-31, "Parallelize and hoist invariants in QuadSurface resample/rotate warps (#1080)", present in the fork `evilaliv3/villa`; that this commit is an ancestor of the current `ScrollPrize/villa` main was not verified). Later villa versions change `normalization.py` (31 October 2026, MAD far below the value range) and `inference_runtime.py` (compile fallback), so a newer checkout can change the maps; use the pinned commit.

```
git clone https://github.com/ScrollPrize/villa.git && git -C villa checkout 0bc2c241de7e289e36459468a9a0b32257679966
```

The checkpoints are `ckpt_130001.pth` (m1, sha256 `3a84f453314f4e2ced3dcc72cd3e3dbda9426be3a801e2bb7b3b0915f255e875`) and `ckpt_020000.pth` (m2, sha256 `dc39d5fa8fefe86455f92a415e03fb27d022b95299eea60fe175334774670386`). Both are loaded with `weights_only=True`.

## Input

A stack as an array of shape (planes, rows, columns) with at least 17 planes, either an `.npy` file or an OME-Zarr folder (the array `0` of the group). The stacks of the article have 23 planes, uint16. The stack has to be rendered along the surface normal at the scale of the training data (about 9 um); the article's stacks came from villa's `vc_render_tifxyz`, a build that is not the one of the public render component. Reads of stacks from another render were not tested.

## Commands

```
python3 rectina_read.py info    --checkpoint m2/ckpt_020000.pth
python3 rectina_read.py read    --stack unit.npy --checkpoint m2/ckpt_020000.pth --villa-src villa/vesuvius/src --device cuda --out out/unit
python3 rectina_read.py compare out/unit/map.npy reference_map.npy
```

`read` options: `--device cuda|cpu` (bf16 is on by default on cuda, off on cpu; `--bf16` and `--fp32` force it), `--starts 0 1 2 3 4 5 6`, `--views 2v`, `--batch 8`, `--threads N`, `--divisor X`, `--crop R0 R1 C0 C1`. `info` prints the checkpoint's sha256, step, crop size and tensor count (it needs torch only). `compare` exits 0 inside the tolerance and 14 outside (max abs 0.05, mean abs 0.005, Pearson 0.995, the tolerance used between GPU and CPU reads in the article's checks).

Output folder: `map.npy` (float32, rows by columns of the stack, values in [0, 1]), `reads.csv` (start, seconds, patches, device) and `DONE`, a JSON record with the sha256 of both files, the checkpoint sha256, patch size, tensor count, views, divisor and bf16 flag. A folder with a `DONE` is never overwritten.

## GPU and CPU

- GPU: the reads of the article ran on RTX 4090 pods, bf16. Measured for m2 on unit ag1 (2048 x 2560 pixels, 5.24 Mpx): 73.5 to 79.5 s per start, 533.7 s for 7 starts, 7631 MiB peak, 546 patches per start, about 102 s per Mpx for seven starts. m1 (patch 128) is faster per pixel; its wall time on the same unit is given under Tests.
- CPU: possible, not practical for whole units. One forward pass on 6 threads in fp32 took 0.056 s per 128 patch (m1) and 0.59 s per 384 patch (m2), measured on 31 October 2026 under `nice -n 19` at a machine load of about 3. A whole unit has hundreds of patches times 4 lattices times 2 views times 7 starts, which is hours for m1 and days for m2.
- Not calibrated: see the top of this file.

## Tests

- `test_rectina_read.py`: a stub model that is pixelwise and equivariant, so a correct lattice, shifted ensemble, views and Hann stitching must return exactly that function of the stack. Checks lattice coverage, view inverses, the stitch against the closed form for 1, 2 and 4 views on a size that is not a multiple of the patch, blank windows, the mean over starts, the refusal of a start past the end, the output files and `compare`. CPU, seconds, numpy only. Run: `python3 test_rectina_read.py`. It does not exercise a checkpoint.
- `test_parity_crop.py`: a CPU read of a 640 pixel crop of unit ag1 with m1 against the same area of the stored GPU map, with an inset of one patch on every side, inside the tolerance above. Real weights; estimated at under 30 minutes on 6 threads. Its result: on unit ag1, 640 pixel crop, inset 128, 361 patches per start, 327 s on 6 threads, max abs 0.001983, mean abs 0.000835, Pearson 0.9999958, inside the tolerance. m2 has no CPU crop test, because a crop would need more than 1100 pixels a side; its proof is the GPU read of this release, below.
- GPU reproduction of a whole unit, tested on unit ag1 only (one unit): this release of `rectina_read.py` was run on a rented cloud GPU machine (RTX 4090, bf16, device cuda) and its map was compared, with its own `compare`, against the stored GPU map of the same checkpoint and unit. Tolerances: max abs 0.05, mean abs 0.005, Pearson 0.995.

| model | checkpoint | patch | wall time | max abs | mean abs | Pearson | sha256 of the map, equal to the stored map |
| --- | --- | --- | --- | --- | --- | --- | --- |
| m2 | ckpt_020000 | 384 | 879.3 s | 0.0 | 0.0 | 1.0 | 55e2252f660fcd4ed8551fd97cebb7d6ed56847eaebe6c7ca652ebd4e1783e55 |
| m1 | ckpt_130001 | 128 | 451.8 s | 0.0 | 0.0 | 0.9999999999999998 | fc4d29c34cebd2694d53297271ad329cf3072d4588329c6ae6bd29ec827edfb5 |

Equal sha256 means that the public reader reproduces the stored maps of the same checkpoints on this one unit, nothing more: it says nothing about other units, other stacks or other hardware. Each figure is one run of one read. The commands were:

```
python3 rectina_read.py read --stack ag1.npy --checkpoint m2/ckpt_020000.pth --villa-src villa/vesuvius/src --device cuda --out out/ag1
python3 rectina_read.py compare out/ag1/map.npy ag1_m2_map.npy
```

## Licence

MIT, as the other code of this repository. Villa is GPL-3.0 and is used as a separate, unmodified package that is not copied here. The checkpoints have their own terms, stated in their cards.
