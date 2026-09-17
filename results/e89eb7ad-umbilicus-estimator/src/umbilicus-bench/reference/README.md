# reference

The four umbilici published by the Vesuvius Challenge that this bench scores against, copied here
so that the bench has its ground truth without a network round trip and so that a run is
reproducible against exactly the files we used.

Each is a list of control points {x, y, z} in level 0 voxels of the scan the umbilicus was
annotated on. Points flagged `rejected` are skipped when read; none of these four files has any.

## Where each one came from

Copied from the Vesuvius Challenge open-data bucket on 2026-09-10 and checked against it again on
2026-09-18, when the control points of all four still matched the published objects point for
point. Prefix every object name below with the bucket root to fetch it again:

```
https://vesuvius-challenge-open-data.s3.amazonaws.com/
```

| file | object in the bucket | points | annotated at | bytes | sha256 |
|---|---|---:|---:|---:|---|
| `PHerc0125-umbilicus.json` | `PHerc0125/representations/umbilicus/20250821151825-umbilicus-20260808111524.json` | 83 | 9.362 um | 4647 | `eecf0368f3e6b2dca2ed5a0f65f36f18e4f48bae1333829a31ff0d4f13c40df4` |
| `PHerc0211-umbilicus.json` | `PHerc0211/representations/umbilicus/20250821151803-umbilicus-20260808112626.json` | 87 | 9.362 um | 4830 | `087ef49b32281cebfe1f9f42240fe6ace839826ecc71758e1f3abf3dcdee81ed` |
| `PHerc0826-umbilicus.json` | `PHerc0826/representations/umbilicus/20250821151701-umbilicus-20260808113303.json` | 49 | 9.362 um | 2950 | `3417e42b091cda2c3d10aa578f2063b6c3332e670eff6ba62feb8035413b2dc0` |
| `PHerc0332-umbilicus.json` | `PHerc0332/representations/umbilicus/20251211183505-umbilicus-20260828110920.json` | 169 | 2.399 um | 9069 | `f5e403d7c4343b3e762f8c7f20d3859e187de5d7db6fcb8e1086ac5c68ad72d5` |

To fetch one again, and to see for yourself that it is the same data:

```
curl -sO https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0826/representations/umbilicus/20250821151701-umbilicus-20260808113303.json
python -c "import json,sys; a=json.load(open('20250821151701-umbilicus-20260808113303.json'))['control_points']; b=json.load(open('reference/PHerc0826-umbilicus.json'))['control_points']; print([(p['x'],p['y'],p['z']) for p in a]==[(p['x'],p['y'],p['z']) for p in b])"
```

The sha256 above will not match the object you download, and that is expected: these copies were
written back out by `data.py` as compact JSON, so the whitespace differs. The control points, their
order, their scores and the `metadata` block are unchanged, which is what the command above checks.
The object names are also in `data.py`, under `SCROLLS[...]["umbilicus"]`, and `data.py` falls back
to downloading them if these files are missing.

The `metadata` block travels with each file and is worth reading: it carries the annotation
timestamps and thresholds, and for PHerc0332 the annotator and the source annotation file.

## Licence

Open data under CC BY-NC 4.0: attribution required, non-commercial use only. The citation the
organizers ask for is in `../LICENSE-DATA.md`.
