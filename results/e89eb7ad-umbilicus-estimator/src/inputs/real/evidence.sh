#!/bin/bash
# This file is a copy of the same script in the working tree and differs from it in one way only:
# the absolute paths of the machine the measurements ran on are replaced by paths inside
# this folder, resolved from the file's own location, and the report it names is named as it
# is named here. Nothing else is changed.
# One saved run of villa's own compiled code, before and after the one line, so that the pull
# request page and the paper quote the same figures.
#
# Why this exists: on 2026-09-15 result-d-one-division.md and the draft of the pull request
# page printed different coordinates for the same slice, because each quoted a different run
# of the same binary. The C++ hill climb seeds itself from an unseeded generator, so two runs
# differ by construction. From here on the numbers come from these files and from nowhere else.
#
# Repeats and dumps are fixed here, before the run: 20 repeats, the same four dumps as before.
set -eu
cd "$(dirname "$0")"
REPEATS=${REPEATS:-20}
# RUNPATH on the executable is not searched for the dependencies of a shared library, so OpenCV's
# own libopenblas and libtbb are only found through LD_LIBRARY_PATH. This changes where libraries
# are looked up and nothing about the code being measured.
OCV=${OCV:-${TMPDIR:-/tmp}/ocv/root}
L=$OCV/usr/lib/x86_64-linux-gnu
export LD_LIBRARY_PATH="$L:$L/openblas-pthread${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
OUT=evidence
mkdir -p "$OUT"

for dump in d-0125-2140 d-0125-6891 d-0332-4049 d-0826-8000; do
  for pair in "as-is:./driver" "no-division:./driver_pr"; do
    name=${pair%%:*}; bin=${pair##*:}
    f="$OUT/$name-$dump.txt"
    echo "== $name $dump -> $f"
    { echo "# binary $bin, dump $dump.bin, $REPEATS repeats, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      "$bin" "$dump.bin" "$REPEATS"; } > "$f"
  done
done
echo "written to $OUT/"
