# external-references

Local copies of the known umbilici, with their provenance beside them, because a measurement is
redone against exactly the files we used. The full inventory and the criteria for excluding a
reference are kept with the frozen run and are not part of this folder.

| file | origin | method | licence |
|---|---|---|---|
| `challenge-PHercParis4-umbilicus.json` | the public bucket of the challenge, `PHercParis4/representations/umbilicus/` | hand annotation, 146 points, volume 20260411134726 at 2.4 um | challenge open data |
| `challenge-PHerc0139-umbilicus.json` | the same, `PHerc0139/...` | hand annotation by David Josey in webknossos, 391 points, volume 20260102150214 at 2.399 um. **Not usable**: no surface prediction on the same scan | the same |
| `drobkov-PHerc*-umbilicus.json` (ten) | `github.com/AlexeyDrobkovStrikesBack/herculaneum-umbilici` | hand annotation with the mouse on level 3 PNG (scale 8), one slice every 480 or so in z | MIT |
| `drobkov-PHerc*-meta.json` (ten) | the same | the record of which slices were annotated and of the coordinate conversion | MIT |
| `dopico-PHerc1218-umbilicus.json` | `github.com/IyanDopico/vesuvius-sheet-tools`, `data/spiral_input_pherc1218/` | **derived** from sheet instance labels, not clicked: 365 points, volume 20250521120456 at 8.640 um | MIT |
| `drobkov-README.md` | the same as Drobkov | their own document, kept for the note on PHerc1218 that says to prefer Dopico's file in the z band 7500 to 9500 | MIT |

`drobkov-README.md` is a quotation of somebody else's file and is published here exactly as it
was written, punctuation and all.

The four already in `../reference/` (PHerc0125, PHerc0211, PHerc0332, PHerc0826) are not
duplicated here.
