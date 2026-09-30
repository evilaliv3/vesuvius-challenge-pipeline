#!/bin/bash
# clock_fixes.sh <stack arm>: growth-exact-fixes-88's quiet clock (DECLARATION.md, step 4). A copy of
# growth-lto-pgo-1447/tools/clock_runner.sh (not touched) with only these changes:
#   - arms HV3 and STACK; STACK = this study's scratch/bin-<stack arm>/<seed>/simpaper10, sha equal to evidence/binary-gate.csv's
#     differs_from_HV3_reference row, evidence/fma-check.csv 0/yes for that sha, evidence/identity-summary.csv identity_holds
#     yes for the stack arm (else refused);
#   - two phases, one after the other: PHerc1447-seed1111 in HV3's environment on 1447's zarr (HV3 =
#     growth-avx512-1447/scratch/bin/avx512/simpaper10, sha 0c03fd19...; reference tree seeds-at-scale-1447/out/<seed>/growth),
#     then PHerc0826-seed237 in chain-0826's environment (cap 512) with BOTH arms on the Z copy codec-z-0826/scratch/z/0 (HV3 =
#     chain-0826/scratch/bin-flathash+avx512/PHerc0826-seed237/simpaper10, sha 7127e7e6... of its gate; reference tree
#     growth-lto-pgo-1447/scratch/identity/unchanged/PHerc0826-seed237/growth);
#   - rotations HV3 STACK / STACK HV3 / HV3 STACK per phase;
#   - starts only when chain-0826/scratch/next-mlp-z/QUIET-PERF.done exists and no simpaper10, vc_grow_seg_from_seed, perf or
#     compiler (cc1plus, lto1) runs; writes scratch/CLOCK.lock AND growth-lto-pgo-1447/scratch/CLOCK.lock (the item 88
#     memory runner reads the latter), both removed at exit; waits while the latter exists from someone else;
#   - a run counts when rc 0, tree identical by tree_identity.py (exit 0), no other growth seen, others under 1.0;
#   - evidence/clock-runs-<seed>.csv, clock-machine.csv, clock-summary-<seed>.csv (tools/clock_summary_fixes.py),
#     clock-identity-<seed>-<tag>.csv; scratch/clock-<seed>-<tag>; scratch/clock.done.
# Touches no process but its own growths. Never edit this file while it runs.
#   setsid nohup bash tools/clock_fixes.sh F2 > log/clock.txt 2>&1 < /dev/null &
set -u
E=/data/scrollagent/runs/rev1/growth-exact-fixes-88
LP=/data/scrollagent/runs/rev1/growth-lto-pgo-1447
QW=/data/scrollagent/runs/rev1/quiet-window-2026-09-27
H=/data/scrollagent/runs/rev1/patch-filter-harness-1447
GM=/data/scrollagent/runs/rev1/growth-memory-1447
C=/data/scrollagent/runs/rev1/chain-0826
PY=/data/scrollagent/.venv/bin/python
LEDGER=/data/scrollagent/ledger/ledger.csv
QDONE=$C/scratch/next-mlp-z/QUIET-PERF.done
TOOL=growth-exact-fixes-88/tools/clock_fixes.sh
SA=${1:?stack arm}
WAIT_UNTIL=2026-09-28T04:00:00Z
LAST_START=2026-09-28T05:00:00Z
LOCK=$E/scratch/CLOCK.lock; LOCK2=$LP/scratch/CLOCK.lock
MC=$E/evidence/clock-machine.csv
export TMPDIR=/data/tmp
NP=$(nproc)
ROT=("HV3 STACK" "STACK HV3" "HV3 STACK")
PHASES=(PHerc1447-seed1111 PHerc0826-seed237)
declare -A BIN SHA
ENV1447="SIMPAPER_SHARED_CHUNKS=128 SIMPAPER_FORCE_THREADS=1 OMP_WAIT_POLICY=passive OMP_NUM_THREADS=3"
ENV0826="SIMPAPER_SHARED_CHUNKS=512 SIMPAPER_FORCE_THREADS=1 OMP_WAIT_POLICY=passive OMP_NUM_THREADS=3"

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
CT=/data/tmp/clock-fixes-times-$$.txt
childcpu() {
  times > $CT
  awk 'NR==2 { s=0; for (k=1; k<=2; k++) { x=$k; m=x; sub(/m.*/, "", m); sec=x; sub(/.*m/, "", sec); sub(/s/, "", sec); s+=m*60+sec }; printf "%.2f", s }' $CT
}
# stack arm MLP (addition 10:50Z): the binaries, gates, FMA rows and identity row of growth-lto-pgo-1447 (arm MLP)
if [ "$SA" = MLP ]; then SE=$LP; SBIN() { echo "$LP/scratch/bin-MLP/$1/simpaper10"; }; else SE=$E; SBIN() { echo "$E/scratch/bin-$SA/$1/simpaper10"; }; fi
gate_sha() { awk -F, -v r="$SA" -v a="$1" '$3==r && $4==a && $8=="differs_from_HV3_reference" && $11=="yes" {s=$7} END {print s}' $SE/evidence/binary-gate.csv; }

# gates on the stack arm
if [ "$SA" = MLP ]; then IH=$(awk -F, '$1=="flathash+avx512 -march=native -flto=auto PGO (MLP)" {print $NF}' $LP/evidence/identity-0826-summary.csv 2>/dev/null)
else IH=$(awk -F, -v a="$SA" '$2==a {print $NF}' $E/evidence/identity-summary.csv 2>/dev/null); fi
[ "$IH" = yes ] || { say "REFUSED: identity_holds [$IH] for $SA in evidence/identity-summary.csv"; exit 2; }
for A in "${PHASES[@]}"; do
  s=$(gate_sha $A); b=$(SBIN $A)
  [ -n "$s" ] && [ "$(sha256sum $b | cut -d' ' -f1)" = "$s" ] || { say "REFUSED: $b not its gate's sha [$s]"; exit 2; }
  f=$(awk -F, -v r=$SA -v x=$s '$2==r && $5==x && $6=="whole_text" {print $7 "/" $10}' $SE/evidence/fma-check.csv)
  [ "$f" = "0/yes" ] || { say "REFUSED: fma row [$f] for $b"; exit 2; }
done
for f in $H/tools/peak.py $GM/tools/tree_identity.py $QW/tools/busy_procs.py $E/tools/clock_summary_fixes.py; do [ -e "$f" ] || { say "REFUSED: $f absent"; exit 3; }; done
[ -e "$LOCK" ] && { say "REFUSED: $LOCK exists: $(cat $LOCK)"; exit 2; }
say "armed (pid $$), stack arm $SA; waiting for $QDONE"
WU=$(epoch $WAIT_UNTIL)
until [ -e "$QDONE" ]; do [ "$(date +%s)" -ge "$WU" ] && { say "STOP: no QUIET-PERF.done by $WAIT_UNTIL"; exit 4; }; sleep 60; done
n=0
while :; do   # no lock while waiting (coordinator's rule of 10:29Z): first no foreign growth, perf or compiler
  x=$(foreign); [ -z "$x" ] && [ ! -e "$LOCK2" ] && break
  [ "$(date +%s)" -ge "$WU" ] && { say "STOP: foreign process or $LOCK2 still at $WAIT_UNTIL: $x"; ledger growth-exact-fixes-88-clock-not-run "clock not run: foreign process or lock at $WAIT_UNTIL: $x" "runs/rev1/growth-exact-fixes-88/log/clock.txt"; exit 4; }
  [ $((n % 5)) = 0 ] && say "waiting (no lock held) for foreign processes [$x] or $LOCK2 [$(cat $LOCK2 2>/dev/null)]"; n=$((n+1)); sleep 60
done
trap 'rm -f "$LOCK" $CT $CT.c0 $CT.c1; grep -q "pid $$ " "$LOCK2" 2>/dev/null && rm -f "$LOCK2"' EXIT
echo "$(date -u +%FT%TZ) pid $$ $TOOL" > "$LOCK"; echo "$(date -u +%FT%TZ) pid $$ $TOOL" > "$LOCK2"
say "locks written: $(cat $LOCK); waiting for quiet (processes that pause under the lock do so now)"
[ -e $MC ] || echo "tool,utc,tag,cores_busy_60s,loadavg_1min,mem_available_kb,growths_of_others" > $MC
while :; do
  s0=$(stat_ticks); sleep 60; s1=$(stat_ticks); QB=$(busy_between "$s0" "$s1"); QG=$(foreign)
  csvrow $MC $TOOL "$(date -u +%FT%TZ)" quiet-test "$QB" "$(cut -d' ' -f1 /proc/loadavg)" "$(awk '/MemAvailable/{print $2}' /proc/meminfo)" "${QG:-none}"
  if [ -z "$QG" ] && awk -v b="$QB" 'BEGIN{exit !(b+0 < 2.0)}'; then say "quiet: cores busy $QB over 60 s, no growth"; break; fi
  say "not quiet: cores busy $QB over 60 s; foreign [${QG:-none}]; over 1 per cent [$($PY $QW/tools/busy_procs.py 5 1 | cut -c1-300)]"
  [ "$(date +%s)" -ge "$WU" ] && { say "STOP: not quiet by $WAIT_UNTIL"; ledger growth-exact-fixes-88-clock-not-run "clock not run: not quiet by $WAIT_UNTIL (cores busy $QB)" "runs/rev1/growth-exact-fixes-88/evidence/clock-machine.csv"; exit 4; }
done

LE=$(epoch $LAST_START)
SUMS=""
for A in "${PHASES[@]}"; do
  R=$E/evidence/clock-runs-$A.csv; SU=$E/evidence/clock-summary-$A.csv
  [ -e $R ] && { say "REFUSED: $R exists"; exit 2; }
  case $A in
    PHerc1447-*) ZARR=/data/scrollagent/data/datasets/PHerc1447/0; MANIFEST=/data/scrollagent/data/datasets/PHerc1447/chunks.txt
      DG=/data/scrollagent/runs/rev1/seeds-at-scale-1447/out/$A/growth; ENV=$ENV1447
      BIN[HV3]=/data/scrollagent/runs/rev1/growth-avx512-1447/scratch/bin/avx512/simpaper10; SHA[HV3]=0c03fd194644d488a4ab8aba8af6cb5770aaaf1bec885e59451210b6dee98226 ;;
    *) ZARR=/data/scrollagent/runs/rev1/codec-z-0826/scratch/z/0; MANIFEST=/data/scrollagent/data/datasets/PHerc0826/chunks.txt
      DG=$LP/scratch/identity/unchanged/$A/growth; ENV=$ENV0826
      BIN[HV3]=$C/scratch/bin-flathash+avx512/$A/simpaper10; SHA[HV3]=7127e7e6289ec5bde3af397b5d551a0ef029bf98b8ba132f4b632fd03b3197e8 ;;
  esac
  BIN[STACK]=$(SBIN $A); SHA[STACK]=$(gate_sha $A)
  [ "$(sha256sum "${BIN[HV3]}" | cut -d' ' -f1)" = "${SHA[HV3]}" ] || { say "STOP: HV3 binary ${BIN[HV3]} not sha ${SHA[HV3]:0:12}"; exit 3; }
  [ -d "$DG/patches" ] && [ -f "$DG/rel.csv" ] && [ -d "$ZARR" ] || { say "STOP: reference $DG or zarr $ZARR absent"; exit 3; }
  echo "tool,seed,tag,arm,rotation,order,started_utc,ended_utc,return_code,wall_clock_seconds,peak_rss_kb,cores_busy_over_run,run_cpu_seconds,cores_busy_others_over_run,cores_busy_60s_samples,other_growths_start,other_growths_end,other_growths_in_samples,busy_procs_start,busy_procs_end,growth_identity,patch_files,tree_bytes_removed,binary,binary_sha256,zarr,env,counted,why_not_counted" > $R
  ORDER=0; STOPWHY="three rotations done"
  for r in 0 1 2; do
    for arm in ${ROT[$r]}; do
      if [ "$(date +%s)" -ge "$LE" ]; then STOPWHY="no start after $LAST_START"; break 2; fi
      w=0
      until [ "$(memgb)" -ge 30 ] && [ "$(diskgb)" -ge 20 ]; do
        [ "$(date +%s)" -ge "$LE" ] && { STOPWHY="memory or disk gate unmet until $LAST_START"; break 3; }
        [ $((w % 5)) = 0 ] && say "hold: MemAvailable $(memgb) GB (30), /data free $(diskgb) GB (20)"; w=$((w+1)); sleep 60
      done
      [ "$(sha256sum "${BIN[$arm]}" | cut -d' ' -f1)" = "${SHA[$arm]}" ] || { STOPWHY="binary $arm changed"; break 2; }
      ORDER=$((ORDER+1)); tg=$arm-r$((r+1))
      W=$E/scratch/clock-$A-$tg; G=$W/growth; rm -rf $W; mkdir -p $G/surface.bp/surface $G/boundary.bp/surface $G/patches
      OGS=$(growths 0); BPS=$($PY $QW/tools/busy_procs.py 5 1)
      childcpu > $CT.c0; c0=$(cat $CT.c0); s0=$(stat_ticks); e0=$(date +%s.%N); ST=$(date -u +%FT%TZ)
      ( cd $W
        for kv in $ENV; do export "$kv"; done
        SIMPAPER_OUTPUT_DIR=$G SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$G/missing.txt ZARR_CHUNK_MANIFEST=$MANIFEST \
        exec nice -n 10 $PY $H/tools/peak.py $W/peak-growth.txt ${BIN[$arm]} g 36000 ) > $W/growth.log 2>&1 &
      P=$!
      say "started $A $tg (rotation $((r+1)), order $ORDER), peak.py pid $P"
      SAMP=""; OGI=""; sp=$(stat_ticks); nx=$(( $(date +%s) + 60 ))
      while :; do
        st=""; read -r _ _ st _ 2>/dev/null < /proc/$P/stat
        [ -z "$st" ] || [ "$st" = Z ] && break
        sleep 5
        if [ "$(date +%s)" -ge "$nx" ]; then
          sn=$(stat_ticks); b=$(busy_between "$sp" "$sn"); sp=$sn; nx=$(( $(date +%s) + 60 ))
          og=$(growths $P); [ -n "$og" ] && OGI="${OGI:+$OGI | }$(date -u +%H:%M:%S) $og"
          SAMP="${SAMP:+$SAMP }$b"
          csvrow $MC $TOOL "$(date -u +%FT%TZ)" $A-$tg "$b" "$(cut -d' ' -f1 /proc/loadavg)" "$(awk '/MemAvailable/{print $2}' /proc/meminfo)" "${og:-none}"
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
      gid=$($PY $GM/tools/tree_identity.py $DG $G $E/evidence/clock-identity-$A-$tg.csv growth); grc=$?
      bytes=$(du -sB1 $G | cut -f1); rm -rf $G; gzip -f $W/growth.log
      why=""
      [ "$prc" = 0 ] || why="${why:+$why; }rc $prc"
      [ "$grc" = 0 ] || why="${why:+$why; }tree $gid"
      [ -z "$OGS" ] || why="${why:+$why; }other growth at start"
      [ -z "$OGE" ] || why="${why:+$why; }other growth at end"
      [ -z "$OGI" ] || why="${why:+$why; }other growth in a sample"
      awk -v c="$CO" 'BEGIN{exit !(c+0==c && c+0 < 1.0)}' || why="${why:+$why; }others $CO not under 1.0"
      cnt=yes; [ -n "$why" ] && cnt=no
      csvrow $R $TOOL $A $tg $arm $((r+1)) $ORDER $ST $EN "$prc" "$psec" "$pkb" "$CB" "$RCPU" "$CO" "${SAMP:-none}" "${OGS:-none}" "${OGE:-none}" "${OGI:-none}" "$BPS" "$BPE" "$gid" "$np" "$bytes" "${BIN[$arm]#/data/scrollagent/runs/rev1/}" "${SHA[$arm]}" "${ZARR#/data/scrollagent/}" "$ENV" $cnt "${why:-}"
      say "$A $tg rc $prc, $psec s, $pkb kB, cores busy $CB (run cpu $RCPU s, others $CO), $gid, counted $cnt ${why:+($why)}"
    done
  done
  say "$A runs ended: $STOPWHY; $ORDER runs"
  LINE=$($PY $E/tools/clock_summary_fixes.py $R $SU)
  say "$A summary: $LINE"; SUMS="${SUMS:+$SUMS || }$A: $LINE"
  ledger growth-exact-fixes-88-clock-$A "quiet clock on $A, HV3 against STACK ($SA), one growth at a time, $ORDER runs ($STOPWHY); zarr ${ZARR#/data/scrollagent/}; rule declared in DECLARATION.md (median below HV3's minimum, CPU and wall): $LINE" "runs/rev1/growth-exact-fixes-88/evidence/clock-summary-$A.csv; runs/rev1/growth-exact-fixes-88/evidence/clock-runs-$A.csv; runs/rev1/growth-exact-fixes-88/evidence/clock-machine.csv"
done
rm -f "$LOCK"; grep -q "pid $$ " "$LOCK2" 2>/dev/null && rm -f "$LOCK2"; say "locks removed"
touch $E/scratch/clock.done
say "done: $SUMS"
