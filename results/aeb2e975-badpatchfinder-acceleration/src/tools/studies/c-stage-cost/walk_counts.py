#!/usr/bin/env python3
"""Exactly how many steps the odometer of FindBadPatchesGeneral takes on a tree, counted from that
tree's own rel.csv and its own patches/ directory, without running the stage.

Why it can be counted and not only sampled. The enumeration in badpatchfinder.cpp is an odometer
over indices[0..length-1]: indices[0] runs over the indexed patches from the last down to 1, and
each later index runs over the alignment list of the patch the previous index landed on. The
number of index tuples for a start v is therefore exactly the number of walks of length-1 edges
from v in the augmented alignment multigraph, which is

    W_0(v) = 1,   W_k(v) = sum over the alignment list of v of W_{k-1}(target).

Bad patches and repeats do NOT reduce this count: the build loop breaks out of assembling the
chain, but the odometer still increments through every suffix of the dead prefix. That is the
change this study proposes, and this tool is the number it is proposed against.

The graph is built the way the stage builds it and not in any other way:
  - patches/ gives the keys of the patches map: every *.bin whose digits form the patch number,
    kept when that number is <= SIMPAPER_PATCH_LIMIT (40000 here, as the seed runs used).
  - rel.csv gives am[row0].push_back(row1), keeping a row only when both ends are <= the limit,
    exactly as LoadPatchesAndRelationships does.
  - AugmentAlignmentMap then appends, for every key a in ascending key order and every alignment
    (a -> b) in insertion order, the reverse b -> a. Appended after the forward list of b, which
    is what the C++ does with insert(end(), ...).
  - indexedPatches is the keys of patches, ascending, keeping only those that are a key of am
    with a non empty list.

Cross check: the same numbers are produced by a counting build of the stage itself on the small
seeds, in evidence/step-counts-measured.csv. Two ways of counting that agree is the reference.

Usage: walk_counts.py <attempt> [<attempt> ...]
"""
import csv, os, sys

SEEDS = "/data/scrollagent/runs/rev1/seed-search-1447/out"
S = "/data/scrollagent/runs/rev1/c-stage-cost"
LIMIT = 40000
LENGTHS = [2, 3, 4, 5]


def load(attempt):
    growth = os.path.join(SEEDS, attempt, "growth")
    patch_ids = set()
    for n in os.listdir(os.path.join(growth, "patches")):
        if len(n) >= 4 and n.endswith(".bin"):
            num = 0
            for c in n:
                if c.isdigit():
                    num = num * 10 + int(c)
            if num <= LIMIT:
                patch_ids.add(num)
    fwd = {}
    order = []
    with open(os.path.join(growth, "rel.csv")) as f:
        for line in f:
            if not line.strip():
                continue
            p = line.split(",")
            a, b = int(float(p[0])), int(float(p[1]))
            if a > LIMIT or b > LIMIT:
                continue
            if a not in fwd:
                fwd[a] = []
                order.append(a)
            fwd[a].append(b)
    # AugmentAlignmentMap: newEntries is itself a std::map, so it is walked in ascending key
    # order when it is merged back, but each list keeps its insertion order, which follows the
    # ascending key order of the source map.
    rev = {}
    for a in sorted(fwd):
        for b in fwd[a]:
            rev.setdefault(b, []).append(a)
    am = {}
    for k in set(fwd) | set(rev):
        am[k] = fwd.get(k, []) + rev.get(k, [])
    indexed = [p for p in sorted(patch_ids) if am.get(p)]
    return patch_ids, am, indexed


def main():
    out = os.path.join(S, "evidence", "step-counts-model.csv")
    new = not os.path.exists(out)
    with open(out, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            fh.write("# the exact number of odometer steps FindBadPatchesGeneral takes at each "
                     "chain length, counted from the tree's own rel.csv and patches/ by "
                     "tools/walk_counts.py, with no run. odometer_steps is the number of index "
                     "tuples the while loop visits: sum over the indexed starts from the last "
                     "down to index 1 of the number of walks of length-1 edges in the augmented "
                     "alignment multigraph. map_lookups_lower_bound is 2*(length-1) per step, the "
                     "two am[currentPatch] on the same key in the build loop alone, and it is a "
                     "lower bound because the increment loop walks the chain again. "
                     "patch_files, am_keys and indexed_starts say what the graph was.\n")
            w.writerow(["attempt", "patch_files", "am_keys", "directed_edges", "indexed_starts",
                        "length", "odometer_steps", "map_lookups_lower_bound"])
        for attempt in sys.argv[1:]:
            patch_ids, am, indexed = load(attempt)
            edges = sum(len(v) for v in am.values())
            for L in LENGTHS:
                W = {k: 1 for k in am}
                for _ in range(L - 1):
                    W = {k: sum(W.get(t, 0) for t in v) for k, v in am.items()}
                steps = sum(W[p] for p in indexed[1:])
                w.writerow([attempt, len(patch_ids), len(am), edges, len(indexed), L,
                            steps, steps * 2 * (L - 1)])
                print("%s length %d: %d odometer steps" % (attempt, L, steps), flush=True)
            fh.flush()
    print("written to %s" % out)


if __name__ == "__main__":
    sys.exit(main())
