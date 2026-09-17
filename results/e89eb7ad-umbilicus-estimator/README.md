# A Far Field Attractor in the Umbilicus Score of Volume Cartographer

The umbilicus is the axis of the rolled scroll, the input every spiral fit starts from, and on
most Herculaneum scrolls it does not exist and has to be estimated. `volume-cartographer` carries
an estimator for it and no accuracy had ever been reported. We measured it on the normal grids the
challenge publishes, against every published umbilicus, and found that one division in the
refinement score turns the objective into one with no interior maximum, so the hill climb walks out
of the volume; removing it is a one line change that brings the estimate from tens of millimetres
to within a few.

```
article.pdf  the article, thirteen pages
src/         the evidence files, the tools that wrote them, the inputs they read, the
             pre-registrations, the patch, the bench, and the walkthrough
```

The article is published elsewhere under a file name made from its title; here it is `article.pdf`,
because a title can be reworded and a file name that quotes one goes stale the day it is. The
title is on the first page of the file and at the top of this page.

The article is delivered as that PDF and is not rebuilt from this folder. What is here is the
science it rests on: every number in it expands from a file in `src/evidence/`, every one of those
files is written by a tool in `src/tools/` from an input in `src/inputs/`, and `src/README.md` is
the walkthrough. It says what rebuilds from this folder alone, what needs the 297 MB of cut grid
slices that are not in the repository, the environment, and one command for every step.

Code is MIT, the article and its figures are CC BY 4.0, the evidence files are CC BY-NC 4.0. Third
party files keep their own licence and say so where they are.

The upstream proposal is a pull request to `ScrollPrize/villa`: https://github.com/ScrollPrize/villa/pull/1823
