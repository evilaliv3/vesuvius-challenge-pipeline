# An Automatic Patch Based Unwrapping Pipeline Applied to PHerc. 0826

The organisers of the Vesuvius Challenge ask how to make the reading of a scroll work "automatically,
reliably, and at scale for every scroll", and among its bottlenecks they name a traced sheet that jumps
from one wrap to another, for which they want "Smarter surface tracing algorithms that avoid introducing
sheet switches". We built a loop that runs Stevens' published pipeline on the unread PHerc. 0826 with no
person in it, chooses where each surface starts, and keeps a surface only where a set of automatic checks
finds no fault. A square is certified when none of its cells is a hole, crosses one of
the sheets it is compared with, folds onto the next winding or lies in a cluster of points that run
steeply across the surface prediction. Where two traced surfaces cross, the one our sheets agree with
less loses the cell. On a surface grown by the organisers'
tracer from a start our search chose, the checks certify a square of 28.1285 mm on one lamina. They also
reject the 4 largest certified pieces of our own sheets, which fail a fibre test. Our faster bad patch
finder and growth build together make Stevens' pipeline 8.63 times faster per seed with every measured
output equal, the growth build alone 8.21; the chain as delivered also carries 6 corrections that
change its sheets. The checks establish geometry, not legibility. On labelled PHerc. 0139 our sheets
carry the ink to the released model, but our label free statistic does not see that ink, so no reading
of PHerc. 0826 is claimed.

The article gives no coordinates on the scroll: the evidence copies withhold seed points, start points,
heights and chunk indices (column `columns_dropped` of `src/evidence/MANIFEST.csv`).

```
article.pdf     the article
src/paper/      body.tex, appendix.tex, the build and its gates, and phrase-gates.csv
src/evidence/   studies/: the copied CSVs and MANIFEST.csv (source, sha256, copy time, writing tool,
                columns withheld); derived/: what src/tools computes from them; figures/: the plotted tables
src/inputs/     the GitHub answers read, the organisers' open problems page, the copies of
                render-routes-0826 that the headline square is read from, and the nine
                corrections the chain as delivered carries (chain-0826-corrections/)
src/prereg/     the declarations of the studies, as they were written
src/tools/      paper_numbers.py and the tools that write derived/ and figures/; src/tools/studies/
                the tools that wrote the copied evidence
```

The article is built by `bash src/paper/build.sh`, which refuses to replace `article.pdf` when any of
its gates fails. Every number in the article is a macro of `src/paper/numbers.tex`, written by
`src/tools/paper_numbers.py` from one cell of a CSV here.

Upstream items of ours named in the article, all open when it last read them: `ScrollPrize/villa` issue 1875, pull request 1915
and issue 1914; `WillStevens/scrollreading` issue 2 and pull requests 3 and 4;
`Hob3rMallow/scrollfiesta_public` pull requests 17, 18 and 21 and issues 19 and 20.

Code is MIT, the article and its figures are CC BY 4.0, the evidence files are CC BY-NC 4.0. Third
party files keep their own licence and say so where they are.
