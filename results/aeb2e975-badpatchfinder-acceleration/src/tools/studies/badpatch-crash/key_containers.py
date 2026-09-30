#!/usr/bin/env python3
"""For every patch number the instrumented run reported as missing, say what each container holds.

Containers, one column each, in the order the c stage builds them:
  patch_file_on_disk   patch_<p>.bin exists under the tree's patches/ folder
  patches_map          the c stage's std::map<int,Patch>: it is exactly one entry per .bin file
                       whose parsed number is at most SIMPAPER_PATCH_LIMIT, so this column is read
                       from the file listing and from the limit, not assumed
  rel_col0 / rel_col1  how many rows of rel.csv name p as the first or the second column
  alignment_map        p is a key of the AlignmentMap: rel_col0 rows make it one directly,
                       rel_col1 rows make it one through AugmentAlignmentMap
Nothing here is inferred from the crash: each column is counted from the file that carries it.
"""
import csv, os, re, sys

TREE = "/data/scrollagent/runs/rev1/badpatch-crash/scratch/C40"
DIAG = "/data/scrollagent/runs/rev1/badpatch-crash/evidence/diag-missing.txt"
OUT = "/data/scrollagent/runs/rev1/badpatch-crash/evidence/key-containers.csv"
LIMIT = 40000

keys, rows = [], []
first_q, first_p = None, None
with open(DIAG) as f:
    for line in f:
        if not line.startswith("DIAG length="):
            continue
        d = dict(kv.split("=", 1) for kv in line.split() if "=" in kv and not kv.startswith("seq"))
        p, q = int(d["p"]), int(d["q"])
        rows.append((q, p, int(d["lastPatch"]), int(d["count"]), int(d["am_has_p"]),
                     int(d["patches_has_p"])))
        keys.append(p)
        if first_q is None or q < first_q:
            first_q, first_p = q, p

uniq = sorted(set(keys))

names = set()
for n in os.listdir(os.path.join(TREE, "patches")):
    if n.endswith(".bin"):
        names.add(int(re.sub(r"[^0-9]", "", n)))

col0, col1 = {}, {}
with open(os.path.join(TREE, "rel.csv")) as f:
    for line in f:
        a = line.split(",")
        if len(a) < 2:
            continue
        x, y = int(float(a[0])), int(float(a[1]))
        col0[x] = col0.get(x, 0) + 1
        col1[y] = col1.get(y, 0) + 1

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["patch", "times_reported_missing", "patch_file_on_disk", "in_patches_map",
                "rel_rows_as_col0", "rel_rows_as_col1", "key_of_alignment_map",
                "alignment_map_key_source"])
    for p in uniq:
        on_disk = "yes" if p in names else "no"
        in_map = "yes" if (p in names and p <= LIMIT) else "no"
        c0, c1 = col0.get(p, 0), col1.get(p, 0)
        key = "yes" if (c0 or c1) else "no"
        src = ("rel.csv column 0" if c0 else "") + (" and " if c0 and c1 else "") + \
              ("rel.csv column 1, through AugmentAlignmentMap" if c1 else "")
        w.writerow([p, keys.count(p), on_disk, in_map, c0, c1, key, src or "not a key"])

print("distinct missing patch numbers: %d, reports: %d" % (len(uniq), len(rows)))
print("on disk: %d of %d" % (sum(1 for p in uniq if p in names), len(uniq)))
print("in patches map: %d of %d" % (sum(1 for p in uniq if p in names and p <= LIMIT), len(uniq)))
print("key of the alignment map: %d of %d"
      % (sum(1 for p in uniq if col0.get(p, 0) or col1.get(p, 0)), len(uniq)))
print("named in rel.csv column 0: %d, column 1: %d"
      % (sum(1 for p in uniq if col0.get(p, 0)), sum(1 for p in uniq if col1.get(p, 0))))
print("lowest sequence index reported: q=%d, p=%d" % (first_q, first_p))
print("patch files on disk: %d, max number: %d" % (len(names), max(names)))
print("rel.csv distinct col0: %d, distinct col1: %d" % (len(col0), len(col1)))
print("ids named in rel.csv with no patch file on disk: %d"
      % len((set(col0) | set(col1)) - names))
print("written to", OUT)


def orphans():
    """Every patch number named in rel.csv with no patch file on disk, and whether the c stage's
    length 2 enumeration can reach it: a chain [a,p] is kept only when a < p
    (badpatchfinder.cpp, `currentSequence.front() < currentSequence.back()`), and a must itself be
    a loaded patch with at least one alignment."""
    out = "/data/scrollagent/runs/rev1/badpatch-crash/evidence/orphan-patches.csv"
    reported = set()
    with open(DIAG) as f:
        for line in f:
            if line.startswith("DIAG length="):
                reported.add(int(dict(kv.split("=", 1) for kv in line.split()
                                      if "=" in kv and not kv.startswith("seq"))["p"]))
    sources = {}
    with open(os.path.join(TREE, "rel.csv")) as f:
        for line in f:
            a = line.split(",")
            if len(a) < 2:
                continue
            x, y = int(float(a[0])), int(float(a[1]))
            sources.setdefault(y, []).append(x)
    orph = sorted((set(col0) | set(col1)) - names)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["patch", "patch_file_on_disk", "rel_rows_as_col0", "rel_rows_as_col1",
                    "sources_loaded_and_lower", "reachable_as_second_of_a_kept_length_2_chain",
                    "reported_missing_by_the_instrumented_run"])
        n_reach = 0
        for p in orph:
            lower = sorted(set(s for s in sources.get(p, []) if s < p and s in names))
            reach = "yes" if lower else "no"
            n_reach += 1 if lower else 0
            w.writerow([p, "yes" if p in names else "no", col0.get(p, 0), col1.get(p, 0),
                        len(lower), reach, "yes" if p in reported else "no"])
    print("orphans (named in rel.csv, no patch file): %d" % len(orph))
    print("of those reachable as the second of a kept length 2 chain: %d" % n_reach)
    print("of those reported missing by the instrumented run: %d"
          % len([p for p in orph if p in reported]))
    print("written to", out)


orphans()
