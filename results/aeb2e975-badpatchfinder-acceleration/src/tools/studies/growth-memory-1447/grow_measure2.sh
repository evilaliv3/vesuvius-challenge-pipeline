#!/bin/bash
# grow_measure2.sh <variant> <attempt> [<cap>]
# grow_measure.sh with TWO changes, in a new file because grow_measure.sh is running (written 2026-09-25T13:5xZ):
#   a. an optional third argument <cap>: the growth gets SIMPAPER_SHARED_CHUNKS=<cap> (zarr_1.c zarrStoreDecideCap: the
#      process wide store of decompressed chunks holds at most <cap> chunks of 7.08 MB instead of a quarter of MemAvailable
#      at the start), and the run's tag, its folder and its CSVs are named <variant>-cap<cap>. The binary is unchanged.
#   b. the slot check and the pid file are taken under flock on scratch/slots.lock, so two runners of this file never
#      both see a free slot; the memlog lines are kept for every variant whose name starts with mem.
# --- grow_measure.sh's header follows ---
# grow_measure.sh <variant> <attempt>
# growth-memory-1447 (DECLARATION.md): one growth of <attempt> with this study's binary scratch/bin/<variant>/<attempt>/simpaper10,
# its peak memory, its identity against the delivered growth tree, and the full downstream on its tree against the
# delivered sheets.
#   1. Refuses unless: the binary's sha256 is the one evidence/binary-gate.csv records for <variant> with passes yes;
#      fewer than 2 growths of this study run (scratch/slots/*.pid alive by ps -p); MemAvailable - 32 GB >= 20 GB;
#      /data has >= 70 GB free by df. The start waits (60 s steps) on memory, slots and disk, it never forces.
#   2. The growth as seeds-at-scale-1447/tools/run_seed_v6.sh runs it: g 36000, SIMPAPER_OUTPUT_DIR, SIMPAPER_SURFACE_ZARR,
#      ZARR_MISSING_LIST, ZARR_CHUNK_MANIFEST, no time cap; here under nice -n 10 and patch-filter-harness-1447/tools/peak.py
#      (ru_maxrss). A sampler writes evidence/rss-<variant>.csv every 10 s: seconds, VmRSS, VmHWM (kB, /proc/<pid>/status),
#      patch files on disk, rel.csv bytes.
#   3. For streamfree only: snapshots at 120, 300, 600, 1200 s while the growth runs, into scratch/run/<variant>/snap-<s>:
#      rel.csv copied first, then the patch files whose id is at most the largest id rel.csv names (a patch is written
#      before its rows, so a file past that id may be half written). Each snapshot then gets the five downstream stages.
#   4. Identity of the growth: sha256 of every file under patches/ and of rel.csv against seeds-at-scale-1447/out/<attempt>/growth
#      (tools/tree_identity.py -> evidence/growth-identity-<variant>.csv).
#   5. Downstream: the tree copied to scratch/run/<variant>/C40 (cp -a, as run_seed_v6.sh does), the stages c, l, vm 10, hm 10,
#      fm 30 10 with the DELIVERED per seed binary (the harness's binary: the growth is the only thing under test), SIMPAPER_PATCH_LIMIT
#      40000, timeout 3600 each; then sheet identity against the delivered C40/patch_<n>.bin (evidence/sheets-identity-<variant>.csv).
#   6. Rows to evidence/growth-<variant>.csv (tool,variant,attempt,quantity,value,what_it_is) through csv.writer.
# SA_CHECK_ONLY=1: every check of 1, the plan printed, nothing created, nothing run. Never edit this file while it runs.
set -u
M=/data/scrollagent/runs/rev1/growth-memory-1447
S=/data/scrollagent/runs/rev1/seeds-at-scale-1447
H=/data/scrollagent/runs/rev1/patch-filter-harness-1447
PY=/data/scrollagent/.venv/bin/python
ZARR=/data/scrollagent/data/datasets/PHerc1447/0
TOOL=growth-memory-1447/tools/grow_measure2.sh
export TMPDIR=/data/tmp
V=$1; A=$2; CAP=${3:-}
BIN=$M/scratch/bin/$V/$A/simpaper10
if [ -n "$CAP" ]; then [[ "$CAP" =~ ^[0-9]+$ ]] && [ "$CAP" -gt 0 ] || { echo "cap must be a positive integer" >&2; exit 2; }; T=$V-cap$CAP; else T=$V; fi
DBIN=$S/scratch/bin-delivered/$A/simpaper10
DG=$S/out/$A/growth; DC=$S/out/$A/C40
W=$M/scratch/run/$T; G=$W/growth
R=$M/evidence/growth-$T.csv
say() { echo "$(date -u +%FT%TZ) [$T $A] $*"; }
row() { $PY -c "import csv,sys; csv.writer(open(sys.argv[1],'a',newline=''),lineterminator='\n').writerow(sys.argv[2:])" "$R" "$TOOL" "$T" "$A" "$1" "$2" "$3" || { say "FATAL: row $1"; exit 6; }; }

GSHA=$($PY - "$M/evidence/binary-gate.csv" "$V" "$A" <<'PYEOF'
import csv, sys
r = [x for x in csv.DictReader(open(sys.argv[1])) if x["variant"] == sys.argv[2] and x["attempt"] == sys.argv[3] and x["passes"] == "yes"]
print(r[-1]["sha256"] if r else "")
PYEOF
)
[ -n "$GSHA" ] && [ -x "$BIN" ] && [ "$(sha256sum "$BIN" | cut -d' ' -f1)" = "$GSHA" ] || { say "REFUSED: $BIN absent or not the gated sha [$GSHA]"; exit 3; }
[ -x "$DBIN" ] && [ -d "$DG/patches" ] && [ -f "$DG/rel.csv" ] && [ -d "$DC" ] || { say "REFUSED: delivered binary or tree of $A absent"; exit 3; }
slots() { local n=0 f; for f in $M/scratch/slots/*.pid; do [ -e "$f" ] || continue; ps -p "$(cat $f)" > /dev/null 2>&1 && n=$((n+1)); done; echo $n; }
memok() { local m; m=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo); [ $((m - 32)) -ge 20 ]; }
diskok() { [ "$(df -B1G --output=avail /data | tail -1 | tr -d ' ')" -ge 70 ]; }

if [ "${SA_CHECK_ONLY:-0}" = 1 ]; then
  say "CHECK ONLY: binary $BIN sha ${GSHA:0:12} (gated), delivered binary for downstream $DBIN"
  say "CHECK ONLY: slots busy $(slots) of 2, MemAvailable $(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo) GB (needs >= 52), /data free $(df -B1G --output=avail /data | tail -1 | tr -d ' ') GB (needs >= 70)"
  say "CHECK ONLY: SIMPAPER_SHARED_CHUNKS [${CAP:-unset}], tag $T"
  say "CHECK ONLY: would grow g 36000 into $G, sample every 10 s into $R and evidence/rss-$T.csv, compare with $DG, downstream into $W/C40, compare with $DC"
  exit 0
fi
[ -e "$W" ] && { say "REFUSED: $W exists"; exit 2; }
mkdir -p $M/scratch/slots
exec 8>$M/scratch/slots.lock
while :; do
  flock 8
  [ "$(slots)" -lt 2 ] && memok && diskok && break
  flock -u 8
  say "hold: slots $(slots), memory or disk below the rule"; sleep 60
done
mkdir -p $G/surface.bp/surface $G/boundary.bp/surface $G/patches $M/log
echo "tool,variant,attempt,quantity,value,what_it_is" > $R
row binary_sha256 "$GSHA" "the growth binary, gated in evidence/binary-gate.csv"
row downstream_binary_sha256 "$(sha256sum $DBIN | cut -d' ' -f1)" "the delivered per seed binary, used for the five downstream stages"
row shared_chunks_cap "${CAP:-unset}" "SIMPAPER_SHARED_CHUNKS given to the growth; unset is the delivered run (a quarter of MemAvailable)"
row mem_available_gb_at_start "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" "/proc/meminfo at the start; other runners were growing"
LOG=$W/growth.log
cd $W
( [ -n "$CAP" ] && export SIMPAPER_SHARED_CHUNKS=$CAP
  SIMPAPER_OUTPUT_DIR=$G SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$G/missing.txt \
  ZARR_CHUNK_MANIFEST=/data/scrollagent/data/datasets/PHerc1447/chunks.txt \
  exec nice -n 10 $PY $H/tools/peak.py $W/peak-growth.txt $BIN g 36000 ) > $LOG 2>&1 8>&- &
PPK=$!
sleep 2
GP=$(ps -o pid= --ppid $PPK | tr -d ' ' | head -1)
[ -n "$GP" ] || { say "no growth pid under $PPK"; }
echo "${GP:-$PPK}" > $M/scratch/slots/$T.pid
flock -u 8
say "growth started, peak.py pid $PPK, simpaper10 pid $GP"
RS=$M/evidence/rss-$T.csv
echo "tool,variant,seconds,vmrss_kb,vmhwm_kb,patch_files,rel_csv_bytes" > $RS
t0=$(date +%s); snaps=""
while ps -p $PPK > /dev/null 2>&1; do
  el=$(( $(date +%s) - t0 ))
  if [ -n "$GP" ] && [ -r /proc/$GP/status ]; then
    rss=$(awk '/^VmRSS/{print $2}' /proc/$GP/status); hwm=$(awk '/^VmHWM/{print $2}' /proc/$GP/status)
    np=$(find $G/patches -maxdepth 1 -name 'patch_*.bin' | wc -l); rb=$(stat -c %s $G/rel.csv 2>/dev/null || echo 0)
    [ -n "$rss" ] && $PY -c "import csv,sys; csv.writer(open(sys.argv[1],'a',newline=''),lineterminator='\n').writerow(sys.argv[2:])" $RS $TOOL $T $el $rss $hwm $np $rb
  fi
  if [ "$V" = streamfree ]; then
    for s in 120 300 600 1200; do
      case " $snaps " in *" $s "*) continue ;; esac
      if [ $el -ge $s ]; then
        $PY $M/tools/snapshot.py $G $W/snap-$s > $W/snap-$s.txt 2>&1 && say "snapshot at $el s: $(cat $W/snap-$s.txt)"
        snaps="$snaps $s"
      fi
    done
  fi
  sleep 10
done
wait $PPK; grc=$?
rm -f $M/scratch/slots/$T.pid
IFS=, read prc psec pkb < $W/peak-growth.txt
say "growth rc $grc in $psec s, ru_maxrss $pkb kB, patches $(ls $G/patches | wc -l)"
row growth_return_code "$grc" "0 is a growth that ended by itself"
row growth_wall_clock_seconds "$psec" "patch-filter-harness-1447/tools/peak.py; other runners were growing"
row growth_peak_rss_kb "$pkb" "ru_maxrss of the growth (getrusage RUSAGE_CHILDREN via peak.py), the exact peak"
row growth_peak_vmhwm_sampled_kb "$($PY -c "import csv,sys; print(max([int(r['vmhwm_kb']) for r in csv.DictReader(open(sys.argv[1]))] or ['not measurable']))" $RS)" "largest VmHWM of evidence/rss-$T.csv, sampled every 10 s"
row growth_patch_files "$(ls $G/patches | wc -l)" "files under patches/"
case "$V" in mem*) grep '^SA_MEM,' $LOG > $M/evidence/memlog-$T.txt ;; esac
$PY $M/tools/tree_identity.py $DG $G $M/evidence/growth-identity-$T.csv growth > $W/gid.txt; gid=$?
row growth_identity "$(cat $W/gid.txt)" "tools/tree_identity.py: every patches/ file and rel.csv, sha256 against the delivered growth tree (rc $gid)"
[ $grc -ne 0 ] && { say "growth failed"; exit 4; }

dstages() {  # <tree> <tag>: the five stages with the delivered binary
  local O=$1 tg=$2 st rc
  for st in "c" "l" "vm 10" "hm 10" "fm 30 10"; do
    ( cd $O && SIMPAPER_OUTPUT_DIR=$O SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$O/missing-C40.txt SIMPAPER_PATCH_LIMIT=40000 \
      nice -n 10 timeout --foreground -s TERM 3600 $DBIN $st ) > $W/stage-$tg-$(echo $st | tr ' ' '_').txt 2>&1
    rc=$?
    [ $rc -ne 0 ] && { echo "stage_${st// /_}_rc_$rc"; return $rc; }
  done
  echo "rc_0_sheets_$(ls $O/patch_[0-9]*.bin 2>/dev/null | wc -l)"
}
cp -a $G $W/C40 || { row downstream "not run" "copy failed"; exit 5; }
d0=$(date +%s); out=$(dstages $W/C40 C40); drc=$?
row downstream "$out" "five stages c, l, vm 10, hm 10, fm 30 10 on the copy, $(( $(date +%s)-d0 )) s"
$PY $M/tools/tree_identity.py $DC $W/C40 $M/evidence/sheets-identity-$T.csv sheets > $W/sid.txt; sid=$?
row sheets_identity "$(cat $W/sid.txt)" "tools/tree_identity.py: sha256 of every delivered C40/patch_<n>.bin against this run's (rc $sid)"
say "downstream $out, sheets identity $(cat $W/sid.txt)"
for s in 120 300 600 1200; do
  [ -d $W/snap-$s ] || continue
  out=$(dstages $W/snap-$s snap-$s)
  row "snapshot_${s}_s" "$(cat $W/snap-$s.txt); downstream $out" "tools/snapshot.py then the five stages on the snapshot"
  say "snapshot $s: $out"
done
gzip -c $LOG > $M/log/growth-$T-$A.txt.gz
say "done"
