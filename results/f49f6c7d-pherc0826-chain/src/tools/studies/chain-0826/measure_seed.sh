#!/bin/bash
# chain-0826 copy of seeds-at-scale-1447/tools/measure_seed_v3.sh, written 2026-09-26 by a coordinator agent (DECLARATION.md part 2):
# paths and names moved to chain-0826 and PHerc0826 (study root, prediction, raw volume, draw and queue file names, ledger
# slugs chain-0826-deliver-*); every other change is listed below this line; the text after the list is the original's.
# measure_seed_v3.sh: measure_seed_v2.sh with the changes below, in a NEW FILE (v2 may still be called by
# deliver_survivors.sh for seeds 55 and 64). Written 2026-09-23T18:5xZ.
#
# Why. v2 was copied from seed-search-1447 with only the study root changed, so it calls
# $S/tools/tree_freshness.py, not_measurable.py, square.py and square_selftest.py, and NONE of the four
# exists in this study's tools/. Its first call, seed57 at 18:28:22Z, died on «can't open file
# tools/tree_freshness.py», took that for a stale tree, then failed to write the refusal too (rc=5,
# no evidence file). DECLARATION.md says the measurer is seed-search-1447/tools/square.py unchanged with
# the same self test summary, so the changes are:
#   1. the four python tools are called from seed-search-1447/tools/ (T below), unchanged;
#   2. the self test summary is seed-search-1447/evidence/square-selftest-summary.csv, and if it is
#      absent this refuses (exit 6) instead of running the self test into the other study's evidence;
#   3. the freshness check tells a missing tool from a stale tree: a missing tool is exit 7 and writes
#      nothing, it is not a refusal of the tree;
#   4. SA_CHECK_ONLY=1 prints what it would run and exits 0, writing nothing;
#   5. it prints the sheet count it expected (the C40 patch_*.bin) and the rows square.py wrote.
# The voxel, the reading of it from the manifest, square.py's arguments and traced_area.py are v2's.
#
# Usage: measure_seed_v3.sh PHerc1447-seedNN
set -u
S=/data/scrollagent/runs/rev1/chain-0826
T=/data/scrollagent/runs/rev1/seed-search-1447/tools
SELFTEST=/data/scrollagent/runs/rev1/seed-search-1447/evidence/square-selftest-summary.csv
PY=/data/scrollagent/.venv/bin/python
A=$1
SCROLL=PHerc0826
say() { echo "$(date -u +%FT%TZ) [$A measure v3] $*"; }
for t in tree_freshness.py not_measurable.py square.py; do
  [ -f "$T/$t" ] || { say "REFUSED: $T/$t absent, nothing measured, nothing written"; exit 7; }
done
[ -f "$SELFTEST" ] || { say "REFUSED: self test summary $SELFTEST absent"; exit 6; }
UM=$($PY -c "import sys;sys.path.insert(0,'/data/scrollagent/pipeline/datasets');import voxel;print(voxel.voxel_um('$SCROLL')[0])")
[[ "$UM" =~ ^[0-9.]+$ ]] || { say "REFUSED: voxel not read: [$UM]"; exit 6; }
say "voxel $UM um, read from the manifest of $SCROLL"
G=$S/out/$A/growth
SHEETS=$(ls $S/out/$A/C40/patch_*.bin 2>/dev/null | wc -l)

if [ "${SA_CHECK_ONLY:-0}" = 1 ]; then
  say "CHECK ONLY: tools from $T, self test $SELFTEST, growth $G, sheets $SHEETS, out evidence/squares-$A.csv and area-$A.csv; nothing run"
  exit 0
fi

if [ -d "$G/surface.bp" ]; then
  $PY $T/tree_freshness.py "$G" > $S/log/freshness-measure-$A.txt 2>&1
  frc=$?
  if [ $frc -ne 0 ]; then
    if grep -q "stale yes" $S/log/freshness-measure-$A.txt; then
      say "REFUSED: $(tail -1 $S/log/freshness-measure-$A.txt)"
      $PY $T/not_measurable.py --arm $A --voxel-um $UM \
          --squares $S/evidence/squares-$A.csv --area $S/evidence/area-$A.csv \
          --reason "more than one growth wrote this tree, so any measurement of it is a measurement of a mixture: $(tail -1 $S/log/freshness-measure-$A.txt | sed 's/,/ /g'); see runs/rev1/growth-bookkeeping/OUTCOME.md"
      exit 5
    fi
    say "freshness check failed without a verdict (rc=$frc): $(tail -1 $S/log/freshness-measure-$A.txt); nothing written"
    exit 7
  fi
  say "freshness: $(tail -1 $S/log/freshness-measure-$A.txt)"
fi

say "delivered sheets: $SHEETS"
if [ "$SHEETS" -eq 0 ]; then
  $PY $T/not_measurable.py --arm $A --voxel-um $UM \
      --squares $S/evidence/squares-$A.csv --area $S/evidence/area-$A.csv \
      --reason "no sheet was delivered for this seed, evidence/runs/$A.csv"
  exit 0
fi

D=$S/out/$A/sheets/patches; mkdir -p $D
for f in $S/out/$A/C40/patch_*.bin; do ln -sf "$f" "$D/$(basename $f)"; done
$PY $T/square.py $D --point $A --out $S/evidence/squares-$A.csv --voxel-um $UM \
  --selftest-summary $SELFTEST > $S/log/square-$A.txt 2>&1
src=$?
say "square rc=$src, sheets expected $SHEETS, rows written $(grep -c "^$A," $S/evidence/squares-$A.csv 2>/dev/null || echo 0)"
$PY /data/scrollagent/pipeline/tools/traced_area.py $S/out/$A/sheets --scroll $SCROLL \
  --csv $S/evidence/area-$A.csv > $S/log/area-$A.txt 2>&1
arc=$?
say "area rc=$arc"
[ $src -eq 0 ] && [ $arc -eq 0 ] || exit 8
