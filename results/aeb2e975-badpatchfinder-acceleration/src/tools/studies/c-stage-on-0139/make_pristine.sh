#!/bin/bash
# c-stage-on-0139: one real copy of each PHerc0139 growth tree, inside this study.
#
# Every run of this study works on a hard link copy of one of these, never on the tree that
# belongs to another study: that tree is read once, here, and never opened again. A stage that
# wrote in place would therefore damage this copy and nothing else, and tools/check_pristine.py
# is what notices.
#
# The tree list and the paths come from evidence/trees.csv, written by tools/tree_inventory.py
# from the declaration's list, so no path is typed here.
set -eu
S=/data/scrollagent/runs/rev1/c-stage-on-0139
mkdir -p "$S/scratch/pristine"
python3 - "$@" <<'PY'
import csv, os, subprocess, sys
S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
want = sys.argv[1:]
with open(os.path.join(S, "evidence", "trees.csv")) as f:
    rows = list(csv.DictReader(l for l in f if not l.startswith("#")))
for r in rows:
    if r["exists"] != "yes":
        continue
    if want and r["tree"] not in want:
        continue
    dst = os.path.join(S, "scratch", "pristine", r["tree"])
    if os.path.isdir(dst):
        print("%s already there" % dst)
        continue
    print("copying %s to %s" % (r["path"], dst), flush=True)
    subprocess.check_call(["cp", "-a", r["path"], dst + ".partial"])
    os.rename(dst + ".partial", dst)
    print("done %s" % r["tree"], flush=True)
PY
