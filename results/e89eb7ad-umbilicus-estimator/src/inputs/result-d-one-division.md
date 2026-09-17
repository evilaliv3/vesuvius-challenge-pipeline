# One division. `normalgridtools.cpp:116`

Date: 2026-09-15. Criterion: that of the pre-registration of variant C, written the same day at
14:17:39.

---

## In three lines

1. **The responsible person was right, and the coordinator's suspicion was the right one.** The line
   `return score/wsum;` (`normalgridtools.cpp:116`) is what destroys the interior maximum of the
   objective function. Removing it, **and touching nothing else**, repairs the estimator.
2. **Measured on their compiled code**: on the slice that diverged to four million pixels, with that
   one line changed the answer comes back to 200 px from the true axis. Zero estimates outside the
   volume on all four scrolls, against 22, 13, 9 and 0 out of 24 before.
3. **And it wins by the criterion written beforehand**: it beats the centroid on three scrolls out
   of four with margins of 0.80, 1.37 and 0.41 mm, and on the fourth it does not reach twice. It is
   the first estimator that has ever beaten the baseline our own paper declares unbeatable.

---

## 1. Why that division breaks everything

The refined score of `cpp:98-117` is

```cpp
score += (cos_angle * cos_angle) * weight;   // weight = 1/max(100, dist)
wsum  += weight;
...
return score/wsum;
```

Without the division it is a **weighted sum**: when the candidate moves away, every weight tends to
`1/D`, so the sum tends to zero. A positive, continuous function that tends to zero at infinity
**has a maximum at a finite distance by construction**.

With the division it is a **weighted mean**: numerator and denominator go to zero together, and the
limit is the plain mean of the `cos^2`, which stays high. A mean does not know **how many** normals
are contributing, a sum does. From far away few normals really contribute, but those few agree
well, so the mean stays high while the sum collapses.

The interior maximum is therefore not a property the objective has by chance: it is a property the
sum always has and that the division takes away.

## 2. The evidence that says so, one variant at a time

**RUN**, `float64`, same slices, same table of local maxima as before, run by the script that
scores the variants side by side.

| slice | M, mean (villa) | **W, sum without the division** | S, unweighted sum |
|---|---:|---:|---:|
| PHerc0332 z=3039 | 0.3 mm, interior | **0.1 mm, interior** | 0.3 mm, interior |
| PHerc0125 z=2140 | 0.7 mm, interior | **0.8 mm, interior** | 0.7 mm, interior |
| PHerc0826 z=8000 | **40.3 mm, on the edge** | **2.8 mm, interior** | 40.3 mm, on the edge |
| PHerc0125 z=6891 | **38.2 mm, on the edge** | **3.1 mm, interior** | 40.8 mm, on the edge |

On the two slices where the mean sends the maximum to the edge at 38 to 40 mm, the sum puts it at
2.8 and 3.1 mm from the true axis. And the unweighted sum, that is villa's other score, the one of
`cpp:87` that chooses the seed, repairs **nothing**: it is precisely the combination of weight plus
sum that does it.

## 3. On their compiled code, with one line changed

**RUN.** Copy of `core/src/normalgridtools.cpp` with line 116 alone modified, compiled and run with
the same driver as before. The rest of the file is not touched.

**PHerc0125 xy 6891**, true axis about (4320, 4345), grid 8387 by 8387:

| | run 0 | run 1 | run 2 |
|---|---|---|---|
| original | (325,674, minus 3,792,262) | (350,742, minus 4,082,684) | (405,676, minus 4,822,970) |
| **line 116 without the division** | **(4560, 4248)** | **(4539, 4400)** | **(4644, 4086)** |

**PHerc0826 xy 8000**, true axis about (3323, 4297):

| | run 0 | run 1 | run 2 |
|---|---|---|---|
| original | (3050, minus 272) | (3076, minus 250) | (3060, minus 347) |
| **without the division** | **(3084, 4782)** | **(2887, 4391)** | **(3035, 4751)** |

## 4. The table on the four scrolls, and the verdict

Median in millimetres, 24 slices per scroll, the bench's metric.

| scroll | B faithful | C corrected | **B without the division** | **D corrected and without the division** | centroid |
|---|---:|---:|---:|---:|---:|
| PHerc0125 | 138.03 | 39.97 | **1.68** | 1.71 | 2.48 |
| PHerc0211 | 66.62 | 37.77 | **1.46** | 1.27 | 2.83 |
| PHerc0332 | 0.35 | 0.35 | **0.36** | 0.36 | 0.77 |
| PHerc0826 | 38.57 | 35.08 | **5.55** | 6.19 | 4.27 |
| estimates outside the volume | many | 22/13/9/0 | **0 everywhere** | **0 everywhere** | n/a |

### Verdict by the criterion written beforehand: **it wins**
- it beats the centroid on **3 scrolls out of 4**: PHerc0125, PHerc0211, PHerc0332;
- margins **0.80, 1.37 and 0.41 mm**, all above the threshold of 0.30;
- on the fourth, PHerc0826, it stands at 5.55 against 4.27, that is **1.30 times**, well below
  twice.

### The thing that surprises, and that simplifies the report upstream
**The repairs of the search are of no use.** `B without the division` keeps the whole of villa's
structure (search without bounds, update inside the 3x3 loop, two different objectives) and reaches
1.68 / 1.46 / 0.36 / 5.55, that is **as much as or better than the version rewritten from scratch**.
A well posed objective makes even a sloppy search converge, and the estimates outside the volume
disappear by themselves.

So there is no rewrite to propose: **there is a division to remove.**

### Robustness with respect to the seed, declared outside the criterion
Three different seeds on two scrolls: PHerc0125 1.53 / 1.71 / 1.85 (spread 0.32 mm), PHerc0826
5.75 / 6.19 / 6.27 (0.52 mm). The margin on PHerc0125 holds with all three.

## 5. What is retracted of what I wrote this morning

This overturns the conclusion of the report written earlier the same day, at 14:22, and it goes
said and not hidden.

- **Retracted**: "the objective is the problem, and we know it by elimination". False. The objective
  is right; one division was breaking it.
- **Still true**: that the weighted mean has no interior maximum, that C ended on the edge, that the
  errors of realisation were worth up to 98 mm. They were right measurements on an incomplete
  premise.
- **My error**: I had read `score/wsum` as a design choice and had kept it in C precisely because I
  did not want to "change the idea". It was instead the one point where the intention and the
  writing diverged, and it is the point I left intact.

## 6. What it is worth

The umbilicus is the input the spiral fitting cannot leave out, and it has to be estimated for
nineteen scrolls out of twenty-three. Until today our paper said that no estimator beats the
centroid. This one beats it, on three scrolls out of four, and the repair needed upstream is **one
division removed from one line**.
