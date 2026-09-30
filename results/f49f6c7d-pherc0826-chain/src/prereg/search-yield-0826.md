<!-- Shipped copy of search-yield-0826/DECLARATION.md, 2026-09-30, as the study wrote it. Where it says PRIVATE, private or never public it describes how the study kept its own outputs on the day it was written, before the owner's decision of 2026-09-30 to publish this article with no position on the scroll. -->
# search-yield-0826: squares found per machine hour, Stevens' pipeline against ours, counting the whole search

Declared 2026-09-28T18:24:40Z (`date -u`) by a coordinator agent, before any number of this study exists. Order: director
2026-09-28T18:20:15Z («a zero CPU measure for the 0826 article ... declare the formula before computing; state it as
composed with its parts»). Zero CPU: this study grows nothing and runs nothing but one Python tool that reads existing
CSVs. Read before this file, not computed: the headers and some rows of the source files named below (item 91's
arms.csv and per-run.csv, the chain's ladder.csv, per-seed-queue.csv, refill.csv, runs/<seed>.csv, the article's
chain-as-run.csv and chain-summary.csv, square20-0826-95's certified-squares.csv). No ratio, sum or count of this study
has been computed when this is written.

## The question

How many squares of 10 mm or more does each pipeline find per machine hour on PHerc0826, when the cost is the whole
search (every seed it tried, the attempts that died included), not only the seeds that delivered?

- **Original**: Stevens' pipeline as published (item 91 arm A), fed uniformly drawn seeds (the chain's random waves 1
  to 3), 3 growths at once on the 24 core machine (director).
- **Ours**: the chain on PHerc0826 as run, every wave in the order it ran (waves 1 to 3 random, 4 and 5 drawn near the
  earlier finds), per delivered seed item 91 arm C's time, 7 growths at once (director).

## What counts as a find

Two quantities, each a separate row, never pooled:
- **hole free**: a delivered sheet whose `hole_free_square_mm` is at least 10.0;
- **certified**: a delivered sheet whose `certified_square_mm` is at least 10.0.

Source: `square20-0826-95/evidence/certified-squares.csv` (tool square20-0826-95/tools/cert.py), rows with `source` C40
only (the chain as run at g 36000); C80 (the g 72000 regrowths) is never read. A sheet whose `status` is not
`measured` is not a find. **Counting: per seed** (the result): a seed is one find when at least one of its delivered
sheets qualifies. **Per sheet** is a column beside it (every qualifying sheet counted). A delivered seed with no C40
row in certified-squares.csv is written as a count in a check column, «not measurable» for that seed, never a zero.
Check column: the per seed hole free count against the article's `SeedsTen` (chain-summary.csv, scope all, quantity
seeds_square_at_least_source_mm, from per-seed-queue largest_square_mm_min_step), equal or not, written.

## The chain as run (both arms read it)

The article's rule: the chain frozen at 2026-09-28T16:15:12Z. The seeds, waves and outcomes are read from the article's
frozen snapshot, `results/f49f6c7d-pherc0826-chain/src/evidence/studies/chain-0826/` (`seed-rule.csv` column group and
the draw count per wave, `ladder.csv` one row per seed grown at the ladder cap with wall_s and group,
`per-seed-queue.csv` one row per queued survivor with delivering_binary, growth_return_code and
growth_wall_clock_seconds), and `src/evidence/derived/chain-as-run.csv` (in_chain_as_run). Waves are the five groups
in draw order: batch-1-400-0826, batch-401-2400-0826, batch-2401-6400-0826 (random), batch-6401-6712-0826,
batch-6713-6752-0826 (near). A delivered seed is a queue row whose delivering_binary begins with «delivered», the
article's test.

## Time: wall seconds per seed, turned into machine hours by the concurrency

**Per seed time is wall seconds** (item 91 per-run.csv `wall_seconds`: growth plus the five downstream stages of that
run, measured two runs at a time, each OMP_NUM_THREADS=3, on the shared machine). A growth holds one slot for its wall
time whatever its CPU; the director fixes the slots: k = 3 for the original, k = 7 for ours. **Conversion (declared
model: slots refilled back to back, no idle slot, and the wall of a seed at k at once equal to its wall measured at 2 at
once)**:

    machine_hours(parts at k at once) = sum of slot seconds / (k x 3600)

A step that holds the whole machine (the seed rule step) counts its wall seconds once, not divided by k. CPU seconds
(item 91 `cpu_seconds`) are read and written beside the wall figures as the confirmation the director asked for (medians
A 4430.15 s, C 513.50 s in arms.csv), not used in the result.

**Per delivered seed time t is the mean over item 91's 8 seeds** of the arm's `wall_seconds` (a total cost needs the
mean, not the median; the 8 seeds are item 91's stratified draw from the delivered 0826 seeds with at most 10000 growth
patches, one per cell of 8, so the mean is taken over equal weight cells). The median is a column beside it. Declared
limit: item 91's arms ran with SIMPAPER_PATCH_LIMIT 10000 and grew smaller trees than the chain delivered on the same
seeds (per-run.csv growth_patches, arm X); the chain's own as run delivery wall is therefore written as a third row
(below), never mixed into the order's rows.

## The formulas, as composed of named parts

### Original (arm A), per quantity q in {hole free, certified}

    N_O   = delivered seeds of waves 1 to 3 (the random waves), chain as run
    F_O,q = those of the N_O seeds that are a find for q (per seed; per sheet in a column)
    y_O,q = F_O,q / N_O                      the random draw yield, finds per seed grown to the end
    t_A   = mean over item 91's 8 seeds of arm A wall_seconds
    b_A   = full build CPU seconds per seed, nongrowth-profile-1447/evidence/build-objects-only.csv,
            series corrected, full_rebuild_cpu_s (Stevens' readme builds per seed with a full make)
    H_O   = N_O x (t_A + b_A) / (3 x 3600)   machine hours
    R_O,q = F_O,q / H_O = y_O,q x 3 x 3600 / (t_A + b_A)   finds per machine hour

**Declared model for the original, a bound in its favour.** Seeds that die under arm A (those that fail the seed rule,
end by themselves or write no patch at the ladder, or crash at growth) have no arm A time anywhere: item 91 grew only
delivered seeds. That time is **not measurable** and is **not counted**: the original is charged only for the seeds
that grow to the end, as if it knew them in advance, and it gets the chain's seed rule and ladder for free. So R_O is an
**upper bound** of the original's finds per machine hour. Its finds are counted on the chain's delivered sheets, which
item 91 shows are larger than arm A's own on the same seeds (per-run.csv best_square_mm, arm A against arm X): also in
the original's favour; the count of item 91's 8 seeds with best square at least 10 mm under A and under X is a column.

### Ours (arm C), cumulative over the waves in the order they ran, per quantity q

For each wave w, in order 1 to 5:

    S_w  = seed rule step wall seconds, whole machine: from chain-0826/evidence/refill.csv, the utc of the wave's
           «seed-rule» row minus the utc of its «draw» row (same from/to). Wave 1's steps were restarted across
           launches (13:14:29Z draw, 17:52:50Z seed rule), so its interval is not measurable; declared model: wave 1's
           S = 400 x the largest per draw S_w / draws_w of waves 2 to 5 (against ours). The draw's own seconds are
           written in no CSV (only its end time): **not measurable, not counted**, the one part left out.
    P_w  = ladder rows of the wave (ladder.csv, group), each a growth capped at 120 s
    L_w  = sum of their wall_s (ladder.csv), slot seconds
    B_w  = P_w x b_C, b_C = partial_build_cpu_s of the same file and row (the one object build), slot seconds
    D_w  = delivered seeds of the wave, chain as run
    t_C  = mean over item 91's 8 seeds of arm C wall_seconds
    G_w  = sum of growth_wall_clock_seconds (per-seed-queue.csv, as run by the chain's own binary) of the wave's queued
           seeds that grew and were not delivered (growth crashed, rc 139; or grew and stopped before its downstream):
           the chain's own time, since arm C has no time for them (declared)
    Seeds queued and never grown before the freeze (growth_return_code «not measurable») cost nothing beyond their ladder.

    H_w  = S_w / 3600 + (L_w + B_w + D_w x t_C + G_w) / (7 x 3600)
    H_C(W) = sum of H_w for w = 1..W, F_C,q(W) = finds of the delivered seeds of waves 1..W
    R_C,q(W) = F_C,q(W) / H_C(W)            the cumulative finds per machine hour after wave W

**The result is W = 5**, the whole chain as run, random waves included. Rows after each wave are written too (the
cumulative curve), and one row per wave alone.

### Third row, information: ours with the chain's own delivery time

The same as ours with D_w x t_C replaced by the sum over the wave's delivered seeds of growth_wall_clock_seconds plus
downstream_wall_clock_seconds of `chain-0826/evidence/runs/<seed>.csv` (as run, on the shared machine, at whatever
concurrency ran then), at k = 7. Labelled «as delivered, information», never the result.

### The comparison

    ratio_q = R_C,q(5) / R_O,q

written with every part beside it. Since R_O is an upper bound, ratio_q is a lower bound of our advantage (or an upper
bound of our disadvantage, if below 1).

## Measurement cost

Measuring the sheets (square.py, the a2 and certification tools) is not a search cost of either pipeline and is left out
of both; it is the same per delivered sheet.

## Output

`tools/yield.py` (Python, standard library, nice 10, one core) writes `evidence/yield.csv`: one row per arm and quantity
(and per wave for ours), columns: the parts named above with their values, the formula as text, the result, the per
sheet variant, the checks; a header line naming the tool and the sha256 of each input file read. It writes nothing else
but `evidence/yield-seeds.csv`, one row per delivered seed of the chain as run (wave, best hole free, best certified,
qualifying sheets), the per seed parts.

## What would change these rules

Nothing after yield.py's first run; a change is a dated addition below with its reason.

## Addition of 2026-09-28T18:25:55Z: G_w counts the downstream seconds too, before yield.py's first run

Read after the declaration, before any number: PHerc0826-seed6549 grew (rc 0) and its downstream ran and crashed (runs
file downstream_return_code 139, five stage seconds written). So G_w, for a queued seed that grew and was not delivered,
is its per-seed-queue growth_wall_clock_seconds **plus** the sum of its downstream_stage_*_seconds rows in
chain-0826/evidence/runs/<seed>.csv when that file exists (none when it does not). Nothing else changes.
