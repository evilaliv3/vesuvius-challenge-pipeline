<!-- Shipped copy of positive-control-0139/DECLARATION.md, 2026-09-30, as the study wrote it. Where it says PRIVATE, private or never public it describes how the study kept its own outputs on the day it was written, before the owner's decision of 2026-09-30 to publish this article with no position on the scroll. -->
# positive-control-0139: an end to end positive control of our chain, render and ink reader on labelled PHerc. 0139

Written 2026-09-29T06:28:38Z (`date -u`) by an agent of the coordinator, on the
director's order of 2026-09-29T06:22:17Z (the owner asks whether we are doing something wrong). No number of this study
exists yet: nothing has been mapped, grown, rendered or read. Nothing below is retouched after the first number; additions
are dated and declared. PHerc0139 is not a prize restricted scroll; every output stays in this study all the same.

## The question and the bar (the order, verbatim)

«The one check we never ran: an END TO END POSITIVE CONTROL. Study positive-control-0139, DECLARATION first: grow our own
chain (same binary and settings as chain-0826, g 36000, the five downstream stages) from 3 seeds inside the held out
labelled region of pherc0139-w016 (heldout-labels-0139/evidence/heldout-clean.csv; the 0139 prediction is on disk under
data/datasets/PHerc0139), render our sheet over that region with the SAME render path as ink-square-0826
(vc_render_tifxyz, 28 layers), run the SAME ink reader, and compare against the reader on the organisers' own w016 segment
over the same region (known ink, labelled). Read in all 8 in plane orientations (4 quarter turns x mirror) and both depth
directions, plus the axis aligned render of the earlier order. Bar declared now: if the organisers' segment shows ink on
the labels (balanced accuracy on the clean held out region at least 0.70) and ours stays below 0.60 in every orientation,
our render path is wrong and the 12 readings on 0826 are void; if ours reaches at least 0.70 in some orientation, that
orientation is the one to use on 0826. Highest priority after the axis aligned renders; results by 14:00Z. If the 0139
data needed is not on disk, size the fetch first.»

How the bar is read, fixed here before any number:
- «theirs shows ink» = the best `ba` of the surface «theirs» over its rows (orientation x direction x checkpoint, lattice
  render) is at least 0.70. If it is under 0.70 the control itself failed: the verdict row says «control not valid» and the
  bar decides nothing about our sheets.
- «ours below 0.60 in every orientation» = every row of the surface «ours» (every covering sheet, orientation, direction,
  checkpoint, lattice and axis aligned render) has `ba` under 0.60 (a «not measurable» row counts as not reaching 0.60 and
  is listed).
- «ours reaches at least 0.70 in some orientation» = any row of «ours» at 0.70 or more; the verdict row names the
  orientation (k, m), direction, checkpoint and render of the best such row.
- Anything else (ours best between 0.60 and 0.70, theirs at least 0.70): «neither branch of the bar», said so.
- The verdict uses the common region (below) at match radius k = 4 voxels; k = 2 rows are written beside and decide
  nothing.

## Inputs (all on disk; anything missing is sized in evidence/fetch-plan.csv before a fetch)

- Labels: `runs/rev1/heldout-labels-0139/data/labels/pherc0139-w016/` (inklabels z 10, ink = value > 0) and the clean
  held out mask `data/masks/pherc0139-w016_heldout_clean.tif` (heldout-clean.csv row pherc0139-w016: 171,693 px, 0.1581
  cm2, label grid 9.596 um, level 2 of the render of the 2.399 um tifxyz of public segment 20250108000004-w029 on volume
  20260102150214).
- The organisers' surface on OUR scan frame: the 9.362 um tifxyz of the same public segment on volume 20250728140407,
  `runs/rev1/ink-labels-0139/data/PHerc0139/segments/20250108000004-w029_2025010827/mesh/20250108000004-on-20250728140407-9.362um.tifxyz`.
- Prediction: `/data/scrollagent/data/datasets/PHerc0139/0` (manifest.json there: volume 20250728140407, model
  20260413222639-surface-m7-L0-th0.2, shape 20974 6621 6621, 192 cubed chunks, blosc zstd) and its chunk manifest
  `chunks.txt`. The threshold is the published one (th0.2, stored as 0/255); nothing is re thresholded.
- Raw volume for the render: s3 open data `PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/`, streamed
  by vc_render_tifxyz through the house cache `data/cache/vc3d-remote-cache` (15 GB of this volume already there).

## Label points in our scan frame (the one mapping, declared before it is fitted)

Label pixel (r, c) of the level 2 grid has its centre at level 0 pixel (4r + 1.5, 4c + 1.5), and a level 0 pixel (i, j)
sits at grid coordinate 0.05 (i + 0.5), 0.05 (j + 0.5) of the 2.399 um tifxyz, bilinear, invalid when a corner is invalid
(heldout-labels-0139/tools/sheet_overlap.py's convention). That gives each clean pixel a point in the 2.399 um frame of
volume 20260102150214. A 3D affine A from that frame to the voxels of 20250728140407 is fitted by iterative closest point
between the two published tifxyz of the SAME segment (the 2.399 um grid upsampled bilinearly by 4, transformed by A,
against the 9.362 um grid upsampled by 4), started from the per axis scale and translation of the two bounding boxes,
least squares affine at each iteration, 30 iterations or until the change is under 0.01 voxel. Accepted only if (a) the
median distance from the 9.362 um upsampled nodes near the held out region (within 64 voxels of a clean point) to the
transformed 2.399 um upsampled nodes is at most 1.0 voxel, and (b) the same A applied to a second segment with both
tifxyz on disk (20250108000005-w030: 2.399 um in heldout-labels-0139/data/meshes, 9.362 um in ink-labels-0139/data)
gives a median at most 1.5 voxels. Refused otherwise, and the study stops with a row. `tools/map_labels.py`,
`evidence/label-map.csv` (the affine, the residuals, a and b), `scratch/labels-9362.npz` (per clean pixel: r, c, ink, point).

## Seeds (rule declared before any point is seen)

Candidates: clean held out pixels whose mapped point, rounded to the nearest voxel, reads 255 in the local 0139
prediction. The clean region's label column range is cut into three equal thirds; in each third the seed is the
candidate nearest (label grid distance) to the centroid of that third's clean pixels. A third with no candidate gives no
seed and the row says so. Seeds are integer voxels (x, y, z), axes the stock 1 0 0 and 0 0 1. `tools/seeds.py`,
`evidence/seeds.csv`.

## The growth and delivery (chain-0826's binary and settings, one declared difference: the scroll's shape)

- Binary: the runtime seed build of chain-0826 (BUILD flathash+avx512+lto+pgo+native+runtime-seed), built once in a copy of
  runtime-params-96/scratch/tree-clean with runtime-params-96/tools/runtime-seed.patch (sha pinned 4660fcad...), the PGO
  profile restored with every .gcda sha256 checked against chain-0826/scratch/pgo-profile/pgo-profile.csv, the same make
  line and flags. **Known reference first:** with PHerc0826's shape the copy must build to a37944ea... (runtime-params-96's
  gated binary); a difference refuses. Then the SAME tree with PHerc0139's shape (VOL_SIZE_X 6621, Y 6621, Z 20974, from
  pipeline/datasets/manifests/PHerc0139.json; the only change, since VOL_SIZE_* is compiled in and 0826's 16920 z would
  cut 0139's 20974), FMA count 0. `tools/build_0139.py`, `evidence/build-gate.csv`.
- Settings: chain-0826/scratch/deliver-settings.env read (never sourced): SIMPAPER_SHARED_CHUNKS 512, CAP_CHUNKS 512,
  SIMPAPER_FORCE_THREADS 1, OMP_WAIT_POLICY passive, OMP_NUM_THREADS 3. Growth `simpaper10 g 36000` (the order's g,
  not the chain's current 72000), no time cap, SIMPAPER_SEED_X/Y/Z exported and the start line «Seed at run time: x y z
  (environment)» checked; SIMPAPER_SURFACE_ZARR the 0139 prediction (original zstd; the chain's lz4hc copy exists only for
  0826), ZARR_CHUNK_MANIFEST its chunks.txt. Then c, l, vm 10, hm 10, fm 30 10 on a copy of the tree with
  SIMPAPER_PATCH_LIMIT 40000 and run_seed.sh's downstream cap formula. `tools/run_seed_0139.sh` copies run_seed.sh's stage
  lines; rows per seed in `evidence/runs/<seed>.csv` (run_seed.sh's columns).
- Coverage of each delivered sheet (patch_<n>.bin, to tifxyz by squares-ink-1447/tools/signal_null.py patch2tifxyz):
  clean label points matched by the sheet within k = 2, 4, 6 voxels (nearest sheet point, bilinear on the lattice), in
  pixels and mm2 (label pixel 9.596 um), and the lattice cells within 4 voxels of a clean point. `evidence/coverage.csv`.
  A sheet covers the region when at least 2,000 clean ink and 2,000 clean no ink pixels are matched at k = 4
  (score_ink_0139's MIN_PIX). If no seed's sheet covers it, that is said early and the study stops at a row.

## Render and reader (ink-square-0826-seed2604/tools/run_one_v2.sh's path, copied; nothing of that study edited)

Both surfaces, «ours» (the covering sheet with the most matched clean pixels at k 4 first, the other covering sheets after)
and «theirs» (the 9.362 um w029 tifxyz), go through the same steps:
- Window: the surface's grid cells within 64 voxels of a clean label point, bounding box plus 60 cells (run_one_v2's margin,
  in cells of each surface's own grid), cut from the tifxyz (ink-square-0826-seed2604/tools/sq.py cut); window mask by
  signal_null.py validmask; size row by signal_null.py chunks (raw chunks the renders need) BEFORE any render.
- vc_render_tifxyz (villa-tracer-build, sha 8401cea2...) `--num-slices 28 --slice-step 1 --scale 1 --flip-normals
  --voxel-size 9.362 --group-idx 0 --pyramid 0 --cache-gb 8`, remote url as above. Base render, gap_profile.py, lamina
  centring per direction by `tf.py delta A DIR LOW HIGH 9.362` from the gap minima (shift 0 if a side has no minimum, as
  run_one_v2), `tf.py shift`, render of the shifted surface.
- Orientation: the step `sq.py orient` of run_one_v2 reads PHerc0826's published umbilicus and is not applicable to 0139;
  instead ALL EIGHT (k in 0..3 quarter turns, m in 0, 1 mirror) are forced with `tf.py make` and turned back with `tf.py
  back ... 1 0 0 0 0 H W` exactly as run_one_v2.
- Reader: ink-detector-0139/scratch/venv, PYTHONPATH seven-squares-references/scratch/villa-78877eaf/vesuvius/src,
  hybrid_3d2d seed42 and seed43 step-075000.pth (sha256 e635558a... and 2aeaa85a..., checked), `infer --direction
  {forward,reverse} --overlap 0.5 --blend-mode hann --batch-size 4 --num-workers 1 --no-compile` with the turned mask;
  the input contract row (record.py contract) on every input. Forward reads the forward centred render, reverse the
  reverse centred render, as run_one_v2.
- Axis aligned arm (the earlier order): best-windows-0826's align.py is bound to 0826 targets (it imports that study's
  window list); so the declared fallback is used: each surface's window grid is ROTATED in its own parameter plane by the
  circular median, over window cells within 64 voxels of a clean point, of the angle of grad z (dz/drow, dz/dcol) to the
  row axis, resampled bilinearly (a point valid only if its four corners are), so that scan z runs along the rows; then the
  same render, centring, eight orientations, two directions, two checkpoints. `tools/axis_rotate.py`. The angle is a
  column.
- Scoring: each back turned prediction is read at the clean label points: the render pixel whose 3D point
  (score_ink_0139.points_at convention) is nearest the label point, if within k voxels (k = 2, 4). Common region = clean
  label pixels matched at k by BOTH the ours surface of that row and theirs. `score_ink_0139.ba_auc` (balanced accuracy at
  uint8 >= 128, AUC with ties one half; «not measurable» under 2,000 ink or no ink pixels), the threshold the earlier 0139
  studies used. Also ba on each surface's own matched set, as a column. One row per surface x render (lattice, axis
  aligned) x sheet x orientation x direction x checkpoint x k in `evidence/control.csv` (tool `tools/score.py`).
- Verdict: `evidence/verdict.csv`, one row by `tools/verdict.py` after theirs and the first covering sheet of ours are
  read on both renders; a later row (never a rewrite) when the other sheets are read.

Caveats carried by every row: the region is small (0.1581 cm2 clean) and was the organisers' online validation region
during training (step 75000 is a fixed step, but the region was watched); the labels were drawn on the 2.399 um render,
mapped to our frame by the affine above.

## Load and disk

At most 8 cores, nice 10, read from /proc/loadavg before each heavy start: growths OMP 3, at most two at once (6 cores);
inferences 2 threads, at most one beside two growths, else at most three at 2 threads (or two at 3). best-windows-0826 has
priority. The chain-0826 runner (PGID 2525901) and its files are never touched. Long work runs as setsid runners in
tools/, PGIDs in the ledger. TMPDIR=/data/tmp. Disk: /data had 40 GB free at 06:21Z; a growth starts only with at least 38
GB free, every step stops under 35 GB free, and no fetch starts if free minus its bound is under 35 GB (a refusal row).
Raw chunks this study adds to the cache are listed (scratch/cache-new-*.txt) in a ledger row and deleted after use; growth
trees are deleted after delivery if the disk needs it (listed first). Target: results by 14:00Z.

## Addition of 2026-09-29T06:33:16Z (the clock read by the ledger row written with it): render variants on our sheet, roughness, and the window margin (director 06:30:48Z, relayed by the coordinator), before any number of them

No number of this study exists yet except the binary's build gate (evidence/build-gate.csv, no measurement of the
question). The director's addition, verbatim: «the owner uploaded two organisers' style renders
(inbox/organisers-renders/*.png: a segment texture with Greek letters marked, and its ink prediction; source not given).
Against ours the differences are: (1) orientation, their fibres a strict horizontal and vertical grid (known); (2)
SMOOTHNESS: their surface follows the sheet smoothly, fibres as thin continuous lines; ours shows wavy streaks and patches
'combed' in different directions, the signature of a surface made of many patches with small ripples, so sampling along
the normal cuts across fibre layers; (3) depth: theirs looks like a composite of several layers, ours one layer; (4)
contrast: ours saturates. Add to positive-control-0139, declared first, render variants on our w016 sheet, each read by
the same ink reader on the labelled region: (a) axis aligned; (b) mesh smoothed before rendering (Gaussian on the 3D
positions over the grid, sigma 2 and 5 cells, normals recomputed from the smoothed surface); (c) layer composite, mean
over the central 7 layers, as the organisers' composite; (d) contrast as theirs (p1 to p99 over the whole segment, no per
window stretch); plus a+b+c and a+b+c+d. Report balanced accuracy per variant and orientation beside the organisers' own
w016 segment; the best becomes our render path for rereading the 12 squares of 0826 and the best windows. Also measure
mesh roughness (median angle between neighbouring cell normals) on our w016 sheet and on the organisers' w016 tifxyz, the
same way.»

What the reader does with its input, read in villa 78877eaf before declaring (not a number of this study): infer.py takes
the whole 28 layer stack, keeps the central 17 layers (`center_crop_layer_indices`: layers 6 to 22; reversed for
direction reverse), and normalises EVERY PATCH by itself (`tifxyz_robust` = normalize_robust: clip at the patch's own 1st
and 99th percentile, then median and MAD; the checkpoints' config says normalization robust_mad). So:

- **(a) axis aligned**: the rotation declared above (circular median angle of grad z to the row axis, over window cells
  within 64 voxels of a clean point; grid rotated and resampled bilinearly; render as the lattice).
- **(b) smoothed mesh**: the window tifxyz's x, y, z grids each convolved by a Gaussian of sigma 2 cells, and separately 5
  cells, of OUR sheet's grid (normalised convolution over valid cells only: sum of w p over sum of w; a cell stays valid only
  if it was valid), written as a new tifxyz; vc_render_tifxyz computes the normals from that surface, so they are the
  smoothed surface's normals. The cell size in voxels is a column. Centring (gap minima) is measured again on each variant's
  own base render, as the lattice.
- **(c) layer composite**: the model cannot take one image, so (c) is applied to its input as: every layer i of the 28
  layer render replaced by the mean of the 7 layers i-3 .. i+3 (clamped at the stack ends), rint to uint8; the stack keeps
  its 28 layers and the reader crops 17 as always. The single central 7 layer mean image (layers 11 to 17) is written as a
  PNG, visual only, for the owner.
- **(d) contrast as theirs**: one linear stretch of the whole window render (all 28 layers, window mask pixels), p1 to 99
  mapped to 0 to 255, clipped, uint8. Because the reader renormalises every patch by its own percentiles, (d) changes the
  model input only through clipping and rounding: measured and written beside (`evidence/variant-input.csv`: share of
  pixels clipped, and median absolute difference of normalize_robust between the plain and stretched stack over 64 patches
  of 128 x 128 x 17 at fixed positions). The rows are read all the same.
- **a+b+c** and **a+b+c+d**: (b) with the sigma whose best row (over orientation, direction, checkpoint, k 4) is higher
  (tie: 2), rotated as (a), then (c), then (d); the order of operations as written.
- Every variant is read in all 8 orientations x 2 directions x 2 checkpoints, scored as declared (common region with theirs,
  k 2 and 4), one row each in `evidence/control.csv` with a column `variant` (lattice, a, b2, b5, c, d, abc, abcd).
  Variants run on the best covering sheet only; theirs is read on the lattice render (its own form) and, for reference
  only, with (a) (its rotation measured the same way).
- **Order of work under the 14:00Z deadline**: theirs lattice and ours lattice first, then a, b2, b5, c, d, then abc and
  abcd. What is not finished by 14:00Z is reported «not run» with the reason. The verdict of the order's bar is written
  when theirs and ours lattice and (a) are read; the variants follow as later rows of verdict.csv (never a rewrite), and the
  best variant is named by the highest k 4 ba row of ours.
- **Roughness** (`evidence/roughness.csv`, `tools/roughness.py`): per grid cell the unit normal from the cross product of
  central differences of the 3D grid; the angle between the normals of each cell and its right and lower neighbour (both
  valid); median and 90th percentile over cells whose point is within 4 voxels of a clean label point. Measured on each
  surface's own grid AND on a common spacing of about 20 voxels (theirs native; ours taken every n cells, n = rint(20 /
  our cell size)), since the angle between neighbours depends on their spacing; the comparison row is the common spacing.
- **Window margin corrected here, before any render**: the margin «60 cells of each surface's own grid» written above
  would give theirs (20 voxels per node) 1,200 voxels and ours about 240; it is replaced by the same margin in render
  pixels for both, **128 render pixels (voxels)** around the cells within 64 voxels of a clean point (one reader tile of
  context on every side).

## Addition of 2026-09-29T06:38:01Z: the ICP start, changed after its first numbers (declared as such)

The first run of tools/map_labels.py (PGID 3623152, stopped by its group after 5 minutes with no iteration finished) and
two probes on the console (not kept as evidence; the numbers are restated here only to say why the start changes): from
the bounding box start, the median distance from the 9.362 um nodes to the transformed 2.399 um nodes was 264 voxels, too
far for closest point matching; a correspondence through the two grids (9.362 node (i, j) against the 2.399 grid at
(f i + oi, f j + oj)) gave a least squares affine with a median residual near 1.2 voxels. So the ICP now STARTS from that
correspondence affine: f in {9.362 / 2.399, 1404 / 361, 1444 / 371} (the resolution ratio and the two grid size ratios),
oi and oj from -30 to 30 by 2, then by 0.25 within 2 of the best, on 5,000 evenly drawn valid 9.362 nodes; the start is
the affine of the (f, oi, oj) with the smallest median residual. Everything after the start (ICP on the upsampled grids,
the checks a and b and their bars) is unchanged. The start's f, oi, oj and median residual become rows of label-map.csv.

## Addition of 2026-09-29T06:40:01Z: (a) is the z regrid; the rotation becomes a control (owner's decision, director 06:38:48Z), before any variant number

Verbatim as relayed: variant (a), «axis aligned», is the TRUE correction: the render is regridded with v = the scan's z and
u = arc length along the sheet at constant z. render-routes-0826/tools/regrid_z.py is to be used when it exists; until
then this study builds its own by the same definition, declared here; the per window rotation stays ONLY as a labelled
control variant «rotation control» (variant name `rotctl` in control.csv), never as (a).

- **(a) = regrid_z.** At the moment (a) is run: if runs/rev1/render-routes-0826/tools/regrid_z.py exists and takes a tifxyz
  (or a patch file) and writes a regridded surface, it is used unchanged and the row names it with its sha256. Otherwise
  `tools/regrid_z.py` of this study, by best-windows-0826's definition (its DECLARATION addition of 2026-09-29, «Full
  resampling»): h = median 3D distance between valid grid neighbours of the window; centre = the valid cell nearest the
  centroid of the cells within 64 voxels of a clean point; rows are z levels z_v = z(centre) + v dz; u = 0 on the steepest
  ascent curve of z through the centre (marched in the grid's parameter space along grad z / |grad z|^2, bilinear); each
  row is the iso-z contour of level z_v in the parameter space (skimage find_contours on the z grid, invalid cells NaN), the
  piece nearest that row's origin point, its 3D arc length accumulated from the origin both ways and points taken at u_k =
  k h by linear interpolation along it; dz = h for a first pass, then dz_final = h h / (median 3D distance between vertically
  adjacent points of the first pass), one correction. Output a tifxyz of scale 1 / h (one render pixel about one voxel as
  the lattice), columns u, rows v. dz_final, h, the rows with an origin and the median |z - z_v| are columns of
  evidence/regrid.csv.
- **a+b+c, a+b+c+d** use this (a): smoothing (b) first on the lattice, then the regrid, then (c), (d).
- Theirs: read on its lattice render (its own z vertical form) and, for reference, through the same regrid.
- The first numbers (theirs on its lattice) go to the coordinator with a ledger row as soon as they land.

## Addition of 2026-09-29T06:42:47Z: the third seed (after seeds.csv's first numbers, declared as such)

evidence/seeds.csv: the middle third of the clean region's column range holds no clean pixel (the clean held out region is
two blocks), so the declared rule gives two seeds (thirds 1 and 3). The order asks for 3. The third seed, fixed here: the
candidate nearest (label grid distance) to the centroid of ALL clean pixels, if it differs from the two seeds; written as a
fourth row of seeds.csv by tools/seeds3.py (seeds.py's code, one more row), and the row says it was added after the first
two were seen.

## Addition of 2026-09-29T06:44:05Z: a seed whose growth stops on its first seed (after that number, declared as such)

evidence/runs/PC0139-seedB.csv: seed B (third 3) returned 1 at once, its log «Aborting, too few points added» and «Not
enough growth steps ... on first seed». Seeds A and C grow. Rule for B, fixed here: the next candidates of the same third
(clean pixels reading 255, ordered by label grid distance to that third's centroid), each at least 25 label pixels from
every seed already tried, grown one at a time with the same runner until one passes its first seed, at most 4 more tries
(tools/seed_retry.py writes each try as a row of evidence/seeds.csv; the growths run only after A or C has ended, to stay
within 8 cores).

## Addition of 2026-09-29T06:52:00Z: (a) through render-routes-0826's regrid_z.py (it now exists), and 0139's umbilicus in our frame

The coordinator reports render-routes-0826/tools/regrid_z.py ready (self test 06:48:05Z; sha256 ef1b9c63... read now).
By the addition of 06:40:01Z it is the tool of (a) and of a+b+c, a+b+c+d, used read only: `regrid_z.py run --input
<window tifxyz> --umbilicus <JSON> --out <tifxyz> --label <surface-variant> --csv evidence/regrid-routes.csv` with its
defaults (--fit spline, --knot-mm 0.5, h the median input step, side the larger box side + 128), the box the whole window.
This study's own tools/regrid_z.py was run once on theirs' window before the tool existed (evidence/regrid.csv, row
theirs-a); that output is set aside (scratch/theirs/a-own-regrid/) and not read.
The tool needs an umbilicus JSON. The only published PHerc0139 umbilicus is
s3://vesuvius-challenge-open-data/PHerc0139/representations/umbilicus/20260102150214-umbilicus-20260826112529.json (27,960
bytes), on volume 20260102150214 (2.399 um), not on 20250728140407. It is fetched (evidence/fetch-plan.csv row first) and
its control points mapped to our frame by the affine A of evidence/label-map.csv (the same map as the labels);
tools/umbilicus_map.py writes scratch/umbilicus-0139-on-20250728140407.json in the published JSON's form (x, y, z, score
kept). No other change.

## Addition of 2026-09-29T07:20:47Z: block 3 seeded in the sheet's plane; seed C crashed (after those numbers, declared as such)

evidence/runs: seed B and its four retries (seeds.csv rows «retry 1..4») all stop on their first seed in 0 to 1 s; seed C
grew 2204 s and ended with a segmentation fault (rc 139, no patch file written). The stock seed plane of simpaper10 is
spanned by axes 1 0 0 and 0 0 1 (normal y); the organisers' w029 tifxyz's unit normal at seed B is about (0.98, -0.14,
0.14), i.e. along x, while at seeds A and C it is about y (read on the console from the tifxyz, not kept as evidence). So
block 3 cannot seed with the stock plane. Fixed here: seed B's point is grown once more with the runtime binary's own
axis variables SIMPAPER_SEED_AXIS1 = 0 1 0 and SIMPAPER_SEED_AXIS2 = 0 0 1 (the plane whose normal is x), everything
else as chain-0826 (name PC0139-seedBx; a row seed_axes in its runs CSV). This departs from «same settings» on the seed
plane only, and every row of that sheet says so. Seed C is not retried (a crash of the same binary on the same seed is
expected to repeat); seed A still grows.

## Addition of 2026-09-29T07:32:13Z: the director's top priority orders of 07:22:16Z (render path against the organisers' prepared input), declared before their numbers

Verbatim (relayed by the coordinator): «(1) score both on the exact common pixels; (2) compare our render with their
surface-volume.zarr layer by layer on the same tifxyz: correlation per layer pair to find the depth offset, the normal sign,
the layer spacing, the interpolation and the value mapping; (3) change our render path, one declared change at a time,
until it reproduces theirs (correlation at least 0.95 on the matched layers) and the ba on the common pixels is within
0.02 of theirs; (4) that corrected path becomes the render for everything after (best windows, certified square, K2, 0826
squares).» Also: the z regrid (a) failed its bar at render-routes-0826 and «may be used for figures, with that failure
stated, never for a number»: (a) and a+b+c, a+b+c+d give no number in this study.

A fact read before declaring (heldout-labels-0139/data/prepared/pherc0139-w016/surface-volume.zarr/.zattrs and
tools/prepare_w016.sh, not a number of this study): their input is villa's prepare_9um_isotropic_input --level 2 of the
segment's published surface volume **2.399um-0.22m-78keV-volume-20260102150214** (level 2 in plane, mean of 4 planes in
z, planes 13 to 97 of 109, 21 slices), a different scan (0.22 m, 78 keV, 2.399 um) from the one our path renders
(20250728140407, 1.2 m, 113 keV, 9.362 um). Candidate (b) of the coordinator is therefore a scan difference, which (2)
measures.

- **(1)** `tools/common_pixels.py` -> evidence/common-pixels.csv: pixel sets = the clean held out pixels (171,693) and, for
  reference, all held out pixels (178,146); theirs = orientation-1447/scratch/ho-o00-seed{42,43}-back.tif (identity, crop
  rows 4816:5553, cols 1675:4083 of the label grid, forward); ours = scratch/theirs/lattice/p/{forward,reverse}-k0m0-seed*.tif
  read at the render pixel matched to each label point within 4 voxels (score.py's rule); a label pixel enters only if both
  have a value. score_ink_0139.ba_auc.
- **(2)** `tools/layer_corr.py` -> evidence/layer-corr.csv: at the clean pixels matched within 4 voxels, the Pearson
  correlation of each of their 21 slices with each of our 28 layers, for our unshifted base render and our forward
  (centred) render. Per their slice: the best our layer and its r. Over the 21 slices: least squares line of best layer
  index against slice index (slope sign = normal sign, slope = spacing ratio, expected about 9.596 / 9.362 = 1.025 in
  magnitude; intercept = depth offset), and at the best pair the linear value map (gain, offset) and the Spearman rank
  correlation. Also r of their slice 10 against our layer 13.5 (mean of 13 and 14), the centres.
- **(3)** is declared change by change in later additions, each before its numbers, each with a correlation and a ba row.

## Addition of 2026-09-29T07:33:56Z: change 1 to our render path, no lamina centring (order (3)), before its numbers

The only change: the reader reads the UNSHIFTED base render (tf.py delta and shift not applied) in both directions, orientation
k0 m0 (the one matching their frame), both checkpoints. Everything else as the path. `tools/probe.sh theirs nocentre
scratch/theirs/lattice/r/base.zarr` (infer + nothing else: the base render is k0 m0 already), scored by
`tools/probe_score.py nocentre` on the same 171,693 clean pixels as common-pixels.csv, rows to evidence/render-changes.csv
(change, checkpoint, direction, ba ours, ba theirs prepared, difference, and the layer correlation r of their slice 10
against our layers 13 to 14 of the input read, from layer-corr.csv). Accepted by the order's bar when the correlation is at
least 0.95 and the ba within 0.02 of theirs; otherwise the row says «not accepted» and says which part failed, and the next
change is declared.

## Addition of 2026-09-29T07:43:00Z: change 1 not accepted; what order (3) can and cannot reach on w016 (after change 1's numbers)

evidence/render-changes.csv: without centring, forward ba 0.6663 (seed42) and 0.6843 (seed43) against theirs 0.7644 and
0.8052; not accepted (ba and correlation). The centring is not where the gap is. The fact of the 07:32:13Z addition stands:
their w016 input is rendered from the 2.399 um scan 20260102150214; PHerc0826 has only its 9.362 um scan (aws s3 ls of
PHerc0826/volumes/ at this time: one volume, 20250821151701-9.362um), and on the 9.362 um scan our renderer reproduces the
organisers' native9 inputs exactly (ink-finetune-k2/evidence/refcheck.csv: NCC 1.0000 at k0 m0 on w035 and w039). No change
of a render of scan 20250728140407 can make it equal an image of another scan, so the 0.95 correlation of order (3) is not
reachable on w016 by a 9.362 um render. The one test that would close order (3) on w016, rendering the 2.399 um scan through
our renderer (level 2, mean of 4 planes, as prepare_9um_isotropic_input) to show the same code reproduces their slices, is
declared here but NOT run until the director says so (it needs a fetch of that scan's chunks under the surface, sized first,
and it could not serve 0826). The positive control of the order (ours against theirs, both through our 9.362 um path) goes on.

## Addition of 2026-09-29T08:22:47Z: order (3)'s correlation bar recorded as not reachable (director 08:22:08Z)

The director accepts the diagnosis: the renderer is right (ink-finetune-k2 refcheck NCC 1.0000 on native9 inputs), and the
0.09 of balanced accuracy on w016 is the 2.399 um input. The 0.95 correlation of order (3) is recorded as NOT REACHABLE
across two scans: their w016 slices are images of scan 20260102150214 (0.22 m, 78 keV, 2.399 um, level 2, mean of 4
planes), ours of scan 20250728140407 (1.2 m, 113 keV, 9.362 um); the best layer pair reaches r 0.849 (layer-corr.csv) and
no render change of the 9.362 um scan can make it the other scan. No further render change is chased. The control of the
order continues: our seed A S0 (and Bx S0) read in all 8 orientations x 2 directions x 2 checkpoints beside theirs through
the same path; verdict by the bar declared at 06:28:38Z.

## Addition of 2026-09-29T08:54:22Z: the window of sheet Bx S0 (after its size row, declared as such)

evidence/reads/ours-Bx-S0-lattice/b-chunks.csv: the window rule «cells within 64 voxels of a clean point» took 54,110 cells
of Bx S0 spread over rows 1136 to 4120 (other windings of the same sheet pass within 64 voxels), a 2419 x 12197 px render
whose fetch bound (6.788 GB) was refused by the disk rule. For Bx S0 only, the window is the cells within 4 voxels of a
clean point (7,262 cells, the coverage rule's radius) plus the same 128 render pixels: tools/prep.py bounds with a radius
argument (default 64 unchanged, so A's windows are as they were). The Bx rows say «window radius 4».

## Addition of 2026-09-29T09:13:32Z: the coordinator's two checks (after verdict row 1), declared before their numbers

(1) **The 0826 orientation and radial rule on our lattice.** sq.py orient (run_one_v2's choice of k, m and direction:
orient_0826.py's side rule with orientation-1447's measure, stride 4) on the window tifxyz of ours-A-S0 and of theirs, with
the axis given by an umbilicus of 0139 in place of 0826's (orient_0826.axis reads 0826's file; `tools/orient_rule_0139.py`
imports orient_0826.measure and tf and orientation-1447's orient.load unchanged and builds the same linear in z axis from
a JSON). Run with BOTH 0139 axes, since they disagree by 707 to 824 voxels (evidence/umbilicus-map.csv): the published one
mapped to our frame, and villa-tracer-0139's estimate on the prediction. Rows to evidence/orient-rule.csv: surface, axis,
k, m, direction predicted, the rule's shares and check. Written before any comparison with the scores is made in a row.
(2) **The null's best of 32.** By the director's ruling of 08:52:07Z a best over 32 (orientation x direction x checkpoint) is
a selection. The null is run_one_v2's: copies of the window displaced along the grid normal to the gap minima of the base
render (plus = shift by -|low|, minus = shift by +|high|; low -4.838, high +12.222 from evidence/reads/ours-A-S0-lattice),
each copy then shifted by the SHEET's own centring per direction (5.1795 forward, 1.2045 reverse, shifts.txt), rendered,
read in all 8 orientations x 2 directions x 2 checkpoints, scored on the same labels and the same common pixel rule as the
sheet (tools/read_null.sh, a copy of read_surface.sh with that one difference; score.py with variant names nullplus and
nullminus). Rows in control.csv; evidence/null-best.csv (tools/null_best.py): per copy and for both copies together, the
best k 4 ba of 32 (and of 64), beside the sheet's 0.6960. Reading: the sheet's best is a signal beyond selection only if it
exceeds the null's best of 32 (both copies) ; otherwise «not beyond the null's selection».

## Addition of 2026-09-29T09:55:41Z: the same null for sheet Bx S0

The null of the 09:13:32Z addition, unchanged, is also run for ours-Bx-S0 (its gap minima low -3.971, high +8.418 and its own centring from evidence/reads/ours-Bx-S0-lattice/shifts.txt), tools/read_null.sh ours-Bx-S0, summarised by null_best.py ours-Bx-S0. Afterwards, variants d, b2, b5, rotctl of ours-A-S0 resume (variants_A.sh from kept files).

## Addition of 2026-09-29T10:25:19Z: run_one_v2's label free statistic on our w016 sheets (director 10:22:18Z), before any number of it

Verbatim: «run the SAME label free statistic of run_one_v2 (both nulls, tile test, same window size about 20 mm or the
largest that fits) on our w016 sheets A and Bx, in their predicted orientation and in their best one, declared first. If it
says 'signal yes' there, the 0826 'no' is a real no at our sensitivity; if it says 'no' on known ink, the 0826 statistic is
blind and every 0826 'no' is void. Also finish Bx's null before quoting 0.7436 anywhere.»

- Code: `tools/run_one_v2_0139.sh`, a copy of ink-square-0826-seed2604/tools/run_one_v2.sh (sha256 cc043e6b... read at this
  time) with ONLY these changes: D and every output path in this study (evidence/labelfree/<SQID>/, scratch/labelfree/,
  log/labelfree/, images under scratch/labelfree/art); the raw volume PHerc0139 20250728140407 (s3 and https) and its cache
  directory name in the chunk listing; the orientation line: `sq.py orient` (0826's umbilicus) replaced by K and M given in
  the environment (FORCE_K, FORCE_M); `--scroll PHerc0139` in the test2 call; the PNG step (q.py png, which reads
  ink-square's own files) left out; summary_v2.py called from ink-square's tools with this study's evidence folder. The
  half pitch 7.5625 (0826's), the null rule (gap minima copies, else fixed half pitch), test2's code and thresholds, the 60
  cell margin, both directions and both checkpoints: unchanged, so the statistic is the same code.
- Window: a 20 mm square as on 0826 (S = rint(20 / step_mm) cells, step_mm = the sheet's cell size x 0.009362), centred on
  the centroid of the sheet's cells within 4 voxels of a clean label point, shifted inside the lattice if needed; if 20 mm
  cannot be placed inside the lattice, the largest square that can, size stated. `tools/labelfree_square.py` writes the
  square (corner, S, mm, share of the square's cells within 4 voxels of a clean label point) to evidence/labelfree-squares.csv.
- Orientations, both directions, both checkpoints each: A in its predicted k3 m1 (orient-rule.csv) and its best k2 m1;
  Bx in its predicted k3 m1 and its best k0 m0 (control.csv). The rows of interest are those of the direction the reading
  names (reverse for all four), the others reported beside.
- Output: evidence/labelfree/<SQID>/summary.csv (run_one_v2's form) gathered by `tools/labelfree_table.py` into
  evidence/labelfree-w016.csv, one row per sheet x orientation x checkpoint x direction, with the verdict line per sheet:
  «signal yes on known ink» if any row of the named direction says signal yes, else «no on known ink (the 0826 statistic is
  blind)». Stated with every row: the square holds labelled ink only on part of it (the share is a column).
- Order of work: Bx's null finishes first (running); then these four runs, one at a time, at most 2 inferences at once
  (run_one_v2 runs one inference at a time, 3 threads here). Variants d, b2, b5, rotctl wait.
