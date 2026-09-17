# Umbilicus annotations for ten of the thirteen First Letters prize scrolls

![All ten axes: hand-placed nodes on the side projection](panels/axis_polylines_all_ten.png)

> **Two of these ten scrolls do not fit the format.** On PHerc0268 two winding
> centres run side by side for thirteen annotated heights; on PHerc0800 three
> centres share six heights and the traced axis returns in height. Figures and
> measurements: [multicentre/](multicentre/).

*The ten shipped axes, 413 hand-placed nodes, on the XZ side projection. Re-rendered 2026-08-20 on the curves this repository ships.*

Manual umbilicus (winding-axis) polylines for ten of the thirteen First
Letters prize scrolls: PHerc 0191, 0257, 0268, 0358, 0800, 0813, 1203, 1218,
1447, 1545. The other three the prize page lists — PHerc 0125, 0211, 0826 —
already had published umbilici from sean, which §3 uses as the calibration
reference. (The count is the prize page's own, re-read 2026-08-20: "Eligible
scroll volumes (13)". An earlier version of this line said "the ten First
Letters prize scrolls", contradicting the thirteen this README itself counts
below.)
**Nine of them had no umbilicus. One did:** Iyán Dopico
([@IyanDopico](https://github.com/IyanDopico)) published one for **PHerc1218**
in [vesuvius-sheet-tools](https://github.com/IyanDopico/vesuvius-sheet-tools)
on 2026-07-21, three weeks before ours. What that file is, and how our axis
compares against it, is §7 — and it is the only external check in this package.
As of 2026-08-20 that check no longer reads as a pass: third-party winding
observations, made by neither annotator for this purpose, arbitrate the
z 7500–9500 band against our axis, which is off by up to about 7 mm there
(§7.6). Over that band, prefer his file to ours.

File format matches sean's published umbilicus files (integer voxel
coordinates, per-point `score`, `metadata` block), plus the five frame keys of
the open PR ScrollPrize/villa#1454 (§8). Coordinates are level-0 voxels of each
scroll's masked prize volume — 9.362 µm for six scrolls and **8.640 µm for
PHerc 0268, 0800, 1218, 1447** — and every file now carries that voxel size and
its grid dimensions as machine-readable metadata, verified against the bucket by
`scripts/stamp_frame.py`. The full bucket path stays in
`metadata.source_volume`.

Note on PHerc1203, and the same trap on every scroll the prize page lists. The
visible label there for PHerc1203 is `20250720004030-9.362um-1.2m-113keV`, and
**no such key exists in the bucket**: the only 9.362 µm derivation of PHerc1203
is `20250820131727-9.362um-1.2m-113keV-masked`, which is what that same link
actually resolves to and what all our coordinates refer to. This is not a typo
in one row. On all thirteen scrolls listed on <https://scrollprize.org/prizes>
the visible id differs from the id its own link resolves to: the visible one is
the ESRF **scan-session** id, the bucket path carries the **reconstruction** id.
The rule reproduces — for each of our ten, the visible label equals that
volume's own `metadata.json` acquisition timestamp
(`scan.tomo.acquisition.date`) converted to UTC, to the second. Iyán Dopico
documented the same thing for PHerc1218 in his pack's `README.txt` in July; we
checked it independently on all ten (`scripts/stamp_frame.py --check` reads that
metadata). Cite the bucket id, not the label.

## Motivation

We are working on the First Letters prize scrolls, and kept running into the
same missing input: every winding-number assignment, every polar unwrap and
every spiral fit we tried takes a centre per z-slice, and nine of these ten had
none. Three other scrolls have a published umbilicus (sean's PHerc0125, 0211,
0826), and one of the prize ten — PHerc1218 — had one from Iyán Dopico three
weeks before ours. The other nine had nothing.

**That correction matters enough to say plainly.** Until 2026-08-15 this README
was titled "the 10 remaining First Letters scrolls" and said the ten "did not
have one yet". That was wrong about PHerc1218, and it had been wrong since the
first commit: `data/spiral_input_pherc1218/umbilicus.json` has been public in
[IyanDopico/vesuvius-sheet-tools](https://github.com/IyanDopico/vesuvius-sheet-tools)
since commit `6a831e0` on 2026-07-21. We did not find it before publishing; we
found it before publishing was final, and the claim is withdrawn rather than
softened. The credit is his. What replaces the claim is worth more than it was:
PHerc1218 is now the one place in this package where our annotation is measured
against someone else's, and that is §7. Being measured is not the same as
passing: since 2026-08-20 the measurement goes against us over one band of that
scroll — §7.6 — and this README no longer presents §7 as a check we passed.

What we kept running into is that substituting a straight vertical line for the
axis is not a small approximation. On the ten shipped files the annotated centre
departs from a vertical line through the scroll's own mean centre by up to
**19.8 mm** (PHerc0813; then PHerc0268 at 19.3 and PHerc0800 at 18.4), and on
PHerc0268 the axis sweeps **36.7 mm** laterally over the height of the scroll. At the 247–371 µm
pitch we measure at five readable spots (see caveats — those spots are locally
separated, and tightly-wound material is finer, which would make this count
larger not smaller), 19.8 mm of lateral error crosses
roughly 53 to 80 windings — far more than enough to assign a sheet to the wrong
turn at the top or bottom of a scroll. Placing the vertical optimally
instead of through the mean centre does not rescue it: the best a straight stick
can do on PHerc0268 is still 18.4 mm (`scripts/axis_stats.py`, `cheby_mm`).

So we annotated the ten by hand, in the same format sean published. We are
contributing them because a per-slice centre is an input that several tools in
this project take and that did not exist for these ten scrolls. All numbers
below are measured on real scroll data; no part of this validation uses
synthetic data or injected defects.

Downstream consumer, run rather than assumed: villa's spiral loader
`scripts/spiral/umbilicus.py` (`json_umbilicus_z_to_yx`) was run against all ten
of these files and sean's three. All thirteen parse and return a working
z → (y, x) interpolator. See "Format compatibility" below.

Parsing is not benefit, so that loader was then used to ask whether the axis buys
the tool anything: on a rule fixed in writing beforehand, over 300 cross-sections
of all ten scrolls, the annotated axis beats the best straight vertical stick on
10 of 10 scrolls, p = 0.0020, 2.11× — and the measure that says so is blind below
3.63 mm (a finer pre-registered ladder puts the end of the blind zone below
about 2.7 mm; §6.4's dated notes say why that ladder's exact rung moves too
easily to quote, and 3.63 mm stays the headline until the finer run is
reproduced by someone else), so it credits gross placement and not annotation precision. That
is validation check 6, and its figure failed.

## Method
Manual annotation on 32 to 64 axial slices per scroll after the second and
third passes (31 or fewer before the second; small web annotator with
auto-suggested centers, triplanar side views and winding-ring overlays;
khartes `exp-2025-08-01` used to cross-check ambiguous spots). Untouched
auto-suggestions were dropped at finalization — polylines interpolate
between human-confirmed points only. **The rule that implements this is a
2-voxel threshold** (`scripts/finalize.py --tol`, default 2.0): a point counts
as human-confirmed if it sits ≥2 voxels from the auto-suggestion it started
from. Two voxels at L3 is a quarter of a pixel, so we name the three published
points that sit within 10 voxels of their auto-suggestion — PHerc1447 z=11888
(3.3 vox), PHerc0257 z=15272 (6.6 vox), PHerc0813 z=3496 (9.9 vox). These are
deliberate micro-adjustments, but they are not distinguishable from a slipped
click, so we would rather list them. **That list is the first pass's**
(`scripts/finalize.py` needs the annotator output, which does not ship, so it
cannot be recomputed from a clone); of the three, PHerc0813 z=3496 was
re-placed in the second pass and now sits 808 voxels from where it was, so the
entry describes a point that no longer exists at that position.

### Second pass, 19 August 2026 — density where the axis bends

Paul (pmh47) pointed out that ~30 slices is thin where the umbilicus xy moves
quickly with z, and suggested looking at slices halfway between control points.
We measured that before drawing anything: `scripts/midpoint_audit.py` drops each
interior control point, interpolates its neighbours at that z and reports the
miss in micrometres — a leave-one-out measurement of how wrong linear
interpolation is, with no CT read and no model involved. It put 161 of 269
intervals above 280 µm and 27 above 1 mm. Run again on the 19 August densified
curves it reported **188 of 383 intervals above 280 µm and 2 above 1 mm** — more
intervals over 280 µm because there are more intervals, and an order of
magnitude fewer of the bad ones. (On the shipped curves, after the third pass
on PHerc0191 — §10 — the same script returns **194 of 403 above 280 µm, still
2 above 1 mm**.)

Midpoint slices were then fetched for the worst intervals and annotated by the
same hand as the first pass.
**279<!--ledger:umb.rp.points_15aug--> →
393<!--ledger:umb.rp.points_19aug--> human-confirmed points.** (The
third pass of 20 August then took PHerc0191 from 44 to
64<!--ledger:umb.rp.points_max--> and the shipped
total to 413<!--ledger:umb.rp.total_points--> — §10.) The largest
estimated midpoint miss per scroll, before and after, in micrometres:

| scroll | before | after | | scroll | before | after |
|---|---:|---:|---|---|---:|---:|
| PHerc0191 | 1931 | 892 | | PHerc0813 | 1755 | 417 |
| PHerc0257 | 1706 | 775 | | PHerc1203 | 673 | 443 |
| PHerc0268 | 1901 | 1064 | | PHerc1218 | 1014 | 736 |
| PHerc0358 | 1196 | 516 | | PHerc1447 | 1209 | 492 |
| PHerc0800 | 1893 | 820 | | PHerc1545 | 1524 | 550 |

PHerc0191's "after" above is the second pass's 892 µm. The third pass (§10)
reshaped its intervals again: today's audit puts its median estimated miss at
354 µm (438 before that pass) and its worst at 991 µm — a *different* interval,
z 13088–13560, which the denser grid exposed exactly the way the next paragraph
describes.

PHerc1203 is the instructive one. Its existing points did not move in this pass,
yet the denser grid pushed its worst interval from 673 µm to 1462 µm: the
density had exposed a bend the sparse polyline was too coarse to see. A further
pass on that stretch brought it to 443 µm, and the same sequence played out on
PHerc0813 (930 → 417 µm). Where a scroll got *worse* on this measure, the
annotation had not degraded — the measurement had got sharper.

### 19 August 2026 — the pre-registered run repeated on these curves, and what it says

An earlier version of this section said the axis-benefit run of §6 had not been
re-run on the densified curves. It has been, and this README now quotes the
repeated run throughout. Three things, and the third is the one that matters.

**1. The pre-registered claim holds.** `scripts/axis_benefit.py` on the new
per-slice outputs prints, for the primary comparison and for the secondary one,
*"verdict under PREREGISTRATION.md 10.2: CLAIM SUPPORTED"* — 10 of 10 scrolls
positive, W = 0.0, p = 0.0020, exactly as before. The old per-slice outputs are
not deleted: they ship as `axis_benefit/superseded_2026-08-15/`, so the two runs
can be compared by anyone who wants to check what follows.

**2. The slice rule was re-derived where the annotated range grew.** The
pre-registered sampling rule reads `z_min` and `z_max` off the first and last
control point of each shipped file. On PHerc0268 and PHerc0800 the second pass
extended the annotated range — PHerc0268's `z_min` from 5320 to 2680, and
PHerc0800's from 4256 to 3672 with its `z_max` from 20760 to 21352 — so the rule
gives different z on those two, and those two scrolls were re-measured on the z
the rule now gives.
`axis_benefit/measure/scroll_meta.json` carries the new range and
`scripts/axis_benefit.py` re-derives all 300 indices and reports *"all ten: the
run used exactly the slices the rule gives"*. The consequence is stated rather
than buried: on those two scrolls the two runs share **2 and 0** of their thirty
slices respectively, so nothing about PHerc0268 or PHerc0800 pairs across the
two runs.

**3. The densification did not measurably improve the axis on this instrument.**
This is the honest headline of the repeat and it is not the one we wanted.
Pairing every slice that is scorable in both runs — 198 of them, over the eight
scrolls whose z are unchanged plus the two PHerc0268 slices that survive —

- the annotated axis **did not move at all** on 112 of the 198, and moved less
  than even the optimistic 1.81 mm floor on 148 of them;
- q on the annotated axis is a coin flip: 60 up, 64 down, 74 exactly tied,
  Wilcoxon p = 0.93;
- the gap over the straight stick moves +0.0044 on average, Wilcoxon p = 0.17;
- restricted to the 50 slices where the axis moved at least 1.81 mm, 28 are
  better and 22 worse, and the mean change in the gap is **negative**
  (−0.0063); at the 3.63 mm floor §6.4 now measures it is 18 better against
  20 worse (at the 2.72 mm floor of §6.4's 20 August finer ladder, 23 better
  against 20 worse, mean change still negative);
- at the scroll level, the change in each scroll's mean gap is positive on 5 of
  10, Wilcoxon **p = 1.00** (on the eight scrolls that pair slice for slice,
  5 of 8, p = 0.84).

**And the pooled ratio's rise is the baseline degrading, not our axis
improving.** Pooled it went 2.03× → 2.09×. On the 197 slices that pair across
the eight unchanged scrolls, the annotated axis's mean q fell by 0.0003 while
the straight stick's fell by 0.0045: densification moved the mean of the control
points, which is where the stick stands, so the comparator got worse faster than
we did. A wider ratio earned that way is not evidence of a better axis and we do
not present it as one.

**What that does and does not mean.** It does not mean the second pass was
worthless. The pass operated at a scale — median movement 0.000 mm, three
quarters of the slices under the floor — that this instrument is blind to by its
own §6.4 measurement, so the null is a statement about the instrument as much as
about the annotation. It does mean that this package has **no measurement that
shows the densification helped**, and it should not be sold as if it had one.
The measure that would show it must resolve sub-millimetre axis error, and there
is no such measure here.

> **Dated, 2026-08-20 — an external source found the errors, and q preferred
> the wrong centre.** The paragraph above says this package has no measurement
> that shows densification helped, and that at and above the floor q's
> per-slice verdicts are close to a coin flip. A test run this evening
> sharpens that into something worse, and it is recorded here rather than left
> for a reviewer to find.
>
> Iyán Dopico's public pack (1,863 same-winding arcs and 12,924 relative-winding
> chains for PHerc1218, machine-derived from stitched instance labels and from
> no umbilicus at all) identifies axis errors independently of us. Correcting
> PHerc1218 from the arcs alone, and judging with the held-out chains, drops the
> sign-violation rate from 4.98 % to 2.18 % overall and from 7.8 % to 2.4 %
> across the corrected bands. On the 18 nodes the correction moved,
> 72 %<!--ledger:floorx.d1218.below_floor_pct.shipped_200px--> lie below the
> 3.456 mm<!--ledger:floorx.d1218.floor_mm.shipped_200px--> floor on that
> scroll — invisible to q by construction, exactly as §6.4 says.
>
> **5<!--ledger:floorx.d1218.dq_above_n--> lie above the floor**, and there q
> was supposed to speak. Scoring the paired quantity the floor is defined on —
> q(corrected centre) − q(shipped centre), same slice, same annulus, same frozen
> measure — it reaches the 0.01 criterion on only
> 2<!--ledger:floorx.d1218.dq_above_n_reach--> of the five. On the other
> 3<!--ledger:floorx.d1218.dq_above_n_neg--> **q prefers the centre the external
> data refutes**: delta_q reads
> -0.0810<!--ledger:floorx.d1218.dq_z7184-->,
> -0.0996<!--ledger:floorx.d1218.dq_z8208--> and
> -0.0916<!--ledger:floorx.d1218.dq_z9232--> — wrong sign, and roughly eight
> times the criterion in magnitude. Across all 18 nodes,
> 14<!--ledger:floorx.d1218.dq_n_neg_total--> of the deltas are negative.
>
> **What this changes.** §6.4's floor stands: it is a population median from a
> displacement experiment, and this does not touch it. What does not stand is
> any reading of q as a per-slice arbiter between two nearby axes — above the
> floor as well as below it. **A slice that passes q is not thereby certified.**
> The validated use of q in this package is the population-level, pre-registered
> comparison it was built for, and nothing in it licenses "q agrees, so the
> centre is right".
>
> **The obvious objection, tested.** Both centres are scored on a *common*
> annulus, which must shrink as they separate — so a sceptic's first move is
> "you measured a construction that punishes movement, not a preference". If
> that were the mechanism, delta_q would fall as the correction grows. It does
> not: Spearman(correction, delta_q) =
> -0.189<!--ledger:floorx.d1218.dq_rho_move--> over the 18 nodes, and **the
> single largest correction of all, 8.07 mm, yields a positive delta_q**
> (+0.0443<!--ledger:floorx.d1218.dq_z8720-->) on the smallest annulus in the
> set. Shrinkage is real but is not what sets the sign. At n = 18 a small
> contribution cannot be excluded, only a dominant one. `_floorcheck/dq_artefact_check.py`
>
> **Does this undermine this package's headline?** The headline compares the
> annotated axis against a straight stick, and that comparison is literally what
> it says: an image-informed centre scores more concentric than an image-blind
> line, pooled over ten scrolls, pre-registered. Nothing above touches it. What
> the result does forbid is a *second* reading that is easy to slide into — "q
> prefers our axis, therefore our axis is right". If a hand annotator and q read
> the same visible structure, q agreeing with the hand is not independent
> evidence about the hand, and on the PHerc1218 bands above it is demonstrably
> not: there q prefers a centre that external data refutes. Beating an
> image-blind baseline and being correct are different claims, and only the
> first is measured here.
>
> One caveat kept deliberately: this is one scroll, 18 nodes, one external pack,
> and the alternative "q is right and the correction is wrong" was weighed
> rather than waved away — the chains, the arcs' independent convergence to
> Dopico's line, and the eye on slices z 8700 / 8928 / 9540 would all have to be
> wrong together. A mechanism is offered as a hypothesis only: a hand annotator
> and q read the same visible laminar structure, so q is not an independent
> check of the hand, and the two can be wrong in company. Working notes and
> per-slice numbers: `FIX_1218_2026-08-20.md`, `_floorcheck/delta_q.py`.


> **Dated, 2026-08-20 — the third pass moved one side of this comparison.**
> The numbers above pair the 15 August run against the 19 August run, and they
> are kept as measured. Later on 20 August PHerc0191 was re-annotated again
> (44 → 64 points, §10) and `axis_benefit/prereg_PHerc0191.json` was replaced
> by the run on that curve, so the by-hand join described in "What is
> scripted" now pairs the 15 August archive against a file that is no longer
> the 19 August one (which remains in git history at the parent of the commit
> carrying this note). Re-run on what ships today the join gives: 198 paired
> slices, 110 unmoved, q up on 65 / down on 62 / tied on 71 (Wilcoxon
> p = 0.52), the gap over the stick +0.0058 on average (p = 0.12), and 29
> better against 22 worse among the 51 slices that moved past 1.81 mm (19
> against 19 past 3.63 mm, mean change still negative). The conclusion this
> section states — no measurable improvement from densification on this
> instrument — is unchanged. Pooled, the ratio is now 2.11×, and unlike the
> 15 → 19 August step, the 19 → 20 August step is mostly the annotated axis
> improving on PHerc0191 (mean q +0.1386 → +0.1448) rather than the stick
> degrading (+0.0955 → +0.0924); §10 measured that improvement before
> shipping and quotes it as leaning positive, not significant (p = 0.084).

## Validation

Seven checks, and they are not equally reproducible. To be exact:

- **Check 7 (the one external check) reproduces from a fresh clone.** It is the
  only check in this package that compares our annotation against somebody
  else's annotation of the same scroll, and the only one whose other side we did
  not make. It was pre-registered: `qc/PRIOR1218_PREREGISTRATION.md` was written
  and hashed before `scripts/prior_1218.py` first ran, and its sha256 is quoted
  in §7.2. Both polylines ship, so the distances recompute with numpy alone; the
  post-hoc CT measurement inside it needs the network to *re-*measure but ships
  its raw. It covers one scroll of ten, and §7.5 says so. **Dated 2026-08-20:
  it is also no longer a check we pass.** Third-party arc and chain
  observations, independent of both axes, arbitrate the z 7500–9500 band
  against our file — §7.6. The distance comparison still reproduces from a
  clone; the arbitration itself runs in a working tree that does not ship here
  yet, and §7.6 and the "What is scripted" table say so.
- **Check 6 (does the axis help a tool?) reproduces from a fresh clone**, from
  the ten `axis_benefit/prereg_PHercNNNN.json` via `scripts/axis_benefit.py`.
  It was re-measured on the 19 August densified curves and the previous run
  ships beside it as `axis_benefit/superseded_2026-08-15/`, so the two are
  comparable from a clone as well. It
  is the only check here that asks whether these files benefit anything rather
  than what they look like, and it is the only one that was pre-registered — the
  specification ships as `axis_benefit/PREREGISTRATION.md`. The measurement that
  produced those per-slice files does not run from a clone: it streams 5.7 GB out
  of the public volumes and imports villa's spiral code. §6.9 says so exactly.
- **Check 2 (the shifted-axis control) reproduces from a fresh clone.** Its raw
  per-slice measurements ship as `qc/validation_raw.json`, and
  `scripts/count_wins.py` recomputes every count, rate, median and p-value
  quoted in §2 from that file with nothing but python, numpy and scipy. So does
  `scripts/snapshot_recheck.py`, which sizes the one snapshot caveat this
  package carries by re-measuring the same control on the final files.
- **Check 5 (the straight-stick control) reproduces from a fresh clone**, from
  `qc/stick_control_raw.json` via `scripts/stick_control.py`.
- **Every geometry number about our own ten axes** (deviations, sweep, kink with
  the z-spacing each value was measured at, largest gap and its endpoints, and
  now also the tissue-band coverage and the bare edges, since the ten
  `PHercNNNN/meta.json` ship) reproduces from a fresh clone via
  `scripts/axis_stats.py`. One exception, marked in the table below: **sean's
  three rows of the smoothness table** come from his three published files,
  which are not ours to redistribute. Their values, and the sha256 of the file
  each was computed from, ship in `qc/sean_reference.json`, so the rows print
  and are tied to specific bytes; supply the files and the script recomputes
  them and reports whether the two agree.
- **Check 1 (the winding-order test): the statistic now reproduces from a fresh
  clone**, from the shipped `qc/order_fixture_PHercNNNN.npz` via
  `scripts/order_stat.py`. The tracing that produced those fixtures does not —
  that code is not in this repository, and the table below says exactly what
  shipping it would take and what it would weigh. Every number in this check,
  and where it came from, is tabulated in `STEP2_CONSISTENCY.md` §13.
- **Check 3 (calibration against sean)** needs the annotation tree — the
  per-slice PNGs — and sean's three files. Script ships.
- **Check 4** has no script at all and never did. It is marked below.

The table under "What is scripted" repeats this per number. There is no blanket
claim, and the previous heading — "scripts included for every number except one,
marked" — was not true.

### 1. Winding-order test, swap-controlled (the practical one)

> **Dated, 2026-08-19.** The fixtures behind every number in this section —
> `qc/order_fixture_PHercNNNN.npz` — hold the **15 August** axes and were not
> rebuilt for the 19 August densification: rebuilding needs the tracer, which
> does not ship. The gap is not hypothetical. Nine PHerc0191 points and four
> PHerc0358 points were re-placed in the second pass (PHerc1203: none), and
> the third pass re-placed and added more on PHerc0191 (§10). At
> z = 15480 — the exact middle height of this section's PHerc0191 stack — the
> fixture's manual centre and the shipped file now disagree by **12.6 mm**
> (fixture (3491, 5338) at level 0 against the shipped (4380, 4322); on the
> 19 August file it was 12.3 mm against (4803, 5240); re-checked 2026-08-20
> after the third pass), which is comparable to the 13.30 mm median separation from the
> auto-centroid that this section credits the manual axis with beating on that
> scroll. Read every "manual axis" number below as the first-pass axes, not the
> files that ship.

Arcs of papyrus are traced around a fixed neutral centre (independent of either
axis under test), matched across slices geometrically, and the pairwise winding
ORDER implied by each axis is compared between neighbouring heights. On the
shipped tracing pipeline, with neutral tracing:

| scroll | manual axis | auto-centroid | shared pairs | kept only by manual : only by auto |
|---|---|---|---|---|
| PHerc0191 | 0.919 (354/385) | 0.826 (318/385) | 385 | 43 : 7 |
| PHerc0358 | 0.900 (206/229) | 0.738 (169/229) | 229 | 42 : 5 |
| PHerc1203 | 0.850 (226/266) | 0.782 (208/266) | 266 | 21 : 3 |

The pair sample is strictly identical for the two axes — same denominator in
every row — so the last column is a paired count: pairs whose order the manual
axis preserves and the centroid does not, against pairs where it is the other
way round. So 85–92% against 74–83%, and in paired counts the centroid loses
order **6.1–8.4×** more often. (The earlier text said "3–8×". That was wrong:
43/7, 42/5 and 21/3 are 6.1, 8.4 and 7.0. The 3.8 came from a different run —
the circle-replacement control, counts 19:5 on PHerc1203 — which that sentence
did not mention.)

**What this does not show, and it belongs here rather than in a caveats
section: none of that advantage comes from the axis being per-slice.** Freeze
the manual axis at a single constant point — the mean of its own 25 centres
over the stack, no per-slice variation whatsoever — and score it against the
live per-slice axis and the auto-centroid on one common pair sample (a pair
enters only if all three candidates return a defined sign on at least three
common heights, which trims 385/229/266 to 358/223/260):

| scroll | per-slice manual axis | manual axis **frozen at its stack mean** | auto-centroid | pairs |
|---|---|---|---|---|
| PHerc0191 | 0.919 (329) | **0.919 (329)** | 0.821 (294) | 358 |
| PHerc0358 | 0.897 (200) | **0.897 (200)** | 0.744 (166) | 223 |
| PHerc1203 | 0.850 (221) | **0.850 (221)** | 0.788 (205) | 260 |

**Net gain from tracking the core slice by slice: +0.000 on all three — the same
integer counts, not merely the same rounded rate.** This is now both scripted and
drawn: `scripts/stat_figures.py frozen` recomputes the table above from the
shipped fixtures and draws `panels/frozen_axis.png`, which puts the three
candidates beside the distances that explain them. Or reproduce it yourself from
the fixture in about twenty lines: load `qc/order_fixture_PHercNNNN.npz`,
replace `man_c` with `man_c.mean(axis=0)` broadcast over the 25 heights, and
score all three candidates with `order_stat.radial_sign` unchanged, keeping
only pairs on which all three return a sign on ≥3 common heights. Take the
common sample seriously: if instead you just substitute the frozen axis into
`order_stat.py` and let it pick its own denominator as usual, you get
0.921 (361/392) / 0.900 (208/231) / 0.866 (251/290) — the frozen axis scoring
*above* the live one, on a sample it partly selected. Same conclusion, weaker
evidence; the identical-counts version above is the one to quote.

This is what §9 of `STEP2_CONSISTENCY.md` predicts, and we should have said so
here. §9 measures the metric's detection threshold at 3–6 mm depending on the
window; the manual axis's excursion from its own stack mean is median
1.8 / 1.5 / 3.1 mm with a maximum of 4.1 / 3.3 / 5.1 mm, over stacks spanning
18.0 / 13.9 / 19.3 mm. The whole motion we are asking the metric to see sits at
or under its resolution. The metric is not literally blind to the freeze —
20.1% / 15.3% / 24.3% of individual (pair, height) sign decisions change status
when the axis is frozen, mostly by moving in or out of evaluability, and among
decisions both versions do resolve they disagree on 0.3% / 0.2% / 0.7% — but
the changes cancel to nothing in aggregate.

So read this section as measuring **where the centre sits, not how it moves**.
The two distances make the point on their own, both computed from the same
fixture: the median separation between the manual axis and the auto-centroid is
13.30 / 13.44 / 6.75 mm, comfortably above the 3–6 mm the metric can resolve,
while the manual axis's own per-slice excursion is 1.8 / 1.5 / 3.1 mm, at or
below it. The metric sees the gap between the two axes and cannot see the
motion of either. (Jitter is not the explanation either. The auto-centroid does
move more between adjacent heights on two of the three — median step 18.1 and
11.3 L3 px against the manual axis's 5.8 and 4.7 on PHerc0191 and PHerc0358 —
but on PHerc1203 it moves *less*, 5.3 against 7.1, and still loses by 0.062.
§9 of `STEP2_CONSISTENCY.md` reaches the same conclusion by a different route,
comparing the centroid against a rigid shift of equal size.) This section
therefore lands on the same limit section 5 reaches from the other direction,
and section 5 already states it plainly: *"We do **not** claim that this is
because the axis follows the scroll's curvature."* Nothing here demonstrates a
benefit from
per-slice tracking on these three stacks, and the panels' title — *"does the
axis keep the order of the turns BETWEEN slices"* — should not be read as
saying otherwise. What per-slice annotation is for is the scrolls and zones
where the core wanders further than 3 mm; that case is not made by this test.

**Swap control.** The same test re-run with the tracing itself done around the
manual axis, and again around the auto-centroid, gives nine cells. Counted
exactly: the manual axis is ahead in **six**, exactly level in **two** — both
scrolls traced around the auto-centre, PHerc0191 at 221/238 for each axis and
PHerc1203 at 223/269 for each — and **behind in one**. The one it is behind on
is PHerc0358 traced around the auto-centre, where the auto-centre keeps 131 of
143 pairs (0.916) against the manual axis's 130 (0.909). Our working document
calls that a tie and we think that is fair, but a reviewer is entitled to call
it a loss, so we print it rather than writing "never reverses", which is what
the earlier README said.

Strict absolute winding numbering is unresolvable at L3 preview resolution for
**either** axis. Under neutral tracing only 8–20 arcs per stack are even
evaluable, and of those 0–12.5% keep the same absolute number under the manual
axis against 0–22.2% under the auto-centroid. Neither axis is consistently
ahead, the counts are too small to say anything, and the metric is simply not
usable at this resolution. Stated honestly; we make no claim there. See
`panels/step2_*`, and `panels/order_map_*` / `panels/order_bump_*` for the same
three stacks drawn two other ways.

**Two caveats we found ourselves and would rather state than have you discover:**

(a) What is matched across heights are *traced papyrus arcs*, not verified single
sheets — beyond the core our chaining can hop between neighbouring laminae, so
read the numbers as arc order, not sheet identity. We retracted the "physical
sheets" wording ourselves on 2026-08-10 and the shipped panels now say arcs.

(b) The *size* of the gap is tracing-pipeline dependent, and under an
alternative, stricter first-order chainer the sign is not stable. Swept across
that chainer's chaining tolerance — its module default is
`tol = clip(0.30·gap, 0.6, 1.2)`, hard-coded in the module. A cell is the manual
axis's preserved-pair rate minus the auto-centroid's on an identical pair
sample; the parenthesised number is that shared pair count.

| chaining tolerance | PHerc0191 | PHerc0358 | PHerc1203 |
|---|---|---|---|
| **0.30·gap, cap 1.2 (module default)** | +0.000 (12 pairs) | **−0.024 (42)** | +0.125 (32) |
| 0.40, cap 1.5 | **−0.031 (32)** | **−0.049 (41)** | +0.054 (93) |
| 0.50, cap 1.8 | +0.000 (61) | **−0.013 (77)** | +0.017 (113) |
| 0.65, cap 2.4 | +0.042 (95) | +0.012 (169) | +0.045 (111) |
| 0.80, cap 3.0 | +0.000 (95) | +0.052 (114) | +0.054 (55) |
| 1.00, cap 4.0 | +0.000 (54) | +0.014 (69) | +0.086 (35) |
| shipped pipeline (zero order) | +0.093 (385) | +0.162 (229) | +0.068 (266) |

**On PHerc0358, at the module's own default tolerance, the manual axis loses**
(−0.024 on 42 pairs), and it loses again at the next two tolerances (−0.049 and
−0.013); it only turns positive at 0.65 and looser, and never approaches the
shipped pipeline's +0.162. On PHerc0191 it loses at 0.40/1.5 (−0.031), is
exactly zero at four of the six tolerances and reaches at most +0.042. Only on
PHerc1203 does the gap survive every tolerance we tried (+0.017…+0.125). The
earlier README said this "is not reproduced on 0191/0358 at any chaining
tolerance", which reads as *vanishes*; what it actually does on 0358 is
**reverse**, and we would rather say so.

We tested whether the PHerc0358 reversal is a small-sample artifact and it is
not. Random 42-pair subsamples of the shipped 229-pair run (4000 draws without
replacement) give an expected gap of **+0.163, 95% band +0.048…+0.286**;
**−0.024 was observed, p < 0.001.** Our own resampling test says the
disagreement is real, not noise. We do not yet understand why, and we publish it.

Because of this we do not claim "the manual axis never loses". The claim we do
make, stated mechanically rather than with the undefined word "reliable" the
earlier text used — and "reliable" was undefined, there is no minimum pair
count or threshold behind it anywhere in our own evidence:

> **On the shipped zero-order pipeline, splitting its pairs by lamella-following
> retention at k = 1, 2 and 3 (`gate_by_ridge`: a continuous run of ≥30 samples
> where the arc's tangent agrees with the structure-tensor lamella direction to
> within 22° at coherence ≥0.25, both tracks passing on ≥k common slices) and by
> radius belt from the tracing centre, the manual axis's advantage is
> non-negative in every cell.**

It is *positive* in all but one: on PHerc1203's outermost radius belt (r > 140 px
at L3, 14 pairs) it is exactly +0.000. Two further cells carry too few pairs to
report at all — PHerc0191's innermost retained subset has none, PHerc0358's
outermost belt has four — and we are not counting those in our favour. It is
largest where the arcs provably
follow a lamella — +0.154 on 39 pairs of PHerc0358 at k ≥ 3, +0.238 on 21 pairs
of PHerc1203 at k ≥ 3, and +0.294 on the 17 lamella-retained pairs inside
PHerc1203's innermost belt (r 0–60 px). **Those subset numbers belong to the
shipped pipeline**, not to the first-order chainer; the earlier text attributed
the +0.29 to the first-order chainer, which was wrong.

Full tables, the resampling test, the null control and the provenance of every
number are in **`STEP2_CONSISTENCY.md` in this repository**. (The earlier README
cited a Russian working document that did not ship. That is fixed: the evidence
is now in the repo, in English, and it contains the results that argue against
us as well as the ones that do not.)

**The statistic itself is now recomputable — the tracer still is not.** This
used to be the one headline number a reader could not check at all. What ships
now is `qc/order_fixture_PHercNNNN.npz` (about 600 KB each): the tracer's
output for the three neutral-tracing stacks — the traced arcs, already matched
across heights into tracks, in L3 pixel coordinates, together with the two axes'
centres on each of the 25 heights of each stack. `scripts/order_stat.py` reads
those and recomputes, with numpy alone and no other input, every number in the
table above: 0.919 / 0.900 / 0.850 against 0.826 / 0.738 / 0.782, the shared
pair counts 385 / 229 / 266, and the paired cross-tabulation whose off-diagonal
is 43:7, 42:5 and 21:3.

Be clear about what that does and does not close. It closes the step from
"traced arcs on slices" to "85–92% against 74–83%" — the sign convention, the
pair selection, the requirement that both axes be scored on an identical sample,
the counting. It does **not** close the step from CT to traced arcs: the tracer
is still not in this repository, so a reader has to take the fixture as given.
What that would cost is stated in "What is scripted" below.

The fixtures were made by re-running the neutral stacks from scratch on
2026-08-13, and that re-run reproduced all nine published figures exactly, which
is itself the first independent re-execution of this pipeline since the numbers
were first written down.

### 2. Shifted-axis control across 297 annotated slices

A banded-energy measure is computed at each annotated centre and at the same
centre displaced by a fixed number of voxels in four directions; a ratio above 1
is a win for the annotated centre. Reproduce with
`scripts/validate_axes.py` then `scripts/count_wins.py`. Both displacements are
drawn side by side, on the same scale and in the same scroll order, in
`panels/shifted_axis_controls.png` (`scripts/stat_figures.py shifted`) — the one
that passed and the one that failed, because the pair is what licenses the
reading at the end of this section and neither alone does.

At **+300 voxels** (≈2.6–2.8 mm, depending on the scroll's voxel size) the
annotated centre wins **184/297** slices, 0.620.

- The **defensible statistic is the scroll-level sign test: 9 of 10 scrolls
  above 50%, one-sided p = 0.011.** We quote that one. The pooled slice-level
  binomial gives p = 2.3e-05, and that is what an earlier version of this README
  quoted, but it pseudoreplicates: within a scroll the slices sit ~480 voxels
  apart, share one linearly-interpolated axis and sample continuous tissue, so
  they are not 297 independent trials. The unit of replication is the scroll.
  p = 0.011 is roughly 500× weaker and it is the number that survives scrutiny.
- **The tenth scroll is on the wrong side.** PHerc0800 is 14/29 = 0.483, median
  ratio 0.970 — there the annotated axis loses to the deliberately displaced one
  more often than it wins. That is not underpower, it is the wrong sign, and we
  name it rather than folding it into "limited per-scroll power".
- Per-scroll, uncorrected: PHerc0191 22/31 p=0.015, PHerc0813 21/31 p=0.035,
  PHerc1203 21/31 p=0.035, PHerc1218 20/30 p=0.049, PHerc0358 20/31 p=0.075,
  PHerc1545 17/29, PHerc0257 18/31, PHerc1447 18/31, PHerc0268 13/23,
  PHerc0800 14/29. **These p-values are uncorrected for multiplicity. Under
  Bonferroni (α = 0.05/10 = 0.005) none of the ten survives.**
- **The tighter control failed and here it is.** The same script also runs a
  **+150-voxel** displacement (≈1.3–1.4 mm). There the test is null:
  **159/297 = 0.535, pooled p = 0.12**, scroll-level 7/10 above 50%, sign-test
  p = 0.17, and three scrolls are below 50% (PHerc0268 0.348, PHerc1447 0.419,
  PHerc1545 0.483). `count_wins.py` prints both magnitudes side by side, so
  anyone who runs it sees this. The honest reading: **this measure resolves
  gross displacement, not annotation-scale accuracy.** It is evidence that our
  axes are not ~3 mm wrong; it is not evidence about their precision.
- **The snapshot behind this control is now measured, not just disclosed.** The
  caveat at the bottom of this README says the control ran on a slightly older
  snapshot of the files. `scripts/snapshot_recheck.py` re-runs the whole of this
  section on the **final shipped files** and prints both results side by side;
  its raw output ships as `qc/validation_final_raw.json`, so the comparison
  reproduces from a bare clone. The drift is exactly three slices: 294 of the
  297 give a bit-identical measured value at the annotated centre, and the three
  that move are PHerc1545 z = 2544, 3088 and 3640 — precisely the three points
  the caveat names. The effect on the numbers: **+300 goes from 184/297 = 0.620
  to 182/297 = 0.613** (PHerc1545 alone, 17/29 → 15/29; every other scroll
  identical), pooled p from 2.3e-05 to 6.0e-05; **+150 goes from 159/297 to
  158/297**. **Both sign tests are unchanged — 9/10 with p = 0.011 at +300 and
  7/10 with p = 0.17 at +150** — so the statistic this README actually quotes
  does not depend on which snapshot is used. The published 184/297 is left as it
  is, because it is what the shipped `validate_axes.py` produced on the input it
  had; the newer number is shipped next to it rather than in place of it.

### 3. Calibration against sean's three published umbilici (0125/0211/0826)

Same ring-symmetry gates run on both sides, `scripts/calib_sean.py` (needs the
annotation tree for the slice PNGs; `UMBILICI_TREE`).

Median ring-gate displacement: **ours 268.3 voxels over all ten shipped axes
(279 points); sean's 273.6 over his three (75 points).** The gate is the same in
both cases and it does not separate us: it measures how crushed a cross-section
is, not how well it was annotated.

> **Dated, 2026-08-19.** Those 279 points are the 15 August curves. The shipped
> files now carry **393** points and this number has not been recomputed on
> them: `calib_sean.py` needs the per-slice PNGs and `ref_sean/`, neither of
> which ships, so it cannot run from a clone and did not run here. Read 268.3 as
> "measured on the ten 279-point axes of 15 August", and the same for
> `panels/calibration_summary.png`, which draws it.

> **Dated, 2026-08-20 — re-measured on the densified curves.** `calib_sean.py`
> was re-run on our side (it still cannot run from a clone) against the shipped
> 393-point axes. Median ring-gate displacement: **ours 279.9 voxels over 393
> points; sean's 273.6 over his 75, unchanged and reproducing exactly.** Two
> things to say plainly about that. First, the ordering of the two medians
> flips: on the 15 August curves ours was nominally lower (268.3 against
> 273.6), on the densified curves it is nominally higher (279.9 against
> 273.6). Nothing in this section ever rested on that ordering — the claim
> here has always been that the gate measures how crushed a cross-section is,
> not how well it was annotated, and that it does not separate us; both runs
> support exactly that reading, and a reader who wants to lean on the 5–6
> voxel difference in either direction should not. Second,
> `panels/calibration_summary.png` was re-rendered from this run on the same
> day, so the panel and this note describe the same measurement; the 268.3
> above stays as the 15 August value it is.

> **Dated, 2026-08-20, after the third pass.** `calib_sean.py` was re-run once
> more with PHerc0191 at 64 points (§10; 413 points in total). Median
> ring-gate displacement: **ours 279.9 voxels over 413 points; sean's 273.6
> over 75** — both medians unchanged at this precision, so the note above
> stands number for number, and `panels/calibration_summary.png` was re-drawn
> from this run. The third pass also moved PHerc0191's row of the smoothness
> table below: as published 166 → 147 (shorter chords again), and at matched
> spacing 252 → 327 over 28 triples — denser and, on the one column that
> compares like with like, rougher, the same trade the second pass showed on
> PHerc0268.

> **Correction.** An earlier version of this README said "ours 265 vs sean's 274".
> That 265 was three of our ten scrolls (PHerc0191/0257/0268, 93 points), read
> from the pre-finalization annotator output — 31-point polylines that still
> contained the untouched auto-suggestions this package says it drops. It also
> does not reproduce today (268.3). `calib_sean.py` now runs all ten scrolls
> against the shipped files, and 268.3 is what it printed on the 15 August
> files (279.9 on the densified ones — the dated note above). Sean's 273.6 → 274 is
> unchanged and reproduces exactly.

**Smoothness, and this one is not in our favour.** Kink = median distance of a
point from the chord between its z-neighbours. **Kink grows with the length of
the chord**, so no kink value means anything without the z-spacing it was
measured at, and every value below carries one (`scripts/axis_stats.py`; the
panel is `scripts/calib_figure.py`):

| scroll | whose | as published | at its median step | after thinning towards 480 | at its realized step | matched, 480 ± 20% only | triples |
|---|---|---|---|---|---|---|---|
| PHerc0211 | sean | 32 | 188 | 98 | 474 | **87** | 16 |
| PHerc0125 | sean | 39 | 212 | 61 | 465 | **51** | 16 |
| PHerc0826 | sean | 63 | 283 | 92 | 467 | **70** | 9 |
| PHerc0358 | ours | 78 | 368 | 176 | 376 | **251** | 3 |
| PHerc1447 | ours | 78 | 640 | 64 | 640 | – | 0 |
| PHerc1218 | ours | 84 | 608 | 78 | 608 | – | 0 |
| PHerc0813 | ours | 90 | 224 | 160 | 448 | **156** | 18 |
| PHerc1203 | ours | 99 | 512 | 106 | 520 | **103** | 22 |
| PHerc1545 | ours | 134 | 552 | 134 | 552 | **127** | 24 |
| PHerc0257 | ours | 154 | 472 | 177 | 480 | **177** | 28 |
| PHerc0800 | ours | 155 | 584 | 168 | 588 | – | 0 |
| PHerc0268 | ours | 165 | 168 | 328 | 496 | **544** | 9 |
| PHerc0191 | ours | 147 | 240 | 327 | 480 | **327** | 28 |

**The middle column is not a common-step comparison, and an earlier version of
this README wrongly said it was.** The thinning keeps, for each point of a
480-voxel target grid, the nearest point that already exists. That resamples a
*dense* polyline onto ~480 — it does exactly that for sean, whose three land at
465/474/467 — but it cannot manufacture a spacing a sparse polyline does not
have. Ours end up at 376 to 640, a 1.7× spread, and only two of the ten land on
480. So "thinned to a common 480-voxel z-step" was wrong about our own side, and
the sentence that called that column the fair one named the wrong column. The
error ran against us rather than for us — it made our roughest scroll look 1.8×
rougher than it is — but a fairness argument that points at the unfair column is
worth correcting either way.

The last column is the comparison that convention was meant to be: only those
triples whose **both** chords are within ±20% of 480 voxels, and no resampling
at all. **On that column sean is 51–87 and the seven of ours that can be
measured on it are 103–544** — our smoothest matched scroll is 1.2× his roughest
matched value and our roughest is 6.3×. The remaining three of our ten contain
no pair of adjacent chords near 480 anywhere and simply cannot be placed on that
axis; for those we quote the as-published figure with its spacing, and nothing
else.

**The second pass changed this table more than it changed anything else here,
and not uniformly in our favour.** Denser annotation means shorter chords, so
the as-published column falls across the board — our range was 86–264 on the
15 August curves and is 78–165 now — but that is the chord length talking, which
is exactly the trap this section exists to name, and it is not a claim that the
annotation got smoother. The matched column is the one to read, and there the
news is mixed: five scrolls that could be measured on it before still can, two
more (PHerc0358 and PHerc0268) now can, and **PHerc0268 lands at 544 — the
roughest matched value of all thirteen rows in this table, six times sean's
roughest.** PHerc0358's 251 rests on three triples and should not be leaned on.

**PHerc0268's 469 was an artifact of resampling and that withdrawal stands.**
On the 15 August curves its honest as-published figure was 261 over 328-voxel
chords and it had no matched-spacing value at all. The second pass took it from
23 points to 44, which brings its median spacing down to 168 and its
as-published kink to 165, and — for the first time — gives it nine triples at
matched spacing. That matched value is **544**, worse than the 469 the
resampling artifact had produced. The withdrawal was still right: 469 was
measured the wrong way. But nobody should read this section as PHerc0268 having
come out better, because on the one column that compares like with like it is
now the worst row on the page.

What does not change: **sean's axes are smoother than ours.** As published his
32–63 sit below our 78–165 with no overlap, and at matched spacing his 51–87 sit
below our 103–544 with no overlap. The one column where the two sides interleave
is the thinned one — his 61–98 against our 64–328, with two of our ten
(PHerc1447 at 64 and PHerc1218 at 78) inside his band — and that is the column
this section has already said is not a fair comparison. Only the *size* of the
gap depends on which column is used. An earlier version of this README said "our
later scrolls match his range" — that is false on the shipped files and it is
removed. The two sides are annotated at different z-densities and we have not
shown that the difference costs anything downstream, but we are not going to
claim parity we do not have.

> **Correction, and it is about reproducibility rather than about a number.**
> An earlier version of this README told you to fetch sean's three files "from
> the open bucket". They are not there. As far as we can establish they exist
> only as the three attachments sean posted in the Vesuvius Challenge Discord
> `#general` on 2026-08-08, so there is no URL we can honestly give.
>
> **A second correction, to how we described the check that established that.**
> An earlier version of this paragraph — and of `scripts/fetch_sean.py` — said
> each of the three prefixes in `vesuvius-challenge-open-data` "holds exactly
> three non-volume keys: a mask photo, a photo and a lasagna prediction". That
> was an incomplete enumeration written as an exhaustive one, and in the
> paragraph whose whole purpose is to show that we looked properly. Those three
> are simply the first three keys S3 hands back in key order. Each prefix
> actually holds tens of thousands of non-volume keys. Re-walked recursively on
> 2026-08-13, `volumes/` and zarr chunk interiors excluded:
>
> | prefix | non-volume keys | of which under `representations/predictions/surfaces/` |
> |---|---|---|
> | `PHerc0125/` | 37,813 | 37,802 |
> | `PHerc0211/` | 35,508 | 35,497 |
> | `PHerc0826/` | 33,481 | 33,470 |
>
> The bulk of each prefix is a `…-surface-m7-L0-th0.2.normal-grids/` tree we
> never mentioned: per-axis normal grids as `xy/`, `xz/` and `yz/` `.grid` files
> (20,840 / 8,387 / 8,387 for PHerc0125, and similarly for the other two;
> 37,614 / 35,312 / 33,258 `.grid` files per scroll in total), a few hundred
> preview jpgs under `xy_img/`, `xz_img/`, `yz_img/`, a `metadata.json`, and
> beside it a `…-surface-m7-L0-th0.2.zarr` root. **This is not staleness on our
> part.** Those keys carry `LastModified` between 2026-05-13 and 2026-07-07, so
> the tree was already there, a month old, on the day we said we had checked.
> We had listed one page and described it as the whole prefix.
>
> **What the check does establish is unchanged, and we re-ran it rather than
> restate it.** A full recursive walk of all three prefixes — 106,802 keys,
> descending everything except `volumes/` and zarr chunk interiors — returns
> **zero** matches for `umbilic|axis|centre|center|spiral|winding`,
> case-insensitively, and no loose key sits directly under any of the three
> prefixes. A crawl of `dl.ash2txt.org/community-uploads/bruniss/` to depth 3 —
> 345 directory pages, 137,026 files — likewise returns zero matches for
> `umbilic`. There is no umbilicus file under any of the three prefixes and none
> in his community-uploads area. That conclusion never depended on the miscount;
> the description of the evidence did.
>
> The listing command, corrected. What the earlier text described is what you
> get **only with `&delimiter=/`**, which collapses each prefix to its immediate
> children:
>
> ```
> $ curl -s "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/\
>     ?list-type=2&prefix=PHerc0125/&delimiter=/&max-keys=1000"
> ```
>
> returns 504 bytes: `<KeyCount>3</KeyCount>`, `<IsTruncated>false</IsTruncated>`,
> the three sub-prefixes `PHerc0125/photos/`, `PHerc0125/representations/`,
> `PHerc0125/volumes/`, and no `<Key>` elements at all — identical in shape for
> `PHerc0211/` and `PHerc0826/`. Without the delimiter the same command returns
> 412 KB, `<KeyCount>1000</KeyCount>`, `<IsTruncated>true</IsTruncated>`, and
> after those first three keys nothing but `…_cos.ome.zarr/…` chunk paths. That
> truncated page is what the earlier claim was read off, and running the command
> as it was previously documented shows a reader 1000 zarr chunks rather than the
> tidy three the sentence promised.
>

> What ships instead is `qc/sean_reference.json`: for each of his three files,
> its sha256 and byte length, its z range, and the eight derived scalars of its
> row. `scripts/axis_stats.py` prints all thirteen rows on a bare clone, marking
> sean's three as read from that digest. If you supply the files —
> `scripts/fetch_sean.py --from <dir>` verifies them against those hashes and
> refuses to install a file that does not match — the script runs **two
> independent checks per row and prints both**: whether your copy's sha256
> matches the digest, and whether all eight recomputed values match it. Be
> precise about what that buys. The bytes leg says your copy is the copy we
> measured. The numbers leg says *this version of the script, run on your copy,
> still produces the values recorded in the digest* — it catches a digest edited
> away from the code as well as a file edited away from the digest, and nothing
> about either check speaks to whether sean's annotation is right.
>
> That is a correction, not just a description. Until 2026-08-13 the numeric
> comparison sat in an `elif` behind the sha256 test, so it ran only on bytes
> already proven identical — where deterministic code cannot make it fire — and
> the set of columns it compared omitted `kinkM`, the one column the argument
> above rests on. Doctoring the shipped digest's `kinkM` from 50.79 to 999,
> leaving every sha256 untouched, still printed *"matches
> qc/sean_reference.json"*. It now prints
> `(bytes match; !! recomputed ['kinkM'] DIFFER from the digest)`.
>
> Before any of this, three of the thirteen rows were simply absent from a clean
> clone and there was no way to tell whether your copy of his files was the one
> we measured.

### 4. Independent track on PHerc0358 — **not scripted**

Its core is filled with dense sediment (bright in CT); auto-tracking that plug
confirmed 19/22 trackable points within 11–93 vox. This is a journal-documented
spot check. There is no script for it in this repository and there was none
when it was run.

### 5. The straight-stick control — new, and it is half a negative result

The Motivation section argues that a straight vertical line is not a substitute
for a per-slice axis, and until now it argued that **geometrically**: our points
move by up to 19.8 mm. That says our annotation moves. It does not say that
moving with it buys anything. Section 2 is a different question again — it
displaces the centre by a fixed 150 or 300 voxels in four directions. Nothing in
this package had ever put the annotated axis against the straight stick and
measured which one the data prefers. `scripts/stick_control.py` does, on the
same 297 slices, with the banded-energy measure of section 2 imported unchanged,
against two sticks: the vertical through the mean of each scroll's annotated
points (the reference the 19.8 mm is measured from) and the optimally placed
vertical (the Chebyshev centre, the reference behind the 18.4 mm). Its raw
output ships as `qc/stick_control_raw.json`, so it recomputes from a bare clone.

**Dated, 2026-08-19: this control was not re-measured on the densified curves.**
`qc/stick_control_raw.json` is the 15 August measurement and re-measuring needs
the slice PNGs, which do not ship. Every number in this section therefore
describes the 279-point axes, and the sticks in it stand at the mean and the
Chebyshev centre of *those* points. §6 was re-measured and this was not; where
the two sections quote a stick distance they are no longer quoting the same
sticks.

**The positive half.** Against the mean stick the annotated axis wins 188/296
slices; against the optimally placed stick, 184/295. Per scroll it is ahead in
**all ten** in both cases — sign test p = 0.00098, which is the strongest
clustered statistic in this package, stronger than section 2's 9/10 at p = 0.011
— with per-scroll median ratios of 1.07–1.54 against the mean stick and
1.01–1.69 against the optimally placed one. The denominators are 296 and 295
rather than 297 because the measure returns nothing at all at the stick centre
on a slice or two — PHerc1545 z = 17960 for both sticks, and PHerc0268
z = 12584 for the optimally placed one: the stick lands far enough off the
tissue that fewer than 20 radii carry data. Dropping those runs against this
control, since they are slices where the stick fails outright.

**The negative half, and it is the important one.** The effect does not scale
with displacement, and it was supposed to. Section 2 established that this
measure is null at a 150-voxel displacement and positive at 300, so if what the
control sees is the axis tracking real curvature, the win rate should rise with
the stick's distance from the annotated centre. Binned by that distance
(mean stick): 10/14 = 0.71 below 150 voxels, 17/27 = 0.63 at 150–300,
64/92 = 0.70 at 300–600, 97/163 = 0.60 above 600. That is flat, and if anything
faintly decreasing. Against the optimally placed stick it is 0.60, 0.72, 0.64,
0.61 — flat again. The two small-displacement bins are far too small to test on
their own (14 and 27 slices, p = 0.09 and 0.12), so this is not a
contradiction of section 2; it is a failure to demonstrate the dose–response
that would have made the result mean what we wanted it to mean.

**What we therefore claim, and what we do not.** We claim: on every one of the
ten scrolls, the banded-energy measure prefers the annotated per-slice axis to
the best straight line through that scroll's own annotation, and it prefers it
on about 62–64% of slices. We do **not** claim that this is because the axis
follows the scroll's curvature, because the flat dose–response gives us no
evidence for that mechanism. The most likely alternative — that both sticks are
derived from our own points, so the comparison is between our annotation and a
smoothed version of itself — we cannot rule out with this design.

Unlike section 2 this control was measured on the final shipped files, so it
carries no snapshot caveat.

**The figure is `panels/stick_control.png`** (`scripts/stat_figures.py stick`),
and it gives the two halves panels of the same size: the ten scrolls on the left,
the flat dose–response on the right with the confidence intervals that show the
two small bins carry almost no information. A figure of the left panel alone
would claim more than this section does.

### 6. Does the axis help a tool? A pre-registered run on all ten scrolls

Sections 1–5 are statistics about the axes. None of them is a test of whether
the axes help anyone, and that is the thing reviewers of contributions like this
one ask for: a true test that it benefits current tooling — `fit_spiral.py` is
the tool usually named — or images and demonstrations of accuracy. This package
did not have one. This section is that test. Its *unwrap demonstration* failed;
§6.7 says so before anyone has to ask. What it has instead is a statistics
figure, `panels/prereg_axis_benefit.png`, which draws the ten pairings, the
pooled result and — to scale, on one linear millimetre axis — the sensitivity
floor against the distance the straight stick actually sits at. Those are
different genres and §6.7's verdict is not softened by this one existing.

**The result.** Under a rule fixed in writing before any comparative quantity
existed, the annotated axis makes the papyrus more concentric about it than the
best straight vertical stick does about itself, on **10 of 10 scrolls** —
Wilcoxon signed-rank over the ten per-scroll means, **W = 0.0, p = 0.0020**
two-sided, pooled **+0.1598 against +0.0756, 2.11×**, 206 of 256 slices.
(Re-measured on the curves as shipped, the 20 August third pass on PHerc0191
included — §10. The 19 August densified run gave +0.1590 against +0.0760,
2.09×, 202 of 256; its PHerc0191 per-slice file is in git history at the
commit this update replaced. The 15 August run gave +0.1611 against +0.0795,
2.03×, 209 of 252, and ships as `axis_benefit/superseded_2026-08-15/`.)

**The bound, in the body and not in a footnote.** The measure is **blind below
3.63 mm**. On the 15 August curves the same pre-registered rule put that floor
at 1.81 mm; on these curves it is 3.63 mm, and §6.4 gives the table and says how
much weight the change will bear. We quote the worse of the two, because it is
the one measured on the files this package ships. A finer displacement ladder,
pre-registered and run on 20 August, adds rungs between those two; its answer
sits on the pre-registered 0.01 threshold's knife edge and has already moved a
rung within the day — **150 px = 2.72 mm** on the 19 August curves,
**125 px = 2.27 mm** after the PHerc0191 third pass (§6.4's dated notes) — so
the defensible finer statement is that the blind zone ends somewhere below
about 2.7 mm, not an exact rung, and 3.63 mm remains
the headline until the finer ladder is reproduced by someone other than us.
Either way the measure resolves gross
displacement, not annotation-scale accuracy — the same wall section 2 hits,
reached again from a different direction with a different measure. **This
section therefore credits gross axis placement and can never credit annotation
precision.** It stands up because the straight stick is a median **6.26 mm**
off, not quite twice that floor rather than the three times the earlier floor
allowed us to say, and not because our clicking is good.

`scripts/axis_benefit.py` recomputes every number below from `axis_benefit/` on a
fresh clone with numpy and scipy. The measurement itself does not run here; §6.9
says exactly what it needs.

**There was an earlier attempt, and it is not hidden.** A first, exploratory run
on ten cross-sections of two scrolls gave 7/10 slices, 0.138 against 0.084
(1.65×), Wilcoxon p = 0.037 — **but its annulus rule was adopted after a first
rule had returned a null** (5 of 8, p = 0.25). That is a forking path, so that
number was never quoted and is not quoted here; it is why the run below was
pre-registered instead. The two z-samplings do not intersect at all: **none of
the 300 slices below was scored by the earlier run** (`scripts/axis_benefit.py`
prints the 300 indices it re-derives; the earlier run used z = 6000, 7500, 9000,
10500, 12000 on PHerc0268 and 4000, 6500, 9000, 11500, 14000 on PHerc0813, and
not one of those ten is in the 300).

#### 6.1 What was fixed in advance, and when

The specification ships verbatim as `axis_benefit/PREREGISTRATION.md`, written
before any comparison existed. In summary:

| decision | fixed value |
|---|---|
| scrolls | all ten, none droppable afterwards |
| slices | 30 per scroll, `z_k = round(z_min + k(z_max−z_min)/29)`, k = 0..29, decremented if odd; `z_min`, `z_max` = the first and last annotated control point |
| axis A | villa's `json_umbilicus_z_to_yx` at `downsample_factor = 2` |
| baseline B1 (primary) | straight vertical stick at the mean of that scroll's annotated control points — the strongest straight baseline |
| baseline B2 (secondary) | straight vertical stick at the volume centre, i.e. no umbilicus at all |
| annulus | equal-evidence: largest `r1` in [400, 2000] at which A, B1 **and** B2 each see a ring ≥ 95% on the scroll; `r0 = 0.25 r1` |
| coverage inadequate | slice is non-scorable, counted and reported (§6.5) |
| visibly bad annotation | **not excluded** — in particular the two PHerc0813 points §6.6 is about |
| measure | radial gradient anisotropy `q`, 72 sectors, σ_d 1.5, σ_t 6.0, subsampling 2 |
| primary statistic | per-scroll mean of (q_A − q_B1) |
| primary test | two-sided Wilcoxon signed-rank over the ten scroll values, α = 0.05 |
| failure | p ≥ 0.05, **or** fewer than 6 of 10 scrolls positive → claim not made |
| third variant | forbidden |

The slice indices were a rule, not a choice, and that is checkable rather than
asserted: `scripts/axis_benefit.py` re-derives all 300 from the ten shipped
`PHercNNNN_umbilicus.json` and reports that the run used exactly those.

`q` = +1 means every sheet crosses every ray at right angles, i.e. the sheets are
the circles villa's spiral model assumes; 0 means no preference; negative means
sheets running radially. The structure tensor is computed once per slice and does
not depend on the axis, so **all three conditions are scored on identical image
evidence** — only the axis differs.

#### 6.2 The tool, and what could not be run

Villa's own `scripts/spiral/umbilicus.py` — the loader `fit_spiral.py:137` calls
on `<dataset>/umbilicus.json`, which is what our ten files are — and villa's own
`scripts/spiral/sample_spiral.py`, both imported **unmodified**. Nothing was
reimplemented, so what is compared is the tool's model rather than a paraphrase
of it.

**`fit_spiral.py` itself could not be run here, and this is not its output.**
Three separate reasons, each sufficient: it requires a CUDA-capable PyTorch and
this machine has no NVIDIA device (`torch 2.13.0+cpu`, `torch.cuda.is_available()`
false); its `scripts/spiral/.python-version` pins **3.14** and this machine has
3.12.3; and it consumes a prepared dataset root containing `verified_patches/`,
which does not exist for any of these ten scrolls and which we cannot produce
here. So this is a proxy for one geometric property the fitter's model asserts,
measured through the fitter's own loader and parameterisation. It is not the
fitter's loss and does not stand in for it. See §6.8.

#### 6.3 The pre-registered result

| scroll | scorable | dropped | mean q annotated | mean q stick | **Δ** | slice wins |
|---|---|---|---|---|---|---|
| PHerc0191 | 30 | 0 | +0.1448 | +0.0924 | **+0.0524** | 24/30 |
| PHerc0257 | 29 | 1 | +0.1299 | +0.0596 | **+0.0703** | 23/29 |
| PHerc0268 | 28 | 2 | +0.1416 | +0.1018 | **+0.0398** | 21/28 |
| PHerc0358 | 26 | 4 | +0.1830 | +0.0944 | **+0.0886** | 21/26 |
| PHerc0800 | 27 | 3 | +0.2118 | +0.0582 | **+0.1536** | 27/27 |
| PHerc0813 | 29 | 1 | +0.1460 | +0.0311 | **+0.1150** | 22/29 |
| PHerc1203 | 29 | 1 | +0.2208 | +0.1363 | **+0.0845** | 23/29 |
| PHerc1218 | 19 | 11 | +0.1049 | +0.0423 | **+0.0627** | 14/19 |
| PHerc1447 | 24 | 6 | +0.1527 | +0.0546 | **+0.0981** | 20/24 |
| PHerc1545 | 15 | 15 | +0.1366 | +0.0681 | **+0.0684** | 11/15 |

- **Primary: Wilcoxon signed-rank on the ten Δ values, W = 0.0, p = 0.0020,
  two-sided.** That is the smallest p this test can return at n = 10 — every
  scroll moved the same way.
- **10 of 10 scrolls positive**, against a pre-registered requirement of ≥ 6.
- Pooled over the 256 scorable slices: **+0.1598 against +0.0756, 2.11×**;
  medians +0.1486 against +0.0746; **206 of 256** slice-level wins.
- Secondary, against the volume-centre stick: +0.1598 against +0.0764, **2.09×**,
  W = 0.0, p = 0.0020, 10/10, 211/256 slices.
- Secondary and **anticonservative, so not the headline**: slices within a scroll
  are not independent, and the slice-level tests pseudoreplicate exactly the way
  section 2's pooled binomial does. For completeness they are Wilcoxon
  p = 3.8e-29 and sign test p = 1.1e-23. The scroll is the unit of replication.
- The wins are large and the losses are small: mean gap +0.1102 on the 206 wins,
  −0.0236 on the 50 losses. The annotated axis loses where it is already weak —
  mean q +0.1059 on its losses against +0.1728 on its wins. **The 50 losses are
  real and they are in the table above.**
- **All ten Δ values moved from the 15 August run, and four of them are
  down on the shipped curves** (PHerc0268 +0.0410 → +0.0398, PHerc0358
  +0.0962 → +0.0886, PHerc0800 +0.1566 → +0.1536, PHerc1545 +0.1024 → +0.0684).
  PHerc0191's fell too on the 19 August curves (+0.0467 → +0.0431) and rose to
  +0.0524 with the third pass (§10). The dated section above shows that the
  15 → 19 August rise in the pooled ratio came from the straight stick getting
  worse rather than from our axis getting better, and that at the scroll level
  that change was null at p = 1.00; the further 19 → 20 August rise is mostly
  PHerc0191's own axis improving, which §10 measured before shipping and
  quotes as leaning positive, not significant (p = 0.084).

**Villa's own winding-phase concentration does not discriminate, and we report
that too.** Computed with villa's `get_theta_and_radii` on all 256 slices, `dr`
swept 4.0–30.0 independently per axis: mean R̄ 0.0139 (annotated), 0.0145 (mean
stick), 0.0141 (volume-centre stick). At the noise floor for every axis on every
slice and identical between them. A single global Archimedean spiral does not
describe these crushed cross-sections regardless of the axis — which is why
`fit_spiral` carries a deformation field — and this quantity cannot tell axes
apart. It is reported because it is villa's own, not because it helps.

#### 6.4 The sensitivity floor, which bounds what this can claim

Our own axis displaced sideways by d in four directions, on the six
pre-registered control slices per scroll (60; 52 had valid coverage). Displaced
centres are kept only where the ring at r1 is still ≥ 95% on the scroll.

| displacement | mm | slices | median q(annotated) − q(displaced) | mean | fraction degraded |
|---|---|---|---|---|---|
| 25 px | 0.45 | 52 | +0.0002 | +0.0001 | 0.56 |
| 50 px | 0.91 | 52 | +0.0015 | +0.0017 | 0.63 |
| 100 px | 1.82 | 51 | +0.0076 | +0.0085 | 0.73 |
| **200 px** | **3.63** | 50 | **+0.0274** | +0.0338 | 0.82 |
| 400 px | 7.23 | 43 | +0.0660 | +0.0828 | 0.84 |
| 800 px | 14.36 | 15 | +0.1000 | +0.1324 | 1.00 |

**The measure is not insensitive to the axis**: at the largest valid displacement
the score is lower than at the annotated axis on **43 of 52** control slices, and
it falls monotonically. **The floor is 200 px = 3.63 mm**, the first displacement
whose median drop reaches the pre-registered 0.01 threshold. Below it, moving the
axis a millimetre and a half changes q in the third decimal, which is noise.

**The floor got worse, and that is the single number in this README that the
second annotation pass moved against us.** On the 15 August curves the same
pre-registered rule returned **100 px = 1.81 mm**: the median drop at 100 px was
+0.0105, just over the 0.01 threshold, and it is +0.0076 now, just under. Read
honestly, the threshold is a step function sitting on a median that is within
noise of 0.01 from either side. Paired on the 40 control slices the two runs
share, the 100 px drop goes from a median +0.0134 to +0.0104 with Wilcoxon
p = 0.41 (on the 19 August curves the join gave +0.0097 at p = 0.43; the
third pass moved the number, not the reading): the floor moved, the quantity
under it did not, in any sense a test can see. So the defensible statement is
that **this measure's blind zone is somewhere between 1.8 and 3.6 mm**, and that
1.81 mm was the optimistic end of it. Everywhere this README used to quote
1.81 mm it now quotes 3.63 mm, because 3.63 mm is what the pre-registered rule
returns on the files that ship. The old table, and the run behind it, are in
`axis_benefit/superseded_2026-08-15/`.

> **Dated, 2026-08-20 — a finer ladder locates the crossing at 2.72 mm, and
> both figures now travel together.** The pre-registered ladder has nothing
> between 100 and 200 px, so it brackets the floor rather than locating it —
> which is exactly how the 1.81 → 3.63 mm doubling happened on a quantity that
> moved by 0.0029. Under a second pre-registration, written — per its own
> status line — before the finer run (shipped verbatim as
> `axis_benefit/finegrid_2026-08-20/FLOOR_FINEGRID_PREREGISTRATION.md`, sha256
> `ed0d38b45e5b66711f4d2c8ff97be84879cb74f10973dd2f0553041f5d7ba252`), the
> same measure, threshold, control slices and acceptance rule were run on the
> same shipped curves with rungs added at 75, 125, 150, 175 and 300 px. Every
> original rung reproduced bit-identically, the median drop is monotone across
> all eleven rungs, and the rule returns **150 px = 2.72 mm**, with the
> crossing bracketed between 2.27 mm (median drop +0.0098, two thousandths
> under the threshold — the knife edge moved a rung down, it did not go away)
> and 2.72 mm (+0.0159). So the defensible statement narrows: the blind zone
> ends somewhere between 2.27 and 2.72 mm. Per the pre-registration's own
> commitments: **both floors are quoted together wherever this README quotes
> one, 3.63 mm remains the headline until the finer ladder has been reproduced
> by someone other than us, and 2.72 mm does not license re-quoting 1.81 mm**
> — that number came off a ladder too coarse to locate the crossing. The finer
> floor is *favourable* to us (the PHerc1203 stick margin becomes 1.5× rather
> than 1.1×, the pooled margin 2.3× rather than 1.7×), which is a reason to
> hold it to the external-reproduction bar rather than promote it; and it does
> not rescue §7.5 — the 2.00 mm agreement there is below 2.72 mm and stays
> inside the blind zone. The result document, the summary and the ten
> per-scroll control outputs ship in `axis_benefit/finegrid_2026-08-20/`
> (result copied verbatim except that one local absolute path in its
> reproduction block was shortened, the same form commits `26b4970` and
> `f9445b6` used; original sha256
> `ab3051c43a3ce11107a5613367294336f90a7fb2753897e9b1b38c18ccdd0cc4`; the ten
> json have their `umbilicus` field rewritten to `<repo>/`, nothing else). The
> rule recomputes from those json with numpy alone — median over per-slice
> direction-mean drops in q, first rung whose median reaches 0.01 — and was
> re-checked from the shipped copies before this note was written. The runner
> does not ship: like `measure/prereg_run.py` it streams the volumes and is
> referenced rather than redistributed, and the control-slice values it
> recomputed are bit-identical to the ten `prereg_PHercNNNN.json` already
> here, which is checkable from a clone.

> **Dated, 2026-08-20, after the third pass — the finer rung moved with twenty
> points of annotation, and that is the finding.** PHerc0191 was re-annotated
> later the same day (44 → 64 hand-confirmed points, §10), and
> `axis_benefit/prereg_PHerc0191.json` and
> `finegrid_2026-08-20/prereg_PHerc0191_finegrid.json` were replaced with runs
> on the new curve — full control ladder, six control slices, verified against
> the rule before this note was written. On the shipped copies the same
> pre-registered finer-ladder rule now returns **125 px = 2.27 mm**: the
> 125 px rung's median drop was +0.0098 on the 19 August curves, two
> thousandths under the 0.01 threshold, and is **+0.0111** now, two
> thousandths over (the 150 px rung moved +0.0159 → +0.0161). Nothing about
> the instrument changed; twenty re-placed points on one scroll of ten carried
> the rung across. The note above already named this knife edge, and the
> honest reading is not "the floor is 2.27 mm". It is that **a step-function
> rule evaluated on a quantity sitting near its threshold is unstable to
> ordinary annotation work** — the same fragility that produced the
> 1.81 → 3.63 mm doubling, demonstrated a second time and in the opposite
> direction. So the defensible statement is that the blind zone ends somewhere
> below about 2.7 mm, and no exact rung of this ladder should be quoted as
> though it were measured to that precision. The move is *favourable* to us —
> a lower floor widens every margin — which is one more reason not to promote
> it: **3.63 mm remains the headline**. Where this README previously asked a
> reader to reproduce the finer run and expect 150 px, it now asks for
> reproduction of the *rule* on the shipped files — the same numpy loop as
> above — which returns 125 px = 2.27 mm on the current curves, with this
> note attached. `FLOOR_FINEGRID_RESULT.md` and `floor_finegrid_result.json`
> in `axis_benefit/finegrid_2026-08-20/` are kept verbatim as the record of
> the 19 August-curve run and still say 150 px; the ten control outputs
> beside them are the current ones, and the original rungs in them are still
> value-identical to the shipped `prereg_PHercNNNN.json` (1248 of 1248 shared
> control values — the count was 1300 before the third pass changed how many
> control displacements keep a valid ring on PHerc0191).

**Why the result is nevertheless not an artifact of a blind instrument.** The
straight stick sits a median **6.26 mm** from the annotated axis over the 256
slices (mean 7.05 mm; per-scroll medians 4.09 mm on PHerc1203 to 12.07 mm on
PHerc0813). That clears the new floor on every scroll, but by a factor of 1.1 on
PHerc1203 rather than the comfortable margin the 1.81 mm floor used to give, and
that narrowing is part of the cost of this update. (Against the finer
ladder's rungs the factor would be wider, and the second dated note above says
why no exact rung of that ladder is leaned on.) The gap we measure is +0.0841
pooled; the control's median drop is +0.0274 at 3.63 mm and +0.0660 at 7.23 mm,
so the observed gap sits **above** what the control predicts for a displacement
of the observed size. The effect is therefore the right order of magnitude for
an axis error of several millimetres and no more than that; we are not claiming
a match to a decimal place, and we note that the mismatch runs in our favour,
which is a reason to be careful with it rather than pleased about it.

**What that leaves.** This section establishes that **a straight vertical axis is
wrong by several millimetres on these scrolls and that this costs a downstream
geometric measure about half of what it can score.** It establishes nothing about
millimetre-scale annotation quality, and no experiment of this shape can. Section
2 says the same thing in its own words — *"this measure resolves gross
displacement, not annotation-scale accuracy"* — about a different measure on
different slices.

Note also what this does **not** repair: section 5's dose–response is still flat.
That is a different measure (banded energy) binned by stick distance, and the
monotone control above does not stand in for it.

#### 6.5 The 44 non-scorable slices, charged against us

The exclusion rule is a joint requirement on all three axes, so no slice can be
dropped for the annotation alone. Of the 44 dropped, the axis whose ring failed
the 95% coverage test at r = 400 was **the annotated axis on 9**, the
annotation-mean stick on **33**, and the volume-centre stick on **39** (they
overlap; a slice can fail for more than one). Most drops are the *sticks* running
off the edge of the scroll — that is, the exclusion removes slices the annotated
axis would mostly have won, so it works against this claim rather than for it.
Two scrolls carry most of them (PHerc1545 15, PHerc1218 11), both because
annotation and stick diverge so far that no common ring survives.

**The adversarial version, pre-registered before the drops were known: charge
every one of the 44 to the annotated axis as a loss.** Slice-level wins become
**206/300, sign test p = 8.9e-11**. The result does not depend on the exclusions.
(On the 15 August curves this was 48 drops, 8 / 37 / 41, and 209/300 at
p = 7.7e-12.)

#### 6.6 Post-hoc, and labelled post-hoc: the two bad PHerc0813 points

Not part of the pre-registered result — the primary number above keeps these
slices in, exactly as the specification required. Two PHerc0813 control points,
z = 6616 and z = 9296, sit visibly off the coil centre on the rendered
cross-sections. Three corrections were tried, each in a *copy* of the JSON; the
shipped file was not touched.

| variant | how the two points were re-placed | PHerc0813 Δ | primary test with it substituted |
|---|---|---|---|
| **pre-registered, unchanged** | not touched | **+0.1150** | W = 0.0, p = 0.0020 |
| post-hoc "eye" ‡ | placed by eye from the sheet curvature, without reference to q | +0.0788 | W = 0.0, p = 0.0020 |
| post-hoc "drop" ‡ | deleted, letting villa's loader interpolate across | +0.0721 | W = 0.0, p = 0.0020 |
| post-hoc "argmax" ‡ | placed at the q-argmax on their own slice — **circular by construction, an upper bound** | +0.0829 | W = 0.0, p = 0.0020 |

> ‡ **Read this table with the date in mind, and it is a caveat we would rather
> print than let a reader find.** The pre-registered row is the 19 August
> re-measurement on the densified curves. **The three post-hoc rows are not**:
> `axis_benefit/PHerc0813_posthoc_{eye,drop,argmax}.json` are corrected copies of
> the 29-point 15 August file, they were measured on 13 August, and they have not
> been re-made against the 49-point file that ships. So the three variants are
> only strictly comparable with the 15 August pre-registered value of +0.0906,
> which is what they were built against and which is in
> `axis_benefit/superseded_2026-08-15/`. Against that value the reading below
> holds exactly as written. Against the +0.1150 in the row above them, the
> comparison is between two different curves and should not be made.

**All three corrections leave PHerc0813's Δ *lower* than the uncorrected
annotation they were built from** (+0.0906) — including the circular upper bound
that was allowed to choose the axis the score likes best — and the primary test
is unchanged at p = 0.0020 in every variant. Those two points are worth fixing
for the package's own sake; they do not move this number.

**Both of those points were re-placed in the second annotation pass**, so the
shipped file no longer holds the coordinates the three variants were corrections
of: z = 6616 is now (x 4890, y 5714) and z = 9296 is now (x 5716, y 3728). That
is a fourth placement, made by the same hand on denser evidence and without
reference to q, and it is the one that ships. It is not a fifth row of the table
because it was never measured as a variant — it is simply the annotation.

**The by-eye replacement is low-confidence and should be read that way.** Those
two cross-sections are crushed flat and show no identifiable whorl, so the
placement carries an uncertainty of roughly ±300 level-0 voxels (2.8 mm). It sits
12.6 mm and 14.0 mm from the currently published points, and **13.7 mm and
16.3 mm from the q-argmax** — that disagreement is evidence the eye was not
following q, which is what it was for, but it also means "eye" is one plausible
correction, not the correction. `scripts/axis_benefit.py` prints all three
placements and every pairwise distance, measured against the shipped file as it
stands.

#### 6.7 The figure failed, and it is not shipped

A reviewer asking for "accompanying images or demonstrations of accuracy"
deserves to be told this before they go looking. **We tried to build the picture,
under its own stated rule, and nothing passed.** (This attempt was made on the
15 August curves and was not repeated on the densified ones. Repeating it would
need the volumes again, and the finding it reached is about the material rather
than about our axes, so nothing in it turns on the extra points.)

The rule, fixed before rendering and never applied to any number in §6.3–§6.6:
candidates are the 300 pre-registered slices ranked by q on the **annotated axis
only** (ranking on one panel cannot manufacture a gap in the other), capped at 3
per scroll; a narrow near-core annulus, `r_in` the smallest radius ≥ 40 px where
both axes see a ≥ 95% ring and `r_out = r_in + 12 × pitch` from villa's own best
`dr`; angular sampling at Nyquist along the arc; legibility = the fraction of the
unwrap's spectral energy in the winding band sitting at angular frequency |m| ≤ 2,
i.e. "how much of the layered signal runs horizontally"; ship only if the
annotated panel shows readable horizontal bands and the stick panel their break.

**Nothing passed.** The best full-turn legibility across all ten scrolls was
PHerc0191 z = 3496 at **0.184 annotated against 0.049 for the stick** — a real
and large ratio, and the panel still reads as chaos. PHerc0257 z = 3872 gave
0.122 against 0.079; PHerc1203 z = 13558 gave 0.130 against 0.082, and there the
two axes are only ~4 mm apart so the panels look alike anyway.

**Checked on known-good data before blaming the material.** PHercParis4
(Scroll 1) at 45.532 µm, an intact scroll, at its visible core, with the centre
additionally optimised by search *for legibility*, reaches only **0.094** — no
better than our crushed scrolls, and its unwrap shows a clean two-lobed sweep,
which is ovality of the coil rather than a wrong centre. So the failure is not
our axes and not our scrolls: sheets in a Herculaneum cross-section do not lie on
circles about *any* point well enough to read as horizontal bands over a full
turn at these resolutions.

**The only crops that do read as bands are 90° windows chosen because they look
right.** PHerc0191 z = 3496, sector 270–360°, reaches 0.642 against the stick's
0.328 and is genuinely legible. That is a flattering crop; the honest answer to
"why only a quarter turn?" is "because the other three quarters do not work", so
**it is not shipped**.

**The finding, plainly: a demonstration of this kind in unwrap form does not
exist for this material.** The statistic is real at 2.11× and p = 0.0020 and it is
not visible to the eye in a polar unwrap, because what q measures — a
several-millimetre bias in a gradient-direction average over 72 sectors — is not
what an eye picks out of a crushed cross-section. We stopped building this figure
rather than ship a caption describing something the image does not contain.

**What was built instead, on 2026-08-14, and why it is not a way around the
above.** `panels/prereg_axis_benefit.png` draws the *arithmetic* of this section:
the ten paired per-scroll values, the pooled result and the tests, and the
sensitivity floor to scale against the stick distance. Every number on it is
recomputed by `scripts/stat_figures.py` from the shipped per-slice results and
printed, and its captions were written under the rule that none may claim more
than the section it illustrates — which is why the panel that would otherwise be
the flattering one, the bound, is given the full width and carries §6.4's ceiling
in the image. **Nothing above is retracted.** The unwrap demonstration a reviewer
asking for "images of accuracy" most likely has in mind still does not exist for
this material, and no crop of one is shipped. A figure of a statistic is not a
demonstration that the eye can check, and we would rather say which one this is.

#### 6.8 What this establishes, and what it does not

**Established.** Under a rule fixed in writing before the data were touched, the
annotated axes make the papyrus more concentric than the best straight vertical
stick on all ten scrolls, 2.11×, p = 0.0020, and the result survives charging
every excluded slice against us. That holds on all three releases of the
curves: 2.03× on 15 August, 2.09× on 19 August and 2.11× on the shipped
20 August curves, with W = 0.0, p = 0.0020 and 10/10 in each. Villa's spiral
geometry is demonstrably sensitive to the axis (43/52 control slices degrade
monotonically). The sensitivity floor is 3.63 mm and the effect lives at a
median 6.26 mm — a factor of 1.7, where the earlier floor made it a factor of
3.3 (the finer ladder of §6.4's dated notes would widen that factor, and those
notes say why its exact rung is not leaned on).

**Not established, and not claimed.**

- **This is not `fit_spiral`'s output** (§6.2). The real fitter also carries a
  deformation field, surface tracks, patches and winding-consistency losses, any
  of which could recover from a wrong axis or profit from a right one in ways
  nothing here measures. The unambiguous version of this experiment is a GPU host
  with a prepared spiral dataset and `fit_spiral` run twice on one scroll; that
  is still the thing to do and this is not a substitute for it.
- **Nothing here credits annotation precision** (§6.4), and no experiment of this
  shape can. The second annotation pass is the demonstration: it added 114
  hand-confirmed points and this test cannot see them (dated section above,
  scroll-level p = 1.00).
- Nothing here confirms or overturns sections 1–5, which use different measures
  on different slices.
- One thing this run suggested and did **not** test, left for a fresh
  pre-registration rather than reported alongside as a result: the effect looks
  largest where the annotation departs furthest from vertical. That is a new
  claim and it needs its own specification, written first.

#### 6.9 What ships, and what does not travel

Shipped: `axis_benefit/PREREGISTRATION.md` (the specification, verbatim), the ten
`axis_benefit/prereg_PHercNNNN.json` (every slice, every axis, every control
displacement, with the q, the pixel count, the ring coverage, the displacement in
µm and villa's R̄), the three post-hoc variants and the corrected copies they were
run from, and `axis_benefit/measure/` (the measurement code as it ran), and
since 2026-08-19 the whole of the previous run under
`axis_benefit/superseded_2026-08-15/` (a further 590 KB), so that the two
releases of the curves can be compared rather than taken on trust. 1.4 MB in
total. `scripts/axis_benefit.py` turns the per-slice values into every statistic
above on a fresh clone.

**What does not travel is the measurement itself.**
`axis_benefit/measure/prereg_run.py` streams one z-plane at a time out of ten
masked OME-Zarr volumes in `vesuvius-challenge-open-data` — level 1 of each
scroll's prize volume, uint8, 3422² to 6073² per slice, so **12 to 38 MB of range
reads per slice and about 5.7 GB across the 300** — and nothing is cached, so
re-measuring means re-streaming. It also imports villa's `umbilicus.py` and
`sample_spiral.py` from a `volume-cartographer` checkout: those are not ours to
redistribute and are referenced by path rather than copied. It needs torch (CPU
is enough). Every volume id is in `PREREGISTRATION.md` §3 and in each scroll's
own `metadata.source_volume`, so the inputs are named exactly and are public.
The run took 39 minutes of wall time in two processes of two torch threads each.

### 7. The one external check: PHerc1218 against a prior annotation

Everything above compares our axes against a control we built ourselves — a
displaced centre, a straight stick, an auto-centroid — or against sean's three
files, which are three *other* scrolls. **On exactly one of our ten there is an
independent annotation by someone who is not us**, and this section is it.

> **Dated, 2026-08-20 — read this before the history below.** As first
> written, this section presented an agreement — median 2.00 mm over the
> overlap — with a disagreement noted: one band, z ≈ 7500–9500, where the
> two files diverge by up to 7.20 mm. That disagreement has since been
> **arbitrated by observations neither side made for the purpose** — the
> relative-winding chains and same-winding arcs of the same public pack,
> machine-generated from stitched instance labels and derived from no
> umbilicus — **and our axis loses the band.** §§7.1–7.5 stand as the
> measurements they are; §7.6 is the arbitration, with the numbers, the
> caveat, and the practical consequence: over z 7500–9500, prefer the prior
> file to ours. This section can no longer be read as a check we passed.

#### 7.1 What the prior annotation is

`data/spiral_input_pherc1218/umbilicus.json` in
[IyanDopico/vesuvius-sheet-tools](https://github.com/IyanDopico/vesuvius-sheet-tools),
added in commit
[`6a831e0`](https://github.com/IyanDopico/vesuvius-sheet-tools/commit/6a831e0a9a)
on **2026-07-21**, three weeks before our files. 33,718 bytes, sha256
`a153ad7a…c29560`. MIT-licensed, and shipped here verbatim as
`qc/prior_umbilicus_PHerc1218_IyanDopico.json` with its provenance and licence
notice in `qc/prior_umbilicus_PHerc1218_SOURCE.md`, so this section runs from a
bare clone rather than on our word.

| | ours | the prior annotation |
|---|---|---|
| points | 36, integer, hand-placed | 365, float, generated |
| z range / spacing | 3432 → 21144, step 304–616 vox, median 608 | 32 → 23216, median step 64 vox |
| shape | `{"control_points": [{x, y, z, score}], "metadata": {…}}` | `{"control_points": [{z, y, x}]}` — no metadata, no score |
| frame | level-0 voxels of `20250521120456-8.640um-…-masked` | the same |
| what a point *is* | a human's placement of the winding centre | **the centroid of the papyrus mask of that slice** |

The last row is the finding, and it is a difference of convention, not of
quality. Their generator, `scripts/constraints/make_umbilicus.py` in the same
repository, composites the nonzero-label mask of their own instance
segmentation at eight sampled slices per 256-slice slab, takes `ys.mean(),
xs.mean()` of that mask, running-median smooths the z→(y, x) series over five
samples, and multiplies by 2 to go from their L1 working grid to level 0.
Slices with fewer than 10,000 nonzero mask pixels are dropped. It is a mass
centroid, and it is honest about being one: the file is an input to a spiral
fit's loss, not a claim about where the winding centre is.

**The frame is shared, and that was checked rather than assumed.** Their
generator hard-codes `FULL_Z = 23247`, `FULL_YX = 7593`; their pack's
`README.txt` names the same volume our `metadata.source_volume` does; the
bucket's `…/0/.zarray` returns `shape [23247, 7593, 7593]` and its
`metadata.json` returns `samplePixelSize` 0.00864 mm. All four agree, so what
follows is a distance and not a registration problem
(`scripts/prior_1218.py --check-bucket`).

#### 7.2 What was fixed before the numbers existed

`qc/PRIOR1218_PREREGISTRATION.md`, sha256
`e375f3730305218ebeec66205fdd92b8ec71636477119cbb2c808566164dc9b4`, written and
hashed **before** `scripts/prior_1218.py` was first run. It states, in advance:
that the two files are not defined to be the same point and that no result would
be reported as one being right; what would be computed (the overlap, the
distance distribution rather than a single number, the signed offset, the
residual after removing it); and four bands, expressed in distances this package
already publishes rather than in a number invented for the occasion:

| band | meaning, fixed beforehand |
|---|---|
| median < **1.81 mm** | closer than the sensitivity floor of §6.4 — interchangeable for this package's own benefit test |
| median < **6.0 mm** | smaller than the axis-to-stick distance §6 measures — agreement at the scale that matters |
| median < **20.7 mm** | the size of the effect this package claims; would have to be explained, not absorbed |
| median ≥ **20.7 mm** | larger than the Motivation number; the comparison failed and the framing is withheld |

**Those three thresholds are frozen at the values §6.4, §6 and the Motivation
section carried on 15 August, and they stay frozen** — a pre-registered band
that is re-tuned after the fact is not a pre-registered band, and
`scripts/prior_1218.py` still prints them as written. What they mean has
shifted, and a reader is entitled to know by how much: §6.4's floor is now
3.63 mm rather than 1.81 mm (with the 20 August finer ladder ending the blind
zone somewhere below about 2.7 mm — §6.4's dated notes), §6's median stick
distance is 6.26 rather than
6.0 mm, and the Motivation number is 19.8 rather than 20.7 mm. The verdict below
is unaffected — it falls in the second band on either set of thresholds — but
the first band would now be a *weaker* statement than it was, not a stronger
one, and §7.5 says what that does to the reading.

It also fixed what each *shape* of disagreement would mean: a constant offset
would be a convention or frame difference; a z-dependent one, largest where a
cross-section stops being symmetric, would be the centroid-versus-centre gap
opening; a disagreement of the order of the scroll's radius would be an actual
error in one of the two files.

#### 7.3 The result

Over the overlapping z — 3432 → 21144, 153.0 mm of scroll, 76% of the z their
file spans — on their 64-voxel grid, 276 samples, our polyline interpolated
linearly, which is what villa's own `json_umbilicus_z_to_yx` does:

| | voxels | mm |
|---|---|---|
| min | 71.4 | 0.62 |
| p25 | 157.4 | 1.36 |
| **median** | **231.9** | **2.00** |
| p75 | 362.3 | 3.13 |
| p90 | 506.3 | 4.37 |
| max (at z = 8608) | 833.3 | 7.20 |

At our 36 hand-placed nodes only, with our file not interpolated at all, the
median is 2.20 mm and the max 7.25 mm — the same answer, so none of it is an
artifact of our own interpolation. Re-running the interpolation through villa's
loader instead of `np.interp` changes the distances by **0.0000 voxels**
(`--villa`).

**Recomputed on the 19 August curves; the median came down and the tail went
up.** On the 15 August 28-point axis this section read median 2.10 mm and max
4.92 mm at z = 5856. The densified axis agrees with the prior annotation
slightly better in the middle (2.00 mm) and disagrees considerably more at its
worst (7.20 mm, at z = 8608, inside the band §7.3 already identified as carrying
the disagreement). We are not going to describe a 46% larger maximum as an
improvement because the median moved 0.1 mm the other way.

**Verdict, against the band fixed beforehand: the second one, and the script
prints it.** The two independent annotations of PHerc1218 differ by 2.00 mm in
the median and by up to 7.20 mm — below the 6.26 mm distance §6 measures between
our axis and the straight stick it beats in the median, though the tail now
exceeds it, and above the 1.81 mm the pre-registered band names. The whole
distribution and the figure are `panels/prior_1218_agreement.png`. (The tail
of that distribution — the z 7500–9500 excursion — is the part §7.6 has since
arbitrated against us.)

**It is not a constant offset.** The mean (Δy, Δx) is (−33.5, +161.5) voxels =
1.42 mm, and removing it leaves a median residual of 1.78 mm: a single constant
vector explains only **11%** of the median distance. So this is not a frame or
origin difference. It is z-dependent, and it is concentrated. Over eight equal z
bands the medians are 1.15, **3.52**, **5.15**, 1.33, 1.37, 1.82, 2.67 and
1.67 mm: one band of scroll around z 5700–10100 carries most of it, and the
densified axis makes that band worse rather than better (3.82/3.20 → 3.52/5.15).

**And it is not our coarser sampling either.** Our nodes sit a median 608 voxels
apart, theirs 64. Resampling *their* polyline onto our node grid and
interpolating it back — the most a polyline sampled like ours could carry of a
line sampled like theirs — loses a median of 0.15 mm, a p90 of 0.44 mm and at
most 1.16 mm, well under the 2.00 mm.
The two files genuinely put the centre in different places.

#### 7.4 Why, measured rather than asserted — and post-hoc

§7.1 says their points are a mass centroid. That is a statement about their
source code, and it can be tested against the CT: if their file is a mass
centroid, then the CT's own per-slice mass centroid should lie on their line and
not on ours. **This was not pre-registered.** It was added after seeing that the
disagreement was z-dependent rather than a constant offset — which is the outcome
the pre-registration named — and it is a diagnostic of the mechanism, not a test
of either file. `scripts/prior_1218.py --measure-centroid` streams level 5 of the
same masked volume (276.5 µm per voxel, 24 chunks, about 48 MB) and takes three
centroids per slice; its output ships as `qc/prior_1218_centroid_raw.json`.

Over the 553 slices of the overlap:

| centroid of | to ours | to theirs | theirs closer on |
|---|---|---|---|
| the nonzero mask | 1.96 mm | **0.25 mm** | 550 / 553 |
| intensity, all nonzero | 1.93 mm | **0.24 mm** | 552 / 553 |
| intensity, top 40% only | 2.05 mm | **1.20 mm** | 403 / 553 |

The CT measurement itself is frozen — `qc/prior_1218_centroid_raw.json` is the
13 August streaming run and their file has not changed — so the "to theirs"
column is identical to the earlier version of this table and only the "to ours"
column moves with our axis.

The CT's mass centroid sits on their line, a quarter of a millimetre from it,
on essentially every slice. Their generator says the file is a papyrus-mask
centroid and the CT agrees that it is one. **So the 2.00 mm is the distance
between a mass centroid and a hand-placed winding centre on this scroll — a
property of PHerc1218's cross-sections, not annotation error on either side.**
*(Dated 2026-08-20: that sentence survives for the median and fails for the
tail. Over z 7500–9500, §7.6's arbitration says the residual is annotation
error, and it is ours.)*
The third row is the interesting one, and it does not rescue the winding
centre — less than ever. Restricting the weight to the densest 40% of the
material moves the centroid 0.95 mm **off** their line and, on the densified
axis, 0.09 mm **further from** ours rather than closer to it; it still lands
closer to theirs on 403 of the 553 slices, which is 11 more than before. On the
15 August axis that row moved 0.20 mm towards ours and we said so; on these
curves it moves the other way, and the honest reading is that the hand-placed
centre is not the centroid of the brighter papyrus either, and is now a little
further from it than it was.

#### 7.5 What this establishes, and what it does not

It establishes that on the one scroll where an independent annotation exists,
our hand-placed axis and an automatic mass centroid agree to 2.00 mm in the
median, that the
residual is explained by the two being different quantities, and that the
explanation is measurable in the CT rather than argued.

It does **not** make either file ground truth — two methods can share a bias, and
on a scroll that leans consistently to one side a human eye and a mass centroid
can be pulled the same way. It covers one scroll of ten and only the z both files
span. Nothing here licenses a claim about the other nine. And it is not a test of
precision — **less of one than this section used to claim.** On the 15 August
curves the median 2.10 mm sat just above §6.4's then-floor of 1.81 mm, which put
the comparison at the edge of what this package can resolve. §6.4's floor is now
3.63 mm and the median is now 2.00 mm, so the whole of this agreement sits
**inside** the blind zone of the only instrument here that could have priced it.
(The 20 August finer ladder returns 2.72 mm on the 19 August curves and
2.27 mm on the shipped ones — §6.4's dated notes; 2.00 mm is below either
rung, so this reading does not change.)
Two axes 2.00 mm apart are, by this package's own benefit measure, the same
axis. That does not make the agreement worthless — it is still an independent
annotation agreeing with ours at a scale far below the effect §6 measures — but
it does mean this section can no longer be read as evidence about millimetre
accuracy, and the 7.20 mm maximum is the part of the distribution that the
instrument could actually see.

**Dated 2026-08-20 — one clause above is withdrawn rather than qualified.**
"The residual is explained by the two being different quantities" was measured
over the whole overlap and is now known to be false for one band of it: §7.6
measures, on observations neither annotator made, that over z 7500–9500 the
residual is our annotation error. What this subsection establishes after that
is smaller and should be stated at its new size: outside that band, an
independent line and ours agree to about 2 mm and the difference is the
centroid-versus-centre convention; inside it, the external data sides against
us.

#### 7.6 Dated, 2026-08-20 — the disagreement is arbitrated by observations neither side made, and we lose it

Everything above measured *that* the two files disagree and *where*. Nothing
above could say which one is wrong: two annotations, no third witness. The
third witness turned out to already exist. The same public pack the prior axis
ships in also carries the spiral fitter's constraint inputs for PHerc1218 —
12,924<!--ledger:wind.d1218.n_chains--> relative-winding chains and
1,863<!--ledger:wind.d1218.n_arcs--> same-winding arcs, machine-generated from
stitched instance labels. They were made as inputs to a spiral fit's loss, not
for this comparison, and they are derived from no umbilicus — so as between
the two axes under test they are third-party evidence, independent of both.
Checked against both axes, three signals agree:

- **The chains contradict our axis twenty times more often than his.** A
  +1-winding step should move radially in one consistent direction about the
  true centre (the direction is taken from each axis's own median, so the test
  is self-calibrated per axis). About our shipped axis,
  600<!--ledger:wind.d1218.sign_viol_ours_common--> of
  12,058<!--ledger:wind.d1218.chain_steps_common--> evaluable steps carry the
  minority sign, against 31<!--ledger:wind.d1218.sign_viol_his_common--> about
  his prior axis on the identical step sample; as rates over each axis's full
  evaluable support, 0.0498<!--ledger:wind.d1218.sign_viol_rate_ours--> versus
  0.0024<!--ledger:wind.d1218.sign_viol_rate_his-->.
- **A centre fitted from the arcs alone lands on his line, not on ours.**
  Minimizing the mean within-arc radius spread per 1024-voxel z-band gives a
  fitted centre whose own residual is a median
  3.305<!--ledger:wind.d1218.resid_fit_med_vox--> voxels (29 µm) — far below
  the local pitch the chains themselves measure,
  18.8<!--ledger:wind.d1218.chain_pitch_med_vox--> L0 voxels (162 µm) per
  +1 winding — so the arcs in every band agree on a single centre. That centre
  sits a median 1.0 mm<!--ledger:wind.d1218.dist_fit_his_med_mm--> from his
  axis against 2.125 mm<!--ledger:wind.d1218.dist_fit_ours_med_mm--> from
  ours, and his axis beats ours on the arc-consistency objective in
  16<!--ledger:wind.d1218.arcfit_his_beats_ours_bands--> of
  16<!--ledger:wind.d1218.arcfit_bands_both--> bands
  (Wilcoxon p = 3.05e-05<!--ledger:wind.d1218.arcfit_wilcoxon_p-->).
- **All of it peaks where the two axes diverge.** The chain-violation rate
  about our axis is 12.5%<!--ledger:wind.d1218.sign_viol_rate_ours_band_pct-->
  inside z 7500–9500 against
  3.9%<!--ledger:wind.d1218.sign_viol_rate_ours_outside_pct--> outside,
  peaking at 14.5%<!--ledger:wind.d1218.sign_viol_rate_ours_peakband_pct--> in
  the worst 1024-voxel band; the arc-fitted centre is
  8.07 mm<!--ledger:wind.d1218.dist_fit_ours_worstband_mm--> from our axis at
  that band; and the two hand axes are furthest apart in exactly that band —
  7.14 mm<!--ledger:wind.d1218.axis_sep_z8700_mm--> at z = 8700 (§7.3's
  7.20 mm maximum at z = 8608 is the same excursion).

**The practical consequence, said plainly.** Anyone consuming
`PHerc1218_umbilicus.json` should prefer the prior file — shipped in this
repository as `qc/prior_umbilicus_PHerc1218_IyanDopico.json` — over
z 7500–9500. Over the rest of the height the two files agree to about 2 mm
and either serves this package's own instruments. The fix on our side is
re-annotation of that band; it has not been done, and this note stands until
it is.

**How it was found, because that is the method's point.** No new annotation
was involved. The arcs and chains were already held, imported losslessly from
the pack's `same_windings.json` and `relative_windings.json`, and the finding
fell out of cross-checking assertion kinds against each other — which is the
argument for recording arcs and chains alongside centres at all. The checker
and the derivation (`checks.py`, `derive1218.py`) live in the
winding-observations working tree and do not ship in this repository yet; the
arbitrating inputs are public, and every number above is under provenance in
our measurement ledger.

**The caveat, stated rather than absorbed.** The chains were generated by
rays from slice centroids, so an axis lying near the centroid field is
structurally favoured by the sign check — and §7.4 measured that the prior
axis essentially *is* the mass centroid, so this arbitration is weakly
circular in the prior's favour. It is not fully circular: the arc-fit
objective does not use the ray construction, and three instruments agreeing —
chains, arcs, and the radial fan the chains draw around his centre in the
working tree's z = 8700 view (not shipped here) — makes centroid bias an
unlikely full explanation. The clean
closure, a CT-only concentricity measurement of §6's kind at both axes over
the band, has not been run; until it has, "we lose the band" rests on the
constraint data, not on the CT itself.

**What this does not say.** It says our shipped PHerc1218 axis is wrong over
roughly z 7500–9500, by up to about 7 mm, on this one scroll. It does not
impeach the annotation method: outside the band the same chains fall to the
3.9% background about our axis, and no comparable constraint data exists on
the other nine scrolls in either direction. It does not touch §6, whose
axis-benefit claim was measured against a straight stick, not against this
prior, and stands as measured. And it does not make the prior axis right
everywhere: his file remains what §7.1 says it is — a mass centroid, an input
to a fit's loss, not a claim about the winding centre — and the arbitration
localizes *our* error; it does not certify his line beyond what the arcs and
chains, which come from his own segmentation, can witness.

### 7b. A second external check, arriving after the fact — TAUIL Abd Elilah

On 16 August, after this package was published, TAUIL Abd Elilah released
[`umbilicus-cross-validation`](https://github.com/TAUIL-Abd-Elilah/umbilicus-cross-validation)
— six independently hand-drawn curves (PHerc0191, 0257, 0358, 0800, 0813, 1203)
plus an exact-CT audit, pinned to this repository at commit `57e09a3`, which is
the state *before* the 19 August densification. Everything below is his work
measured against ours; none of it is ours to claim, and the comparison numbers
here move as either set changes.

Three things belong in this README rather than only in his:

- **He withdrew his own PHerc1203 in favour of ours**, after his review found
  four separated regions where the public curve follows the scroll core more
  consistently. His words about his own findings (release notes, v0.2.0;
  verified against the live releases page 2026-08-20 — the sentence appears
  there, not in his repository's files): *"AI-assisted triage, not
  anatomical ground truth or proof that this curve set is more accurate than
  Aleksei Drobkov's."* That is a check on our most important scroll, and it went
  our way, but it is an assisted review and it says so.
- **His comparison tool runs here, and which release of our curves it is fed
  decides what it returns.** Re-run 2026-08-20: against PHerc0191 as this
  repository stood at `57e09a3` — the commit his audit pins, before the
  densification — `compare_independent_curves.py` reproduces his published
  table exactly, median 4.38 mm, max 18.31 mm at z=15480, the same peaks our
  own independent measurement found. Against the shipped densified curves it
  returns **median 3.06 mm, max 14.21 mm at z=15240**: the densification moved
  the comparison, which is what this section's opening paragraph says happens
  as either set changes. A reader who clones both repositories today and runs
  his script gets the second pair of numbers, not the first. An earlier
  version of this bullet said the exact reproduction was obtained "against
  this repository unchanged"; that was false — the run behind that sentence
  was made on the pre-densification curves — and it is corrected here rather
  than deleted. Re-run once more after the 20 August third pass on PHerc0191
  (§10): against the shipped 64-point curve his script returns **median
  2.92 mm, max 13.65 mm at z = 8528** — the peak moves out of the z ≈ 15240
  band, which the third pass re-annotated, to the other band of concentrated
  disagreement.
- **The densification moved us further from him on PHerc0813, not closer.** Our
  own curve there got smoother — worst estimated midpoint miss 930 → 417 µm — and
  the median distance to his went 4.81 → 9.21 mm at the same time. Getting
  smoother and further apart is not noise behaviour; it says the two annotations
  are following different folds on that scroll. Four of the six disputed
  locations there and on PHerc0191 read, to our eye on the CT, as ours on the
  core; on PHerc0358 z=9944 the two curves converged from 10.9 mm to 1.6 mm after
  our pass, which is the one place his provisional reading was right and ours
  moved onto it. All of that is a reading of CT by one experienced pair of eyes,
  the same standing he gives his own, and none of it is settled.

Two rankings of where a curve most needs more control points — his, from spacing
and turn angle, and ours in micrometres from `scripts/midpoint_audit.py` — agree
at Spearman ρ 0.48 to 0.89 per scroll. The lowest agreement is on PHerc1203,
where they share one interval in five worst. Where two independent instruments
disagree about where to look is probably where to look.

### 8. Frame metadata: the villa#1454 keys, and the byte identity we retired

Open PR [ScrollPrize/villa#1454](https://github.com/ScrollPrize/villa/pull/1454)
(*umbilicus: frame metadata, project attachment, shared resolver*, opened
2026-08-14, **not merged**) adds five optional keys to the `metadata` block of
`umbilicus.json` — `volume`, `voxelsize_um`, `volume_width`, `volume_height`,
`volume_slices` — and says outright that "longer term the detection tool should
stamp these keys at generation time". **Our ten now carry them.**

**Why, in one line:** our ten span two voxel sizes, 9.362 µm for six and
8.640 µm for four. This README has carried that in prose since the first commit,
where a consumer has to read it; these keys make it machine-checkable, and the
consumer rule the PR states — rescale by `voxelsize_um / target_voxelsize_um` —
is exactly the arithmetic a reader of our files has to get right.

**The argument against, stated because it is real.** The PR is unmerged and its
schema has already changed once under review: the first version stamped a
pyramid level, `zarr_level`, and commit `85c5be1` replaced it with the three
grid dimensions, on the reasoning that integer voxel counts identify a rescaled
copy where rounded micrometre sizes are ambiguous. It can change again. We
stamped anyway, because the keys are optional and additive — the PR's own loader
reads unstamped files exactly as before, and any consumer that does not know
them ignores them — so the cost of a further change is regenerating five lines,
which `scripts/stamp_frame.py --write` does. What we do not do is claim
conformance to a merged standard: this follows PR #1454 at commit `85c5be1`, and
that is what the sentence should say wherever it is repeated.

**No value was typed by hand.** `scripts/stamp_frame.py` derives every one from
that file's own `metadata.source_volume` and verifies it against the bucket
before writing:

- `voxelsize_um` — the `-<n>um-` token of the volume id, **cross-checked** against
  `<volume>/metadata.json` → `scan.tomo.acquisition.detector.samplePixelSize`
  × 1000. All ten agree exactly (9.3620 and 8.6400); a mismatch is a hard error
  and nothing is written.
- `volume_width` / `volume_height` / `volume_slices` — `shape[2]` / `shape[1]` /
  `shape[0]` of `<volume>/0/.zarray`.
- `volume` — the store name, the last path component of `source_volume`. The full
  bucket path stays in `source_volume`, which was not touched.

Two further checks it runs and prints: every control point of every file is
inside the shape it is stamped with, and the shape matches the `shape_L0`
recorded independently in that scroll's own `PHercNNNN/meta.json` when the
slices were cut. All ten pass both.

**A limit of these ten files, printed per scroll so it cannot be missed:** all
ten volumes have `shape[1] == shape[2]`, so `volume_width` and `volume_height`
are equal in every one of them. Our files therefore cannot distinguish the two
conventions and must not be read as evidence for either.

**The byte-identity invariant is deliberately retired at this commit.** Until
now the ten json files were byte-identical to commit `da52f97`, and that was
worth something: every number in this README was measured on files nobody had
touched. Stamping changes them. The change is five lines appended inside
`metadata` and nothing else — the rewrite is `json.dump(indent=1)` with no
trailing newline, which round-trips these files byte-for-byte when nothing is
added, so the diff is the five keys and only the five keys, and `git diff` shows
exactly that. **No coordinate, no score and no existing metadata field moved,
and every number in §§1–7 is unaffected.** The hashes, so the old files remain
identifiable:

| scroll | md5 at `da52f97` | md5 now |
|---|---|---|
| PHerc0191 | `bffb38e51d4bfd4b75912c44816b72c8` | `a850067c227caab3ed09a1f9e7e79298` |
| PHerc0257 | `ed40d7c7a2e2ad2a18371320ff1316c2` | `7f1aa8e7b232bc183b51c8d7bfc3211c` |
| PHerc0268 | `7280c94dcf7575fdf240d6065e780dc0` | `16380cea367374808a129c50ff9f75f1` |
| PHerc0358 | `0345614a1468886bc4e74be89441adde` | `91e75cf40ad7644d3677795e53c0cb82` |
| PHerc0800 | `3bae66bf7b0846a9cb16ffa37bf591d7` | `55e591ac2ebff738ab3aa20675dee5e9` |
| PHerc0813 | `3b268edc47c9f9d9cb1469ebd8631e11` | `276d60f9b08bc024f5867c40fa802c4d` |
| PHerc1203 | `a64ea80a7197139074abb05211cc6e3f` | `9ca94cb82b7950738b57746547046777` |
| PHerc1218 | `13e542d12855d64bfca65c40ac7a2e58` | `9e8f53e74cbf7878d7737f3d02ddcaa2` |
| PHerc1447 | `d05acb9d7a0e9ca89bce2b1da93aae22` | `9d6ea06fe8e09169526a176edeea09e9` |
| PHerc1545 | `bc6d5fe47f945267d9f6c24327b3769b` | `f965763fd3629b20f024d30810cb45f4` |

## Panels

Thirty-six figures ship in `panels/`. None of them is the source of a number:
every quantity printed on a panel is one this README states and one of the
scripts recomputes. Where a panel and this README disagreed, the panel was
re-rendered — the ten-scroll atlas below is that case, and it is named rather
than quietly fixed. One figure was rejected for printing a count that only it
could produce, rebuilt without the count, and is described under "the two
centres" below.

> **Re-rendered, 2026-08-20.** An earlier version of this box said that all
> thirty-six panels predated the 19 August densification, that none had been
> re-rendered for it, and named the four worst cases; that was true when it
> was written and is not the state of this directory any more.
> **Twenty-four of the thirty-six were re-rendered on 2026-08-20** on the
> shipped densified curves and the current result files: the four statistics
> panels (`scripts/stat_figures.py`), `prior_1218_agreement.png`
> (`scripts/prior_1218.py --figure`), `calibration_summary.png`
> (`scripts/calib_sean.py` re-run on the densified curves, then
> `scripts/calib_figure.py`), the ten `axis_PHercNNNN.png`, the ten-scroll
> atlas, the four annotation-site panels and the three `centre_in_core_*.png`.
> Every re-render was compared against the file it replaced before shipping.
> Five of the twenty-four came back **byte-identical** — `stick_control.png`,
> `shifted_axis_controls.png` and `frozen_axis.png` from their frozen raw
> inputs, and `annotation_site_PHerc1203.png` with its close-up, whose nodes
> the densification did not move — so for those five the re-render is the
> check that the pipeline still reproduces them.
>
> The four cases the earlier box named are closed the corresponding way:
>
> - `prereg_axis_benefit.png` now draws the current §6 run — +0.1590/+0.0760,
>   2.09×, 202/256, the 3.63 mm floor with the 20 August finer-ladder floor of
>   2.72 mm beside it (§6.4; both computed at draw time), and the 6.24 mm
>   stick distance. Re-drawing it also exposed a hardcoded panel title in
>   `stat_figures.py` still reading "blind below 1.81 mm … median 6.0 mm";
>   the title is computed now. The redrawn bound is honestly *tighter* than
>   the old picture: the stick clears the headline floor by 1.7× (2.3×
>   against the finer floor) where the old figure showed 3.3×.
> - `prior_1218_agreement.png` now draws the current §7 distribution — median
>   2.00 mm, max 7.20 mm — against the current yardsticks (2.72 / 3.63 / 6.24 /
>   19.8 mm), all recomputed at draw time; the verdict bands sealed in
>   `qc/PRIOR1218_PREREGISTRATION.md` stay 1.81 / 6.0 / 20.7 mm and the panel
>   footer says so. One thing the new picture shows that the old one could
>   not: the distribution's tail now crosses the stick yardstick (7.20 mm
>   against 6.24), where the old panel's whole distribution sat below its
>   6.0 mm line. §7 states both numbers.
> - `axis_polylines_all_ten.png` now draws the 32–64-node polylines, the
>   19.8 mm Motivation deviation (PHerc0813), and §3's re-measured ring-gate
>   median — 279.9 vox over 413 points against sean's 273.6 over 75 — see
>   the dated note in §3, which that re-measurement also updates.
> - `centre_in_core_PHerc0191.png` now draws the green cross where the shipped
>   file puts it. The two crosses at z = 15480 are 8.48 mm apart where the
>   first pass had 16.71 mm; the visual verdict is unchanged — the fold is still beside
>   the auto-centroid, the manual node still stands on flat layering, and the
>   caption still says so. The at-this-height separation on all three panels
>   of that set is now computed from the drawn centres, so it cannot drift
>   from the picture again; the stack medians still come from the §1
>   fixtures, which hold the 15 August axes, and the captions say that too.
>
> **Twelve panels were deliberately not re-rendered**: `step2_points_*` and
> `step2_stack_*` (three each), `order_map_*` and `order_bump_*` (three
> each). They draw §1's winding-order measurement — the traced stacks and the
> `qc/order_fixture_*.npz` fixtures, which hold the 15 August axes and were
> not rebuilt, because rebuilding them means re-running the tracer, which
> does not ship (§1's dated box). Re-drawing those twelve on the densified
> curves would be a re-measurement of §1 presented as a re-render, and §1 has
> not been re-measured. They remain the 15 August renders and are exact for
> their frozen inputs.

> **Dated, 2026-08-20, later the same day — the PHerc0191 third pass (§10)
> postdates most of the renders the box above describes.** Re-rendered on the
> shipped third-pass curve or its results, the same day: the ten-scroll atlas
> `axis_polylines_all_ten.png` (PHerc0191 now 64 nodes, 413 points in total);
> `prereg_axis_benefit.png` and `prior_1218_agreement.png`, whose quantities
> are computed at draw time and now come from the 20 August run — so where the
> box above quotes +0.1590/+0.0760, 2.09×, 202/256 and yardsticks
> 2.72 / 3.63 / 6.24 mm for those two panels, the panels as shipped draw
> +0.1598/+0.0756, 2.11×, 206/256 and 2.27 / 3.63 / 6.26 mm (§6.4's second
> dated note on why the finer rung moved); and `calibration_summary.png`,
> re-drawn from the 413-point re-measurement (§3's dated notes — the medians
> round to the same 279.9 against 273.6). Re-running `stat_figures.py` also
> reproduced `stick_control.png`, `shifted_axis_controls.png` and
> `frozen_axis.png` **byte-identically** from their frozen inputs, and exposed
> two hardcoded labels in it — "252 scorable slices" and "53 control slices",
> wrong since the 19 August re-measurement (256 and 52) — which are computed
> now. **Three PHerc0191 panels still draw the 19 August 44-point curve**:
> `axis_PHerc0191.png`, `annotation_site_PHerc0191.png` and
> `centre_in_core_PHerc0191.png` need the annotation tree to re-render and
> were not redone for the third pass. In particular the green cross of
> `centre_in_core_PHerc0191.png` is the 44-point placement of the z = 15480
> node, 8.48 mm from the auto-centroid; the shipped 64-point file puts that
> node 5.62 mm from it. And `axis_PHerc0191.png`'s printed deviation is the
> 44-point curve's 9.82 mm, where `scripts/axis_stats.py` on the shipped file
> prints 9.98 mm. The visual verdicts those captions record were made on the
> drawn placements and are not re-argued here.

**The axes themselves.**

- `axis_PHercNNNN.png` × 10 — each axis drawn on its scroll. **Re-rendered
  2026-08-20 on the shipped densified curves** (an earlier note here said they
  were drawn on the 15 August curves and should be read as the first pass's
  axes; that render is replaced). The caption's max deviation from vertical is
  recomputed from the shipped json at draw time; nine of the ten values printed
  match `scripts/axis_stats.py` run today, 19.8 mm (PHerc0813) at the top —
  the tenth, PHerc0191, predates §10's third pass and prints the 44-point
  curve's 9.82 mm where the shipped file gives 9.98 mm (dated note above).
- `axis_polylines_all_ten.png` — all ten axes on the XZ side
  projection: the hand-placed nodes and the linear interpolation between them,
  which is exactly what a consumer of these files reads. **Re-rendered
  2026-08-20 on the shipped densified curves**: the node counts under each
  cell are the current `control_points` counts, 32 to 64, and its two
  quantities are the current ones — the 19.8 mm of the Motivation section
  (`scripts/axis_stats.py`, PHerc0813; the earlier render printed 20.7 mm,
  which was PHerc0268's, now 19.3) and the ring-gate calibration of §3
  re-measured today — ours 279.9 voxels over 413 points against sean's 273.6
  over 75, marked on the panel as the 2026-08-20 re-run (see §3's dated
  note). **An earlier draft of this panel printed "265 against 274"** — the
  withdrawn three-scroll, pre-finalization figure §3 corrects — and the
  15 August render printed the 268.3-over-279 that §3 carried until today;
  both are replaced, not erased: §3 keeps the full history.
- `annotation_site_PHercNNNN.png` × 3 (PHerc 0191, 0358, 1203) and
  `annotation_site_closeup_PHerc1203.png` — **new.** What the annotator was
  looking at: a crop around an annotated node — ~26 mm, ~38 mm for the close-up
  — with the ring detector's suggestion beside it and the turns traced around
  the point. These carry no statistic. Read the broken lines literally: a
  segment is drawn only where its tangent agrees with the structure-tensor
  lamella direction, and nothing is interpolated across a gap, so the empty
  regions are where the tracer does not hold a sheet, not where there is no
  papyrus. Every column is a height that was actually annotated: all ten of the
  crosses on these four panels are hand-placed control points of the **shipped**
  json, not interpolated values — re-checked and **re-rendered 2026-08-20** on
  the densified curves (an earlier note said the check had not been redone
  against the 19 August files; it now has). What the re-render changed: the two
  PHerc1203 panels came back byte-identical (none of its points moved); on
  PHerc0191 the top column's cross (z = 15480) moved with the second pass's
  12.3 mm re-placement of that node (§10's third pass has since re-placed it
  again, after this render — dated note above), and the tracer holds noticeably less around the
  re-placed point than the first render showed around the old one — that ships
  as it is; on PHerc0358 the middle column now shows z = 8080, because the
  column rule takes the middle of the slice catalogue and the catalogue grew
  during densification — the height shown is still a hand-placed node. The
  original one-column correction from the first render is still described in
  `scripts/README.md`.
- `calibration_summary.png` — our gates against sean's three, all ten scrolls
  (§3). **Re-measured and re-rendered 2026-08-20**: `calib_sean.py` was re-run
  on the shipped densified curves (it still cannot be re-run from a clone —
  it needs the slice PNGs and `ref_sean/`), and the panel now draws the
  413-point re-measurement of §3's dated notes (medians unchanged at that
  precision from the 393-point run). Both halves are computed, not
  copied: the kink bars now match §3's already-recomputed table, and the
  re-measurement moved two of our ten inside sean's kink band where the old
  render had one.
- `prior_1218_agreement.png` — **re-rendered 2026-08-20 on the shipped
  densified curves; see the box above.** §7: our PHerc1218 axis against Iyán
  Dopico's prior annotation. Both axes component by component and looking down
  the scroll; the disagreement along z with §6.4's floors (3.63 mm, and the finer
  ladder's rung, 2.27 mm on the shipped curves — §6.4's dated notes), §6's
  6.26 mm stick distance and the
  Motivation's 19.8 mm all drawn **to scale on the same millimetre axis**,
  each recomputed at draw time rather than typed in — so how small the
  2.00 mm median is against the effect this package
  claims is something to look at rather than a sentence; and the whole
  distribution as an ECDF, because §7 reports a distribution and a panel that
  showed only the median would be reporting less than the section does. It also
  carries the post-hoc CT mass centroid (§7.4) in a third colour, which is the
  panel's real work: the reader can see it lying on *their* line, which is why
  the 2.00 mm is a difference of definition — over most of the height;
  §7.6's z 7500–9500 band is the measured exception, where the difference is
  our error, and the panel predates that arbitration and does not show it. The
  header says in the image, not
  in a caption elsewhere, that the two files are not defined to be the same
  point. `scripts/prior_1218.py --figure`, and every number on it is printed to
  stdout by the same run.

**The two centres, side by side on one image** — `centre_in_core_PHercNNNN.png`
× 3 (PHerc 0191, 0358, 1203), **new on 2026-08-15, re-rendered 2026-08-20 on
the shipped densified curves**. One slice at full
brightness with *both* claimed centres drawn on it — the hand-placed node in
green, the auto-centroid §1 tests against in blue — and the arcs traced from
each of them, in each one's colour, by the same tracer with the same settings.
The question is which centre the laminae actually wrap around, and the reader
answers it by looking, because both crosses are in the same crop.

Everything that could have been tuned to flatter the picture is fixed and
printed on the panel: the slice is the **middle** height of §1's own stack
(index 12 of the 25 in `qc/order_fixture_PHercNNNN.npz`, and on all three
scrolls a hand-placed control point of the json as it stood at the render —
on PHerc0191, z = 15480, that node moved 12.3 mm in the second pass, and the
2026-08-20 re-render put **the green cross where the 44-point file put the
centre**, 8.48 mm from the auto-centroid where the first pass had 16.71.
§10's third pass then re-placed that node again, after the render: the
**shipped** 64-point file puts it 5.62 mm from the auto-centroid, and the
panel has not been redrawn on it (the panels' dated note above).
PHerc0358 z = 11432 and PHerc1203 z = 11632 did not move and their crosses
are the shipped nodes); the crop is the same
43 mm on all three and is centred on the **midpoint between the crosses**, not
on either of them; the tracer runs to the same 22 mm radius around both,
independently of the crop; and the gate — 45 of 360 rays, tangent within 22° of
the structure-tensor lamella direction, coherence ≥ 0.25, over runs of ≥ 30
rays — is in the subtitle. A line is drawn only where the tracer holds a
lamella and is cut where it does not; no circle is ever completed.

**These panels print no count.** Their two numbers are the separation of the
two axes at the drawn height and its median over the stack. Since the
2026-08-20 re-render the at-height separation is **computed from the two
centres actually drawn** — 8.48 / 16.09 / 9.16 mm on PHerc 0191 / 0358 / 1203
— so it cannot drift from the picture (though the drawn PHerc0191 centre is
now itself a render behind the shipped file — 5.62 mm on the third-pass
curve, the dated note above); the stack medians — 13.30 / 13.44 /
6.75 mm — still come from the shipped fixtures, which hold the 15 August axes
(`scripts/order_stat.py` prints them alongside §1's statistic; the fixtures
were not rebuilt and rebuilding them needs the tracer, which does not ship),
and each caption labels the two provenances. The 16.71 mm the earlier render
printed for PHerc0191 was the fixture value at that height and described the
15 August node. The comparison the panels themselves make is visual,
and their captions say so.

**All three ship, including the one that goes against us.** On PHerc0358 and
PHerc1203 the arcs the tracer holds bend and close around the hand-placed node
while nothing goes round the auto-centroid. On PHerc0191, at its own middle
height, it is the other way round: the laminae fold beside the auto-centroid
and the manual axis stands on flat layering. That is worth having in the
package rather than out of it — a slice can hold more than one swirl and the
most visible one need not be the core, which is exactly why the axis comparison
in §1 is made by a neutral method that does not depend on where a crop sits.
The manual axis still wins §1 on PHerc0191, 92% against 83%, and each panel
carries that sentence. (An earlier version of this line called PHerc0191 the
scroll where the manual axis wins §1 *most clearly*. Withdrawn: the widest §1
margin of the three is PHerc0358's, 0.900 against 0.738 — +0.162 against
PHerc0191's +0.093 — and PHerc0358 also has the wider paired count, 8.4×
against 6.1×. The 92/83 figures are unchanged, and no panel ever carried the
superlative.)

(This replaces a rejected figure. Its earlier form drew the two centres in two
*different* crops, so nothing marked where the core was, and printed
"12 segments traced around the cross against 9" — a count produced by no
shipped script, dependent on the crop radius and the gate thresholds. The count
is gone and there is one frame.)

**The winding-order test (§1).**

- `step2_points_PHercNNNN.png`, `step2_stack_PHercNNNN.png` × 3 each — as before.
- `order_map_PHercNNNN.png` × 3 — **new.** The same three neutral-tracing stacks
  with the slice image removed altogether: only the matched arcs, ranked by
  distance from each axis, the auto-centroid row above the manual-axis row.
- `order_bump_PHercNNNN.png` × 3 — **new.** The same arcs as a bump chart, one
  line per arc, a crossing being an order reversal.

Both kinds print the whole-stack figures of §1 — 0.919 / 0.900 / 0.850 against
0.826 / 0.738 / 0.782 and the paired 43:7, 42:5, 21:3 — which
`scripts/order_stat.py` recomputes from the shipped fixtures with numpy alone.
The reversal counts in their subtitles ("3 of 3 pairs", "5 of 10 pairs") are for
the five slices displayed, not for the stack, and the panels say which is which.
**Both kinds also carry the limit §1 states**, in the figure and not in a
caption elsewhere: none of the advantage comes from the axis being per-slice,
and the manual axis frozen at its own stack mean scores identically. A figure
whose title asks whether the axis keeps the order *between* slices must not be
left to imply that per-slice tracking is what does the work, because on these
three stacks it demonstrably is not.

**The four statistics panels (§§6, 5, 2, 1)** — **new on 2026-08-14**, all four
from `scripts/stat_figures.py`, which recomputes every number it draws from the
shipped inputs and prints them, so each panel can be checked as text without
opening the image. Sections 5 and 6 previously had no figure at all.

- `prereg_axis_benefit.png` — §6, **re-rendered 2026-08-20 on the current
  run** (the 15 August render drew +0.1611/+0.0795, 209/252 and the 1.81 mm
  floor against a 6.0 mm stick; those were right for its archived inputs). The
  ten paired per-scroll means with the ten
  pairings drawn one to a row, so "10 of 10" is something to count rather than a
  claim; the pooled +0.1598 against +0.0756 with W = 0.0, p = 0.0020 and 206/256;
  and the bound, which is the panel that matters — the **3.63 mm sensitivity
  floor drawn to scale on the same linear millimetre axis as the 6.26 mm median
  stick distance**, with the finer-ladder rung marked
  beside it (both floors computed at draw time — the finer one from the
  shipped `axis_benefit/finegrid_2026-08-20/` files, by the same rule, which
  puts it at 2.27 mm on the shipped curves; §6.4's second dated note on why
  that rung is drawn but not leaned on) and
  everything below the headline floor shaded as not credited. The re-render
  fixed a hardcoded title that still said "blind below 1.81 mm … median
  6.0 mm" over a drawing whose lines were current — the title is computed
  now. §6.4's
  ceiling is therefore *in* the image: this run credits gross axis placement and
  cannot credit annotation precision. The header says it is not `fit_spiral`'s
  output (§6.2). This is a statistics figure and it is **not** the demonstration
  §6.7 failed to build — that was an unwrap-form picture, a different genre, and
  §6.7's verdict on it stands unchanged.
- `stick_control.png` — §5, both halves, in two panels of the same size. Left:
  all ten scrolls above 50% against both sticks, 188/296 and 184/295, sign test
  p = 0.00098. Right: the **flat dose–response** across the four offset bins
  (0.71 / 0.63 / 0.70 / 0.60 against the mean stick), with 95% Clopper–Pearson
  intervals that show the two small bins carry almost nothing. A figure showing
  only the left panel would be exactly the overclaim §5 exists to avoid, so the
  right panel is the same width and the footer carries §5's own sentence: we do
  not claim the win is because the axis follows the scroll's curvature.
- `shifted_axis_controls.png` — §2's two displacements side by side, same scale,
  same scroll order: **+300 passes** (184/297, 9/10 scrolls, p = 0.011) and
  **+150 is null** (159/297 slices, pooled p = 0.12; 7/10 scrolls, sign-test
  p = 0.17; three scrolls on the wrong side). The two p-values are the two units
  of replication, not two runs — `count_wins.py` prints both from one pass.
  Rates are drawn as stems from the 50% line rather than bars from zero, so a
  scroll below chance points left. Showing the control that failed is the point.
- `frozen_axis.png` — §1's frozen-axis comparison, which until now existed only
  as a sentence. Like everything in §1 it is computed from
  `qc/order_fixture_*.npz`, whose manual-axis centres are the 15 August ones;
  the fixtures are frozen inputs and the panel is exact for them. Left: the live axis, the same axis frozen at its own stack mean,
  and the auto-centroid on one common pair sample — the first two identical to
  the integer count (329/329, 200/200, 221/221). Right: why — the excursion being
  frozen out (1.8–4.1, 1.5–3.3, 3.1–5.1 mm) against the 3–6 mm the metric can
  resolve and the 13.30 / 13.44 / 6.75 mm gap between the two axes.

**Five of the thirty-six regenerate from a bare clone**: the four statistics
panels above from `scripts/stat_figures.py`, and `prior_1218_agreement.png` from
`scripts/prior_1218.py` — the last of these because both files it draws ship,
and so does the raw of its post-hoc CT measurement. All five were re-checked on
a fresh clone on 2026-08-15 and came back byte-identical, and **all five were
re-rendered on 2026-08-20**: the three that read frozen raw files
(`qc/validation_raw.json`, `qc/stick_control_raw.json`,
`qc/order_fixture_*.npz`) came back byte-identical again, and
`prereg_axis_benefit.png` and `prior_1218_agreement.png` — whose inputs, the
ten `axis_benefit/prereg_*.json` and the shipped PHerc1218 axis, changed on
19 August — were replaced by the current renders after being compared with
the old ones (the box at the top of this section says what changed on each).
An earlier version of this paragraph said the two stale renders had been left
in place because nobody had checked a re-render; they have now been checked,
and shipped. Running the two scripts on a clone today reproduces the shipped
files (same matplotlib pin; re-verified 2026-08-20).
`calibration_summary.png` is **not** among them, although `scripts/calib_figure.py`
ships and draws it: its input `qc/calibration_sean.json` holds sean's verbatim
coordinates and is deliberately withheld (`.gitignore` — the package ships only
the twelve-scalar digest `qc/sean_reference.json`), so the script stops at its
first read on a clone. The other thirty do not regenerate from a clone either: they come from three
producers that need the annotation tree — the per-scroll L3 slice PNGs, the
side projections and the tracer — and would be dead code here. On this side
they were re-run on 2026-08-20 against the shipped densified curves for
eighteen of the thirty (the ten axis panels, the atlas, the four
annotation-site panels and the three `centre_in_core_*.png`); the twelve §1
order panels were deliberately left as the 15 August renders, for the reason
the box gives. The three `centre_in_core_*.png` cannot move into the
clone-regenerable group: their at-height separations are computed from shipped
files, but their image is a level-3 slice and their lines come from the
repaired tracer, neither of which is in this repository. `scripts/README.md`
names the producers, says what each draws, and reports the check each
re-render was verified with.

## What is scripted

| number | script | runs on a fresh clone? |
|---|---|---|
| **every number in §6** — the per-scroll table, W = 0.0 / p = 0.0020, the pooled 2.11× and 2.09×, 206/256, the worst-case 206/300 at p = 8.9e-11, the drop attribution 9 / 33 / 39, the control table and the 3.63 mm floor, the 6.26 mm median stick distance, R̄, the three post-hoc variants and the distances between the three placements — and the check that the 300 slice indices are the ones the pre-registered rule gives | `scripts/axis_benefit.py` | **yes** — the ten `axis_benefit/prereg_PHercNNNN.json` ship (1.4 MB with the post-hoc files, the measurement code and the archived 15 August run) |
| **the 20 August finer-ladder rule** — 125 px = 2.27 mm on the shipped curves (it returned 150 px = 2.72 mm on the 19 August curves it first ran on, and §6.4's dated notes say why the rung moves and is not leaned on), and the eleven-rung control table in §6.4's dated notes | no script here; `axis_benefit/finegrid_2026-08-20/` ships the pre-registration, the result document, the summary and the ten per-scroll control outputs | **the rule yes, by hand**: median over per-slice direction-mean drops in q, first rung whose median reaches the pre-registered 0.01 — a numpy loop over the ten shipped `prereg_*_finegrid.json`, re-checked from the shipped copies on 2026-08-20. The measurement itself does not travel, for the same reason as the row below; the original rungs in these files are value-identical to the ten `prereg_PHercNNNN.json` above (1248 of 1248 shared control values since the third pass; 1300 of 1300 before it), which a clone can check |
| **the per-slice q values themselves** | `axis_benefit/measure/prereg_run.py`, shipped verbatim as it ran | **no.** It streams 12–38 MB per slice, about 5.7 GB over the 300, out of the ten masked OME-Zarr volumes named in `axis_benefit/PREREGISTRATION.md` §3, and it imports villa's `umbilicus.py` and `sample_spiral.py` from a `volume-cartographer` checkout, which are referenced by path rather than redistributed. Needs torch; CPU is enough |
| **the unwrap demonstration of §6.7** | **there is none, and that is the finding.** §6.7 gives the selection rule it was built under, the four best candidates and their scores, the Scroll 1 control at 0.094, and why the one legible crop was not shipped. Unchanged on 2026-08-14: the statistics panel below is a different genre and does not revisit that verdict | — |
| **the four statistics panels** — `prereg_axis_benefit.png` (§6, re-rendered 2026-08-20 with §6's current numbers, both floors included; re-running the script on a clone reproduces the shipped bytes), `stick_control.png` (§5, the win and the flat dose–response), `shifted_axis_controls.png` (§2, the +300 that passed beside the +150 that failed), `frozen_axis.png` (§1, the frozen axis and the identical counts) | `scripts/stat_figures.py` | **yes** — it reads only `axis_benefit/`, `qc/validation_raw.json`, `qc/stick_control_raw.json`, `qc/order_fixture_*.npz`, the ten umbilicus files and the ten `PHercNNNN/meta.json`, all of which ship. numpy + scipy + matplotlib. It imports the counting from `axis_benefit.py`, `count_wins.py`, `stick_control.py` and `order_stat.py` rather than reimplementing it, and prints every number it draws. A little over 20 seconds, nearly all of it §1 |
| **every number in §§7.1–7.5** — the overlap, the distance distribution (median 2.00 mm, max 7.20 mm at z = 8608), the 2.20 mm at our own nodes, the 1.42 mm mean offset and the 11% it explains, the verdict against the pre-registered bands, and the post-hoc CT-centroid table (0.25 / 0.24 / 1.20 mm, 550 / 552 / 403 of 553) | `scripts/prior_1218.py` | **yes** — the prior annotation ships verbatim as `qc/prior_umbilicus_PHerc1218_IyanDopico.json` (MIT, sha256 recorded), and `qc/prior_1218_centroid_raw.json` carries the CT measurement. `--fetch` re-downloads the prior file and refuses a hash mismatch, `--check-bucket` re-reads the frame, `--villa DIR` re-runs the interpolation through villa's own loader (it agrees to 0.0000 vox), `--measure-centroid` re-streams the 48 MB. All four are optional |
| **every number in §7.6** — the chain sign-violation counts and rates, the arc-fit distances and residuals, the band counts and the Wilcoxon p, the band-localization rates, the 7.14 mm axis separation at z = 8700 | not in this repository: `checks.py` and `derive1218.py` in the winding-observations working tree | **no, not yet.** The arbitrating inputs are public (the pack's `same_windings.json` / `relative_windings.json`); the checker and derivation are not shipped here, so §7.6 is our measurement on public data, stated with provenance (every number is a tracked entry in our measurement ledger) but not recomputable from this clone. Shipping the checker is the open item |
| **the five frame keys of §8**, and the checks behind them — the voxel size against `samplePixelSize`, the level-0 shape, the in-bounds test and the agreement with each `PHercNNNN/meta.json` `shape_L0` | `scripts/stamp_frame.py` | **no, by design** — it reads the bucket every time. `--check` verifies the ten as they stand and writes nothing; `--write` restamps. Values are never taken from the file being checked |
| 19.8 / 19.3 / 18.4 mm deviations (PHerc0813 / 0268 / 0800, in that order), 36.7 mm sweep, 18.4 mm optimal stick, largest gap 640 vox **and its endpoints z 2944→3584** (PHerc1447; before the PHerc0191 third pass it was that scroll's 1440 vox, z 15480→16920) | `scripts/axis_stats.py` | **yes** |
| **our ten rows** of the §3 kink table — all three columns, the z-spacing of each, and the matched-triple counts | `scripts/axis_stats.py` | **yes** — recomputed on the shipped curves (19 August for nine scrolls, the 20 August third pass for PHerc0191) |
| **sean's three rows** of the §3 kink table, his 61–98 band and his 51–87 matched range (unchanged; his files did not move) | `scripts/axis_stats.py`, `scripts/fetch_sean.py` | **the values yes, the recomputation no.** His files are not ours to redistribute and are not on any public URL we could find (see the correction in §3), so the six numbers of each row ship in `qc/sean_reference.json` with the sha256 of the file they came from, and print marked as such. Supply his files and the script recomputes them and reports whether they agree |
| 184/297, p = 2.3e-05, the clustered p = 0.011, per-scroll table **including the median ratios** (PHerc0800's 0.970), Bonferroni, the 159/297 null at 150 vox | `scripts/count_wins.py` | **yes** — `qc/validation_raw.json` ships, and it too is the 15 August measurement (§2) |
| **the same control re-measured on the final files** (182/297, 158/297, both sign tests unchanged) and the three-slice drift itself | `scripts/snapshot_recheck.py` | **yes** — `qc/validation_final_raw.json` ships. `--measure` needs the slice PNGs |
| **the straight-stick control of §5** — 188/296 and 184/295, all ten scrolls above 50%, sign test p = 0.00098, the per-scroll medians and the displacement bins | `scripts/stick_control.py` | **yes** — `qc/stick_control_raw.json` ships, and it is the 15 August measurement: `--measure` needs the slice PNGs, so §5 was not repeated on the densified curves |
| the banded-energy measure itself | `scripts/validate_axes.py`, `scripts/validate_bands.py` | no — needs the per-scroll slice PNGs |
| bare edges, tissue-band coverage per scroll **and the 92.9% aggregate** (z-weighted; the script also prints the 93.1% unweighted mean and the 94.0% median so the definition is visible) | `scripts/axis_stats.py` | **yes** — the ten `PHercNNNN/meta.json` now ship (25 KB in total; they carry the tissue band, the slice list and the volume id) |
| the ring-gate median displacement (279.9 vs 273.6 on the densified curves, 2026-08-20; 268.3 vs 273.6 on the 15 August curves), the kink figure | `scripts/calib_sean.py`, `scripts/calib_figure.py` | needs the slice PNGs and `ref_sean/`, so not from a clone — re-measured here on 2026-08-20 (§3's dated notes) |
| the shipped axes themselves, from annotator output | `scripts/finalize.py` | needs `results/` |
| **winding pitch 247–371 µm, the 380–468 µm cross-check, the per-spot 6%–90% ratios and the PHerc0800 voxel correction** | `scripts/pitch_table.py` | **yes** — the producer's own five-spot output ships verbatim as `qc/winding_map_metrics.json` and the script applies the voxel correction, taking each spot's voxel size from that scroll's shipped `metadata.source_volume`. The measurement that produced those five pairs (`qc/витковая_карта_код/` in the annotation tree) does not ship |
| **85–92% vs 74–83%, 43:7 / 42:5 / 21:3** | `scripts/order_stat.py` | **yes** — recomputed from `qc/order_fixture_PHercNNNN.npz`, which ships. The *tracer* that produced those fixtures still does not: see the row below |
| **the two axis separations on the `centre_in_core_*.png` panels** — the median over each §1 stack (13.30 / 13.44 / 6.75 mm, the same figures §1 quotes) and the fixture value at the stack's middle height (16.71 / 16.09 / 9.16 mm). Since the 2026-08-20 re-render the panels' own at-height numbers are computed from the drawn centres instead (8.48 / 16.09 / 9.16 mm — PHerc0191 differs because its z = 15480 node was re-placed after the fixtures were built; §10's third pass then re-placed it again after the render, and the shipped file puts it 5.62 mm from the drawn centroid — the panels' dated note) | `scripts/order_stat.py` | **yes** for the fixture values — the same shipped fixtures, whose manual-axis centres are the 15 August ones; it prints them under the order table, with the height's z. The drawn-centre values need the annotation tree's `auto_centers.json`, which does not ship |
| **the `centre_in_core_*.png` panels themselves** | `qc/эвиденс_кандидаты/код/evidence_panels_en.py` in the annotation tree | no — the numbers regenerate here, the picture does not: it needs the level-3 slice PNGs and the repaired tracer. The panels print **no count**, so nothing on them depends on that tracer being trusted for a quantity |
| **the tracing that produces the fixtures** | **not shipped here.** `qc/шаг2_код/stack.py` (31 KB) plus `winding_map.py` (12 KB) and `numbering.py` (6 KB) from the same tree | no. Stated exactly, because "too big to ship" would not be true: the missing *data* is **14.6 MB** — 25 L3 slices for each of PHerc0191/0358/1203, each one plane `round(z/8)` of level 3 of that scroll's `…-masked.zarr` in `vesuvius-challenge-open-data`, normalised to the 1st/99th percentile of its non-zero pixels, exactly as `build.py` writes the catalogue slices. What blocks it is the ~49 KB of tracer code: it is Russian-commented, hard-wired to the annotation tree, and shipping it means proving it still regenerates the published numbers rather than merely running. We re-ran it on 2026-08-13 and it does (all nine figures exact), but translating and de-hardcoding it is a separate pass |
| **the tolerance sweep and the resampling test** | **not shipped here.** Produced by `qc/эвиденс_кандидаты/код/развилка/развилка3.py` in the annotation tree; every number and its provenance is tabulated in `STEP2_CONSISTENCY.md` §13 | no |
| **19/22 on PHerc0358** | **no script, journal-documented** | no |
| **the midpoint audit** — the leave-one-out and estimated-midpoint tables, the 194-of-403 count on the shipped curves (188 of 383 on the 19 August curves) and the worst-interval list | `scripts/midpoint_audit.py` | **yes** — it reads only the ten shipped json. The "before" column of that section's table is the same script on the 15 August files, which are in git history at `HEAD~1` |
| **the paired old-versus-new comparison in the dated 19 August section** — 198 paired slices, 112 unmoved, the Wilcoxon p = 0.93 / 0.17 / 1.00, the 28-against-22 above the floor, and the 0.0003-against-0.0045 pooled fall | **no script; it is a comparison of two shipped result sets, not a measurement** | **yes, by hand from what ships.** Both sets are in the repository — `axis_benefit/prereg_PHercNNNN.json` and `axis_benefit/superseded_2026-08-15/prereg_PHercNNNN.json`. Join them on `z_L0` within each scroll, keep the slices flagged `scorable` in both, and read `centres.annotated` (times `um_per_px`, ÷ 1000, for millimetres) and `conditions.annotated.q` / `conditions.stick_mean.q`. Every number in that section is a numpy line over those two files. Since the PHerc0191 third pass the current side of the join is the 20 August file, so this recipe returns the figures in that section's closing dated note rather than the 19 August ones printed above it |

`scripts/README.md` lists the known rough edges in the scripts themselves.

**One row of this table is worth reading twice.** Three of the checks in this
package — §2, §3 and §5 — could not be re-measured on the 19 August curves
from a clone, because all three need the per-slice PNGs or sean's files and
neither ships. §3's ring-gate calibration has since been re-measured on our
side (2026-08-20, twice — on the densified curves and again after the third
pass; its dated notes carry the values); **§2 and §5 still have not been**,
and their numbers describe the
279-point axes. §6, §§7.1–7.5, the geometry table and the midpoint audit all
recompute from what ships and all were repeated; §7.6's arbitration does not
recompute from a clone, and its table row says so. Where a section could not
be repeated it now says so in its own words rather than leaving the date to be
inferred.

## Honest caveats
- Collapse zones (chevron-folded interiors) are best-effort judgement;
  PHerc0268 is crushed almost throughout. Note that PHerc0268 is also the scroll
  carrying the second-largest deviation, 19.3 mm, and the largest sweep, the
  Motivation's 36.7 mm, and that on the one column of §3's
  smoothness table that compares like with like it is now **the roughest of all
  thirteen axes there, ours and sean's — 544 against sean's 51–87** (an earlier
  version of this README quoted 469 here, which was an artifact of resampling
  and is withdrawn in §3; the second pass gave the scroll matched-spacing
  triples for the first time and the honest value they yield is worse than the
  artifact was). So the largest sweep figure in this package, and its
  second-largest deviation, rest on its weakest annotation. (An earlier version
  of this caveat said PHerc0268 carried "the headline 19.3 mm number" and
  called PHerc0800 the second-largest deviation. Since the Motivation
  superlative was corrected, the headline deviation is 19.8 mm and belongs to
  PHerc0813 — `scripts/axis_stats.py`: 0813 19.8, 0268 19.3, 0800 18.4 — so
  PHerc0800 is third, and the caveat is restated from that ordering rather
  than deleted.) The third-largest deviation, PHerc0800 at 18.4 mm, makes
  the same several-scrolls point without leaning on PHerc0268 at all. Its
  tissue-band coverage is no longer
  the worst of the ten — the second pass extended its annotated range from
  z 5320 to z 2680 and took it from 69% to 94% — and the lowest is now
  PHerc1545 at 88%.
- Bare edges: PHerc1545 top 1624 vox, PHerc1218 bottom 1192 vox,
  PHerc1447 608/608, PHerc0800 568/568 and PHerc1218 top 584 vox carry no axis;
  interior gaps after finalization do not exceed 640 vox (PHerc1447,
  z 2944→3584; before the PHerc0191 third pass the largest was that scroll's
  1440 vox at z 15480→16920). Coverage of the tissue band runs 88–94%, 92.9% overall.
  (On the 15 August curves this read: PHerc0268 bottom 2952, PHerc0800
  1152/1160, gaps to 2400 vox, coverage 69–94% and 90.6% overall. The second
  pass improved every one of those figures, which is the one thing in this
  README that it unambiguously did improve — and it is a statement about
  coverage, not about accuracy.)
- Three slices excluded as undeterminable (PHerc1545 z=19056; PHerc0191
  z=15960, z=16440).
- Winding pitch at five readable spots is **247–371 µm** by FFT (locally
  separated sheets); tightly wound regions sit at the L3 Nyquist limit. An
  independent ridge-interval cross-check at the same five spots gives
  **380–468 µm** — 6% to 90% higher place for place — and it is quantised: the
  cross-check returns exactly 5.5 px at L3 at three of the five spots, which is
  411.9 µm on the two 9.362 µm scrolls and 380.1 µm on PHerc0800, whose voxel is
  8.640 µm. We quote the FFT range and we are not treating the cross-check as
  independent confirmation to micrometre precision. **Correction:** an earlier
  version of this README gave that range as 393–468 µm and called 411.9 µm "the
  value returned at three of the five spots". Both statements carried PHerc0800
  at the wrong voxel size — the demo pipeline assumed 9.362 µm for every scroll.
  Converting it (× 8.640 / 9.362) moves its cross-check from 411.9 to 380.1 µm
  and its FFT value from 358 to 331 µm; the FFT range 247–371 is set by
  PHerc0191 and PHerc0358, both 9.362 µm scrolls, and is unaffected.
- These five are **local** pitches, measured exactly where the laminae have
  separated far enough to be readable at L3, which is why they are larger than
  the 180–225 µm bracket our own pitch work gives for tightly-wound material;
  a contribution from the second harmonic (stuck-together sheet pairs) is also
  possible. Read 247–371 µm as "the pitch at these five spots", not as the
  winding pitch of these scrolls. The consequence for the Motivation section is
  conservative in the direction that matters: at a finer true pitch, 19.8 mm of
  lateral error would cross *more* windings than the 53–80 quoted there, not
  fewer.
- The shifted-axis control ran on a snapshot slightly older than the final
  files: 18/297 slices carry points that were later dropped at finalization,
  and three PHerc1545 points were moved (≤260 vox) after the control run.
  Winding-map numbers were computed on the final files. The calibration in §3
  now runs on the final files too — it did not in the earlier version of this
  README, which is why that number changed. **All of §2 is nonetheless a
  15 August measurement**: `qc/validation_raw.json` is that run's raw and
  re-measuring needs the slice PNGs, which do not ship, so this control has not
  been repeated on the densified curves. **The cost of that staleness is now
  measured rather than left open**: re-running the control on the final files
  changes the measured value on 3 of 297 slices, moves 184/297 to 182/297 and
  159/297 to 158/297, and leaves both scroll-level sign tests identical. See §2
  and `scripts/snapshot_recheck.py`. The straight-stick control of §5 was
  measured on the final files from the start.
- **The one external check covers one scroll, and we do not pass it.** §7
  compares us against an
  independent annotation on PHerc1218 and nowhere else, because nowhere else is
  there one. The nine other axes in this package have never been checked against
  anybody but ourselves. That is a limit of the field's data, not a claim we can
  argue around, and the 2.00 mm of §7 says nothing about PHerc0268 or any other
  scroll. Since 2026-08-20 there is a second half to this caveat: on the one
  scroll where the check exists, third-party observations arbitrate the
  z 7500–9500 band against our axis, by up to about 7 mm (§7.6). The shipped
  PHerc1218 axis is thereby the one file in this package known to be wrong
  somewhere — which is more than can be said, in either direction, about the
  other nine.
- **The frame keys follow an unmerged PR.** §8's five `metadata` keys track
  ScrollPrize/villa#1454 at commit `85c5be1`. That PR is open, and its schema has
  already changed once under review. The keys are optional and additive, so
  nothing breaks if it changes again, but this package does not claim
  conformance to a merged standard and the wording should not drift into
  claiming it.
- **The ten json files are no longer byte-identical to `da52f97`.** That
  invariant was retired deliberately at the commit that added the frame keys, the
  diff is those five lines and nothing else, and both md5s of every file are
  tabulated in §8. Every measured number in this README predates the stamp and is
  unaffected by it. The md5 table in §8 is a further round out of date: the
  second and third annotation passes rewrote the ten files with 413 points in
  place of 279,
  so neither column of that table is the current hash of anything. It is kept
  because its purpose was to make the *pre-stamp* files identifiable, and it
  still does that.
- **The second annotation pass bought no measurable accuracy on any instrument
  in this package.** §6 was repeated on the densified curves and returns a null
  on the change (dated section above: 112 of 198 paired slices with the axis in
  exactly the same place, scroll-level p = 1.00, 28 better against 22 worse
  among the slices that moved past the floor). The pooled ratio rose from 2.03×
  to 2.09× and that rise is the straight-stick baseline getting worse, not our
  axis getting better. (The third pass took it further, to 2.11× — and that
  last step is mostly PHerc0191's own axis improving, which §10 measured
  before shipping and quotes as leaning positive, not significant, p = 0.084 —
  so this caveat's subject remains the second pass.) §6.4's sensitivity floor
  went the wrong way, from 1.81 mm
  to 3.63 mm (a finer, separately pre-registered ladder run on 20 August adds
  rungs there; its answer sits on the 0.01 threshold's knife edge and moved a
  rung within the day — 2.72 mm on the 19 August curves, 2.27 mm on the
  shipped ones — so §6.4's dated notes quote the bracket rather than the rung,
  the doubling was ladder resolution rather than the annotation degrading, and
  3.63 mm remains the headline until the finer run is externally reproduced).
  The pass demonstrably improved coverage and the interpolation
  audit; it has not been shown to have improved the axis, and this package has
  no measurement that could show it.

### 10. Third pass on PHerc0191, and the §1 fixture dispute resolved by measurement (2026-08-20)

PHerc0191 was re-annotated on 20 August: **44 → 64 hand-confirmed points**, none
removed, with the additions concentrated where the axis bends hardest — six of
the largest moves fall between z = 14040 and z = 15480.

**The pre-registered concentricity measure was run on the new curve before it was
shipped**, on the same 30 slices, same code, same conditions as the run behind
§6 (`axis_benefit/measure/prereg_run.py`, `--no-control`). It improves:

| | mean q | median q | better on |
|---|---|---|---|
| shipped (44 points) | 0.1386 | 0.1353 | — |
| this pass (64 points) | **0.1448** | 0.1339 | **19 of 30 slices** |

Paired difference +0.0062 mean, Wilcoxon p = 0.084 — leaning positive, not
significant at 0.05, and quoted as such. Interpolation roughness improves
separately: the estimated midpoint miss falls from a median of 438 µm to 354 µm.

**§1's dispute closes.** That section carries a dated box recording a **12.3 mm**
disagreement at z = 15480 between its frozen fixture and the shipped file. This
pass moved z = 15480 by 9.5 mm and z = 15240 by 13.5 mm, and the nearest measured
slice, z = 15400, improves from q = 0.0241 to **0.1027** — the largest gain in the
run. The disagreement was the shipped file being wrong there, and it is now
measured rather than argued.

**One regression, stated because it is real.** At z = 13912 the measure falls from
0.1909 to 0.0759, the largest single change in either direction. That slice is
not a control point in either version; it is interpolated between z = 13560 and
z = 14040, and that 480-voxel gap is the widest in this scroll and one the
midpoint audit had flagged. Moving the endpoint at z = 14040 helped elsewhere and
hurt here. The fix is a control point inside that gap, and it has not been placed
yet.

### 11. Allowing more than one axis beats forcing one, measured (2026-08-20)

Section 9 records that PHerc0268 is split by a fissure and that the halves have
separate winding centres. This section is the measurement that followed, and it
is about the modelling choice rather than about the number two: **where a scroll
is delaminated, letting the annotation carry more than one axis scores better
than making it carry exactly one.** The band tested here happens to present two
centres; N is a property of the band, not of the method, and the third-pass
annotation already suggests further centres elsewhere on this scroll that have
not been measured.

**The data.** A third annotation pass produced two axes that *overlap* in z
rather than abut: one covering z 2680–6312, the other 5560–12584. On the
overlap, 13 annotated slices carry two independently placed centres for the same
slice.

**The measure** is the one used everywhere else in this package —
`axisdemo.radial_anisotropy_sectored`, frozen at pre-registration time, imported
rather than reimplemented, same annulus rule, same 95 % ring-coverage condition.
Each slice was scored at three centres: each of the two axes, and the single
axis this repository ships.

| centre | mean q | median q |
|---|---|---|
| axis A | **0.0659** | 0.0744 |
| axis B | 0.0510 | 0.0522 |
| the single shipped axis | 0.0396 | 0.0349 |

**Better of the two axes against the single one: +0.0391 mean, winning on 12 of
13 slices, Wilcoxon p = 0.0105.** The single axis is worse than *either* axis
taken alone, which is the shape a compromise between two true answers has.

Which axis wins moves up the scroll: B from z 5648 to 5816 (0.0687 against
0.0349 at z = 5816), A from z 6144 to 6312 (0.1236 against 0.0146 at z = 6312).

**The one exception, stated because it is unexplained.** At z = 5984 the shipped
single axis wins outright, 0.1070 against 0.0508 and 0.0260. Either a third
centre sits there — the annotator reports seeing more than two in this band — or
the old point happens to fall well. We do not know which.

**What this does not establish.** The measure integrates a full annulus around
each centre, so material from the other domain is inside it either way and
dilutes both axes.

> **Dated, 2026-08-20, later the same day — the stricter measure was run, and it
> halves the gap rather than widening it.** With each centre scored only over its
> own domain — pixels assigned by nearest centre, the rule checked against the
> traced fissure at z = 6144, where the two partitions agree on 85.4 % of pixels
> and give the same verdict — the two-centre model still beats the single axis on
> **12 of 13 slices, Wilcoxon p = 0.0134**, but the mean gap falls from **+0.0391
> to +0.0208**. The reason is a property of the statistic above rather than of the
> scroll: the annulus comparison allowed itself *the better of the two axes* on
> every slice, a per-slice maximum that inflates by selection, and the strict
> comparison has nowhere to hide it — which axis serves which domain is fixed by
> geometry before any score is seen. Removing that freedom cost about half the
> apparent advantage, and what remains is the part that survives with nothing left
> to pick.
>
> The stricter measure also **localizes** the failure. The single shipped axis
> serves the upper domain about as well as the upper branch does (+0.0115, 7 of
> 13, p = 1.0); it is the lower domain it abandons (+0.0567 for the lower branch,
> 10 of 13, p = 0.0266, with the shipped axis scoring negative above z = 6144).
> The z = 5984 exception above persists and is still unexplained.
>
> A matched null was run and is clean: above the band, where the section has a
> single centre, a fake second centre placed at the same 22.8 mm separation is
> **punished, not flattered** — mean −0.0463, one win in nine, and three of
> sixteen configurations refused outright by the pre-registered ring rule. So the
> per-domain construction does not manufacture two-centre advantages. Working:
> `SECTOR_Q_2026-08-20.md`, ledger keys `umb.sectorq.*`. Thirteen slices, one band, one scroll. And the result says
nothing about which surface patch belongs to which axis, which is the question a
tracer actually has to answer.

Working script: `axis_benefit/measure/branch_q.py` in the working tree, output
`branch_q_PHerc0268.json`; neither ships here yet.

### 9. PHerc0268 carries two winding centres between z = 5400 and 6224 (2026-08-20)

Found by eye during a third annotation pass on 20 August, then measured. In that
band the axial section is cut by a fissure into an upper and a lower region, and
each region has its own winding centre. Both are plausible centres; neither is
the centre of the other's coil.

The consequence is not cosmetic. The axis enters the band from the lower region
— around (5100–5230, 5470–6570) below z = 5320 — and leaves in the upper one,
around (6300–6410, 4045–4230) above z = 6312. Any annotation that walks one
branch and then continues on the other records a step of **16.3 mm sideways
across 0.07 mm of height** (measured between the z = 6144 and z = 6152 points of
that pass, a rate of 236 mm per mm). `json_umbilicus_z_to_yx` interpolates
linearly between consecutive control points, so a consumer reading such a file
draws the axis straight across papyrus where no axis is, and nothing warns it.

**What this repository ships.** One axis per scroll, single-valued in z, as the
format requires — so the shipped PHerc0268 file follows a single branch and does
not cross. The second branch is a real feature of this scroll and is not
representable in sean's format, which is a single `control_points` polyline read
through a single-valued loader; recording it needs either a second file or an
extension to the format. Neither is shipped yet, and until one is, **the shipped
PHerc0268 axis is the dominant branch and not a statement that the other does not
exist.**

**Why it matters beyond this scroll.** A delaminated band is exactly the place an
automatic tracer changes branch without noticing, and the resulting axis looks
well-formed. This is one measured instance, on one scroll, found by a human
looking at slices; we have not surveyed the other nine for the same thing.

## Format compatibility
Field-for-field against sean's three files: top-level keys identical and in the
same order; per-point keys `x, y, z, score` identical and in the same order; all
coordinates integer on both sides; `score: 100` on every point on both sides;
`z_grid_spacing: 0` is sean's own convention; `min_score_threshold` and
`high_score_threshold` both 0.75. Our `metadata` is an exact superset of his,
adding `source_volume`, `annotator_note` and the five frame keys of PR
villa#1454 at commit `85c5be1` — `volume`, `voxelsize_um`, `volume_width`,
`volume_height`, `volume_slices` (§8). Those five are optional in that PR's
loader and unknown to every consumer that predates it, so the files still read
as before wherever they are not understood.

Against the prior PHerc1218 annotation (§7) the format differs and neither side
is wrong: it is a bare `{"control_points": [{z, y, x}]}` with float coordinates,
no `score` and no `metadata` block, which is the minimum villa's json loader
accepts. Both parse through `json_umbilicus_z_to_yx` without special-casing.

## Files
- `PHercNNNN_umbilicus.json` × 10 — the axes.
- `panels/axis_PHercNNNN.png` — each axis drawn on its scroll.
- `panels/axis_polylines_all_ten.png` — all ten axes as node polylines on the
  XZ side projection, with the §3 calibration numbers.
- `panels/annotation_site_PHerc{0191,0358,1203}.png` and
  `panels/annotation_site_closeup_PHerc1203.png` — the annotation site itself:
  crop, detector suggestion, and the turns traced around an annotated node.
- `panels/centre_in_core_PHerc{0191,0358,1203}.png` — one slice with both
  claimed centres on it and the arcs traced from each, in two colours: which
  centre the laminae wrap around, judged by eye. No count is printed; on
  PHerc0191 the picture goes against us and ships anyway.
- `panels/step2_stack_*.png`, `panels/step2_points_*.png` — the winding-order
  test on PHerc 0191, 0358 and 1203.
- `panels/order_map_*.png`, `panels/order_bump_*.png` — the same three stacks
  drawn without the slice image, and as a bump chart of arc rank.
- `panels/calibration_summary.png` — our gates calibrated against sean's three
  published umbilici, all ten scrolls.
- `panels/prereg_axis_benefit.png` — §6 as statistics: the ten pairings, the
  pooled result, and the 3.63 mm sensitivity floor (with the finer-ladder
  rung of §6.4's dated notes beside it, 2.27 mm on the shipped curves) drawn
  to scale against
  the 6.26 mm median stick distance that bounds what the run may claim.
  Re-rendered 2026-08-20 on the current run.
- `panels/stick_control.png` — §5 in both halves: the win on all ten scrolls, and
  beside it the flat dose–response across the offset bins.
- `panels/shifted_axis_controls.png` — §2's two controls together: the +300 that
  passed and the +150 that failed, same scale, same scroll order.
- `panels/frozen_axis.png` — §1's frozen-axis comparison: the manual axis frozen
  at its own stack mean scores identically to the live one, and the distances
  that explain why.
- See the "Panels" section above for what each one shows and what regenerates it.
- `STEP2_CONSISTENCY.md` — the full evidence behind the winding-order test,
  including the results that go against us.
- `qc/validation_raw.json` — the raw per-slice measurements of the shifted-axis
  control, so §2 can be recomputed without rebuilding anything.
- `qc/validation_final_raw.json` — the same control re-measured on the final
  shipped files, so the disclosed snapshot drift can be sized (§2).
- `qc/stick_control_raw.json` — the raw per-slice measurements of the
  straight-stick control (§5).
- `qc/order_fixture_PHercNNNN.npz` × 3 — the traced arcs and the two axes'
  centres for the three winding-order stacks, so §1's headline statistic can be
  recomputed without the tracer.
- `qc/sean_reference.json` — sha256 and derived smoothness numbers for sean's
  three reference umbilici, which are not redistributed here (§3).
- `qc/prior_umbilicus_PHerc1218_IyanDopico.json` — the prior PHerc1218
  annotation, redistributed verbatim under its MIT licence so §7 runs from a
  bare clone. **Not our file.**
- `qc/prior_umbilicus_PHerc1218_SOURCE.md` — where it came from: repository,
  commit, path, bytes, sha256, git blob sha1, its generator, its licence notice
  reproduced, and what its points are.
- `qc/PRIOR1218_PREREGISTRATION.md` — the specification of §7, written and
  hashed before `scripts/prior_1218.py` was first run; its sha256 is in §7.2.
- `qc/prior_1218_raw.json` — §7's per-sample distances, so the distribution can
  be recomputed without re-reading either polyline.
- `qc/prior_1218_centroid_raw.json` — the post-hoc CT mass-centroid measurement
  of §7.4 (level 5, 727 slices), so that table does not need the network.
- `panels/prior_1218_agreement.png` — §7 as one figure: both axes, the
  disagreement against this package's own yardsticks to scale, the whole
  distribution, and the CT centroid that explains the residual.
- `axis_benefit/PREREGISTRATION.md` — the specification of §6, fixed in writing
  before any comparative quantity existed, shipped verbatim.
- `axis_benefit/prereg_PHercNNNN.json` × 10 — the per-slice results of §6: for
  every one of the 300 slices, the q of each axis and of every control
  displacement, with the pixel counts, ring coverage, the stick's displacement in
  µm and villa's R̄. `scripts/axis_benefit.py` recomputes §6 from these. These
  are the **19 August** measurement on the densified curves for nine scrolls;
  `prereg_PHerc0191.json` is the **20 August** measurement on the third-pass
  curve (§10 — the 19 August file it replaced is in git history).
- `axis_benefit/superseded_2026-08-15/prereg_PHercNNNN.json` × 10 — the same ten
  files from the **15 August** run on the 279-point curves, kept in-tree rather
  than deleted so that the two runs can be compared. They are what the earlier
  numbers in the git history of this README were computed from, and what
  `panels/prereg_axis_benefit.png` drew until its 2026-08-20 re-render.
- `axis_benefit/finegrid_2026-08-20/` — the finer sensitivity-ladder run of
  §6.4's dated note: `FLOOR_FINEGRID_PREREGISTRATION.md` (verbatim, written
  before the run), `FLOOR_FINEGRID_RESULT.md` (verbatim except one shortened
  local path; original sha256s are quoted in §6.4), `floor_finegrid_result.json`
  and the ten `prereg_PHercNNNN_finegrid.json` control outputs, whose
  `umbilicus` field is rewritten to `<repo>/` and which are otherwise as the
  runner wrote them. The headline 3.63 mm floor recomputes
  from these and from `axis_benefit/prereg_PHercNNNN.json`; the finer rule on
  the shipped copies returns 125 px = 2.27 mm since the PHerc0191 third pass,
  while the result document and the summary json are kept verbatim from the
  19 August-curve run and record 150 px = 2.72 mm (§6.4's dated notes).
  PHerc0191's control output is the 20 August re-run on the third-pass curve.
- `axis_benefit/prereg_PHerc0813_posthoc_{eye,drop,argmax}.json` and the three
  corrected `PHerc0813_posthoc_*.json` they were run from — the post-hoc variants
  of §6.6. These are **not** the published annotation; the shipped
  `PHerc0813_umbilicus.json` is untouched. They are corrections of the
  **29-point 15 August** PHerc0813 file and were not re-made for the 49-point
  file that ships, which is why §6.6 compares them against that run's +0.0906
  and not against the current +0.1150.
- `axis_benefit/measure/` — the measurement code of §6 as it ran. It does not run
  from a bare clone (§6.9); it is here so the method is inspectable.
- `qc/winding_map_metrics.json` — the winding-map measurement's own output for
  the five readable spots, copied verbatim from the annotation tree, so the
  pitch numbers in the caveats have a source (`scripts/pitch_table.py`).
- `PHercNNNN/meta.json` × 10 — the annotation catalogue's own metadata for each
  scroll: source volume, level-3 frame, tissue band, and the list of annotated
  slices. 25 KB in total, shipped verbatim from the annotation tree so that the
  coverage and bare-edge numbers recompute from a bare clone. (These are the
  only shipped files that still carry a Russian sentence, in their `note`
  field; they are shipped byte-for-byte as the scripts read them rather than
  retyped.)
- `requirements.txt` — the versions every number here was produced or
  re-verified with.
- `scripts/` — QC gates, finalization, and the validation scripts behind the
  numbers above (`qc_gates.py`, `finalize.py`, `validate_axes.py`,
  `validate_bands.py`, `count_wins.py`, `calib_sean.py`, `calib_figure.py`,
  `axis_stats.py`, `qc_sheet.py`, `order_stat.py`, `stick_control.py`,
  `snapshot_recheck.py`, `fetch_sean.py`, `pitch_table.py`,
  `axis_benefit.py`, `stat_figures.py`).

The annotator itself is a small web page; happy to share it on request.

---

## Note added 23 August 2026 — two uncited figures in this README

*Appended by a sweep of every number in this repository's prose that carries no
provenance citation. Nothing above this line is edited except by the citations
added to the point totals in the second-pass section.*

The densification totals now cite the ledger records that hold them: 279 before
the 19 August pass, 393 after it, 64 on PHerc0191 after the 20 August third
pass, and 413 shipped. Two numbers on this page still do not, and are named
here rather than left to look maintained:

* **"took PHerc0191 from 44 to 64"** — the 44 has no record. It is recoverable
  from this repository's own git history, which is where the 279 figure came
  from; that has not been done here, so the 44 is a transcription until it is.
* **"the mean of its own 25 centres over the stack"**, in the frozen-axis
  control of section 1 — this cannot be reconciled with the point counts
  elsewhere on the page, and there is no record or script output behind it. The
  control's *result* is unaffected: freezing the axis at its stack mean is
  defined without reference to how many centres the mean was taken over, and
  the table beside the sentence carries the scores. But the specific count "25"
  is not supported by anything findable today, and until the control is re-run
  it should be read as "its own centres" with no number attached. Stated here
  rather than corrected, because guessing a replacement would be worse than
  saying it is unknown.
