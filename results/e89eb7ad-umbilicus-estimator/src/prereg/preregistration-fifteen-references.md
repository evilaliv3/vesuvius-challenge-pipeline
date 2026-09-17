# Pre-registration: the three-value table on the fifteen scrolls, in two declared blocks

Written on 2026-09-15 at 15:33:39Z, **before** running the estimator on a single grid of the
eleven new scrolls, and **before** having seen one accuracy number outside the four already
published in `result-d-one-division.md`. It does not move afterwards.

The machine is busy with another measurement: this document is written now precisely so that the
criterion exists before the measurement is possible.

---

## 1. The decision on structure, taken by the responsible

The table goes in **two separate and declared blocks**, which are never mixed into a single column.

**Primary block: the five references of the challenge.** PHerc0125, PHerc0211, PHerc0332,
PHerc0826, PHercParis4. **This is where the claim lies**: on the references published by the
organisers, with the division removed, the estimator beats the centroid.

**Confirmation block: the ten third party references.** PHerc0191, 0257, 0268, 0358, 0800, 0813,
1203, 1218, 1447, 1545, all from `AlexeyDrobkovStrikesBack/herculaneum-umbilici`, MIT licence.
With author, method and licence beside every row, and with their weaker nature declared: clicked
with a mouse on images of pyramid level 3 (scale 8), one slice every about 480 in z. They serve to
answer the question the reader will ask anyway, that is whether it generalises: agreement between
**independent** reference sets is one more piece of evidence, because it says that the result is
not an artefact of the habits of one annotator.

**If the two blocks said different things, that disagreement is the result and it is told.**
They are not merged, the convenient block is not chosen, no scroll is removed.

## 2. What is in each row

Three values per scroll, plus the columns of provenance and of control:

| column | what it is |
|---|---|
| **reference** | which file, who made it, with what method, with what licence, how many control points fall inside the coverage in z |
| **published algorithm** | `align_and_extract_umbilicus` as it stands today in `volume-cartographer`, faithful transcription, median of the distance from the reference in millimetres |
| **algorithm with the division removed** | the same, with `normalgridtools.cpp:116` returning `score` instead of `score/wsum`, median in millimetres |
| centroid of the filled mask, level 3 | the baseline declared in our paper, and it is the column against which one wins or loses |
| fake axis | negative control: a constant axis at the centre of the field. Where it beats everything, on that scroll no ranking means anything |
| outside the volume | how many of the 24 estimates fall outside the bounding box of the grid, for each of the two variants |

Median, p90 and worst are reported. The criterion looks at the **median**; p90 and worst are
reported and do not enter the criterion.

## 3. How it is said, and how it is not said

**We say "lies at a distance", not "is in error".** The hand annotation has an error of its own
that we do not know until the measurement on PHerc1218 estimates it. A row of the table says how
far an estimate **lies** from that reference, not by how much it is wrong with respect to the true
axis, which nobody has measured. It is the exact point where our previous paper burned itself by
declaring itself "within the precision of the hand annotation" and having to retract it.

## 4. Method, fixed now

- **Input**: the `normal-grids` published on the bucket, `xy` plane, the same representation the
  estimator inside `volume-cartographer` runs on.
- **Same scan**: every scroll enters only if the volume identifier of the annotation coincides with
  that of the surface prediction the grids come from. Verified for all fifteen and written down in
  the survey of the references made on 2026-09-15; for Drobkov's ten, the level 0 width declared in their `meta.json` coincides
  with the bounding box of the `GridStore` in every case checked, so the scale factor between the
  two systems is 1 and there is no registration to invent.
- **Heights**: **24 slices** per scroll, evenly spaced in the intersection between the z range of
  the reference's control points and the slices the grid possesses. Twenty-four because it is the
  number used in every measurement of this line of work. The same slices for the two variants.
- **Estimator**: the faithful transcription in `reproduce.py` and the same with the division alone
  removed, that is exactly the two variants of `result-d-one-division.md`. Villa's search stays as it is:
  walk without bounds, update of the best inside the 3x3 loop, seed from the argmax of the
  unweighted sum. **Nothing is added**, because it is already measured that repairs of the search
  are of no use.
- **Generator**: seeded with `20260915 + z`, one seed only for the table. The spread between seeds
  is measured separately on three seeds and is reported outside the criterion, as already done on
  the four.
- **Metric**: `bench.errors()` of `umbilicus-bench`, the same as the paper's: for every control
  point inside the z coverage of the estimate, distance in the xy plane in millimetres.
- **Millimetres per voxel**: those of the system the reference is annotated in, scroll by scroll
  (9.362 um or 8.640 um or 2.399 / 2.400 um). Which one is written in the table, because a
  threshold in millimetres is worth a different number of voxels on different scrolls.
- **Baseline**: `bench.polylines(..., level=3, heights=24)['centroid']`, that is the centroid of
  the filled mask, on the bench's own heights, sampled on the common z range. It is the baseline
  declared in our paper, and its rule for heights is kept so as not to change the meaning of the
  column in secret.
- **PHercParis4, difference of provenance to be declared**: its normal grid comes from the
  predictor `surface-recto-2um-ps256-L0-th0.45`, while the other four of the primary block come
  from `m7-L*-th0.2`. Same scan, another predictor, and for that scroll no `normal-grids` of the
  `m7` family exists. The centroid of PHercParis4 is computed on the prediction `m7-L2-th0.2`,
  which is the family of the other baselines. **It goes written in the table beside the row**, not
  hidden in a note.
- **PHerc1218**: in the confirmation block the row uses Drobkov's file, like the other nine.
  Dopico's second reference does **not** enter that row: it serves the uncertainty measurement
  (pre-registered on its own on 2026-09-15 at 15:34) and is reported in addition as a marked
  alternative row.
  Together with the row goes the sentence of their own README, which in the band z 7500..9500 says
  to prefer Dopico's file to theirs.

## 5. Criteria, fixed now

The threshold stays **0.30 mm**, the same as this whole campaign, for the same reason: it is about
32 voxels at 9.362 um. On PHerc0332 and PHercParis4, at 2.4 um, it is about 125 voxels: the
threshold is physical, not in voxels, and is declared so.

### Primary block, five scrolls
- **P1, repair.** The variant without the division has a better median than the published one on
  **at least 4 scrolls out of 5**, and the count of estimates outside the volume goes to **zero on
  all 5**.
- **P2, beats the baseline.** The variant without the division has a better median than the
  centroid on **at least 3 scrolls out of 5**, with a margin **of at least 0.30 mm** on each of
  those three, and on none of the 5 is it worse **by more than twice** the median of the centroid.
- **P2 is lost** if the centroid beats it by more than 0.30 mm on at least 3 scrolls out of 5.
- In the other cases it is neither won nor lost, and it is written so.

### Confirmation block, ten scrolls
- **C1, repair.** Better median than the published variant on **at least 8 scrolls out of 10**, and
  estimates outside the volume at zero on all 10.
- **C2, beats the baseline.** Better median than the centroid on **at least 6 scrolls out of 10**,
  with a margin of at least 0.30 mm on each of those six, and never worse by more than twice on any
  of the 10.
- **C2 is lost** if the centroid beats it by more than 0.30 mm on at least 6 scrolls out of 10.

### Agreement between the blocks, defined now
The two blocks **agree** if P1 and C1 give the same verdict and P2 and C2 give the same verdict.
If they do not agree, **the disagreement is the result**: it takes a section of its own in the
article, with the simplest hypothesis written beside it (the most probable being the coarse
resolution of the third party annotation, one slice every ~480 and a click quantised to 8 voxels),
and without either block being removed, merged or reweighted.

## 6. What is done with the number for the uncertainty of the reference

The measurement on PHerc1218 arrives **after** these criteria are fixed, and **does not move
them**. Decided now, before knowing it:

- If the uncertainty measured between two independent annotations turns out to be **above
  0.30 mm**, the criteria stay those written here and in addition it is written that differences
  below that value are not interpretable, marking in the table the rows whose margin falls below
  it. The threshold is not rewritten, no row is redeclared won or lost.
- If it turns out to be **below 0.30 mm**, it is written that the threshold chosen was prudent and
  we go on.
- In no case is the uncertainty number used to remove a scroll from the table.

## 7. What is **not** done

- The two blocks are not mixed into a single median.
- A scroll is not chosen after seeing its number.
- The heights, the seed or the metric are not changed per scroll.
- The following stay out, for the reasons already written in section 4 of that same survey of the
  references: PHerc0139, the
  second umbilicus of PHercParis4 at 7.91 um, and the five of `Umbilicus_Maker`. They are excluded
  for lack of a published transformation between systems, not for their numbers, which we have not
  looked at.

## 8. Declared cost

Grids: eleven new scrolls times 24 slices. Ten are at 66..270 KB per slice, about 60 MB in all;
PHercParis4 is at 1.5..2.0 MB per slice, about 45 MB. Of these, the grids of PHerc0191, 0257,
0268, 0358, 0800, 0813, 1203 are already in `grid23/`, but on heights chosen for another purpose
(0.08..0.92 of the scroll) and therefore in general not reusable for this table.
Level 3 masks for the centroid: eleven scrolls, roughly 18 MB each in the bench's cache, about
200 MB. Computation: from the run on the twenty-three, about 50 s per scroll for the two variants
on the 24 slices, hence about 15 minutes plus PHercParis4, which has ten times the segments per
slice.
