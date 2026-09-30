#!/bin/bash
# seed-search-1447: measure one delivered seed at the PUBLISHED voxel of PHerc. 1447, read from
# its own manifest through pipeline/datasets/voxel.py, which gives 8.640 um. Copied from
# base-on-1447/tools/measure_arm.sh with the study root and the per seed paths changed.
#
# Nothing here carries a default: 9.362 is the reference scroll's value and passing it would make
# every millimetre 8.4 per cent too large. When the seed delivered no sheet, the two CSVs are
# written as not measurable with the reason, never as zero.
#
# Usage: measure_seed.sh PHerc1447-seedNN
set -u
S=/data/scrollagent/runs/rev1/seed-search-1447
PY=/data/scrollagent/.venv/bin/python
A=$1
SCROLL=PHerc1447
UM=$($PY -c "import sys;sys.path.insert(0,'/data/scrollagent/pipeline/datasets');import voxel;print(voxel.voxel_um('$SCROLL')[0])")
say() { echo "$(date -u +%FT%TZ) [$A] $*"; }
say "voxel $UM um, read from the manifest of $SCROLL"

SHEETS=$(ls $S/out/$A/C40/patch_*.bin 2>/dev/null | wc -l)
say "delivered sheets: $SHEETS"
if [ "$SHEETS" -eq 0 ]; then
  $PY $S/tools/not_measurable.py --arm $A --voxel-um $UM \
      --squares $S/evidence/squares-$A.csv --area $S/evidence/area-$A.csv \
      --reason "no sheet was delivered for this seed, evidence/runs/$A.csv"
  exit 0
fi

[ -f $S/evidence/square-selftest-summary.csv ] || $PY $S/tools/square_selftest.py > $S/log/selftest.txt 2>&1
D=$S/out/$A/sheets/patches; mkdir -p $D
for f in $S/out/$A/C40/patch_*.bin; do ln -sf "$f" "$D/$(basename $f)"; done
$PY $S/tools/square.py $D --point $A --out $S/evidence/squares-$A.csv --voxel-um $UM \
  --selftest-summary $S/evidence/square-selftest-summary.csv > $S/log/square-$A.txt 2>&1
say "square rc=$?"
$PY /data/scrollagent/pipeline/tools/traced_area.py $S/out/$A/sheets --scroll $SCROLL \
  --csv $S/evidence/area-$A.csv > $S/log/area-$A.txt 2>&1
say "area rc=$?"
