<!-- Shipped copy of certified-piece-0826/DECLARATION.md, 2026-09-30, as the study wrote it, except one quotation of the owner, rendered in English and marked so. Where it says PRIVATE, private or never public it describes how the study kept its own outputs on the day it was written, before the owner's decision of 2026-09-30 to publish this article with no position on the scroll. -->
# certified-piece-0826: the largest connected certified piece of each delivered PHerc0826 sheet, declared 2026-09-28T22:22:32Z

Written by a coordinator agent before any number of this study exists. PRIVATE (raw prize scroll work), never public.

**Order** (director 2026-09-28T22:21:04Z, on the owner's word «above 4 cm2 / 20 mm, on a single lamina» (the owner's words, rendered in English)), verbatim:
«Pairwise read back: best 15.7059 (seed5364, now bound by v2), seed2604 C80 S0 10.0315: its fold is inside the square, so
no 20 mm square exists among the delivered sheets. Second measure, declared now, the owner's 4 cm2 as AREA: per sheet, the
largest 4-connected piece of certified cells (the strict mask cert = valid & ~v2 & ~sc & ~a2r of cert.py, both ends of every
self conflict pair excluded), area in cm2 = cells x step_i_mm x step_j_mm on the full lattice; column
largest_certified_piece_cm2 plus its bounding box and cells, beside the squares, never replacing them. Self test: a synthetic
mask with two pieces joined by one excluded column gives two pieces. Order: seed2604 C80 S0, seed5364, then every sheet with
certified_cells x step^2 of 4 cm2 or more, then all. The best piece, if 4 cm2 or more: texture with the piece outlined (cyan)
and excluded cells (magenta, red) into outputs/artifacts/square-0826-seed2604/piece-*.png, the ink reader on its bounding
box. Ledger and queue item by 03:30Z.»

**What the measure is.** A connected AREA of certified cells on one sheet's own parametrisation lattice. It is not a square,
and it is not the prize's 20 mm square; the squares of square20-0826-95/evidence/certified-squares.csv and
pairwise-cert-0826/evidence/pairwise-squares.csv stay as they are, and this study's column stands beside them.

**Mask.** Exactly cert.py one()'s mask on the full lattice: `cert = valid & ~v2 & ~sc & ~a2r` (valid: covered cell; v2:
crossed or jumped, nearest working cell; sc: lamina.conflicts(W, W, pitch, True) at one pitch, nearest working cell; a2r: a2
cluster rule holes). The masks come from cert.py's own code path, reproduced as square20-0826-95/tools/check_best.py and
pairwise-cert-0826/tools/pairwise.py already do (reuse branch for the C40 sheets whose sha256 equals area-0826-90's sheets
json, computed branch otherwise; cert.py, lamina.py, area90.py imported unchanged). «Both ends of every self conflict pair
excluded»: lamina.conflicts flags the a end of each pair; the b ends come from pairwise.py's conflict_pairs (imported
unchanged, its flag checked equal to lamina.conflicts' per sheet). The measured mask is `piece_mask = cert & ~B`, B the full
lattice cells of every b end (nearest working cell). Column `b_end_extra_cells` counts cells of B not already in sc; when it is
0 the piece mask is cert.py's cert exactly.

**Piece.** scipy.ndimage.label with 4-connectivity (the cross structure, no diagonal contact) on piece_mask. Largest piece by
cell count; its area `largest_certified_piece_cm2 = cells x step_i_mm x step_j_mm / 100`, step_i_mm and step_j_mm read from the
sheet's squares file row (chain-0826/evidence/squares-<seed>.csv for C40, square20-0826-95/evidence/squares-<seed>.csv for C80,
as cert.py.where names them), not certified-squares.csv's single step_mm. Columns: largest_certified_piece_cm2, piece_cells,
piece_bbox (i0 i1 j0 j1, inclusive, full lattice), piece_bbox_mm_i and _j (extent x step), piece_all_certified (check: every
piece cell is in cert.py's cert, yes or no), recomputed counts equal the certified-squares.csv row (yes or no), second largest
piece (cells and cm2), number of pieces. Every certified-squares.csv column is copied unchanged beside them. A sheet whose
masks cannot be reproduced (a2 reference differs, pairs flag differs) is «not measurable», never 0.

**Self tests** (evidence/selftest.csv, one row each, with its bar):
- P1: synthetic mask, two 6 by 6 blocks joined by one column; with the column excluded: 2 pieces; control, column kept: 1.
- P2: two blocks touching only at a corner: 2 pieces (4-connectivity, no diagonal).
- P3: area formula on a synthetic piece of known cells and steps.
- P4: seed5364 C40 S0: recomputed cells, v2, self conflict, a2 rule, certified cells and certified square equal
  certified-squares.csv (certified_cells 1262883); the largest piece contains the certified square (15.3693 mm, corner from the
  row); every piece cell is certified.

**Order of sheets.** C80 seed2604 S0; then every seed5364 sheet (C40 and C80); then every sheet with certified_cells x
step_i_mm x step_j_mm of 4 cm2 or more, largest first; then all the others. At nice 10, at most 4 processes, no new start when
/proc/loadavg reads 22 or more.

**At 4 cm2 or more** for the best piece: a copy of pairwise-cert-0826/tools/pairwise_texture.py in tools/ renders the texture
of the piece's bounding box with the piece outlined in cyan and excluded cells coloured (self conflict magenta, v2 red, a2
orange, holes white) into outputs/artifacts/square-0826-seed2604/piece-<label>-{grey,marks}.png; then the ink reader
ink-square-0826-seed2604/tools/run_one_v2.sh on the bounding box (the smallest square covering it if the reader takes only
a square, said so in the output), sqid «<seed>-S<k>-<src>-piece-<cm2>», writing ink.html, never index.html, with the ink
poller stopped by group before and relaunched after, never at the same time as pairwise-cert-0826/tools/reach.sh.

## Addition 2026-09-28T23:22:35Z (director's order of 23:21:39Z), written before any number of it exists

**(a) Reused masks.** Rows whose masks came from area-0826-90 (masks «reused from area-0826-90», partners «area-0826-90»)
had a v2 crossing check that saw only the collection's own sheets, not the 800. They carry no number until recomputed. New
tool tools/piece2.py (piece.py unchanged, its running runner untouched until stopped by group between sheets) recomputes
them with cert.py's computed branch exactly: a2 by area90.a2_grid and the cluster rule, v2 by V2.pair_v2 and V2.marks
against every one of the 800 whose keys meet the sheet's dilated keys plus every measured sibling of the same collection,
self conflict by lamina.conflicts at one pitch, b ends by pairwise.py's conflict_pairs. Output scratch/piece2/<label>.json.
Every existing column and value of evidence/certified-pieces.csv stays unchanged; a new column `piece_mask_status` reads
«reused mask, not counted» for a reused row until its piece2 json exists, then «recomputed with the 800 and the siblings»,
and new columns carry the recomputed values (recomputed_piece_cm2 and the rest). Rows computed here read «computed here».
Order: the reused rows among the 4 cm2 group, largest first, then the open variant (b), then all.

**(b) Open variant, beside the plain piece.** Disc of radius 0.5 mm, in cells per axis ri = 0.5 / step_i_mm and
rj = 0.5 / step_j_mm (steps of the sheet's squares row): the structuring element is the cells (di, dj) with
(di / ri)^2 + (dj / rj)^2 <= 1. The strict piece mask (as above: cert.py's cert with both ends of every self conflict pair
excluded) is opened: erosion then dilation by the disc, cells outside the lattice counted as excluded. The opened mask is
labelled with 4-connectivity. For each of the 10 largest opened components (by opened cells), its piece is the certified
cells within 0.5 mm of it: the component dilated by the same disc, intersected with the strict mask. The open piece is the
largest of these by cells. So no two parts are joined by a strand narrower than about 1 mm. Columns:
largest_certified_piece_open_cm2, open_piece_cells, open_piece_bbox, n_open_components. piece_fill = piece cells over its
bounding box cells, for the plain piece (piece_fill) and the open piece (open_piece_fill).
Self test O1 (evidence/selftest.csv): two 120 by 120 blocks 20 cells apart at step 0.0374 mm, joined by a strand 2 cells wide
(0.075 mm, under 1 mm): 2 open pieces; joined by a joint 60 cells wide (2.2 mm, over 1 mm): 1 open piece. O2: an isolated
single block keeps all its cells after the opening and re-expansion (the piece equals the block).

**(c) For the owner.** seed3648 C40 S0 (computed here, 27.9846 cm2 plain): tools/piece_texture.py into
outputs/artifacts/square-0826-seed2604/piece-seed3648.png (grey with the cyan outline) and piece-seed3648-marks.png, after its
own fetch budget check. Ink read: an estimate row (evidence/ink-estimate.csv) first, from the last runs' rates (window pixels,
minutes, fetch bound GB); the piece's bounding box is read only if it finishes before 06:00Z and stays above the reader's 40 GB
stop on /data; otherwise the sheet's largest hole free square from its squares file row. sqid «seed3648-S0-C40-piece-<cm2>» or
«seed3648-S0-C40-square-<mm>».

## Addition 2026-09-29T00:22Z (director's order of 00:21:25Z), written before any number of it exists

**Dark cells.** The marks image of seed3648 C40 S0 shows dark bands (low scan value), possibly surface running in a gap, which
no check of ours sees. Rule, as finally stated by the director: sample every piece cell with piece_texture.py's sampler (nearest
voxel of the RAW masked PHerc0826 scan 20250821151701, level 0, at the cell's px, py, pz; render_surface.Raw.sample). Threshold
T = 0.5 x the median raw value over the piece's cells, sampled the same way (the median over all piece cells, stored 0 included).
A piece cell is dark when its value is under T; a cell whose stored value is 0 (masked) or not measurable counts as dark.
Columns, beside every existing one, for the strict piece and the open piece each: piece_dark_share = dark cells / piece cells;
piece_bright_cm2 = (piece cells - dark cells) x step_i_mm x step_j_mm / 100; plus the median, T and the counts. Tool
tools/dark.py (new; imports piece_texture.py's Raw2 and fetch loop unchanged in behaviour), output evidence/dark-pieces.csv.
Order: seed3648 C40 S0 (chunks cached by its render, no fetch), then seed2427, seed4391, seed6206 C40 S0. Before each sheet a
row of evidence/dark-fetch-plan.csv (chunks needed, cached, to fetch, GB, /data free); fetch only when /data stays above 35 GB
free after it and the run fits before 05:30Z; otherwise the sheet's row reads «not measurable: fetch refused (free X GB)».
Then seed2427 C40 S0 is rendered by a copy of piece_texture.py with the dark cells shaded blue in the marks image
(piece-seed2427.png, piece-seed2427-marks.png). The raw chunks fetched into this study's own scratch/raw-chunks are deleted
after the values are written, listed in a ledger row first.

## Addition 2026-09-29T01:24:25Z (director's order of 01:21:47Z), written before any number of it exists

**Fibre score.** Question: does the raw texture of a certified piece show the papyrus fibre grid (seed3648 C40 S0 does by eye;
seed2427 C40 S0 shows a smooth even grey with polygonal holes)? Nothing of this goes into the article.
Sheets, in this order, all C40 S0: seed3648 (reference, fibre visible), seed2427, seed4391, seed6206, seed3412, seed5364.
Piece = the strict piece mask of scratch/piece2/<label>.npz, or scratch/piece/<label>.npz where piece2 holds none (as dark.py).
Steps step_i_mm, step_j_mm from scratch/piece2/<label>.json (the sheet's squares file row).

Windows. 128 by 128 lattice cells. numpy default_rng(20260929), restarted for each sheet; each draw is a top left corner
(i, j), i uniform in [bi0, bi1 - 127], j uniform in [bj0, bj1 - 127] (the piece's bounding box, inclusive). A draw is accepted
when all 16384 cells are piece cells AND every one has a sampled value that is measurable and not 0 (0 = masked voxel). Draws go
on in sequence until 64 windows are accepted or 200000 draws are made; drawn, accepted by the mask, and accepted are recorded.
If fewer than 64 are accepted the score is the median of those accepted, with the count; none accepted reads «not measurable».

Values. Nearest voxel of the raw masked scan 20250821151701 level 0 at the cell's px, py, pz (piece_texture.py's Raw2, the
render's sampling). For seed3648 and seed2427 the values are read from scratch/texture/<label>.csv, written by piece_texture.py
with that same sampler over the bounding box and 60 cells around it (every piece cell), so no fetch. For the other four the
chunks under the mask accepted windows (and under the crop below) are fetched into this study's scratch/raw-chunks, the shared
caches (chain-0826, square20-0826-95, pairwise-cert-0826) read first, read only.

Spectrum of one window. v = value minus the window mean; v x H, H = outer(hanning(128), hanning(128)) (numpy.hanning, the Hann
window); P = |fft2|^2. Integer frequency indices ki, kj in -64..63 (numpy fftfreq x 128); the period along i of index ki is
128 x step_i_mm / |ki| mm, along j 128 x step_j_mm / |kj| mm. Band I: 128 x step_i_mm / 0.6 <= |ki| <= 128 x step_i_mm / 0.15
and |kj| <= 2. Band J: the same with i and j exchanged. Half width of each band around its axis: 2 frequency bins (|k| <= 2 on the
other axis, 5 bins wide). The two bands do not overlap (|k| >= 7.9 on the band axis). Total = sum of P over all bins except
(0, 0). window score = (sum of P over band I union band J) / total. fibre_score = median of the window scores; IQR = 75th
minus 25th percentile. For white noise the expected score is the band's share of the non DC bins (written in the CSV).

Self test (evidence/selftest.csv, rows F1 to F3, the same window code, synthetic 600 by 600 texture at step 0.0373 mm, all cells
piece, same rng): F1 a grid of horizontal and vertical lines at a 0.3 mm period plus noise scores higher than F2 white noise;
F1 scores higher than F3, a smooth field (Gaussian blur of noise, sigma 1 mm) with dark polygonal holes at random orientations
painted into the texture. Bar: F1 > F2 and F1 > F3, each by a factor of at least 2. A failed bar stops the measure.

Fetch. Before each fetching sheet a row of evidence/fibre-fetch-plan.csv (chunks needed for the windows and the crop, cached,
to fetch, GB, /data free). Fetch only when /data stays above 35 GB free after it; otherwise the sheet reads «not measurable:
fetch refused (free X GB)». The crop's own chunks stay under 1 GB or the crop is refused. After a sheet's values and crop are
written, its fetched chunks are listed in a ledger row and deleted, before the next sheet fetches.

Output evidence/fibre-score.csv: one row per sheet, fibre_score, IQR, windows drawn, accepted by the mask, accepted, band
indices, white noise share, fetch GB, source of the values.

Crops (seed4391, seed6206, seed3412, seed5364): 20 by 20 mm, round(20 / step_i_mm) by round(20 / step_j_mm) cells, one cell per
pixel, into outputs/artifacts/square-0826-seed2604/crop-<seed>.png (PRIVATE), with a scale bar. Centre rule: the centre of the
piece's bounding box if the crop there holds at least 75 per cent piece cells; otherwise the nearest crop centre (Euclidean
distance in cells, crop inside the lattice) where it holds at least 75 per cent; if none does, the centre with the largest
share, stated on the image. Grey window p1 to p99 of the nonzero values of the crop's piece cells; cells not in the piece white;
masked or not measurable cells dark blue (to_grey). The share of piece cells is written on the image and in the CSV.

## Addition 2026-09-29T02:22:50Z (director's order of 02:21:36Z), written before any number of it exists

**Fibre bar and ranking.** A piece counts as papyrus surface when its fibre_score is at least 0.75 x the reference seed3648 C40
S0 score 0.0906 of evidence/fibre-score.csv, that is 0.0680 (bar = 0.75 x 0.0906 = 0.06795, compared to four decimals as
0.0680: passes when fibre_score >= 0.0680). Population: every row of evidence/certified-pieces.csv whose strict piece is 10 cm2
or more, the strict piece being recomputed_piece_cm2 where piece_mask_status reads «recomputed with the 800 and the siblings»,
else largest_certified_piece_cm2; largest first (ties by source, seed, sheet). fibre_score exactly as in the addition of
01:24:25Z (same windows, rng, band, acceptance), no crop. Mask: scratch/piece2/<label>.npz, else scratch/piece/<label>.npz; the
mask's cell count must equal the CSV's piece cells or the row reads «not measurable: mask differs». Sheet file: C40 in
chain-0826/out/<seed>/C40/patch_<k>.bin, C80 in square20-0826-95/out/<seed>/C80/patch_<k>.bin (cert.py's where). Up to 4 sheets
at a time at nice 10; each fetch step holds a lock while it checks /data free and fetches, so the check sees the other
workers' undeleted chunks; refused when /data would fall to 35 GB free or under («not measurable: fetch refused (free X GB)»).
After each sheet's row, its fetched chunks are listed in a ledger row and deleted. Rows already measured (the six of 01:24:25Z)
are reused, not rerun.
Output evidence/fibre-ranking.csv, one row per sheet: source, seed, sheet, strict and open piece cm2, fibre_score, IQR,
windows drawn and accepted, passes_bar, bright cm2 (piece_bright_cm2 of dark-pieces.csv strict piece where it exists, else «not
measured»), certified_square_mm (certified-pieces.csv), pairwise square mm (pairwise-cert-0826 pairwise-squares.csv where a row
exists, else «absent»). Two summary rows: LARGEST_PIECE_PASSING = the passing row with the largest strict piece; LARGEST_SQUARE_
PASSING = the passing row with the largest certified_square_mm (its pairwise square beside it). A sheet not measurable does not
pass.

## Addition 2026-09-29T05:22:42Z (coordinator's order of 05:2xZ, on the director's), written before any number of it exists

**Fibre score of the pooled run's four seeds.** Population: C40 sheet 0 of PHerc0826-seed6365, seed5349, seed1383 and seed4868,
the four seeds of the article's pooled run (area-0826-90 declaration, addition 2026-09-27T20:50:30Z, (1) One collection).
Piece: the strict piece of scratch/piece2/<label>.npz (all four exist, computed by piece2.py; none is recomputed here); its
cm2 is piece2's json piece.cm2. Score, windows, bands, acceptance, rng (default_rng(20260929) restarted per sheet), fetch lock
and 35 GB rule exactly as fibre2.py (addition 02:22:50Z, bar 0.0680 = 0.75 x 0.0906); passes_bar when fibre_score >= 0.0680.
A sheet with no piece or no accepted window reads «not measurable» and does not pass. Tool tools/fibre3.py (new, imports
fibre2.py unchanged, its own scratch/fibre3), output evidence/fibre-pooled-four.csv; each sheet's fetched chunks are listed in
a ledger row and deleted after its row. No crop. Nothing into the article.
