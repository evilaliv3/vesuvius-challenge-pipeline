#!/usr/bin/env python3
"""Count, for a growth tree, the patch numbers rel.csv names that have no patch_<n>.bin file.

Read only: it lists patches/ and reads rel.csv, nothing else, and writes one row per tree.
The column `reachable` is the same filter as badpatchfinder's length 2 enumeration: a chain
[a,p] is kept only when a < p and a has a patch file.
"""
import csv, os, re, sys

OUT = "/data/scrollagent/runs/rev1/badpatch-crash/evidence/orphans-per-tree.csv"


def one(tree):
    names = set()
    for n in os.listdir(os.path.join(tree, "patches")):
        if n.endswith(".bin"):
            names.add(int(re.sub(r"[^0-9]", "", n)))
    col0, col1, sources = set(), set(), {}
    rows = 0
    with open(os.path.join(tree, "rel.csv")) as f:
        for line in f:
            a = line.split(",")
            if len(a) < 2:
                continue
            rows += 1
            x, y = int(float(a[0])), int(float(a[1]))
            col0.add(x)
            col1.add(y)
            sources.setdefault(y, []).append(x)
    orph = sorted((col0 | col1) - names)
    reach = [p for p in orph if any(s < p and s in names for s in sources.get(p, []))]
    return [tree, len(names), rows, len(orph), len(reach),
            min(orph) if orph else "", max(orph) if orph else "",
            max(names) if names else ""]


def main(trees):
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tree", "patch_files", "rel_rows", "ids_in_rel_with_no_patch_file",
                    "of_those_reachable_as_second_of_a_kept_length_2_chain",
                    "lowest_orphan_id", "highest_orphan_id", "highest_patch_file_id"])
        for t in trees:
            r = one(t)
            w.writerow(r)
            print(r, flush=True)
    print("written to", OUT)


if __name__ == "__main__":
    main(sys.argv[1:])
