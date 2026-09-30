#!/bin/bash
# ladder_par.sh <group> <draw csv>: tools/ladder.sh COPIED (never edited) in a NEW FILE, written 2026-09-26T22:2xZ by a
# coordinator agent on the director's order of 22:17:19Z (chain-0826 DECLARATION.md addition of 2026-09-26T22:19:18Z).
# ladder.sh starts one seed about every 18 s (a build, a 10 s cores sample, a 5 s sleep, in one loop), so most seeds, which
# end in 0 s, run one at a time. Changes against ladder.sh, and no others:
#   L1. PAR_W (default 8) worker processes replace the one start loop; each runs a seed to its end before the next;
#   L2. a seed is claimed under the lock $PLOCK (scratch/ladder-par.lock): not in the output CSV and not in the run's claim
#       file $RUND/claims; so no seed is classified twice by this script. It must not run on a group ladder.sh is running;
#   L3. the start gates are ladder.sh's (stop file, settings, quiet gate 300 s for a build and 120 s for a growth, disk every
#       10 min, the memory guard, /data FREE_MIN_GB, cores busy under 22 over 10 s), with the memory, free, quiet and cores
#       tests taken one worker at a time under $PLOCK.gate, the cores test counting 3 cores for each start of this run in
#       the last 12 s, and the lock held 2 s after a start so the next worker's memory guard sees the new process;
#   L4. LP_OUT, LP_Q, LP_DONEF, LP_LOGD, LP_GROWD, LP_BIN, LP_GATES, LP_RUND, LP_LOCK, LP_QLOCK, LP_ATTEMPTS move every
#       file for the bar test to a scratch directory (defaults: ladder.sh's files); rows to the output CSV under $PLOCK.out.
# The per seed command, the 120 s cap, the exported environment, the build (tools/build_variant_seed.py unchanged, one
# object), the classification and the row form are ladder.sh's.
# --- tools/ladder.sh follows (its header, then its text as changed above) ---
# 2026-09-26T18:1xZ coordinator (director 18:05:59Z): init_why sets MEM_WHY and FREE_WHY empty before the loop; the owner's relaunch at 17:52Z stopped at
#   17:55:02Z on «FREE_WHY unbound variable» (line 260, set -u) when the cores test failed first; check only now runs the holding branch. No other change.
# chain-0826 copy of seeds-at-scale-1447/tools/ladder.sh, written 2026-09-26 by a coordinator agent (DECLARATION.md part 2):
# paths and names moved to chain-0826 and PHerc0826 (study root, prediction, raw volume, draw and queue file names, ledger
# slugs chain-0826-deliver-*); every other change is listed below this line; the text after the list is the original's.
#   A. the ladder grows each seed with the per seed build of the variant `unchanged` (tools/build_variant_seed.py, build.sh
#      delivered) into scratch/bin-ladder/, not the corrected series: the delivered series differs from corrected only in the c
#      stage (work S), which a 120 s growth never runs; the classification stays on the unchanged build whatever BUILD says.
# ladder.sh <group> <draw csv>: ladder_v10.sh COPIED (never edited), in a NEW FILE, written 2026-09-26T04:3xZ by a
# coordinator agent on the director's order of about 04:15Z (DECLARATION.md addition of 2026-09-26T04:18Z): the ladder of
# the one runner's lineage (tools/deliver.sh starts tools/refill.sh, which starts this). Changes against ladder_v10.sh, and
# no others:
#   1. the stop file is scratch/deliver.stop (v10 read deliver20.stop), checked before every ladder start as in v10;
#   2. the settings are scratch/deliver-settings.env through tools/deliver_settings.sh, at launch (refused: exit 3) and
#      again before every ladder run (refused: that start is held, logged, read again in 60 s): the four variables
#      SIMPAPER_SHARED_CHUNKS, SIMPAPER_FORCE_THREADS, OMP_WAIT_POLICY, OMP_NUM_THREADS exported to every ladder growth
#      (v10 exported the first three; OMP_NUM_THREADS=3 is new here, declared), CAP_CHUNKS, FLOOR_GB and FREE_MIN_GB, and
#      the quiet window (v10 sourced tools/quiet_gate.sh with the dates of 2026-09-25/26);
#   3. cores from `nproc --all` (getconf if absent) in the cores busy formula; plain nproc obeys OMP_NUM_THREADS.
# The classification, the binary series and its gates, the 120 s cap, PAR 20, cores busy under 22, the memory guard, the
# row form, the files (evidence/ladder.csv, evidence/queue.txt, evidence/ladder-<group>.done) are v10's.
# SA_CHECK_ONLY=1 [SA_CLOCK=<epoch>] [SA_STOPF=<file>]: the plan and every gate; runs nothing, writes nothing.
#
# --- ladder_v10.sh's header follows ---
# ladder_v10.sh <group> <draw csv>: ladder_extension2.sh's 120 s classification, in a NEW FILE, written 2026-09-25T19:1xZ
# by a coordinator agent on the director's note of 2026-09-25 about 19:1xZ (DECLARATION.md addition of 2026-09-25T19:13:31Z).
# Changes against ladder_extension2.sh, and no others:
#   1. the seeds are the rows of evidence/seed-rule.csv of <group> with passes_rule yes, in draw order; the draw file
#      (for the corrected binary's build) is <draw csv>; both are arguments;
#   2. rows go to evidence/ladder.csv (one file for every v10 group); survivors to evidence/queue.txt (flock
#      scratch/queue.lock), which deliver_guarded20.sh reads and orders by share, lowest first; the queue never
#      closes (the refill appends); when every seed of the group is classified, evidence/ladder-<group>.done holds
#      the counts;
#   3. SIMPAPER_SHARED_CHUNKS=128, SIMPAPER_FORCE_THREADS=1, OMP_WAIT_POLICY=passive are EXPORTED to every ladder growth,
#      after v19's two checks (cap 128 «identical 10 of 10»; arm F trees identical and downstream bytes);
#   4. the start gates: at most PAR 20 at once; cores busy under 22 over 10 s (machine.sh's /proc/stat formula); the
#      house memory guard (MemAvailable minus the unrealised declared peaks of the running growths and sweep tracers
#      minus the new run's PEAK36_GB at or above 20 GB, v19's functions copied; PEAK36_GB read as v19 reads it); /data at
#      least 70 GB free by df before each start; machine.sh's budget line and the 98 per cent brake, read every 10 minutes;
#   5. the quiet gate: tools/quiet_gate.sh (a byte copy of stevens-remedy-half-on's, sha256 checked), need 120 s: no
#      ladder run starts from 23:28:00Z (so none runs at 23:30:00Z) to 2026-09-26T03:15:00Z.
# The classification (rc 124 at the cap = survivor; no patch written; ended by itself), the binary series and its
# gates, the 120 s cap and the row form are ladder_extension2.sh's.
# SA_CHECK_ONLY=1 [SA_CLOCK=<epoch>]: prints the plan and every gate on the real state and on simulated clocks and
# memory; runs nothing, writes nothing.
set -u
S=/data/scrollagent/runs/rev1/chain-0826
GROUP=${1:?group}
DRAW=${2:?draw csv}
ZARR=/data/scrollagent/data/datasets/PHerc0826/0
CAP=120
PAR_W=${PAR_W:-8}   # L1: worker processes
CORES_MAX=22
FLOOR_GB=""; FREE_MIN_GB=""; PEAK36_UNCAPPED_GB=24; PEAK_TRACER_GB=10; CAP_MARGIN_GB=4; PEAK72_CAPPED_GB=8   # FLOOR_GB, FREE_MIN_GB: settings file
CAP_CHUNKS=""   # the settings file
PY=/data/scrollagent/.venv/bin/python
RULE=$S/evidence/seed-rule.csv
Q=${LP_Q:-$S/evidence/queue.txt}
OUT=${LP_OUT:-$S/evidence/ladder.csv}   # L4: test overrides
DONEF=${LP_DONEF:-$S/evidence/ladder-$GROUP.done}
LOGD=${LP_LOGD:-$S/log}; GROWD=${LP_GROWD:-$S/scratch/ladder}; BIND=${LP_BIN:-$S/scratch/bin-ladder}; GATED=${LP_GATES:-$S/evidence/gates}
RUND=${LP_RUND:-$S/scratch/ladder-par/$GROUP}; PLOCK=${LP_LOCK:-$S/scratch/ladder-par.lock}; QLOCK=${LP_QLOCK:-$S/scratch/queue.lock}
BUILD_LOCK=$S/scratch/build.lock   # chain-0826 A: this study's build tree (tools/build_variant_seed.py)
MACHINE=/data/scrollagent/tools/machine.sh
LARGER_RUNS=/data/scrollagent/runs/rev1/larger-sheets-1447/evidence/runs
TOOL=tools/ladder_par.sh
STOPF=$S/scratch/deliver.stop
[ "${SA_CHECK_ONLY:-0}" = 1 ] && [ -n "${SA_STOPF:-}" ] && STOPF=$SA_STOPF   # check only: a test copy
SETTINGS=$S/scratch/deliver-settings.env
say() { echo "$(date -u +%FT%TZ) [ladder_par $GROUP${WID:+ w$WID}] $*"; }

if [ "${SA_CHECK_ONLY:-0}" != 1 ]; then for v in SA_CLOCK SA_STOPF SA_LEDGER_SIM SA_SUMMARY_CAP_FILE SA_MEM_SIM_KB SA_FREE_SIM SA_CORES_S; do [ -n "${!v:-}" ] && { say "REFUSED: $v is a check only override"; exit 3; }; done; fi
source "$S/tools/deliver_settings.sh" || { say "REFUSED: tools/deliver_settings.sh not sourced"; exit 3; }
ds_apply "$SETTINGS" || { say "REFUSED: settings: $DS_ERR"; exit 3; }
say "settings read at launch: $DS_LINE"
SET_ERR=""
[ -s "$DRAW" ] || { say "REFUSED: draw file $DRAW absent"; exit 3; }

# ---- change 3: the four variables were exported by ds_apply after the checks of deliver_settings.sh (cap, arm F, arm F3)

# ---- change 4: the memory guard, v19's functions copied
r=$($PY "$S/tools/capped_peak_v18.py" "$CAP_CHUNKS") || { say "REFUSED: no measured capped peak for cap $CAP_CHUNKS"; exit 3; }
set -- $r
PEAK36_GB=$(( ($1 + 1048575) / 1048576 + CAP_MARGIN_GB ))
PEAK_WHY="capped_peak_v18.py $CAP_CHUNKS: $1 kB ($2) -> ceil + $CAP_MARGIN_GB"
PEAKLOG=$S/evidence/peak36-under-cap.csv
if [ -s "$PEAKLOG" ]; then
  last=$($PY - "$PEAKLOG" <<'PY'
import csv, sys
R = list(csv.DictReader(open(sys.argv[1], newline="")))
print(R[-1]["peak36_gb_after"] if R else "")
PY
)
  [[ "$last" =~ ^[0-9]+$ ]] || { say "REFUSED: $PEAKLOG last peak36_gb_after [$last]"; exit 3; }
  [ "$last" -gt "$PEAK36_GB" ] && { PEAK36_GB=$last; PEAK_WHY="$PEAK_WHY; raised by the peak rule of v19/v20 ($PEAKLOG)"; }
fi
PEAK72_GB=$($PY - "$LARGER_RUNS" <<'PY'
import csv, glob, math, os, sys
v = []
for p in glob.glob(os.path.join(sys.argv[1], "*.csv")):
    if ".before-" in p:
        continue
    for r in csv.reader(open(p, newline="")):
        if len(r) >= 4 and r[2] == "growth_peak_rss_gb":
            try: v.append(float(r[3]))
            except ValueError: pass
print(math.ceil(max(v)) if v else "")
PY
)
[[ "$PEAK72_GB" =~ ^[0-9]+$ ]] || { say "REFUSED: g 72000 peak not read: [$PEAK72_GB]"; exit 3; }
capped() { tr '\0' '\n' < /proc/$1/environ 2>/dev/null | grep -qx "SIMPAPER_SHARED_CHUNKS=$CAP_CHUNKS"; }
unrealised() {
  local pid peak rss n=0 u=0
  while read -r pid peak; do
    [[ "$pid" =~ ^[0-9]+$ && "$peak" =~ ^-?[0-9]+$ ]] || continue
    rss=$(awk '/^VmRSS/{print $2}' /proc/$pid/status 2>/dev/null)
    [[ "$rss" =~ ^[0-9]+$ ]] || continue
    [ "$peak" = 0 ] && { capped "$pid" && peak=$((PEAK36_GB*1048576)) || peak=$((PEAK36_UNCAPPED_GB*1048576)); }
    [ "$peak" = -72 ] && { capped "$pid" && peak=$((PEAK72_CAPPED_GB*1048576)) || peak=$((PEAK72_GB*1048576)); }
    n=$((n+1)); [ "$rss" -lt "$peak" ] && u=$((u + peak - rss))
  done < <(ps -eo pid=,comm=,args= | awk -v pt=$((PEAK_TRACER_GB*1048576)) '
      $2=="simpaper10" && $4=="g" && $5=="36000" {print $1, 0; next}
      $2=="simpaper10" && $4=="g" && $5=="72000" {print $1, -72; next}
      $3 ~ /\/vc_grow_seg_from_seed$/ {print $1, pt}')
  echo "$n $u"
}
mem_ok() {
  local akb nu n u left
  akb=${SA_MEM_SIM_KB:-$(awk '/^MemAvailable/{print $2}' /proc/meminfo)}
  nu=$(unrealised); n=${nu% *}; u=${nu#* }
  [[ "$akb" =~ ^[0-9]+$ && "$n" =~ ^[0-9]+$ && "$u" =~ ^[0-9]+$ ]] || { MEM_WHY="memory not measurable: avail [$akb] declared [$n] unrealised [$u]"; return 1; }
  left=$(( (akb - u - PEAK36_GB*1048576) / 1048576 ))
  MEM_WHY="MemAvailable $((akb/1048576)) GB, declared runs $n unrealised $((u/1048576)) GB, new $PEAK36_GB GB: floor left $left of $FLOOR_GB"
  [ "$left" -ge "$FLOOR_GB" ]
}
cores_busy10() {   # machine.sh's formula over 10 s of /proc/stat ticks, times nproc
  local _ u1 n1 s1 i1 r u2 n2 s2 i2 nc
  nc=$(ds_cores)   # nproc --all: plain nproc obeys OMP_NUM_THREADS
  read _ u1 n1 s1 i1 r < /proc/stat; sleep "${SA_CORES_S:-10}"; read _ u2 n2 s2 i2 r < /proc/stat
  awk -v c=$nc -v u=$((u2-u1)) -v n=$((n2-n1)) -v s=$((s2-s1)) -v i=$((i2-i1)) 'BEGIN{t=u+n+s+i; if(t<=0){print "x"} else {printf "%.1f", c*(u+n+s)/t}}'
}
free_ok() {
  local f; f=${SA_FREE_SIM:-$(df -B1G --output=avail /data | tail -1 | tr -d ' ')}
  [[ "$f" =~ ^[0-9]+$ ]] || { FREE_WHY="/data free [$f] not a number"; return 1; }
  FREE_WHY="/data $f GB free against $FREE_MIN_GB"; [ "$f" -ge "$FREE_MIN_GB" ]
}
in_flight() { jobs -rp | wc -l; }
# qg_allows and qw_wait: tools/deliver_settings.sh, the settings file's quiet window
settings_ok() {  # read again before every ladder run; refused = held
  if ds_apply "$SETTINGS"; then [ -n "$SET_ERR" ] && say "  settings accepted again: $DS_LINE"; SET_ERR=""; return 0; fi
  [ "$DS_ERR" != "$SET_ERR" ] && { SET_ERR=$DS_ERR; say "  settings REFUSED, no ladder start, read again in 60 s: $DS_ERR"; }
  return 1
}

mapfile -t SEEDS < <($PY - "$RULE" "$GROUP" <<'PY'
import csv, sys
L = [l for l in open(sys.argv[1], newline="") if not l.lstrip().startswith('"#')]
for r in csv.DictReader(L):
    if r["group"] == sys.argv[2] and r["passes_rule"] == "yes":
        print(r["attempt"], r["pred_chunk_share_255"])
PY
)
if [ -n "${LP_ATTEMPTS:-}" ]; then   # L4: the bar's subset, in the file's order
  mapfile -t SEEDS < <(for row in "${SEEDS[@]}"; do grep -qx "${row%% *}" "$LP_ATTEMPTS" && echo "$row"; done)
fi
[ ${#SEEDS[@]} -gt 0 ] || { say "REFUSED: no passing seed of group $GROUP in $RULE"; exit 3; }

DISK_OK=1; DISK_AT=0
disk_check () {
  local now line n b pct
  now=$(date +%s); [ $((now-DISK_AT)) -lt 600 ] && return
  DISK_AT=$now
  line=$(bash "$MACHINE" 2>/dev/null | head -1)
  n=$(echo "$line" | sed -n 's/.*our disk \([^ ]*\) GB \/ \([^ ]*\).*/\1/p')
  b=$(echo "$line" | sed -n 's/.*our disk \([^ ]*\) GB \/ \([^ ]*\).*/\2/p')
  pct=$(df -P /data | awk 'NR==2 {sub("%","",$5); print $5}')
  if [[ "$n" =~ ^[0-9]+$ && "$b" =~ ^[0-9]+$ && "$pct" =~ ^[0-9]+$ ]] && [ "$n" -lt "$b" ] && [ "$pct" -lt 98 ]; then
    DISK_OK=1; say "  disk: our disk $n GB of $b GB (machine.sh), /data $pct per cent"
  else
    DISK_OK=0; say "  disk: our disk [$n] / [$b], /data [$pct] per cent: holding"
  fi
}

init_why() { MEM_WHY=""; FREE_WHY=""; }   # 2026-09-26 fix (director 18:05:59Z): under set -u the holding line read them unset when the cores test failed before mem_ok and free_ok ran

if [ "${SA_CHECK_ONLY:-0}" = 1 ]; then
  say "CHECK ONLY: ${#SEEDS[@]} passing seeds of $GROUP; first ${SEEDS[0]}, last ${SEEDS[-1]}; draw $DRAW"
  say "CHECK ONLY: $DS_LINE"
  say "CHECK ONLY: environment exported: $(env | grep -E '^(SIMPAPER_SHARED_CHUNKS|SIMPAPER_FORCE_THREADS|OMP_WAIT_POLICY|OMP_NUM_THREADS)=' | tr '\n' ' ')"
  say "CHECK ONLY: stop file $STOPF $([ -e "$STOPF" ] && echo 'present: no ladder run would start' || echo absent)"
  say "CHECK ONLY: PEAK36_GB $PEAK36_GB ($PEAK_WHY), g 72000 $PEAK72_GB GB, tracer $PEAK_TRACER_GB GB, floor $FLOOR_GB"
  mem_ok; say "CHECK ONLY: memory guard on the real state: rc $? ($MEM_WHY)"
  for g in 20 27 28 60; do ( SA_MEM_SIM_KB=$((g*1048576)); mem_ok; say "CHECK ONLY: memory guard on simulated MemAvailable $g GB: rc $? ($MEM_WHY)" ); done
  free_ok; say "CHECK ONLY: free gate on the real state: rc $? ($FREE_WHY)"
  for f in 69 70; do ( SA_FREE_SIM=$f; free_ok; say "CHECK ONLY: free gate on simulated $f GB: rc $? ($FREE_WHY)" ); done
  ( unset MEM_WHY FREE_WHY; init_why; b=23.0; fl=0; k=0
    if awk -v b="$b" -v c="$CORES_MAX" 'BEGIN{exit !(b<c)}' && mem_ok && free_ok; then say "CHECK ONLY: simulated cores busy $b: a ladder run would start"
    else k=$((k+1)); [ $((k % 30)) -eq 1 ] && say "CHECK ONLY: simulated cores busy $b against $CORES_MAX, first iteration: holding: in flight $fl of $PAR, cores busy $b, [$MEM_WHY], [$FREE_WHY]"; fi )
  say "CHECK ONLY: PAR_W $PAR_W, cores $(ds_cores) (nproc --all; plain nproc here $(nproc) under OMP_NUM_THREADS=$OMP_NUM_THREADS), cores busy over 10 s now $(cores_busy10) against $CORES_MAX"
  for c in 2026-09-26T22:30:00Z 2026-09-26T23:27:59Z 2026-09-26T23:28:00Z 2026-09-26T23:30:00Z 2026-09-27T00:00:00Z 2026-09-27T03:14:59Z 2026-09-27T03:15:00Z 2026-09-27T12:00:00Z; do
    e=$(date -u -d "$c" +%s)
    ( SA_CLOCK=$e; qg_allows $CAP && m="a ladder run may start" || m="HOLD (quiet gate)"; say "CHECK ONLY: simulated clock $c, need $CAP s: $m | deliver_settings.sh: $(qw_wait ladder $CAP)" )
  done
  a=${SEEDS[0]%% *}
  say "CHECK ONLY: $a binary $([ -x "$S/scratch/bin-ladder/$a/simpaper10" ] && echo present || echo 'to build with tools/build_variant_seed.py unchanged'); build lock $BUILD_LOCK"
  say "CHECK ONLY: queue $Q has $( [ -f "$Q" ] && grep -c . "$Q" || echo 0) lines; nothing run, nothing written"
  exit 0
fi

for d in "$GROWD" "$GATED" "$RUND" "$LOGD" "$BIND"; do mkdir -p "$d"; done
[ -s "$OUT" ] || printf '%s\n' "\"# written by chain-0826/$TOOL: the draws of each batch that pass the seed rule, grown at the ladder cap of 120 s with SIMPAPER_SHARED_CHUNKS=128 SIMPAPER_FORCE_THREADS=1 OMP_WAIT_POLICY=passive; outcome is ladder_hundred.sh's classification; column group names the draw batch; cores_busy_at_start is over 10 s\"" > "$OUT"
grep -q '^tool,' "$OUT" || printf 'tool,utc,attempt,exit_code,killed_at_cap,wall_s,patches,outcome,binary_sha256_head,cores_busy_at_start,memavail_gb_at_start,ladder_in_flight_at_start,pred_chunk_share_255,group\n' >> "$OUT"
touch "$Q" "$RUND/claims"; mkdir -p "$RUND/running"

build () {   # ladder.sh's build with the directories as variables (L4)
  local a=$1 g=$GATED/binary-gate-ladder-$1.csv
  [ -x "$BIND/$a/simpaper10" ] && [ -f "$g" ] && return 0
  ( flock 7; DRAW_CSV=$DRAW $PY "$S/tools/build_variant_seed.py" unchanged "$BIND" "$g" "$a" ) 7> "$BUILD_LOCK" > "$LOGD/build-ladder-$a.txt" 2>&1 || { say "  $a: build failed, see $LOGD/build-ladder-$a.txt"; return 1; }
  [ "$(awk -F, -v a="$a" '$2==a && $6=="differs_from_stock" {print $9}' "$g")" = yes ] || { say "  $a: differs_from_stock not yes"; return 1; }
  [ "$(awk -F, -v a="$a" '$2==a && $6=="carries_acceleration" {print $9}' "$g")" = yes ] || { say "  $a: carries_acceleration not yes"; return 1; }
  return 0
}

one () {   # ladder.sh's one: the same command, cap, environment, classification and row; directories as variables (L4)
  local a=$1 share=$2 busy=$3 mem=$4 fl=$5
  local bin="$BIND/$a/simpaper10"
  local g="$GROWD/$a"
  rm -rf "$g"; mkdir -p "$g/surface.bp/surface" "$g/boundary.bp/surface" "$g/patches"
  local t0=$(date +%s)
  ( cd "$g" && SIMPAPER_OUTPUT_DIR=$g SIMPAPER_SURFACE_ZARR=$ZARR \
      ZARR_MISSING_LIST=$g/missing.txt \
      ZARR_CHUNK_MANIFEST=/data/scrollagent/data/datasets/PHerc0826/chunks.txt \
      timeout --foreground -s TERM $CAP "$bin" g 36000 > "$LOGD/ladder-$a.txt" 2>&1 )
  local rc=$?
  local secs=$(( $(date +%s)-t0 ))
  local n=$(ls "$g/patches" 2>/dev/null | wc -l)
  local killed=no; [ $rc -eq 124 ] && killed=yes
  local outcome="ended by itself"
  [ "$n" -eq 0 ] && outcome="no patch written"
  [ "$killed" = "yes" ] && outcome="still growing at the cap"
  ( flock 5; printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' "$TOOL" "$(date -u +%FT%TZ)" "$a" "$rc" "$killed" "$secs" "$n" "$outcome" \
    "$(sha256sum "$bin" | cut -c1-16)" "$busy" "$mem" "$fl" "$share" "$GROUP" >> "$OUT" ) 5> "$PLOCK.out"
  say "  $a rc=$rc ${secs}s patches $n: $outcome"
  if [ "$killed" = yes ]; then
    ( flock 6; grep -qx "$a" "$Q" || echo "$a" >> "$Q" ) 6> "$QLOCK"
    say "  $a is a survivor (share $share): appended to the v10 queue"
  fi
}

claim () {   # L2: under $PLOCK, the next seed neither in $OUT nor claimed; prints "attempt share" or nothing
  ( flock 4
    for row in "${SEEDS[@]}"; do
      a=${row%% *}
      grep -qx "$a" "$RUND/claims" && continue
      tail -n +3 "$OUT" | awk -F, -v a="$a" '$3==a' | grep -q . && continue
      echo "$a" >> "$RUND/claims"; echo "$row"; break
    done ) 4> "$PLOCK"
}

recent_starts () {   # L3: growth starts of this run in the last 12 s, each counted as 3 busy cores
  local now=$(date +%s) n=0 t
  [ -f "$RUND/starts" ] || { echo 0; return; }
  while read -r t; do [ $((now - t)) -lt 12 ] && n=$((n+1)); done < "$RUND/starts"
  echo $n
}

worker () {
  WID=$1; init_why; local row a share k b m fl rs
  while true; do
    [ -e "$STOPF" ] && { say "$STOPF present: no more starts"; return 0; }
    row=$(claim); [ -n "$row" ] || return 0
    a=${row%% *}; share=${row##* }
    qg_allows 300 || qw_wait "ladder build $a" 300   # a build is a start too: none from 23:25:00Z
    build "$a" || continue
    k=0
    while true; do
      [ -e "$STOPF" ] && break
      settings_ok || { sleep 60; continue; }
      if ! qg_allows $CAP; then qw_wait "ladder $a" $CAP; continue; fi
      disk_check
      [ "$DISK_OK" = 1 ] || { sleep 600; DISK_AT=0; continue; }
      b=$(cores_busy10); m=$(free -g | awk 'NR==2 {print $7}')
      [[ "$m" =~ ^[0-9]+$ && "$b" =~ ^[0-9.]+$ ]] || { say "FATAL: avail [$m] cores [$b] not numbers"; return 2; }
      # L3: the memory guard, free, quiet and the cores test with recent starts, one worker at a time
      exec 3> "$PLOCK.gate"; flock 3
      rs=$(recent_starts); fl=$(ls "$RUND/running" | wc -l)
      if awk -v b="$b" -v r="$rs" -v c="$CORES_MAX" 'BEGIN{exit !(b+3*r<c)}' && mem_ok && free_ok && qg_allows $CAP; then
        date +%s >> "$RUND/starts"; touch "$RUND/running/$a"
        ( one "$a" "$share" "$b" "$m" "$fl"; rm -f "$RUND/running/$a" ) &
        sleep 2; flock -u 3; exec 3>&-
        wait $!
        break
      fi
      flock -u 3; exec 3>&-
      k=$((k+1)); [ $((k % 30)) -eq 1 ] && say "  holding: in flight $fl, recent starts $rs, cores busy $b, $MEM_WHY, $FREE_WHY"
    done
    [ -e "$STOPF" ] && { say "$STOPF present: no more starts"; rm -f "$RUND/running/$a"; return 0; }
  done
}

say "ladder_par starts (pid $$): ${#SEEDS[@]} seeds of $GROUP passing the rule, $PAR_W workers, cap ${CAP} s, cores busy plus 3 per start of the last 12 s under $CORES_MAX over 10 s, memory guard (PEAK36_GB $PEAK36_GB: $PEAK_WHY), /data $FREE_MIN_GB GB free, quiet gate need $CAP s; out $OUT, queue $Q"
init_why
for w in $(seq 1 "$PAR_W"); do worker "$w" & sleep 1; done
wait
got=$(tail -n +3 "$OUT" | awk -F, -v g="$GROUP" '$14==g {print $3}' | sort -u | wc -l)
surv=$(tail -n +3 "$OUT" | awk -F, -v g="$GROUP" '$14==g && $8=="still growing at the cap"' | wc -l)
say "ladder_par of $GROUP done: expected ${#SEEDS[@]} seeds, classified $got, survivors $surv"
if [ "$got" -eq "${#SEEDS[@]}" ]; then
  echo "done $(date -u +%FT%TZ) by $TOOL: group $GROUP, expected ${#SEEDS[@]}, classified $got, survivors $surv" > "$DONEF"
  exit 0
fi
say "NOT marking $GROUP done: classified $got of ${#SEEDS[@]}"
exit 4
