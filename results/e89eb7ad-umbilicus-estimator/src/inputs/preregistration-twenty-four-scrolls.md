# Pre-registration: the correction on the twenty-three scrolls of the competition set

Written on 2026-09-15, **before** downloading a single grid of the nineteen scrolls with no
umbilicus.

## The distinction the experiment rests on

On **four** scrolls a hand annotated umbilicus exists (PHerc0125, 0211, 0332, 0826), and there the
**accuracy** is measured: distance from the truth, in millimetres. That measurement is already
there and it is the result.

On the other **nineteen** a reference does not exist. There the accuracy **cannot be measured** and
must not be insinuated in any form. What is measured is the **generalisation**, with properties
that have no need to know where the axis is.

Note: PHerc0332 is not among the twenty-three of the competition set (it is the only one of the
four annotated ones that is not), so the scrolls measured here are the twenty-three of the
competition set plus PHerc0332 as a reference, and the three annotated ones that are in the
competition set serve as an internal control.

## The five properties, and what counts as "it generalises"

All measured on 24 slices per scroll, `xy` plane, and on **two variants**: the function as it is
today and the same one with the division by `wsum` removed. Without the comparison the measurement
says nothing.

1. **The estimate stays inside the volume.** Criterion: the corrected version must keep **at least
   23 slices out of 24 inside the grid on every scroll**, and at least 99 % over the total.
2. **Stability with respect to the seed.** The function is not seeded. Three seeds per slice;
   criterion: the median spread between the three results must stay **below 1 % of the width of
   the grid** on every scroll.
3. **Continuity along z.** A true axis moves slowly as it rises. Criterion: the **median** jump
   between two consecutive sampled slices must stay **below 2 % of the width of the grid** on
   every scroll. The maximum is reported and does not enter the criterion, because the sampled
   slices are a twenty-fourth of the scroll apart from one another and an isolated jump can be
   true.
4. **An interior maximum exists.** Probe of the table of local maxima on one slice at mid height
   per scroll, fine lattice of 4 px in a window of 400 px around the estimate. Criterion: **at
   least 90 % of the scrolls** must have a maximum interior to the window.
5. **Distance from the centroid of the points of the grid.** **It is not a criterion** and it is
   not a measurement of accuracy, because the centroid is not the truth. It is reported, and every
   scroll where the median distance exceeds 10 % of the width of the grid is **flagged for
   inspection**.

**The correction generalises** if criteria 1, 2, 3 and 4 pass. If one of them fails, which one and
on how many scrolls is written down, and nothing is rounded.

## Why this is not a correction tuned on the four scrolls

It goes in the paper and I fix it here so that it does not become a justification built afterwards.
The division was not found by trying variants until the numbers improved. It was identified by an
argument about the **shape of the function**: a sum whose weights go as `1/D` vanishes at infinity,
so it has a maximum at a finite distance by construction; dividing by the sum of the weights gives
a mean, which tends to the plain mean of the `cos^2` and has no such guarantee. The argument would
have been valid without having looked at a single scroll. **Deduced, then verified.** The nineteen
scrolls with no reference are out of sample and serve to confirm it, not to find it.

## Declared cost
24 slices per scroll, about 200 KB per slice, so about 110 MB for the twenty-three. The disk has
699 GB free.
