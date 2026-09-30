# Walkthrough of the text and the evidence

What is in this folder, where each number of `../paper/draft.md` comes from, and what has not
been done. `../README.md` is the walkthrough of the figures.

```
../paper/draft.md         the text, ten sections: the eight of the plan, a ninth on the author's remedy and a tenth on limits
../paper/PLACEHOLDERS.md  every marker left in the draft, and the three that closed
studies/                  the CSVs, one folder per study, copied unchanged from runs/rev1/<study>/evidence/
figures/                  one CSV per figure, the numbers plotted, written by the figure scripts
../prereg/                one file per study, its declaration as written before any number of it existed
```

## How to check a number

Every number in the draft names the file it was read from and the column on it. The file is under
`studies/<study>/`, copied byte for byte from that study's own `evidence/` folder, and each was
written by a tool of that study. Nothing is typed by hand. The check is to open the file and read
the column.

Two numbers come from a column whose own source is a log, and each says so where it appears: the
reference times of the `c` stage on the large trees of PHerc. 1447, which
`studies/c-stage-cost/c-stage-times.csv` records in `reference_seconds` with the log named beside
them in `reference_source`; and the untouched `c` stage of seed11, which lived in a log and in
three different roundings in three places until a tool read it into
`studies/seed-search-1447/untouched-seed11-downstream.csv` on 2026-09-22, where it is 22,699 s
with a return code of zero. The profile shares come from `studies/c-stage-cost/profile-baseline.csv`,
a CSV the study wrote from `perf report`.

## A missing key is not a zero

**No number in the draft is read through a default.** Where a file has no value for a quantity the
draft writes «not measurable» and names the file that does have one.

One case is live and it matters for anything that joins two of these tables.
`studies/seed-search-1447/alignment-fanout.csv` reads `not measurable` in `fan_out`, `edges`,
`keys`, `patch_files` and `keys_without_a_patch_file` on row `PHerc1447-seed44`. What was repaired
in that file on 2026-09-22T00:31Z is the five columns it **copies** from `per-seed.csv`, and its
guard `seed-search-1447/tools/check_fanout_agrees.py` watches those five copies and nothing else.
seed44's fan out is **32.97** and it is in `studies/early-tangle/prediction-seed44.csv`, column
`answer_when_the_growth_ends`, and in `studies/seed-search-1447/prediction-seed44-square.csv`,
column `fan_out`. A script that reads it from the fan out file gets an absence, and if it takes a
default it gets a zero that reads like a measurement.

The header of that same fan out file still says seed44 «grew zero patches under its 10800 s cap
and wrote no rel.csv». That was true of the capped first growth and is not true of the tree on
disk: `studies/seed-search-1447/per-seed.csv` records growth return code 0 in 9,097 s, 28,444
patches and 468,938 `rel.csv` lines for that seed.

## The studies, in the order the draft uses them

| folder under `studies/` | what it established | its declaration |
|---|---|---|
| `seed-search-1447` | ten drawn seeds of PHerc. 1447, their trees, their fan out, their squares | `../prereg/seed-search-1447.md` |
| `early-tangle` | the kind of a tree is readable 532 s into a growth that runs for hours, and the one prediction written before its answer existed | `../prereg/early-tangle.md` |
| `c-stage-cost` | the profile, the exact step counts, the two changes, the identity on seven trees of PHerc. 1447 | `../prereg/c-stage-cost.md` |
| `c-stage-on-0139` | the same two changes on eight growth trees of the reference scroll, identity and times | `../prereg/c-stage-on-0139.md` |
| `badpatch-crash` | the throwing call, the 104 orphan ids and the 73 reachable ones, before any change | `../prereg/badpatch-crash.md` |
| `orphan-guard` | the guard, what it refuses and what it does not move | `../prereg/orphan-guard.md` |
| `growth-bookkeeping` | the growth that reopened a folder, read out of the source and the filesystem | `../prereg/growth-bookkeeping.md` |
| `quiet-bench` | the re measurement of every headline time with nothing else on the machine | `../prereg/quiet-bench.md` |
| `seeds-at-scale-1447` | `seed-rule.csv` only: the seed rule of 2026-09-23, read per seed, which puts three of the ten on papyrus and seven in air (group `delivered-22-september-1447`, column `passes_rule`); re shipped 2026-09-26: the live file had grown by the groups of later draws (2,250 rows appended on 2026-09-25, groups `extension-751-1500-1447` and `extension-1501-3000-1447`), its first 653 lines, which hold the ten rows this work reads, are byte identical to the copy of 2026-09-23 | the study is `runs/rev1/seeds-at-scale-1447/` |
| `published-segments-eligible` | the published segments of the eligible scrolls, measured by the same square tool | the study is `runs/rev1/published-segments-eligible/` |
| `coverage-union-1447` | `union-per-sheet-renamed-v3.csv`, the same copy per sheet, read only to check that the two sheets of the ink sentence of section 10 are the two largest by the area accepted by the uncalibrated certificate in both modes; and `union-renamed-v3.csv`: the delivered cells of 29 seeds of PHerc. 1447 deduplicated at one cell and at two, unstitched, with Stevens' words beside as his; numbers by `tools/studies/coverage-union-1447/union_area.py`, names and labels by `tools/studies/certified-area/accepted_names_v3.py` (a copy of `union.csv` whose certificate labels read «accepted by a certificate that cuts a sharp change of winding and not a gradual one»; the column names stay `accepted_uncalibrated_*`) | the study is `runs/rev1/coverage-union-1447/` |
| `field-0826-0800` | `field-sums-renamed-v3.csv` only: per scroll, the delivered area of the published surfaces measured by this laboratory's tool and summed with every overlap counted; row `PHerc1667` is Stevens' ten published components; numbers by `tools/studies/field-0826-0800/field_table.py`, names by `tools/studies/certified-area/accepted_names_v3.py` | the study is `runs/rev1/field-0826-0800/` |
| `ink-detector-0139` | `descriptive-row.csv`: the organisers' 9 um detector on our two largest sheets of PHerc. 1447 and on the labelled segments of PHerc. 0139, descriptive, no null, written by `tools/studies/ink-detector-0139/descriptive_row.py` (the sheet only row of seed325, from `sheet_only_stats.py`, is in the file and not in the text); `tauil-quotes.csv`: the quotations of TAUIL Abd Elilah's survey, each checked verbatim against `inputs/github-api/tauil-pherc1447-ink-survey/README.md` by `tools/studies/ink-detector-0139/tauil_quotes.py`. No output of the detector is a figure | the study is `runs/rev1/ink-detector-0139/` |
| `stevens-remedy-half-on` | section 9: `remedy-parts.csv`, which of the three methods of Stevens' report12 reach the delivered sheets at 62cbc21, every quotation checked verbatim at its line by `tools/studies/stevens-remedy-half-on/remedy_parts.py`; `per-seed.csv` (`summarise.py`), his full recipe (annealing and bridges put back) on the ten seeds of `ten-seeds.csv` (`draw_seeds.py`), run by `rerun_remedy.sh`; `identity-off-PHerc1447-seed262.csv`, the same runner with the annealing left out, written by `tools/studies/patch-filter-harness-1447/identity_compare.py`; `draws-per-seed.csv` and `overlap-per-seed.csv` (`summarise_draws.py`), three more annealing draws on seed355, seed262 and seed664, the best square per draw and the declared overlap class with a2's flags, whose rule is in the header of `overlap-per-seed.csv` | the study is `runs/rev1/stevens-remedy-half-on/`, `DECLARATION.md` and its additions of 2026-09-25T14:01:33Z and 18:43:23Z |
| `growth-memory-1447` | section 7, one sentence: `summary-cap.csv` (`tools/studies/growth-memory-1447/finalize2.py`), the peak ratio of a growth of seed1111 with the chunk store capped at 128 over the unchanged one and the bar's verdict; `growth-unchanged-cap128.csv` (`grow_measure2.sh`), the identity of its growth tree and sheets | the study is `runs/rev1/growth-memory-1447/` |
| `quiet-window-2026-09-26` | section 7, the same sentence: `summary.csv` (`tools/studies/quiet-window-2026-09-26/summary.py`), read only to check that the clock rule of every arm is «not measurable» or «not applicable»; no clock is printed | the study is `runs/rev1/quiet-window-2026-09-26/` |
| `prize-eligibility` | section 1 and section 8: `prize-eligibility.csv` (`tools/studies/prize-eligibility/read_prize_eligibility.py`), villa pull request 1887 that took PHerc1447 off the First Letters list, its merge time, the line it removes and the counts of both prize lists at villa main, read from the GitHub API with the raw answers in `log/` | `../prereg/prize-eligibility.md` |

## What has not been done

- **The bench has not ended.** `studies/quiet-bench/c-stage-runs.csv` is a snapshot of a file that
  is still being appended to. Four of the draft's markers wait on it and every time in the draft
  is marked provisional for that reason; `../paper/PLACEHOLDERS.md` is the list, with the three
  that closed on 22 September kept in it beside the file that closed each.
- **No article is built from this folder.** There is no PDF and no LaTeX for the text here. The
  draft is under judgement.
- **The draft does not yet reference figure numbers.** It should not until each figure's table of
  plotted numbers is beside it, which is what `figures/` holds.
- **Nothing here has been offered upstream.** The two changes and the guard go to the author of
  the tracer as one series, and that text is prepared elsewhere.

## What was verified by running it here, and what was not

Verified by running: the two changes lay down from their patch files to the same working copy as
the hand edit they were developed as (`studies/c-stage-cost/patch-verification.csv`); the
untouched binary rebuilds byte for byte from the series, twice, on two different days
(`studies/c-stage-cost/binaries.csv`, `studies/quiet-bench/binaries.csv`); the harness of the
reference scroll reproduces, file by file, an output taken before it existed
(`studies/c-stage-on-0139/harness-reference.csv`); and every growth tree the runs read is byte for
byte unchanged afterwards (`studies/c-stage-on-0139/pristine-check.csv`).

Not verified: whether a stock upstream build, without this project's series, reproduces the 104
orphan ids exactly. It would require regrowing, and two corrections of the series change which
alignments are found, so the exact set would differ. What does not depend on it is that the path
producing an orphan id is entirely in the upstream source, which is read line by line in
`studies/growth-bookkeeping/upstream-vs-ours.csv`.
