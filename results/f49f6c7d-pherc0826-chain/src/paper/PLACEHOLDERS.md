# Numbers that wait for a file

Opened 2026-09-28. Each row is declared in `src/tools/paper_numbers.py` with the file and column that
fill it; while the file is absent the macro is not written, `paper_numbers.py` exits 3, and
`build.sh` refuses the article. The paragraphs that use them sit in `%% PENDING` blocks of
`body.tex`, which only the preview drops. When a file lands: rerun `src/tools/copy_evidence.py`
(it re snapshots every study, so rerun `chain_summary.py`, `area_summary.py` and `render.sh` too),
then the build.

| block | macros | file (under src/evidence/studies/) | note |
|---|---|---|---|
| section IV, road 1b | RoadOneBFormula, RoadOneBAtwo, RoadOneBVtwo, RoadOneBSquare | `area-0826-90/collection-eight-6365.csv`, row whose sheet begins with «all », columns stevens_formula_cm2, a2_share, v2_cells, square_mm_delivered | 2026-09-28T06:1xZ: name confirmed by the coordinator (it replaced the guess collection-road1b-6365.csv); eight seeds, ranks 1 to 8 of road1b-seeds.csv, cut from 12 by the director before launch (06:01:51Z); expected about 2026-09-28T19:00Z to 2026-09-29T00:00Z, killed at 2026-09-29T18:00Z if not done |
| section V, item 91, Table IV | ArmA to ArmD × Cpu, Wall, Sheets, Formula, Square, Atwo, Vtwo, Deaths; ArmESeedsPerDraw; ArmSeeds | `stevens-changes-0826-91/arms.csv`, one row per arm A to E, columns cpu_seconds, wall_seconds, sheets, stevens_formula_cm2, largest_square_mm, a2_share, v2_cells, deaths, seeds_per_draw (E), seeds (C) | the study did not exist at opening; file and column names are this work's request. Arms A and B not finished by 2026-09-30T12:00Z are rows whose cells read «not run», written by the study, never by this work |

## 2026-09-28T08:3xZ: the work becomes the September headline article

Director 06:40:45Z and PLAN 93 addition 07:53:42Z (spine), then 08:03:17Z (owner's rule, scope): the
article measures only the assembly on PHerc0826, with item 91 as its one comparison; the four works
are cited for their modules on their authors' data; Stevens' 365 cm2 is a labelled reference on
PHerc1667 only. Item 93's section «The four corrections on PHerc. 0826» is DROPPED, with its pending
file (four-corrections-0826-93/summary.csv, requested at 08:0xZ and removed the same hour).

item 91's arms.csv exists with cells «pending» and rows noted «pending N of M seeds»: paper_numbers.py
treats both as a missing file, so neither the word nor a median over part of the seeds is written.

| still open | what fills it |
|---|---|
| module before/after images from PHerc0826 at the same place and scale (a2 flags, SetSeed, bad patch finder A against B, flattened mask) | tools c-f11 to c-f14 being drawn by a figure agent; each enters the text with its caption's numbers as macros from its CSV (key column), then gate 12 holds on the real folder |
| c-f10 (papyrus, page 1) | in the text now; its tool joins gate 15 (rerun, rows compared) once the figure agent's fixes land |

## 2026-09-28T12:3xZ: the cut off, declared before it (director 12:21:38Z, owner's word)

`src/tools/cutoff.py` holds the rule and writes `evidence/derived/cutoff.csv`; the decision is taken once, at
the first run at or after **2026-09-29T03:30:00Z**, and kept:
- road 1b: `collection-eight-6365.csv` absent from the snapshot at the cut off gives the fallback paragraph
  (the four seed collection, and the eight seed run «did not finish before this article's cut off»); present,
  the eight seed paragraph. The switch is `\ifRoadOneBRun`, written by paper_numbers.py from the decision only.
- item 91: an arm with at least one completed seed prints its row with the count of completed seeds beside
  it; an arm with none prints «no run» (the caption says what it means). Neighbouring arms are also compared
  on the seeds both completed (`tools/arms_paired.py`, Table of paired arms).
Before the cut off both stay pending and the article refuses. `tools/finalize.sh`, run BY HAND by a round
at or after 03:31Z (it refuses earlier; a detached waiting runner was launched at 12:32Z and stopped at
12:45Z, since an unattended action at the cut off is not allowed), re snapshots, decides, redraws, builds
the article and renders its pages to the laboratory folder `outputs/artifacts/fifth-work/final/`. Before
running it, the round sets `\SeriesDraftfalse` in `src/paper/sidestripe.tex` (the owner's commit script
refuses a draft mark) and afterwards fills ARTICLE_C_SHA and WANT_C of the owner's commit script itself. Simulated in a scratch copy with the cut off
passed: 0 pending, 4 macros unused by the fallback, 7 pages, every gate passes except gate F, which waits for
`results/facts/check_facts.py`.

## 2026-09-28T12:5xZ: growth section additions (director 12:29:13Z and 12:30:13Z)

- The compile time constants simpaper10 uses: SEED_X, SEED_Y, SEED_Z (parameters.h lines 15 to 17 at
  62cbc21, with the seed axes after them) and SURFACE_ZARR (line 13), opened at simpaper10.cpp line 201;
  VOLUME_ZARR is not used by simpaper10 and is not stated (coordinator's correction).
- The one object build: nongrowth-profile-1447/build-objects-only.csv (series corrected: 3.11 against 19.73
  CPU s, binary identical) and chain-0826/build-objects-check.csv (9 of 9 objects only builds equal to a
  full make, 3 variants).
- Item 96 (run time parameters): the text switches on `runtime-params-96/evidence/identity-summary.csv`
  (requested name, the form of chain-0826's identity-0826-summary.csv, last column identity_holds). In the
  snapshot and holding: stated as done; otherwise stated as the next step offered to Stevens. Never pending.
- Upstream: villa 1885 is closed (merged_at from the API) and replaced by issue 1914 and pull request 1915;
  that passage was written by the facts agent at 12:37Z in this body.tex, kept. The items the facts table
  carries are read from its saved answers (tools/fetch_upstream.sh copies them); the others are fetched by
  that tool, which never overwrites a good answer with an error.

## 2026-09-29T07:2xZ: the reframe around the checks (director 06:54:31Z and 07:15:48Z, owner's word)

Abstract first half and Section I rewritten (the engine is not ours; the loop and the checks are; what the checks caught;
three contributions); new Section IX «The checks as a tool» with figure C20 (c-f20-best-windows.py, best-windows-0826's
panel data pinned by sha256 in src/tools/c-f20-best-windows-pins.csv) and a closing paragraph of next steps. New derived
table src/tools/checks_summary.py; fibre_summary.py gains the rows fibre_top_failing_*; copy_evidence.py gains the study
best-windows-0826 and the option --only, so that adding a study does not re snapshot the others.

| block | macros | file (under src/evidence/studies/) | note |
|---|---|---|---|
| Section I and Section IX, positive control | Pc* and the switches ifPcNeither, ifPcRight, ifPcWrong, ifPcInvalid (paper_numbers.py, from checks_summary.py) | `positive-control-0139/verdict.csv`, `control.csv` | filled 2026-09-29T09:1xZ from the first verdict row; the study appends rows as its variants are read: rerun `copy_evidence.py --only positive-control-0139` and the build to carry the last row |
| Abstract and Section IX, render routes R2b (director 12:52:52Z, the headline: our search finds the start, the organisers' tracer makes the surface, our checks certify it) | RoutesHeadlineAbstract, RoutesHeadlineSection (reserved slots, to be replaced by macros of its final files) | `render-routes-0826/routes.csv`, `square-checks.csv` (not yet in PLAN) | due 20:00Z; numbers only from those files once final; regrid_z.py renders stay out until the director clears them |

2026-09-29T13:0xZ, director 12:52:52Z: the positive control carried from verdict.csv, null-best.csv and labelfree-w016.csv
(checks_summary.py rows pc_*); the PHerc0826 ink reads are stated only as «not measurable at our sensitivity» with the w016
control beside them; results/facts gains six rows (facts.py section 13, check_facts.py MACROS Pc*), prepared as a separate
patch since results/facts is also in the owner's commit of today.
