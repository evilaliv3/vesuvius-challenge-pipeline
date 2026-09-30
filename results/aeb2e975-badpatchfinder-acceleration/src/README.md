# Walkthrough of the figures

This is the walkthrough of the figures only. The folder holds a work: its draft is in `paper/`,
the files its numbers are read from are in `evidence/studies/`, its pre registrations are in
`prereg/`, and the top level `README.md` is the work's page and not this one's. What follows
covers `tools/` and `evidence/figures/`.

No figure source carries a number. Each figure is
two files with the same name: a Python script that reads the study CSVs the figure is drawn from
and writes `evidence/figures/<figure>.csv`, the table of the numbers plotted, and a source that
draws the picture. For the four plots the source is a standalone pgfplots document that reads
that CSV back with `pgfplotstable`; for the two rasters the script is the source, and it writes
the PNG and the CSV in one run.

That arrangement is the point. The picture and the table of plotted numbers are the same file
read twice, so they cannot disagree, and a figure that would need a number no CSV holds says so
on its own face instead of borrowing one.

## The shortest check

```
bash ../../render_all.sh tables     rewrite every evidence/figures/<figure>.csv
bash ../../render_all.sh plots      the tables, then the pgfplots figures into paper/figures
bash ../../render_all.sh            everything, the four rasters last
```

`render_all.sh` sits beside the two works because it renders both. Each raster refuses to start
above two cores busy of twenty four and says so rather than drawing: these scripts read
gigabytes, and a figure is worth less than a bench.

## What is here

```
evidence/figures.csv      the six figures: the script, the source, what each reads, and its state
evidence/figures/         one CSV per figure, the numbers plotted, written by the scripts
paper/figures/            the pictures, written by render_all.sh and not kept in the repository
tools/figlib.py           reading a study CSV, writing a plotted table, the load bar, the readers
tools/figpreamble.tex     what every pgfplots figure loads, and why the tables are wide
tools/s-f*.py, s-f*.tex   the six figures, one pair per figure
```

The study folders the scripts read are under `/data/scrollagent/runs/rev1/` and the growth trees
and delivered sheets in them are not in this repository: they are gigabytes. Every script takes
`--runs` to point elsewhere, and resolves each study file through `figlib.Studies`, which prefers
the live tree over the copy shipped in `evidence/studies/` and writes a warning into the plotted
table when the two differ. A study that is still running writes rows after its copy was taken,
and a figure drawn from a frozen snapshot is a picture of yesterday that does not say so. On the
night these were written that warning fired on `seed-search-1447/evidence/alignment-fanout.csv`,
whose shipped copy predates the repair of 00:31Z. The pre registration of each measurement is the
`DECLARATION.md` of the study that made it, under `prereg/`.

## One thing a figure says that the plan did not

Figure S3, the square of each seed against the fan out of its alignment map, was removed from the
article on 2026-09-30: it pictured a bound that the work withdrew. Its script and plotted table
stay in this folder.

Figure S4 does not colour its strip. The counts of what became of seed34's stale ids are in
`id-inventory-seed34.csv` and the ids are in `impossible-ids-seed34.csv`, and nothing joins them,
so the figure prints a pending line naming the table that would.

## A missing key is not a zero

`figlib.required` and `figlib.required_number` raise rather than return a default, and every
figure here uses them for a value it cannot draw without: a square's side, its corner. A side of
zero is a sheet with no square, which is a real and different thing from a side the file does not
carry, and a raster that silently drew the first when the second was true would look entirely
plausible. Where an absence is legitimate the scripts test membership and write what was missing
into the plotted table. The rule comes from a reader of `quiet-bench/evidence/cube-stages.csv`
who wrote `named.get("RESIDUE", 0)` against a table whose key is a whole sentence: the lookup
missed, the default came back, and 0.000 is indistinguishable from a measurement of zero.

## One rule about a table that carries two voxels

`remeasure-at-9362/evidence/restated.csv` has `largest_square_mm_at_9_0` next to
`largest_square_mm_at_9_362`. They differ by 4.02 per cent and nothing in a row says which one a
reader wants. Two readers of this laboratory took the wrong one from it within ten minutes on the
night these figures were written, in opposite directions. No figure here reads that file: every
square is column `square_mm_min_step` of a per sheet table whose own header states its voxel, and
the plotted table writes that column name beside the number. **Any caption or sentence that
prints a number from a table with two unit columns prints the column name beside it.**

The largest fully covered square this laboratory has measured on a delivered sheet of PHerc. 0139
is **12.1230 mm**, on sheet 1, and three arms reach it: C40, P40 and A500. That is the maximum of
`square_mm_min_step` over the twelve arms and six hundred and ten measured sheets of
`remeasure-at-9362/evidence/squares-*.csv`, and the figures that use it recompute it at render
time through `figlib.largest_delivered_sheet` rather than taking an arm on faith.

## Figures of the scan

Figures S5, S6 and S7 show reconstructed volume data and delivered surfaces of PHerc. 1447 and
PHerc. 0139, with our own surfaces drawn on them. They are kept in the article by the owner's
decision of 2026-09-30, which suspends the rule against surface texture of this scroll;
`evidence/figures.csv` records that decision in its `not_for_public` column, and each script and
plotted table says so in its own header.

Code is MIT, the article and its figures are CC BY 4.0, the evidence files are CC BY-NC 4.0.
