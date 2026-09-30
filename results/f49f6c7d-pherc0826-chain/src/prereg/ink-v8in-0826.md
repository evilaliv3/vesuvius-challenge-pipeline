<!-- Shipped copy of ink-v8in-0826/DECLARATION.md, 2026-09-30, as the study wrote it. Where it says PRIVATE, private or never public it describes how the study kept its own outputs on the day it was written, before the owner's decision of 2026-09-30 to publish this article with no position on the scroll. -->
# ink-v8in-0826: Youssef Nader's v8-in ink model read on the R2c squares of PHerc0826

Written 2026-09-29T19:16Z (`date -u` read at 19:15:13Z just before writing) by an agent of the coordinator. PRIVATE study:
PHerc0826 is a prize scroll; nothing of it leaves this machine except as the private Kaggle dataset allowed below, and
nothing enters any text before the director reads it. No number of the question exists yet: no model has been run.
Nothing below is retouched after the first number; additions are dated and declared.

## The order and its change of scope

Director 2026-09-29T19:10:51Z (owner's news): verify the facts of the release from the raw repo files, then (1) reproduce
his released prediction on a small part of his w062 surface (correlation at least 0.99), (2) calibrate on our w016 renders
of PHerc0139 (positive-control-0139) at offsets -4 to +4 in both depth orders, (3) only after (1) and (2) pass, read the R2c
squares of PHerc0826 seed6273 (29.8961 mm) and seed5364 (27.2369 mm), (4) GPU on Kaggle at most 8 h, private.

**Scope change, director 2026-09-29T19:12:48Z (the owner's word overrides the earlier order), relayed by the coordinator,
received before any model was run:** steps (1) and (2) are DROPPED. What was downloaded is kept and recorded in the ledger.
Only v8-in on PHerc0826: the R2c squares of seed6273 and seed5364, both depth orders (normal and --reverse, the right one is
unknown), the central 24 layers of our 28 layer renders, the gap minimum null copies read the same way, maps turned upright
with best-windows-0826's align.py (through the alignment render-routes-0826 made with it) and saved as PNG under this study
folder, PRIVATE. CPU if the model runs within an hour per square (one tile timed first, the timing in the ledger); otherwise
a private Kaggle kernel and private dataset, at most 8 GPU hours, the 0826 data deleted from Kaggle after. Each map is sent
to the coordinator the moment it exists.

**Therefore nothing in this study is calibrated.** There is no known reference run of this model on our machine and no
reading on known ink through our render path. The maps are only images to look at, never a claim of ink or of no ink. The
numbers beside the null copies are descriptive and decide nothing. If anything in a map looks like letters, nothing leaves
this machine, the work stops and the coordinator is told so the director tells the owner first (First Letters rule).

## The release, as read from the raw files (not a summary)

Read at 2026-09-29T19:12:05Z: `https://huggingface.co/api/models/YoussefMoNader/ink-8um-v8in?blobs=true`, saved as
scratch/hf/api-model.json (and api-tree.json). Downloaded at the pinned revision into scratch/hf/repo (all files except
training/r3d50_KM_200ep.safetensors, the Kinetics initialiser, not needed). Files read 19:13Z to 19:15Z.

- Revision (commit sha) `d89166b41a3f5fad7749b3d7c0fdd1bd3695d844`, lastModified `2026-09-28T20:28:56.000Z` (API JSON).
- Licence MIT: API `cardData.license` "mit" and tag `license:mit`; README front matter `license: mit` and its License
  section «Code and weights: MIT»; training data «CC BY-NC 4.0».
- Files: model.safetensors (333,532,180 bytes, LFS sha256 3b94548d... in the API JSON; the downloaded file's sha256 read
  3b94548d7f9b..., equal), ink8um/inference.py, ink8um/modeling.py, predict.py, config.json, training/ (code and recipe).
  Every file's sha256 goes to evidence/hf-files.csv (tools/hf_files.py), with the API's LFS sha beside where the API has one.
- Architecture: README «ResNet3D-50 encoder with a 2D U-Net decoder»; modeling.py docstring «ResNet3D-50 encoder + 2D U-Net
  decoder», Bottleneck blocks [3, 4, 6, 3]; depth collapsed by max over depth at each encoder level.
- Parameters: README table «83.4 M»; counted from the safetensors tensors by tools/hf_files.py (a row of hf-files.csv).
- Input: config.json in_depth 24, tile_size 64, clip_max 200, stride 21, reverse_layers false; inference.py clips uint8 to
  [0, 200] and multiplies by 1/255; modeling.py `nn.InstanceNorm3d(num_features=1, affine=True)` then trilinear upsample to
  96 x 256 x 256.
- Layers: inference.read_stack uses `layer_start = max(0, (len(files) - 24) // 2)` unless --layer-start is given (the
  central 24); `--reverse` flips the depth axis only (`stack[..., ::-1]`), never XY; README: «The depth order matters».
- Finetune: `YoussefMoNader/ink-8um-v8in-pherc1447-loo-w062` exists (API read 19:12Z: sha 2bf9f421862c..., lastModified
  2026-09-28T19:26:11Z, license mit), scratch/hf/api-finetune.json. Not downloaded.
- 1447 surfaces: dataset `YoussefMoNader/ink-8um-pherc1447-surfaces` (API: sha 7e4d918712a8..., lastModified
  2026-09-28T20:28:44Z, cardData.license cc-by-nc-4.0), scratch/hf/api-dataset.json. For step (1), before the scope
  change, only w062/layers/00..23.tif and w062/predictions/v8in.png were downloaded (570 MB, scratch/hf/ds1447; the README
  and SHA256SUMS in the include list did not arrive). Kept private, redistributed nowhere, not read by this study after the
  scope change.

## Inputs (asserted to exist and be non empty before each step; the assert tested once on a missing path)

- seed6273, R2c: the renders already made by run_one_v2.sh for render-routes-0826 (SQID rr-seed6273-squarecentre-R2cnative)
  in runs/rev1/ink-square-0826-seed2604/scratch/rr-seed6273-squarecentre-R2cnative/: r/forward-{sheet,plus,minus}.zarr and
  r/reverse-{sheet,plus,minus}.zarr (28 layers, 9.362 um, lamina centred per direction by tf.py delta, null copies at the
  gap minima of the base render; that study's evidence/.../shifts.txt, null.txt), window.tifxyz and window-mask.tif. Read
  only; nothing of that study is written. sha256 of each .zarr's .zarray and of window-mask.tif in evidence/inputs.csv.
- seed5364, R2c: no render exists. It is rendered here by `tools/render_r2c.sh`, a copy of run_one_v2.sh's steps up to the
  per direction renders (same renderer binary sha 8401cea2..., same flags, same window of 60 cells, same gap profile and
  null rule, same centring), with the patch file written by a copy of render-routes-0826/tools/ink_orient.py that writes
  into this study only. Size row first (signal_null.py chunks); refused if /data free minus the fetch bound would be under
  42 GB, and then the study reports and waits. Raw chunks it adds to the cache are listed and deleted after, with a row.
- Model: scratch/hf/repo at the pinned revision, loaded with `InkDetector.from_pretrained(<local dir>)`, code imported
  unchanged from the repo.
- Upright mapping: render-routes-0826/scratch/aligned-R2cnative-PHerc0826-seed{6273,5364}-squarecentre.npz (Q, valid,
  c0, S, written by its align_square.py through best-windows-0826 align.py's Field and resample_grid).

## The read (fixed now)

- Order «normal»: the forward centred render set read with reverse = False; order «reverse»: the reverse centred render
  set read with reverse = True (as run_one_v2 pairs the forward render with the forward read). Layers: the central 24 of 28
  (layer_start 2, the default of read_stack). The render zarr (28, H, W) is transposed to H x W x 28, clipped to [0, 200],
  exactly the uint8 path of read_stack; then `predict_stack` of ink8um/inference.py unchanged (coverage mask, stride 21,
  Gaussian blend). The window mask is not applied to the input; the coverage mask of his code decides the tiles.
- Per square 6 reads: {normal, reverse} x {sheet, plus, minus}. Output float32 probability map per read
  (scratch/pred/<sq>/<order>-<surface>.npy), same pixel grid as the render.
- Numbers (descriptive, decide nothing), `tools/describe.py` -> evidence/describe.csv, one row per square x order x
  surface: pixels scored (window mask and prediction count > 0), mean probability, share at or above 0.5, 99th percentile;
  and per square x order the sheet's mean and share over the larger of the two copies' (ratio columns). No verdict row.
- Upright maps, `tools/upright.py`: for every valid node Q of the aligned grid, the render pixel of the window whose 3D point
  (score_ink_0139.points_at on window.tifxyz) is nearest, taken if within 2 voxels; the probability of each read at that
  pixel; the centred square (c0, S) of the aligned grid, flipped so z is up. One PNG per square x order: panels raw texture
  (VAL of the npz, p1 to p99) | sheet | plus copy | minus copy, probability 0 to 1 in grey, holes white, 5 mm bar, the
  words «PRIVATE, not calibrated, not a claim of ink». Under scratch/png/ of this study only, never under outputs/.
- Compute: one tile timed on CPU (6 threads, nice 10) and a count of the tiles of one read; the extrapolated hours per
  square (6 reads) in evidence/timing.csv and the ledger. CPU if at most 1 h per square, else Kaggle.

## Kaggle (only if the timing says so)

Private dataset of the model repo and the renders' central 24 layers as uint8 arrays (no 0826 file anywhere else), private
GPU kernel built with ink-finetune-k1's make_kernel.py pattern, visibility read back by its visibility.py pattern before any
0826 file is uploaded (the dataset is created private and read back private). Hours from the kernel's own clock into
evidence/gpu-hours.csv; the sum over this study stops before 8 h. The dataset and the kernel outputs holding 0826 data are
deleted from Kaggle after the pull, with a ledger row. Credentials read from ~/.kaggle (KAGGLE_CONFIG_DIR) by the CLI only,
never printed, copied or uploaded.

## Load, disk, processes

At most 6 cores (torch threads 6), nice 10, long work as setsid runners with the PGID in the ledger, killed only by group.
TMPDIR=/data/tmp. /data at least 42 GB free, read with df before every download or render.

## Correction of 2026-09-29T19:16:29Z (a fact of the listing, not of the question)

evidence/hf-files.csv: SHA256SUMS of the 1447 dataset did arrive (8,974 bytes, size equal to the API's); only its README did
not. Every downloaded file's size equals the API's, and every LFS sha256 the API gives equals the file's (column
sha_matches_api). Parameters counted from model.safetensors: a row of hf-files.csv.

## Addition of 2026-09-29T19:18:40Z: the CPU timing, and the quick look (director 19:17:05Z), before any model output

evidence/timing.csv, first row (19:17:55Z): 8 tiles of the seed6273 forward sheet render at 6 threads, 5.4257 s per tile;
29,584 tiles in one full read at stride 21, so 44.6 h per read and 267.5 h per square of 6 reads. CPU is refused for the
full maps; they go to Kaggle as declared.

Quick look, verbatim in substance (director 19:17:05Z, relayed): on this machine's CPU, in parallel with the Kaggle route,
which remains the reading. Input: the central 15 x 15 mm of the R2c seed6273 square from its existing 28 layer render
(runs/rev1/ink-square-0826-seed2604/scratch/rr-seed6273-squarecentre-R2cnative, found there): the forward centred sheet
render r/forward-sheet.zarr for order normal and the reverse centred r/reverse-sheet.zarr for order reverse (as the full
read), central 24 layers. The square spans render pixels 60/s to (60 + 795)/s with s = 0.2487795 cells per pixel (window
margin 60 cells both axes, window.json); its centre is pixel 1839 on both axes; 15 mm = 15 / 0.037605 = 399 cells = 1,602
pixels; the crop is rows and columns 1038:2640. v8-in at tile stride 64 (about 9 times fewer tiles; a coarser map, said on
the PNG and in the ledger), both orders, up to 12 threads, nice 10, setsid, killed by group only. One tile timed first and
the estimate sent to the coordinator before the rest runs. No null copies in the quick look.
Upright: each valid node of render-routes-0826's aligned grid (scratch/aligned-R2cnative-PHerc0826-seed6273-squarecentre.npz,
best-windows-0826 align.py) takes the probability of the crop pixel whose 3D point (points_at on window.tifxyz) is nearest,
if within 2 voxels; the aligned nodes' bounding box of those matched is drawn, z up, holes white, 5 mm bar, labelled «v8-in
quick look, stride 64, uncalibrated, not a result» and the order. ; PNGs to
/data/scrollagent/outputs/artifacts/ink-map-0826/ (the director's location for the quick look; PRIVATE, never published,
never index.html). The match share and median match distance are columns of evidence/quicklook.csv.

Note of 2026-09-29T19:19Z on the addition above: the shell ate a tool name in backquotes when it was appended; the sentence
«; PNGs to ...» names the tool tools/quicklook_png.py. Nothing else changed.

## Addition of 2026-09-29T19:26Z: the Kaggle route in detail (before any Kaggle push)

- Dataset per square, PRIVATE: giovannipellerano/v8in-0826-s6273 (then -s5364), built by tools/pack_kaggle.py: the six
  renders' layers 2..25 as uint8 (H, W, 24) .npy, the model files of the pinned revision, SHA256SUMS (evidence/kaggle-pack.csv).
  Read back private by visibility (metadata and an anonymous request) right after creation; if it is not private it is
  deleted at once and the study stops.
- Kernels, PRIVATE, GPU T4 x2 (tools/kernel_template.py, make_kernel.py; tested locally on CPU on a synthetic 106 x 106 input
  before the first push): the dataset's files checked by sha256, then one worker per GPU running predict_stack unchanged
  (batch 16, fp16 autocast as his code does on CUDA, DataLoader workers 0), output float16 maps. To send maps as soon as
  they exist, a square is two kernels: «sheets» (normal on GPU 0, reverse on GPU 1) then «nulls» (plus and minus of each
  order). Each kernel carries a wall cap (no read starts after it); the caps are set so the sum of this study's sessions
  stays under 8 h, read from evidence/gpu-hours.csv (tools/pull.sh, the kernel's own clock) before each push.
- After the pull, tools/upright_full.py makes the upright PNG of each read (declared method: points_at nearest within 2
  voxels on render-routes-0826's aligned grid; the whole aligned square), and tools/describe.py the descriptive rows.
- After each square's last pull: the dataset and the kernels are deleted from Kaggle (kaggle datasets delete, kaggle
  kernels delete), a ledger row each; the local pack folder is listed to a file and deleted, with a row.

## Addition of 2026-09-29T19:28:19Z: his layer convention against ours, and the mapping (director 19:25:45Z), before any model output is seen

Read at 2026-09-29T19:26:33Z, raw file https://huggingface.co/datasets/YoussefMoNader/ink-8um-pherc1447-surfaces/raw/7e4d918712a8d8642a6fdeee45b80217c1e98317/README.md
(saved scratch/hf/ds1447-README.md, 6,861 bytes, sha256 48850f7562bc...). Lines quoted verbatim:
- line 58: «layers/00.tif … 23.tif     uint8 render, one layer per normal offset (−11.5 … +11.5 voxels, step 1)»
- lines 72 to 74: «**Layers:** `NN.tif` samples the volume at normal offset `NN − 11.5` voxels from the surface; layers are in ascending
  offset order. Both released models read them **reversed** (23 → 0): the finetune's config sets `reverse_layers: true`, and
  for the base model pass `--reverse`.»
- lines 43 to 45: «`v8in.png` comes from the v8-in base model ..., run with depth-reversed layers (`--reverse`).»
- lines 51 to 54: base v8-in AUC / AP «w058 0.862 / 0.693», «w060 0.810 / 0.677».
- line 75 and lines 91 to 92: tifxyz vertex (i, j) is render pixel (4i, 4j); «rendered into 24 native-L0 layers» with «the
  VC3D tools». The README does NOT say which way his normal points (towards the umbo or outwards), nor whether his render
  used --flip-normals.

(a) Our 28 layer renders. Tool: villa-tracer-build/scratch/build/bin/vc_render_tifxyz (sha256 8401cea2..., built from
villa-tracer-build/scratch/src/volume-cartographer, CMakeCache CMAKE_HOME_DIRECTORY), called by
ink-square-0826-seed2604/tools/run_one_v2.sh lines 54 to 56 with --num-slices 28 --slice-step 1 --scale 1 --flip-normals
--voxel-size 9.362 --pyramid 0 --group-idx 0. Offsets: apps/src/vc_render_tifxyz.cpp buildOffsetList (lines 354 to 370):
center = 0.5 (28 - 1) = 13.5, offset of layer zi = (zi - 13.5) x 1 voxel along the unit normal; layer 0 at -13.5, layer 27
at +13.5, step 1 voxel (gap_profile.csv of rr-seed6273 lists layer0 -13.5, layer2 -11.5). The normal: core/src/Geometry.cpp
grid_normal_int (lines 47 to 54) N = xv x yv with xv along the grid columns and yv along the rows; --flip-normals negates it
(vc_render_tifxyz.cpp line 301). The radial rule (ink-input-form/tools/orient_0826.py measure, lines 60 to 83, the same
cross product d/dcol x d/drow, side = sign of N . r against the published 0826 umbilicus) on the seed6273 window gives
side -1 with agreement 0.9304 (ink-square-0826-seed2604/evidence/orientation.csv row 33, direction «reverse»): N points
towards the umbo, so the rendered normal -N points OUTWARDS, and our layer index increases outwards (layer 0 is 13.5 voxels
towards the umbo). The villa comment at vc_render_tifxyz.cpp lines 1041 to 1048 says the opposite holds for a segment in the
standard orientation (with --flip-normals the stack grows towards the scroll centre); our grid is not in that orientation.
forward-sheet.zarr and reverse-sheet.zarr share that convention (the same renderer and flag); they differ only by the
lamina centring of run_one_v2: the window surface was moved by tf.py shift (ink-point-1447-trainform/tools/tf.py lines 85 to
96: P + dv (-N), i.e. along the rendered normal, outwards here) by dv = 3.9650 voxels for forward and -0.0100 for reverse
(ink-square-0826-seed2604/evidence/rr-seed6273-squarecentre-R2cnative/shifts.txt).
(b) The central 24 are layers 2 to 25 (read_stack's rule, (28 - 24) // 2 = 2), offsets -11.5 to +11.5 voxels, step 1,
about the surface the render was made from: exactly his offsets and step, and the same half voxel centring (no layer at
offset 0). The difference is the centring shift: about the tracer's own sheet surface, the forward-sheet render's 24 layers
span -11.5 + 3.965 = -7.535 to +15.465 voxels (outwards positive), the reverse-sheet render's span -11.49 to +11.51. Our
voxel is 9.362 um, his 8.640 um: 23 voxels are 215.3 um here against 198.7 um in his renders (ratio 1.0836).
(c) The mapping. His setting: layers ascending along HIS normal, read reversed, so the model's first input layer is the one
at +11.5 along his normal. Our read «normal» (forward-sheet, no --reverse) feeds first our layer 2, at 11.5 voxels towards
the umbo; our read «reverse» (reverse-sheet, --reverse) feeds first our layer 25, at 11.5 voxels outwards. Hence:
our «normal» read is his order if his normal points towards the umbo; our «reverse» read is his order if his normal points
outwards. His README does not say which. If his renders follow the villa convention quoted above (standard orientation,
--flip-normals: stack growing towards the centre), his normal points towards the umbo and **our «normal» read is his order,
our «reverse» read is not his order**; this is an inference from the villa comment, not a measurement of his files, and
every label says «his order (inferred from the villa convention, not measured)» or «not his order (same inference)».
A measurement is declared here and run next if the data can be had within the disk rule: his w062 tifxyz (30 MB,
CC-BY-NC, private) against a published PHerc1447 umbilicus gives the direction of his grid's d/dcol x d/drow; and his layers
00 and 23 compared, at a few hundred pixels, with the 1447 volume sampled at -11.5 and +11.5 voxels along that normal give
the sign his renderer used. Until then the labels carry the inference.
(d) The quick look: «normal» = his order (inferred), «reverse» = not his order (inferred); the PNG labels say so (the
quick look runner is not changed; quicklook_png.py, which runs after each read, gets the words before it runs).

## Addition of 2026-09-29T19:34:25Z: the Kaggle reading, centred as his renders (director 19:29:39Z), before any Kaggle number

Supersedes the Kaggle part of the additions above. The reading is made on renders centred on the traced surface itself,
with no lamina centring shift: 24 layers at -11.5 to +11.5 voxels, step 1, same renderer and flags (--flip-normals, voxel
9.362, same crop and pixel grid).
- seed6273: run_one_v2's base render r/base-sheet.zarr IS that render with 28 layers (the window tifxyz unshifted, 28 slices,
  offsets (zi - 13.5)); its layers 2..25 are offsets -11.5..+11.5 sampled at exactly the points a 24 slice render samples
  (buildOffsetList with 24 slices gives (zi - 11.5), the same offsets), so no new render is made: layers 2..25 of
  base-sheet.zarr. Asserted non empty and 24 layers after the slice, before the pack.
- The null copies without any centring step: the window displaced along the normal to the two gap minima of that base
  render (run_one_v2's copies before its centring: tf.py shift by -|low| and +|high|), rendered with the same flags and not
  shifted further: r/base-plus.zarr (low minimum -4.796 voxels, towards the umbo) and r/base-minus.zarr (high minimum +9.751
  voxels, outwards) (ink-square-0826-seed2604/log/rr-seed6273-squarecentre-R2cnative.txt 15:02:59Z), layers 2..25 each. The
  gap minima place the copies on the inter sheet gaps only; nothing moves the sheet.
- Reads: both orders on each of the three: «normal» (no --reverse) = his order (inferred from villa's normal convention);
  «reverse» (--reverse) = the other order. 6 reads for seed6273. Second arm, only if GPU time allows: the forward-sheet set
  (shifted +3.965) in both orders.
- seed5364: the same three renders are needed (base-sheet, base-plus, base-minus, rendered as run_one_v2 does, 24 or 28
  slices); its raw chunk fetch is about 4.6 GB (seed6273's size row) plus about 1 GB of renders, which the 42 GB floor does not
  allow now (/data 42 GB free at 19:33Z). It is sized by the size row and run only if the floor holds; otherwise reported.
- Labels on every map, PNG and CSV row, exactly: «his order (inferred from villa's normal convention)» or «the other order».

## Addition of 2026-09-29T20:22:24Z: his surface at our quick look's coarseness (director 20:20:58Z), the crop chosen before anything runs

Question (the owner, relayed): would Nader's own surface show characters at our quick look's stride 64? Answered on his w062
(PHerc1447, CC-BY-NC, private, scratch/hf/ds1447).
- Crop, chosen by eye on his released w062/predictions/v8in.png (4668 x 8864, the base v8-in, stride 21, --reverse) before
  any run: 15 mm at his 8.640 um voxel = 15 / 0.00864 = 1,736 px; six candidate 1,736 px boxes were viewed at 1/4 scale
  (scratch/w062/candidates.png, overview scratch/w062/v8in-thumb-grid.png); box A, rows 1300:3036, columns 1900:3636, is
  chosen: the brightest and most stroke like connected shapes of the six (no box shows legible letters in his base map;
  said here before our run). A copy of his crop: scratch/w062/his-v8in-crop-r1300-3036-c1900-3636.png.
- Run: tools/v8in_read.py on a 24 layer folder view of that crop, stride 64, --reverse, 6 threads, nice 10, setsid; the input
  is his layers 00..23.tif (asserted 24 files, non empty, crop inside their shape), read with his read_stack convention
  (uint8, clip 200) through a small driver tools/w062_quick.py that builds the (H, W, 24) stack from the crop of each layer
  and calls predict_stack exactly as v8in_read.py does. Starts only after the third 0826 quick look read (PGID 844120) ends
  and its PNG exists.
- Output: side by side PNG, his release crop (stride 21) | ours stride 64 --reverse, both probability 0 to 1 on one grey
  scale, labelled «w062 PHerc1447, Nader's surface; left his release stride 21, right v8-in stride 64 --reverse; private»,
  /data/scrollagent/outputs/artifacts/ink-map-0826/w062-stride64-vs-21.png (PRIVATE). One row of evidence/w062-compare.csv:
  Pearson correlation of the two maps on the crop (ours on his grid: same pixel grid, pixels covered by our tiles only),
  mean and share >= 0.5 of each (his png / 255).

## Addition of 2026-09-29T21:51:01Z: director 21:48:50Z (Nader's reading of the seed6273 maps), before any number of it

Relayed: «promising but no clear letters; the thicker strokes are lettery; run both sides of the segment (reverse the layers)».
(1) seed5364: the queued kernel v8in-0826-s5364-sheets (scratch/jobs/s5364-sheets.json) already reads base-sheet in both
orders, normal = his order (inferred from villa's normal convention) on GPU 0 and --reverse = the other order on GPU 1; not
changed. Labelled PNGs go also to outputs/artifacts/ink-map-0826/ under names of this study, with captions-v8in.txt; index.html
there is not this study's and is never written.
(2) Both faces of the sheet, seed6273: two new renders of the seed6273 window tifxyz moved along the rendered normal by +5.0 and
-5.0 voxels (tf.py shift, the same tool and sign as run_one_v2's centring: P + dv (-N), outwards positive here), no gap minima
step, rendered exactly as the base render (vc_render_tifxyz sha 8401cea2..., --num-slices 28 --slice-step 1 --scale 1
--flip-normals --voxel-size 9.362 --pyramid 0 --group-idx 0) but cropped to the aligned square's window part: render pixels
177:3501 on both axes (the square spans 241:3437, plus 64 px, one tile of context); layers 2..25 of each = offsets -6.5..+16.5
(+5, outwards face) and -16.5..+6.5 (-5, umbo face) about the traced surface. Read on Kaggle at stride 21 by the same kernel code;
the maps are padded back into the window pixel grid (zeros outside the crop) before tools/upright_full.py, which draws only the
square. Budget, fixed now: the study's cap is 8 GPU h; spent 1.142 h, running and queued about 5.8 h (s6273-nulls, s5364-nulls,
s5364-sheets), so about 1.0 h remains: ONE kernel, +5 and -5 in HIS ORDER (normal), one per T4, cap 70 min; the other order
of the two offsets is not run unless the hours read after the pulls allow it (a later dated line). Account: 19.26 h before
tonight (ink-finetune-k1 evidence/gpu-week.csv total 12.688 plus gpu-hours.csv 6.568; gpu_week.py itself failed on this
study's kernel logs, IndexError, so the sum is read from the two CSVs). Disk: the raw chunk fetch is sized first; it runs
only if free minus fetch minus renders stays at or above the floor in force; the chunks are listed and dropped after.
(3) Stroke view, a DISPLAY transform only, never used for a number: per full map, the square's probabilities stretched from
their p1 to p99.5 (over the square's matched nodes) to 0..255, clipped, then a Gaussian of sigma 2 px; upright, beside the raw
map and the texture; outputs/artifacts/ink-map-0826/strokeview-<map name>.png, labelled «stroke view: display stretch p1..p99.5
and Gaussian sigma 2 px, not a measurement». tools/strokeview.py.
(4) Null copies: the plus and minus maps are shown in the same raw and stroke views with the SHEET's stretch limits (its p1
and p99.5), so a stroke on the sheet can be told from one on the null layers.

## Addition of 2026-09-29T21:54:27Z: cap 9.5 GPU h and the other order at the faces (director 21:54:07Z), before the face pushes

The study's GPU cap becomes 9.5 h (the week about 28.5 of 30 h); after it, no more Kaggle GPU this week without the director's
word. Approved: the other order (--reverse) at +5 and -5, on the same two face renders (no new fetch), as a second kernel
(v8in-0826-s6273faces-other, cap 70 min) queued after the his-order face kernel (v8in-0826-s6273faces-his, cap 70 min).

## Addition of 2026-09-29T22:11:07Z: the depth order measured on w016 carried to seed6273 by the side sign (coordinator 22:0xZ), verified before any relabel or push

Read at 2026-09-29T22:11:07Z: selftrain-v8in-0826/evidence/order-0139.csv (tool selftrain-v8in-0826/tools/w016.py order): base v8-in on the
organisers' w016 surface rendered by positive-control-0139 (scratch/theirs/lattice/r/base.zarr), 171,693 clean held out pixels
(40,331 ink): «normal» ba 0.6798, AUC 0.7385 (chosen); «reverse» ba 0.4411, AUC 0.4556. Side signs there: theirs +1, ours A and
Bx -1 (positive-control-0139/evidence/orient-rule.csv, published umbilicus rows).
Verification, each link checked in the source:
1. Same renderer and flags. w016: positive-control-0139/tools/read_surface.sh lines 18 to 19 (binary sha 8401cea2...) and 44 to 46
   (--scale 1 --group-idx 0 --num-slices 28 --slice-step 1 --flip-normals --pyramid 0 --voxel-size 9.362), base.zarr rendered
   from $W/window.tifxyz unshifted (lines 33, 81, 101). seed6273: ink-square-0826-seed2604/tools/run_one_v2.sh lines 12 to 13
   and 53 to 58, the same binary sha and the same flags, base-sheet.zarr from the unshifted window.tifxyz. Layer offsets are
   therefore the same, (zi - 13.5) voxels (vc_render_tifxyz.cpp 354 to 370), along -N with N = d/dcol x d/drow
   (Geometry.cpp 47 to 54, flip at vc_render_tifxyz.cpp 301).
2. Same side sign. orient-rule.csv is written by positive-control-0139/tools/orient_rule_0139.py, which imports
   ink-input-form/tools/orient_0826.py measure unchanged (lines 9, 37) and runs it on scratch/<surface>/window.tifxyz, the tifxyz
   the base render was made from; seed6273's side (-1, agreement 0.9304) is from ink-square-0826-seed2604/tools/sq.py orient
   (lines 39 to 57), which calls the same orient_0826.measure on the window.tifxyz its base render was made from. measure:
   n = np.cross(xv, yv) with xv along columns and yv along rows (orient_0826.py lines 61 to 68), side = sign(n . r) against the
   scroll's axis (line 69): +1 when N points outwards. The two rules are the same function; only the axis differs (0139's
   umbilicus mapped by the label affine for w016, 0826's published umbilicus for seed6273).
3. Which layer v8-in sees first. Both reads take layers 2..25 (selftrain-v8in-0826/tools/st_common.py stack_in_order lines 134
   to 141, refusing unless start is 2 and depth 24; this study's v8in_read.load_stack) and «reverse» is st[..., ::-1] in both.
   w016, side +1: N outwards, rendered normal -N inwards, layer 2 is 11.5 voxels OUTWARDS; «normal» feeds it first. So the
   order measured on w016 = the outermost layer first. seed6273, side -1: N towards the umbo, rendered normal outwards, layer 2 is
   11.5 voxels towards the umbo and layer 25 11.5 voxels outwards; the outermost first is «--reverse».
Verdict: the transfer holds as a rule: on seed6273 the order measured on w016 is our «reverse» read, the map labelled «the
other order» until now; my earlier label «his order (inferred from villa's normal convention)» (on the «normal» read) was an
inference from a source comment and is contradicted by this measurement. It is a RULE carried by geometry, not a measurement
on PHerc0826: w016 is PHerc0139 at 9.362 um (scan 20250728140407), seed6273 is PHerc0826 (scan 20250821151701); the ba 0.68 is
on 0139's labelled region only.
Relabel, fixed now: «reverse» on seed6273 and seed5364 (seed5364 side read by the same rule before its labels change) is «the
order measured on w016 (normal on w016, side +1; --reverse here, side -1)»; «normal» is «the order not measured on w016
(reverse on w016, ba 0.44)». The old labels stay as a column (old_order_label) in the CSVs; files keep their names and get
new copies with the new labels in outputs/artifacts/ink-map-0826; captions-v8in.txt is rewritten; index.html is never touched.
Face kernels: the --reverse face kernel is pushed first.

## Addition of 2026-09-29T22:23:43Z: calibrating the 0826 ratio on known ink (director 22:21:42Z), declared before any number of it

The number to calibrate: seed6273, the order measured on w016 (--reverse), base render: sheet share >= 0.5 0.08415 against
plus 0.05438 and minus 0.05544, ratio to the larger copy 1.5179 (evidence/describe-v2.csv). Statistic S = share of pixels with
v8-in probability >= 0.5 on the sheet divided by the same share on a null copy; reported against the larger of the two copies
(the 0826 number's form), against each copy alone, and flagged by the layers each copy shares with the sheet's 24
(shared = 24 - ceil(|gap minimum offset|), a copy sharing more than 12 layers is written «NOT an independent null»).
0826 copies: plus 4.796 voxels (19 shared: NOT independent), minus 9.751 (14 shared: NOT independent by that rule either;
written so). The director's «against the 9.751 voxel copy alone» is a column for 0826; for w016 the column is each copy alone.
Known ink, PHerc0139 w016 at 9.362 um (positive-control-0139 renders; order by the side sign: theirs +1 -> normal, A and Bx -1
-> reverse, as order-0139.csv carries it):
- Pixel set: the clean held out label pixels matched to the render within 4 voxels (positive-control-0139/tools/score.py
  matched, k 4), the same pixels on sheet and copies (the copies share the sheet's pixel grid); also the whole window's
  covered pixels as a second row.
- Sheet and copies as run_one_v2 builds them, in the direction the order rule pairs with the read (forward render with the
  normal read, reverse render with --reverse, as on 0826 where the reverse set's centring is -0.010, i.e. the base render):
  A: lattice/r/reverse.zarr (centring +1.2045), nullplus/r/reverse.zarr (gap minimum -4.838), nullminus/r/reverse.zarr
  (+12.222). Bx: lattice/r/reverse.zarr (-0.2640), nullplus (-3.971), nullminus (+8.418). These renders exist
  (positive-control-0139 read_null.sh). Theirs: lattice/r/forward.zarr (centring -1.2690) exists; its copies do not: they
  are made here as read_null.sh makes them (the window tifxyz moved to the gap minima -10.829 and +5.316, then by the sheet's
  forward centring -1.2690, rendered with the same binary and flags), after a size row, under the 42 GB floor (37 only with
  the coordinator's word); chunks listed and dropped after.
- Differences from 0826, stated: the w016 sets carry run_one_v2's centring (up to 1.27 voxels), 0826's base set none (-0.010).
- No ink region of PHerc0139: none found on disk. The label sets under ink-labels-0139 and heldout-labels-0139 hold only
  inklabels and supervision masks (supervised pixels without ink are no ink pixels inside the written, labelled area); no
  file declares a region outside the written area, and no organiser statement of one is on disk. So no such row is made.
Stride and compute: GPU stride 21 if the study cap (9.5 h) holds: the tiles of the nine w016 reads are counted first and the
estimate at 0.135 s per tile is written in the ledger; the w016 kernel goes before the not-w016-order face kernel, which runs
only if hours remain. Otherwise CPU stride 64 for w016 AND the seed6273 square (w016 order, sheet and both copies), 6 threads,
nice 10, load under 22, so both sides share one stride. Output evidence/ratio-calibration.csv (tools/ratio_cal.py), one row
per surface x pixel set x stride, the 0826 row beside; PRIVATE, no text uses it.

## ENDED 2026-09-30T00:29:23Z

The study is closed. Final numbers are in the CSVs named in the final report (describe-v2.csv, ratio-calibration.csv, with its
correction row of 00:29:09Z, side-sign.csv, gpu-hours.csv 8.601 h, w062-compare.csv, quicklook-v2.csv). Nothing of it enters
any text before the director reads it. No process of this study is running. Kaggle: all 7 kernels and 4 datasets deleted
(ledger rows ink-v8in-0826-kernel-deleted-* and -dataset-deleted-*, read back empty at 00:28:05Z).
What stays PRIVATE, and where (all on this machine only):
- PHerc0826 maps, renders and texture: runs/rev1/ink-v8in-0826/scratch/ (pred/s6273, pred/s5364: probability maps; r5364/r and
  faces/r: our renders; png/: upright maps; kaggle-out/: pulled kernel outputs; quick/: quick look maps; kds/: pack listings);
  outputs/artifacts/ink-map-0826/: strokeview-*, v8in-quicklook-*, captions-v8in.txt, superseded-labels/ (PRIVATE, never
  published, index.html not this study's).
- PHerc0139 (w016) maps: scratch/pred/v8in-0826-w016cal; theirs' null copy renders: scratch/w016/.
- PHerc1447 (CC-BY-NC, Nader's dataset): scratch/hf/ds1447 (w062 layers, v8in.png, SHA256SUMS), scratch/hf/ds1447-README.md,
  scratch/w062/ (crops, our stride 64 map); outputs/artifacts/ink-map-0826/w062-stride64-vs-21.png. Redistributed nowhere.
- The v8-in model (MIT): scratch/hf/repo at d89166b4.
