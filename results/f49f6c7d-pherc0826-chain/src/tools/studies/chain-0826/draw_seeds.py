#!/usr/bin/env python3
# chain-0826 copy of seeds-at-scale-1447/tools/draw_seeds_v2.py, written 2026-09-26 by a coordinator agent (DECLARATION.md part 2):
# paths and names moved to chain-0826 and PHerc0826 (study root, prediction, raw volume, draw and queue file names, ledger
# slugs chain-0826-deliver-*); every other change is listed below this line; the text after the list is the original's.
#   B. DRAW_WORKERS (optional, default 12 as the original) bounds the worker processes; the checks run at 4.
#   A. DRAW_OUT_DIR (optional) replaces evidence/ as the output folder: used only by the known reference run on PHerc1447.
"""draw_seeds_v2.py: draw_seeds.py with THREE changes, in a new file (2026-09-23T19:2xZ, PLAN 56 extended to about
750 draws on the director's ruling of 19:14:15Z). The generator, the population, the lattice, the candidate rule,
the one-index-at-a-time draw with repeats redrawn: all draw_seeds.py's, unchanged.
  1. The seeds go to evidence/seeds-<scroll>-draw<COUNT>.csv, whose first line names this tool; the rows after it
     are written exactly as draw_seeds.py writes them, so the first 150 can be compared byte for byte with
     evidence/seeds-PHerc1447.csv (header plus 150 rows).
  2. The population rows go to evidence/candidate-population-draw<COUNT>.csv (a new file with a tool line), and
     candidate-population.csv of the 150 is not appended to.
  3. COUNT comes from DRAW_COUNT as before; nothing else is read from the environment.
--- draw_seeds.py's docstring follows ---
The fifty seeds of one scroll, drawn by the rule DECLARATION.md fixed before any voxel was read.

The rule, from DECLARATION.md of 2026-09-20T15:43:44Z:

  candidates are voxels of 255 whose six face neighbours are all 255, found by the search
  base-on-1447/tools/ already implements, and 50 seeds per scroll are drawn from them uniformly
  at random with the seed 20260920 written into the tool.

So the candidate definition and the search layout are taken verbatim from
base-on-1447/tools/seed_search.py, kept beside this file as seed_search-base-on-1447.py: the
coarse lattice of every chunk on disk whose three chunk indices are multiples of 4, each read
whole, candidates counted on the chunk interior (indices 1 to 190 on each axis) so that the six
face neighbours of a candidate are inside the same chunk and no chunk boundary is read as a hole.
What is new here is only what the declaration asks for: instead of the one candidate nearest the
centre of the bounding box, fifty candidates drawn uniformly from the whole population.

How the draw is uniform without reading the population twice into memory. Pass one counts the
candidates of every lattice chunk, in the fixed order of the sorted chunk keys, so every candidate
has a global index in [0, total). Pass two draws the indices and re-reads only the chunks they
fall in, at most fifty of them. Drawing an index is therefore drawing a candidate, and a chunk
holding twice the candidates is twice as likely to be drawn from, which is what uniform over the
population means.

The draw itself: numpy.random.default_rng(20260920), one index at a time with
rng.integers(0, total), a repeat redrawn, until fifty distinct indices exist. That is a uniform
draw without replacement and it is reproducible from the generator seed alone, which is written
into this file and not passed on the command line.

Usage: draw_seeds.py <PHerc0826|PHerc1447>
"""
import csv
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import zarr

S = "/data/scrollagent/runs/rev1/chain-0826"  
DATA = "/data/scrollagent/data/datasets"
MANIFESTS = "/data/scrollagent/pipeline/datasets/manifests"
RNG_SEED = 20260920      # declared in DECLARATION.md, written into the tool and not into a flag
COUNT = int(__import__("os").environ.get("DRAW_COUNT","50"))               # declared in DECLARATION.md
STRIDE = 4               # the coarse lattice of base-on-1447/tools/seed_search.py
CHUNK = 192
WORKERS = int(os.environ.get("DRAW_WORKERS", "12"))   # chain-0826 change B: DRAW_WORKERS (default 12, the original's)

_arr = None
_zpath = None


def array():
    global _arr
    if _arr is None:
        _arr = zarr.open(_zpath, mode="r")
    return _arr


def init(zpath):
    global _zpath
    _zpath = zpath


def candidates_of(block):
    """255 with 255 on all six face neighbours, on the block interior. Verbatim from seed_search.py."""
    sol = block == 255
    out = np.zeros(sol.shape, dtype=bool)
    out[1:-1, 1:-1, 1:-1] = (sol[1:-1, 1:-1, 1:-1] & sol[:-2, 1:-1, 1:-1] & sol[2:, 1:-1, 1:-1]
                             & sol[1:-1, :-2, 1:-1] & sol[1:-1, 2:, 1:-1]
                             & sol[1:-1, 1:-1, :-2] & sol[1:-1, 1:-1, 2:])
    return sol, out


def count_chunk(key):
    cz, cy, cx = key
    z0, y0, x0 = cz * CHUNK, cy * CHUNK, cx * CHUNK
    block = np.asarray(array()[z0:z0 + CHUNK, y0:y0 + CHUNK, x0:x0 + CHUNK])
    sol, cand = candidates_of(block)
    n_sol = int(sol.sum())
    if n_sol == 0:
        return (0, int(cand.sum()), None)
    idx = np.nonzero(sol)
    bbox = (int(idx[0].min()) + z0, int(idx[0].max()) + z0,
            int(idx[1].min()) + y0, int(idx[1].max()) + y0,
            int(idx[2].min()) + x0, int(idx[2].max()) + x0)
    return (n_sol, int(cand.sum()), bbox)


def main():
    scroll = sys.argv[1]
    zpath = os.path.join(DATA, scroll, "0")
    manifest = json.load(open(os.path.join(MANIFESTS, scroll + ".json")))
    shape = manifest["shape"]

    present = []
    for line in open(os.path.join(DATA, scroll, "chunks.txt")):
        key = line.split(" ", 1)[0]
        cz, cy, cx = (int(v) for v in key.split("/"))
        present.append((cz, cy, cx))
    lattice = sorted(k for k in present
                     if k[0] % STRIDE == 0 and k[1] % STRIDE == 0 and k[2] % STRIDE == 0)
    print("%s: chunks on disk %d, coarse lattice %d" % (scroll, len(present), len(lattice)))

    t0 = time.monotonic()
    counts = np.zeros(len(lattice), dtype=np.int64)
    surface = 0
    chunks_with_surface = 0
    bbox = None
    with Pool(WORKERS, initializer=init, initargs=(zpath,)) as pool:
        for i, (n_sol, n_cand, bb) in enumerate(pool.imap(count_chunk, lattice, 8)):
            counts[i] = n_cand
            surface += n_sol
            if bb is not None:
                chunks_with_surface += 1
                if bbox is None:
                    bbox = list(bb)
                else:
                    for j in (0, 2, 4):
                        bbox[j] = min(bbox[j], bb[j])
                    for j in (1, 3, 5):
                        bbox[j] = max(bbox[j], bb[j])
            if (i + 1) % 200 == 0:
                print("  %d/%d chunks, %d candidates so far" % (i + 1, len(lattice), int(counts.sum())),
                      flush=True)
    pass_one_seconds = time.monotonic() - t0
    total = int(counts.sum())
    print("candidates %d in %.1f s" % (total, pass_one_seconds))
    if total < COUNT:
        raise SystemExit("only %d candidates on %s: fewer than the %d the draw needs" % (total, scroll, COUNT))

    rng = np.random.default_rng(RNG_SEED)
    drawn = []
    seen = set()
    draws = 0
    while len(drawn) < COUNT:
        g = int(rng.integers(0, total))
        draws += 1
        if g not in seen:
            seen.add(g)
            drawn.append(g)
    print("%d indices drawn in %d draws" % (len(drawn), draws))

    cum = np.cumsum(counts)
    a = zarr.open(zpath, mode="r")
    rows = []
    for order, g in enumerate(drawn):
        ci = int(np.searchsorted(cum, g, side="right"))
        local = g - (int(cum[ci - 1]) if ci else 0)
        cz, cy, cx = lattice[ci]
        z0, y0, x0 = cz * CHUNK, cy * CHUNK, cx * CHUNK
        block = np.asarray(a[z0:z0 + CHUNK, y0:y0 + CHUNK, x0:x0 + CHUNK])
        _sol, cand = candidates_of(block)
        idx = np.nonzero(cand)
        zz = int(idx[0][local]) + z0
        yy = int(idx[1][local]) + y0
        xx = int(idx[2][local]) + x0
        nb = np.asarray(a[zz - 1:zz + 2, yy - 1:yy + 2, xx - 1:xx + 2])
        six = [int(nb[0, 1, 1]), int(nb[2, 1, 1]), int(nb[1, 0, 1]),
               int(nb[1, 2, 1]), int(nb[1, 1, 0]), int(nb[1, 1, 2])]
        rows.append({
            "scroll": scroll,
            "attempt": "%s-seed%02d" % (scroll, order + 1),
            "draw_order": order + 1,
            "global_candidate_index": g,
            "lattice_chunk": "%d/%d/%d" % (cz, cy, cx),
            "seed_x": xx, "seed_y": yy, "seed_z": zz,
            "seed_value": int(nb[1, 1, 1]),
            "six_face_neighbours_all_255": "yes" if all(v == 255 for v in six) else "no",
            "neighbourhood_3x3x3_of_255": int((nb == 255).sum()),
            "edge_margin_x": min(xx, shape[2] - 1 - xx),
            "edge_margin_y": min(yy, shape[1] - 1 - yy),
            "edge_margin_z": min(zz, shape[0] - 1 - zz),
        })
        print("  seed %2d: x %d y %d z %d, value %d, six neighbours %s"
              % (order + 1, xx, yy, zz, int(nb[1, 1, 1]), rows[-1]["six_face_neighbours_all_255"]),
              flush=True)

    out = os.path.join(os.environ.get("DRAW_OUT_DIR") or os.path.join(S, "evidence"), "seeds-%s-draw%d.csv" % (scroll, COUNT))
    with open(out, "w", newline="") as f:
        f.write('"# written by chain-0826/tools/draw_seeds.py: rng %d, %d seeds; rows as draw_seeds.py writes them"\r\n' % (RNG_SEED, COUNT))
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("written %s" % out)

    pop = os.path.join(os.environ.get("DRAW_OUT_DIR") or os.path.join(S, "evidence"), "candidate-population-draw%d.csv" % COUNT)
    exists = False
    with open(pop, "w", newline="") as f:
        f.write('"# written by chain-0826/tools/draw_seeds.py"\r\n')
        w = csv.writer(f)
        if not exists:
            w.writerow(["scroll", "quantity", "value", "what_it_is"])
        vals = [
            ("chunks_on_disk", len(present), "chunks listed in chunks.txt"),
            ("stage1_chunks_read", len(lattice), "chunks whose three indices are multiples of %d" % STRIDE),
            ("stage1_voxels_read", len(lattice) * CHUNK ** 3, "voxels decompressed in the counting pass"),
            ("stage1_chunks_with_surface", chunks_with_surface, "read chunks holding a 255"),
            ("stage1_surface_voxels", surface, "voxels of 255 seen in the counting pass"),
            ("stage1_candidates", total,
             "255 with six 255 face neighbours, chunk interiors of the coarse lattice: the population drawn from"),
            ("rng_seed", RNG_SEED, "numpy default_rng seed, written into the tool"),
            ("seeds_drawn", COUNT, "seeds drawn from that population"),
            ("draws_made", draws, "draws made, a repeated index being redrawn"),
            ("pass_one_seconds", round(pass_one_seconds, 1), "wall clock of the counting pass, not a result"),
        ]
        for name, value, what in vals:
            w.writerow([scroll, name, value, what])
        if bbox is not None:
            for name, value in zip(("bbox_z_min", "bbox_z_max", "bbox_y_min", "bbox_y_max",
                                    "bbox_x_min", "bbox_x_max"), bbox):
                w.writerow([scroll, name, value, "bounding box of the surface voxels found in the counting pass"])
    print("appended %s" % pop)


if __name__ == "__main__":
    main()
