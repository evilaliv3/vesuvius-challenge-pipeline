# Output Preserving Acceleration of the Bad Patch Finder in the Scrollreading Pipeline

The bad patch finder of Will Stevens' scrollreading chain discards pieces of surface that cannot sit
together, and on three tangled growths of PHerc. 1447 it ran for hours and was abandoned. We made two
changes inside its one function. The first stops the enumeration from extending a chain that is already
dead, and the second replaces a map rebuilt on every pass with a vector. On a quiet machine the `c`
stage of the tangle seed40 goes from 7,094.8 s to 35.5, about two hundred times faster. On seed38 it
goes from 7,930.6 s to 61.2, a factor that a disturbance of the untouched run can only have inflated. On
a ribbon, where the enumeration was never the cost, the factor is only 1.05. Every file the five
delivery stages write is byte identical between the arms on fifteen named growth trees of two scrolls,
and the stage's whole standard output is identical on fourteen of them. A third change, a guard, turns
an abort into a result on a tree whose alignment file names missing patches. The changes make a search
over many seeds affordable but move no delivered square. The main limit is that identity is not
correctness.

```
article.pdf     the article
src/paper/      the LaTeX sources and build.sh with its gates
src/evidence/   the CSVs every number is read from, one folder per study, and the figures' plotted tables
src/prereg/     the declaration of each study, written before any number of it existed
src/tools/      the tools that write the numbers and draw the figures; src/tools/studies/ the tools
                that wrote the copied evidence
```

The article is built by `bash src/paper/build.sh`, which refuses to replace `article.pdf` when any of
its gates fails. Most numbers in the article are macros written by `src/tools/paper_numbers.py`, each from one
cell of a CSV in `src/evidence/`. The rest are copied by hand from such a cell.

Upstream, on Will Stevens' repository https://github.com/WillStevens/scrollreading: the two changes and
the guard are pull request #4, stacked on #3, which carries the earlier performance patch; the growth
that reuses a folder is issue #2. All three were open when the article last read them.

Code is MIT, the article and its figures are CC BY 4.0, the evidence files are CC BY-NC 4.0. Third
party files keep their own licence and say so where they are.
