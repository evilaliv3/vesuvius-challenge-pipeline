#!/usr/bin/env python3
"""What the odometer would cost if a prefix that already carries a bad patch were not extended.

The same graph as tools/walk_counts.py, with the bad patch set of each round read from the c
stage's own log, which prints it: `Round N bad patches` followed by one id per line. Round 1's
list is what badPatches holds when the length 3 round starts, round 1 plus round 2 when the
length 4 round starts, and so on; the length 2 round starts with the set empty.

A prefix that contains a bad patch can never be emitted, because the build loop sets hasBadPatch
and the chain is dropped, and neither can any extension of it. So the walks that a pruning
enumeration takes are the walks of the subgraph on the patches that are not bad, from the starts
that are not bad.

CORRECTION of 2026-09-21T16:45Z. This file was written before the change was built and it called
its own number an upper bound on the pruned cost. It is not one: the pruned odometer also takes
one step for every prefix that dies, and those steps are not counted here. The counting build
reads 946,327 steps over seed40's four rounds where this model sums to 581,101
(evidence/step-counts-measured.csv). What the model got right is the order of magnitude and the
shape: five to six hundred thousand steps against fifty one and a half billion.

This is a model, not a measurement. The measured numbers are in evidence/step-counts-measured.csv
and evidence/runs.csv.

Usage: pruned_counts.py <attempt> <c-stage-log>
"""
import csv, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from walk_counts import load  # same graph, built once and not twice

S = "/data/scrollagent/runs/rev1/c-stage-cost"
LENGTHS = [2, 3, 4, 5]


def rounds(log):
    """The four cumulative bad patch sets the stage printed, one per round."""
    per = {}
    cur = None
    with open(log) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("Round ") and line.endswith(" bad patches"):
                cur = int(line.split()[1])
                per[cur] = []
            elif cur is not None:
                if line.isdigit():
                    per[cur].append(int(line))
                else:
                    cur = None
    return per


def main():
    attempt, log = sys.argv[1], sys.argv[2]
    per = rounds(log)
    patch_ids, am, indexed = load(attempt)
    out = os.path.join(S, "evidence", "step-counts-pruned-model.csv")
    with open(out, "w", newline="") as fh:
        fh.write("# what the odometer would cost with a prefix that carries a bad patch not "
                 "extended, modelled from the same graph tools/walk_counts.py builds and from the "
                 "bad patch sets the c stage printed in its own log. bad_patches_entering is the "
                 "size of badPatches when that round starts: empty at length 2, round 1's list at "
                 "length 3, rounds 1 and 2 at length 4, rounds 1 to 3 at length 5. "
                 "pruned_steps counts the walks of the full length in the subgraph on the "
                 "patches that are not bad. CORRECTION of 2026-09-21T16:45Z, after the counting "
                 "build measured the pruned odometer: this is NOT the pruned step count and not "
                 "an upper bound on it. The pruned odometer also visits every prefix that dies, "
                 "one step each, and those are not counted here, so this column is below what "
                 "the counter reads (evidence/step-counts-measured.csv: 946,327 steps over the "
                 "four rounds of seed40 against the 581,101 this column sums to). It stands as "
                 "the order of magnitude that was written before the change was built. "
                 "unpruned_steps is the figure of step-counts-model.csv, which the counting "
                 "build confirms exactly on seed26. This is a model, not a measurement.\n")
        w = csv.writer(fh)
        w.writerow(["attempt", "length", "bad_patches_entering", "indexed_starts_alive",
                    "unpruned_steps", "pruned_steps", "ratio", "log"])
        for L in LENGTHS:
            bad = set()
            for r in range(1, L - 1):
                bad |= set(per.get(r, []))
            alive_am = {k: [t for t in v if t not in bad]
                        for k, v in am.items() if k not in bad}
            starts = [p for p in indexed[1:] if p not in bad]
            # unpruned
            W = {k: 1 for k in am}
            for _ in range(L - 1):
                W = {k: sum(W.get(t, 0) for t in v) for k, v in am.items()}
            unpruned = sum(W[p] for p in indexed[1:])
            # pruned
            V = {k: 1 for k in alive_am}
            for _ in range(L - 1):
                V = {k: sum(V.get(t, 0) for t in v) for k, v in alive_am.items()}
            pruned = sum(V.get(p, 0) for p in starts)
            w.writerow([attempt, L, len(bad), len(starts), unpruned, pruned,
                        "%.4g" % (unpruned / pruned) if pruned else "not measurable", log])
            print("length %d: bad %d, unpruned %d, pruned at most %d"
                  % (L, len(bad), unpruned, pruned), flush=True)
    print("written to %s" % out)


if __name__ == "__main__":
    sys.exit(main())
