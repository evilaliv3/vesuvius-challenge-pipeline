#!/bin/bash
# Build core/test/test_normalgridtools from the villa commit named in src/COMMIT (dec288ff4 on
# 2026-09-17, 7a4129a1d after the rebase of 2026-09-18) without CMake, Qt or the rest
# of volume-cartographer: the test, the two source files under test (normalgridtools.cpp and the
# real GridStore.cpp with MemMap.cpp and utils/Json.cpp behind it), the in-tree doctest shim
# (core/test/vc_test.hpp via doctest_compat/), and OpenCV 4.10.0 from the Ubuntu packages
# unpacked without root under /data/tmp/ocv/root, plus nlohmann/json.hpp 3.11.3 copied out of the
# volume-cartographer:edge docker image into third_party/. Nothing from the tree is modified.
set -eu
W=$(cd "$(dirname "$0")" && pwd)
S=$W/src/volume-cartographer
OCV=${OCV:-/data/tmp/ocv/root}
L=$OCV/usr/lib/x86_64-linux-gnu
B=$W/build
mkdir -p "$B"
CXX=${CXX:-g++}
FLAGS="-std=c++23 -O2 -Wno-deprecated-enum-enum-conversion -DVC_TEST_FIXTURES_DIR=\"$S/core/test/data\" \
  -I $S/core/include -I $S/utils/include -I $S/core/test -I $S/core/test/doctest_compat \
  -I $W/third_party -I $OCV/usr/include/opencv4"
SRCS="core/test/test_normalgridtools.cpp core/src/normalgridtools.cpp core/src/GridStore.cpp core/src/MemMap.cpp utils/src/Json.cpp"
printf '%s\n' $SRCS | xargs -P 4 -I{} sh -c "$CXX $FLAGS -c $S/{} -o $B/\$(basename {} .cpp).o"
$CXX -o "$B/test_normalgridtools" "$B"/*.o -L "$L" -L "$L/openblas-pthread" \
  -lopencv_core -lopencv_imgproc -Wl,--disable-new-dtags -Wl,-rpath,"$L" -Wl,-rpath,"$L/openblas-pthread"
echo "built $B/test_normalgridtools"
