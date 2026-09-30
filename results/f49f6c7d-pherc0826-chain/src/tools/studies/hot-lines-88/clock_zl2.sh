#!/bin/bash
# clock_zl2.sh: clock_zl.sh with only the L label changed to lz4hc 5 (DECLARATION.md addition of 10:5xZ).
# clock_zl.sh: hot-lines-88 (DECLARATION.md, C), the quiet clock of arms Z and L. A copy of
# growth-lto-pgo-1447/tools/clock_runner.sh (not touched) with only these changes:
#   - one binary for both arms, the MLP binary of PHerc0826-seed237 (memory-profile-0826-mlpz/scratch/bin-MLP, sha typed
#     df299a99); the arms differ only in the growth zarr: Z = codec-z-0826/scratch/z/0, L = hot-lines-88/scratch/l/0 (only
#     when evidence/identity-l-summary.csv says verdict identical); manifest PHerc0826/chunks.txt;
#   - chain-0826's environment read from chain-0826/scratch/deliver-settings.env and checked (512, 1, passive, 3);
#   - the tree bar: growth-lto-pgo-1447/scratch/identity/unchanged/PHerc0826-seed237/growth, identical 3830 of 3830;
#   - rotations Z L / L Z / Z L;
#   - waits (60 s steps, until WAIT_UNTIL) for growth-exact-fixes-88's clock to have ended: its scratch/clock.done, or a
#     ledger row growth-exact-fixes-88-clock-not-run or growth-exact-fixes-88-F2-dropped; and for neither
#     growth-exact-fixes-88/scratch/CLOCK.lock nor growth-lto-pgo-1447/scratch/CLOCK.lock to exist; then writes those two
#     AND hot-lines-88/scratch/CLOCK.lock (removed at exit, each only if it still names this PID); then waits for no other
#     simpaper10, vc_grow_seg_from_seed, perf or compiler; then the quiet test (cores busy under 2.0 over 60 s);
#   - evidence names: evidence/clock-runs.csv, clock-machine.csv, clock-summary.csv (tools/clock_summary_zl.py),
#     clock-identity-<tag>.csv; scratch/clock-<tag>; scratch/clock.done.
# Touches no process but its own growths. Never edit this file while it runs.
set -u
Q=/data/scrollagent/runs/rev1/hot-lines-88
R1=/data/scrollagent/runs/rev1
E=$R1/growth-exact-fixes-88
QW=$R1/quiet-window-2026-09-27
H=$R1/patch-filter-harness-1447
GM=$R1/growth-memory-1447
C=$R1/chain-0826
PY=/data/scrollagent/.venv/bin/python
LEDGER=/data/scrollagent/ledger/ledger.csv
MANIFEST=/data/scrollagent/data/datasets/PHerc0826/chunks.txt
TOOL=hot-lines-88/tools/clock_zl2.sh
A=PHerc0826-seed237
DG=$R1/growth-lto-pgo-1447/scratch/identity/unchanged/$A/growth
WANT="identical 3830 of 3830"
WAIT_UNTIL=2026-09-28T08:00:00Z
LAST_START=2026-09-28T09:00:00Z
LOCK=$Q/scratch/CLOCK.lock; LOCKE=$E/scratch/CLOCK.lock; LOCKP=$R1/growth-lto-pgo-1447/scratch/CLOCK.lock
R=$Q/evidence/clock-runs.csv
MC=$Q/evidence/clock-machine.csv
SU=$Q/evidence/clock-summary.csv
export TMPDIR=/data/tmp
NP=$(nproc)
BIN=$R1/memory-profile-0826-mlpz/scratch/bin-MLP/$A/simpaper10
SHA=df299a99a7d5389fe87f4610afadd7f6cb35ce783266eb7e737e46450f702163
declare -A ZARR
ZARR[Z]=$R1/codec-z-0826/scratch/z/0; ZARR[L]=$Q/scratch/l/0
ROT=("Z L" "L Z" "Z L")

say() { echo "$(date -u +%FT%TZ) [clock] $*"; }
csvrow() { $PY -c "import csv,sys; csv.writer(open(sys.argv[1],'a',newline=''),lineterminator='\n').writerow(sys.argv[2:])" "$@"; }
ledger() { csvrow "$LEDGER" "$(date -u +%FT%TZ)" rev1 coordinator-agent "$1" "$2" "$TOOL" "" "" 0 "$3"; }
epoch() { date -u -d "$1" +%s; }
memgb() { awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo; }
diskgb() { df -B1G --output=avail /data | tail -1 | tr -d ' '; }
stat_ticks() { local c a1 a2 a3 a4 a5 a6 a7 a8 r; read -r c a1 a2 a3 a4 a5 a6 a7 a8 r < /proc/stat; echo "$((a1+a2+a3+a4+a5+a6+a7+a8)) $((a4+a5))"; }
busy_between() {
  local t0 i0 t1 i1; read -r t0 i0 <<< "$1"; read -r t1 i1 <<< "$2"
  awk -v dt=$((t1-t0)) -v di=$((i1-i0)) -v n=$NP 'BEGIN{ if (dt>0) printf "%.2f", (dt-di)/dt*n; else print "not measurable"}'
}
growths() {  # growth processes "pid comm", leaving out children of pid $1
  ps -eo pid=,ppid=,comm=,args= | awk -v me="${1:-0}" '{ b=$4; sub(/.*\//, "", b) }
    ($3=="simpaper10" || $3 ~ /^vc_grow_seg/ || b=="simpaper10" || b=="vc_grow_seg_from_seed") && $2!=me && $1!=me { printf "%s%s %s", (n++ ? "; " : ""), $1, $3 }'
}
foreign() {  # any simpaper10, vc_grow_seg_from_seed, perf or compiler
  ps -eo pid=,comm=,args= | awk '{ b=$3; sub(/.*\//, "", b) } ($2=="simpaper10" || $2 ~ /^vc_grow_seg/ || $2=="perf" || $2=="cc1plus" || $2=="lto1" || b=="simpaper10" || b=="perf" || b=="vc_grow_seg_from_seed") { printf "%s%s %s", (n++ ? "; " : ""), $1, $2 }'
}
other_clock_ended() {
  [ -e $E/scratch/clock.done ] && { echo "growth-exact-fixes-88/scratch/clock.done"; return 0; }
  local r; r=$(grep -m1 -oE "growth-exact-fixes-88-(clock-not-run|F2-dropped)" $LEDGER) && { echo "ledger row $r"; return 0; }
  return 1
}
CT=/data/tmp/clock-zl-times-$$.txt
childcpu() {
  times > $CT
  awk 'NR==2 { s=0; for (k=1; k<=2; k++) { x=$k; m=x; sub(/m.*/, "", m); sec=x; sub(/.*m/, "", sec); sub(/s/, "", sec); s+=m*60+sec }; printf "%.2f", s }' $CT
}

for f in $R $MC $SU; do [ -e $f ] && { say "REFUSED: $f exists"; exit 2; }; done
for f in $H/tools/peak.py $GM/tools/tree_identity.py $QW/tools/busy_procs.py $Q/tools/clock_summary_zl.py $MANIFEST ${ZARR[Z]}/.zarray; do
  [ -e "$f" ] || { say "REFUSED: $f absent"; exit 3; }; done
[ -d "$DG/patches" ] && [ -f "$DG/rel.csv" ] || { say "REFUSED: reference tree $DG absent"; exit 3; }
[ "$(sha256sum $BIN | cut -d' ' -f1)" = "$SHA" ] || { say "REFUSED: $BIN is not sha ${SHA:0:12}"; exit 3; }
declare -A EV
for k in SIMPAPER_SHARED_CHUNKS SIMPAPER_FORCE_THREADS OMP_WAIT_POLICY OMP_NUM_THREADS; do EV[$k]=$(sed -n "s/^$k=//p" $C/scratch/deliver-settings.env); done
ENV="SIMPAPER_SHARED_CHUNKS=${EV[SIMPAPER_SHARED_CHUNKS]} SIMPAPER_FORCE_THREADS=${EV[SIMPAPER_FORCE_THREADS]} OMP_WAIT_POLICY=${EV[OMP_WAIT_POLICY]} OMP_NUM_THREADS=${EV[OMP_NUM_THREADS]}"
[ "$ENV" = "SIMPAPER_SHARED_CHUNKS=512 SIMPAPER_FORCE_THREADS=1 OMP_WAIT_POLICY=passive OMP_NUM_THREADS=3" ] || { say "REFUSED: settings environment [$ENV]"; exit 3; }
LV=$(awk -F, '$1=="verdict"{print $2}' $Q/evidence/identity-l-summary.csv 2>/dev/null)
[ "$LV" = identical ] && [ -f ${ZARR[L]}/.zarray ] || { say "REFUSED: L copy identity verdict [$LV]"; exit 3; }
say "armed (pid $$), waiting for growth-exact-fixes-88's clock to have ended and for both clock locks to be absent"
WU=$(epoch $WAIT_UNTIL)
trap 'for l in $LOCK $LOCKE $LOCKP; do grep -q "pid $$ " "$l" 2>/dev/null && rm -f "$l"; done; rm -f $CT $CT.c0 $CT.c1' EXIT
n=0
while :; do
  oc=$(other_clock_ended) && [ ! -e $LOCKE ] && [ ! -e $LOCKP ] && [ ! -e $LOCK ] && break
  [ "$(date +%s)" -ge "$WU" ] && { say "STOP: at $WAIT_UNTIL the other clock has not ended [${oc:-no}] or a lock exists"; ledger hot-lines-88-clock-not-run "clock not run: growth-exact-fixes-88's clock not ended or a clock lock present at $WAIT_UNTIL" "runs/rev1/hot-lines-88/log/clock.txt"; exit 4; }
  [ $((n % 15)) = 0 ] && say "waiting: other clock ended [${oc:-no}], locks: $(cat $LOCKE $LOCKP 2>/dev/null | tr '\n' ' ')"; n=$((n+1)); sleep 60
done
say "other clock ended: $oc"
for l in $LOCK $LOCKE $LOCKP; do echo "$(date -u +%FT%TZ) pid $$ $TOOL" > "$l"; done
say "locks written: $LOCK $LOCKE $LOCKP"
n=0
while :; do
  x=$(foreign); [ -z "$x" ] && break
  [ "$(date +%s)" -ge "$WU" ] && { say "STOP: foreign growth, perf or compiler still at $WAIT_UNTIL: $x"; ledger hot-lines-88-clock-not-run "clock not run: foreign process at $WAIT_UNTIL: $x" "runs/rev1/hot-lines-88/log/clock.txt"; exit 4; }
  [ $((n % 5)) = 0 ] && say "locks held, waiting for foreign processes: $x"; n=$((n+1)); sleep 60
done
echo "tool,utc,tag,cores_busy_60s,loadavg_1min,mem_available_kb,growths_of_others" > $MC
while :; do
  s0=$(stat_ticks); sleep 60; s1=$(stat_ticks); QB=$(busy_between "$s0" "$s1"); QG=$(foreign)
  csvrow $MC $TOOL "$(date -u +%FT%TZ)" quiet-test "$QB" "$(cut -d' ' -f1 /proc/loadavg)" "$(awk '/MemAvailable/{print $2}' /proc/meminfo)" "${QG:-none}"
  if [ -z "$QG" ] && awk -v b="$QB" 'BEGIN{exit !(b+0 < 2.0)}'; then say "quiet: cores busy $QB over 60 s, no growth"; break; fi
  say "not quiet: cores busy $QB over 60 s; growths or perf [${QG:-none}]; over 1 per cent [$($PY $QW/tools/busy_procs.py 5 1 | cut -c1-300)]"
  [ "$(date +%s)" -ge "$WU" ] && { say "STOP: not quiet by $WAIT_UNTIL"; ledger hot-lines-88-clock-not-run "clock not run: not quiet by $WAIT_UNTIL (cores busy $QB)" "runs/rev1/hot-lines-88/evidence/clock-machine.csv"; exit 4; }
done

echo "tool,tag,arm,rotation,order,started_utc,ended_utc,return_code,wall_clock_seconds,peak_rss_kb,cores_busy_over_run,run_cpu_seconds,cores_busy_others_over_run,cores_busy_60s_samples,other_growths_start,other_growths_end,other_growths_in_samples,busy_procs_start,busy_procs_end,growth_identity,patch_files,tree_bytes_removed,binary,binary_sha256,zarr,env,counted,why_not_counted" > $R
LE=$(epoch $LAST_START)
ORDER=0; STOPWHY="three rotations done"
for r in 0 1 2; do
  for arm in ${ROT[$r]}; do
    if [ "$(date +%s)" -ge "$LE" ]; then STOPWHY="no start after $LAST_START"; break 2; fi
    w=0
    until [ "$(memgb)" -ge 30 ] && [ "$(diskgb)" -ge 20 ]; do
      [ "$(date +%s)" -ge "$LE" ] && { STOPWHY="memory or disk gate unmet until $LAST_START"; break 3; }
      [ $((w % 5)) = 0 ] && say "hold: MemAvailable $(memgb) GB (30), /data free $(diskgb) GB (20)"; w=$((w+1)); sleep 60
    done
    [ "$(sha256sum "$BIN" | cut -d' ' -f1)" = "$SHA" ] || { STOPWHY="binary changed"; break 2; }
    ORDER=$((ORDER+1)); tg=$arm-r$((r+1))
    W=$Q/scratch/clock-$tg; G=$W/growth; rm -rf $W; mkdir -p $G/surface.bp/surface $G/boundary.bp/surface $G/patches
    OGS=$(growths 0); BPS=$($PY $QW/tools/busy_procs.py 5 1)
    childcpu > $CT.c0; c0=$(cat $CT.c0); s0=$(stat_ticks); e0=$(date +%s.%N); ST=$(date -u +%FT%TZ)
    ( cd $W
      for kv in $ENV; do export "$kv"; done
      SIMPAPER_OUTPUT_DIR=$G SIMPAPER_SURFACE_ZARR=${ZARR[$arm]} ZARR_MISSING_LIST=$G/missing.txt ZARR_CHUNK_MANIFEST=$MANIFEST \
      exec nice -n 10 $PY $H/tools/peak.py $W/peak-growth.txt $BIN g 36000 ) > $W/growth.log 2>&1 &
    P=$!
    say "started $tg (rotation $((r+1)), order $ORDER), zarr ${ZARR[$arm]}, peak.py pid $P"
    SAMP=""; OGI=""; sp=$(stat_ticks); nx=$(( $(date +%s) + 60 ))
    while :; do
      st=""; read -r _ _ st _ 2>/dev/null < /proc/$P/stat
      [ -z "$st" ] || [ "$st" = Z ] && break
      sleep 5
      if [ "$(date +%s)" -ge "$nx" ]; then
        sn=$(stat_ticks); b=$(busy_between "$sp" "$sn"); sp=$sn; nx=$(( $(date +%s) + 60 ))
        og=$(growths $P); [ -n "$og" ] && OGI="${OGI:+$OGI | }$(date -u +%H:%M:%S) $og"
        SAMP="${SAMP:+$SAMP }$b"
        csvrow $MC $TOOL "$(date -u +%FT%TZ)" $tg "$b" "$(cut -d' ' -f1 /proc/loadavg)" "$(awk '/MemAvailable/{print $2}' /proc/meminfo)" "${og:-none}"
      fi
    done
    wait $P 2>/dev/null
    e1=$(date +%s.%N); s1=$(stat_ticks); childcpu > $CT.c1; c1=$(cat $CT.c1); EN=$(date -u +%FT%TZ)
    OGE=$(growths 0); BPE=$($PY $QW/tools/busy_procs.py 5 1)
    CB=$(busy_between "$s0" "$s1")
    RCPU=$(awk -v a=$c0 -v b=$c1 'BEGIN{printf "%.1f", b-a}')
    CO=$(awk -v cb="$CB" -v rc=$RCPU -v e0=$e0 -v e1=$e1 'BEGIN{ w=e1-e0; if (w>0 && cb+0==cb) printf "%.2f", cb - rc/w; else print "not measurable"}')
    if [ -s $W/peak-growth.txt ]; then IFS=, read prc psec pkb < $W/peak-growth.txt; else prc="not measurable"; psec="not measurable"; pkb="not measurable"; fi
    np=$(ls $G/patches 2>/dev/null | wc -l)
    gid=$($PY $GM/tools/tree_identity.py $DG $G $Q/evidence/clock-identity-$tg.csv growth)
    bytes=$(du -sB1 $G | cut -f1); rm -rf $G; gzip -f $W/growth.log
    why=""
    [ "$prc" = 0 ] || why="${why:+$why; }rc $prc"
    [ "$gid" = "$WANT" ] || why="${why:+$why; }tree $gid"
    [ -z "$OGS" ] || why="${why:+$why; }other growth at start"
    [ -z "$OGE" ] || why="${why:+$why; }other growth at end"
    [ -z "$OGI" ] || why="${why:+$why; }other growth in a sample"
    awk -v c="$CO" 'BEGIN{exit !(c+0==c && c+0 < 1.0)}' || why="${why:+$why; }others $CO not under 1.0"
    cnt=yes; [ -n "$why" ] && cnt=no
    csvrow $R $TOOL $tg $arm $((r+1)) $ORDER $ST $EN "$prc" "$psec" "$pkb" "$CB" "$RCPU" "$CO" "${SAMP:-none}" "${OGS:-none}" "${OGE:-none}" "${OGI:-none}" "$BPS" "$BPE" "$gid" "$np" "$bytes" "${BIN#/data/scrollagent/runs/rev1/}" "$SHA" "${ZARR[$arm]#/data/scrollagent/runs/rev1/}" "$ENV" $cnt "${why:-}"
    say "$tg rc $prc, $psec s, $pkb kB, cores busy $CB (run cpu $RCPU s, others $CO), $gid, counted $cnt ${why:+($why)}"
  done
done
say "runs ended: $STOPWHY; $ORDER runs"
for l in $LOCK $LOCKE $LOCKP; do grep -q "pid $$ " "$l" 2>/dev/null && rm -f "$l"; done; say "locks removed"
LINE=$($PY $Q/tools/clock_summary_zl.py $R $SU)
say "summary: $LINE"
ledger hot-lines-88-clock "quiet clock on $A, MLP binary, arms Z (zstd 1 no shuffle) and L (lz4hc 5 no shuffle) growth zarr, one growth at a time, $ORDER runs ($STOPWHY); rule declared in DECLARATION.md C (L median below Z's minimum, CPU and wall): $LINE" "runs/rev1/hot-lines-88/evidence/clock-summary.csv; runs/rev1/hot-lines-88/evidence/clock-runs.csv; runs/rev1/hot-lines-88/evidence/clock-machine.csv"
touch $Q/scratch/clock.done
say "done"
