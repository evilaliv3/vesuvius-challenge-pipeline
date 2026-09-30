#!/bin/bash
# regrow72.sh <seed>: PLAN item 95 (c). New file, written 2026-09-28T12:5xZ by a coordinator agent (DECLARATION.md of this
# study). The growth and downstream of chain-0826/tools/run_seed.sh, with these differences and no others:
#   1. the study is runs/rev1/square20-0826-95 (out/, log/, evidence/ here; nothing written under chain-0826);
#   2. the binary is the one the chain delivered this seed with: chain-0826/scratch/bin-<binary_series>/<seed>/simpaper10,
#      series and sha256 read from chain-0826/evidence/runs/<seed>.csv and checked before the start (exit 3 otherwise);
#   3. the growth is «g 72000» (the chain's is g 36000; each of the five reached generation 36000, evidence/cap-check.csv);
#   4. the downstream stages are the chain's five (c, l, vm 10, hm 10, fm 30 10) into out/<seed>/C80 with
#      SIMPAPER_PATCH_LIMIT 80000: the loader drops patch numbers above the limit, so the chain's 40000 would cut a
#      72000 growth near 40000; 80000 keeps every generation, as 40000 did at g 36000 (larger-sheets-1447's g 72000 did
#      the same); the downstream cap is run_seed.sh's formula;
#   5. the environment is the chain's: SIMPAPER_SHARED_CHUNKS, SIMPAPER_FORCE_THREADS, OMP_WAIT_POLICY, OMP_NUM_THREADS
#      read from chain-0826/scratch/deliver-settings.env (read, never written), the growth reading the chain's
#      GROWTH_ZARR (hot-lines-88 L copy, identical decoded bytes) and the manifest, the downstream the original zarr;
#   6. VmHWM of the growth sampled every 10 s into evidence/rss-<seed>.csv;
#   7. the construction check: rel.csv rows whose two patch numbers are both at most 36000, and patch_<n>.bin files with
#      n at most 36000, against chain-0826/out/<seed>/growth/rel.csv and chain-0826/out/<seed>/C40/patches (sha256),
#      into evidence/identity-36000-<seed>.csv; reported, not a gate;
#   8. then tools/measure72.sh (square.py, traced area) and tools/a2_72.py (the a2 cluster column), and a result row
#      evidence/result-<seed>.csv: best square_mm_min_step at g 72000 beside g 36000 and 20 mm;
#   9. after the measurement, growth/patches is removed (C80 holds its copy, as the chain keeps its trees in C40).
set -u
C=/data/scrollagent/runs/rev1/chain-0826
S=/data/scrollagent/runs/rev1/square20-0826-95
A=${1:?seed}
TOOL=square20-0826-95/tools/regrow72.sh
PY=/data/scrollagent/.venv/bin/python
export TMPDIR=/data/tmp
ZARR=/data/scrollagent/data/datasets/PHerc0826/0
GROWTH_ZARR=/data/scrollagent/runs/rev1/hot-lines-88/scratch/l/0
MAN=/data/scrollagent/data/datasets/PHerc0826/chunks.txt
L=$S/log; R=$S/evidence/runs-$A.csv; G=$S/out/$A/growth
say() { echo "$(date -u +%FT%TZ) [$A regrow72] $*"; }
row() {
  $PY - "$R" "$TOOL" "$A" "$1" "$2" "$3" <<'PYEOF'
import csv, sys
p = sys.argv[1]
with open(p, "a", newline="") as f:
    csv.writer(f, lineterminator="\n").writerow(sys.argv[2:7])
PYEOF
}
rq() { awk -F, -v q="$1" '$3==q {v=$4} END {print v}' "$C/evidence/runs/$A.csv"; }
SERIES=$(rq binary_series); WANT=$(rq binary_sha256)
BIN=$C/scratch/bin-$SERIES/$A/simpaper10
[ -x "$BIN" ] || { say "no binary at $BIN"; exit 3; }
HAVE=$(sha256sum "$BIN" | cut -d' ' -f1)
[ -n "$WANT" ] && [ "$HAVE" = "$WANT" ] || { say "REFUSED: $BIN sha $HAVE is not the chain run's [$WANT]"; exit 3; }
[ -f "$GROWTH_ZARR/.zarray" ] || { say "REFUSED: $GROWTH_ZARR has no .zarray"; exit 3; }
for k in SIMPAPER_SHARED_CHUNKS SIMPAPER_FORCE_THREADS OMP_WAIT_POLICY OMP_NUM_THREADS; do
  v=$(grep -E "^$k=" $C/scratch/deliver-settings.env | tail -1 | cut -d= -f2)
  [[ "$v" =~ ^[A-Za-z0-9]+$ ]] || { say "REFUSED: $k not read from deliver-settings.env [$v]"; exit 3; }
  export $k=$v
done
[ -e "$G" ] && { say "REFUSED: $G exists (a growth tree is never written twice)"; exit 3; }
mkdir -p $S/out/$A $G/surface.bp/surface $G/boundary.bp/surface $G/patches $S/evidence
echo "tool,attempt,quantity,value,what_it_is" > $R
row binary_sha256 "$HAVE" "the chain-0826 delivered binary, equal to binary_sha256 of chain-0826/evidence/runs/$A.csv"
row binary_series "$SERIES" "chain-0826/scratch/bin-$SERIES/$A/simpaper10"
row environment "SIMPAPER_SHARED_CHUNKS=$SIMPAPER_SHARED_CHUNKS SIMPAPER_FORCE_THREADS=$SIMPAPER_FORCE_THREADS OMP_WAIT_POLICY=$OMP_WAIT_POLICY OMP_NUM_THREADS=$OMP_NUM_THREADS" "read from chain-0826/scratch/deliver-settings.env, exported to the growth and the five stages"
row growth_zarr "$GROWTH_ZARR" "the chain's growth prediction; downstream stages read $ZARR"
cd $S/out/$A || exit 3
t0=$(date +%s)
say "growth g 72000 starts, no time cap, binary $SERIES sha ${HAVE:0:12}"
SIMPAPER_OUTPUT_DIR=$G SIMPAPER_SURFACE_ZARR=$GROWTH_ZARR ZARR_MISSING_LIST=$G/missing.txt ZARR_CHUNK_MANIFEST=$MAN \
  $BIN g 72000 > $L/growth-$A.txt 2>&1 &
GP=$!
echo "time,vmhwm_kb" > $S/evidence/rss-$A.csv
while kill -0 $GP 2>/dev/null; do
  h=$(awk '/^VmHWM/ {print $2}' /proc/$GP/status 2>/dev/null); [ -n "$h" ] && echo "$(date -u +%FT%TZ),$h" >> $S/evidence/rss-$A.csv
  sleep 10
done
wait $GP; rc=$?
secs=$(( $(date +%s)-t0 ))
patches=$(ls $G/patches | wc -l)
hi=$(grep -a '^Patch [0-9]* had' $L/growth-$A.txt | awk '{print $2}' | sort -n | tail -1)
say "growth rc=$rc in $secs s, patches $patches, highest generation $hi"
row growth_return_code "$rc" "0 is a growth that ended by itself or at g 72000; no time cap"
row growth_wall_clock_seconds "$secs" "wall clock from date, the machine carried other work"
row growth_patches "$patches" "files under the growth tree's patches/"
row growth_highest_generation "${hi:-none}" "largest N of «Patch N had» in log/growth-$A.txt; 72000 or more is the cap"
row growth_rel_csv_lines "$(wc -l < $G/rel.csv 2>/dev/null || echo 'not measurable')" "lines of rel.csv"
row growth_peak_vmhwm_kb "$(tail -n +2 $S/evidence/rss-$A.csv | cut -d, -f2 | sort -n | tail -1)" "largest VmHWM sampled every 10 s, evidence/rss-$A.csv"
row growth_missing_chunks "$(grep -a 'Zarr chunks absent from disk during growth:' $L/growth-$A.txt | tail -1 | sed 's/.*growth: *\([0-9]*\).*/\1/')" "read from the growth's standard output"
[ $rc -eq 0 ] || { row downstream_return_code "not run" "the growth returned $rc"; exit 4; }

# 7 construction check, reported only
$PY - "$A" "$G" "$C/out/$A/growth/rel.csv" "$C/out/$A/C40/patches" "$S/evidence/identity-36000-$A.csv" <<'PYEOF' > $L/identity-36000-$A.txt 2>&1
import csv, hashlib, os, subprocess, sys
a, g, oldrel, oldp, out = sys.argv[1:6]
def rel(p):
    v = []
    for l in open(p):
        f = l.split(",")
        if len(f) > 1 and int(float(f[0])) <= 36000 and int(float(f[1])) <= 36000:
            v.append(l.rstrip("\n"))
    return v
n_new, n_old = rel(os.path.join(g, "rel.csv")), rel(oldrel)
def pn(f):
    return int("".join(c for c in f if c.isdigit()))
def pats(d):
    return {f: hashlib.sha256(open(os.path.join(d, f), "rb").read()).hexdigest() for f in os.listdir(d)
            if f.endswith(".bin") and pn(f) <= 36000}
pn_new, pn_old = pats(os.path.join(g, "patches")), pats(oldp)
same = sum(1 for f in pn_old if pn_new.get(f) == pn_old[f])
t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
with open(out, "w", newline="") as fh:
    fh.write('"# written by square20-0826-95/tools/regrow72.sh at %s: the g 72000 regrowth of %s against the chain-0826 g 36000 '
             'growth, patch numbers at most 36000; reported, not a gate"\n' % (t, a))
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["attempt", "quantity", "g72000", "g36000", "equal"])
    w.writerow([a, "rel_rows_both_at_most_36000_in_order", len(n_new), len(n_old), "yes" if n_new == n_old else "no"])
    w.writerow([a, "rel_rows_both_at_most_36000_as_sets", len(set(n_new)), len(set(n_old)), "yes" if set(n_new) == set(n_old) else "no"])
    w.writerow([a, "patch_files_at_most_36000_sha256_equal", len(pn_new), len(pn_old), "%d of %d" % (same, len(pn_old))])
print("identity: rel in order %s, as sets %s, patches %d of %d equal (%d new)" % (n_new == n_old, set(n_new) == set(n_old), same, len(pn_old), len(pn_new)))
PYEOF
say "$(tail -1 $L/identity-36000-$A.txt)"

N=C80; LIM=80000
RELLINES=$(wc -l < $G/rel.csv)
CAP=$($PY -c "import sys; n=float(sys.argv[1] or 0); print(int(min(14400.0, max(3600.0, 60.0*(n/25505.0)**2))))" "$RELLINES")
row downstream_cap_seconds "$CAP" "run_seed.sh's formula on $RELLINES rel lines"
O=$S/out/$A/$N
rm -rf $O && cp -a $G $O || { row downstream_return_code "not run" "copy failed"; exit 5; }
d0=$(date +%s)
for st in "c" "l" "vm 10" "hm 10" "fm 30 10"; do
  left=$(( CAP - ($(date +%s)-d0) ))
  [ $left -lt 1 ] && { row downstream_return_code 124 "the $CAP s downstream cap was reached"; exit 5; }
  t1=$(date +%s)
  SIMPAPER_OUTPUT_DIR=$O SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$O/missing-$N.txt SIMPAPER_PATCH_LIMIT=$LIM \
    timeout --foreground -s TERM $left $BIN $st > "$L/chain-$A-$N-$(echo $st | tr ' ' '_').txt" 2>&1
  rc=$?
  row "downstream_stage_$(echo $st | tr ' ' '_')_seconds" "$(( $(date +%s)-t1 ))" "wall clock of this stage"
  say "$N stage '$st' rc=$rc"
  [ $rc -ne 0 ] && { row downstream_return_code "$rc" "the stage '$st' returned it"; exit 5; }
done
row downstream_return_code 0 "all five stages returned zero, SIMPAPER_PATCH_LIMIT $LIM"
row delivered_sheets "$(ls $O/patch_*.bin 2>/dev/null | wc -l)" "patch_<n>.bin written by the fm stage"

bash $S/tools/measure72.sh "$A" >> $L/measure-$A.txt 2>&1; m=$?
say "measure72.sh rc=$m"
row measure_return_code "$m" "tools/measure72.sh: square.py and traced area"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLOSC_NTHREADS=1 \
  nice -n 10 $PY $S/tools/a2_72.py "$A" >> $L/a2-cluster-$A.txt 2>&1; r2=$?
row a2_return_code "$r2" "tools/a2_72.py"
say "a2 rc=$r2"
[ $m -eq 0 ] && rm -rf "$G/patches" && row growth_patches_removed yes "C80/patches holds the copy"

$PY - "$A" "$S/evidence/squares-$A.csv" "$C/evidence/squares-$A.csv" "$S/evidence/a2-cluster/$A.csv" "$S/evidence/result-$A.csv" <<'PYEOF'
import csv, os, subprocess, sys
a, new, old, a2, out = sys.argv[1:6]
def rows(p):
    if not os.path.exists(p):
        return []
    return list(csv.DictReader([l for l in open(p, newline="") if not l.lstrip().startswith('"#')]))
def best(p):
    m = [r for r in rows(p) if r.get("status") == "measured"]
    if not m:
        return None, None
    b = max(m, key=lambda r: float(r["square_mm_min_step"]))
    return b["square_mm_min_step"], b["sheet"]
bn, sn = best(new); bo, so = best(old)
a2r = {r["sheet"]: r for r in rows(a2)}
t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
with open(out, "w", newline="") as f:
    f.write('"# written by square20-0826-95/tools/regrow72.sh at %s: best square_mm_min_step of the g 72000 regrowth (C80) '
            'beside the chain-0826 g 36000 delivery (C40) and the 20 mm bar of PLAN item 95"\n' % t)
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["attempt", "best_square_mm_g72000", "best_sheet_g72000", "best_square_mm_g36000", "best_sheet_g36000",
                "gain_mm", "meets_20_mm", "a2_cluster_rule_square_mm_of_best_sheet"])
    gain = "%.4f" % (float(bn) - float(bo)) if bn and bo else "not measurable"
    w.writerow([a, bn or "not measurable", sn or "", bo or "not measurable", so or "", gain,
                ("yes" if float(bn) >= 20.0 else "no") if bn else "not measurable",
                a2r.get(sn, {}).get("a2_cluster_rule_square_mm", "not measurable") if sn else "not measurable"])
print("result %s: g72000 %s (sheet %s), g36000 %s, gain %s" % (a, bn, sn, bo, gain))
PYEOF
say "done"
