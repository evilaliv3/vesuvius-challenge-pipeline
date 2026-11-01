# Rectina, a dense ink reader for Herculaneum papyri trained from scratch on composite labels

This folder holds the article on the Rectina ink reader: the typeset PDF (15 pages), the LaTeX sources, the 36 control panels, the numbers behind the text and the code pieces that read, render and convert the data.

## The two models

Rectina m1 (folder m1 on evilaliv3/rectina), compared with Reader v2: Ink detection checkpoint of the Seek and Unroll dense recipe: the model after the first training step (s1), taken at the fixed step 130001 (file ckpt_130001; embedded step counter 130000).

Rectina m2 (folder m2 on evilaliv3/rectina), compared with Reader v3: Ink detection checkpoint of the Seek and Unroll dense recipe: the model after the third and last training step (s4), taken at the final step of stage 4 (file ckpt_020000; embedded step counter 19999).

## What is here

- article.pdf: the article, sha256 bb047fde616dcdd30780c8f15821ce65161cde160768d5c6606318337023ac0e, registered 2026-11-01T02:16:49Z.
- src/paper: the LaTeX sources (26) and the class files.
- src/figures: the control panels (36).
- src/evidence: the numbers files (3) and MANIFEST.csv, which lists each file with its sha256.
- src/inputs/INPUTS.csv: every input of the typeset article with its sha256 and size.
- src/read, src/render, src/convert: how a map is read from a checkpoint, how the surface stacks were rendered, how maps are converted.
- src/tools: the helpers the paper build calls.

## Data terms

Note on terms: the data of the Vesuvius Challenge are subject to its data licence.
