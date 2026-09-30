#!/bin/bash
# c-stage-on-0139, phase 1: the bar. The whole downstream, three arms, every tree, then the
# sha256 of every file each arm wrote and the comparison between arms.
#
# One script in the queue, as the house rule wants: no waiting on a process name, no pgrep, the
# three arms of a tree are started here and waited on by their own PIDs. The arms of one tree run
# together because they are independent of each other; trees run one after the other so that the
# machine stays well inside the ceiling of 22 cores busy (three arms at OMP_NUM_THREADS=4).
#
# Nothing is run in place: every arm works on a hard link copy of scratch/pristine/<tree>, and
# tools/check_pristine.py runs after the first tree and again at the end.
set -u
S=/data/scrollagent/runs/rev1/c-stage-on-0139
cd "$S"
say() { echo "$(date -u +%FT%TZ) $*"; }

TREES=$(python3 - <<'PY'
import csv
with open("/data/scrollagent/runs/rev1/c-stage-on-0139/evidence/trees.csv") as f:
    print(" ".join(r["tree"] for r in csv.DictReader(l for l in f if not l.startswith("#"))
                   if r["exists"] == "yes"))
PY
)
say "trees: $TREES"

first=1
for T in $TREES; do
  pids=""
  for ARM in plain guarded c2; do
    python3 tools/run_arm2.py --arm "$ARM" --tree "$T" --tag "id-$ARM" --stages all \
        --threads 4 --repeat 1 >> "log/identity-$ARM-$T.txt" 2>&1 &
    pids="$pids $!"
  done
  say "$T: arms started, pids$pids"
  bad=0
  for p in $pids; do wait "$p" || bad=1; done
  say "$T: arms finished, bad=$bad"
  for ARM in plain guarded c2; do
    python3 tools/hash_run.py "$ARM" "$T" "id-$ARM" 1 || say "$T $ARM: hashing failed"
  done
  if [ $first -eq 1 ]; then
    say "first tree done, checking that nothing was written in place"
    python3 tools/check_pristine.py || { say "PRISTINE CHECK FAILED, stopping"; exit 3; }
    first=0
  fi
  for ARM in plain guarded c2; do rm -rf "$S/scratch/out/id-$ARM/$T-r1"; done
  say "$T: working copies dropped"
done

say "all trees done, final pristine check"
python3 tools/check_pristine.py || say "PRISTINE CHECK FAILED at the end"
say "identity plain against c2"
python3 tools/identity.py plain c2; say "identity.py plain c2 exit $?"
say "identity guarded against c2"
python3 tools/identity.py guarded c2; say "identity.py guarded c2 exit $?"
say "identity plain against guarded"
python3 tools/identity.py plain guarded; say "identity.py plain guarded exit $?"
say "phase 1 finished"
