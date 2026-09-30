#!/bin/bash
# chain-0826 copy of seeds-at-scale-1447/tools/run_seed_v6.sh, written 2026-09-26 by a coordinator agent (DECLARATION.md part 2):
# paths and names moved to chain-0826 and PHerc0826 (study root, prediction, raw volume, draw and queue file names, ledger
# slugs chain-0826-deliver-*); every other change is listed below this line; the text after the list is the original's.
#   STAGED (scratch/next-mlp-z/tools/, 2026-09-27, director's order of 08:48:07Z; installed only by scratch/next-mlp-z/apply.sh):
#   Z. the GROWTH alone (simpaper10 g 36000) reads GROWTH_ZARR, codec-z-0826's copy of the prediction (blosc zstd clevel 1,
#      shuffle 0, blosc2 chunk format: readable by zarr_1.c's c-blosc2 only; codec-z-0826/evidence/identity-summary.csv
#      verdict identical, 46715 of 46715 chunks decoded byte identical); the five downstream stages keep ZARR, the original.
#      The chunk manifest stays the original's (its chunk list equals the copy's: identity-summary.csv lists_equal yes).
#   L. From 2026-09-27T14:1xZ (owner's choice, director's note 14:13:52Z) GROWTH_ZARR is hot-lines-88's lz4hc 5 shuffle 0 copy:
#      hot-lines-88/evidence/identity-l-summary.csv verdict identical (46715 of 46715); clock Z against L on seed237 passes
#      (clock-summary, trees identical 3830 of 3830). Same c-blosc2 path as Z; the Z copy is kept until the owner says.
#      A GROWTH_ZARR whose .zarray is absent refuses at the start (exit 3); a row growth_zarr names it in the seed's CSV.
#   B. the binary is the per seed build of the settings file's BUILD variant (CHAIN_BUILD), sha checked against its gate row.
# run_seed_v6.sh: run_seed_v5.sh with ONE change, in a NEW FILE, written 2026-09-25T06:2xZ for the rerun after the crash of
# 2026-09-24 (director's order of 2026-09-24T21:52:09Z point 1), called by tools/deliver_guarded12.sh:
#   NO TIME CAP ON THE GROWTH (coordinator.md addition of 2026-09-21T09:17:55Z: this chain writes its patches at the end,
#   so a time cap on a growth destroys the whole growth and protects nothing the memory guard does not). v5 ran the growth
#   under «timeout 10800»; v6 runs it bare. No growth run of this study reached 10800 s (the longest growth_wall_clock_seconds
#   row in evidence/runs/ is 4475 s, seed169; no growth_return_code 124), so the change moves no row of the series; a growth that would have been cut at 10800 s now
#   ends by itself, and its wall clock row says how long it took. The downstream cap (capfor) is unchanged.
# Everything below is v5's text, unchanged except TOOL, the log tag v6, the growth line and the texts that named the cap.
#
# run_seed_v5.sh: run_seed_v4.sh with ONE change, in a NEW FILE because v4 is executing for seeds 1300 and 1390
# (deliver_guarded10.sh's subshells). Written 2026-09-24T14:0xZ on the director's order of 2026-09-24T13:53:31Z point 4,
# the same fix larger-sheets-1447/tools/run_larger_v3.sh received at 12:4xZ:
#   EVERY ROW THROUGH csv.writer. v4's row() wrote printf "$TOOL,$1,$2,$3,$4" with no quoting, so a comma in
#   what_it_is (growth_return_code, growth_wall_clock_seconds, downstream_cap_seconds, downstream_return_code 0) gave
#   the row six or nine fields. v5's row() passes the five fields to python's csv.writer, and before appending it
#   reads the file with csv.reader and refuses (exit 6, the seed stops, nothing written) unless the header is exactly
#   tool,attempt,quantity,value,what_it_is and every row already there has five fields. The rows v4 wrote were
#   rewritten by tools/repair_unquoted_rows_v4.py (originals in evidence/runs-original-unquoted/, each row in
#   evidence/unquoted-rows-repair.csv).
# SA_CHECK_ONLY=1 also tests row() on scratch files under /data/tmp: a note with commas is read back as five fields,
# a wrong header and a malformed row are refused with nothing written.
# Everything below is v4's text, unchanged except TOOL, the log tag v5 and row().
#
# --- v4's header follows ---
# run_seed_v4.sh: run_seed_v3.sh with the changes below, in a NEW FILE because v3 is executing for
# seeds 55, 64, 65, 72 and 73. Written 2026-09-23 on the director's decision of 18:14:20Z.
#
#   1. BIN is the delivered series' per seed binary, scratch/bin-delivered/<seed>/simpaper10
#      (corrected + acceleration, tools/build_binaries_delivered.py, evidence/binary-gate-delivered.csv).
#   2. A second argument `downstream_only` reruns the five downstream stages from the seed's
#      existing growth tree, with no growth. The growth rows of the v3 run stay where they are, in
#      evidence/runs/<seed>.csv, untouched; this mode writes its own rows to
#      evidence/runs/<seed>-delivered-downstream.csv. The cap is computed exactly as v3 computes it.
#   3. In the full mode an existing evidence/runs/<seed>.csv (an earlier run, stopped or not) is
#      moved to evidence/runs/superseded/ with a time stamp before the new one is written, so a
#      stop leaves its trace instead of being overwritten.
#   4. SA_CHECK_ONLY=1 checks the inputs (binary, growth tree, rel.csv), prints the plan and the cap
#      it would use and exits 0 without writing anything or running the binary.
#   5. Every CSV row names this tool in a first column `tool`.
#   6. A row binary_series says which series the binary is from.
# The stages, their order, SIMPAPER_PATCH_LIMIT, the environment, the growth cap and the downstream
# cap formula are v3's, unchanged. The cap is not raised for the new binary.
#
# --- v3's header follows ---
# run_seed_v3.sh: v2 with ONE change: ZARR_CHUNK_MANIFEST is passed to the growth.
# run_seed_v2.sh: the count of zarr chunks absent during growth is read from the growth's stdout.
# seed-search-1447: grow one drawn seed of PHerc. 1447 to the end and deliver it. A run stopped by
# its cap comes back with a non zero return code and stays non zero: this study measures no square
# on a tree whose growth did not finish.
#
# Usage: run_seed_v4.sh PHerc1447-seedNN [downstream_only]
set -u
S=/data/scrollagent/runs/rev1/chain-0826
A=$1
MODE=${2:-full}
TOOL=chain-0826/tools/run_seed.sh
# chain-0826 B: the per seed binary of the variant CHAIN_BUILD (exported by tools/deliver_settings.sh from the settings
# file's BUILD), verified at every start against its gate row by sha256; no variant, no gate or another sha: exit 3.
CHAIN_BUILD=${CHAIN_BUILD:?CHAIN_BUILD not exported (tools/deliver_settings.sh)}
BIN=$S/scratch/bin-$CHAIN_BUILD/$A/simpaper10
GATE=$S/evidence/gates/binary-gate-$CHAIN_BUILD-$A.csv
ZARR=/data/scrollagent/data/datasets/PHerc0826/0
GROWTH_ZARR=/data/scrollagent/runs/rev1/hot-lines-88/scratch/l/0   # L (lz4hc 5, shuffle 0), since 2026-09-27T14:1xZ, owner's choice 14:13:52Z: the growth only
L=$S/log
PY=${PY:-/data/scrollagent/.venv/bin/python}
G=$S/out/$A/growth
case "$MODE" in
  full)            R=$S/evidence/runs/$A.csv ;;
  downstream_only) R=$S/evidence/runs/$A-delivered-downstream.csv ;;
  *) echo "unknown mode $MODE (full, downstream_only)" >&2; exit 2 ;;
esac

say() { echo "$(date -u +%FT%TZ) [$A v6 $MODE] $*"; }
rowto() {  # v5: file attempt quantity value what_it_is; csv.writer, header and every existing row checked first
  $PY - "$1" "$TOOL" "$2" "$3" "$4" "$5" <<'PYEOF'
import csv, sys
p, row = sys.argv[1], sys.argv[2:7]
head = ["tool", "attempt", "quantity", "value", "what_it_is"]
with open(p, newline="") as f:
    rows = list(csv.reader(f))
if not rows or rows[0] != head:
    sys.exit("REFUSED: header of %s is %r, not %r" % (p, rows[0] if rows else None, head))
bad = [i + 1 for i, r in enumerate(rows) if len(r) != len(head)]
if bad:
    sys.exit("REFUSED: %s lines %s do not have %d fields" % (p, bad, len(head)))
if len(row) != len(head):
    sys.exit("REFUSED: the row has %d fields, the header %d" % (len(row), len(head)))
with open(p, "a", newline="") as f:
    csv.writer(f, lineterminator="\n").writerow(row)
PYEOF
  local r=$?
  [ $r -eq 0 ] || { say "FATAL: row $3 not written to $1 (rc $r): the seed stops here"; exit 6; }
}
row() { rowto "$R" "$1" "$2" "$3" "$4"; }
capfor() { $PY -c "import sys; n=float(sys.argv[1] or 0); print(int(min(14400.0, max(3600.0, 60.0*(n/25505.0)**2))))" "$1"; }

[ -x "$BIN" ] || { say "no binary at $BIN"; exit 3; }
GSHA=$(awk -F, -v a="$A" '$2==a && $6=="differs_from_stock" && $9=="yes" {s=$5} END {print s}' "$GATE" 2>/dev/null)
BSHA=$(sha256sum "$BIN" | cut -d' ' -f1)
[ -n "$GSHA" ] && [ "$GSHA" = "$BSHA" ] || { say "REFUSED: $BIN sha256 $BSHA is not the gate's [$GSHA] ($GATE)"; exit 3; }
[ -f "$GROWTH_ZARR/.zarray" ] || { say "REFUSED: GROWTH_ZARR $GROWTH_ZARR has no .zarray"; exit 3; }   # Z
if [ "$MODE" = downstream_only ]; then
  [ -f "$G/rel.csv" ] || { say "downstream_only needs a growth tree with rel.csv at $G"; exit 3; }
fi

if [ "${SA_CHECK_ONLY:-0}" = 1 ]; then
  say "CHECK ONLY: binary $BIN sha $(sha256sum $BIN | cut -c1-12), csv $R; growth zarr $GROWTH_ZARR, downstream zarr $ZARR"
  if [ -f "$G/rel.csv" ]; then
    n=$(wc -l < $G/rel.csv); say "CHECK ONLY: growth tree $G, rel lines $n, downstream cap would be $(capfor $n) s"
  else
    say "CHECK ONLY: no growth tree yet; full mode would grow g 36000 with no time cap"
  fi
  say "CHECK ONLY: stages c, l, vm 10, hm 10, fm 30 10 into $S/out/$A/C40, SIMPAPER_PATCH_LIMIT=40000; nothing run, nothing written"
  TD=$(mktemp -d /data/tmp/run-seed-v6-rowtest.XXXXXX)   # v5: the row test, on scratch files only
  echo "tool,attempt,quantity,value,what_it_is" > $TD/good.csv
  ( rowto $TD/good.csv rowtest growth_return_code 0 "0 is a growth that ended by itself, with no time cap" ); r1=$?
  nf=$($PY -c "import csv,sys; print(','.join(str(len(r)) for r in csv.reader(open(sys.argv[1], newline=''))))" $TD/good.csv)
  back=$($PY -c "import csv,sys; print([r for r in csv.reader(open(sys.argv[1], newline=''))][-1])" $TD/good.csv)
  say "CHECK ONLY: row with commas: rc $r1 (want 0), fields per line [$nf] (want 5,5), row read back $back"
  echo "tool,attempt,quantity,value" > $TD/badhead.csv
  ( rowto $TD/badhead.csv rowtest x 1 y ) 2>/dev/null; r2=$?
  printf 'tool,attempt,quantity,value,what_it_is\na,b,c,d,e,f\n' > $TD/badrow.csv
  ( rowto $TD/badrow.csv rowtest x 1 y ) 2>/dev/null; r3=$?
  say "CHECK ONLY: wrong header rc $r2 (want 6), six field row present rc $r3 (want 6); lines after: $(wc -l < $TD/badhead.csv) and $(wc -l < $TD/badrow.csv) (want 1 and 2)"
  rm -rf "$TD"
  exit 0
fi

mkdir -p $S/evidence/runs
if [ "$MODE" = full ] && [ -f "$R" ]; then
  mkdir -p $S/evidence/runs/superseded
  mv "$R" "$S/evidence/runs/superseded/$A.before-$(date -u +%Y%m%dT%H%M%SZ).csv"
fi
if [ "$MODE" = downstream_only ] && [ -f "$R" ]; then
  mkdir -p $S/evidence/runs/superseded
  mv "$R" "$S/evidence/runs/superseded/$A-delivered-downstream.before-$(date -u +%Y%m%dT%H%M%SZ).csv"
fi
echo "tool,attempt,quantity,value,what_it_is" > $R
row $A binary_sha256 "$(sha256sum $BIN | cut -d' ' -f1)" "the per seed binary this run used"
row $A binary_series "$CHAIN_BUILD" "tools/build_variant_seed.py variant $CHAIN_BUILD on build.sh delivered (corrected plus acceleration); sha checked against $GATE"
row $A mode "$MODE" "full grows then delivers; downstream_only delivers from the existing growth tree"
row $A growth_zarr "$GROWTH_ZARR" "the prediction the growth read (L copy lz4hc 5, hot-lines-88; before 2026-09-27T14:1xZ the Z copy, codec-z-0826); downstream stages read $ZARR"

cd $S/out/$A 2>/dev/null || { mkdir -p $S/out/$A && cd $S/out/$A; } || exit 3
if [ "$MODE" = full ]; then
  mkdir -p $G/surface.bp/surface $G/boundary.bp/surface $G/patches
  t0=$(date +%s)
  say "growth g 36000 starts, no time cap"
  SIMPAPER_OUTPUT_DIR=$G SIMPAPER_SURFACE_ZARR=$GROWTH_ZARR ZARR_MISSING_LIST=$G/missing.txt \
    ZARR_CHUNK_MANIFEST=/data/scrollagent/data/datasets/PHerc0826/chunks.txt \
    $BIN g 36000 > $L/growth-$A.txt 2>&1
  rc=$?
  secs=$(( $(date +%s)-t0 ))
  patches=$(ls $G/patches 2>/dev/null | wc -l)
  say "growth rc=$rc in $secs s, patches $patches"
  row $A growth_return_code "$rc" "0 is a growth that ended by itself; no time cap (run_seed_v6.sh)"
  row $A growth_wall_clock_seconds "$secs" "wall clock from date, the machine carried other growths"
  row $A growth_patches "$patches" "files under the growth tree's patches/"
  if [ -f $G/rel.csv ]; then
    row $A growth_rel_csv_lines "$(wc -l < $G/rel.csv)" "lines of rel.csv in the growth tree"
  else
    row $A growth_rel_csv_lines "not measurable" "the growth wrote no rel.csv"
  fi
  if [ -f $G/missing.txt ]; then
    row $A growth_missing_chunks "$(wc -l < $G/missing.txt)" "lines of ZARR_MISSING_LIST"
  elif grep -q "Zarr chunks absent from disk during growth:" $L/growth-$A.txt; then
    row $A growth_missing_chunks "$(grep 'Zarr chunks absent from disk during growth:' $L/growth-$A.txt | tail -1 | sed 's/.*growth: *\([0-9]*\).*/\1/')" "read from the growth's own standard output"
  else
    row $A growth_missing_chunks "not measurable" "ZARR_MISSING_LIST wrote no file"
  fi
  if [ $rc -ne 0 ]; then
    say "growth did not finish, no downstream and no square"
    row $A downstream_return_code "not run" "the growth returned non zero"
    exit 4
  fi
fi

N=C40; LIM=40000
RELLINES=$(wc -l < $G/rel.csv 2>/dev/null || echo 0)
DOWNSTREAM_CAP=$(capfor "$RELLINES")
[[ "$DOWNSTREAM_CAP" =~ ^[0-9]+$ ]] || { say "cap not computed: [$DOWNSTREAM_CAP]"; row $A downstream_return_code "not run" "the downstream cap could not be computed"; exit 5; }
say "downstream cap $DOWNSTREAM_CAP s for $RELLINES rel lines, by the amendment of 19:52Z"
row $A downstream_cap_seconds "$DOWNSTREAM_CAP" "computed from $RELLINES lines of the growth's rel.csv, not a constant"
O=$S/out/$A/$N
say "$N: copying the growth tree"
rm -rf $O && cp -a $G $O || { say "copy failed"; row $A downstream_return_code "not run" "the growth tree could not be copied"; exit 5; }
d0=$(date +%s)
for st in "c" "l" "vm 10" "hm 10" "fm 30 10"; do
  left=$(( DOWNSTREAM_CAP - ($(date +%s)-d0) ))
  [ $left -lt 1 ] && { say "$N: downstream budget spent before stage '$st'"; row $A downstream_return_code "124" "the ${DOWNSTREAM_CAP} s downstream cap was reached"; exit 5; }
  t0=$(date +%s)
  LOG=$L/chain-$A-$N-$(echo $st | tr ' ' '_')-v4.txt
  SIMPAPER_OUTPUT_DIR=$O SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$O/missing-$N.txt \
    SIMPAPER_PATCH_LIMIT=$LIM timeout --foreground -s TERM $left $BIN $st > "$LOG" 2>&1
  rc=$?
  say "$N stage '$st' rc=$rc in $(( $(date +%s)-t0 )) s, sheets $(ls $O/patch_*.bin 2>/dev/null | wc -l)"
  row $A "downstream_stage_$(echo $st | tr ' ' '_')_seconds" "$(( $(date +%s)-t0 ))" "wall clock of this stage"
  [ $rc -ne 0 ] && { say "$N: stage '$st' failed"; row $A downstream_return_code "$rc" "the stage '$st' returned it"; exit 5; }
done
row $A downstream_return_code "0" "all five stages of c, l, vm 10, hm 10, fm 30 10 returned zero"
row $A downstream_wall_clock_seconds "$(( $(date +%s)-d0 ))" "wall clock of the five stages together"
row $A delivered_sheets "$(ls $O/patch_*.bin 2>/dev/null | wc -l)" "patch_<n>.bin written by the fm stage"
say "$N done, sheets $(ls $O/patch_*.bin 2>/dev/null | wc -l)"
say "chain finished"
