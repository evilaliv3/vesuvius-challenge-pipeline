#!/bin/bash
# identity_runtime.sh: runtime-params-96's bar (DECLARATION.md, «Bar»). A copy of growth-lto-pgo-1447/tools/identity_arms.sh
# with these changes only:
#   - arms: perseed (growth-lto-pgo-1447/scratch/bin-MLP/<seed>/simpaper10, sha equal to its binary-gate.csv row
#     differs_from_HV3_reference: the per seed MLP binary the chain builds, chain-0826/scratch/next-mlp-z/tests/build-tests.csv)
#     and runtime (scratch/bin-runtime/simpaper10, sha equal to evidence/build-gate.csv's fma_count_zero row), the
#     runtime arm given SIMPAPER_SEED_X/Y/Z from chain-0826's draw row;
#   - the growth reads chain-0826/tools/run_seed.sh's GROWTH_ZARR (hot-lines-88 lz4hc copy), the stages the original, as
#     the chain runs now;
#   - no time cap; at most MAXJOBS 2 jobs at once (OMP 3 each: 6 cores), nice 10; a start is held while any
#     runs/rev1/*/scratch/CLOCK.lock exists, MemAvailable minus 6 GB is under 20 GB, or /data has under 52 GB free;
#     running jobs are stopped (SIGSTOP to their own process group) while a CLOCK.lock exists and continued after;
#   - at the end tools/identity_compare_runtime.py writes the rows, the summary and the ledger row.
# Environment: chain-0826's settings file by chain-0826/tools/deliver_settings.sh ds_apply (read only), as G6.
#   usage: setsid nohup bash tools/identity_runtime.sh > log/identity-runner.txt 2>&1 < /dev/null &
set -u
P=/data/scrollagent/runs/rev1/runtime-params-96
M=/data/scrollagent/runs/rev1/growth-lto-pgo-1447
C=/data/scrollagent/runs/rev1/chain-0826
PY=/data/scrollagent/.venv/bin/python
ZARR=/data/scrollagent/data/datasets/PHerc0826/0
GROWTH_ZARR=/data/scrollagent/runs/rev1/hot-lines-88/scratch/l/0
MANIFEST=/data/scrollagent/data/datasets/PHerc0826/chunks.txt
DRAW=$C/evidence/seeds-PHerc0826-draw400.csv
PEAK_GB=6; FLOOR_GB=20; DISK_MIN=52; MAXJOBS=2
export TMPDIR=/data/tmp
SEEDS=(PHerc0826-seed300 PHerc0826-seed237 PHerc0826-seed109)
ARMS=(perseed runtime)
say() { echo "$(date -u +%FT%TZ) [identity-runtime] $*"; }
source "$C/tools/deliver_settings.sh" || { say "REFUSED: deliver_settings.sh"; exit 3; }
ds_apply "$C/scratch/deliver-settings.env" || { say "REFUSED: settings: $DS_ERR"; exit 3; }
[ -f "$GROWTH_ZARR/.zarray" ] || { say "REFUSED: $GROWTH_ZARR has no .zarray"; exit 3; }
say "settings $DS_LINE; seeds ${SEEDS[*]}"

want_sha() {  # arm seed
  if [ "$1" = perseed ]; then
    awk -F, -v a="$2" '$3=="MLP" && $4==a && $8=="differs_from_HV3_reference" && $11=="yes" {s=$7} END {print s}' $M/evidence/binary-gate.csv
  else
    awk -F, '$3=="runtime" && $7=="fma_count_zero" && $10=="yes" {s=$6} END {print s}' $P/evidence/build-gate.csv
  fi
}
src_of() { if [ "$1" = perseed ]; then echo "$M/scratch/bin-MLP/$2/simpaper10"; else echo "$P/scratch/bin-runtime/simpaper10"; fi; }
seedxyz() {  # seed: "x y z" from the draw row
  $PY - "$DRAW" "$1" <<'PYEOF'
import csv, sys
rows = [r for r in csv.DictReader(l for l in open(sys.argv[1]) if not l.startswith('"#')) if r["attempt"] == sys.argv[2]]
assert len(rows) == 1, rows
print(rows[0]["seed_x"], rows[0]["seed_y"], rows[0]["seed_z"])
PYEOF
}
for a in "${SEEDS[@]}"; do for arm in "${ARMS[@]}"; do
  w=$(want_sha "$arm" "$a"); s=$(src_of "$arm" "$a")
  [ -n "$w" ] && [ -x "$s" ] && [ "$(sha256sum "$s" | cut -d' ' -f1)" = "$w" ] || { say "REFUSED: $arm $a: $s absent or not its gate's sha [$w]"; exit 4; }
  say "binary $arm $a sha ${w:0:12} equals its gate"
done; done

job() {  # arm seed k: runs in its own process group (setsid)
  local arm=$1 a=$2 k=$3 b O G t0 rc st L x y z
  b=$P/scratch/identity/run-bin/$arm-j$k/simpaper10; mkdir -p "$(dirname "$b")"; cp "$(src_of "$arm" "$a")" "$b"
  O=$P/scratch/identity/$arm/$a; G=$O/growth; L=$P/log/identity-$arm-$a.txt
  [ "$(sha256sum "$b" | cut -d' ' -f1)" = "$(want_sha "$arm" "$a")" ] || { mkdir -p "$O"; echo "run copy sha differs" > "$O/RESULT"; return 0; }
  rm -rf "$O"; mkdir -p "$G/surface.bp/surface" "$G/boundary.bp/surface" "$G/patches"
  cd "$O" || return 9
  unset SIMPAPER_SEED_X SIMPAPER_SEED_Y SIMPAPER_SEED_Z
  if [ "$arm" = runtime ]; then read -r x y z < <(seedxyz "$a"); export SIMPAPER_SEED_X=$x SIMPAPER_SEED_Y=$y SIMPAPER_SEED_Z=$z; fi
  t0=$(date +%s)
  echo "$(date -u +%FT%TZ) growth starts, binary sha $(sha256sum "$b" | cut -c1-12), $(env | grep -E '^(SIMPAPER_SHARED_CHUNKS|SIMPAPER_FORCE_THREADS|OMP_WAIT_POLICY|OMP_NUM_THREADS|SIMPAPER_SEED_[XYZ])=' | tr '\n' ' ')" > "$L"
  SIMPAPER_OUTPUT_DIR=$G SIMPAPER_SURFACE_ZARR=$GROWTH_ZARR ZARR_MISSING_LIST=$G/missing.txt ZARR_CHUNK_MANIFEST=$MANIFEST \
    nice -n 10 "$b" g 36000 >> "$L" 2>&1; rc=$?
  echo "$(date -u +%FT%TZ) growth rc $rc in $(( $(date +%s)-t0 )) s, patches $(ls "$G/patches" | wc -l)" >> "$L"
  [ $rc -eq 0 ] || { echo "growth $rc" > "$O/RESULT"; return 0; }
  rm -rf "$O/C40"; cp -a "$G" "$O/C40" || { echo "copy failed" > "$O/RESULT"; return 0; }
  for st in "c" "l" "vm 10" "hm 10" "fm 30 10"; do
    SIMPAPER_OUTPUT_DIR=$O/C40 SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$O/C40/missing-C40.txt SIMPAPER_PATCH_LIMIT=40000 \
      nice -n 10 "$b" $st >> "$L" 2>&1; rc=$?
    echo "$(date -u +%FT%TZ) stage '$st' rc $rc" >> "$L"
    [ $rc -eq 0 ] || { echo "stage $st $rc" > "$O/RESULT"; return 0; }
  done
  echo "0 sheets $(ls "$O"/C40/patch_*.bin 2>/dev/null | wc -l) wall $(( $(date +%s)-t0 ))" > "$O/RESULT"
}
if [ "${1:-}" = __job ]; then shift; job "$@"; exit $?; fi

declare -A RUN=()   # pgid -> "arm seed"
stopped=0
clock_gate() {  # stop or continue the running groups by CLOCK.lock
  if ls /data/scrollagent/runs/rev1/*/scratch/CLOCK.lock >/dev/null 2>&1; then
    if [ $stopped -eq 0 ] && [ ${#RUN[@]} -gt 0 ]; then for g in "${!RUN[@]}"; do kill -STOP -- -"$g" 2>/dev/null; done; stopped=1; say "CLOCK.lock present: stopped groups ${!RUN[*]}"; fi
    return 1
  fi
  if [ $stopped -eq 1 ]; then for g in "${!RUN[@]}"; do kill -CONT -- -"$g" 2>/dev/null; done; stopped=0; say "CLOCK.lock gone: continued groups ${!RUN[*]}"; fi
  return 0
}
alive() { [ -r /proc/$1/status ] && ! grep -q "^State:[[:space:]]*Z" /proc/$1/status; }
reap() { for g in "${!RUN[@]}"; do alive "$g" || { wait "$g" 2>/dev/null; say "ended ${RUN[$g]} (pgid $g): $(cat $P/scratch/identity/${RUN[$g]% *}/${RUN[$g]#* }/RESULT 2>/dev/null || echo 'no RESULT')"; unset "RUN[$g]"; }; done; }
mkdir -p "$P/scratch/identity" "$P/log"
k=0
for a in "${SEEDS[@]}"; do for arm in "${ARMS[@]}"; do
  k=$((k+1))
  if grep -q '^0 ' "$P/scratch/identity/$arm/$a/RESULT" 2>/dev/null; then say "skip $arm $a: done"; continue; fi
  while true; do
    reap
    if clock_gate && [ ${#RUN[@]} -lt $MAXJOBS ]; then
      m=$(awk '/^MemAvailable/{print int($2/1048576)}' /proc/meminfo); dk=$(df -B1G --output=avail /data | tail -1 | tr -d ' ')
      [ $(( m - PEAK_GB )) -ge "$FLOOR_GB" ] && [ "$dk" -ge "$DISK_MIN" ] && break
      say "holding $arm $a: MemAvailable $m GB, /data free $dk GB (min $DISK_MIN)"
    fi
    sleep 30
  done
  setsid bash "$0" __job "$arm" "$a" "$k" < /dev/null &
  g=$!; RUN[$g]="$arm $a"
  say "started $arm $a (pid and pgid $g), MemAvailable $m GB, /data free $dk GB, loadavg $(cut -d' ' -f1-3 /proc/loadavg)"
  sleep 20
done; done
while [ ${#RUN[@]} -gt 0 ]; do reap; clock_gate; sleep 30; done
say "all jobs ended"
for a in "${SEEDS[@]}"; do for arm in "${ARMS[@]}"; do say "$arm $a: $(cat "$P/scratch/identity/$arm/$a/RESULT" 2>/dev/null || echo absent)"; done; done
$PY $P/tools/identity_compare_runtime.py; say "identity_compare_runtime.py rc $?"
