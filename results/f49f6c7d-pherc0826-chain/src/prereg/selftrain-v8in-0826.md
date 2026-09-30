<!-- Shipped copy of selftrain-v8in-0826/DECLARATION.md, 2026-09-30, as the study wrote it. Where it says PRIVATE, private or never public it describes how the study kept its own outputs on the day it was written, before the owner's decision of 2026-09-30 to publish this article with no position on the scroll. -->
# selftrain-v8in-0826: head only self training of v8-in on PHerc0826 with automatic pseudo labels

Written 2026-09-29T20:41Z (`date -u` read at 20:41:31Z just before writing) by a study agent of the coordinator, on the
director's order of 2026-09-29T20:35:11Z (the owner's go). PRIVATE study: PHerc0826 is a prize scroll; nothing of it
leaves this machine, nothing goes into the September texts. No number of this study exists yet: no tile has been chosen,
no feature computed, no model run. Nothing below is retouched after the first number; additions are dated and declared.
If anything in any map looks like letters, nothing leaves this machine: the work stops and the coordinator is told.

## What is reused (read only, never written)

- Model and code: runs/rev1/ink-v8in-0826/scratch/hf/repo, HF revision d89166b41a3f5fad7749b3d7c0fdd1bd3695d844,
  model.safetensors sha256 3b94548d... (checked again here at load time into evidence/inputs.csv), MIT. Loaded with
  `InkDetector.from_pretrained`, modules imported unchanged. ink-v8in-0826/tools/v8in_read.py is imported for
  `assert_input` and `load_stack` (central 24 of 28 layers, layers 2..25, offsets -11.5..+11.5 voxels, clip 200, uint8).
- Its layer mapping: «his order (inferred from villa's normal convention)» = the base render read WITHOUT --reverse
  (order «normal»). All 0826 reads of this study use the base renders (window unshifted, no lamina centring) in that order.
- 0826 renders, 28 layers, vc_render_tifxyz sha 8401cea2..., --flip-normals, voxel 9.362:
  seed6273: ink-square-0826-seed2604/scratch/rr-seed6273-squarecentre-R2cnative/r/base-{sheet,plus,minus}.zarr, window.json
  (square cells 60..855 of a 914 cell window, S 795, 29.8960 mm), window.tifxyz;
  seed5364: ink-v8in-0826/scratch/r5364/r/base-{sheet,plus,minus}.zarr, window.json (S 725, 27.2368 mm), window.tifxyz.
  Each window is the R2c surface cut to the certified square plus 60 cells on every side (run_one_v2's margin). The ring
  between the square and the window edge IS the part of the R2c surfaces outside the squares that is already rendered with
  the same renderer and flags. No new 0826 render and no fetch is made: the disk allows none (/data 42 GB free at 20:35Z
  against a floor of 37).
- 0139: w016 labels, render and scoring from positive-control-0139 (scratch/labels-9362.npz, scratch/theirs/lattice/r/
  base.zarr, mask.tif and window.tifxyz, tools/score.py's `matched` and score_ink_0139.ba_auc); the label free 20 mm
  windows of our sheets ours-A-S0 and ours-Bx-S0 (positive-control-0139/scratch/labelfree/A-k2m1-best and Bx-k0m0-best:
  r/base-{sheet,plus,minus}.zarr, window.tifxyz, window.json), rendered by the same run_one_v2 path, 28 layers.
- Upright: render-routes-0826/scratch/aligned-R2cnative-PHerc0826-seed6273-squarecentre.npz (best-windows-0826 align.py) by
  the method of ink-v8in-0826/tools/quicklook_png.py (nearest 3D point within 2 voxels, z up, holes white, 5 mm bar).

## Compute: CPU (decided now)

The Kaggle quota is not exposed by the Kaggle CLI; ink-v8in-0826/evidence/gpu-hours.csv does not exist yet (its kernels are
running), ink-finetune-k1's file holds 6.568 h, and the director's figure is about 19.3 of 30 h used before tonight with up
to 8 more for the v8-in maps, so at most about 2.7 h could remain and only after those kernels end. Features are about
3.93 MB per tile in fp16 (below), so any Kaggle feature pass would have to come back through a disk that has 5 GB of room.
Therefore everything runs on this CPU: nice 10, setsid, PGID in the ledger, killed only by group. Threads: each runner reads
/proc/loadavg before every batch; others = load1 minus the threads my runners declare in scratch/threads-*.txt; room = 22
minus others; a runner takes min(3, floor(room / number of my active runners)) threads, and sleeps 60 s (logged) when that is
0. At most two runners at once (6 threads). The full model timing of ink-v8in-0826 (5.41 s per tile) is the planning figure.

## Encoder features (step 1)

- Frozen: InstanceNorm3d, trilinear upsample to 96 x 256 x 256, ResNet3D-50, max over depth: 4 levels per 64 x 64 tile,
  (256, 64, 64), (512, 32, 32), (1024, 16, 16), (2048, 8, 8), cached in fp16 (1,966,080 values, 3.93 MB per tile) ONCE, for
  training tiles only, under scratch/feat/<scroll>/ (one .npy per level per block of tiles). Evaluation passes (w016, guard b,
  quick look) are not cached: the encoder runs once and the base and tuned decoders read the same features in memory.
- Tile grid: his `tile_positions` rule on his `coverage_mask` of the 24 layer stack, stride 64 (non overlapping tiles).
- 0826 candidate tiles, per seed: every stride 64 tile of base-sheet whose 64 x 64 pixels are ALL (i) at least 1 mm on the
  surface from the seed's own square: distance in render pixels (Euclidean distance transform from the square's pixels,
  pixel (i, j) in the square when its grid coordinate s (i + 0.5), s (j + 0.5), s = the window tifxyz scale, lies in cells
  [60, 60 + S) on both axes) times the pixel size (s x STEP mm); and (ii) at least 1 mm = 106.8 voxels in the volume from
  every 3D point of BOTH squares (points_at on each window.tifxyz over all square pixels, stride 1, KD tree).
  Also required for the tile: inside base-plus's and base-minus's coverage as well (so the guard b tiles have all three).
- Split, fixed now: the candidates of each seed are shuffled by numpy default_rng(20260929); the first 50 are the guard b set
  (never in training); the next 240 are the training set (all, if fewer remain). So at most 480 0826 training tiles and 100
  guard b tiles. Proof written by tools/tiles_0826.py to evidence/exclusion-0826.csv: per seed and set, the tile count, the
  minimum surface distance (mm) and minimum volume distance (voxels, to each square) over ALL their pixels, and the count of
  pixels within 1 mm of either square: the bar is 0, asserted; a nonzero count refuses the step.
- 0139 region (guard a): the same rule on the two label free windows, with «the square» replaced by «w016»: w016 = every
  nonzero pixel of slice 10 of pherc0139-w016_supervision_mask.zarr (heldout-labels-0139 data, the whole labelled region,
  not only the clean held out part), mapped to volume 20250728140407 exactly as positive-control-0139/tools/map_labels.py maps
  the clean pixels (level 2 pixel (r, c) -> grid coordinate 0.05 (4r + 2), 0.05 (4c + 2) of the 2.399 um w029 tifxyz,
  bilinear, then the affine A stored in scratch/labels-9362.npz). A tile qualifies when all its pixels are at least 1 mm
  (106.8 voxels) in the volume from every mapped w016 point AND at least 1 mm on the surface from the window's w016
  footprint (render pixels whose 3D point is within 4 voxels of a w016 point; EDT times pixel size); an empty footprint is
  written as such. Shuffled by the same rng, 240 per window. evidence/disjoint-0139.csv, bar 0 pixels within 1 mm, asserted.
  If fewer than 160 tiles qualify over the two windows, guard a cannot be run as declared: the study stops and reports.
- Disk: 480 tiles are 1.89 GB per scroll, at most 3.8 GB with both caches. Before each block is written the runner reads df
  and refuses under 37 GB free on /data (plus the block's size). The 0139 cache is listed to a file and deleted after guard
  a; the 0826 cache after the study; each deletion with a ledger row naming its listing.
- Cut for time, fixed now: the runner times its first 32 tiles; if the projected end of all declared passes is after
  2026-09-30T05:30Z, the training sets are cut to 160 per seed or window (the first 160 of the same shuffled order); the
  guard sets, w016 tiles and the quick look are never cut. The cut, if any, is a ledger row and an addition here.

## Pseudo labels (step 2), fixed now

Per scroll and round, the current model's per tile sigmoid probabilities (raw tile output, no Gaussian blend; tiles do not
overlap at stride 64) on all pixels of all training tiles, pooled: t_ink = the 0.98 quantile, t_no = the 0.50 quantile
(numpy.quantile, linear). ink = p >= t_ink (the top 2 per cent), no ink = p <= t_no (the bottom 50 per cent), the rest
ignored. Round 1 labels come from the base model; round r + 1 from the model after round r. Thresholds and counts per
round in evidence/thresholds.csv.

## Training (step 3), fixed now

Decoder2D only (the three conv blocks and the logit conv, 2D), initialised from the base weights; the encoder is frozen by
construction (cached features). BatchNorm2d layers stay in eval mode (running statistics frozen); their affine weights
train. Loss: binary cross entropy with logits, unweighted mean over labelled pixels. AdamW, lr 1e-4, weight decay 1e-4,
batch 8 tiles, one epoch per round over the training tiles in an order shuffled by torch.Generator seeded 20260929 + round;
torch.manual_seed(0), numpy seed 0, torch threads as above. 3 rounds. evidence/loss.csv, one row per scroll and round: the
labelled pixel counts, the loss of the round's labels under the model at the round's start (before any step), the mean
training loss over the epoch, and the loss after the epoch (a second pass, no step). Weights per round in scratch/head/.

## Guard (a): 0139 (bar fixed now)

1. Depth order for 0139: the base model reads the w016 base render (theirs lattice r/base.zarr, layers 2..25) in both
   orders, normal and reverse. Pixels: the clean held out label points matched to a render pixel within 4 voxels by
   score.py's `matched('theirs', 'lattice', ...)`, and covered by a stride 64 tile (tiles with at least one such pixel).
   Prediction at each pixel = the raw tile probability as uint8 (round(255 p)); ba and auc by score_ink_0139.ba_auc (ba at
   uint8 >= 128), as score.py scores. One row per order in evidence/order-0139.csv. The order with the higher ba is used on
   w016 afterwards. It is carried to the label free windows by the side sign of positive-control-0139/evidence/orient-rule.csv
   (published umbilicus rows: theirs +1, ours-A-S0 -1, ours-Bx-S0 -1): where the sign differs from theirs, the other flag is
   used, so that the model's first layer lies on the same side of the sheet (towards or away from the umbo) as on w016. The
   label free windows are cut from sheet 0 of those same grids (window.json SHEET 0), so the sign is theirs.
2. Steps 1 to 3 as above on the 0139 training tiles, in that order.
3. w016 read by the base and by the tuned (round 3) decoder on the SAME encoder features, the same pixels, the same scoring.
   evidence/guard-a.csv: ba and auc of each, n pixels (ink, no ink), and the pass column.
   Bar: PASS when ba(tuned) >= ba(base) on the same pixels. Otherwise the study STOPS and reports (no 0826 map).
   A «not measurable» ba (under 2,000 ink or no ink pixels) is a stop, said so.

## Guard (b): 0826 null copies (bar fixed now)

The 100 guard b tiles (never trained), base-sheet, base-plus (low gap minimum, towards the umbo) and base-minus (high gap
minimum), order normal, one encoder pass each, base and tuned decoders on the same features. Mean raw tile probability over
all pixels of the tiles, per surface and model. d_sheet = mean_tuned(sheet) - mean_base(sheet); d_plus, d_minus the same on
the copies. Bar: PASS when max(d_plus, d_minus) <= d_sheet. Otherwise «guard b failing», reported. evidence/guard-b.csv.

## Step 5: the held out square, only when both guards pass

If guard (a) passes and guard (b) passes: seed6273 base-sheet.zarr, crop rows and cols 1038:2640 (ink-v8in-0826's quick
look crop, central 15 x 15 mm), order normal (his order, inferred), stride 64; one encoder pass, the base and tuned decoders
on the same features, each stitched with predict_stack's own rule (Gaussian blend divided by count), so the base panel is
the same computation as ink-v8in-0826's quick looks. Upright by quicklook_png.py's method; one PNG with panels raw texture |
base | tuned, labelled «self trained v8-in head, stride 64, uncalibrated, not a result, PRIVATE», z up, 5 mm bar, to
/data/scrollagent/outputs/artifacts/ink-map-0826/selftrain-seed6273-R2c-base-sheet-normal-his-order-inferred.png; a row in
evidence/quicklook.csv. Never index.html, never published. If guard (b) fails, no map is made unless the coordinator orders
it. The full map goes to Kaggle only if GPU hours remain; not planned tonight.

## Processes, files, ledger

setsid runners, nice 10, TMPDIR=/data/tmp, PGID written to log/<runner>.pgid and the ledger. Every input asserted existing and
non empty (v8in_read.assert_input), the assert tested once on a missing path (evidence/selftest.txt). Every number from a CSV
written by a tool under tools/ and read back before it is reported. Ledger rows appended with csv.writer, ten fields.

## Addition of 2026-09-29T20:49:05Z: tile counts from the selection, and the 0139 count equalised (before any model output)

tools/tiles_0826.py log (evidence/exclusion-0826.csv once its verify ends): the 1 mm ring left inside the rendered windows is
narrow; candidates are 228 tiles for seed6273 and 94 for seed5364 (106 and 209 covered tiles fell under 1 mm in the volume).
By the declared split the guard b set is 50 + 50 and the training set 178 + 44 = 222 tiles (the «all, if fewer» clause).
No new render or fetch is made to widen it: /data has about 5 GB above the 37 GB floor while render-routes-0826's R2d growths
write to the same disk, and the time budget is the same. tools/tiles_0139.py (evidence/disjoint-0139.csv): 511 and 952
qualifying 0139 tiles, 240 kept per window. So that guard (a) runs the same procedure with the same settings, including the
number of optimisation steps (one epoch per round, batch 8), the 0139 training set is cut to the same count as 0826's: the
first ceil(n / 2) of A's shuffled list and the first floor(n / 2) of Bx's, n = the 0826 training count (tools/cache.py). The
time cut clause (160 per seed) cannot bind below this and is dropped.

## Addition of 2026-09-29T20:55Z: the exclusion check (before any model output)

The first run of tools/tiles_0826.py refused at its own verify: its independent check counted pixels inside the square widened
by 1 mm as a Chebyshev box, which also takes pixels diagonal to the square's corners that lie farther than 1 mm (Euclidean) from
it (576 such pixels in seed6273's training set, all at 1 mm or more by the declared EDT and volume rules). The independent check
is now the analytic Euclidean distance from each pixel's grid coordinate to the square (box_mask in the tool), and the tool was
run again; the refused rows are kept in evidence/exclusion-0826-run1-refused-box-check.csv. Selection unchanged (same rng).

## Addition of 2026-09-29T20:55:21Z: the Chebyshev box check kept, its flagged tiles dropped (coordinator's order, 20:57Z)

Correcting the addition of 20:55Z: a failed check is not replaced with a looser one. The Chebyshev box check (square widened by
1 mm on every side in grid cells) is kept as the bar, and every tile it flags is dropped from its set with no refill, since the
sampling rule declared none (tools/box_drop_0826.py, evidence/box-check-0826.csv). It flagged 1 tile, in seed6273's training set;
the guard b sets are unchanged (50 + 50); training is 177 + 44 = 221 tiles, and the 0139 count follows (111 + 110). The analytic
Euclidean check of exclusion-0826.csv is kept beside it as information only. The chain_0826 launched at 20:54:41Z (PGID 993903)
was killed by group before any feature was written (it was waiting for load room) and is relaunched on the kept tiles.

## Addition of 2026-09-29T22:09Z: guard (a) failed, the study stops (results are in the CSVs; this only records the stop)

evidence/guard-a.csv ends in «FAIL: tuned below base, study stops». As declared, nothing of the 0826 square was read and no map
was made. chain_0826 was in guard (b), past its sheet and plus copy reads; it was killed by group (PGID 994197) before
guard-b.csv was written, so guard (b) has no verdict. Both feature caches were listed (log/feature-cache-deleted-2026-09-29.txt)
and deleted. The decoder weights per round stay in scratch/head/. CPU wall hours: evidence/cpu-hours.csv.
