# src: the data the article rests on, and the tools that compute it

The article is delivered as `../article.pdf`. This folder holds what it rests on: the 60 evidence
files every number in it comes from, the tools that wrote those evidence files and drew its
figures, the small inputs they read, the pre-registrations, the logs of the regression test run
the article quotes, and the patch the article proposes upstream. Nothing that typesets the
article is here, because a reader checks a claim against data and a tool, not against a LaTeX
source.

## What can be rebuilt here, and what cannot

On 2026-09-18 the article changed its instrument. Tables III and IV, the twenty four scroll run of
Section V and the exponent table are now produced by calling the shipped C++ function through
`vc_gen_umbilicus`, a driver whose source is in `driver/`, and no longer by the Python
transcription in `inputs/villa_estimator.py`. That is a real cost to this folder and it is stated
as one: **the driver links against `libvc_core.so` of the official VC3D build, which this
repository does not and cannot ship**, so every step that recomputes those tables from the grids
now needs the extracted official AppImage as well as the cut slices, where before it needed the
slices alone. What the folder buys in exchange is that those tables are the compiled function and
not a reading of it. The transcription's versions of the same files are still here, without the
`cpp-` prefix, because the article names four things that stay on the transcription and compares
the two instruments row by row.

There are therefore four categories, not three.

**A caption is generated, and once it went out blank.** The build of 12:18 UTC on 2026-09-18
printed a blank where a scroll name should have been in the caption of Figure 4: the sentence
about the cap of the search was written for the transcription's positions, and with the compiled
function's, where no walk is capped, its list of scrolls was empty. The caption is generated, so
the defect was in `tools/figure_umbilicus_gallery.py`, and it was fixed the same afternoon: a
clause built on a list is now emitted only when the list has members, the formatter stops rather
than write a blank, the cap sentence is chosen from the data, and the file the figure was drawn
from is named by its basename and not by a typed string. It is written down here because a blank
in a generated sentence is the class of defect no check catches by reading the source.

**From this folder alone, with no download:** thirteen of the evidence files regenerate from
scratch and come out byte for byte the same, which is the check that the chain is real and not
just a pile of CSV files: `evidence/second-reference.csv`,
`evidence/synthetic-density.csv`, `evidence/mechanism-curve.csv`,
`evidence/synthetic-sections-refit.csv`, `evidence/inference-refit.json` with
`evidence/bland-altman-refit.csv`, `evidence/far-field-per-scroll.csv` with
`evidence/far-field-permutation.csv`, read from `evidence/far-field-slices.csv` alone,
`evidence/k20-search-noise.csv`, read from the four saved slices in `inputs/real/`,
`evidence/cpp-exponent-aggregate.csv`, read from two of the compiled function's files,
`evidence/prereg-timeline.csv`, read from three documents in
`inputs/` and one in `prereg/`, and `evidence/regression-test-run.csv`, read from the logs of the
test run in `evidence/regression-test/` (two of its columns also ask the fork of
`volume-cartographer` that carries the patch). Figures 1 and 2 also redraw here, and so does the
comparison of the two instruments, `evidence/cpp-vs-transcription.csv`, which reads only files that
are here.

Both modes of `rev1_recompute.py` carry their own known reference. `synthetic` reads
`evidence/synthetic-sections.csv`, the frozen run of September, after writing the refit file, and
prints the sections whose median moved by more than 0.05 grid units: six of the forty-five move,
three of the partial arcs and three where most of the segments are removed, which is the
twenty-seed recomputation against the one of September and not a disagreement. `twentythree` reads
`evidence/twentythree.csv` the same way and prints the scrolls that moved. Both frozen files are
here, so both checks run.

**Only with the cut grid slices, 297 MB, which are not in this repository:** the files that score
estimates already on disk or that read the grids without calling the C++, and two of the four
figures. They are the scoring of the compiled function's estimates, `evidence/cpp-k20.csv` with
`cpp-k20-verdicts.json`, `evidence/cpp-twentyfour.csv`, `evidence/cpp-exponent-fifteen-k20.csv`
with `cpp-exponent-seed-spread.csv` and `evidence/search-cap.csv`, which read the raw estimates
here and the grids for the width and the masks; the transcription's own files
`evidence/fifteen-k20.csv`, `evidence/k20-estimates.csv`, `evidence/ablation-search.csv`,
`evidence/ablation-estimates.csv`, `evidence/density-asymmetry.csv`,
`evidence/density-asymmetry-slices.csv`, `evidence/density-asymmetry-fifteen.csv` with its
`-slices.csv` and `-summary.csv`, `evidence/far-field-slices.csv`,
`evidence/far-field-prediction.csv`, `evidence/twentythree-refit.csv`,
`evidence/positions-24-refit.csv` and `evidence/baselines-k20.csv`; plus Figure 3 and Figure 4.
`evidence/far-field-eigenvalue.csv`
and the two CSVs `figure_exponent.py` writes need only the one slice Figure 3 needs, and the eight
`evidence/exponent-ablation-*.csv` of the transcription's exponent ablation need `inputs/grid15/`
for the six that run the estimator and that one slice for the other two; the ninth file of that
name, `evidence/exponent-ablation-aggregate.csv`, is the transcription's aggregate and is no longer
what the article reads. The slices are cuts of normal grids
the challenge publishes in an open bucket, the cut is deterministic, and the rule and the command
are in "Cutting the grid slices" below. Nothing in the article depends on data that is not public.

**Only with the cut grid slices and the driver, which needs the extracted official build:** the
three raw files of the compiled function, `evidence/cpp-k20-estimates.csv` (14,400 calls),
`evidence/cpp-positions-24.csv` (2,304) and `evidence/cpp-exponent-estimates.csv` (21,600). Section
7 says how the driver is built and what it needs; the five binaries it produces were rebuilt from
this folder on 2026-09-18 and, given the same seed, return the same point to the last digit as the
rows shipped here. Recomputing the three files in full takes about fifty minutes, eight and
seventy-five on six cores, from the mean of 1.25 s per call that `evidence/cpp-k20-cost.csv`
records.

**One evidence file needs one thing that is still outside:** `evidence/bench-rules.csv` is the
record of a run of the umbilicus bench, and `tools/bench_rules.py` reads that run's own output
rather than measuring anything. That run is the one thing outside, named by
`UMBILICUS_BASELINE_RUN` in section 2. The bench itself is no longer outside: the state the
article's numbers were measured against is archived here at `umbilicus-bench/`, and the tool finds
it there with nothing set and re-checks the bench's six committed rows against it, all 72 cells,
before it writes anything. It is simply a second sample, on other heights and another input, that
the article cites and never pools with the tables.

## Layout

```
tools/     the tools that write the evidence files and draw the figures, and palette.py
evidence/  the CSV and JSON files every number in the article expands from, and in
           evidence/regression-test/ the logs of the regression test run the article quotes
inputs/    the configuration, the two reference sets, the transcribed estimator, the grid reader,
           the synthetic sections, the stand-in C++ build with its four saved slices, and the
           three documents prereg_timeline.py reads, and the two declarations the compiled
           runs were made under, and in inputs/second-reference/ the one table that says what
           the second umbilicus of PHerc1218 is
patch/     the commit this article proposes to volume-cartographer, as a git patch
prereg/    the two pre-registrations the article cites, with MANIFEST.md saying what each is,
           when it was written, and its size and sha256
driver/    vc_gen_umbilicus.cpp, the driver the compiled tables were made with, and build.sh
build/     where a run writes, and nothing else: build/driver/ is where driver/build.sh puts the
           five binaries, build/figures-umbilicus/ the SVG and PNG on their way to a PDF, and
           build/figures/ the figures themselves. Nothing in it is kept, because the figures the
           article prints are delivered inside ../article.pdf
umbilicus-bench/   a frozen copy of the umbilicus bench, the state this article's numbers were
           measured against, archived here so that nothing this folder needs can change under
           it. It is the only copy this folder knows about: see the note at the top of
           umbilicus-bench/README.md
requirements.txt   the four packages the tools import, pinned
```

Three runs the article cites are not in this folder and nothing under them is either: the run in
which the exponent ablation was declared and measured, the run of the umbilicus bench that
`evidence/bench-rules.csv` is read from, and the study of 2026-09-18 that measured the second
reference. Each is described where the article uses it, and every file of theirs the article
needs is here: the ablation's tables under `evidence/`, the bench rules in
`evidence/bench-rules.csv`, the second reference table in `inputs/second-reference/`.

**This folder is finished and is not refreshed.** Under `results/` a piece of work is frozen and
self contained, reaching outside itself for nothing that can change, and `umbilicus-bench/` is
archived here for that reason. The bench also goes on living outside this repository, and it is
not to be brought in here: if a new measurement needs the newer bench, it belongs to a new piece
of work with its own folder and its own archived copy, not to this one.

One file under `tools/` is shared with the other papers built from the same working tree, which
are not in this folder, and is edited in one place rather than copied: `tools/palette.py`, which
carries the colour rule the figures follow (a continuous field in viridis, a category in the two
house roles, a mark over a field in white or black) together with an inventory of which figure of
which paper is which. The figure tools import the palette by role and never by value, so that
changing a colour reaches every figure that asked for that role.

Every tool here is a copy of the tool that produced the measurement, and each copy carries a
comment at the top saying so. The copies differ from the working ones in the paths, and in
nothing that computes: the absolute paths of the machine the measurements ran on are resolved
inside this folder instead, from each file's own location, and a tool that reads or writes a
label reads and writes it as the files here carry it. Each copy says at its top what was
changed in it. Five
things that live outside the folder are taken from the environment, and each is named where it is
needed below: `UMBILICUS_SRC`, `UMBILICUS_BENCH`, `UMBILICUS_BASELINE_RUN`, `VILLA_UPSTREAM`,
`VILLA_FORK`. Only two of them have to be set to run anything here. `UMBILICUS_BENCH` is not one of
them any more: the umbilicus bench is archived inside this folder at `umbilicus-bench/`, which is
what the default resolves to, so nothing needs cloning and the variable is only the override the
working tree uses to point at the copy it keeps outside.

Every command below is run from this folder, `results/e89eb7ad-umbilicus-estimator/src`, unless it says otherwise.

## The sources, the coordinates and the slice rule

Before any number here can be checked, four things have to be unambiguous: which files the
measurements read, how a coordinate in one of those files becomes a distance in millimetres, and
which slices were measured. All four are in the configuration rather than in prose, and this
section says where each one is, so that a reader can go to the file instead of taking the answer
from a paragraph.

**The normal grids.** They are the ones the challenge publishes in its open bucket,
`https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/`. The grid URL of a scroll is
the `grids` field of `inputs/fifteen-config.json` for the fifteen scrolls that have a reference,
and of `inputs/scrolls-24.json` for the twenty-four of the competition set; that URL names the
surface prediction the grid was built from, so the prediction is identified by it and not by a
separate note. One slice is one file, `xy/<z>.grid`, with `z` written in six digits. Section 3
cuts them, and nothing here reads a grid from anywhere else.

**The manual umbilici.** Four of the fifteen are published by the challenge and are copied into
`inputs/reference/`, whose `README.md` names the bucket objects they come from and the scan each
was annotated on. The other eleven are copied into `inputs/external-references/`, ten of them hand
annotations by a third party and one more published by the challenge; `PROVENANCE.md` there gives
for every file its origin, how it was annotated, how many points it carries and its licence. The
file `dopico-PHerc1218-umbilicus.json` there is not a sixteenth reference and is not a
hand annotation: it is derived from published sheet instance labels as a per slice centroid of the
papyrus mask, it is the second umbilicus PHerc1218 carries, and `evidence/second-reference.csv`
says what follows from that. The fifteen hand umbilici fall on fifteen different scrolls, five
from the challenge and ten from the third party, so **no scroll here carries two independent hand
annotations** and the error of a hand cannot be measured on this data. Which
file is the reference of which scroll, together with the `source`, `author`, `method` and
`licence` of that reference, is a field of `inputs/fifteen-config.json`, so no tool here picks a
reference by guessing at a name. A control point flagged `rejected` is skipped when the file is
read, which `rev1_lib.reference` does once for every tool.

**The coordinates.** Three systems are in play, and two numbers per scroll convert between them.

| system | what is written in it | to leave it |
|---|---|---|
| grid units | the slice files, the estimator, the `bounds` of the slice header, the `x` and `y` columns of the raw estimate files | multiply by `grid_scale` to get level 0 voxels |
| level 0 voxels of the scan | the control points of every reference file, the polylines the error metric is computed on, the `z` of a slice once multiplied back | multiply by `voxel_um / 1000` to get millimetres |
| millimetres | every distance the article prints | |

`grid_scale` and `voxel_um` are per scroll fields of `inputs/fifteen-config.json`. One grid unit is
therefore `grid_scale * voxel_um / 1000` millimetres: 0.009362 mm on PHerc0826, whose grid is at
scale 1 of a 9.362 um scan, and 0.009596 mm on PHerc0332, whose grid is at scale 4 of a 2.399 um
scan. `mask_scale` is a third number and is not interchangeable with `grid_scale`: it is the scale
of the surface prediction store that the centroid baseline is computed on, and on PHercParis4 it
is 4 where `grid_scale` is 1.

The conversion is written once, in `tools/rev1_lib.py`, so that no two tables here can convert
differently: `heights` divides a reference by `grid_scale` to get slice indices, and the scoring
half of `tools/fifteen_k20.py` multiplies an estimate by it to get the level 0 polyline the metric
reads. Every tool that prints millimetres takes `voxel_um / 1000` from the same config. The third
party references were clicked on level 3 images and are stored already converted to level 0: the
`meta.json` beside each one records the level, the scale of 8 and the slices that were annotated,
so that conversion can be checked rather than believed.

**Which slices.** Two rules, both fixed in code and neither chosen by looking at a picture.

* The fifteen scrolls with a reference: `heights` in `tools/rev1_lib.py`. Twenty-four heights
  equally spaced between the lowest and the highest control point of that scroll's own reference,
  divided by `grid_scale` and rounded.
* The twenty-four of the competition set: the fractions `numpy.linspace(0.08, 0.92, 24)` of the
  number of z planes of that scroll's surface prediction, read from `shape[0]` of the level 0
  `.zarray` and truncated to an integer.

Two slices of those lists can drop out, and both are drops by rule and not by choice: a height
with no published grid is cut as an empty file and skipped, and a slice carrying fewer than 100
segments is dropped by `grid15_slice` and `grid23_slices` in `tools/rev1_lib.py`, which is how a
grid that exists but is too thin to hold a section leaves the tables. The z values that survived
are in the evidence and can be counted there: `evidence/k20-estimates.csv` for the fifteen and
`evidence/positions-24-refit.csv` for the twenty-four.

The gallery figure shows one slice per scroll, and its rule was fixed before it was drawn: of the
twenty-four slices sampled on a scroll, in order of z, the panel shows the twelfth, the lower of
the two that straddle the middle of the sampled band. It is `SLICE_INDEX` in
`tools/figure_umbilicus_gallery.py` and it is stated in the caption the tool writes beside the
figure, which is the caption the article prints.

**The commands.** Sections 1 to 5 are the whole of it, one command per step with what it reads,
what it writes and how long it takes: section 3 cuts the 937 slices the measurements run on, 294
MiB and about half an hour of downloading, section 2 regenerates the evidence files, section 1
redraws the figures, and sections 4 and 5 are the patch and the driver. The section that follows
this one is the cheapest of them and needs no download at all.

## A check you can run in a second

This is the cheapest end of the chain and it needs nothing but what is here. It reads two of the
evidence files and the references, and rewrites two other evidence files, which come out byte for
byte as they are in the repository:

```
python3 tools/rev1_inference.py
```

Expected output:

```
{
 "friedman": {
  "chi2": 23.08,
  "p": 3.886178774890479e-05,
  "mean_ranks": {
   "as-is": 3.333,
   "no-division": 1.267,
   "centroid": 2.333,
   "fake_axis": 3.067
  }
 },
 "nemenyi": {
  "critical_difference": 1.211,
  "gap_fixed_vs_centroid": 1.067,
  "separates": false
 },
 "tost": {
  "bound_mm": 0.3,
  "p": 0.9951,
  "equivalent": false,
  "n": 15
 },
 "non_discriminating": [
  "PHerc0125"
 ],
 "worst": {
  "primary": "PHerc0826",
  "confirmation": "PHerc1218"
 }
}
written .../evidence/bland-altman-refit.csv (30 rows)
```

## Environment

Measured on the machine that built the article: Linux, sixteen cores, no GPU.

| | version |
|---|---|
| Python | 3.14.4 |
| numpy | 2.5.2 |
| scipy | 1.18.1 |
| matplotlib | 3.11.1 |
| rsvg-convert (librsvg) | 2.61.3 |
| git | any recent version |
| g++ | 15.2.0, only to build the driver of section 5 |
| OpenCV headers | 4.10, only for the driver; the library itself comes with the AppImage |
| Boost headers and program_options | 1.83, only for the driver |
| VC3D AppImage, extracted | the official build, for `libvc_core.so` and `libutils.so`; only for the driver |

Those are all the packages the tools import, and `requirements.txt` pins the three of them:

```
python3.14 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

On Debian and Ubuntu that first command stops with `ensurepip is not available` unless the
`python3.14-venv` package is installed, which is a system package and not a Python one; any tool
that builds the environment from `requirements.txt` does instead, and the versions that come out
are the ones in the table.

`python3` in every command below is then `.venv/bin/python`. The list in `requirements.txt` was
read off the imports of `tools/`, `inputs/` and `evidence/far-field-seedpoint-probe/`, not off the
machine, so it carries nothing the folder does not use; everything else those files import is in
the standard library, apart from `bench`, `data` and `estimators`, which are modules of the
umbilicus bench archived at `umbilicus-bench/` and are imported from there instead of installed.

The scoring phases of the compiled runs, section 5, read the archived bench at `umbilicus-bench/`
as `fifteen_k20.py` does. Its `data.py` needs `numcodecs` to decode the published chunks, and now
that the bench lives in this folder that is this folder's requirement too, so `numcodecs` is in
`requirements.txt`; before the bench was archived here it came with the checkout instead.

`rsvg-convert` is needed only to redraw the figures, and `git` only for the two steps that read a
clone of `volume-cartographer`.

## 1. Redraw the figures

```
export SOURCE_DATE_EPOCH=1789776000
python3 tools/figure_umbilicus_redraw.py f1        # Figure 1, the mechanism
python3 tools/figure_exponent.py fA                # Figure 2, the score against the exponent
python3 tools/figure_umbilicus_redraw.py f2        # Figure 3, the score field
python3 tools/figure_umbilicus_gallery.py       # Figure 4, the gallery of 24 scrolls
```

The epoch is the date the article prints on its title page and carries in its `/CreationDate`,
2026-09-19T00:00:00Z, and one value governs every figure. `tools/figure_umbilicus_redraw.py`
declares it as `DECLARED_EPOCH` and exports it when the caller has not, so the command above is
the same with or without the first line. Both rendering paths honour it: `figure_exponent.py` and
the gallery go through matplotlib's PDF backend, and the two redraw commands write SVG and convert
it with `rsvg-convert`, whose cairo reads the same variable. Without it every figure carries the
wall clock and no two renders agree; with it all four come back byte for byte, which is what makes
a redraw checkable against the figures printed in `../article.pdf`.

Figure 1 takes a second and needs nothing but `evidence/mechanism-curve.csv`. Figure 2 is the same
kind of thing for the exponent: a second, and nothing but
`evidence/exponent-ablation-mechanism-curve.csv`.

Figure 3 needs one cut slice that is not here, `inputs/cache/pherc0826/ngrid/xy/008000.grid`,
188 KB, cut as described below. Figure 4 needs the whole of `inputs/grid23/`, and draws the
estimates of `evidence/cpp-positions-24.csv`, the compiled function's, when that file is present,
which it is here; `positions-24-refit.csv`, the transcription's, is its fallback. All four figures
are in the brand palette of the series with every label black, which `tools/palette.py` carries as
roles and the redraw tool applies to the frozen drawing script by named substitution, refusing to
draw if a line it expects has moved. Run without them,
Figure 3 stops on the missing file and Figure 4 refuses, naming how many of the twenty-four scrolls
have no slice on disk; neither writes anything. `--allow-missing` draws the gallery anyway and
writes it as `umbilicus-gallery-24-partial`, beside the real one and never over it.

Everything a figure run writes goes under `build/`, which the repository does not keep: the redraw
tools write SVG and PNG into `build/figures-umbilicus/` and the PDF into `build/figures/`, and
`figure_exponent.py` and the gallery write a PDF and a PNG straight into `build/figures/`. The
gallery writes its caption there too, the sentence the article prints under Figure 4, and checks
the panels it drew against `evidence/cpp-twentyfour.csv` before it writes anything: a positions
file and a summary that disagree are two runs under one name, and the tool stops rather than draw
them. `figure_exponent.py` with no argument also draws a second figure, the score field at each
exponent, which the article does not carry.

## 2. Regenerate the evidence files

`python3` below is the interpreter of the environment above. Each tool writes into `evidence/`,
overwriting the file that is there.

| command | reads | writes | time | needs data not in the repository |
|---|---|---|---|---|
| `tools/synthetic_density.py` | `inputs/synthetic_sections.py`, `inputs/core.py` | `synthetic-density.csv`, `mechanism-curve.csv` | about 50 minutes on 16 cores; `mechanism-curve.csv` is written in the first seconds | no |
| `tools/rev1_recompute.py synthetic --workers N` | the same | `synthetic-sections-refit.csv` | about 2 minutes | no |
| `tools/rev1_inference.py` | `fifteen-k20.csv`, `k20-estimates.csv`, `inputs/reference/`, `inputs/external-references/` | `inference-refit.json`, `bland-altman-refit.csv` | a second | no |
| `tools/upstream_check.py --clone DIR` | a clone of `ScrollPrize/villa`, fetched | `upstream-check.csv` | a second | the clone |
| `tools/fifteen_k20.py --workers N` | `inputs/grid15/`, the references, 20 seeds | `fifteen-k20.csv`, `fifteen-k20-verdicts.json`, `k20-estimates.csv`: the transcription's version of Tables III and IV, which the article compares against and no longer prints | hours | `inputs/grid15/` and `umbilicus-bench/`, both in this folder |
| `tools/fifteen_k20.py --reference-check` | `inputs/real/*.bin` | `k20-search-noise.csv` | minutes | no |
| `tools/ablation_search.py --workers N` | `inputs/grid15/`, the references | `ablation-search.csv`, `ablation-estimates.csv` | hours | `inputs/grid15/` and `umbilicus-bench/` |
| `tools/density_asymmetry.py` | `inputs/grid15/`, the references, `fifteen-k20.csv` | `density-asymmetry-fifteen.csv`, `density-asymmetry-fifteen-slices.csv`, `density-asymmetry-fifteen-summary.csv` | minutes | `inputs/grid15/` |
| `tools/far_field_eigenvalue.py` | `inputs/cache/pherc0826/ngrid/xy/008000.grid`, the PHerc0826 reference, `inputs/synthetic_sections.py` | `far-field-eigenvalue.csv` | a second | the one slice of Figure 3 |
| `tools/far_field_eigenvalue.py --slices` | `inputs/grid15/`, the references, `cpp-k20-estimates.csv` for the outcomes of the shipped walk (`k20-estimates.csv` when the compiled file is absent) | `far-field-slices.csv`, `far-field-prediction.csv` | half a minute | `inputs/grid15/` |
| `tools/far_field_scrolls.py` | `far-field-slices.csv` | `far-field-per-scroll.csv`, `far-field-permutation.csv`: Table I and its exact p, by convolution of the per scroll counts | 15 seconds | no |
| `tools/far_field_scrolls.py --input evidence/far-field-slices-transcription.csv` | the transcription's slice file | nothing; it prints the exact p on that file, 1.37e-30, which is the known reference of the convolution | 15 seconds | no |
| `tools/figure_exponent.py --numbers` | `inputs/synthetic_sections.py`, the one slice of Figure 3 | `exponent-ablation-mechanism-curve.csv`, `exponent-ablation-score-field.csv` | a minute | that one slice |
| `tools/exponent_ablation.py --scrolls --workers N` then `--score` | `inputs/grid15/`, the references | `exponent-ablation-k20-estimates.csv`, then `exponent-ablation-fifteen-k20.csv` and `exponent-ablation-seed-spread.csv`: the transcription's version of the exponent table, no longer what the article prints | 19 minutes with 15 to 20 workers | `inputs/grid15/` |
| `tools/exponent_ablation.py --synthetic --workers N` | `inputs/synthetic_sections.py` | `exponent-ablation-synthetic-density.csv` | 36 minutes with 15 to 20 workers | no |
| `tools/exponent_ablation.py --cancellation`, `--rate` | the one slice of Figure 3, `inputs/synthetic_sections.py` | `exponent-ablation-cancellation.csv`, `exponent-ablation-cancellation-rate.csv` | a minute | that one slice |
| `tools/exponent_intervals.py` | `cpp-exponent-fifteen-k20.csv` and `cpp-k20.csv` when present, else the transcription's two | `cpp-exponent-aggregate.csv`, else `exponent-ablation-aggregate.csv` | a second | no |
| `tools/prereg_timeline.py` | `inputs/result-d-one-division.md`, `prereg/preregistration-fifteen-references.md`, `inputs/preregistration-twenty-four-scrolls.md`, `inputs/note-twenty-seeds.md`, `fifteen-k20.csv`, `tools/rev1_recompute.py` | `prereg-timeline.csv` | a second | no |
| `VILLA_FORK=DIR tools/regression_test_result.py` | `evidence/regression-test/` | `regression-test-run.csv` | a second | the fork, for the commit at its tip and the check that its tree is the archived one |
| `tools/rev1_recompute.py twentythree --workers N` | `inputs/grid23/` | `twentythree-refit.csv`, `positions-24-refit.csv`: the transcription's version of the run of Section V, no longer what the article prints | about 20 minutes on one core, 4 with six workers | `inputs/grid23/` |
| `tools/cpp_k20.py estimates --workers N` | `inputs/grid15/`, the two binaries of `driver/build.sh` | `cpp-k20-estimates.csv`, 14,400 calls, resumable | about 50 minutes on six cores | `inputs/grid15/` and the driver, section 5 |
| `tools/cpp_k20.py scores` | `cpp-k20-estimates.csv`, `inputs/grid15/` for the grid width, the bench for the centroid | `cpp-k20.csv`, `cpp-k20-verdicts.json`: Tables III and IV | a minute | `inputs/grid15/` and the bench |
| `tools/cpp_k20.py compare` | `cpp-k20.csv`, `fifteen-k20.csv` and the two verdict files | `cpp-vs-transcription.csv` | a second | no |
| `tools/cpp_gen24.py gen24 --workers N` | `inputs/grid23/`, the two binaries | `cpp-positions-24.csv`, 2,304 calls, resumable | about 8 minutes on six cores | `inputs/grid23/` and the driver |
| `tools/cpp_gen24_score.py` | `cpp-positions-24.csv`, `twentythree-refit.csv` for the two probe columns it carries over | `cpp-twentyfour.csv`: the run of Section V | a second | no |
| `tools/cpp_gen24.py exponent --workers N` | `inputs/grid15/`, the three exponent binaries | `cpp-exponent-estimates.csv`, 21,600 calls, resumable | about 75 minutes on six cores | `inputs/grid15/` and the driver |
| `tools/cpp_exponent_score.py` | `cpp-exponent-estimates.csv`, `cpp-k20-estimates.csv` for p = 1, `inputs/grid15/`, the bench | `cpp-exponent-fifteen-k20.csv`, `cpp-exponent-seed-spread.csv`: the exponent table | a minute | `inputs/grid15/` and the bench |
| `tools/search_cap.py` | `k20-estimates.csv`, `positions-24-refit.csv`, `cpp-runs.csv`, `inputs/real/`, `inputs/grid15/` | `search-cap.csv` | a minute | `inputs/grid15/` and the bench |
| `tools/baselines_k20.py` | `inputs/grid15/`, the references, `fifteen-k20.csv` | `baselines-k20.csv` | minutes | `inputs/grid15/` and `umbilicus-bench/`, which is where the two rules live |
| `tools/second_reference.py` | `inputs/second-reference/hand-vs-mask-centroid.csv`, `inputs/fifteen-config.json`, `evidence/reference-uncertainty.csv` | `second-reference.csv`: what the second umbilicus of PHerc1218 is, and the distance between a hand umbilicus and a per slice centroid of the papyrus mask on all fifteen scrolls | a second | no |
| `UMBILICUS_BASELINE_RUN=DIR tools/bench_rules.py` | that run's `rows.csv`, and `results/bench.json` of `umbilicus-bench/` | `bench-rules.csv` | a second | the run of 2026-09-18 that scored the rules inside the bench, and the archived bench itself |

Four of these tools write files the repository keeps, from grids the repository does not carry:
`density_asymmetry.py`, `far_field_eigenvalue.py --slices`, `rev1_recompute.py twentythree` and,
among the figures, `figure_umbilicus_gallery.py`. Each counts the scrolls that yielded no slice at
all and refuses before its first write if there are any, so a partial cut cannot quietly replace a
file here with a run over the scrolls that happen to be on disk. `rev1_recompute.py twentythree`
counts two kinds of absence, a scroll with no directory and a directory too thin to measure, and
takes its list from `inputs/scrolls-24.json` rather than from what is on disk. A height with no published grid is cut as an
empty file on purpose and is not counted, so a complete cut never trips the check. `--allow-missing`
writes to a `-partial` name instead. The tools that resume, `fifteen_k20.py`,
`ablation_search.py` and `exponent_ablation.py`, need no such guard: with no slices they recompute
nothing and rescore the estimates that are here.

Refusing is not the only answer to a missing input, and the choice between the two is worth stating
for anyone who writes another tool for this folder. **Where the row a tool writes is an observation
about a declared thing, the absence is recorded and the row is kept**, which is what
`eligible_triage.py` does in the working tree: one row per declared scroll with a column saying how
many grids it actually saw, so the gap is visible in the file rather than in an exit code, and the
run stays usable. **Where every column of the row is a statistic over the data that is missing, the
tool refuses**, because a row with those columns blank is either skipped by the reader, which is the
same silent loss in another costume, or coerced to a number, which is worse. Every tool named above
writes statistics, which is why all of them refuse.

`exponent_ablation.py --check` writes nothing and reruns the four reproductions the ablation was
declared on: at exponent 1 the family is the patch, and the check is that it returns the published
estimates unchanged. That is also why `tools/rev1_lib.py` can carry the exponent as an argument
without any number moving: at the default it takes the original expression and not a power of it.

`fifteen_k20.py` and `ablation_search.py` take the centroid baseline from `umbilicus-bench/`,
which computes it on 24 level 3 slices of each scroll's surface prediction (the `mask_pred` of
`inputs/fifteen-config.json`). The bench downloads those slices from the same bucket and caches
them under `umbilicus-bench/cache/` the first time it is run, about 384 MB for the fifteen
scrolls. That folder is inside this one now, and the bench's own `.gitignore` keeps it out of the
repository with a rule anchored to the bench's root, so a run of those two tools leaves 384 MB on
disk and nothing untracked. They need no other data beyond `inputs/grid15/`.

`upstream_check.py` answers a question about a moving target, so it answers about the clone it is
given and about when that clone was last fetched: the count of commits and the tip it names change
as upstream moves. The file here was written against a clone fetched on 2026-09-17.

`fifteen_k20.py`, `ablation_search.py` and the two drivers' estimate phases resume. Each writes
every estimate to its raw file as it goes and reads that file back at the next start, so run on this
folder as it ships they find every estimate already made and compute none: to recompute them, move
the raw file aside first, and to check the summaries against the ones here without paying the hours,
leave it where it is and run the scoring phase alone.

Thirteen evidence files are not regenerated by any tool in this folder. `cpp-k20-cost.csv` is one
row per quantity read off the log of the fifty minute run and is not recomputed. Eight are the frozen run of
September: `fifteen.csv`, `synthetic-sections.csv`, `twentythree.csv`, `cpp-runs.csv`,
`search-noise.csv`, `field-stops.csv`, `function-coverage.csv` and `reference-uncertainty.csv`.
`fifteen.csv` is reproduced by
`fifteen_k20.py` at seed index zero, which is how the tool checks itself against a known result;
`synthetic-sections.csv` and `twentythree.csv` are the two batteries `rev1_recompute.py` recomputes,
kept as the known references those two steps are read against, and the other four come from the
stand-in C++ build in
`inputs/real/` and from a gcov run, and
`inputs/real/build.sh` and `inputs/real/evidence.sh` rebuild them from the four saved slices, given
OpenCV headers and a clone of `volume-cartographer`. The other two are `density-asymmetry.csv` and
`density-asymmetry-slices.csv`, written on 16 September by `density_asymmetry.py` as it then was,
on the five primary scrolls; the tool here is its extension to the fifteen and leaves those two
as they were written. The last two are `consistency.csv` and `villa-lines.csv`, the recount of
every number the article states in a caption or a sentence and the line by line pinning of the
cited lines of `normalgridtools.cpp` to the commit the stand-in build compiled from. They are
written by `rev1_consistency.py`, which is not in this folder because what it exists to serve is
the typesetting: it turns those rows into the macros the captions expand, and it reads two
evidence files of the longer paper that are not here. The two files it wrote are kept, because
every number of the article expands from a file that a reader can read.

**The regression test record.** `evidence/regression-test/` is what the run of 2026-09-17 left,
described file by file in `evidence/README.md`: the test target of the patch commit was built
from the commit's own sources with the system g++ and a stock OpenCV 4.10, no CMake and no Qt,
and run twice in fresh processes; all fifteen cases of `test_normalgridtools.cpp` pass, the four
new ones with the margins `distances.log` prints. `regression_test_result.py` reads those files
and retypes nothing. Running the test again is not a matter of this folder alone:
`evidence/regression-test/build.sh` expects the sources of the commit under
`src/volume-cartographer` next to it (`git archive` of the commit named in `sources-commit.txt`,
or a clone with the patch applied), nlohmann/json under `third_party/`, and an OpenCV 4 with
its headers in the tree named by `OCV`; it compiles the test, the two files under test,
`GridStore.cpp`, `MemMap.cpp` and `Json.cpp`, and links against OpenCV core and imgproc.

## 3. Cutting the grid slices

The slices are cuts of the normal grids the challenge publishes in the open bucket
`https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/`. The grid URL of every scroll is
the `grids` field of `inputs/fifteen-config.json`, and one slice is one file, `xy/<z>.grid`, with
`z` written with six digits.

**`inputs/grid15/`, 132 MB, the fifteen scrolls that have a reference.** The rule is
`heights()` in `tools/rev1_lib.py`: 24 heights equally spaced between the lowest and the highest
control point of that scroll's reference, divided by the scroll's `grid_scale` and rounded. This
writes them:

```
python3 - <<'PY'
import json, os, sys, urllib.error, urllib.request
sys.path.insert(0, "tools")
import rev1_lib as L
for scroll in L.CFG:
    base, d = L.CFG[scroll]["grids"], os.path.join("inputs", "grid15", scroll)
    os.makedirs(d, exist_ok=True)
    for z in L.heights(scroll):
        p = os.path.join(d, f"{z:06d}.grid")
        if os.path.exists(p):
            continue
        try:
            body = urllib.request.urlopen(base + f"xy/{z:06d}.grid", timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise           # anything but a missing object is transient: stop, do not skip
            body = b""          # a height with no published grid is left empty on purpose
        open(p, "wb").write(body)
    print(scroll, "done", flush=True)
PY
```

About twenty minutes on a normal connection.

**`inputs/grid23/`, 165 MB, the 24 scrolls of the competition set.** The rule is 24 heights at the
fractions `numpy.linspace(0.08, 0.92, 24)` of the number of z planes of that scroll's surface
prediction, which is `shape[0]` of the level 0 `.zarray` of the prediction, truncated to an
integer. The list of the 24 scrolls is `inputs/scrolls-24.json`, which carries the grid URL and
the surface prediction of each: `inputs/fifteen-config.json` names only fifteen, and ten of the
twenty-four are not among them (`PHerc0175A`, `PHerc0175B`, `PHerc0306B`, `PHerc0343`,
`PHerc0483A`, `PHerc0483B`, `PHerc0490A`, `PHerc0490B`, `PHerc0846A`, `PHerc0846B`). This writes
them:

```
python3 - <<'PY'
import json, os, urllib.error, urllib.request
import numpy as np
B = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/"
S = json.load(open("inputs/scrolls-24.json"))
for scroll in S:
    base, d = S[scroll]["grids"], os.path.join("inputs", "grid23", scroll)
    os.makedirs(d, exist_ok=True)
    Z = json.loads(urllib.request.urlopen(
        B + S[scroll]["surfaces"][0] + "0/.zarray").read())["shape"][0]
    for z in [int(f * Z) for f in np.linspace(0.08, 0.92, 24)]:
        p = os.path.join(d, f"{z:06d}.grid")
        if os.path.exists(p):
            continue
        try:
            body = urllib.request.urlopen(base + f"xy/{z:06d}.grid", timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            body = b""
        open(p, "wb").write(body)
    print(scroll, "done", flush=True)
PY
```

About eight minutes. The two cuts together are 936 files and 294 MiB, and the names they write are
the z values the evidence files record: `k20-estimates.csv` for grid15, `positions-24-refit.csv`
for grid23.

**Both snippets stop on anything but a missing object, and the reason is worth a paragraph.** An
empty file means a height the bucket does not publish, and every tool here skips it. A transient
network failure that writes an empty file is therefore indistinguishable from that, and it removes
a slice from the run without anybody being told. It happened once while these commands were being
checked: one object of PHerc1218 timed out, the cut left `017991.grid` at zero bytes, and
`rev1_recompute.py twentythree` came back with 575 estimates instead of 576 and reported the
scroll as having 23 slices rather than refusing. The object was there all along, 173,094 bytes on
the next try. After a cut, check before measuring:

```
find inputs/grid15 inputs/grid23 -name '*.grid' -size 0
```

On a complete cut of 2026-09-18 that printed nothing at all, and with it the twenty-four scroll
run reproduced `evidence/positions-24-refit.csv` and `evidence/twentythree-refit.csv` byte for
byte.

**The one slice Figure 3 needs** is `PHerc0826` at z 8000, that is `xy/008000.grid` under the
`grids` URL of `PHerc0826`, saved as `inputs/cache/pherc0826/ngrid/xy/008000.grid`.

## 4. The patch

The article is about one line of `volume-cartographer`. The change is in
`patch/0001-normalgridtools-weighted-sum.patch`, commit `7a4129a1d` of the branch
`normalgrid-umbilicus-score-not-normalised` of the fork `evilaliv3/villa`. It applies to
`ScrollPrize/villa` at commit `b1ef996e3`. It touches three files:

```
volume-cartographer/core/include/vc/core/util/normalgridtools.hpp
volume-cartographer/core/src/normalgridtools.cpp
volume-cartographer/core/test/test_normalgridtools.cpp
```

**The commit hash is not what the measurements were made on; the change is.** That commit has been
amended twice to reword its message, never touching a file, and then rebased onto a newer upstream,
so it has been `dec288ff4`, `e6999be01`, `c6bcb2a58` and is now `7a4129a1d`. The first three carry
the tree `b175fb12`, the rebased one carries
`96a769b3a26dd0bc9c18cee4000ae1f6d980d253`. The two trees differ because the base moved under the
change, and the change itself moved by three comment lines and nothing else: between `c6bcb2a58`
and `7a4129a1d` the header and the test file are identical, and in
`core/src/normalgridtools.cpp` one comment line above the return became four, saying that the
interior maximum is a property of the score and not a guarantee about the search below it. No code
line differs, which was checked line by line and not assumed. The article names both the commit and
the tree for that reason. A
reader who wants to check that the file applied is the file measured should apply the patch onto
`b1ef996e3` and compare the tree it produces, `git rev-parse HEAD^{tree}`, against
`96a769b3a26dd0bc9c18cee4000ae1f6d980d253`, which is what this folder records; that was done on
2026-09-18 and it matches.

The regression test record was redone against the rebased commit on the same day, and
`evidence/regression-test/sources-commit.txt` now holds `7a4129a1d`, the hash the test sources were
archived from. Every distance, margin, tolerance and the pass count are those of the run of
2026-09-17, `distances.log` byte for byte; what moved is the commit identity and one wall clock.
Because the sources were archived from the patch commit itself this time, `sources_commit` and
`patch_commit` in `evidence/regression-test-run.csv` are the same hash and the `same_tree` column
is trivially yes, where before it compared an older archive against the tip of the branch.

The change itself is one line of the first two; the rest of the patch is the regression test that
holds it, three cases on sections built in the file.

```
git clone https://github.com/ScrollPrize/villa
cd villa && git checkout b1ef996e3
git am < /path/to/src/patch/0001-normalgridtools-weighted-sum.patch
```

Then build `volume-cartographer` as its own README says and run the test binary for
`core/test/test_normalgridtools.cpp`, or build that one target as
`evidence/regression-test/build.sh` did.

The branch of the fork also adds `vc_gen_umbilicus` to `apps/CMakeLists.txt`, four lines that
link it against `vc_core`, Boost program_options and OpenCV core; that is how it is built inside the
project, and `driver/build.sh` of section 5 is how it is built here without the project.

## 5. The compiled function and its driver

The tables of Sections III, V and VII are the shipped `align_and_extract_umbilicus`, called through
`vc_gen_umbilicus`, a small command line tool the patch adds beside the one line. Its source is
`driver/vc_gen_umbilicus.cpp`, and it is carried here rather than pointed at, for the same reason the
regression test's sources are: it lives on a branch of a fork, and a reproduction command that
depends on a branch which may be rebased is not a reproduction command. What the folder cannot carry
is what the driver links against. `driver/build.sh` compiles the tool and the patched
`normalgridtools.cpp` from source and takes everything else, `GridStore`, `NormalGridVolume` and the
JSON reader, from `libvc_core.so` of the official VC3D build, the project's own binary release,
extracted from its AppImage. So the recipe is closed but not self contained, and it needs four
things named in the environment:

```
export VILLA_FORK=/path/to/villa      # a checkout with the patch: the fork's branch, or
                                       # ScrollPrize/villa at b1ef996e3 with patch/ applied by git am
export VC3D_ROOT=/path/to/squashfs-root   # the extracted AppImage of the official VC3D build
export OCV_ROOT=/path/to/opencv-tree      # usr/include/opencv4 and usr/lib/x86_64-linux-gnu
export BOOST_ROOT=/path/to/boost-tree     # usr/include/boost and usr/lib/x86_64-linux-gnu
cd driver
./build.sh                    # the patch as it stands: the weighted sum
VARIANT=as-is ./build.sh      # the division restored: the published objective
VARIANT=p0.5 ./build.sh       # the weight raised to that exponent, likewise p1.5 and p2.0
```

Each build takes a few seconds and writes `build/driver/vc_gen_umbilicus-<variant>`. The `as-is`
and exponent variants are made from the patched source by substitutions anchored on exact lines,
and the build fails if an anchor does not match exactly once, because a binary built from an anchor
that slipped is a binary nobody can characterise. The exponent variants are this paper's objective
and not upstream's, as the article says. The AppImage and the OpenCV and Boost trees need no root:
the AppImage extracts with `--appimage-extract`, and the two trees are the distribution's
development packages unpacked anywhere.

All five were rebuilt from this folder on 2026-09-18 and checked against the estimates shipped
here: given the seed a row records, the folder's binary returns the same point to the last
digit, for the weighted sum, the weighted mean and the exponent variants alike, which is the
repeatability the seed argument was added for.

The rules the three runs were made under were written before each run, and each states in its own
first lines the day and the hour it was written. Both are post hoc with respect to every
pre-registration of the article and say so in their first lines. The sizes and digests below are of
the files as they stand here.

| file | what it is | bytes | sha256 |
|---|---|---:|---|
| `inputs/declaration-cpp-comparison.md` | the rule of the driver run, written 2026-09-18 09:23 UTC: the seeds, the wall clock guard, the order of the scrolls, the criterion of agreement between the two instruments and what stops the run | 8749 | `e153ca383a7eda68714a4293e24c0cf04d38872ee5a81f07cca4b6deaf21bba6` |
| `inputs/declaration-cpp-two-runs.md` | the rule of the two runs that remain, written 2026-09-18 10:52 UTC: the same for the twenty four scroll run and the exponent ablation, and the list of what stays on the transcription; its section 8, added at 13:03 UTC, is the rule under which the far field criterion of Table I was read against the shipped walk's outcomes, with the transcription's kept beside as `far-field-*-transcription.csv` | 7503 | `cd4103563aa812dcf5e5b593bdb49caf52d922010764916773cdc7b13c02547c` |

**What `cpp_k20.py compare` prints, and why it does not contradict the article.** Run here it ends
with `OUTCOME C of the declaration: something moves a verdict, everything stops`, naming
`PHerc0268 as-is` and `PHerc1218 no-division`. The article reports both. The first is one of the two
rows whose mark for a margin including zero differs between the instruments; the declaration
excused that case for rows not counted as won, and the tool was left stricter than its own rule
rather than edited once it was known which rows it caught, which the article says in Section III.
The second is the count of confirmation scrolls whose weighted sum loses to the centroid, one by the
transcription and none by the compiled function, which the article names as a change of measuring
instrument and not a new result. Neither is one of the four pre-registered verdicts, and
`cpp-k20-verdicts.json` carries the same four as `fifteen-k20-verdicts.json`. The tool's last word is
the declaration's rule applied to the letter, and the article's is the reading of it; both are kept.

**Table I is the shipped walk's too.** Since the declaration's section 8 of 13:03 UTC the far field
criterion is validated against the outcomes of the compiled function: the eigenvalues come from the
grids and are the same under either instrument, the inside flags come from `cpp-k20-estimates.csv`,
and the counts moved from no miss at all to one, PHerc0257 z 8479, which the article prints as a
difference and does not reconcile. The transcription's four far field files are kept beside as
`far-field-*-transcription.csv`, and the exact p of the permutation test is now a tail computed by
convolution, checked against the transcription's file where the earlier product was right.

**Four things stay on the transcription**, each for a reason the article gives and this folder does
not improve on: the search ablation of Section VII, because the shipped function has no replaceable
search; the audit of the cap and of the sampling, because an audit of the transcription can only be
measured on the transcription; the density bias on synthetic sections, because those sections are
polylines of real coordinates and the shipped `GridStore` holds integer points; and the four scroll
bench run, which is a separate post hoc study on its own slices. The tools and files for those are
the ones without the `cpp-` prefix.

## The pre-registrations

The article cites two pre-registrations, and both are in `prereg/`. Each states in its own first
lines the day and the hour it was written, which is before the measurement it governs, and
`prereg/MANIFEST.md` says what each is and carries its size and sha256, so a reader can check the
copy they are holding against the one the article was built from.

Three more documents are read by `tools/prereg_timeline.py`, which takes from them only what the
article states: the scroll table of the first, and the date each of the other two gives in its
first lines. They are kept in `inputs/`, and the sizes and digests below are of the files as they
stand here:

| file | what it is | bytes | sha256 |
|---|---|---:|---|
| `inputs/result-d-one-division.md` | the report of 2026-09-15 on the one division, whose scroll table is the record of which four scrolls had been measured before the pre-registration of the fifteen was written | 6572 | `3299d7ae7a42e44bb36703206a0bb97f9a5bd0d99264a584488446491a5a0c2b` |
| `inputs/preregistration-twenty-four-scrolls.md` | the pre-registration of the run on the twenty-four scrolls of the competition set, written 2026-09-15, which fixed three seeds per slice | 3699 | `2128e85a9f66b4ef6608f69498bde3ee11497fce065f4052b953eeb2aaaaf75e` |
| `inputs/note-twenty-seeds.md` | the design note of 2026-09-16 10:59Z for the twenty seed tables, post hoc with respect to the frozen paper and saying so | 4055 | `0adafaf6102993ae1997183818e083ff4da830105e3b39ea6753cec9dea531df` |

The `document` column of `evidence/prereg-timeline.csv` names these files as they are named here.

## Licences

The code in `tools/` and `inputs/` is MIT, as `../../../LICENSE` says. The article and its figures
are CC BY 4.0. The evidence files are CC BY-NC 4.0. The references
under `inputs/reference/` are published by the Vesuvius Challenge under the terms of the challenge
data; those under `inputs/external-references/` are third party and MIT, and
`inputs/external-references/PROVENANCE.md` says which came from where.
