#!/bin/bash
# Compile vc_gen_umbilicus without building the whole of volume-cartographer.
#
# This is runs/umbilicus-driver/build.sh of the working tree with its four absolute paths turned
# into environment variables, each with the meaning it had there, and the binaries written under
# this folder's build/. Nothing that compiles is changed.
#
# The tool, driver/vc_gen_umbilicus.cpp, and core/src/normalgridtools.cpp of the patch are compiled
# from source; everything else they need (GridStore, NormalGridVolume, utils::Json) comes from
# libvc_core.so of the official VC3D build, extracted from its AppImage. The headers come from a
# checkout of volume-cartographer that carries the patch, and OpenCV and Boost from their
# development packages, unpacked anywhere: no root is needed.
#
# Our own normalgridtools.o defines align_and_extract_umbilicus with the seed argument, a symbol
# libvc_core.so does not have, and interposes the other symbols of that file, which are identical
# to the library's apart from the one line under test.
#
#   ./build.sh                 the patch as it stands: the weighted sum
#   VARIANT=as-is ./build.sh   the same source with the division restored: the published objective
#   VARIANT=p0.5 ./build.sh    the weighted sum with the weight raised to that exponent
#
# The exponent variants are OUR objective and not upstream's: nothing shipped has an exponent, the
# weight at normalgridtools.cpp:112 is written 1.0f / std::max(100.0f, dist). They exist so that
# the exponent table and the tables beside it are read by one instrument. Every substitution is
# anchored on an exact line of the patch and the build FAILS if an anchor does not match once,
# because a binary built from an anchor that slipped is a binary nobody can characterise.
#
# What must be named, and what each is:
#   VILLA_FORK   a checkout of volume-cartographer with the patch applied: the fork's branch
#                normalgrid-umbilicus-score-not-normalised, or ScrollPrize/villa at 2dcfaf6a0
#                with patch/0001-normalgridtools-weighted-sum.patch applied by git am. Read for
#                core/src/normalgridtools.cpp and the headers under core/include and utils/include.
#   VC3D_ROOT    the extracted AppImage of the official VC3D build (squashfs-root), read for
#                usr/lib/libvc_core.so and libutils.so. Not in this repository: it is the
#                project's own binary release, which tools/vcx.sh of the working tree runs.
#   OCV_ROOT     a tree holding usr/include/opencv4 and usr/lib/x86_64-linux-gnu of OpenCV 4
#   BOOST_ROOT   a tree holding usr/include/boost and usr/lib/x86_64-linux-gnu of Boost
set -eu

: "${VILLA_FORK:?point VILLA_FORK at a checkout of volume-cartographer that carries the patch}"
: "${VC3D_ROOT:?point VC3D_ROOT at the extracted AppImage of the official VC3D build}"
OCV=${OCV_ROOT:?point OCV_ROOT at a tree with usr/include/opencv4}
BOOST=${BOOST_ROOT:?point BOOST_ROOT at a tree with usr/include/boost}
BRANCH=$VILLA_FORK
case "$BRANCH" in */volume-cartographer) ;; *) [ -d "$BRANCH/volume-cartographer" ] && BRANCH=$BRANCH/volume-cartographer ;; esac
VARIANT=${VARIANT:-no-division}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(dirname "$HERE")/build/driver
mkdir -p "$OUT"

OCVLIB=$OCV/usr/lib/x86_64-linux-gnu
VCLIB=$VC3D_ROOT/usr/lib
SRC=$OUT/normalgridtools-$VARIANT.cpp
cp "$BRANCH/core/src/normalgridtools.cpp" "$SRC"
case "$VARIANT" in p[0-9]*)
  P=${VARIANT#p}
  python3 - "$SRC" "$P" <<'PY'
import sys
path, p = sys.argv[1], sys.argv[2]
s = open(path).read()
anchor = "            float weight = 1.0f / std::max(100.0f, dist);\n"
assert s.count(anchor) == 1, "anchor for the weight not found exactly once"
s = s.replace(anchor,
              "            float weight = 1.0f / std::pow(std::max(100.0f, dist), %sf);\n" % p, 1)
inc = "#include <random>\n"
assert s.count(inc) == 1, "anchor for the includes not found exactly once"
s = s.replace(inc, inc + "#include <cmath>\n", 1)
open(path, "w").write(s)
print("exponent %s: the weight is raised to it" % p)
PY
  ;;
esac

if [ "$VARIANT" = "as-is" ]; then
  # Put back the two lines the patch removes, so that both objectives are compiled from one
  # source and differ by nothing else. The markers are the exact lines of the branch.
  python3 - "$SRC" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
a = "        double score = 0.0;\n        for (size_t j = 0; j < sample_points.size(); ++j) {\n            const auto& point = sample_points[j];\n            const auto& normal = sample_normals[j];\n\n            cv::Vec2f umbilicus_to_segment = cv::Vec2f(point) - candidate;"
assert s.count(a) == 1, "anchor for the score body not found once"
s = s.replace(a, a.replace("double score = 0.0;", "double score = 0.0;\n        double wsum = 0.0;"), 1)
b = "            score += (cos_angle * cos_angle) * weight;\n"
assert s.count(b) == 1, "anchor for the accumulation not found once"
s = s.replace(b, b + "            wsum += weight;\n", 1)
c = "        return score;\n    };"
assert s.count(c) == 1, "anchor for the return not found once"
s = s.replace(c, "        return score/wsum;\n    };", 1)
open(p, "w").write(s)
print("as-is: division restored")
PY
fi

g++ -std=c++20 -O2 -w -o "$OUT/vc_gen_umbilicus-$VARIANT" \
  "$HERE/vc_gen_umbilicus.cpp" "$SRC" \
  -I "$BRANCH/core/include" -I "$BRANCH/utils/include" \
  -I "$OCV/usr/include/opencv4" -I "$BOOST/usr/include" \
  -L "$VCLIB" -L "$BOOST/usr/lib/x86_64-linux-gnu" -L "$OCVLIB" -L "$OCVLIB/openblas-pthread" \
  -lvc_core -lutils -lboost_program_options -lopencv_core -lopencv_imgproc -lopencv_imgcodecs \
  -Wl,-rpath,"$VCLIB" -Wl,-rpath,"$OCVLIB" -Wl,-rpath,"$OCVLIB/openblas-pthread" \
  -pthread

echo "built $OUT/vc_gen_umbilicus-$VARIANT"
