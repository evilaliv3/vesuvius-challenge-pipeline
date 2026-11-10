# Rectina m3 and m4, dense ink readers for Herculaneum papyri rebuilt on current renders

This folder holds the article on Rectina m3 and m4, the second pair of checkpoints of the Rectina ink reader: the typeset PDF (17 pages), the LaTeX sources, the 84 panels of the 28 triptychs, the numbers behind the text and the code pieces that read, render and convert the data. It replaces the version of this folder that covered Rectina m1 and m2 (the article of 1 November 2026); that version stays in the history of this repository.

## The two models

Rectina m3 (folder m3 on evilaliv3/rectina): Ink detection checkpoint of a new chain of the Seek and Unroll dense recipe, retrained on bicubic renders: the model after the stages s1, ft116k and s2, taken at the last step of stage s2 (file ckpt_040000; embedded step counter 39999). Compared with Reader v2 and Reader v3. sha256 b3346d9dd5e2dea0c770ac7de17ed85adddc73bd77a9f32ee3850424ebdc99c9.

Rectina m4 (folder m4 on evilaliv3/rectina): the same chain continued from the weights of m3 with the stages s3 and s4 at larger patches, taken at the last step of stage s4 (file ckpt_020000; embedded step counter 19999). Compared with Reader v2 and Reader v3. sha256 15e3814db216149d27dcbf0316999d9773c0a51d0dc24a3b561b07a4ad6f4e72.

Rectina m1 and m2 are not described here; they are in the earlier version of this folder and remain in the model repository.

## What is here

- article.pdf: the article, sha256 06095c1800149651731fd51c6d69c54c161292403f281034d7b491c8dcbae20a, 17 pages.
- src/paper: the LaTeX sources (23) and the class files (cls, 2). It builds from this folder with `TEXINPUTS=./cls//: pdflatex article.tex`, run twice, with SOURCE_DATE_EPOCH set to the build date.
- src/figures: the triptych panels (84: m3 and m4, fourteen units each, three panels per triptych: Reader v3, the model, the difference).
- src/evidence: the numbers files (26) and MANIFEST.csv, which lists each file with its sha256. Scores of the pairs (scores/), the table of the units, the check of the placement of the labels (label-check/), the offset of w00 and the scan of its AUC (w00/), the training patch, the five stage configurations and the manifest of the set (training/), the render manifest, the read list and MACROS.csv, which ties each number of the text to its source.
- src/inputs/INPUTS.csv: every input of the typeset article with its sha256 and size, including the two checkpoints.
- src/read: how a map is read from a checkpoint. The files of October are unchanged (rectina_read.py and its tests, for m1 and m2); src/read/m3m4 holds the read path used for m3 and m4.
- src/render: how the surface stacks were rendered. The files of October are unchanged (the renders of Reader v2, Reader v3, m1 and m2); src/render/m3m4 holds the render tools used for m3 and m4.
- src/convert: how maps are converted, the same as in October, not run again.
- src/tools: the helpers the paper build calls, the same as in October.

In the sources the figure paths point to ../figures, so the paper builds from src/paper. Absolute paths of the machine of the study were removed from the evidence files; the tool scripts in src/read/m3m4 and src/render/m3m4 keep them as written, and say so.

## Data terms

Note on terms: the data of the Vesuvius Challenge are subject to its data licence.
