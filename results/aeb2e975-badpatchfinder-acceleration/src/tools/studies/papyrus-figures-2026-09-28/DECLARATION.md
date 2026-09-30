# DECLARATION: papyrus figures for works S (aeb2e975) and A (e44c8116)

Opened 2026-09-28T06:36:01Z (`date -u`), before any number of this study exists, on the director's note of
2026-09-28T06:27:33Z (director.md section 5): one figure with papyrus per work.

## What is made, and nothing else

1. **S.** The raw texture of ONE delivered sheet of a PHerc. 1447 growth tree whose untouched `c` stage was stopped
   by the seed runner's cap (seed-search-1447/evidence/runs/PHerc1447-seed<N>.csv, `downstream_return_code_v2` 124,
   «the stage 'c' returned it»): seeds 38, 40, 48. The sheet is chosen by a rule fixed here: among the sheets of those
   three seeds (seed-search-1447/evidence/squares-PHerc1447-seed<N>.csv, status measured), the one with the largest
   `square_mm_min_step`. Sampling is the house tool's, unchanged: nearest voxel of the raw masked scan
   20250521151220-8.640um-1.2m-116keV-masked.zarr level 0, one sample per lattice cell
   (squares-ink-1447/tools/sheet_texture_v2_squares.py, copied here with only its evidence path and label string
   changed). No ink detector runs. The fetch goes ahead only under the tool's own budget test, and only if it is
   under 2 GB; otherwise the next sheet by the same order whose chunks are cached is taken and the file says so.
2. **A.** One cube of the armed PHerc. 0139 window re meshed exactly as the window spawned it
   (gate-leaves-faces/tools/stage_ladder.sh with `--dump-final-only`, the window's own flag), cube
   z08576_y02432_x03840, the cube with the most faces above 0.30 in gate-leaves-faces/evidence/faces-above-030.csv
   (23, all made by HoleFill per stage-ladder.csv). Identity bar before any figure: the re meshed step12 matches
   stage-ladder.csv's step12_final row on nv and nf, and every one of the 23 rejected face centroids of
   faces-above-030.csv (placed coordinates) has a face of the re meshed mesh with centroid within 0.01 voxel after
   the placement offset. If the bar fails, no figure is drawn from it and the failure is the result.
   The texture is the RAW grey of finished-sheet-0139/data/cubes_RAW sampled at the surface.

## CPU and disk

Four cores at most, nice 10. /data at 95 per cent at opening (48 GB free); the S fetch is capped at 2 GB and the A
dump is the final stage only.

## Addition of 2026-09-28T08:08:39Z (dated, declared; the text above is unchanged)

Found at 06:4xZ, before any figure: the three trees whose `c` stage the cap stopped (38, 40, 48) all grew in air
(seed-search-1447/evidence/per-seed.csv, on_papyrus_or_in_air), and the chosen sheet, seed38 sheet 1, sampled at level 0,
has 205,424 of 205,424 cells not measurable (evidence/S/PHerc1447-seed38-texture-summary.csv): every chunk under it is
absent from the masked scan. There is no papyrus texture under it to render. So the S figure shows WHERE it lies: one z
plane of the raw masked scan at level 3 (8 voxels a pixel) through the sheet's median z, and, for comparison, the same for
the largest sheet of the seeds on papyrus (seed26 sheet 2); tools/fetch_level_slice.py fetches those two planes. The
level 0 texture of seed26 sheet 2 needs 2.53 GB (evidence/S26/PHerc1447-seed26-texture-fetch-plan.csv), above the 2 GB cap
declared above, with /data under the 50 GB floor: not fetched. A: the re mesh ran as declared (log/A-remesh-*.txt); the
identity bar is checked inside the figure tool (work A, tools/a-f8-a-face-the-certificate-rejects.py).
