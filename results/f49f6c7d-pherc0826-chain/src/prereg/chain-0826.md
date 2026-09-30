# chain-0826: the delivery chain moved to PHerc. 0826, inputs checked and the chain declared

Written 2026-09-26T08:32:21Z (`date -u`), before any number of this study exists. Owner's decision relayed by
the director at 2026-09-26T08:25:26Z (director.md section 5, ledger row `move-to-pherc0826`): the chain moves
from PHerc1447 to PHerc0826 (First Letters list, volume 20250821151701, surface prediction m7 on disk). This
study does parts (2) and (3) of that order: the inputs checked, then the chain declared. **Nothing grows here
until the director reads this file and says so.**

## Part 1: the input check, bars first

What is already known and reused, not re measured (each read from its CSV, cited):
- The prediction on disk: `data/datasets/PHerc0826/` (`manifest.json`, `chunks.txt`, level 0 in `0/`), fetched
  2026-09-20 by `fetch-two-eligible/tools/fetch.sh` (ledger 2026-09-20T15:25:13Z).
- `field-0826-0800/OUTCOME.md` (2026-09-24): 0826 publishes no surface (no `segments/` in the bucket, no
  spiral output, Miller and Müller publish renders and crops, no mesh); the umbilicus json was fetched there
  into `field-0826-0800/scratch/`.
- `umbilicus-1447/evidence/reference-0826-summary.csv`: the house umbilicus estimator against the published
  0826 umbilicus (the 2.7747 mm median quoted in the ledger of 2026-09-21T16:22:31Z).
- `first-light-0826-reference/evidence/reference.csv`: Miller and Müller's First Light on the same volume
  (window z 10,000 to 11,000, windings w010 to w065, no x/y box published, umbilicus «sean (bruniss)» 49
  points z 1941 to 16262). An external reference, declared as one, never a result of this study.

The tool is `tools/check_inputs_0826.py`, new: the lab's `check_dataset.py` was in the old home, deleted on
2026-09-20 (CLAUDE.md), and has no successor on disk (ledger grep «check_dataset», last row 2026-09-17). It
runs at nice 10 with at most 4 worker processes. One CSV per check under `evidence/inputs/`, each naming the
tool in its first line, and one verdict CSV `evidence/inputs/verdict.csv`, one row per check plus one overall.
Each check runs on **PHerc1447 beside 0826** where the same quantity exists for it, as the known reference.

The checks and their bars, fixed now:

- **I1 voxel.** `samplePixelSize` read from the organisers' `metadata.json` of the 0826 masked volume on the
  open bucket, converted to micrometres; beside it the value in the volume's key name, the house manifest
  (`pipeline/datasets/voxel.py`), and Miller and Müller's quoted 9.362. Pass: all four equal to four
  decimals. Reference: the same read on 1447 must give 8.640. The chain's compiled `VOXEL_SIZE 9` is written
  as a row with whether any compiled source other than `parameters.h` uses it (it must not, or it is a fail:
  the lab once used 9.0 in place of 9.362).
- **I2 shapes and levels.** The published prediction level 0 `.zarray`, the local one, and the masked volume
  level 0 `.zarray`: shape equal on all three (a prediction voxel is a raw voxel), prediction uint8 blosc
  chunks 192, raw uint8 uncompressed C order (what `seed_rule_check.py` requires). The level the chain reads
  (`SIMPAPER_SURFACE_ZARR` = the local level 0) and the level the seed rule reads (raw level 0) written as rows.
- **I3 manifest.** The bucket's listing of the prediction level 0 taken again now: key count, total bytes,
  listing sha256 in the manifest's form, against `manifest.json` and `chunks.txt`. Pass: equal. Then every
  listed chunk on disk with its listed size, and md5 of every local file against the listed ETag (single part
  ETags are the md5). Pass: 0 missing, 0 size differs, 0 md5 differs, 0 local files not listed.
- **I4 decode.** 400 listed chunks drawn with `numpy.random.default_rng(20260926)` decoded by zarr: each gives
  a 192 cubed uint8 block (edge chunks their clipped shape). Pass: 400 of 400. A chunk outside the listing is
  «absent»: the reader returns the fill value 0, which is «not measurable» for the chain, never «empty
  papyrus»; the count of grid cells not listed is written, not judged.
- **I5 coverage against the volume.** Raw masked level 5 (scale 32) and prediction level 5, fetched whole from
  the bucket (both 529 by 256 by 256). The scroll mask is raw above 0. Rows: share of predicted voxels (level 5
  above 0) inside the mask, in the right frame and with x and y swapped (the frame control of `field-0826-0800`);
  share of mask voxels whose level 0 prediction chunk is listed; the z range of the mask and of the listed
  chunks. Bar, both scrolls: predicted in mask at least 0.95 in the right frame and at least 0.20 lower in the
  swapped one; listed chunks cover at least 0.90 of the mask. 1447 is the reference that must pass.
- **I6 umbilicus.** The published json fetched again: sha256 against the copy of 2026-09-24, the object's
  LastModified, the count of points and the z range against Miller and Müller's «49 points, z 1941 to 16262».
  Every point inside the volume; z strictly increasing; the fraction of points whose (x, y) at level 5 lies in
  the scroll mask's slice (right frame and swapped). Bar: sha equal, 49 and 1941 to 16262 equal, all inside,
  increasing, in mask at least 0.90 right and the swapped frame lower. The z band the chain may seed in is the
  umbilicus z range intersected with the mask's z range; written as a row. The house estimator's distance to it
  (`reference-0826-summary.csv`) is read back as a row, not re measured.

**Verdict.** «inputs hold» only if I1 to I6 pass on 0826 and every 1447 reference row passes. Any failure is
named in `verdict.csv` and the chain part below does not run on that input.

## Addition of 2026-09-26T08:39:24Z: I5 failed as declared on both scrolls, its reference included; what was seen and one read back, labelled post hoc

`tools/check_inputs_0826.py` ran 08:34Z to 08:37Z (`log/check-inputs.txt`). I1, I2, I3, I4, I6 pass on 0826 and on
every 1447 reference row. **I5 fails on both scrolls**: predicted voxels inside the raw mask at level 5 are 0.3935
on 0826 and 0.5335 on 1447 against the declared 0.95 (`evidence/inputs/i5-coverage.csv`). Since the reference fails
too, the bar was wrong about both scrolls, not a fault of 0826's copy; the verdict row stays «no» as written and is not
rewritten. Seen by hand at 08:38Z (not a number of this study until the tool below writes it): at z 8320 of 0826, the
predicted voxels outside the level 5 mask lie a median of about 10 level 5 voxels outside it, and the raw level 0
chunks under them answer 404 (masked away). So the m7 prediction marks surface where the organisers' mask removed
the scan: the case the seed rule's raw grey test was written for (seeds 38, 40, 11 of 1447).

Declared now, **after** I5's numbers were seen, so post hoc and labelled so: `tools/i5_readback.py` writes
`evidence/inputs/i5-readback.csv`: (a) on each scroll, 20 predicted level 0 voxels outside the level 5 mask drawn with
`default_rng(20260926)` from the slices of the mask's middle z, and the raw level 0 chunk status under each (present,
absent); (b) 1447's raw grey pass share over every row of `seeds-at-scale-1447/evidence/seed-rule.csv`, beside
1447's predicted in mask share, and the ratio carried to 0826 as the expected raw grey pass share of its draws (a
sizing figure for the draw, not a bar). The mask z ranges of `i5-coverage.csv` end at the level 5 edge (16927 on
0826, above the level 0 shape 16920): a cosmetic clip, noted, not rewritten.

## Part 2, written 2026-09-26T08:53:42Z: the chain on 0826, declared before any 0826 seed is drawn

No 0826 seed, ladder row, growth or sheet exists when this is written. Numbers quoted here come from the CSVs named beside
them. Five things were run before this part, all references or checks, none a chain number of 0826: the input check
(part 1), `tools/i5_readback.py`, `tools/draw_reference.py 0` (`evidence/draw-reference-check.csv`: this study's draw
tool on PHerc1447 gives seeds-PHerc1447.csv header plus 50 rows byte for byte, stage1_candidates 1758034915 and rng
20260920 equal; this study's seed rule tool gives villa-tracer-build's rows for 1447 seeds 38, 40, 11), `tools/a2_cluster_seed.py
--reference PHerc1447-seed1393` (`evidence/a2-cluster-reference.csv`: 70 of 70 equal to map-1447), and
`tools/disk_plan.py` (`evidence/disk-plan.csv`).

### The seed rule (seeds-at-scale-1447's rule, and what differs on 0826)

A seed is a voxel of the 0826 prediction (level 0, local) that (1) is 255 with its six face neighbours at 255, (2) lies on
raw grey in the masked scan `PHerc0826/volumes/20250821151701-9.362um-1.2m-113keV-masked.zarr/0` (nearest voxel non zero
and present; a 404 is masked away; a failed fetch is «not measurable»; all three fail), and (3) sits in a prediction chunk
(192 cubed) with at most 0.5 of its voxels at 255. The candidates and the draw are `draw_seeds.py`'s: the stride 4 chunk
lattice, chunk interiors, `numpy.random.default_rng(20260920)`, one index at a time, repeats redrawn. The **rule set** of
0826 (the analogue of 1447's rule-50) is every delivered seed with `passes_rule` yes; its union is the headline, the
all-seeds union beside it.

Differences, each because an input differs:
- the scroll, the prediction and the raw volume are 0826's (I2: same shape 16920 x 8169 x 8169, raw uint8
  uncompressed 128 cubed chunks);
- the first batch has no earlier draw to compare a prefix with: its known reference is `tools/draw_reference.py` (above),
  run again by `tools/refill.sh 1 400` before the seed rule and written to `evidence/draw400-prefix-check.csv`;
- the reference columns of the seed rule tool (`ref_seed_chunk_share`, `ref_seed_block_check`) name no 0826 seed and
  read «not listed»; the tool's own reference is the 1447 three, which passed;
- **no z band is added**: 1447 had none. A seed outside the umbilicus z range (1941 to 16262) is drawn and grown as any
  other; its axis based columns (certificate, orientation) are «not measurable» there, never filled;
- sizing only, not a rule: 0826's expected raw grey pass share is 0.3031 against 1447's measured 0.4109
  (`i5-readback.csv`), and 1447's latest ladder kept 87 survivors of 616 classified (`seeds-at-scale-1447/evidence/ladder-v10.csv`).
  So the first wave draws **400** (about 121 passing, about 17 survivors if 0826 behaves as 1447; not a bar).

### The ladder and the deliveries

- **Ladder**: 120 s, `simpaper10 g 36000`, rc 124 at the cap = survivor, «no patch written», «ended by itself» as on
  1447; grown with the per seed build of the variant `unchanged` in `scratch/bin-ladder/` (the delivered series; it differs
  from 1447's corrected ladder builds only in the c stage, which a 120 s growth never runs). Survivors to
  `evidence/queue.txt`, delivered lowest chunk share first.
- **Deliveries**: `tools/run_seed.sh` (run_seed_v6.sh's route: growth g 36000 with no time cap, then c, l, vm 10, hm 10,
  fm 30 10 under the downstream cap from rel.csv, SIMPAPER_PATCH_LIMIT 40000), with the settings of
  `scratch/deliver-settings.env`: SIMPAPER_SHARED_CHUNKS 128 (= CAP_CHUNKS), SIMPAPER_FORCE_THREADS 1, OMP_WAIT_POLICY passive,
  OMP_NUM_THREADS 3 (their identity evidence is 1447 seed1111's, growth-memory-1447, a property of the binary, checked by
  the parser at every start), quiet window 2026-09-26T23:30:00Z to 2026-09-27T03:15:00Z with no growth started less than
  5400 s before it (the longest 1447 growth took 4475 s), FLOOR_GB 20, CORES_BUSY_MAX 20, FREE_MIN_GB 30 (director's
  order of about 08:5xZ, 46 GB free, cleanup pending), HOLD_GB 900, STUDY_MAX_GB 40, BUILD unchanged.
- **The build** (director's note of the morning): the variant is the settings key BUILD, one of `unchanged`,
  `flathash` (HF3's binary), `flathash+avx512` (HV3's), built per seed by `tools/build_variant_seed.py` into
  `scratch/bin-<BUILD>/<seed>/`, each seed's point compiled in; the tree of a variant is accepted only if it rebuilds 1447
  seed1111's known binary sha (unchanged 3fb3e87e, flathash ddfaa0c3, flathash+avx512 0c03fd19) and, for unchanged, its
  stock equals seeds-at-scale-1447's delivered stock; the patches are pinned by sha256; `run_seed.sh` checks the binary's
  sha against its gate row at every start. **Now `unchanged`**; the director's order puts HF3 against HV3 in tonight's
  window. A change to another variant needs its ledger settings row and **the identity bar on the first three seeds**:
  each grown with the variant and with `unchanged`, trees and sheets byte identical (`evidence/identity-0826-summary.csv`,
  written by a tool declared then); the runner refuses a variant without it.
- **One runner, one stop file, one settings file**: `tools/deliver.sh` (seeds-at-scale-1447's deliver.sh, changes G1 to
  G7 in its header), `scratch/deliver.stop` (read by the runner, `tools/ladder.sh` and `tools/refill.sh`),
  `scratch/deliver-settings.env` (its sha needs a ledger row `chain-0826-deliver-settings`, `tools/settings_row.py`).
  Order of a launch: `tools/refill.sh 1 400` (draw, reference, seed rule, ladder), then `tools/deliver.sh`; the runner
  refuses without a draw, the seed rule rows, the a2 reference, and inputs verdict rows I1 I2 I3 I4 I6 passing on 0826.
  No batch beyond draw 400 without the director (G4).

### What each delivered seed gets, and the bars, written before any number

- **Square**: `seed-search-1447/tools/square.py` unchanged through `tools/measure_seed.sh`, voxel read from the 0826
  manifest (9.362, I1); `square_mm_min_step` per sheet, and the square on covered cells at 1 voxel beside it (covered
  share at 1, 3, 5 voxels against the 0826 prediction) by coverage-union-1447's union tool, copied, after the wave.
- **a2**: `tools/a2_cluster_seed.py` per seed, T* 25 degrees and S 101 **carried, not recalibrated**: the negatives that
  set them are PHerc0139 w035 and w040 (9.362 um, the voxel of 0826, the same m7 prediction family; verdict.csv and
  cluster-calibration.csv of lamina-crossing-detect and lamina-crossing-map-1447), and 0826 publishes no surface to serve
  as a negative (field-0826-0800/OUTCOME.md). Checked on 0826 as information only: the flagged share distribution of the
  wave's sheets beside 1447's 550.
- **v2 crossing map**: `sheet-crossing-map-1447/tools/sheet_cross_v2.py` unchanged over the pairs of 0826 sheets after
  the wave; L2_cross 1572.923 and L2_jump 133.631 voxels **carried in voxels**, since both were set by PHerc0139 pairs
  (`v2-thresholds.csv`), 9.362 um as 0826 (14.73 mm and 1.25 mm).
- **Orientation**: orientation-1447's `orient.py` algorithm (z direction from the lattice, side from the axis, reliable
  only with axis share at least 0.99 and side agreement at least 0.90), with the axis of 0826 taken from the published
  umbilicus (I6), interpolated linearly between its 49 points and «not measurable» outside z 1941 to 16262; the house
  estimator's distance to it (umbilicus-1447 reference-0826) quoted beside, not a correction. Its self test on w035 must
  still return the identity.
- **External reference, not a result**: Miller and Müller's First Light window on the same volume, z 10,000 to 11,000,
  windings w010 to w065 of their fit (unpublished, so the windings cannot be placed; only the z window can), where their
  preregistered reading found no letters (`first-light-0826-reference/evidence/reference.csv`). Any ink reading of ours in
  that z window is written with their null beside it.

**Bars of the first wave**, against 1447's own numbers from seeds-at-scale-1447's DECLARATION (median of the ten 9.2948
mm, best 12.7244 as delivered and 6.2101 on covered cells, spread 2.6213 mm):
- B1, the chain works on 0826: the median `square_mm_min_step` of the wave's best sheets per seed at least 9.2948 minus
  2.6213 = 6.6735 mm; below that, «the chain delivers smaller squares on 0826», stated.
- B2, a lead for ink: a sheet with a square of 20 mm or more as delivered whose a2 cluster rule square is also 20 mm or
  more (the owner's 4 cm2 of one region); none, said as none.
- B3, crossings: the share of cells removed by the a2 clusters over the wave's union, beside 1447's rule-50 figure; no bar.

### Disk plan (`evidence/disk-plan.csv`, 08:5xZ)

/data 983.2 GiB, 41.6 free, 18.8 free at the 98 per cent brake, so **22.8 GiB before the brake** now. A delivered 1447
seed took a median 2,846 MiB (growth plus C40), largest 8,298 (145 seeds); a ladder run 4.53 MiB; a raw chunk 1.05 MiB.
The first wave: 400 raw chunks (about 0.4 GiB), about 121 ladder trees (about 0.5 GiB), then deliveries while this study
plus one largest seed (9 GiB) stays under STUDY_MAX_GB 40 and /data keeps FREE_MIN_GB 30 free. **With 41.6 GiB free and a
floor of 30, the runner has room for about 11 GiB of deliveries, about 3 or 4 seeds, before it holds**; the 40 GB wave
needs the owner's cleanup list first. The ladder has its own start line (FREE_MIN_GB) and the 98 per cent brake.
- 2026-09-26T13:13:51Z: launched by the owner with /data/scrollagent/lancia-0826.sh after the quiet clock (verdict: HV3 wins beyond the spread). I5 is descriptive, not a gate: its bar failed its own reference (1447 0.5335), the predicted voxels outside the mask sit on masked raw chunks, which the seed rule's raw grey test filters. BUILD at launch: flathash+avx512.
- 2026-09-26T13:30:59Z: (item 86 (c), director 13:30:29Z, owner's ok) the growth trees of every 0826 seed are KEPT, not removed after delivery, for the organisers' 9 um ink recipe when it is released; the disk plan reads this. (item 86 (b)) every 0826 square of 20 mm or more is read by the published checkpoints with the void null, numbers only, as squares arrive. Written by the coordinator; the chain is not running at this time (first launch stopped at refill, see the ledger).
- 2026-09-26T17:27:14Z: (director 16:17:03Z, «the one object build») tools/build_variant_seed.py now builds a seed by recompiling only simpaper10.o and linking against the tree's other 18 objects, when the tree's base key (parameters.h without the SEED_X/Y/Z lines, written after a full make) equals the new parameters.h minus those lines and no other .c/.cpp/.h/.hpp names SEED_X/Y/Z; otherwise, on BUILD_FULL=1, or when make compiles anything but simpaper10.cpp, the full make is the fallback. The known reference build of a tree is always full; the mode is a gate row build_mode. Checked before it was put in place by tools/build_objects_check.py in scratch/objects-check (never the chain's tree): evidence/build-objects-check.csv, variants unchanged, flathash, flathash+avx512, seeds 01 to 04 of the draw400, seed01 full (the base for 0826's shape), seeds 02 to 04 objects_only with sha256 equal to a full make of the same seed, 12 of 12 equal, tree gates pass, verdict PASS, on the tool sha256 af9f74a5... now in place; the previous version kept as scratch/next/build_variant_seed.before-objects-only-20260926T172701Z.py (sha256 0afdc02f...). Moved in with one mv while no launch_chain.sh, refill.sh, deliver.sh or ladder.sh ran. Measured saving (nongrowth-profile-1447, 1447 seed1111): 3.11 against 19.73 CPU s per build.
- 2026-09-26T17:52:05Z: launched by the owner with /data/scrollagent/lancia-0826.sh after the quiet clock (verdict: HV3 wins beyond the spread). I5 is descriptive, not a gate: its bar failed its own reference (1447 0.5335), the predicted voxels outside the mask sit on masked raw chunks, which the seed rule's raw grey test filters. BUILD at launch: flathash+avx512.
- 2026-09-26T18:16:06Z: launched by the owner with /data/scrollagent/lancia-0826.sh after the quiet clock (verdict: HV3 wins beyond the spread). I5 is descriptive, not a gate: its bar failed its own reference (1447 0.5335), the predicted voxels outside the mask sit on masked raw chunks, which the seed rule's raw grey test filters. BUILD at launch: flathash+avx512.

## Addition of 2026-09-26T18:58:51Z: seed rule v2, from batch 401 on (director 18:57:00Z), declared before its check runs

Written by a coordinator agent on the director's order of 18:57:00Z, after chain-0826-ladder-diagnosis (its
`evidence/ladder-early-stop-bins.csv`: on 0826 no cap survivor outside the umbilicus z range or above chunk share 0.30;
on 1447 87 of 87 ladder-v10 survivors at chunk share at most 0.30; both cuts were read after seeing the data, post hoc).
**Batch 1 to 400 is not re judged**: its seed-rule.csv rows, ladder and queue stay as they are.

From the batch starting at draw 401, a seed is a seed when the three tests of part 2 hold **and**:
- (4) `test_z_in_umbilicus_band`: seed_z within the published umbilicus z range, read from
  `evidence/inputs/i6-umbilicus.csv` row `seed_z_band_level0` (1941..16262), ends included;
- (5) `test_share_at_most_0_30`: pred_chunk_share_255 (the same exact fraction as test 3) at most 0.30.

Written by `tools/seed_rule_check_v2.py` (new file; `tools/seed_rule_check.py` untouched). Its rows in
`evidence/seed-rule.csv` keep the 21 columns unchanged (so tools/ladder.sh and tools/deliver.sh read them without any
edit), with `tool` = `chain-0826/tools/seed_rule_check_v2.py` and **passes_rule = tests 1 to 5**; tests 4 and 5 and
`passes_rule_v1` (tests 1 to 3) are columns of a sidecar `evidence/seed-rule-v2-tests.csv`, one row per seed of the same
group, written in the same run. The refill that calls it is `tools/refill_v2.sh` (a copy of tools/refill.sh changed
only on the seed rule step), put in place of tools/refill.sh by the director's switch, never while a refill runs.

The checks, before the switch, by `tools/seed_rule_v2_check.py` into `evidence/seed-rule-v2-check.csv`:
- R1, the 1447 reference: every ladder-v10 attempt of seeds-at-scale-1447 with outcome «still growing at the cap»,
  its seed-rule.csv row, tests 4 and 5 by the v2 code, the z band being the z range of the rows of
  umbilicus-1447/evidence/umbilicus-1447.csv with an axis (the house estimator: 1447 publishes no umbilicus; labelled
  so). Pass: every survivor kept (the director's 87 of 87).
- R2, 0826 batch 1: every cap survivor of evidence/ladder.csv group batch-1-400-0826 kept by the v2 tests. Pass: all.
- R3, descriptive, no bar: the 400 draws of batch 1 under v1 and v2 (passing counts, and how many fail test 4, test 5).
- R4, the tool's own reference: seed_rule_check_v2.py run on 10 batch 1 seeds (the first 10 of the draw, raw chunks
  from the cache, written to a scratch file, never to evidence/seed-rule.csv) must give the 21 columns of the existing
  rows equal except `tool`, `passes_rule` equal to passes_rule_v1 AND tests 4 and 5.

## Addition of 2026-09-26T19:03:06Z: the identity bar of G6 for BUILD flathash+avx512, declared before any of its growths

Written by a coordinator agent on the director's order relayed at about 19:0xZ, after tools/deliver.sh refused at
18:57:56Z under G6 (log/deliver.txt): the settings file carries BUILD flathash+avx512 and cap 512 since the owner's launch,
and `evidence/identity-0826-summary.csv` did not exist. No growth of any variant exists on 0826 when this is written.

- **Seeds**: the first three of `evidence/queue.txt` in the runner's order (lowest pred_chunk_share_255 first, as
  deliver.sh's next_seed takes them): PHerc0826-seed109 (0.0751), PHerc0826-seed300 (0.1298), PHerc0826-seed43 (0.1333).
- **Arms**: each seed built per seed by `tools/build_variant_seed.py` as `flathash+avx512` (into
  `scratch/bin-flathash+avx512/`, gates `evidence/gates/binary-gate-flathash+avx512-<seed>.csv`) and as `unchanged`
  (`scratch/bin-unchanged/`, gates `binary-gate-unchanged-<seed>.csv`); both grown `g 36000` with the settings file's
  environment as tools/deliver_settings.sh exports it (SIMPAPER_SHARED_CHUNKS 512, force threads 1, passive, OMP 3), no
  time cap, then c, l, vm 10, hm 10, fm 30 10 with SIMPAPER_PATCH_LIMIT 40000 on a copy of the growth tree, each arm with
  its own binary, as tools/run_seed.sh does. Into `scratch/identity/<variant>/<seed>/` (never `out/`, never
  `evidence/runs/`: these are not deliveries). Six growths at once, nice 10, if MemAvailable minus 6 GB per growth stays
  above the house floor of 20 GB at each start (cap 512 peak 5586884 kB, growth-memory-1447 summary-cap.csv).
- **The bar**: per seed, the growth trees (every patches/ file and rel.csv) byte identical by
  growth-memory-1447/tools/tree_identity.py `growth`, the sheets (patch_<n>.bin of fm) by its `sheets`, and the small stage
  files of C40 (patch-filter-harness-1447 identity_compare.py's STAGE_FILES list) sha256 equal. identity_holds is «yes»
  only when all three hold on all three seeds; a seed that did not finish is «not measurable» and the summary is «no».
- **Time**: no growth starts after 21:30:00Z; any process of this bar still alive at 23:20:00Z is stopped by its group
  and its seed is «not measurable, stopped before the hold».
- **Output**: `evidence/identity-0826.csv` (one row per seed, arm comparison and file counts) and
  `evidence/identity-0826-summary.csv` in the form deliver.sh reads: first column `build`, last column `identity_holds`,
  one row for flathash+avx512. Written by `tools/identity_0826.sh`. If identity does not hold: «no», and nothing else;
  the director chooses between BUILD unchanged and a fix.

## Addition of 2026-09-26T19:46:28Z: a crashed seed is replaced in the identity bar; seed237 (director 19:44:17Z)

Result of the first run (evidence/identity-0826.csv, 19:41:48Z): seed109 and seed300 hold; seed43's growth segfaulted
(rc 139) on both builds, 0 patches. The director reads that as an outcome of the seed, not a variant difference, and
orders a fourth seed. **Rule, declared now, before its growth**: a seed whose growth crashes on both builds is kept as
a row «not measurable, crashed on both builds» and is replaced by the next seed of the queue in the runner's order
(lowest pred_chunk_share_255 first). After seed43 (0.1333) that order gives **PHerc0826-seed237 (0.1745)**.

Method: tools/identity_0826.sh's, in a new file `tools/identity_0826_v2.sh` with three changes and no others:
(a) the binaries are built by tools/build_variant_seed.py into `scratch/identity/bin-<arm>/` with gates
`evidence/identity-gates/`, never the runner's `scratch/bin-*` paths, and each growth runs a copy of its binary at
`scratch/identity/run-bin/<arm>/simpaper10` (sha checked equal to its gate), a path without the seed's name, so the
running chain (relaunched on BUILD unchanged) never reads the seed as busy; its memory guard still counts these growths
(it counts every `simpaper10 g 36000`); (b) a start waits while the cores busy over 10 s exceed the settings file's
CORES_BUSY_MAX or MemAvailable minus 6 GB is under FLOOR_GB; (c) it writes `evidence/identity-0826-<seed>.csv` rows only.
Then `tools/identity_summary.py` rewrites `evidence/identity-0826-summary.csv` from the seed rows of both runs:
identity_holds «yes» only if **three measurable seeds** hold (109, 300, 237) with seed43 a row «not measurable, crashed
on both builds», otherwise «no». The settings file is not touched. Same time bounds (no start after 21:30:00Z, stop at
23:20:00Z), nice 10.
- 2026-09-26T19:59:22Z: launched by the owner with /data/scrollagent/lancia-0826.sh after the quiet clock (verdict: HV3 wins beyond the spread). I5 is descriptive, not a gate: its bar failed its own reference (1447 0.5335), the predicted voxels outside the mask sit on masked raw chunks, which the seed rule's raw grey test filters. BUILD at launch: unchanged.

## Addition of 2026-09-26T20:26:07Z: the second wave, draws 401 to 2400 under seed rule v2 (director's order of 2026-09-26T20:24:35Z)

A second wave is the director's (G4); ordered at 20:24:35Z because the queue holds only batch 1's 8 survivors, all
started by 20:17:42Z. **Size**: 2000 draws, 401 to 2400, one batch, group `batch-401-2400-0826`, aimed at about 40
survivors. Reasoning, from evidence/seed-rule-v2-check.csv: batch 1 gave 8 cap survivors of 400 draws and all 8 are
among its 72 v2 passers, so about 2 per cent of draws (8 of 400) end as survivors under v2; 40 survivors need about
2000 draws. A sizing, not a bar: fewer or more survivors are written as they come.
**Route**: `tools/refill_v2.sh 401 2400` (seed rule v2 of the addition of 18:58:51Z, its checks passed at 19:00:33Z),
started by hand with setsid, not by tools/deliver.sh (its G4 stays as written: WAVE_DRAWS 400 makes it start no refill
beyond 400; nothing of deliver.sh, the settings file or the stop file is edited). The draw is draw_seeds.py with
DRAW_COUNT 2400 (rng 20260920); its known reference is tools/prefix_check.py 400 2400 (header and draws 1 to 400 byte for
byte the draw400 file), which is also what makes deliver.sh's cur_draw() move to the 2400 file only once it is equal.
The ladder (tools/ladder.sh, unchanged) appends survivors to evidence/queue.txt under scratch/queue.lock; the running
deliver.sh (PID 220748) reads the queue continuously and builds each seed with DRAW_CSV=$(cur_draw) read at each build.

## Addition of 2026-09-26T22:19:18Z: the third wave (draws 2401 to 6400, v2) and a parallel ladder, director's order of 2026-09-26T22:17:19Z

**Third wave, size.** 60 survivors aimed. `tools/wave_sizing.py 60 2401` (evidence/wave-sizing.csv, 22:19:00Z) reads the
second wave's actual yield: 381 v2 passers of 2000 draws (0.1905 per draw), 24 survivors of 305 classified passers so far
(0.0787), so 0.0150 survivors per draw (batch 1, under v1: 0.0200); 60 / 0.0150 rounded up to 400 is **4000 draws, 2401 to
6400**, group `batch-2401-6400-0826`. A sizing, not a bar.
**Third wave, route now: draw, prefix check, seed rule v2 only** (`tools/wave_prepare_v2.sh 2401 6400`, new): the same
commands as refill_v2.sh's first three steps, in its order, each rc tested, rows to evidence/refill.csv with tool
tools/wave_prepare_v2.sh, the quiet gate before each step. **No ladder**. Races with the running second wave (refill_v2.sh
PGID 236801, which holds scratch/refill.lock, so this cannot take it): that refill is in its ladder step, its draw, prefix
check and seed rule steps ended at 20:30:01Z (evidence/refill.csv), so it writes no draw file and no seed-rule.csv row
again; the third wave writes only new files (seeds-PHerc0826-draw6400.csv, candidate-population-draw6400.csv,
draw6400-prefix-check.csv) plus appended rows of its own group to seed-rule.csv and seed-rule-v2-tests.csv. The appends are
serialised by a lock of their own, scratch/seed-rule-append.lock, and the script refuses to start while any
seed_rule_check process runs. Readers of seed-rule.csv (ladder.sh at its start, deliver.sh by attempt) filter by group or
attempt, which no row of the new group can match. deliver.sh's cur_draw() moves to the 6400 file only once its prefix check
(header and draws 1 to 2400 against the 2400 file) is equal, so already queued seeds read the same rows; its G4 keeps it
from starting a refill of 6400.

**Parallel ladder, declared before it runs.** `tools/ladder_par.sh <group> <draw csv>` (new; ladder.sh untouched): up to
PAR_W 8 worker processes; each takes the next seed of the group not yet in the output CSV nor claimed, under the lock
scratch/ladder-par.lock (claims in a claim file of the run), builds it (tools/build_variant_seed.py unchanged, the one object
build, under scratch/build.lock), passes the same start gates as ladder.sh (stop file, settings, quiet gate 300 s for a
build and 120 s for a growth, disk every 10 min, cores busy under 22 over 10 s, the memory guard with the same peaks,
/data FREE_MIN_GB), and runs ladder.sh's `one` unchanged in command, cap, environment, classification and row form. The
difference from ladder.sh is only that up to 8 seeds pass the gates and build at once instead of one start every about
18 s. It must not run on a group while ladder.sh runs the same group.
**Bar (declared now).** 20 seeds already classified by ladder.sh in group batch-401-2400-0826, chosen by rule: in the
order of evidence/ladder.csv, the first 5 «still growing at the cap», the first 5 «ended by itself», the first 10 «no
patch written». Rerun with ladder_par.sh into scratch/ladder-par-test/ (its own output CSV, queue, done file, logs, growth
dirs, binaries and gates; never evidence/ladder.csv, queue.txt or log/ladder-*.txt). Pass: the outcome equal on 20 of 20
(`tools/ladder_par_check.py`, evidence/ladder-par-bar.csv). Only then is a switch filed; nothing runs on a real group
without the director's reading. The test ends by 23:25Z or resumes after 03:15Z.
- 2026-09-27T08:58:35Z: launched by the owner with /data/scrollagent/lancia-0826.sh after the quiet clock (verdict: HV3 wins beyond the spread). I5 is descriptive, not a gate: its bar failed its own reference (1447 0.5335), the predicted voxels outside the mask sit on masked raw chunks, which the seed rule's raw grey test filters. BUILD at launch: flathash+avx512.
- 2026-09-27T14:58:50Z: launched by the owner with /data/scrollagent/lancia-0826.sh after the quiet clock (verdict: HV3 wins beyond the spread). I5 is descriptive, not a gate: its bar failed its own reference (1447 0.5335), the predicted voxels outside the mask sit on masked raw chunks, which the seed rule's raw grey test filters. BUILD at launch: flathash+avx512+lto+pgo+native.
- 2026-09-27T16:42:01Z: launched by the owner with /data/scrollagent/lancia-0826.sh after the quiet clock (verdict: HV3 wins beyond the spread). I5 is descriptive, not a gate: its bar failed its own reference (1447 0.5335), the predicted voxels outside the mask sit on masked raw chunks, which the seed rule's raw grey test filters. BUILD at launch: flathash+avx512+lto+pgo+native.

## Addition of 2026-09-27T20:25:28Z: the fourth wave, drawn near the seeds of 10 mm or more (director 2026-09-27T18:14:00Z point 2), declared before its draw

Written by a coordinator agent. No draw of this wave exists when this is written. Read before it: the sources list and the
size row, both tool written, neither a result of this wave.

**Sources.** `tools/wave4_sources.py 10` (new) wrote `evidence/wave4-sources.csv` at 20:2xZ: for each of the 102 squares
files, the best `square_mm_min_step` over the seed's measured sheets; **39 seeds at 10 mm or more** are the sources
(is_source yes). The source point is the seed's own point (seed_x, seed_y, seed_z of its draw6400 row): the point that
gave the square, not the square's centre (which would need the sheet's 3D positions and would restart on a surface
already delivered).

**Proximity rule (new).** Around each source, in ascending draw_order of the sources: the candidates are the voxels of the
0826 prediction (level 0, local, the same zarr as draw_seeds.py) that are 255 with their six face neighbours 255
(draw_seeds.py's candidate test, on the interior of a block read around the source), whose Euclidean distance to the
source point in voxels is **at least 48 and at most 256** (0.45 mm to 2.40 mm at 9.362 um, about 3 to 23 laminae at the
103 to 140 um spacing: never the source's own point, always its neighbourhood), inside the volume. Candidates are listed
in numpy.nonzero order of the block (z, y, x). **8 per source** are drawn with `numpy.random.default_rng(20260927)`
(this seed, written into the tool), one index at a time with rng.integers(0, n), a repeat, a point already drawn in
draws 1 to 6400 or a point already drawn for an earlier source redrawn; a source with fewer than 8 candidates gives all
of them, written. Tool: `tools/draw_near.py` (new). **Size: 39 x 8 = 312 draws, attempts PHerc0826-seed6401 onward**,
group `batch-6401-<N>-0826`, N = 6400 plus the draws made.

**Size row** (`tools/wave4_sizing.py 8`, `evidence/wave4-sizing.csv` 20:25:06Z): /data 53 GiB free, FREE_MIN_GB 30, study
130 GiB (du -sBG) of STUDY_MAX_GB 160, SEED_MAX_GB 9; a delivered 0826 seed keeps a median 1290 MiB in out/ (largest 2039,
114 dirs), not 0.75 GB; room before the runner holds 14 GiB counting one seed's 9 GiB transient (21 by the study cap),
so **about 11 seeds fit now** (up to about 16 without the transient). Yield of the third wave: 77 survivors of 4000 draws
(0.0192) and of 808 v2 passers (0.0953); 312 near draws give 6 to 30 survivors (low if they pass v2 as uniform draws do,
high if all pass). Survivors beyond what fits wait in the queue for the owner's disk list; the runner's own gates
(FREE_MIN_GB, STUDY_MAX_GB, the 98 per cent brake) are the stop, unchanged.

**Route, the house tools unchanged.** (1) `tools/draw_near.py` writes `evidence/seeds-PHerc0826-draw<N>.csv` whose tool
line names it and whose header and rows 1 to 6400 are the bytes of the draw6400 file, the near rows after them in the
same columns (global_candidate_index «near <source attempt>», lattice_chunk the prediction chunk of the point, since no
lattice index exists for a near draw; downstream tools read only attempt and seed_x, seed_y, seed_z), and
`evidence/candidate-population-draw<N>.csv` with draw6400's rows copied (they describe rows 1 to 6400) and the near
draw's own rows. (2) Known reference: `tools/prefix_check.py 6400 <N>` unchanged (header plus draws 1 to 6400 byte for
byte, stage1_candidates and rng_seed of the copied population rows equal), written first to
`scratch/wave4/draw<N>-prefix-check.csv` (its PREFIX_OUT), because the evidence file of that name is what moves
deliver.sh's cur_draw() to the new draw file: that move is the feed, below. (3) Seed rule v2 unchanged
(`tools/seed_rule_check_v2.py`, z band 1941..16262 and chunk share at most 0.30, the three tests of part 2) on the
group, appended to seed-rule.csv and seed-rule-v2-tests.csv under scratch/seed-rule-append.lock, with the same flags as
wave_prepare_v2.sh. (4) The ladder as in the earlier waves: `tools/ladder_par.sh` unchanged, PAR_W 8, nice 10, 120 s cap,
rc 124 at the cap = survivor, rows to evidence/ladder.csv, done file evidence/ladder-<group>.done; its survivors go to a
**staged queue** `scratch/wave4/queue-staged.txt` (LP_Q), not to evidence/queue.txt. During steps 1 to 4 this agent
holds scratch/refill.lock (the runner then reads «refill running»; with cur_draw at 6400 above WAVE_DRAWS it starts no
refill in any case).
**The feed** (`tools/wave4_feed.sh`, new, after the director's reading, since the draw file comes from a new tool and
becomes the file every delivered build reads): prefix_check.py 6400 <N> again into evidence/draw<N>-prefix-check.csv,
cur_draw() read back as the new file, then the staged survivors appended to evidence/queue.txt under
scratch/queue.lock (a line only if absent), a ledger row chain-0826-wave4-fed. The running runner (PGID 1237417) reads
the queue afresh and delivers them lowest chunk share first, as every wave.

**Reading of the wave, declared now, descriptive, no bar on the chain:** the share of the wave's delivered seeds whose
best square is 10 mm or more, beside the earlier waves' 39 of 102; the median best square of the wave beside the
earlier median; how many near seeds re grow a sheet already delivered (item 90 (a)'s dedup, when it is rerun). A near
draw that only regrows the source's sheets is said as such.
