# second-reference

One table: how far the hand umbilicus of a scroll sits from an umbilicus built as a per slice
centroid of the papyrus mask, on the fifteen scrolls that carry a hand umbilicus.

## Why the file is here

The article quotes a distance measured on PHerc1218 between its hand umbilicus and the umbilicus
that `vesuvius-sheet-tools` ships for it. That second umbilicus is not a second hand annotation.
Its producing script, `scripts/constraints/make_umbilicus.py`, says in its own header that it takes
the papyrus centroid of each slice as the umbilicus position; it reads the published instance
labels only as a mask, thresholded at `labels > 0`, and never uses which sheet is which. So the
second reference is a per slice centroid of the papyrus mask, which is the construction the
article scores as its `centroid` baseline.

Because only the support of the labels enters, the same derivation runs from files the challenge
publishes for every scroll, the masked scan and the m7 surface prediction, and not only for the
two scrolls that carry published instance labels. That is what this table holds.

## Where it comes from

The study that measured it, closed on 2026-09-18, is not in this repository: producing the second
umbilicus costs about 20 GB of downloads and its scripts run against a cache that is not published.
The one table the article reads is `hand-vs-mask-centroid.csv` beside this file, copied from that
study unchanged in every number. `tools/second_reference.py` recomputes from it every value the
article quotes.

The `second_reference` column says which second umbilicus a row is measured against: `mask centroid,
derived here` for the derivation made from the masked scan and the surface prediction, `Dopico,
published` for the file `vesuvius-sheet-tools` ships.

## What each row is

`A` is the hand umbilicus of that scroll, the same file `fifteen-config.json` names and every
other tool in this folder reads. `B` is the second reference. Sixteen rows for fifteen scrolls:
PHerc1218 carries two, one for the published file of `vesuvius-sheet-tools` and one for the
derivation made here from the masked scan and the surface prediction, which agree to 0.116 mm and
0.113 mm in the two directions. The published row is the guard that the derivation reproduces the
shipped file; `tools/second_reference.py` drops it from every count so that PHerc1218 is not
counted twice.

Distances are medians over the control points of the polyline being measured, in millimetres of
the scan the hand reference is annotated on, both directions, over the coverage the two share in
z: the same function and the same convention as `evidence/reference-uncertainty.csv`, which the
study reproduced cell for cell, all 36 of them, before measuring anything new.

`estimator_error_mm`, `estimator_error_k20_mm` and `centroid_baseline_mm` are copied from the
article's own `evidence/cpp-k20.csv` so that a row reads across. They are not remeasured here.

## What is not in this folder

The derivation itself. Producing `B` costs about 20 GB of downloads, two sets of third party
instance labels from Kaggle and fifteen level 4 pyramids from the open data bucket, and its
scripts stay with the study that ran them. `tools/second_reference.py` recomputes every number
the article quotes from this table, and nothing else here depends on the derivation being rerun.

## Licence

The distances are ours, CC BY-NC 4.0 with the rest of `evidence/`. The hand references keep the
licences `PROVENANCE.md` of `../external-references/` and `README.md` of `../reference/` give
them. The instance labels the guard rows check against are third party Kaggle datasets,
`iyndopicomartnez/pherc1218-sheet-instance-labels` under CC BY-NC 4.0 and
`jhjeong0815/pherc0332-sheet-separation` under CC BY-NC-SA 4.0; no byte of either is redistributed
here.
