#!/bin/bash
# c-stage-on-0139, phase 2: the `c` stage time of each arm on each tree, repeated.
#
# Serial on purpose: a time taken while three other stages run is not a time. The arms of one
# tree run one after the other inside the same minute, so machine drift falls on all of them, and
# the outer loop is the repetition, so that the run can be stopped after any complete round and
# every tree still has the same number of runs in every arm.
#
# The tree `b40` is left out here: evidence/trees.csv gives it the same content_sha256 as
# `repeat`, so it is the same tree and would be a fifth repetition of it dressed as a data point.
# It is run in phase 1, where the question is identity and a duplicate costs nothing.
#
# Every run works on a hard link copy of scratch/pristine/<tree> and drops it afterwards, so the
# disk does not grow. One script in the queue, no waiting on a process name.
set -u
S=/data/scrollagent/runs/rev1/c-stage-on-0139
cd "$S"
ROUNDS=${ROUNDS:-4}
TREES=${TREES:-"A repeat S D450 C D150 P2"}
ARMS=${ARMS:-"plain guarded c2"}
say() { echo "$(date -u +%FT%TZ) $*"; }

case "$ROUNDS" in ''|*[!0-9]*) say "ROUNDS is not a number: '$ROUNDS'"; exit 2;; esac
for T in $TREES; do
  [ -d "$S/scratch/pristine/$T" ] || { say "no pristine copy for $T, stopping"; exit 2; }
done
say "rounds $ROUNDS, trees $TREES, arms $ARMS"

for r in $(seq 1 "$ROUNDS"); do
  for T in $TREES; do
    for ARM in $ARMS; do
      python3 tools/run_arm2.py --arm "$ARM" --tree "$T" --tag "time-$ARM" --stages c \
          --threads 4 --repeat "$r" --drop >> "log/timing-$ARM-$T.txt" 2>&1 \
        || say "round $r $T $ARM: run_arm2 returned non zero, see log/timing-$ARM-$T.txt"
    done
  done
  say "round $r finished"
  python3 tools/summarise_times.py > "log/times-after-round-$r.txt" 2>&1 || true
done
say "phase 2 finished"
