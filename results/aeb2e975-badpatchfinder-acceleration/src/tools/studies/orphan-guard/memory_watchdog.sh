#!/bin/bash
# memory_watchdog.sh: stop this study's own seed34 stage if the machine's free memory falls.
#
# The chain enumeration of FindBadPatchesGeneral grows with the fourth power of the average number
# of alignments per patch, and seed34 has 36 of them against the 4.6 of seed01. The rounds at
# length 4 and 5 can therefore ask for far more memory than the machine has, and the machine is
# carrying five other c stages of the prize line. This watchdog kills the process group this study
# started, by its PGID and nothing else, when MemAvailable falls under the floor.
#
# Usage: memory_watchdog.sh <pgid> <floor_gb>
set -u
PGID=$1
FLOOR=$2
L=/data/scrollagent/runs/rev1/orphan-guard/log/memory-watchdog.txt
echo "$(date -u +%FT%TZ) watching pgid $PGID, floor ${FLOOR} GB" >> $L
while kill -0 -- -$PGID 2>/dev/null; do
  AVAIL=$(( $(awk '/MemAvailable/{print $2}' /proc/meminfo) / 1048576 ))
  if [ "$AVAIL" -lt "$FLOOR" ]; then
    echo "$(date -u +%FT%TZ) MemAvailable ${AVAIL} GB under the ${FLOOR} GB floor, stopping pgid $PGID" >> $L
    kill -- -$PGID
    sleep 20
    kill -9 -- -$PGID 2>/dev/null
    echo "$(date -u +%FT%TZ) stopped" >> $L
    exit 0
  fi
  sleep 20
done
echo "$(date -u +%FT%TZ) pgid $PGID ended on its own, MemAvailable $(( $(awk '/MemAvailable/{print $2}' /proc/meminfo) / 1048576 )) GB" >> $L
