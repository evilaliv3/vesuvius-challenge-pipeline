#!/bin/bash
# run_three.sh: run the whole downstream chain of seeds 01, 15 and 26 on a copy of their growth
# trees, once with the untouched corrected binary and once with the guarded one.
#
# Two series and not one. The sheets on disk were written by a run that used every core of the
# machine; this study has about four, so OMP_NUM_THREADS is fixed at 4 here. Running the untouched
# binary under the same setting is what separates a difference made by the guard from a difference
# made by the thread count.
#
# Usage: run_three.sh <series>   where series is plain or guard
set -u
H=/data/scrollagent/runs/rev1/orphan-guard
S=/data/scrollagent/runs/rev1/seed-search-1447
ZARR=/data/scrollagent/data/datasets/PHerc1447/0
SERIES=$1
STAGE_CAP=5400
export OMP_NUM_THREADS=4
export TMPDIR=/data/tmp

for s in seed01 seed15 seed26; do
  A=PHerc1447-$s
  BIN=$H/scratch/bin/$SERIES/$A/simpaper10
  [ -x "$BIN" ] || { echo "no binary at $BIN"; exit 3; }
  O=$H/scratch/out/$SERIES/$A/C40
  mkdir -p $H/scratch/out/$SERIES/$A
  rm -rf $O
  echo "$(date -u +%FT%TZ) [$SERIES $A] copying the growth tree"
  cp -a $S/out/$A/growth $O
  rm -f $O/patch_*.bin
  for st in "c" "l" "vm 10" "hm 10" "fm 30 10"; do
    LOG=$H/log/chain-$SERIES-$A-$(echo $st | tr ' ' '_').txt
    t0=$(date +%s)
    SIMPAPER_OUTPUT_DIR=$O SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$O/missing-C40.txt \
      SIMPAPER_PATCH_LIMIT=40000 timeout -s TERM $STAGE_CAP $BIN $st > "$LOG" 2>&1
    rc=$?
    echo "$(date -u +%FT%TZ) [$SERIES $A] stage '$st' rc=$rc in $(( $(date +%s)-t0 )) s, sheets $(ls $O/patch_*.bin 2>/dev/null | wc -l)"
    [ $rc -ne 0 ] && { echo "$(date -u +%FT%TZ) [$SERIES $A] stage '$st' failed, stopping this seed"; break; }
  done
done
echo "$(date -u +%FT%TZ) [$SERIES] done"
