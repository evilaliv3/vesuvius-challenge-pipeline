# A Far Field Attractor in the Umbilicus Score of Volume Cartographer

The umbilicus estimator of Volume Cartographer scores a candidate centre with a weighted sum of squared
cosines divided by the sum of the weights, a weighted mean. We show that the limit of that mean far
from the section is the largest eigenvalue of the normals' covariance. Where this limit exceeds the
score on the axis, the hill climb walks out of the volume. The published estimate leaves the grid on
135 of 360 slices, and 134 of those meet the condition. Without the division the score is a weighted
sum, with a maximum at finite distance. The change is one line, now merged into the challenge's code.
On a run of 24 scrolls it keeps 576 of 576 slices inside the grid, against 350 as published. Only 2 of
its four registered criteria pass, so the run does not show that the change generalises. Against the
centroid of the sheet mask, by a margin fixed in advance, the sum wins on 8 of 10 third party
references, out of sample. It costs a bias towards the denser side. The error of the hand references
remains unmeasured, and we do not claim that the weighted sum is the right objective.

```
article.pdf  the article
src/         the evidence files, the tools that wrote them, the inputs they read, the
             pre-registrations, the patch, the bench, and the walkthrough (src/README.md)
src/paper/   the sources the article is typeset from, and build.sh with its gates
```

The article is built by `bash src/paper/build.sh`, which refuses to replace `article.pdf` when any of
its gates fails. Every number in it expands from a file in `src/evidence/`, and
`src/evidence/README.md` names the tool in `src/tools/` that wrote each file, or says that the tool
is not in this folder. `src/README.md` says what rebuilds from this folder alone and what needs the
cut grid slices that are not in the repository.

The upstream change is pull request 1823 to `ScrollPrize/villa`, merged on 2026-09-21:
https://github.com/ScrollPrize/villa/pull/1823

Code is MIT, the article and its figures are CC BY 4.0, the evidence files are CC BY-NC 4.0. Third
party files keep their own licence and say so where they are.
