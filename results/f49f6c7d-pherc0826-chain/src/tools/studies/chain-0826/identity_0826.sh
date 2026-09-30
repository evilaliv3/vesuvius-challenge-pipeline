#!/bin/bash
# identity_0826.sh: the identity bar of G6 for a BUILD variant against unchanged (DECLARATION.md addition of
# 2026-09-26T19:03:06Z). Written 2026-09-26T19:0xZ by a coordinator agent.
#   usage: identity_0826.sh <variant> <seed> [<seed> ...]
# 1. builds, one at a time under scratch/build.lock: tools/build_variant_seed.py <variant> and unchanged, per seed, into
#    scratch/bin-<variant>/<seed>/ with gates evidence/gates/binary-gate-<variant>-<seed>.csv (the runner's own paths);
# 2. one job per seed and arm, all at once while MemAvailable minus PEAK_GB per growth to start stays at or above FLOOR_GB
#    (settings file): growth g 36000 with the settings file's environment (tools/deliver_settings.sh ds_apply), then c, l,
#    vm 10, hm 10, fm 30 10 with SIMPAPER_PATCH_LIMIT 40000 on a copy of the growth tree, as tools/run_seed.sh; into
#    scratch/identity/<arm>/<seed>/{growth,C40}. No growth starts after LAST_START; every process gets
#    timeout --foreground to DEADLINE, and a seed stopped by it is «not measurable, stopped before the hold»;
# 3. per seed: growth-memory-1447/tools/tree_identity.py growth and sheets, and the sha256 of the C40 stage files of
#    patch-filter-harness-1447's identity_compare.py STAGE_FILES; evidence/identity-0826.csv (one row per seed) and
#    evidence/identity-0826-summary.csv (build first, identity_holds last), a ledger row.
# SA_CHECK_ONLY=1: the plan, the settings, the binaries present, the memory gate; runs and writes nothing.
set -u
S=/data/scrollagent/runs/rev1/chain-0826
PY=/data/scrollagent/.venv/bin/python
TI=/data/scrollagent/runs/rev1/growth-memory-1447/tools/tree_identity.py
ZARR=/data/scrollagent/data/datasets/PHerc0826/0
MANIFEST=/data/scrollagent/data/datasets/PHerc0826/chunks.txt
DRAW=$S/evidence/seeds-PHerc0826-draw400.csv
LAST_START=2026-09-26T21:30:00Z; DEADLINE=2026-09-26T23:20:00Z
PEAK_GB=6
STAGE_FILES="badpatches.csv badpatchscores.csv patchVolCoords.csv alignmentorders.txt neighbourss.csv badbridgess_out.csv patchorder.csv patchorders.csv"
TOOL=chain-0826/tools/identity_0826.sh
export TMPDIR=/data/tmp
V=${1:?variant}; shift
SEEDS=("$@"); [ ${#SEEDS[@]} -ge 1 ] || { echo "no seed"; exit 2; }
say() { echo "$(date -u +%FT%TZ) [identity $V] $*"; }
case "$V" in flathash|flathash+avx512) ;; *) say "REFUSED: variant $V (flathash or flathash+avx512 against unchanged)"; exit 2 ;; esac
source "$S/tools/deliver_settings.sh" || { say "REFUSED: deliver_settings.sh"; exit 3; }
ds_apply "$S/scratch/deliver-settings.env" || { say "REFUSED: settings: $DS_ERR"; exit 3; }
[ "$CHAIN_BUILD" = "$V" ] || say "note: the settings file's BUILD is $CHAIN_BUILD, this bar tests $V"
for a in "${SEEDS[@]}"; do grep -qx "$a" "$S/evidence/queue.txt" || { say "REFUSED: $a not in evidence/queue.txt"; exit 3; }; done
LS=$(date -u -d "$LAST_START" +%s); DL=$(date -u -d "$DEADLINE" +%s)
left() { echo $(( DL - $(date +%s) )); }
say "settings $DS_LINE; seeds ${SEEDS[*]}; last start $LAST_START, deadline $DEADLINE"

gate_sha() {  # variant seed -> sha of the gated binary, empty if absent or not yes
  awk -F, -v a="$2" '$2==a && $6=="differs_from_stock" && $9=="yes" {s=$5} END {print s}' "$S/evidence/gates/binary-gate-$1-$2.csv" 2>/dev/null
}
bin_of() { echo "$S/scratch/bin-$1/$2/simpaper10"; }

if [ "${SA_CHECK_ONLY:-0}" = 1 ]; then
  for a in "${SEEDS[@]}"; do for arm in "$V" unchanged; do
    b=$(bin_of "$arm" "$a"); say "CHECK ONLY: $arm $a binary $([ -x "$b" ] && echo "present, sha $(sha256sum "$b" | cut -c1-12), gate [$(gate_sha "$arm" "$a" | cut -c1-12)]" || echo 'to build')"
  done; done
  say "CHECK ONLY: MemAvailable $(awk '/^MemAvailable/{print int($2/1048576)}' /proc/meminfo) GB, floor $FLOOR_GB, $((2*${#SEEDS[@]})) growths at $PEAK_GB GB; seconds to deadline $(left); starts allowed now: $([ "$(date +%s)" -lt "$LS" ] && echo yes || echo no)"
  say "CHECK ONLY: nothing run, nothing written"; exit 0
fi

mkdir -p "$S/evidence/gates" "$S/scratch/identity" "$S/log"
# ---- 1. builds
for a in "${SEEDS[@]}"; do for arm in "$V" unchanged; do
  b=$(bin_of "$arm" "$a"); g=$S/evidence/gates/binary-gate-$arm-$a.csv
  if [ ! -x "$b" ] || [ -z "$(gate_sha "$arm" "$a")" ]; then
    say "build $arm $a"
    ( flock 7; DRAW_CSV=$DRAW nice -n 10 $PY "$S/tools/build_variant_seed.py" "$arm" "$S/scratch/bin-$arm" "$g" "$a" ) 7> "$S/scratch/build.lock" \
      >> "$S/log/identity-build-${arm//+/-}-$a.txt" 2>&1 || { say "build $arm $a FAILED (log/identity-build-${arm//+/-}-$a.txt)"; exit 4; }
  fi
  [ "$(sha256sum "$b" | cut -d' ' -f1)" = "$(gate_sha "$arm" "$a")" ] || { say "REFUSED: $b sha is not its gate's"; exit 4; }
  say "binary $arm $a sha $(gate_sha "$arm" "$a" | cut -c1-12) equals its gate"
done; done

# ---- 2. the jobs
job() {  # arm seed
  local arm=$1 a=$2 b O G t0 rc st n L
  b=$(bin_of "$arm" "$a"); O=$S/scratch/identity/$arm/$a; G=$O/growth; L=$S/log/identity-$arm-$a.txt
  L=${L//+/-}
  rm -rf "$O"; mkdir -p "$G/surface.bp/surface" "$G/boundary.bp/surface" "$G/patches"
  cd "$O" || return 9
  t0=$(date +%s)
  echo "$(date -u +%FT%TZ) growth starts, $(env | grep -E '^(SIMPAPER_SHARED_CHUNKS|SIMPAPER_FORCE_THREADS|OMP_WAIT_POLICY|OMP_NUM_THREADS)=' | tr '\n' ' ')" > "$L"
  SIMPAPER_OUTPUT_DIR=$G SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$G/missing.txt ZARR_CHUNK_MANIFEST=$MANIFEST \
    timeout --foreground -s TERM "$(left)" nice -n 10 "$b" g 36000 >> "$L" 2>&1; rc=$?
  echo "$(date -u +%FT%TZ) growth rc $rc in $(( $(date +%s)-t0 )) s, patches $(ls "$G/patches" | wc -l)" >> "$L"
  [ $rc -eq 0 ] || { echo "growth $rc" > "$O/RESULT"; return 0; }
  rm -rf "$O/C40"; cp -a "$G" "$O/C40" || { echo "copy failed" > "$O/RESULT"; return 0; }
  for st in "c" "l" "vm 10" "hm 10" "fm 30 10"; do
    SIMPAPER_OUTPUT_DIR=$O/C40 SIMPAPER_SURFACE_ZARR=$ZARR ZARR_MISSING_LIST=$O/C40/missing-C40.txt SIMPAPER_PATCH_LIMIT=40000 \
      timeout --foreground -s TERM "$(left)" nice -n 10 "$b" $st >> "$L" 2>&1; rc=$?
    echo "$(date -u +%FT%TZ) stage '$st' rc $rc" >> "$L"
    [ $rc -eq 0 ] || { echo "stage $st $rc" > "$O/RESULT"; return 0; }
  done
  echo "0 sheets $(ls "$O"/C40/patch_*.bin 2>/dev/null | wc -l) wall $(( $(date +%s)-t0 ))" > "$O/RESULT"
}
started=0
for a in "${SEEDS[@]}"; do for arm in "$V" unchanged; do
  while true; do
    [ "$(date +%s)" -lt "$LS" ] || { say "no start after $LAST_START: $arm $a not started"; mkdir -p "$S/scratch/identity/$arm/$a"; echo "not started" > "$S/scratch/identity/$arm/$a/RESULT"; continue 2; }
    m=$(awk '/^MemAvailable/{print int($2/1048576)}' /proc/meminfo)
    [ $(( m - PEAK_GB )) -ge "$FLOOR_GB" ] && break
    say "holding $arm $a: MemAvailable $m GB"; sleep 60
  done
  job "$arm" "$a" &
  say "started $arm $a (pid $!), MemAvailable $m GB"; started=$((started+1)); sleep 20
done; done
wait
say "all jobs ended ($started started)"

# ---- 3. comparison
ROWS=$S/evidence/identity-0826.csv
$PY - "$S" "$V" "$TI" "$STAGE_FILES" "$TOOL" "${SEEDS[@]}" <<'PY'
import csv, hashlib, os, subprocess, sys
S, V, TI, SF, TOOL = sys.argv[1:6]
seeds = sys.argv[6:]
def sha(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def res(arm, a):
    p = "%s/scratch/identity/%s/%s/RESULT" % (S, arm, a)
    return open(p).read().strip() if os.path.exists(p) else "absent"
utc = subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()
rows = []
for a in seeds:
    rv, ru = res(V, a), res("unchanged", a)
    row = dict(seed=a, variant_result=rv.replace(",", ";"), unchanged_result=ru.replace(",", ";"))
    if not (rv.startswith("0 ") and ru.startswith("0 ")):
        row.update(growth_identity="not measurable", sheets_identity="not measurable", stage_files_identity="not measurable",
                   holds="not measurable (a run did not finish: %s / %s)" % (rv.split()[0], ru.split()[0]))
        rows.append(row); continue
    du, dv = "%s/scratch/identity/unchanged/%s" % (S, a), "%s/scratch/identity/%s/%s" % (S, V, a)
    out = {}
    for kind, sub in (("growth", "growth"), ("sheets", "C40")):
        dest = "%s/evidence/identity-0826-%s-%s.csv" % (S, a, kind)
        p = subprocess.run([sys.executable, TI, "%s/%s" % (du, sub), "%s/%s" % (dv, sub), dest, kind], capture_output=True, text=True)
        out[kind] = (p.stdout.strip().splitlines() or ["no output rc %d" % p.returncode])[-1]
        out[kind + "_rc"] = p.returncode
    eq = n = 0; miss = []
    for f in SF.split():
        pu, pv = os.path.join(du, "C40", f), os.path.join(dv, "C40", f)
        if not os.path.exists(pu) and not os.path.exists(pv):
            continue
        n += 1
        if os.path.exists(pu) and os.path.exists(pv) and sha(pu) == sha(pv):
            eq += 1
        else:
            miss.append(f)
    sf = "identical %d of %d" % (eq, n) if eq == n else "differs %s" % ";".join(miss)
    ok = out["growth_rc"] == 0 and out["sheets_rc"] == 0 and eq == n and n > 0
    row.update(growth_identity=out["growth"].replace(",", ";"), sheets_identity=out["sheets"].replace(",", ";"),
               stage_files_identity=sf, holds="yes" if ok else "no")
    rows.append(row)
cols = ["seed", "variant_result", "unchanged_result", "growth_identity", "sheets_identity", "stage_files_identity", "holds"]
with open("%s/evidence/identity-0826.csv" % S, "w", newline="") as f:
    f.write('"# written by %s at %s: %s against unchanged, per seed; growth and sheets by growth-memory-1447/tools/tree_identity.py (files evidence/identity-0826-<seed>-growth.csv and -sheets.csv), stage files by sha256; DECLARATION.md addition of 2026-09-26T19:03:06Z"\n' % (TOOL, utc, V))
    w = csv.DictWriter(f, cols, lineterminator="\n"); w.writeheader(); w.writerows(rows)
holds = "yes" if rows and all(r["holds"] == "yes" for r in rows) else "no"
with open("%s/evidence/identity-0826-summary.csv" % S, "w", newline="") as f:
    f.write("# written by %s at %s: read by tools/deliver.sh (G6): first column the build, last column identity_holds\n" % (TOOL, utc))
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["build", "against", "seeds", "seeds_holding", "evidence", "identity_holds"])
    w.writerow([V, "unchanged", ";".join(seeds), sum(r["holds"] == "yes" for r in rows), "evidence/identity-0826.csv", holds])
    csv.writer(sys.stdout).writerows([[r[c] for c in cols] for r in rows])
print("identity_holds", holds)
PY
rc=$?
H=$(awk -F, -v b="$V" '$1==b {v=$NF} END {print v}' "$S/evidence/identity-0826-summary.csv")
say "summary: identity_holds $H (python rc $rc)"
$PY - "$V" "$H" "${SEEDS[*]}" "$TOOL" <<'PY'
import csv, subprocess, sys
t = subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()
with open("/data/scrollagent/ledger/ledger.csv", "a", newline="") as f:
    csv.writer(f).writerow([t, "rev1", "coordinator-agent", "chain-0826-identity-bar",
        "G6 identity bar, %s against unchanged on %s (cap 512, F3): identity_holds %s (evidence/identity-0826.csv)" % tuple(sys.argv[1:2] + sys.argv[3:4] + sys.argv[2:3]),
        sys.argv[4], "", "", "0", "runs/rev1/chain-0826/evidence/identity-0826-summary.csv"])
PY
