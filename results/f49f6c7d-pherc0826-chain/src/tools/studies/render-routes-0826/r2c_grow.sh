#!/bin/bash
# render-routes-0826 R2c (copy of tools/r2b_grow.sh, two starts, generations 200; params with normal_grid_path = scratch/normal-grids, sparse 2): the organisers' tracer from the ten starts of evidence/r2-starts.csv.
# One core per run, nice 10, at most MAXJ at once; a start waits while load > 22, MemAvailable < 30 GB or /data free < 36 GB.
#   setsid nohup bash tools/r2c_grow.sh > log/r2c_grow.txt 2>&1 < /dev/null &
set -u
S=/data/scrollagent/runs/rev1/render-routes-0826
BIN=/data/scrollagent/runs/rev1/villa-tracer-build/scratch/build/bin/vc_grow_seg_from_seed
VOL=/data/scrollagent/data/datasets/PHerc0826
PAR=$S/scratch/r2c/params.json
PY=/data/scrollagent/.venv/bin/python
OUT=$S/evidence/r2c-runs.csv
MAXJ=${MAXJ:-5}
export VC_GROWPATCH_RNG_SEED=20260923 TMPDIR=/data/tmp OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
say() { echo "$(date -u +%FT%TZ) $*"; }
[ "$(sha256sum $BIN | cut -c1-16)" = 53fbaa948f7abeca ] || { say "binary sha differs"; exit 1; }
if [ ! -s "$OUT" ]; then
  echo '"# every R2c tracer run (headline follow up, addition 11:54Z), written by render-routes-0826/tools/r2c_grow.sh: binary villa-tracer-build/scratch/build/bin/vc_grow_seg_from_seed (sha256 head 53fbaa948f7abeca), params scratch/r2c/params.json (generations 200 by the addition of 11:54Z, step_size 20, thread_limit 1, voxelsize 9.362, no reference_surface; normal_grid_path scratch/normal-grids at sparse 2), -v data/datasets/PHerc0826 (m7 prediction), VC_GROWPATCH_RNG_SEED 20260923, timeout 10800 s; mode, max_gen, area_cm2 from meta.json; cells = valid x.tif nodes; declared target area 20 cm2"' > $OUT
  echo 'utc,start,x,y,z,rc,wall_s,mode,max_gen,area_cm2,target_area_cm2,cells,x_tif_sha256_head,surface' >> $OUT
fi
declare -A J=()
reap() { while [ "${#J[@]}" -ge "$1" ]; do for p in "${!J[@]}"; do kill -0 $p 2>/dev/null || { wait $p; unset "J[$p]"; }; done; [ "${#J[@]}" -ge "$1" ] && sleep 15; done; }
room() { while :; do
  l=$(awk '{print int($1)}' /proc/loadavg); m=$(awk '/MemAvailable/ {print int($2/1048576)}' /proc/meminfo); f=$(df -B1G --output=avail /data | tail -1 | tr -d ' ')
  [ "$l" -le 22 ] && [ "$m" -ge 30 ] && [ "$f" -ge 36 ] && return 0; sleep 30; done; }
tail -n +3 $S/evidence/r2-starts.csv | grep -E "^PHerc0826-seed(6273|5364)-squarecentre," | while IFS=, read -r name seed kind x y z rest; do echo "$name $x $y $z"; done > $S/scratch/r2c/starts.txt
while read -r name x y z; do
  [ -e $S/scratch/r2c/$name.done ] && continue
  reap $MAXJ; room
  (
    o=$S/scratch/r2c/$name; rm -rf $o; mkdir -p $o
    t0=$(date +%s)
    nice -n 10 timeout 10800 $BIN -v $VOL -t $o -p $PAR -s $x $y $z > $o.log 2>&1; rc=$?
    t1=$(date +%s)
    xt=$(find $o -name x.tif | head -1); mode=""; mg="not measurable"; ar="not measurable"; cells=""; sh=none; surf=none
    if [ -n "$xt" ]; then
      sh=$(sha256sum $xt | cut -c1-16); surf=$(dirname $xt); surf=${surf#$S/}
      read mode mg ar cells < <($PY - "$xt" <<'PY'
import json, os, sys, tifffile
a = tifffile.imread(sys.argv[1]); j = json.load(open(os.path.join(os.path.dirname(sys.argv[1]), "meta.json")))
print(j.get("vc_gsfs_mode", "absent"), j.get("max_gen", "not measurable"), "%.4f" % j["area_cm2"] if "area_cm2" in j else "not measurable", int((a != -1).sum()))
PY
)
    fi
    ( flock 9; echo "$(date -u +%FT%TZ),$name,$x,$y,$z,$rc,$((t1-t0)),$mode,$mg,$ar,20,$cells,$sh,$surf" >> $OUT ) 9>$OUT.lock
    echo $rc > $o.done
    say "end $name rc=$rc area=$ar gen=$mg"
  ) &
  J[$!]=$name; say "start $name ($x $y $z) pid $!"
done < $S/scratch/r2c/starts.txt
reap 1
say "all R2c runs ended"
