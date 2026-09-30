#!/bin/bash
# rerun_remedy.sh <seed> <drop-list-file> <out-dir>
# stevens-remedy-half-on (DECLARATION.md): a copy of patch-filter-harness-1447/tools/rerun_downstream.sh (its sha256 in
# log/ at the first run) with ONE change, under SA_REMEDY=1: Stevens' method 3 is switched on between vm 10 and a second
# vm 10: badbridges.csv = badbridgess_out.csv without NEW lines; nm 10 $SA_ITERS (OMP_NUM_THREADS=4, cap SA_NM_CAP s);
# cp annealState_out.csv manualBadPatch.csv. With SA_REMEDY=0 the stages are the harness's five, byte for byte the same
# commands. The harness's own tools (inventory, make_view.py, peak.py, one_winding_rows.py) are called unchanged.
#
#   1. Inputs from evidence/inventory-55.csv (tools/inventory.py): the delivering binary (sha256 checked again here),
#      the growth tree, the delivered downstream cap. A seed whose row says rerunnable no is refused (exit 3).
#   2. The drop list (one patch id per line, # comments, empty = keep all) is checked by tools/make_view.py: a
#      malformed line or an id with no patch file is refused (exit 2).
#   3. The view <out-dir>/view: patches/ of symlinks to the kept delivered patch files, rel.csv without the lines
#      naming a dropped id (a byte copy when none is dropped). The delivered trees are never written: patches/
#      (count, latest mtime) and rel.csv (sha256) are fingerprinted before and after, a difference is exit 9.
#   4. The stages as run_seed_v4/v5/v6.sh run them: c, l, vm 10, hm 10, fm 30 10, each with SIMPAPER_OUTPUT_DIR=view,
#      SIMPAPER_SURFACE_ZARR, ZARR_MISSING_LIST=view/missing-C40.txt, SIMPAPER_PATCH_LIMIT=40000, under
#      timeout --foreground -s TERM <what is left of the delivered cap>; rc tested after each, a non zero rc stops
#      (exit 5). Each stage under nice -n 10 and tools/peak.py (peak RSS).
#   5. The measure as measure_seed_v3.sh: sheets/patches/ of symlinks to view/patch_*.bin, square.py with --point
#      <seed> --voxel-um from the manifest and the seed-search-1447 self test summary, then traced_area.py; then
#      tools/one_winding_rows.py (a column only). Any rc non zero: exit 8.
#   6. Rows to <out-dir>/rerun.csv (tool,attempt,quantity,value,what_it_is) through csv.writer.
#   7. SA_PRUNE=1: after the measures, remove view/patches (symlinks), view/rel.csv and view/patch_*_colours.csv
#      and gzip the stage logs (stage c prints about 96 MB on seed169); the sheets, the small stage outputs, the
#      logs and the measures stay.
# Never edit this file while a rerun runs: bash reads it as it goes.
# SA_CHECK_ONLY=1: every check of 1 and 2, the plan and the fingerprint printed; nothing created, nothing run.
# Refuses an <out-dir> that exists and is not empty, or that lies under seeds-at-scale-1447 (exit 2).
set -u
H=/data/scrollagent/runs/rev1/patch-filter-harness-1447
S=/data/scrollagent/runs/rev1/seeds-at-scale-1447
R1=/data/scrollagent/runs/rev1
PY=/data/scrollagent/.venv/bin/python
ZARR=/data/scrollagent/data/datasets/PHerc1447/0
SQT=/data/scrollagent/runs/rev1/seed-search-1447/tools
SELFTEST=/data/scrollagent/runs/rev1/seed-search-1447/evidence/square-selftest-summary.csv
TOOL=stevens-remedy-half-on/tools/rerun_remedy.sh
REMEDY=${SA_REMEDY:-0}; ITERS=${SA_ITERS:-}; NMCAP=${SA_NM_CAP:-7200}
[ "$REMEDY" = 0 ] || [[ "$ITERS" =~ ^[0-9]+$ ]] || { echo "SA_REMEDY=1 needs SA_ITERS" >&2; exit 2; }
LIM=40000
PEAK_GB=${SA_PEAK_GB:-8}      # declared peak of one rerun; the start waits while MemAvailable - PEAK_GB < 20 GB
export TMPDIR=/data/tmp OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 BLOSC_NTHREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
[ $# -eq 3 ] || { echo "usage: rerun_downstream.sh <seed> <drop-list-file> <out-dir>" >&2; exit 2; }
A=$1; DROP=$2; O=$3
say() { echo "$(date -u +%FT%TZ) [$A rerun] $*"; }

inv() {  # the inventory value of column $1 for this seed; a missing key or seed raises
  $PY - "$H/evidence/inventory-55.csv" "$A" "$1" <<'PYEOF'
import csv, sys
p, a, k = sys.argv[1:4]
R = [r for r in csv.DictReader(l for l in open(p, newline="") if not l.startswith('"#')) if r["attempt"] == a]
if len(R) != 1:
    sys.exit("inventory: %d rows for %s" % (len(R), a))
print(R[0][k])
PYEOF
}
G=$S/out/$A/growth
RR=$(inv rerunnable) || { say "REFUSED: $A not in the inventory"; exit 3; }
[ "$RR" = yes ] || { say "REFUSED: inventory says not rerunnable: $(inv why_not)"; exit 3; }
BIN=$R1/$(inv binary_path) || exit 3
BSHA=$(inv binary_sha256) || exit 3
CAP=$(inv downstream_cap_seconds) || exit 3
[[ "$CAP" =~ ^[0-9]+$ ]] || { say "REFUSED: cap [$CAP]"; exit 3; }
[ -x "$BIN" ] && [ "$(sha256sum "$BIN" | cut -d' ' -f1)" = "$BSHA" ] || { say "REFUSED: binary $BIN absent or its sha256 is not $BSHA"; exit 3; }
[ -f "$DROP" ] || { say "REFUSED: no drop list file $DROP"; exit 2; }
OABS=$(realpath -m "$O")
case "$OABS" in "$S"|"$S"/*) say "REFUSED: out-dir $OABS is inside seeds-at-scale-1447"; exit 2 ;; esac
if [ -e "$OABS" ] && [ -n "$(ls -A "$OABS" 2>/dev/null)" ]; then say "REFUSED: out-dir $OABS exists and is not empty"; exit 2; fi
PLAN=$($PY $H/tools/make_view.py --check "$G" "$DROP") || { say "REFUSED: drop list $DROP"; exit 2; }
fingerprint() { echo "patches $(find "$G/patches" -maxdepth 1 -name '*.bin' | wc -l) latest $(find "$G/patches" "$G/rel.csv" -maxdepth 1 -printf '%T@\n' | sort -n | tail -1) rel $(sha256sum "$G/rel.csv" | cut -c1-16)"; }
FP0=$(fingerprint)
UM=$($PY -c "import sys;sys.path.insert(0,'/data/scrollagent/pipeline/datasets');import voxel;print(voxel.voxel_um('PHerc1447')[0])")
[[ "$UM" =~ ^[0-9.]+$ ]] || { say "REFUSED: voxel not read: [$UM]"; exit 3; }
for t in square.py; do [ -f "$SQT/$t" ] || { say "REFUSED: $SQT/$t absent"; exit 3; }; done
[ -f "$SELFTEST" ] || { say "REFUSED: $SELFTEST absent"; exit 3; }

if [ "${SA_CHECK_ONLY:-0}" = 1 ]; then
  say "CHECK ONLY: binary $BIN sha ${BSHA:0:12} (equal), cap $CAP s (delivered), voxel $UM um"
  say "CHECK ONLY: drop list $DROP: $PLAN"
  say "CHECK ONLY: growth $G fingerprint [$FP0]"
  say "CHECK ONLY: remedy $REMEDY iterations [$ITERS] nm cap $NMCAP s; df /data free $(df -B1G --output=avail /data | tail -1 | tr -d ' ') GB"
  say "CHECK ONLY: would build $OABS/view, run c, l, vm 10, [remedy: bridges, nm 10 $ITERS, manualBadPatch, vm 10,] hm 10, fm 30 10 with SIMPAPER_PATCH_LIMIT=$LIM, then square.py, traced_area.py, one_winding_rows.py into $OABS; prune ${SA_PRUNE:-0}; nothing created, nothing run"
  exit 0
fi

while :; do
  m=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  [ $((m - PEAK_GB)) -ge 20 ] && break
  say "hold: MemAvailable $m GB, declared peak $PEAK_GB GB"; sleep 60
done
mkdir -p "$OABS/log" || exit 2
V=$OABS/view
RC=$OABS/rerun.csv
echo "tool,attempt,quantity,value,what_it_is" > "$RC"
row() { $PY -c "import csv,sys; csv.writer(open(sys.argv[1],'a',newline=''),lineterminator='\n').writerow(sys.argv[2:])" "$RC" "$TOOL" "$A" "$1" "$2" "$3" || { say "FATAL: row $1 not written"; exit 6; }; }
cp "$DROP" "$OABS/drop-list.txt"
row binary_sha256 "$BSHA" "the delivering binary, sha256 checked before the run ($BIN)"
row drop_list_sha256 "$(sha256sum "$DROP" | cut -d' ' -f1)" "the drop list as given, copied to drop-list.txt"
row growth_fingerprint_before "$FP0" "delivered growth tree: patch files, latest mtime of patches/ and rel.csv, rel.csv sha256 prefix"
t0=$(date +%s)
VIEWLINE=$($PY $H/tools/make_view.py "$G" "$DROP" "$V") || { say "view not built"; row downstream_return_code "not run" "the view could not be built"; exit 5; }
say "view: $VIEWLINE in $(( $(date +%s)-t0 )) s"
for kvp in $VIEWLINE; do row "view_${kvp%%=*}" "${kvp#*=}" "tools/make_view.py on the delivered growth tree and the drop list"; done
d0=$(date +%s)
row remedy "$REMEDY" "SA_REMEDY: 1 = method 3 on (nm 10 $ITERS between two vm 10), 0 = the harness's five stages"
if [ "$REMEDY" = 1 ]; then STAGES=("c" "l" "vm 10" "BRIDGES" "nm 10 $ITERS" "MANUAL" "vm 10" "hm 10" "fm 30 10")
else STAGES=("c" "l" "vm 10" "hm 10" "fm 30 10"); fi
NMSEC=0; VMN=0
for st in "${STAGES[@]}"; do
  if [ "$st" = BRIDGES ]; then
    grep -v NEW "$V/badbridgess_out.csv" > "$V/badbridges.csv" || true
    row bridges_in_file "$(grep -cv NEW "$V/badbridgess_out.csv")" "non NEW lines of badbridgess_out.csv written by the first vm 10"
    row bridges_in_badbridges_csv "$(grep -c . "$V/badbridges.csv")" "lines of badbridges.csv as nm reads it"
    cp "$V/badbridgess_out.csv" "$OABS/badbridgess_out-first-vm.csv"; continue
  fi
  if [ "$st" = MANUAL ]; then
    [ -f "$V/annealState_out.csv" ] || { say "no annealState_out.csv"; row downstream_return_code 7 "nm wrote no annealState_out.csv"; exit 5; }
    cp "$V/annealState_out.csv" "$V/manualBadPatch.csv"
    row anneal_excluded_patches "$(grep -c . "$V/manualBadPatch.csv")" "lines of annealState_out.csv copied to manualBadPatch.csv"
    row badpatches_csv_lines "$(grep -c . "$V/badpatches.csv")" "lines of badpatches.csv written by stage c"
    continue
  fi
  if [ "${st%% *}" = nm ]; then
    tag=$(echo $st | tr ' ' '_'); n0=$(date +%s)
    ( cd "$OABS" && SIMPAPER_OUTPUT_DIR=$V SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$V/missing-C40.txt SIMPAPER_PATCH_LIMIT=$LIM OMP_NUM_THREADS=${SA_NM_THREADS:-4} \
        nice -n 10 $PY $H/tools/peak.py "$OABS/log/peak-$tag.txt" timeout --foreground -s TERM $NMCAP "$BIN" $st ) > "$OABS/log/stage-$tag.txt" 2>&1
    rc=$?; NMSEC=$(( $(date +%s)-n0 ))
    IFS=, read prc psec pkb < "$OABS/log/peak-$tag.txt"
    say "stage '$st' rc=$rc in $psec s, peak RSS $pkb kB"
    row "downstream_stage_${tag}_seconds" "$psec" "wall clock of the annealing (tools/peak.py), outside the delivered cap"
    row "downstream_stage_${tag}_peak_rss_kb" "$pkb" "ru_maxrss (tools/peak.py)"
    [ $rc -ne 0 ] && { say "stage '$st' failed"; row downstream_return_code "$rc" "the stage '$st' returned it"; exit 5; }
    continue
  fi
  left=$(( CAP - ($(date +%s)-d0) + NMSEC ))
  [ $left -lt 1 ] && { say "cap spent before stage '$st'"; row downstream_return_code 124 "the delivered cap $CAP s was reached"; exit 5; }
  tag=$(echo $st | tr ' ' '_')
  if [ "$st" = "vm 10" ]; then VMN=$((VMN+1)); [ $VMN = 2 ] && tag=vm_10_second; fi
  ( cd "$OABS" && SIMPAPER_OUTPUT_DIR=$V SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$V/missing-C40.txt SIMPAPER_PATCH_LIMIT=$LIM \
      nice -n 10 $PY $H/tools/peak.py "$OABS/log/peak-$tag.txt" timeout --foreground -s TERM $left "$BIN" $st ) > "$OABS/log/stage-$tag.txt" 2>&1
  rc=$?
  IFS=, read prc psec pkb < "$OABS/log/peak-$tag.txt"
  say "stage '$st' rc=$rc in $psec s, peak RSS $pkb kB, sheets $(ls $V/patch_*.bin 2>/dev/null | wc -l)"
  row "downstream_stage_${tag}_seconds" "$psec" "wall clock of this stage (tools/peak.py)"
  row "downstream_stage_${tag}_peak_rss_kb" "$pkb" "ru_maxrss of the stage's children (tools/peak.py)"
  [ $rc -ne 0 ] && { say "stage '$st' failed"; row downstream_return_code "$rc" "the stage '$st' returned it"; exit 5; }
done
NS=$(ls $V/patch_*.bin 2>/dev/null | wc -l)
row downstream_return_code 0 "every stage returned zero: ${STAGES[*]}"
row downstream_wall_clock_seconds "$(( $(date +%s)-d0 ))" "wall clock of every stage together, the annealing included"
row sheets "$NS" "patch_<n>.bin written by the fm stage"
D=$OABS/sheets/patches; mkdir -p "$D"
for f in $V/patch_*.bin; do [ -e "$f" ] && ln -s "$f" "$D/$(basename $f)"; done
m0=$(date +%s)
if [ "$NS" -gt 0 ]; then
  nice -n 10 $PY $H/tools/peak.py "$OABS/log/peak-square.txt" $PY $SQT/square.py "$D" --point "$A" --out "$OABS/squares.csv" \
    --voxel-um "$UM" --selftest-summary "$SELFTEST" > "$OABS/log/square.txt" 2>&1; src=$?
  nice -n 10 $PY $H/tools/peak.py "$OABS/log/peak-area.txt" $PY /data/scrollagent/pipeline/tools/traced_area.py "$OABS/sheets" \
    --scroll PHerc1447 --csv "$OABS/area.csv" > "$OABS/log/area.txt" 2>&1; arc=$?
  if [ $src -eq 0 ]; then
    nice -n 10 $PY $H/tools/peak.py "$OABS/log/peak-onewinding.txt" $PY $H/tools/one_winding_rows.py "$A" "$D" "$OABS/squares.csv" \
      "$OABS/one-winding.csv" > "$OABS/log/one-winding.txt" 2>&1; orc=$?
  else orc="not run"; fi
else
  src="not run"; arc="not run"; orc="not run"
fi
say "measures: square rc=$src, area rc=$arc, one winding rc=$orc in $(( $(date +%s)-m0 )) s"
row square_return_code "$src" "seed-search-1447/tools/square.py as measure_seed_v3.sh calls it"
row area_return_code "$arc" "pipeline/tools/traced_area.py as measure_seed_v3.sh calls it"
row one_winding_return_code "$orc" "tools/one_winding_rows.py, a column only"
row measure_wall_clock_seconds "$(( $(date +%s)-m0 ))" "square, area and one winding together"
for k in square area onewinding; do
  [ -f "$OABS/log/peak-$k.txt" ] && { IFS=, read prc psec pkb < "$OABS/log/peak-$k.txt"; row "${k}_peak_rss_kb" "$pkb" "ru_maxrss (tools/peak.py)"; }
done
row bytes_written_before_prune "$(du -sb "$OABS" | cut -f1)" "du -sb of the out-dir after the measures (symlinks count as links)"
if [ "${SA_PRUNE:-0}" = 1 ]; then
  rm -rf "$V/patches" "$V/rel.csv"; rm -f $V/patch_*_colours.csv; gzip -f "$OABS"/log/stage-*.txt
  row bytes_kept_after_prune "$(du -sb "$OABS" | cut -f1)" "du -sb after SA_PRUNE removed view/patches, view/rel.csv, colours csv and gzipped the stage logs"
fi
FP1=$(fingerprint)
row growth_fingerprint_after "$FP1" "the same fingerprint after the run"
[ "$FP0" = "$FP1" ] || { say "ERROR: the delivered growth tree changed during the run: [$FP0] [$FP1]"; exit 9; }
say "done, sheets $NS, out $OABS"
[ "$src" = 0 ] && [ "$arc" = 0 ] && [ "$orc" = 0 ] || exit 8
