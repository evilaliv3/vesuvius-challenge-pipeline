<!-- Shipped copy of best-windows-0826/DECLARATION.md, 2026-09-30, as the study wrote it. Where it says PRIVATE, private or never public it describes how the study kept its own outputs on the day it was written, before the owner's decision of 2026-09-30 to publish this article with no position on the scroll. -->
# best-windows-0826: the cleanest 20 x 20 mm windows on single delivered PHerc0826 sheets, declared 2026-09-29T06:14:07Z

Written by a coordinator agent before any number of this study exists (time from `date -u`). PRIVATE (raw prize scroll
work): textures, sections and ink outputs go only to /data/scrollagent/outputs/artifacts/best-windows-0826/, nothing into any
article or results/ folder. The article figure is a separate file under this study's article-figure/ for the director to look
at, never built into the article.

**Order** (director 2026-09-29T06:11:47Z, owner's word), verbatim:
«NEW PRIORITY, before the fill-holes work: the organisers never ask for a hole free square (First Letters: 10 letters within a
single 4 cm2 area; progress prizes: papyrus fibres visible on the output surface and no jump across sheets in cross section; raw
/prizes HTML read at 06:3xZ). Study best-windows-0826, DECLARATION first: a clean window is a 20 x 20 mm window (by the sheet's
steps) on one delivered sheet where covered cells are at least 0.95 of the window, cells flagged by any one lamina check (self
conflict either end, v2, a2 cluster rule) at most 0.01, and the fibre score inside the window at least 0.0680; search every
sheet whose certified piece passes the fibre bar (fibre-ranking.csv), largest pieces first, and rank windows by flagged share
then hole share. For the best 3 windows on 3 different seeds: (1) texture render at one pixel per cell with a 5 mm and a 1 cm
bar and flags marked in a second image; (2) two cross sections of the scan through each window (along i and along j at its
centre, the organisers' volume, raw) with the sheet's trace drawn, showing it stays on one layer; (3) the ink reader (both
checkpoints, both depth directions, null at half pitch) on each window. Into outputs/artifacts/best-windows-0826/ PRIVATE, one
PNG per panel, a CSV of the windows. Then a figure of the 0826 article from it (Times, Okabe-Ito, as the other figures), not
built into the article before I look. Deadline: windows by 10:00Z, renders and sections by 13:00Z, ink by 16:00Z. Machine and
disk: use it all above 35 GB free, delete fetched chunks after.»

## Population

Every row of certified-piece-0826/evidence/fibre-ranking.csv with passes_bar «yes» (the two summary rows excluded), in that
file's order (strict piece cm2, largest first). C40 and C80 sheets of the same seed are separate sheets but the same seed.

## Masks, per sheet, on the full lattice

From certified-piece-0826/scratch/piece2/<label>.npz where it exists, else scratch/piece/<label>.npz (the rule of fibre2.py).
Arrays used: valid, v2, self_conflict, b_end, a2_rule. Check column: the npz's strict piece
(valid & ~v2 & ~self_conflict & ~a2_rule & ~b_end, its largest 4-connected component, the npz's own «piece» array) has the
cell count of certified-pieces.csv (recomputed_piece_cells where recomputed, else piece_cells) as fibre2.py checks; a sheet
failing it reads «not measurable: mask differs». A sheet whose npz lacks one of the five arrays is recomputed with piece2.py's
path (computed_masks) or reads «not measurable».

- covered = valid.
- hole = ~valid (lattice cells with no grown point).
- flagged = valid & (v2 | self_conflict | b_end | a2_rule): v2 crossed or jumped; self conflict at either end of every
  lamina.conflicts pair (self_conflict is the a end as cert.py, b_end the b end as pairwise.py's conflict_pairs); a2 cluster
  rule holes (cert.py's a2r). Any one check suffices.

## Window

Steps step_i_mm, step_j_mm from certified-piece-0826/scratch/piece2/<label>.json (the sheet's squares file row).
cells_i = ceil(20 / step_i_mm), cells_j = ceil(20 / step_j_mm), so the window is at least 20 mm on each axis. Every top left
corner (i0, j0) with the window inside the lattice is scored exactly with summed area tables (int64):
- covered_share = covered cells / (cells_i x cells_j);
- flagged_share = flagged cells / (cells_i x cells_j);
- hole_share = 1 - covered_share.
Candidate: covered_share >= 0.95 and flagged_share <= 0.01. Candidate order within a sheet: flagged_share ascending, then
hole_share ascending, then i0, then j0 ascending.

## Fibre inside a window

fibre.py's window spectrum (bands, Hann window, mean removed, band power over non DC power; functions fibre.bands and
fibre.wscore imported unchanged), restricted to the window: tiles of 128 x 128 cells on a fixed grid inside the window, tile
corners at offsets 0, 64, 128, ... and the last one at cells - 128 on each axis (so the grid reaches the window's far edge;
8 x 8 = 64 tiles for a 535 to 536 cell window). A tile is accepted when all its 16384 cells are covered and not flagged, and
every cell's raw value (piece_texture.py's Raw2, nearest voxel of the raw masked scan 20250821151701 level 0, as fibre.py) is
measurable and not 0. window_fibre = median of the accepted tiles' scores, with IQR and count; fewer than 8 accepted tiles:
«not measurable» (the window is then not clean). The bar is fibre2.py's 0.0680 (passes when window_fibre >= 0.0680).

Values need raw chunks: the chunks under every covered cell of the window (nearest voxel) are fetched into this study's
scratch/raw-chunks, the shared caches read first, read only. The cells' values are saved in scratch/values/<label>-<i0>-<j0>.npz
so the renders do not fetch again.

Per sheet: up to 3 fibre attempts, in candidate order: the first candidate, then the next candidate whose centre is at least
10 mm (half a window) from every tried centre (so a failure is not retried on nearly the same place). The sheet's window is
the first attempt that passes the bar; none passing, the sheet reads «no clean window» with its attempts listed in
evidence/attempts.csv. Order of sheets for the fetches: by their first candidate's (flagged_share, hole_share), best first; a
sheet with no candidate reads «no candidate» and needs no fetch.

## Ranking

evidence/windows.csv: one row per sheet of the population (at most one window per sheet), columns label, source, seed, sheet,
step_i_mm, step_j_mm, cells_i, cells_j, window_mm_i, window_mm_j, i0, j0, i1, j1 (inclusive), covered_share, hole_share,
flagged_share, and each flag's share (v2, self conflict a end, b end, a2 rule), window_fibre, IQR, tiles accepted,
passes_fibre, status, attempts, fetch GB, rank. Rows with a clean window ranked by flagged_share, then hole_share (then label).
The best 3: going down the ranking, a window is taken when its seed is not already taken (C40 and C80 of one seed are one
seed).

## Disk

Before every fetch /data free is read with shutil.disk_usage; a fetch is made only when free minus the fetch stays above 35 GB,
else refused with a row in evidence/fetch-plan.csv («refused, free X GB») and, after 30 minutes of waiting in 60 s steps, the
window reads «not measurable: fetch refused». Fetches run at most 3 at once under a lock so each check sees the others'
reservations. After a sheet's attempts, its fetched chunks are listed in a ledger row and deleted, except while they serve a
best 3 panel not yet drawn (then listed and deleted after the panel).

## Panels for the best 3 (one PNG per panel, outputs/artifacts/best-windows-0826/)

(1) Texture: the window's raw values at one pixel per lattice cell (i down, j across), grey window p1 to p99 of the window's
nonzero covered values, holes white, masked or not measurable dark blue (render_surface.to_grey, as texture_best.py and
piece_texture.py), a 5 mm and a 1 cm bar drawn with the lattice step (min of step_i_mm, step_j_mm), title and caption lines.
Second image: the same grey dimmed with the flags coloured: self conflict (either end) magenta, v2 red, a2 rule green, holes
white. Files <n>-<label>-texture.png and <n>-<label>-flags.png.

(2) Cross sections, in the organisers' volume (raw masked scan 20250821151701 level 0, 9.362 um voxels, the same bucket and
caches as texture95.py and piece_texture.py), geometry: centre cell (ic, jc) = the window's centre; the i line is the
lattice cells (i, jc) for i in the window, their grown points p(i) (px, py, pz); the local normal n at the centre is the unit
cross product of the lattice tangents (central differences of p over +-8 cells along i and j at the centre, nearest valid
cells). The section plane passes through p(ic, jc), spanned by u = unit chord of the i line (last valid point minus first)
made orthogonal to n, and n. Each pixel (a, b) is the raw value, nearest voxel, at p(ic, jc) + a u + b n (one voxel per
pixel); a covers the trace's extent along u plus 40 voxels each side, b covers the trace's extent along n plus 40 voxels
each side (at least +-40). The trace drawn: every grown point of the i line projected on the plane (a = (p - c).u,
b = (p - c).n), coloured by its distance to the plane |(p - c).w|, w = u x n: within 3 voxels cyan, farther orange (the line
leaves the plane there, so the image cannot judge it). The same for the j line (cells (ic, j)). Columns in evidence/sections.csv:
points on the line, points within 3 voxels of the plane, the largest out of plane distance, the image extent, chunks fetched.
Files <n>-<label>-section-i.png and <n>-<label>-section-j.png. Whether the trace stays on one bright layer is read by eye
and written as a judgement, not as a number.

(3) Ink: ink-square-0826-seed2604/tools/run_one_v2.sh (fixed half pitch null, both depth directions, checkpoints seed42 and
seed43) on the window, with ink_piece.sh's lock dance (flock pairwise-cert-0826/scratch/ink.lock, the ink poller stopped by
group between squares, poll.sh and watch_locks.sh relaunched with setsid after), writing ink.html, never index.html. The
reader takes a square: side = max(cells_i, cells_j) cells, corner (i0, j0), stated in the sqid and the output. sqid
«<seed>-S<k>-<src>-bw-<rank>». Its own disk stop stays as the reader has it.

## Article figure

A tool in this study's article-figure/ builds, from the three panels' data (not from the PNGs), one figure in the house style
(results/figstyle.py and figpreamble.tex: Times, Okabe Ito), PNG and PDF into article-figure/ only. Never copied into the
article folder.

## Checks (columns, not prose)

Summed area shares checked against a direct count on the chosen window of every row (column sat_equals_direct).
Self tests in evidence/selftest.csv before the search: S1 a synthetic lattice with a known clean block: the search finds it
with covered 1 and flagged 0; S2 one flagged cell over 1 per cent of the window rejects it; S3 tiles grid for n = 535 gives 64
corners pairs inside the window.

## Addition 2026-09-29T06:21:14Z (after the search, about the procedure only)

Two sheets (C40 seed4480 S0, C40 seed1732 S1) stopped with «chunk neither fetched nor recorded absent»: the two seed groups
ran at once and one group's drop deleted chunks the other had fetched or counted as cached. The sampler refuses a missing chunk,
so no written value was affected (every written attempt sampled all its chunks). Both were rerun alone, one after the other,
with nothing else fetching, and their chunks dropped after. From now on this study fetches and drops in one process at a time.

## Addition 2026-09-29T06:23:23Z (director's addition of 06:21:28Z, relayed by the coordinator), written before any number of it exists

**Order**, verbatim: «our fibres are not horizontal and vertical like the others' renders. Measured (director script,
patch_0.bin of C40, angle of the grid's step vectors to the volume axes): the grid axis i lies at a median 24 to 38 degrees from
pz (the scroll's height axis) with an IQR of 13 to 29 degrees across the sheet (seed5364 24.4, IQR 18.8; seed6273 23.6; seed2604
27.6; seed6732 27.8; seed3648 37.8, IQR 29.0): Stevens' flattening leaves the sheet rotated and the rotation drifts across it.
The organisers' renders keep z vertical, so fibres come out horizontal and vertical, and the released ink model was trained so
(orientation-1447 measured balanced accuracy 0.9375 upright against 0.80 to 0.92 rotated). Orders, inside best-windows-0826:
(1) render every chosen window and the certified square of seed5364 AXIS ALIGNED: resample the sheet on a new grid whose v is
the scan's z and whose u is arc length along the sheet at constant z (from the sheet's own 3D points; or, as a first step,
rotate each render by the local angle of the grid to z measured in the window), declared first; (2) rerun the ink reader on the
axis aligned renders beside the current ones, same null; (3) show both renders side by side for me.»

**Angle column.** For every window (the best 3 and every clean window of windows.csv) and seed5364's certified square: per
lattice cell whose i neighbour (i+1, j) is also covered, d = p(i+1, j) - p(i, j) (3D, voxels); angle_i_to_z = the acute angle
between the line of d and the scan's z axis, degrees, arccos(|d_z| / |d|). Columns angle_i_to_z_median and angle_i_to_z_iqr
(75th minus 25th percentile) over the window's cells, and the same for the j step (angle_j_to_z_*). Tool tools/align.py,
output evidence/angles.csv.

**Full resampling, v = z, u = arc length at constant z** (the full method, not the rotation). For one window: the sheet's
points p(i, j) (px, py, pz) on its lattice; holes filled for the tracing only by normalized Gaussian convolution of the valid
points (sigma 2 cells; a resampled point is valid only when its nearest lattice cell is covered). Centre c = the window's
centre cell (nearest covered cell to it). The step h = the sheet's lattice step in voxels (the median 3D distance between
covered i neighbours in the window, about 4.0 voxels). Rows: z levels z_v = pz(c) + v x dz for integer v; columns: arc length
u_k = k x h along the curve of constant z on the sheet. u = 0 on the steepest ascent curve of pz on the sheet through c (in
the lattice's parameter space, marching along grad pz / |grad pz|^2 by dz per step, bilinear interpolation), so every row's
origin lies on one curve crossing all rows. Each row is traced from its origin both ways along the contour pz = z_v in the
parameter space (tangent perpendicular to grad pz, step h / 4 of 3D arc length, one Newton correction back onto z_v per step),
the 3D arc length accumulated, and the points at u_k = k x h taken by linear interpolation along the traced polyline.
dz = h, then corrected once so that the median 3D distance between vertically adjacent resampled points equals h
(dz_final = h x h / that median), so the surface is sampled at the same spacing both ways (the ink model's scale); dz_final is
a column. Output: a patch file in the reader's format (records x = k index, y = v index, px, py, pz, float32; x the columns,
y the rows, so z runs down the rows) under scratch/aligned/<label>.bin, covering the square of the window's size
(max(cells_i, cells_j) cells, 20 mm) centred on c, plus 64 cells of margin each side for the reader's 60 cell margin. The
aligned square is not the lattice window: it is the same size, centred on the same cell, rotated by the local angle; its own
covered and flagged shares (each resampled point read in the nearest lattice cell's masks) are columns of
evidence/aligned.csv, beside the window's own.

**Renders, side by side.** For each window and for seed5364 C40 S0's certified square (certified-squares.csv corner and
cells): the current render (lattice, one pixel per cell, as the panels above) and the axis aligned render (one pixel per
resampled point, nearest voxel of the same raw volume, the same grey window rule), side by side in one PNG,
<n>-<label>-current-vs-aligned.png, with the 5 mm and 1 cm bars, z shown as «z up» on the aligned half, and the lattice
window's outline drawn in the aligned half (the window's border cells mapped to the resampled grid). PRIVATE.

**Ink on the aligned renders.** run_one_v2.sh unchanged, given the aligned patch file as PATCH, the aligned square as the
square (corner at the margin, side as above), NI, NJ the aligned grid's size, STEP the sheet step in mm. So the aligned
surface goes through the same path as the current one: patch2tifxyz, cut with the 60 cell margin, vc_render_tifxyz 28
slices along the normal, sq.py orient (the multiple of 90 degrees chosen by the same rules), both checkpoints, both
directions, the same null (gap minima, else fixed half pitch). The only change is the resampled surface. sqid
«<seed>-S<k>-<src>-bw<rank>-aligned» beside «<seed>-S<k>-<src>-bw<rank>» for the current lattice. The ink rows gather into
evidence/ink.csv with a column render = «lattice» or «axis aligned». The reader keeps its own disk stop (40 GB free, and a
fetch bound that must leave 40 GB): if /data is under it, the run stops and the row says so; that stop is not changed here.

## Addition 2026-09-29T06:30:29Z (after the first section of bw1 was drawn; geometry of the sections and of the resampling)

(a) Sections. The first section of bw1 (plane spanned by the i line's chord and the centre normal) kept only 103 of 509 trace
points within 3 voxels of the plane (largest 38.8 voxels): the line bends sideways. From now on the plane is the best fit plane
of the line's points through the centre cell: u = its first principal direction (across, signed from the first to the last
point), the second principal direction (up) signed along the local normal; the angle by which the local normal leaves that
plane is a column (normal_out_of_plane_deg). The trace is drawn 3 x 3 pixels per point. The first row is kept as
evidence/sections-chord-plane-superseded.csv (renders-first-pass-superseded.csv for the render row of the same pass).
(b) Resampling, as implemented before any aligned render was judged: holes filled for the tracing at sigma 2, 8, 32 cells; the
tracing runs on that field smoothed at sigma 1.5 cells, three Newton steps per trace step; a trace step that jumps (3D length
over twice the step) or lands more than 0.5 voxel off its z level ends that row's trace; the resampled point is read from the
unsmoothed field at the traced parameters, and a point more than 2 voxels off its z level is dropped (points_dropped_off_z).

## Addition 2026-09-29T06:31:04Z (supersedes (a) of 06:30:29Z, before any judgement of a section)

The best fit plane of (a) came out nearly parallel to the sheet (the local normal 69 and 78 degrees out of it for bw1's i and
j lines: the lattice lines bend inside the sheet, not across it), so it is not a cross section. Its row is kept as
evidence/sections-best-fit-plane-superseded.csv. The sections contain the local normal n (up), as first declared; u (across) =
the first principal direction of the line's points projected on the plane perpendicular to n (signed from the first to the
last point), the plane containing n that keeps the line's points closest. Trace drawn 3 x 3 pixels, cyan within 3 voxels of
the plane, orange farther; the counts are columns.

## Addition 2026-09-29T06:46:40Z (owner's decision relayed by the director at 06:38:48Z; director's look at 06:40:06Z), written before any number of it exists

**Axis aligned path.** Only the true correction is used, never a rotation: v = the scan's z, u = arc length along the sheet at
constant z. This study's align.py already does that (addition 06:23:23Z) and no rotation was made. render-routes-0826 is
writing its own regrid (runs/rev1/render-routes-0826/tools/regrid_z.py); once the director chooses the render path from the
w016 control, the axis aligned renders and the axis aligned ink reads of the best windows are redone with it, and the rows of
this study's own regrid are kept beside them, labelled «align.py regrid». The ink reads already running (tools/ink.sh,
launched 06:33:12Z) go on unchanged, their axis aligned rows labelled so.

**Straightened sections**, replacing the planar sections as the judgement of «one layer» (the planar ones stay as files).
For each target (bw1, bw3, bw4 and seed5364 C40 S0's certified square cert5364) and each of its two centre lines (the lattice
line i through the window's centre column jc, and the line j through its centre row ic; the centre cell as in the planar
sections): one column per grown point of the line, in lattice order (a point missing on the line leaves a white column).
The normal of a point is the unit cross product of the lattice tangents at that cell, central differences over +-2 cells
along i and along j (nearest covered cells, as the renders' grid gives them), smoothed along the line by a moving mean over
9 points and renormalised, its sign chosen so that it agrees with the window centre's normal. Rows: offsets t = -60 .. +60
voxels in steps of 1 voxel along that normal (121 rows, +t up). Sampling: nearest voxel of the raw masked scan 20250821151701
level 0 (as every render here). The traced sheet is the middle row (t = 0), drawn as a faint cyan line on a second copy
under the plain one. Scale bars: 1 mm and 5 mm along the columns (column spacing = the median 3D distance between consecutive
points of the line) and a 1 mm bar along the rows (107 voxels). The picture is magnified 2 x in both directions for
viewing, stated on it. Files: outputs/artifacts/best-windows-0826/straight-<label>-i.png and -j.png (for cert5364 the label
carries «-cert»).

Column of evidence/straight.csv, per section: peak_offset_median_vox = the median over the line's columns of |t*|, t* the
offset of the brightest voxel within t = -15 .. +15 in that column (columns with no measurable value skipped); also the share
of columns with |t*| <= 3 voxels, the number of columns, and the 25th and 75th percentiles of |t*|. A small median means the
brightest layer near the trace sits on the middle row; it is a number to check against the picture, not a proof.

**Article figure**: panels (c), (f), (i) become the straightened section along j of each best window (the same arrays,
from scratch/panel-data/straight-<tag>.npz); the texture panels stay until render-routes-0826's R1 render lands and passes.

## Addition 2026-09-29T07:24:22Z (director's orders of 07:22:16Z relayed by the coordinator), written before any number of it exists

(a) The 8 ink reads of 06:33Z all ended «not measurable» (seven on the reader's old 40 GB floor, bw1 lattice rc 1 with no
summary); evidence/ink.csv keeps those rows. They are NOT rerun on the old render path. The coordinator changed the copy
tools/run_one_v2_bw.sh at 07:22Z (the floor 40 became 35, the director's lowering). The 8 reads (lattice and axis aligned for
bw1, bw3, bw4, cert5364) run again only through the corrected render path that positive-control-0139 names; until that tool
is named they wait. The new rows go beside the old ones with a column naming the render path.
(b) Axis aligned figures by render-routes-0826/tools/regrid_z.py (used read only, its selftest of 06:48:05Z passing): run
--input <the sheet's patch_<k>.bin> --umbilicus field-0826-0800/scratch/20250821151701-umbilicus-20260808113303.json (the
published 0826 umbilicus orient_0826.py reads) --box <the window's i0 i1 j0 j1 grown by 64 cells, clipped> --out
scratch/regrid-z/<tag> --label bw-<tag> --csv evidence/regrid-z.csv, every other option its default. The output grid is
sampled at its valid nodes, nearest voxel of the raw scan, grey p1 to p99, z up. These are pictures only: no number of this
study is computed from regrid_z.py output. Files outputs/artifacts/best-windows-0826/<tag>-<label>-regridz.png, and a
three way PNG <tag>-<label>-lattice-alignpy-regridz.png (lattice | align.py | regrid_z.py). The queue item and every caption
say which tool each axis aligned panel used.
(c) Article figure: the axis aligned column uses regrid_z.py's render (said in the panel title); the section column is the
straightened section along j; under each section panel a one line statement from evidence/straight.csv: the median peak
offset and the share within 3 voxels beside the chance value (7.5 voxels, 0.226), and where the share is not above 0.226
the words «not shown to stay on one layer».

## Addition 2026-09-29T07:28:18Z (coordinator's note of 07:2xZ, after the regrid_z.py pictures were drawn)

Correction to (b) of 07:24:22Z: «its selftest of 06:48:05Z passing» was read from the last rows of
render-routes-0826/evidence/regrid-selftest.csv, where T2's shear row reads «information». As first declared, T2's bar was
0.5 degrees and it measured 0.622, a fail; the director allows regrid_z.py for figures only with that failure stated. Every
regrid_z.py panel of the article figure and its caption (article-figure/best-windows-caption.txt) now says: «regrid_z.py
(render-routes-0826); its self test T2 failed its bar as first declared, 0.622 against 0.5 degrees; picture only, no number».

## Addition 2026-09-29T07:36:17Z (coordinator's note after render-routes-0826 evidence/offsheet.csv), before any new picture

The regrid_z.py pictures are redrawn with its new option --max-dist-3d 8 (self test T7 of 07:34:18Z), every other option as
in (b) of 07:24:22Z; the earlier outputs are moved to scratch/regrid-z-nomaxdist/ (kept, not used). Captions keep the T2
failure statement and add «nodes farther than 8 voxels from the sheet removed; some edge swirl remains». Pictures only.

## Addition 2026-09-29T08:23:30Z (director 08:22:08Z, relayed by the coordinator), written before any read of it

**Order**, verbatim: «the orientation that the organisers' 9.362 um w016 surface reads best at is only meaningful for THAT
grid; for our lattice the right orientation must come from geometry (z up, recto facing the reader); so every 0826 reading
is redone in all 8 orientations and both directions, reporting the best and the spread, with the null, on the best windows
and the certified square first». The render path is the current renderer (NCC 1.0000 against the organisers' renders).

**Reads.** Targets bw1, bw3, bw4, cert5364, lattice render only (the regrid is for figures only). For each target and each of
the 8 in plane transforms (k quarter turns counter clockwise, numpy rot90, then a left right mirror if m; k 0..3, m 0..1, as
orient_0826.py's TRANSFORMS), forced explicitly in place of sq.py orient's choice: both depth directions (forward, reverse),
both checkpoints (seed42, seed43), the null as run_one_v2.sh (gap minima, else the fixed half pitch 7.5625 voxels). Tool
tools/run_one_v2_or.sh, a copy of tools/run_one_v2_bw.sh (floor 35 GB) with three changes only: (1) two more arguments K M
replace the orientation that sq.py orient prints (sq.py orient still runs and writes its row); (2) a third argument BASE:
when BASE differs from the sqid, the base read's renders (the nine zarr and the tifxyz inputs) are linked, not rendered
again, so the 8 orientations read the same pixels; (3) a run that did not render (BASE differs) deletes no cache chunk (only
the rendering run lists and deletes the render chunks it fetched, as run_one_v2.sh does). sqid «<seed>-S<k>-<src>-<tag>-k<K>m<M>».
One rendering read at a time; orientation reads of rendered targets run up to 3 at once, each infer with 6 threads.

**Geometry's prediction**, computed before any read and written as one row per target of evidence/orient-predicted.csv:
the window's grid through sq.py orient (orient_0826.py's two rules on the window with the published 0826 umbilicus: rows
carry z as the organisers render it, and d/dcol x d/drow points along the outward radial, orientation-1447's w035
convention for the recto facing the reader); columns: the side rule's (k, m), the PR 1899 rule's (k, m), their agreement, the
axis share and agreements, and the direction the radial rule gives.

**Table**, evidence/orient-reads.csv: one row per target, transform, direction and checkpoint (the rows of summary_v2.py:
c_sheet, c_null, tile wins and losses, signal), and evidence/orient-summary.csv: per target and checkpoint and direction,
the best transform by c_sheet_over_c_null, its signal, the spread (max minus min of c_sheet_over_c_null over the 8 transforms
and the count of transforms with signal yes), and whether the best is the predicted one. Reads that stop read «not
measurable» with the reason.

**Disk.** A rendering read starts only when /data has at least 36 GB free (the reader stops at 35); the waiting is logged.

## Addition 2026-09-29T08:52:36Z (director's ruling of 08:52:07Z, relayed by the coordinator), written before any orientation read has finished

Verbatim: «on the organisers' own w016 surface the best orientation is NOT the same for the two checkpoints (seed42 k3m1
0.7609, seed43 k1m1 0.7671, which are 180 degrees apart) and the 8 orientations spread 0.6454 to 0.7609 and 0.6761 to 0.7671
(control.csv, forward, k 4): the maximum over 8 orientations x 2 directions x 2 checkpoints is a selection. So the PRIMARY
reading on each 0826 target is the orientation geometry predicted before reading (orient-predicted.csv: bw1 k0m1 reverse, bw3
k3m0, bw4 k2m0, cert5364 k3m0), with its null; the other 31 are descriptive, and any 'best of 32' is compared only against the
best of the same 32 on the null surface, never against a single null.»

Consequences here: evidence/orient-summary.csv keeps its columns, but the primary result per target is the predicted
transform's row (predicted = yes) with its null; the best_* columns are descriptive and are not reported as a signal. A «best
of 32» on the sheet is compared only with the best of the same 32 on the null copies, a column added when the reads exist
(not computed now). Load: the batch goes from 4 reads at once to 2 (the runner stopped by group between reads and
relaunched with NPAR 2; finished reads are skipped; the predicted transforms stay first).

## Addition 2026-09-29T20:15:24Z (director 20:10:55Z, relayed by the coordinator: are other people's surfaces better fitted than ours?), written before any number of it

**Question.** The straightened section statistic of tools/straight.py (evidence/straight.csv), unchanged, on surfaces made
by others, beside ours. Output: ONE file, evidence/straight-others.csv, one row per surface and line, the random peak
baseline beside each row. Nothing else of this study changes.

**Statistic, exactly straight.py's.** Along a grid line through a centre node: one column per grid node of the line; the
normal of a node = unit cross product of the grid tangents, central differences over +-2 nodes along each grid axis
(nearest valid node up to 4 away, as straight.py's tangent()), smoothed along the line by a moving mean over 9 nodes and
renormalised, signed to agree with the centre node's normal; rows t = -60..+60 voxels in steps of 1 voxel of the surface's
own scan; nearest voxel; t* = offset of the brightest voxel within t = -15..+15; columns with a non measurable value in
that range skipped; median |t*|, q25, q75 and the share with |t*| <= 3. Random peak baseline beside every row: median 7.5
and share 7/31 = 0.2258 for a peak placed uniformly on the 31 offsets (arithmetic, as in the queue item of 06:48:56Z).
Parameters are in grid nodes, as straight.py's; since the grids differ, the node spacing in voxels and in mm and the
tangent baseline in voxels (2 x spacing) are columns. Line length: 20 mm (the window size of this study), i.e.
ceil(20 mm / node spacing) nodes centred on the centre node, clipped to the grid; nodes that are invalid leave a column
out. Tool tools/straight_others.py (new; its straightened section code is straight.py's line() and statistic, copied,
with the sampler replaced by a generic one for the three scans: uncompressed 128^3 uint8 zarr chunks from the open data
bucket, nearest voxel, into this study's scratch/raw-chunks-others/).

**Surfaces.**
- (a1) PHerc0139, the organisers' public segment 20250108000004-w029, which carries the label set pherc0139-w016 (the
  labels director and coordinator call «w016»): its 9.362 um tifxyz on volume 20250728140407
  (ink-labels-0139/data/PHerc0139/segments/20250108000004-w029_2025010827/mesh/...-9.362um.tifxyz, scale 0.05, node
  spacing about 20 voxels). Centre: the node of that tifxyz nearest the mean of the clean held out label points already
  in 20250728140407 voxels (positive-control-0139/scratch/labels-9362.npz «p», 171,693 points; map_labels.py's affine,
  checks (a) 0.5732 and (b) 0.5620 voxels). Scan: PHerc0139 20250728140407 9.362 um masked zarr level 0.
- (a2) PHerc0139, the organisers' public segment 20260126000000-w045, which carries the label set pherc0139-w029 (the
  coordinator's «w029»; its label zarr names this segment's surface volume): its 9.362 um tifxyz on 20250728140407.
  Centre: the mean of the labelled pixels (supervision mask non zero, any channel) mapped as map_labels.py maps a label
  pixel: level 2 (r, c) -> 2.399 um tifxyz grid (0.05 (4r + 2), 0.05 (4c + 2)), bilinear, then map_labels.py's affine A
  into 20250728140407 voxels; the nearest node of the 9.362 um tifxyz. Distance from that mean to the node is a column.
  If the word «w029» meant the scroll PHerc1667 w029 (the third held out region of ink-finetune-k1), that surface is not
  read here: no 1667 scan or tifxyz of it is in this study's inputs; said in the CSV header.
- (b) PHerc1447, Youssef Nader's w062 (dataset YoussefMoNader/ink-8um-pherc1447-surfaces at 7e4d918712a8, CC-BY-NC-4.0,
  private, redistributed nowhere): tifxyz/x.tif, y.tif, z.tif, meta.json fetched (not on disk; the SHA256SUMS of
  ink-v8in-0826/scratch/hf/ds1447 checked after the fetch) into scratch/w062-tifxyz/; scale 0.25, node spacing about 4
  voxels. No labels: centre = the valid node nearest the centroid of the valid nodes. Scan:
  PHerc1447/volumes/20250521151220-8.640um-1.2m-116keV-masked.zarr level 0 (the README's source volume; 8.64 um from the
  volume's name and the README, the voxel size column). Offsets are in voxels of that scan (8.64 um), said per row.
- (c) ours: the R2c seed6273 square, read back from render-routes-0826/evidence/square-checks.csv (the row route
  R2cnative, surface PHerc0826-seed6273-squarecentre: i 4.0 / 0.4553, j 8.0 / 0.2692), copied, not recomputed.
- The rows of this study's own straight.csv (bw1, bw3, bw4, cert5364) are copied beside them as further «ours» rows.

**Fetch sizes** (sized before any fetch, evidence/straight-others-fetch.csv): the w062 tifxyz (about 30 MB by the
coordinator's figure; sizes from the dataset API before fetching) and, per surface, the scan chunks under the two lines'
+-60 voxel columns only. /data must stay at or above 42 GB free, read before every fetch; inputs asserted non empty. At
most 2 cores, nice 10. Fetched chunks listed in a ledger row and deleted after the rows exist. Start only after the
coordinator says the v8-in quick look PNGs exist.
