# early-tangle: telling a tangle from a ribbon while the growth is still running

Opened 2026-09-21T15:17:45Z by the coordinator on the direction of 2026-09-21T15:08:07Z, PLAN 51 point (b).
Written before any number of this study exists.

## Why this and not something else

`seed-search-1447/evidence/alignment-fanout.csv` splits the nine seeds that wrote a `rel.csv`
into two kinds with nothing between them: three at a fan out of 4.51 to 4.64 that delivered the
squares of 10.39 to 12.72 mm, and six at 27.40 to 37.67 that delivered small squares or nothing.
The fan out is known only when the growth ends, and a growth of this chain takes 40 minutes to
three hours and writes its patches only at the end. Six of the ten seeds cost that time and gave
a square under 9.3 mm or no square at all.

If the kind can be read early, the search stops a tangle in minutes and spends the machine on
ribbons. That is the first lever on the yield of the seed search since the choice of the seed.

## The question, in one sentence

Can the kind of a growth be told from the growth's own standard output, early enough and
reliably enough to stop it?

## The quantity, fixed before it is read

The growth prints, per patch, a line of the shape `Patch <n> has <m> matches`. The quantity is
the **running mean of m over the first K such lines** of a growth's log, for K on the declared
ladder **50, 100, 200, 500, 1000, 2000**. Nothing else is read, and no other line of the log is
used for the verdict.

The population is the **nine seeds of `seed-search-1447` that wrote a `rel.csv`**: 01, 11, 15,
26, 34, 35, 38, 40, 48. seed44 is excluded, declared here and not after the fact, because its
capped growth wrote no `rel.csv` and so has no final fan out to be judged against. The three
ribbons are 26, 01, 15; the six tangles are 38, 40, 48, 11, 34, 35. That labelling comes from
`alignment-fanout.csv` and is not decided by this study.

## The bar, declared now

The lever exists if **both** hold at some K of the ladder:

1. **Separation.** A single threshold T puts all three ribbons on one side and all six tangles on
   the other, with no seed on the wrong side. Nine of nine, not eight.
2. **Early.** The K-th matching line is written within the **first 10 per cent of that growth's
   wall clock**, on every one of the nine. The time of a line is taken from the growth's own
   progress, not from the file's mtime, so it is measured as the share of the log's matching
   lines that precede it, and the declaration accepts that as the proxy and says so here: it
   assumes the growth announces patches at a roughly even rate, which this study checks and
   reports whether or not it holds.

If separation holds at some K but the earliness does not, the answer is «the kind is readable but
not early», which is not a lever and is written as such.

## What would make it fail honestly

- The mean not separating at any K: the early patches of a tangle look like a ribbon's, and the
  tangle is made later in the growth. Then the lever is not here and 51 (b) closes negative.
- Separating at K = 2000 only, with 2000 patches arriving past a tenth of the growth: readable,
  not a lever.
- The margin between the two groups being smaller than the spread inside either group, which
  would mean a threshold fitted on these nine and nothing else. The margin and both spreads are
  reported beside the verdict, always.
- Fewer than K matching lines in a log, which is a seed that cannot be judged at that K and is
  written as not measurable, never as a pass.

## What this study does not do

No growth is run, no growth is stopped, no parameter is changed. It reads nine logs that already
exist on disk. A rule that stops a growth is a different study and is not opened by this one.

## Dated addition, 2026-09-21T15:18:57Z: the declared quantity failed, and a second one is declared here

The quantity declared above, the running mean of `m` in `Patch <n> has <m> matches`, **does not
separate at any K of the ladder**: `evidence/early-mean.csv`. At every K the ribbon range and the
tangle range overlap, and seed01, a ribbon, sits above five of the six tangles. Point 1 of the bar
fails. Point 2 was never the difficulty: at K = 2000 the worst seed is at 0.0445 of its
announcements, well inside the declared tenth. **51 (b) is closed negative on that quantity** and
the outcome will say so in those words.

Writing the table put a second quantity in view that was not declared, and it is declared here,
before it is measured, rather than reported as though it had been the plan:

**The count of announcements itself.** The whole growth prints 44,924 to 53,766 of those lines on
the three ribbons and 524,636 to 1,140,431 on the six tangles, read from column `announced` of the
same CSV. That is a factor of ten with nothing between, but it is a total, known only when the
growth ends, so **it is not a lever and cannot become one by being restated**.

What could be a lever is its **rate**, which a watcher can read on a running growth with no clock
and no instrumentation: **the share of the first N lines of the log that match
`Patch <n> has <m> matches`**, for N on the ladder **10,000, 50,000, 100,000, 500,000**.

The bar for this second quantity, fixed now:

1. **Separation.** One threshold puts all three ribbons on one side and all six tangles on the
   other, nine of nine.
2. **Early.** The N-th line arrives within the first 10 per cent of the log, measured as N over
   the log's total lines, on every one of the nine.
3. **A margin worth trusting.** The gap between the two groups is wider than the spread inside
   either. The margin and both spreads are reported beside the verdict.

What would make this one fail honestly: the share not separating; separating only at N = 500,000,
which on a 1.5 million line log is a third of the growth and not early; or the ribbons' own three
values spanning more than the gap, which would mean a threshold fitted to three points.

**A caveat that must travel with whatever this finds.** The labels are nine seeds of one scroll
grown by one binary route, and «ribbon» and «tangle» are this home's words for two clusters in one
measurement. A rule that stops a growth on this evidence would be fitted on three ribbons. Nothing
here authorises stopping a growth; that is a different study and is not opened by this one.

## Dated addition, 2026-09-21T16:08:59Z: the rule taken to the other scroll, declared before it is applied

The direction of 2026-09-21T15:36:28Z asks for «the predicting rule on every growth, retested on
0139's logs». The rule is the one that passed above: the share of the growth log's first 100,000
lines matching `Patch <n> has <m> matches`, with the ribbon band **0.02825 to 0.04275** and the
tangle band **0.12002 to 0.15170**, both fitted on nine seeds of **PHerc1447 only**.

**The population, fixed now and not after seeing anything.** Every growth on this disk that (a)
wrote a log carrying that line and (b) has a growth tree with a `rel.csv` beside it, so that its
kind can be settled independently by the fan out exactly as the nine were. The candidates found
by listing, before any number was read: `growth-repeat`, `reference-b40`,
`seed-distance-ladder` (D150 and D450) and `held-patch`, all four declared PHerc0139 in their
own declarations; `why-the-growth-stops` and `ceiling-24000` name no scroll in theirs and are
**included only if the tool can establish the scroll from the study's own files**, otherwise they
are reported as not measurable and not quietly dropped.

**The kind is settled by the fan out, never by the rule being tested.** Twice the edges over the
keys of each growth's own `rel.csv`, the same arithmetic as
`seed-search-1447/evidence/alignment-fanout.csv`, with the same cut at 10, which on PHerc1447
fell in an empty gap between 4.64 and 27.40. **If PHerc0139's fan outs do not fall in two groups
with that gap empty, the cut is not transferable and the outcome says so before saying anything
about the share.**

### The three things this can find, and what each means

1. **The bands hold.** Every 0139 ribbon lands in 0.02825 to 0.04275 and every tangle in 0.12002
   to 0.15170. Then the rule is a property of the chain and is usable on any scroll.
2. **The rule separates but the bands move.** The two kinds are still apart on 0139 but at other
   values. Then the rule works per scroll and needs a calibration on each, which is a much weaker
   and much more expensive thing, and the outcome says the number would have to be fitted before
   it could be trusted anywhere new.
3. **The rule does not separate on 0139.** Then what was measured on PHerc1447 is a property of
   those nine growths and not of the chain, and **51 (b) closes negative after all**. This is the
   outcome that costs us the lever, and it is written here so that finding it is not a surprise
   anyone can talk their way out of.

### What would make this addition itself unsound

Too few growths of one kind to say anything: **if 0139 gives no tangle at all**, which is possible
because our chain works on that scroll, then the test has only ribbons and **cannot separate
anything**. That is not outcome 3, it is «the test could not be run», and the two must not be
confused. The count of each kind is reported first, before any share.

## Dated addition, 2026-09-21T17:15:22Z: the repeat control this study did not have

Everything above judges the rule across seeds. Nothing judged it **across two runs of one seed**,
which is the control that says whether the number is a property of the growth or of the machine
that ran it. PHerc1447-seed44 gives it for free: it was grown twice with the same binary and the
same compiled seed, at 06:00:07Z under a cap and at 15:10:40Z without one, and the binary saw
108,624 MB free the first time and 89,526 the second.

**An honesty note about the order, because it was wrong.** I wrote the measurement and this
paragraph in one action, and the tool ran first. So the bar below was written **after** I had seen
the two numbers, not before, and this addition is not a pre registration. It is stated here
because the rest of this study was pre registered and a reader who assumes the same of this
paragraph would be wrong.

The bar, which would have been the natural one blind and is stated after the fact: **the two
shares differ by less than a tenth of the gap between the two kinds**, that is by less than 0.007.
If they differ by more, the rule reads the machine and not the growth.

The result is in `evidence/repeat-control-seed44.csv` and in the outcome.
