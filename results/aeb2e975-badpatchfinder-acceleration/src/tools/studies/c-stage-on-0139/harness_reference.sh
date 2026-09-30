#!/bin/bash
# c-stage-on-0139: the known reference of this study's harness.
#
# Coordinator.md section 2: every measurement is paired with a known reference. The identity bar
# of this study compares two arms this study built and ran, so a harness that ran both arms
# wrongly in the same way would pass it. This check is the thing that would catch that.
#
# runs/rev1/reference-b40 delivered, on 2026-09-20, the folder out/B40: the whole downstream
# c l vm 10 hm 10 fm 30 10 at SIMPAPER_PATCH_LIMIT 40000, on the growth tree out/growth, with the
# binary /data/scrollagent/pipeline/build/efficient/simpaper10, whose sha256 that study's
# declaration records as 28cd6f45... and whose file is still on disk with that sha. That is a
# binary this study CAN account for and an output written by a route this study can repeat.
#
# So: the same binary, the same tree (this study's pristine copy of it), the same limit and the
# same environment variables as reference-b40/tools/run_chain.sh set, which notably does NOT set
# ZARR_CHUNK_MANIFEST and does not set OMP_NUM_THREADS. If the 39 delivered files come back byte
# for byte, the harness of this study reproduces an output measured before it existed.
#
# Nothing under reference-b40 is written: its out/B40 is read to be hashed, and that is all.
set -eu
S=/data/scrollagent/runs/rev1/c-stage-on-0139
BIN=/data/scrollagent/pipeline/build/efficient/simpaper10
REF=/data/scrollagent/runs/rev1/reference-b40/out/B40
ZARR=/data/scrollagent/data/datasets/PHerc0139/0
O=$S/scratch/out/href/repeat-r1/C40
say() { echo "$(date -u +%FT%TZ) $*"; }

say "binary $(sha256sum $BIN | cut -d' ' -f1)"
rm -rf "$S/scratch/out/href"
mkdir -p "$S/scratch/out/href/repeat-r1"
cp -al "$S/scratch/pristine/repeat" "$O"
cd "$O"
for st in "c" "l" "vm 10" "hm 10" "fm 30 10"; do
  t0=$(date +%s)
  SIMPAPER_OUTPUT_DIR=$O SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$O/missing-B40.txt \
    SIMPAPER_PATCH_LIMIT=40000 TMPDIR=/data/tmp \
    $BIN $st > "$S/log/href-$(echo $st | tr ' ' '_').txt" 2>&1
  say "stage '$st' rc=$? in $(( $(date +%s)-t0 )) s"
done
say "comparing with $REF"
python3 - <<PY
import csv, hashlib, os, subprocess
S = "$S"; O = "$O"; REF = "$REF"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def top(d):
    return sorted(n for n in os.listdir(d)
                  if os.path.isfile(os.path.join(d, n)) and not n.startswith("missing-"))
when = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
out = os.path.join(S, "evidence", "harness-reference.csv")
n = d = 0
with open(out, "w", newline="") as f:
    f.write("# the known reference of the harness. Every file delivered by reference-b40 arm B40 "
            "on 2026-09-20, against the same file written now by this study's harness running the "
            "same binary (pipeline/build/efficient/simpaper10) on this study's pristine copy of "
            "the same growth tree, with the same SIMPAPER_PATCH_LIMIT and the same environment "
            "that study's run_chain.sh set. byte_identical no on any row means this study's "
            "harness does not reproduce an output taken before it existed.\n")
    w = csv.writer(f)
    w.writerow(["file", "reference_sha256", "harness_sha256", "byte_identical", "compared_utc"])
    for name in sorted(set(top(REF)) | set(top(O))):
        a = sha(os.path.join(REF, name)) if os.path.exists(os.path.join(REF, name)) else "absent from the reference"
        b = sha(os.path.join(O, name)) if os.path.exists(os.path.join(O, name)) else "the harness wrote no such file"
        ok = "yes" if a == b else "no"
        n += 1; d += ok == "no"
        w.writerow([name, a, b, ok, when])
print("files %d, different %d" % (n, d))
PY
rm -rf "$S/scratch/out/href"
say "done"
