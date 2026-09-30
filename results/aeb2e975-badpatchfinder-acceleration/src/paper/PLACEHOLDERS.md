# Open placeholders of the draft, and the file and column that fills each

Written 2026-09-22, revised at 02:2xZ when three of the eight closed. One row per marker in
`draft.md`. A marker is never a number, and the draft prints a provisional figure beside one only
where the figure that exists today is labelled with the machine it was taken on. A closed row
stays here with the file that closed it, because a register that deletes what it resolved cannot
be audited.

`quiet-bench` is the bench of `runs/rev1/quiet-bench/`, still running when this was revised, on
seed40's untouched arm.

## Still open: four

| # | section | what is missing | file and column that fills it |
|---|---|---|---|
| 1 | 1, the stage table | the `c` row for seed26 and seed40 on a quiet machine | `quiet-bench/evidence/c-stage-runs.csv`, column `seconds`, arm `c2`, rows `PHerc1447-seed26` and `PHerc1447-seed40` |
| 3 | 4, the time table | the untouched and the changed arm on seeds 26, 40 and 38 on a quiet machine, and the three ratios | `quiet-bench/evidence/c-stage-runs.csv`, column `seconds`, `binary_label` `plain` and `c2`; the spreads and the ratios from `quiet-bench/evidence/c-stage-summary.csv`. Rows for seeds 01, 15 and 48 are **not** replaced and stay labelled as shared machine numbers |
| 6 | 4, the ribbon | at least one further repeat of the untouched arm on seed26, so the baseline of every ratio has a spread of its own | `quiet-bench/evidence/c-stage-runs.csv`, rows `plain` on `PHerc1447-seed26`. Asked for by the direction on 2026-09-21T23:49:50Z as a dated addition after the bench ends |
| 7 | 7, the cost table | every cell. Growth measured with two or three growths in parallel, the `c` stage columns on a shared machine | growth from `seed-search-1447/evidence/per-seed.csv`, column `growth_wall_clock_seconds`; the `c` stage for seeds 26, 38 and 40 from `quiet-bench/evidence/c-stage-runs.csv`, column `seconds`; the sums and the quotients recomputed by the tool that writes `seed-search-1447/evidence/cost-per-ribbon.csv`, never by hand |

## Open since 2026-09-26: what the direction ordered for this work and the text does not carry yet

Not markers in the text: sections the direction assigned to this work that have no measurement
to print. Written 2026-09-26 by an agent of the coordinator; none of them is a number.

| # | where it would go | what is missing | file and column that fills it, and its date |
|---|---|---|---|
| 8 | a section after 9, Stevens on his own scroll (director, 2026-09-25T06:22:48Z, item 69) | our chain grown on PHerc. 1667 from his input, `s4_059_medial_ome.zarr`, measured by the union tool of `coverage-union-1447` beside his ten components (section 8 already carries his components, 363.8629 cm2 with every overlap counted) | no study of item 69 exists under `runs/rev1/` at 2026-09-26T05:5xZ. **Cutoff 2026-09-28T06:00Z**: if its union row is not in by then, the work goes out without it and the section follows after the 30th |
| 9 | section 7, the growth sentence | the growth's clock with the chunk store cap and the other identical arms (items 75 (c), 77 (c), (d)) | a quiet window whose summary gives three counted runs per arm; `quiet-window-2026-09-26/summary.csv` has fewer, so every clock rule is «not measurable». The growth section is a revision after the 30th (director, 2026-09-25T17:12:22Z) |
| 10 | section 9, the offer | the prior art search on the scrollreading repository's issues and pull requests before the seed for the annealing is offered upstream (director's rule of 2026-09-23T22:58:57Z) | not done: the local clone's branches all keep `std::random_device` at anneal.cpp 496 and 675, which is not a search of the upstream issues |

## Closed: three

| # | section | what it was | what closed it |
|---|---|---|---|
| 2 | 2, the fan out table | seed44's fan out, which is also the answer to the one pre registered prediction of `early-tangle` | **32.97, a tangle.** `early-tangle/evidence/prediction-seed44.csv`, column `answer_when_the_growth_ends`, and `seed-search-1447/evidence/prediction-seed44-square.csv`, column `fan_out`. **Not** `alignment-fanout.csv`: see the warning below |
| 4 | 4, the seventh tree | the untouched `c` stage of seed11, which existed in three roundings in three places and in no column | **22,699 s, 6 h 18 min, return code 0.** `seed-search-1447/evidence/untouched-seed11-downstream.csv`, columns `seconds` and `return_code`, row `c`, written 2026-09-22T02:18:34Z from the runner's own log |
| 5 | 4, the earlier performance patch | its factor, which a prepared text claimed at seventeen | **31.11** on seed26, with 1.05 for the two changes of this work and 32.59 for all six together. `quiet-bench/evidence/a8-factor-medians.csv`, column `factor`, with `numerator_range` and `denominator_range` beside each |

## A warning about `alignment-fanout.csv`, for whoever writes the figures

That file's row `PHerc1447-seed44` still reads **`not measurable` in `fan_out`, `edges`, `keys`,
`patch_files` and `keys_without_a_patch_file`**, checked at 2026-09-22T02:19Z against the file on
disk, whose mtime is 00:30:28Z. What was repaired at 00:31Z is the five columns it **copies** from
`per-seed.csv`, and `tools/check_fanout_agrees.py` guards those five copies and nothing else: its
`COPIED` tuple is `largest_square_mm_min_step`, `traced_area_mm2`, `in_the_distribution`,
`downstream_return_code`, `growth_return_code`. A script that reads seed44's fan out from that
file gets `not measurable`, and if it takes a default it gets a zero that reads like a
measurement. The number's home is the two prediction files named in row 2 above, until the fan out
tool is re run over seed44's own `rel.csv`.

Two further things in the same neighbourhood. seed44's 32.97 was computed with the count of
**patch files** as the key count, which is the same thing on every tree here but seed34, where the
map has 104 keys the disk does not have; the draft says so where it prints the number. And
`prediction-seed44-square.csv`'s `basis` column lists five squares, among them 7.5686 for seed11,
which no evidence CSV on this disk carries, and it omits seed34's 5.2008; the draft therefore
quotes that file's `fan_out`, `kind`, `claim` and `confidence` and not its `basis`.

## Three things that are not placeholders and must not be turned into one

- **Byte equality.** It does not depend on load and is not re measured:
  `c-stage-cost/evidence/identity.csv` (585 comparisons), `identity-seed11-untouched.csv` (40) and
  `c-stage-on-0139/evidence/identity-by-tree.csv` (936 files written by the downstream). The
  1,473,675 carried input comparisons in that last file are hard links and are **not** identity
  evidence; the draft says so where it prints the 936.
- **The step counts.** 51,500,264,151 against 946,327, and the agreement of the exact walk with the
  counting build at 10,761,063 on seed26, are counts and not times.
- **No number in the draft comes from a default.** Where a file has no value for a quantity the
  draft writes «not measurable» and names the file that does have one; nothing is read through a
  fallback, and no zero in the draft is an absent key.

## A note on the copies under `src/evidence/studies/`

They are snapshots and are replaced, never edited. `quiet-bench/c-stage-runs.csv` was copied while
the bench was still appending to it. The copies were refreshed at 2026-09-22T02:2xZ.
