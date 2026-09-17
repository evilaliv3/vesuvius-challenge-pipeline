#!/bin/bash
# This file is a copy of the same script in the working tree and differs from it in one way only:
# the absolute paths of the machine the measurements ran on are replaced by paths inside
# this folder, resolved from the file's own location. Nothing else is changed.
# Compile villa's own core/src/normalgridtools.cpp and run align_and_extract_umbilicus on a
# published grid, without building volume-cartographer.
#
# The source file is used unmodified. It needs four things from GridStore (get_all, add, size,
# meta), which stub/ provides, and real OpenCV, which is fetched as .deb packages and unpacked
# locally: no root, about 90 MB, a minute.
set -eu
VILLA=${VILLA:?set VILLA to the volume-cartographer folder of a clone of ScrollPrize/villa}
OCV=${OCV:-${TMPDIR:-/tmp}/ocv/root}
L=$OCV/usr/lib/x86_64-linux-gnu

if [ ! -d "$OCV" ]; then
  mkdir -p "$(dirname "$OCV")" && cd "$(dirname "$OCV")"
  apt-get download libopencv-core-dev libopencv-core410 libopencv-imgproc-dev \
                   libopencv-imgproc410 libopencv-imgcodecs-dev libopencv-imgcodecs410 \
                   libopenblas0-pthread libtbb12 libtbbbind-2-5 libtbbmalloc2 libgfortran5
  for d in *.deb; do dpkg -x "$d" "$(basename "$OCV")/"; done
fi

cd "$(dirname "$0")"
for tgt in driver degenerate; do
  g++ -std=c++20 -O2 -w -o "$tgt" "$tgt.cpp" \
    "$VILLA/core/src/normalgridtools.cpp" \
    -I stub -I "$VILLA/core/include" -I "$OCV/usr/include/opencv4" \
    -L "$L" -L "$L/openblas-pthread" \
    -lopencv_core -lopencv_imgproc -lopencv_imgcodecs \
    -Wl,-rpath,"$L" -Wl,-rpath,"$L/openblas-pthread"
done
echo "built: ./degenerate (villa's own two assertions), ./driver <dump> [repeats]"
