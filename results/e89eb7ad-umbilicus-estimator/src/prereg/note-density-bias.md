# Post hoc pre-registration: density bias of the weighted sum (Goal A of the revision)

Written on 2026-09-16 at 10:54 UTC, **before** running `tools/synthetic_density.py` and before
measuring the density asymmetry on a single real slice. **It is post hoc with respect to the frozen
paper**: when it was written the following were already known, (a) the defeat of the corrected
version against the centroid on PHerc0826 (`evidence/fifteen.csv`, 4.42 against 3.40 mm), (b)
family D of the partial arcs of the battery (its synthetic sections table, measured that morning:
on a half circle the sum is wrong by 258 units, the mean by 0.4), (c) the objective bias table of
the same battery, measured that morning too, which on "D arcs 0.5" puts the maximum of the sum objective at 170 units from the true centre, and (d) the
referee's observation that the sum rewards the zones with many segments while the mean normalised
for the density. No number of this goal had been computed.

## What is measured

Synthetic sections 8000 x 8000 grid units, true centre at (4000, 4000), radii 300..3500 in steps
of 80, like family A of the battery:

1. circular, uniform density (ratio 1:1): it is the known reference, it must reproduce the curve of
   Fig. 2 of the frozen paper (sum with a maximum at finite distance, mean without);
2. elliptical, axis ratio 1.4;
3. sheet interrupted on one side: half circle (angular fraction 0.5), the case of family D;
4. asymmetric sampling density: the points of the half plane x > 4000 all kept, those of the half
   plane x < 4000 thinned to 1/2, 1/5, 1/10 (ratios 1:2, 1:5, 1:10).

For each: the maximum of the weighted sum field and of the weighted mean field on a lattice of step
4 in a window of 1200 units around the true centre, with the same 10000 samples that
`villa_estimator.sample` draws (seed 60000+s, 20 seeds), then the full estimate of the two variants
(villa's search as it is). Reported: distance of the maximum from the true centre, component along
x (positive towards the dense side), median and p90 over the 20 seeds. Grid units and millimetres
at 9.362 um.

## Prediction, written now

- **Sum, ratio 1:10**: the maximum of the field moves **towards the dense side** (x > 4000) by an
  amount between **50 and 250 units** (0.5..2.3 mm), monotone in the ratio (1:2 < 1:5 < 1:10).
- **Mean, ratio 1:10**: displacement **below 10 units**, because the normalisation takes the
  density out of the weight.
- **Ratio 1:1**: the sum stays within the 23 units already measured in that objective bias table,
  the
  mean within 1.
- **Half circle**: reproduces the order of magnitude of family D (sum beyond 150 units).

If the sum at 1:10 moves by less than 50 units, the prediction was wrong and the density bias does
not by itself explain the defeat on PHerc0826; it is written so.

## On the real data (point 4 of the goal)

On the 24 slices of `grid15/` of PHerc0125, 0211, 0332, 0826 and PHercParis4, the same as Table II,
the density asymmetry of the segments around the control point of the reference is measured: the
segments are counted in 8 angular sectors centred on the reference, and the asymmetry is the ratio
between the most populated sector and the least populated one (median over the 24 slices), plus the
vector "centroid of the segments minus reference" in millimetres. **The reference serves only as
the origin of the sectors**: no parameter is chosen by looking at it. Prediction: PHerc0826 has the
highest ratio of the five and the displacement vector of the corrected estimate with respect to the
reference points into the same half plane as the centroid of the segments.
