#!/bin/bash
# measure_seed_v2.sh: measure_seed.sh with ONE change, in a NEW FILE and NOT in place.
#
# Not in place because tools/finish_seed.sh is executing for seeds 11 and 35 and calls
# measure_seed.sh at the end of their chain. Editing it now would change what two runs of four
# hours do when they land, without them having been launched against it. Their trees are already
# known fresh: the survey of evidence/tree-freshness.csv gives them gaps of 37.7 s and 62.9 s
# against a threshold of 1800.
#
# The change, on the direction of 2026-09-21T15:36:28Z, «every finisher and every measurement
# checks the tree's freshness first»: a measurement made on a tree that two growths wrote is a
# measurement of a mixture, so it is refused and the refusal is written where the numbers would
# have gone. It writes the two CSVs as not measurable with the reason, which is what this study
# already does for a seed with no sheet: a refusal must leave a trace in the evidence, not only
# in a log, or the next reader sees an absent file and calls it an absent run.
#
# --- what follows is measure_seed.sh unchanged ---
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

G=$S/out/$A/growth
if [ -d "$G/surface.bp" ] && ! $PY $S/tools/tree_freshness.py "$G" > $S/log/freshness-measure-$A.txt 2>&1; then
  say "REFUSED: $(tail -1 $S/log/freshness-measure-$A.txt)"
  $PY $S/tools/not_measurable.py --arm $A --voxel-um $UM \
      --squares $S/evidence/squares-$A.csv --area $S/evidence/area-$A.csv \
      --reason "more than one growth wrote this tree, so any measurement of it is a measurement of a mixture: $(tail -1 $S/log/freshness-measure-$A.txt | sed 's/,/ /g'); see runs/rev1/growth-bookkeeping/OUTCOME.md"
  exit 5
fi

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
