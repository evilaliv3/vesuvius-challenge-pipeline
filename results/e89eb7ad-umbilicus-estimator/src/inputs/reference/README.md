# reference

The four umbilici published by the Vesuvius Challenge that this bench scores against, copied here
so that the bench has its ground truth without a network round trip and so that a run is
reproducible against exactly the files we used. They are open data; the canonical copies live
under `<scroll>/representations/umbilicus/` in the open-data bucket (the exact object names are in
`data.py`), and `data.py` falls back to downloading them if these are missing.

Each is a list of control points {x, y, z} in level 0 voxels of the scan the umbilicus was
annotated on: 9.362 um for PHerc0125, PHerc0211 and PHerc0826, 2.399 um for PHerc0332. Points
flagged `rejected` are skipped when read.

They are open data under CC BY-NC 4.0: attribution required, non-commercial use only. The
citation the organizers ask for is in `../../umbilicus-bench/LICENSE-DATA.md`.
