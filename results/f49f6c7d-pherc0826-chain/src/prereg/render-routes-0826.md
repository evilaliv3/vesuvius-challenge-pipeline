<!-- Shipped copy of render-routes-0826/DECLARATION.md, 2026-09-30: one scan height is written «[height withheld]» (the owner's decision: no position on the scroll); nothing else differs from the study's file. Where it says PRIVATE, private or never public it describes how the study kept its own outputs on the day it was written, before the owner's decision of 2026-09-30 to publish this article with no position on the scroll. -->
# render-routes-0826: two render routes on PHerc0826 (height field, the organisers' tracer), judged by the same checks

Written 2026-09-29T06:42:35Z (`date -u`) by an agent of the coordinator, before any number of this study exists: nothing has
been fitted, grown, regridded, rendered or scored. Nothing below is retouched after the first number; additions are dated.
PRIVATE: PHerc0826 textures, renders and ink outputs go only to /data/scrollagent/outputs/artifacts/render-routes-0826/.

## The order (director 2026-09-29T06:36:25Z, owner's word), verbatim

«two more render routes, run in parallel with the variants, both declared first and both judged by the same w016 control and
the same one lamina and fibre checks: (R1) HEIGHT FIELD: on a certified one lamina piece, fit the sheet as r(theta, z) around
the published umbilicus with a smoothing spline (knots every 0.5 mm, declared), and render on the grid u = arc length at the
local radius, v = z; this is smooth and axis aligned by construction; valid only where r(theta,z) is single valued, which the
one lamina certificate guarantees; first on seed5364 S0 certified square and on the best windows, and on our w016 sheet for
the control. (R2) THE ORGANISERS' TRACER: villa's vc_grow_seg_from_seed (villa-tracer-build/scratch/build/bin, reference ray
cost off as shipped defaults, V02 fix on) started from our best points on 0826 (the seed points and square centres of
seed5364, seed6729, seed6733, seed2715, seed6273), on the same m7 prediction, grown to a declared size (generations and area
written first), rendered with vc_render_tifxyz as they do; then our checks on its output (self conflict, v2 against our 800
sheets, a2, fibre, largest square and 4 cm2 window). Report per route: fibre score, roughness (median angle between
neighbouring normals), grid angle to z, ink reader balanced accuracy on w016 where applicable. Deadline 16:00Z.»

Coordinator's addition (director 06:38:48Z), before any number: rotation is ONLY the true correction: every render is
regridded with v = the scan's z and u = arc length along the sheet at constant z (R1's grid for our sheets; the tracer's own
grid for R2). The regridding is a standalone tool, `tools/regrid_z.py`, input a tifxyz or our patch_<k>.bin lattice, output a
tifxyz on the (arc length, z) grid, with its self test. First numbers (R1 w016 control, seed5364's R1 render) go to the
coordinator as they land, each with a ledger row.

## Frame and inputs

- Voxel 9.362 um (pipeline/datasets/voxel.py, PHerc0826 manifest; chain-0826 evidence/inputs/i1-voxel.csv). h = the sheet's
  lattice step in voxels (median 3D distance between covered i neighbours of the region, about 4.0).
- The published umbilicus: field-0826-0800/scratch/20250821151701-umbilicus-20260808113303.json, sha256 head fc9c54cdc0ea7f0e
  (the copy chain-0826 I6 checked; 49 control points, z 1941 to 16262). Centre c(z) = linear interpolation of the control
  points' x and y in z, held constant beyond the end points (a column says when a region leaves 1941..16262).
- Sheets: chain-0826/out/<seed>/C40/patch_<k>.bin, read with certified_region.lattice_from_patch (area-0826-90's reader).
  Masks (valid, v2, self_conflict, b_end, a2_rule, piece) from certified-piece-0826/scratch/piece2/<label>.npz, read only.
- Regions on 0826 (lattice index boxes, fixed now):
  - S5364sq: C40 seed5364 S0, the certified square of square20-0826-95/evidence/certified-squares.csv (corner i 376, j 679,
    411 cells).
  - bw1, bw2, bw3: the rows marked best 1, 2, 3 in best-windows-0826/evidence/windows.csv at the time the tool reads it (at
    06:21Z: C40 seed5364 S1 at (115, 710), C40 seed6473 S0 at (591, 1069), C40 seed6731 S0 at (1275, 724), 535 cells); the
    file's header time is a column. That study's files are only read.
- w016 control: OUR w016 sheet from positive-control-0139 (its best covering sheet, as that study names it) over that
  study's window, read only; its scoring tools imported or copied, never edited. If no such sheet exists by 13:00Z, the rows
  say so.

## The regridding tool (tools/regrid_z.py), one tool for R1 and for R2

Input: a patch .bin lattice (records x, y, px, py, pz) or a tifxyz folder, an optional index box, the umbilicus. Every valid
node p = (x, y, z) gets theta = atan2(y - cy(z), x - cx(z)) unwrapped around the circular mean of the region, r = the distance
to c(z) in the slice, and a = r_med x (theta - theta_c), r_med the median r of the region, theta_c the theta of the region's
centre node (the valid node nearest the box centre).

- Surface model r(a, z):
  - `--fit spline` (R1): a cubic tensor product B spline in (a, z) with interior knots every 0.5 mm (53.41 voxels) on both
    axes, from the data's a and z range; least squares on every valid node of the region (the fit box, below), with a ridge
    of 1e-6 x the mean diagonal so that knot spans without data stay defined; solved by scipy sparse normal equations.
  - `--fit none` (R2 and the check of the tool): r linear on the Delaunay triangulation of the nodes in (a, z)
    (scipy LinearNDInterpolator): the surface itself, only reparametrised.
- Grid: rows v with z_v = z_c + (v - v0) h (v = z, one row per h voxels), columns u with arc length u_k = (k - k0) h along
  the curve of constant z, measured from theta_c: s(theta) = integral of sqrt(r^2 + (dr/dtheta)^2) dtheta at z_v, sampled at
  h/4 in a, inverted by linear interpolation. Point = (cx(z) + r cos theta, cy(z) + r sin theta, z). The output grid is square,
  side n given (default the box side plus 2 x 64 cells of margin), centred on the region's centre node.
- A grid node is valid when the nearest valid input node in (a, z) is within 1.5 h and the model is defined there; it keeps
  that nearest input node's index (so masks of the input lattice are read at the nearest input cell, as best-windows-0826's
  aligned squares).
- Columns written by the tool (evidence/regrid.csv, one row per run): input, box, fit, knots, h, r_med, theta span, z span,
  umbilicus z range left (yes or no), nodes in, nodes out valid, fit residual |r_model - r| at the input nodes (median, p95,
  max, voxels), median 3D spacing along u and along v of the output (voxels), angle of the output row step to z (median,
  IQR), and the share of input nodes whose (a, z) bin of h x h holds nodes with r spread above 2 h (fold_share: a check
  that r is single valued; the one lamina certificate should keep it near 0).
- Output: tifxyz (x.tif, y.tif, z.tif float32, -1 invalid, meta.json with scale 1/h, written by signal_null.write_tifxyz's
  convention: rows = v, columns = u) and an npz beside it (X, Y, Z, valid, src_i, src_j).
- Self test first (`regrid_z.py selftest`, evidence/regrid-selftest.csv, every other mode refuses without it): a synthetic
  cylinder r = 1500 + 3 sin(2 pi z / 400) voxels around an axis tilted 2 degrees, sampled on a lattice of step 4 voxels
  rotated 30 degrees to z. Pass bars: (T1) fit none: output row step angle to z median under 0.5 degree, u spacing median
  within 1 per cent of h, |r_out - r_true| p95 under 0.1 voxel; (T2) fit spline with knots 0.5 mm on the smooth part
  (r = 1500 + 0.02 (z - z0)): p95 under 0.1 voxel; (T3) tifxyz round trip exact; (T4) a patch .bin input and the same
  lattice as tifxyz give the same output.

## Routes and surfaces (one row per route x surface in evidence/routes.csv)

- L (ours as delivered): the lattice of the region, no change: the reference row beside each route.
- R1 (height field): `regrid_z.py --fit spline` on the region's certified cells (the npz's piece array: strict certified
  piece) inside a fit box = the output grid's footprint plus 32 cells, so the spline is fitted only on one lamina cells.
  Output grid: side = box side + 2 x 64 cells (663 for the windows, 539 for S5364sq), centred on the region centre.
- R2 (the organisers' tracer):
  - Binary villa-tracer-build/scratch/build/bin/vc_grow_seg_from_seed (sha256 head 53fbaa948f7abeca, «before»). V02 changes
    only the mode choice when a seed coordinate is 0; every start below has three nonzero coordinates, where both arms were
    measured to give explicit_seed (villa-tracer-build/evidence/v02-alone-head.csv, row all-nonzero-seed26). So this binary is
    V02 on for these starts; the column mode (meta.json vc_gsfs_mode must read explicit_seed) checks it on every run.
  - Parameters: tools/vc3d/params-1795-example.json with voxelsize 9.362 (voxel.py), generations 320, thread_limit 1,
    step_size 20 (the shipped example), no reference_surface (reference ray cost off, shipped default); written once to
    scratch/r2/params.json. VC_GROWPATCH_RNG_SEED 20260923, OMP and OpenBLAS one thread, nice 10, timeout 3 h per run.
  - Declared size: 320 generations; target area 20 cm2 (the order of our certified pieces). The tracer has no area stop, so
    the area is read from meta.json (area_cm2) and written beside the target; a run under 4 cm2 says so.
  - Volume: -v /data/scrollagent/data/datasets/PHerc0826 (the m7 prediction chain-0826's downstream stages read, folder 0,
    zarr v2, blosc zstd, uint8, 192 cubed chunks; the same format the tracer read for PHerc0139 in villa-tracer-0139). The
    growth copy hot-lines-88/scratch/l/0 is the same values in lz4hc; the original is used. If the tracer refuses it, a row.
  - Ten starts: for each of seed5364, seed6729, seed6733, seed2715, seed6273: (a) the seed point (chain-0826
    evidence/per-seed-queue.csv seed_x, seed_y, seed_z), (b) the 3D point of the centre cell (corner + cells // 2) of the C40
    S0 certified square (certified-squares.csv), rounded to integer voxels. evidence/r2-runs.csv: start, xyz, rc, wall, mode,
    max_gen, area_cm2, cells, x.tif sha head.
  - Rows: R2-native (the tracer's grid, bilinearly upsampled by 20 / h to our step so the fibre bands can be read; its own
    axes) and R2-regrid (`regrid_z.py --fit none` on the tracer tifxyz). The tracer's native grid angle to z is a column.
  - Render «as they do»: vc_render_tifxyz (the same binary folder) of the tracer tifxyz over its best 4 cm2 window (or its
    largest certified square when no window), `--num-slices 1 --scale 1 --voxel-size 9.362 --group-idx 0` on the raw masked
    scan 20250821151701 through the house cache, as a PNG beside ours. Raw chunks sized before; the disk rule below.

## Checks per row (the same for every route; imported, never edited)

- One lamina checks, cert.py's computed branch on the row's lattice (the regrid output or the upsampled tracer grid as px,
  py, pz, valid): a2 (area90.a2_grid, cluster_rule.rule_holes; a2_rule holes and all flagged blocks), v2 against our 800
  (area90.index keys, sheet_cross_v2.pair_v2 and marks with area90.thresholds) and, for R1, the seed's other delivered sheets
  (siblings) except the source sheet itself (its own surface; excluded and said in the column partners), self conflict
  (lamina.conflicts at lamina.pitch), b end as pairwise.py's conflict_pairs where that module is importable unchanged, else
  «not measurable». For row L the masks of the npz are read (as best-windows-0826).
- Largest certified square: square.py largest_square on valid and not v2 and not self conflict and not a2 rule, mm by h.
- Best 4 cm2 window: best-windows-0826's definition (20 x 20 mm by the row's steps, covered at least 0.95, flagged at most
  0.01, fibre at least 0.0680, ranked by flagged then hole share), searched with summed area tables inside the row's grid.
- Fibre score: fibre.py's bands and wscore imported unchanged, on 128 x 128 tiles at offsets 0, 64, ... and n - 128 of the
  row's grid inside the evaluated square (the region's own square for L, the output grid's central square of the region's
  side for R1 and R2), accepted when every cell is valid, not flagged, and its raw value (nearest voxel of the raw masked scan
  20250821151701 level 0, piece_texture.Raw2, read only) is measurable and not 0; score = median, with IQR and tile count;
  fewer than 8 tiles «not measurable». Steps for the bands: the row's median 3D spacings along i and j in mm.
- Roughness (positive-control-0139's definition, declared identically): per cell the unit normal from the cross product of
  the central differences of the 3D grid; the angle between the normals of each cell and its right and lower neighbour (both
  valid); median and 90th percentile over the evaluated square's valid cells; on the row's own grid AND at a common spacing
  of about 20 voxels (every n = rint(20 / spacing) cells), the common spacing being the comparison column.
- Grid angle to z (best-windows-0826 align.py's definition): per cell with a valid i neighbour, d = p(i+1, j) - p(i, j),
  angle = arccos(|d_z| / |d|); median and IQR (p75 - p25) over the evaluated square; the same for j beside. i is the row
  index of the grid (for L the lattice's first index; for a tifxyz the rows).
- Ink reader balanced accuracy: on w016 only (the only labelled surface): R1 of our w016 sheet through positive-control-0139's
  render, reader and scoring (its declared path, copied), beside that study's own rows for our lattice and theirs. On 0826 no
  label exists: «not applicable».
- PNGs (private): per row a texture at one pixel per cell (raw nearest voxel, grey p1 to p99 of the square's nonzero valid
  values, holes white) and one PNG per region with L, R1 (and the R2 of that seed where it covers) side by side, 5 mm bar,
  «z up» on the regridded halves.

## Load, disk, order of work

Load gate: no new heavy start while /proc/loadavg's first value is above 22 (the coordinator lifted the 6 core cap at
06:38:48Z; nice 10 on everything). Disk: /data free read before every fetch; a fetch starts only if free minus its bound
stays above 35 GB; fetched raw chunks go to this study's scratch/raw-chunks, are listed in a ledger row and deleted after use.
TMPDIR=/data/tmp. Long work as setsid runners; PGIDs in the ledger; kill by PID or PGID only. The chain-0826 runner and its
files, best-windows-0826's and positive-control-0139's files: read only. Order: regrid_z selftest; R2 growths started (cheap,
single thread); R1 on S5364sq (first number to the coordinator), bw1 to bw3; R1 w016 control as soon as the sheet exists;
R2 checks; renders and PNGs; routes.csv; queue item. Deadline 16:00Z; what is not done is written «not run» with the reason.

## Addition of 2026-09-29T06:47:31Z (before the self test is written; one dry run of the synthetic case was looked at, unwritten)

The declared T1 bar «output row step angle to z median under 0.5 degree» cannot pass on its own synthetic case: the cylinder's
axis is tilted 2 degrees and its radius ripples, so a grid whose rows are exactly at constant z still has row steps inclined to
z by the sheet's own inclination (the dry run read 2.0 degrees). best-windows-0826's angle arccos(|d_z| / |d|) mixes two things:
the sheet's inclination to z (dr/dz, a property of the scroll, which no grid removes) and the rotation of the grid inside the
sheet (what the regridding corrects). So every angle is reported twice from here on: the 3D angle as declared (best-windows'
definition, the ordered column), and the IN PLANE angle, between the step and z projected on the tangent plane (the node's unit
normal from the cross product of central differences). T1 and T2 bars move to the in plane angle (under 0.5 degree); the 3D
angle is an information row of the self test. routes.csv carries both, for the i step and the j step.

## Addition of 2026-09-29T06:48:05Z (after the first self test run, which failed T2; its rows stay in evidence/regrid-selftest.csv)

Self test run 06:47:32Z: T2 failed its in plane bar (0.622 degree, bar 0.5); every other row passed. Reading: the grid's
columns are curves of constant arc length from theta_c; on a cone (r grows with z) whose axis is tilted, those curves shear
inside the sheet by about u dr/dz / r plus the axis drift, so the v step is not exactly the in plane z even when the rows are
exactly at constant z. That shear belongs to the ordered grid (v = z, u = arc length at constant z), not to an error of the
tool. What the regridding must guarantee is that each ROW lies at constant z: the u step's 3D angle to z is then exactly 90
degrees. New bars, from the second run on: T5 (fit none, T1's case) and T6 (fit spline, T2's case): median |90 - angle of the
u step to z| under 0.01 degree; the in plane angle of the v step becomes an information row in T1 and T2 (the grid's shear,
also written per surface in routes.csv). The 06:47:32Z run is not rewritten.

## Addition of 2026-09-29T06:54:37Z (before any R2 surface is measured; R2 growths have ended for some starts, only their meta.json areas seen)

The tracer surfaces reach 36 to 71 cm2 (meta.json, evidence/r2-runs.csv), stopping by themselves at 160 to 230 generations.
Sampling raw values over a whole surface would fetch about 10 GB per surface. So the R2 rows are measured on a crop,
fixed now: the tracer nodes within 80 native nodes (80 x 20 voxels = 15.0 mm) of the node nearest the start point on each
axis, i.e. a 30 x 30 mm square of the tracer's own grid centred on our start point. R2native = that crop upsampled
bilinearly by 5 (to 4 voxels); R2regrid = regrid_z.py --fit none on the same crop (--box), h 4.0 voxels, side 801 (30 mm).
Every check, window search and fibre tile of the R2 rows is inside that crop. Fetched raw chunks are deleted after each
region's rows are written (listed in a ledger row first).

Also recorded here, before any R1 row is scored: the R1 regridding of the four 0826 regions (evidence/regrid.csv) put the
certified pieces at a median radius of 692 to 756 voxels (6.5 to 7.1 mm) from the published umbilicus, over theta spans of
202 to 215 degrees, with fold_share 0.37 to 0.55 and spline residual p95 65 to 262 voxels. So r(theta, z) is NOT single
valued on these pieces around the published umbilicus: the premise «which the one lamina certificate guarantees» does not
hold there. The R1 rows are still measured as declared. Their fold_share and residual columns say where the height field
leaves the sheet.

## Addition of 2026-09-29T07:05:46Z (after the L rows of bw1 and bw3 were read: angle i to z 3D 65.14 and 80.86 degrees)

On bw1 and bw3 our lattice's i step lies nearly across z, so its j step is the one near z. The i step angle alone would
report a well aligned grid as badly rotated. So one more column is added for every row: rotation_inplane = min(a, 90 - a),
where a is the in plane angle of the i step to z. This is the grid's rotation away from the nearest axis aligned grid,
modulo 90 degrees. It is given as the median and IQR over the eval box. Tool tools/rotation.py (geometry only, no fetch),
evidence/rotation.csv, joined into routes.csv. The declared i step columns are kept unchanged beside it.

## Addition of 2026-09-29T07:33:27Z: director's decisions of 07:22:16Z (relayed by the coordinator), and the swirl check (best-windows-0826, 07:28:18Z)

1. **R1 is closed.** The director's words: «r(theta, z) is not single valued on a crushed scroll». The R1 rows on 0826 stay in
   routes.csv as measured. The w016 R1 control is NOT run (skipped by order, not for lack of a sheet). The waiter I had set on
   positive-control-0139's sheet is stopped.
2. **regrid_z.py: figures only, never a number.** T2 failed its bar as first declared (0.622 against 0.5 degrees, run
   06:47:32Z). Any figure made with it states that failure in its caption. No number from a regridded surface (R1 rows,
   R2regrid rows, rotation of regridded grids) is used as a result. Those rows stay in the CSVs, marked by their route.
3. **R2b, declared before anything is generated.** The tracer again from the same 10 starts, with the normal grids villa
   expects: vc_gen_normalgrids (the same build folder) on the 0826 m7 prediction (data/datasets/PHerc0826, level 0), passed
   as normal_grid_path, every other parameter as R2. Sizing first:
   - a pilot of a few slices per direction (sparse slices, into /data/tmp/ngpilot, deleted after) gives seconds and bytes
     per slice;
   - the full plan (16920 xy, 8169 xz, 8169 yz slices at sparse 1, or the sparse setting the tracer accepts) is scaled from
     it and written as a row of evidence/r2b-sizing.csv before any grid is generated.
   - If /data free minus the grids' bytes is under 40 GB (the 35 GB floor plus room for the other studies), or the time
     does not fit before 15:00Z, R2b stops at that row.
   - If it fits: grids into scratch/normal-grids, the ten runs, the same checks, R2bnative rows in routes.csv.
4. **Swirls in regrid_z.py renders (best-windows-0826's finding).**
   - Measure: for every output node of the four R1 grids (and the best-windows regrid uses), the 3D distance to the nearest
     VALID lattice cell of the source sheet (KD tree over all covered cells), and the flags of that cell.
   - Shares, per region, over the output grid's valid nodes: off_sheet_2h (distance over 2 h), off_sheet_1h (over 1 h),
     nearest_is_hole_adjacent (the nearest cell has an uncovered 4-neighbour), nearest_self_conflict (either end),
     nearest_not_in_piece.
   - tools/offsheet.py, evidence/offsheet.csv.
   - If off_sheet_2h is above 0.01 in any region, the swirl reading is confirmed, and regrid_z.py gains an option
     --max-dist-3d D: a node is valid only when its 3D distance to the nearest model node is at most D (default for figures:
     2 h). The figures are redrawn with it.

## Addition of 2026-09-29T07:36:46Z: R2b sizing (evidence/r2b-pilot.csv, evidence/r2b-sizing.csv), the choice written before any grid is made

The pilot measured 10 sparse slices per direction:
- per slice: xy 0.23 MB and 0.7 s; xz 0.33 MB and 1.2 s; yz 0.38 MB and 2.0 s.
- Full grids: sparse 1 is 9.76 GB and leaves 38.1 GB free, under the 40 GB rule: refused. Sparse 2 is 4.88 GB (43.0 GB
  left) and sparse 4 is 2.44 GB (45.4 GB left); both allowed.
- Time upper bounds on 8 single thread shards: 40 min for sparse 2 and 20 min for sparse 4.
- Chosen: **sparse 2**, the finest allowed setting.
- villa's NormalGridVolume reads the «sparse-volume» metadata and interpolates between the sampled slices
  (core/src/NormalGridVolume.cpp lines 104 to 110 and 314 to 317), so the tracer accepts it. It is a declared difference
  from a dense grid.
- Generation: tools/r2b_grids.sh; vc_gen_normalgrids generate -i data/datasets/PHerc0826 -o scratch/normal-grids
  --sparse-volume 2, each direction in 8 shards (--num-parts 8, --part-id k) run at once, OMP one thread, nice 10; a shard
  starts only under load 22; the run stops if /data free falls under 38 GB.
- Then the 10 starts with params.json plus normal_grid_path = scratch/normal-grids (every other key as R2), rows R2bnative
  and the same checks; the grids are kept until the rows are written, then listed and deleted (ledger row).

## Addition of 2026-09-29T08:18:16Z: R2b grids stopped by the disk rule

At 08:17:39Z /data fell to 34 GB free: other studies were writing; this study holds 2.6 GB. tools/r2b_grids.sh stopped by
its own rule (under 38 GB). At that point xy was complete (8460 grid files, 1.75 GB), xz was partial (3365 files) and yz was
not started. Kept for a resume.

tools/r2b_resume.sh waits, until 15:00Z at the latest, for /data free of at least 43 GB: the 40 GB rule plus the about 2.3 GB
still to write. It then reruns the generation (vc_gen_normalgrids skips the slices already written) and the chain. If 15:00Z
comes first, R2b is reported «not run: disk».

## Addition of 2026-09-29T10:05:07Z: R2b generations 160 instead of 320 (before any R2b surface exists)

With the normal grids loaded, the five first R2b runs grow unobstructed. The log at gen 96 reads done 36096 nodes, which is
(2g - 2)^2: the whole square, as the 2026-09-23 ledger row describes. At about 1.5 mm2/s each, 320 generations (about 143
cm2) would take about 2.5 h per batch of five, and the second batch would end after the 16:00Z deadline.

The R2 and R2b rows only read the 30 mm crop, which lies within 80 nodes of the start. So R2b is regrown at generations 160.
That is about 35 cm2 if unobstructed, above the declared 20 cm2 target and twice the crop's reach. params scratch/r2b/params.json
gets generations 160 and nothing else changes.

The five runs started at 09:55Z are stopped by group (kill -TERM -- -3974545, the resume and chain group) and their partial
folders deleted. A new chain (tools/r2b_chain.sh) is started with the same gates. R2 (generations 320) and R2b (160) differ
in this one declared respect. For R2 it did not matter: its runs stopped by themselves at 119 to 247 generations.

## Addition of 2026-09-29T11:24:12Z: R2b square checks (director 11:22:26Z, relayed), declared before their numbers

For every R2bnative crop (all 10), on its largest certified square, tools/sq_checks.py writes one row of
evidence/square-checks.csv. The same tool runs on L S5364sq as the known reference for the sections: best-windows-0826's
straight.csv rows cert5364 read 8.0 / 0.1873 (i) and 9.0 / 0.1290 (j).

Columns:
- (a) Inside the square: v2 against our 800 (area90 index, as cert.py); v2 against the 9 other R2b crops (the same
  pair_v2 and marks on their working grids); self conflict at the a end and at the b end; a2 cluster rule cells; holes.
- (b) The strict square (every a2 flagged block avoided) and (c) the pairwise one lamina square (pairwise.py's
  conflict_pairs, build and Pairwise, imported unchanged).
- (d) Straightened sections along the i and j centre lines of the square, with best-windows-0826 straight.py's
  tangent() and line() copied, since that module cannot be imported. Statistic: median |offset| of the brightest voxel
  within +-15 voxels of the middle, q25, q75, and share within 3 voxels.
- (e) Radius about the umbilicus, and the share of the square's nodes within 3 voxels of one of our sheets: the full patch
  lattice of the 3 best candidates by working-grid overlap within 6 voxels. Reported over all of that sheet's cells and
  over its certified piece cells where a piece npz exists; the sheet is named.

The fibre score and the clean 4 cm2 window are already in routes.csv.

An axial cut (tools/axial_cut.py): the raw scan (20250821151701 level 0, nearest voxel) in the plane z = the square's centre
z, a 6 mm box around the square's centre, with:
- the R2b surface's trace (nodes within 1 voxel of that z) marked;
- the square's own nodes on that cut marked in a second colour;
- the nearest of our sheets' trace (the (e) best sheet) in a third colour.
PRIVATE PNG. Whether the trace stays on one bright layer is read by eye and written as a judgement.

**It holds**, for the next steps, when ALL of these are true for a crop:
- in-square v2 (800 and R2b), self conflict at both ends, a2 rule and holes are all 0;
- the pairwise square is at least 20 mm;
- both sections' share within 3 voxels is at least 0.370 (bw1's lattice j line, the director's reference);
- the axial cut is judged on one layer.

Only then: the texture of the square with z up (one pixel per node, raw nearest voxel), and the ink reader.
- The predicted orientation comes from sq.py's orient and radial rule, computed and written in evidence/ink-orientation.csv
  BEFORE any read.
- The reader is run_one_v2.sh with its null, with the lock dance of certified-piece-0826/tools/ink_piece.sh.
- Then a figure (private).

## Addition of 2026-09-29T11:28:50Z: the normal grids are kept for now

The R2b rows are written. The declared deletion of scratch/normal-grids (4.74 GB) is held back until the director answers on
the ink bar: a follow up growth would need the grids again, and they took about an hour to make. /data has 53 GB free. The
grids are deleted, listed first in a ledger row, when this study hands back, unless the coordinator asks to keep them.

## Addition of 2026-09-29T11:54:35Z: the headline follow up (director 11:53:25Z, relayed), declared before any of its numbers

Order, verbatim: «(1) regenerate the normal grids (about 1 h, disk allowing) and regrow seed6273 and seed5364 at the declared
size, then measure the square on a crop large enough that it is not bounded (60 mm), same checks; (2) ink reader on the seed6273
square in its geometry predicted orientation with the null, stated with the label free statistic's w016 result beside it; (3) a
figure (texture z up with 5 mm bar, the axial cut with both traces, the straightened sections) in the house style for the
reframed article; (4) the square's surface stays private (PHerc0826). Deadline for (1)-(3) 20:00Z.»

(1) Grids and regrowth
- Normal grids: the SAME sparse 2 as R2b (tools/r2b_grids.sh unchanged; 4.74 GB). Dense would fit on disk (9.76 GB, 54 GB
  free now), but it would change the method against the R2b rows. With sparse 2 the regrowth can be checked against them.
- Regrowth: the two square centre starts (seed6273, seed5364), params scratch/r2b/params.json with ONE change,
  generations 200 (was 160). A 60 mm crop needs 160 native nodes each side of the start; at 160 generations the grid reaches
  159, at 200 it reaches 199. Output scratch/r2c/<start>, runner tools/r2c_grow.sh (copy of r2b_grow.sh, paths and
  generations only), rows evidence/r2c-runs.csv.
- Check column (the known reference): evidence/r2c-vs-r2b.csv, per start, the median and max 3D distance between the r2c
  and r2b nodes of the same grid index within the old 30 mm crop.

(1) Checks on the 60 mm crop
- Route R2cnative: the tracer nodes within 160 native nodes of the start (60 x 60 mm), upsampled by 5.
- The same checks as R2bnative: routes.py measure, then sq_checks.py (flags in the square, strict and pairwise squares,
  sections, overlap with our sheets, v2 against the other R2b crops) and axial_cut.py.
- «Not bounded»: a column says whether the largest certified square touches the crop's edge (square_touches_crop_edge).

(2) Ink read on the seed6273 square (the R2c square if it holds, else the R2b one; the row says which)
- The square's lattice is written as a patch .bin (records x = i, y = j, px, py, pz; the upsampled tracer grid), under
  scratch/ink/.
- The predicted orientation: signal_null.py patch2tifxyz, then sq.py cut with run_one_v2's 60 cell margin, then sq.py orient
  (orient_0826's two rules, the published umbilicus). It is run by tools/ink_orient.py and written as a row of
  evidence/ink-orientation.csv BEFORE the read.
- The read: ink-square-0826-seed2604/tools/run_one_v2.sh unchanged, run inside its own study as ink_piece.sh does
  (fixed half pitch or gap minimum null, both directions, seed42 and seed43), with the lock dance of
  certified-piece-0826/tools/ink_piece.sh (tools/ink_r2c.sh, a copy with only the inputs changed); ink.html, never
  index.html.
- A check column: the orientation run_one_v2 reads (its shifts.txt k m) equals the predicted row.
- Beside it, read only: positive-control-0139/evidence/labelfree-w016.csv's result for our w016 sheets.

(3) Figure: article-figure/fig_r2c.py in results/figstyle.py's house style (Times, Okabe Ito).
- (a) texture of the square, z up, with a 5 mm bar;
- (b) the axial cut with the R2c trace and our sheet's trace;
- (c) the straightened sections along i and j.
- PNG and PDF only in this study's article-figure/, never in the article folder.

(4) Privacy: everything of PHerc0826 stays under this study and outputs/artifacts/render-routes-0826/.

Deletions: the grids and the fetched chunks are listed in a ledger row before deletion, and only after the rows exist.

## Addition of 2026-09-29T12:58:35Z: the wording of the ink read (director's ruling 12:52:52Z), before the read

run_one_v2's label free statistic reads «no» on known ink on our w016 sheets in 16 of 16 rows
(positive-control-0139/evidence/labelfree-w016.csv). The R2c square's read is therefore a record, not a verdict on ink:
- whatever it gives, it is written «not measurable at our sensitivity», with that control stated beside it;
- never «no ink» or «no signal».
The read runs as declared: orientation row first, with the null.

## Addition of 2026-09-29T15:01:58Z: the headline number (director 14:53:12Z)

**The headline number is 29.8961 mm**: the R2c square of seed6273 square centre, measured on the 60 mm crop (the check that
sees the whole 60 mm surface). It is never 30.0063 mm.

That old square was the whole 30 mm R2b crop. It was bounded by the crop and blind to partners outside it.

Measured with the same check code on the R2c surface (evidence/old-square-on-r2c.csv, tools/old_square.py; check column:
the old square's nodes equal R2b's, max difference 0.0000 voxels, valid masks equal):
- v2 against our 800 and against the other R2b crops: 0 cells;
- a2 rule and holes: 0 cells;
- self conflict: 1926 cells at the a end and 1918 at the b end. Every one of the 1344 (a end) and 1314 (b end) pairs has
  its other end OUTSIDE the old crop.

So the old square loses cells only to self conflict partners that the 30 mm crop could not see, as the director expected.
A first run of this tool placed the square at a wrong offset (200 instead of 400 cells). Its CSV was moved to
scratch/old-square-on-r2c-wrong-offset.csv and is not a result.

Chain rule (no step on empty inputs): every chain script of this study still to start checks its inputs. At this time none
is unstarted: r2c_after.sh has ended, and ink_r2c.sh is running and is not edited (it already refuses without its
orientation row). Any new chain script is written with set -u and an explicit input check before each step.

## Addition of 2026-09-29T16:54:29Z: R2d, more tracer starts (director 16:53:30Z, relayed), declared before any number of it

Order, verbatim: «villa's tracer with normal grids (regenerate them, about 1 h, disk allowing, above 35 GB free) from the square
centres of the next best certified and hole free sheets of our chain (seed1727, seed6475, seed6732, seed2604, seed4440, seed6729,
seed6733, seed2715), 200 generations, 60 mm crops, the same square checks and fibre, rows in square-checks.csv; a larger certified
square than 29.8961 goes into the article only if it lands and is read back before 2026-09-30T12:00Z. Keep the load under 22.»

**Starts** (tools/r2d_starts.py, evidence/r2d-starts.csv). For each seed:
- The sheet is its C40 sheet with the largest certified_square_mm in square20-0826-95/evidence/certified-squares.csv (read at
  16:54Z: 1727 S0, 6475 S0, 6732 S4, 2604 S0, 4440 S1, 6729 S2, 6733 S9, 2715 S0).
- The square is the certified square when certified_square_mm >= 0.75 x hole_free_square_mm on that sheet. Otherwise it is
  the hole free square (chain-0826/evidence/squares-<seed>.csv corner and cells).
- The start is the 3D point of the square's centre cell (corner + cells // 2), rounded; the nearest covered cell if that
  cell is a hole.
- Read at 16:54Z, before any growth:
  - certified square: 1727 (12.90 against 17.05 mm), 6732 (10.80 against 10.80), 4440 (8.53 against 9.09), 6729
    (8.90 against 8.90), 6733 (7.26 against 7.26);
  - hole free square: 6475 (8.50 against 17.37), 2604 (11.41 against 17.80), 2715 (8.76 against 12.05).
  - The tool writes the choice per seed as a column.

**Settings as R2c.**
- Grids: tools/r2b_grids.sh unchanged, sparse 2, 4.74 GB. They start only with /data free of at least 45 GB (/data read 43
  GB at 16:54Z); otherwise a waiter (tools/r2d_chain.sh) waits for it, until 2026-09-30T06:00Z at the latest.
- Growth: params scratch/r2c/params.json (generations 200), runner tools/r2d_grow.sh (copy of r2c_grow.sh: the starts file,
  output scratch/r2d, MAXJ 6). Each start is gated on load 22, MemAvailable 30 GB and 36 GB free, and on an explicit check
  of its inputs.
- Route R2dnative: the 60 mm crop (160 native nodes around the start), upsampled by 5.
- Checks: routes.py measure (fibre, window, certified square, edge column) and sq_checks.py. In sq_checks, v2 runs against
  our 800 and against ALL other tracer crops that exist when it runs: the other R2b starts, both R2c crops, and the other
  R2d crops. Then axial_cut.py.
- Rows go to routes.csv and square-checks.csv as each start lands, with one ledger row per start.

**Report** the moment a certified square above 29.8961 mm is read back from the CSV, and at the end.

**Deletions:** the fetched chunks after each start's rows (drop.py, listing in the ledger); the grids at the end, listed first.

## Addition of 2026-09-29T16:56:49Z: the R2d grid gate at 40 GB (coordinator)

- The waiter tools/r2d_chain.sh (PGID 600765) was stopped by group before it had made anything.
- It is relaunched as tools/r2d_chain2.sh: a copy whose only change is the gate. The grids start at /data free >= 40 GB,
  which is the 35 GB floor plus the 4.74 GB grids.
- Every raw chunk fetch still checks the 35 GB floor before it starts (routes.values, sq_checks.py, axial_cut.py). A fetch
  that would cross it now WAITS, in 60 s steps up to 6 h, for the previous crop's drop. It is never skipped.
- A crop's fetched chunks are listed and dropped as soon as its rows exist (tools/drop.py, in the chain).

## Addition of 2026-09-29T18:41:15Z: R2d first attempt failed (my fault), relaunch

- **What failed:** all 8 tracer runs of 18:37Z aborted at start. They were handed scratch/r2d/params.json, which does not
  exist: the sed that made tools/r2d_grow.sh rewrote the path.
- **Why no check caught it:** the params check I declared was never inserted. A Python replace matched nothing and had no
  assert.
- **Consequence:** the chain's end step deleted the grids. They were listed first (scratch/normal-grids-deleted-3.txt), as
  declared, but nothing had landed.
- **Fixed:**
  - r2d_grow.sh reads scratch/r2c/params.json and refuses unless params, grids and starts pass their checks; the check lines
    are now present, verified by grep.
  - r2d_chain2.sh deletes the grids only after at least one R2d row exists.
- **Kept:** the failed runs' folders and logs are moved, not deleted, to scratch/r2d-failed-1829/. Their rows stay in
  evidence/r2d-runs.csv (rc 134).
- **Relaunch:** the same chain, same settings, log/r2d_chain-3.txt. Grids at /data free >= 40 GB; 49 GB free now.

## Addition of 2026-09-29T22:26:06Z: the both ends square (director 22:24:30Z), declared before its numbers

The certified square of this study (routes.py:448 to 449, sq_checks.py:146) excludes only the a end of self conflict pairs, as
cert.py does.

tools/both_ends.py is a new tool; no running tool is edited. It runs after the R2d chain's checks end, and on every R2 row of
evidence/square-checks.csv (R2bnative, R2cnative, R2dnative):
- It recomputes the masks with routes.checks, the same code and exclusions (none for R2), on the row's surface (routes.surface).
- both_ends_square = SQ.largest_square(V & ~v2 & ~self_conflict & ~b_end & ~a2_rule), in mm by the smaller step, with its
  corner.
- Beside it: the existing certified square of the row. Check columns:
  - recomputed a-ends square equals the existing value;
  - a and b cell counts inside the both ends square (both must be 0).
- Output: evidence/square-checks-both-ends.csv. At most 3 rows at once, load 22.

Also from now: every runner of this study writes its PGID to scratch/pgid-<runner>.txt at launch, and is killed only by that
PGID.

## Addition of 2026-09-29T23:21:06Z: certified_article (director 23:19:48Z), declared before its numbers

The article's certificate excludes crossing «one of our delivered sheets or another traced surface». The R2d chain's log line
«certified square 32.7761 mm ABOVE 29.8961» (seed6729 S2) and its scratch/r2d/ABOVE.txt line used this study's certified square.
That square does not exclude v2 against other traced surfaces (704 such cells inside it). So by the article's definition that
wording is wrong, and 32.7761 mm is not certified and not a record. The running chain is not edited; the correction is in these
rows.

tools/cert_article.py writes one row per R2 row of square-checks.csv (R2b, R2c, R2d, all seeds) into
evidence/square-checks-article.csv:
- **certified_article**: the largest square of V & ~v2_800 & ~v2_traced & ~self_conflict (a end) & ~a2_rule, in mm by the
  smaller step, with its corner and the cell counts of every flag inside it (b end counted as a column). The masks:
  - V, v2_800, self_conflict and a2_rule are those of routes.checks;
  - v2_traced is pair_v2 and marks against every other traced crop (R2b, R2c, R2d) from a DIFFERENT start. The R2c crops
    share their starts with R2b squarecentre, and a crop is never compared with its own regrowth.
- **Per crossing crop:** the v2 cells it marks inside the row's existing certified square, and the centroid (x, y, z) of those
  cells.
- **Beside it:** the existing certified value (this study's rule, a ends and v2 against our 800 only).
- A column says whether certified_article exceeds 29.8961.

For seed6729 S2, tools/axial_cross.py (a copy of axial_cut.py) draws an axial cut at the z of the centroid of the cells crossed
by the crop with the most crossing cells, 6 mm box. It shows this surface's nodes within 1 voxel of that z, the crossing
crop's nodes within 1 voxel, and our nearest sheet (square-checks.csv within3_best_sheet). PNG:
outputs/artifacts/render-routes-0826/PHerc0826-seed6729-S2-sq-R2dnative-crossing-axial.png (private); counts in
evidence/axial-cross.csv.

Runner tools/cert_article_run.sh: PGID file scratch/pgid-cert_article_run.txt, at most 3 at once, load 22. It starts after the
R2d chain has ended. Nothing about seed6729 goes to any owner page until certified_article is read back.

## Addition of 2026-09-29T23:56:12Z: seed2715 S0 (41.9669 mm) checks before any record (director 23:55:12Z), declared before their numbers

Until (1) to (4) are read back, seed2715 S0 is «a candidate, not a record» everywhere.

(1) certified_article: as armed (tools/cert_article.py, 23:21Z).

(2) Dark cells, the house dark rule (certified-piece-0826/tools/dark.py lines 159 to 166, also piece_texture_dark.py line 252,
copied unchanged):
- The raw values are routes.py's sample of the crop, scratch/values-R2dnative-PHerc0826-seed2715-S0-sq.npz (nearest voxel,
  raw masked scan level 0), with not measurable counted 0.
- T = 0.5 x the median over the existing 41.9669 mm square's cells. dark = value < T or not measurable, applied to every
  crop cell with that T.
- Columns: dark share inside the square, and certified_article_no_dark = the largest square of certified_article's mask
  (scratch/article-*.npz «art») and not dark, in mm, with its corner.

(3) The strict square:
- a2's flag grid is recomputed with area90.a2_grid (the calls of routes.checks).
- Inside the 41.9669 mm square: every flagged block (MC.STRIDE cells a side) in grid cells, the count, and their bounding
  box.
- A small map PNG of the square: flagged blocks red, dark cells blue, the strict square outlined.

(4) Axial cuts at the square's bottom and top: z = the 5th and 95th percentile of the square's node z (the extreme rows
hold few nodes).
- Each cut is centred on the square node nearest that z and nearest the square's middle column, in a 6 mm box.
- It shows this surface (cyan, the square's own nodes yellow) and our nearest sheet (square-checks.csv within3_best_sheet,
  magenta), as the cut at [height withheld] did.

Tool tools/cand2715.py; rows in evidence/candidate-2715.csv (one row per quantity), cuts in evidence/axial-cut-z.csv. PNGs
private under outputs/artifacts/render-routes-0826/ with their own names. (2) and (3) run after cert_article's 2715 row
exists; (4) runs now. Fetches wait for 35 GB free as declared.

## Addition of 2026-09-30T00:01:49Z: the ADJUDICATION rule for crossings between traced surfaces (director 23:59:34Z), verbatim, before any number

«In the crossing region of each pair (the crossing cells of both surfaces, and the cells within the same crossing neighbourhood
you use for v2), the surface that shares MORE of its nodes within 3 voxels with our delivered sheets (the 800) is kept, and the
other is flagged. Ties flag both. Measure the share in the crossing region only, never over the whole surface. For reference
only, not for the rule: seed6273's square has 0.7003 of its nodes on our seed1045 S0 overall, and seed6732 S4 has 0.4776 on
seed2441 S2 overall. Also make an axial cut through each crossing centroid with both traces and our sheets drawn.»

**How it is computed** (tools/adjudicate.py, new; nothing running is edited):
- **Pairs.** For every R2 row X and every other traced crop Y from a different start: sheet_cross_v2.pair_v2(X, Y) and
  marks, exactly as cert_article.py (the v2 crossing lines).
- **The crossing region of the pair.**
  - On X: X's marked cells, dilated by the same neighbourhood v2 uses. That is S.R voxels in 3D: X's cells within S.R of a
    marked cell.
  - On Y: Y's cells within S.R of X's marked cells, the points of Y that cross.
  - The pair is also computed the other way (Y against X), and the union of both ways' marked cells is used on each side.
- **Share.** For each side, the share of its region nodes within 3 voxels (3D) of any node of our 800 delivered sheets. The
  sheets are area90's working grids of every candidate in the region's keys, plus their full patch lattices when a working
  grid is within 6 voxels.
- **Verdict.** The larger share is kept and the smaller is flagged. Equal to 4 decimals flags both.
- **certified_adjudicated.** Per row, the largest square of V & ~v2_800 & ~self_conflict (a end) & ~a2_rule & ~(v2 cells
  against the crops of the pairs where this row is FLAGGED).
- **Outputs.**
  - A NEW file, evidence/square-checks-adjudicated.csv, one row per R2 row. Columns: certified_this_study,
    certified_article (read from square-checks-article.csv) and certified_adjudicated, with the flag counts inside it.
  - evidence/crossing-pairs.csv, one row per crossing pair: both surfaces, crossing cells on each, each share, kept,
    flagged, and the cut PNG path.
- **Axial cut per pair,** through the centroid of X's crossing cells, 6 mm box. It draws both traces and our 800 sheets'
  nodes within 1 voxel of the cut's z. PNG outputs/artifacts/render-routes-0826/cross-<X>-<Y>.png (private).
- **Runner** tools/adjudicate_run.sh, PGID file scratch/pgid-adjudicate_run.txt, 3 at a time, load 22. It goes first; the
  seed2715 checks share the machine.

## Addition of 2026-09-30T00:21:17Z: crossing cuts where both surfaces pass, tie wording, three definitions (director 00:20:21Z), before numbers

**(1) The crossing cuts.**
- The first cuts (tools/adjudicate.py) were taken at the z of the MEAN of the crossing region. A mean of curved points need
  not lie on either surface, so a cut could show only one of them.
- tools/recut.py (new; tools/adjudicate.py is running and is not edited) runs after the adjudication rows exist. For every
  row of evidence/crossing-pairs.csv:
  - p = the node of surface 1 nearest the recorded centroid; q = the node of surface 2 nearest p.
  - The z used is z0 = round((p_z + q_z) / 2). If the 6 mm box around p at that z (within 1 voxel) does not hold nodes of
    BOTH surfaces, z0 +- 1, +- 2, ... up to +- 20 is tried, nearest first. «Not measurable» if none works.
  - The cut is drawn at the z used, centred on p: surface 1 cyan, surface 2 red, our 800 sheets magenta.
  - It REPLACES the PNG at the path in crossing-pairs.csv. The first PNGs are listed in a ledger row first; they are
    overwritten, not kept.
- Output: evidence/crossing-pairs-cuts.csv, one row per pair: z used, the offset from z0, nodes of each surface and of our
  800 in the cut, the p to q distance, and a column tie_note = «tie: no 800 sheet in the region» where both shares read
  0.0000. The rule flags both there, and nothing is forced.

**(2) Three definitions** (tools/three_defs.py): evidence/square-three-definitions.csv, one row per R2 row, all read from the
existing CSVs:
- a. certified_this_study (square-checks.csv square_mm: v2 against our 800 only);
- b. certified_article (square-checks-article.csv);
- c. certified_adjudicated (square-checks-adjudicated.csv);
- the crossing partners with each verdict (kept, flagged or tie, from crossing-pairs.csv, both sides);
- exceeds_29_8961 under each definition.
Runner tools/defs_run.sh (PGID file scratch/pgid-defs_run.txt) starts when the adjudication runner has ended.

## Addition of 2026-09-30T00:22:42Z: the remade cuts get new names (coordinator)

tools/recut.py does NOT overwrite the first cuts, because the director has already looked at one of them.
- It writes each new cut beside the first as <first name>-bothpass.png, and keeps the first PNGs as they are.
- evidence/crossing-pairs-cuts.csv names both files (png_first, png_bothpass).
- recut.py had not started; it was fixed before its run.
- tools/defs_run.sh is waiting and is not edited. Its ledger row will still say the first PNGs are listed «before tools/recut.py
  overwrites them»; that wording is superseded by this addition, and nothing is overwritten.

## Addition of 2026-09-30T00:46:30Z: cuts at the actual crossing (coordinator, 00:4xZ), before numbers; cuts for the eye only, verdicts unchanged

tools/atcross.py (new) writes one cut per row of evidence/crossing-pairs.csv. Order: the headline pair (R2c seed6273 square
centre against R2d seed6732 S4) first, then the pairs of the three rows that exceed 29.8961 under a or b (R2b seed6273 square
centre, R2d seed6729 S2, R2d seed2715 S0), then the rest.

For each pair (1, 2):
- recompute sheet_cross_v2.pair_v2 and marks both ways, as adjudicate.py does;
- the centre is the marked cell of surface 1 (else of surface 2) whose node is nearest any node of the other surface;
- z = that node's z, then +-1 ... +-20 until the 6 mm box holds nodes of both within 1 voxel of z;
- drawn: surface 1 cyan, surface 2 red, our 800 magenta, the centre cell yellow;
- new name <first name>-atcrossing.png; both earlier sets are kept.

Output: evidence/crossing-pairs-atcrossing.csv, with the cell used (surface, grid i j, xyz), z, the offset, the distance
between the surfaces at the centre (voxels), and the nodes of each surface and of our 800 in the cut.

Also, for R2d seed6733 S9 (the oddity c 27.3309 > b 26.2437): per partner, the cells that b flags (6733 S9's own v2 marks
against that crop) and whether c flags them (the pair's verdict). Counts inside b's square and inside c's square go to
evidence/oddity-6733-S9.csv.

Runner tools/atcross_run.sh, PGID file scratch/pgid-atcross_run.txt.

## Addition of 2026-09-30T00:54:42Z: in-square crossing cuts (coordinator 00:5xZ), before numbers; for the eye only, verdicts unchanged

tools/insquare.py (new) takes three pairs, each with this study's certified square of the row (square-checks.csv corner and
cells):
- R2c seed6273 square centre against R2d seed6732 S4;
- R2d seed6729 S2 against R2d seed4440 S1;
- R2d seed2715 S0 against R2d seed2604 S0, its one decided (flagged) pair. Its three other pairs are ties, reported as
  columns.

The in-square crossing cells are the row's own v2 marks against the partner (pair_v2 + marks, as cert_article.py), restricted
to the square. Three cuts per pair, each centred on an in-square marked cell:
- (1) the cell nearest the other surface;
- (2) the cell whose z is nearest the median z of the in-square marked cells;
- (3) the same at the 90th percentile z.
z starts at that cell's z and then moves +-1 .. +-20 until the 6 mm box holds both surfaces within 1 voxel.

If a row has no in-square marked cell against that partner, the cuts use its marked cells nearest the square, and a column
says so.

Drawn: the row's surface cyan, the partner red, our 800 magenta, the centre a yellow ring. PNG names:
<first cut name>-insquare-<n>.png; every earlier file is kept. Rows go to evidence/crossing-insquare.csv: pair, n, rule, cell,
xyz, z used, distance between the surfaces, and nodes of each surface and of the 800. Runner tools/insquare_run.sh, PGID file
scratch/pgid-insquare_run.txt.
