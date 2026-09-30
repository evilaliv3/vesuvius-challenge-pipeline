#!/bin/bash
# Read the quiet bench back from its CSVs. This is what the next round runs; it computes nothing
# of its own and starts nothing. Safe at any moment, whether the bench is still in flight or done.
set -u
Q=/data/scrollagent/runs/rev1/quiet-bench
echo "=== is the bench still running? (its own process group, started 2026-09-21T23:34:10Z)"
pgrep_free=$(ps -eo pid,pgid,args | awk '$2=="3131601"' | head -5)
if [ -n "$pgrep_free" ]; then echo "$pgrep_free"; else echo "process group 3131601 has ended"; fi
echo
echo "=== where it got to"
tail -20 $Q/log/bench.txt
echo
echo "=== the c stage, per arm and per seed"
[ -s $Q/evidence/c-stage-runs.csv ] && python3 $Q/tools/summarise_c.py && column -s, -t < $Q/evidence/c-stage-summary.csv | cut -c1-200 || echo "no c stage row yet"
echo
echo "=== what performance/00002 is worth"
[ -s $Q/evidence/a8-factor.csv ] && column -s, -t < $Q/evidence/a8-factor.csv | cut -c1-200 || echo "not yet"
# Two files carry this factor and they are not the same statistic: the one above is the smallest
# run of each arm, the one below the median of each, written by hand on 2026-09-22T01:22:43Z and
# renamed on the director's verdict of 04:17:45Z so the summariser stops overwriting it. Both are
# printed here because both are quoted, and a reader who sees only one will not know that.
echo
echo "=== the same factor as medians, the hand written file"
[ -s $Q/evidence/a8-factor-medians.csv ] && column -s, -t < $Q/evidence/a8-factor-medians.csv | cut -c1-200 || echo "not there"
echo
echo "=== the grid cubes"
[ -s $Q/evidence/cube-stages.csv ] && python3 $Q/tools/cube_table.py && column -s, -t < $Q/evidence/cube-arms.csv | cut -c1-200 || echo "no cube row yet"
echo
echo "=== disk"
tail -3 $Q/evidence/disk.csv
