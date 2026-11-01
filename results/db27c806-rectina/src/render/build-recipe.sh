#!/bin/bash
# Build recipe of the renderer that rendered the Rectina stacks (tier: villa upstream main a4979b990 plus patches/pas-p1bcpp.patch, stock flags).
# This file documents the build. It was not re-run for this release; see README.md, section "What was and was not tested".
# Needs: git, cmake, a C++ toolchain, the system libraries that villa's volume-cartographer needs, and read access to the two dependency sources
# pinned below. Replace WORK with an empty folder. Build time on 6 jobs: 82 s on the first build, 1393 s on the 2026-10-28 rebuild.
set -euo pipefail
WORK=${WORK:?set WORK to an empty folder}
COMMIT=a4979b99004934955784ea19b30da66cfe5f9ead
PATCH_SHA=6138aebd6b794a6f40710a562d10b148dd6c52cc20c23316300abd1db615c9db
HERE=$(cd "$(dirname "$0")" && pwd)
SRC=$WORK/villa-src; B=$WORK/build; DEPS=$WORK/deps; JOBS=${JOBS:-6}
git clone https://github.com/ScrollPrize/villa "$SRC"
git -C "$SRC" checkout --detach $COMMIT
[ "$(sha256sum "$HERE/pas-p1bcpp.patch" | cut -c1-64)" = $PATCH_SHA ] || { echo "patch sha differs"; exit 2; }
git -C "$SRC" apply "$HERE/pas-p1bcpp.patch"
[ "$(git -C "$SRC" diff | sha256sum | cut -c1-64)" = $PATCH_SHA ] || { echo "the tree's diff is not the patch"; exit 2; }
[ "$(git -C "$SRC" status --porcelain | wc -l)" = 7 ] || { echo "not exactly 7 patched files"; exit 2; }
mkdir -p "$DEPS"
git clone https://github.com/ScrollPrize/vc-delta3d.git "$DEPS/vc_delta3d-src"; git -C "$DEPS/vc_delta3d-src" checkout --detach eedd0e62d988bcf97fbaee4ebb7af026f52ca49a
git clone https://github.com/libigl/libigl.git "$DEPS/libigl-src"; git -C "$DEPS/libigl-src" checkout --detach ae8f959ea26d7059abad4c698aba8d6b7c3205e8
mkdir -p "$B"
nice -n 10 cmake -S $SRC/volume-cartographer -B $B -G "Unix Makefiles" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS= -DCMAKE_CXX_FLAGS= \
  -DVC_GIT_SHA1=$COMMIT -DVC_GIT_COMMIT_DATE=2026-10-13 \
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DFETCHCONTENT_SOURCE_DIR_VC_DELTA3D=$DEPS/vc_delta3d-src -DFETCHCONTENT_SOURCE_DIR_LIBIGL=$DEPS/libigl-src \
  -DVC_BUILD_APPS=ON -DVC_BUILD_FLATBOI=OFF -DVC_BUILD_PYTHON=OFF -DVC_BUILD_UI_TRACER=ON \
  -DVC_CCACHE_PCH_SLOPPINESS=pch_defines,time_macros -DVC_DEAD_CODE_REPORT=OFF -DVC_ENABLE_AMGX=OFF \
  -DVC_ENABLE_ASAN=OFF -DVC_ENABLE_COVERAGE=OFF -DVC_ENABLE_ECL_MAXFLOW=OFF -DVC_ENABLE_LSAN=OFF \
  -DVC_ENABLE_NSAN=OFF -DVC_ENABLE_TSAN=OFF -DVC_ENABLE_TYSAN=OFF -DVC_ENABLE_UBSAN=OFF \
  -DVC_LIBBACKTRACE_UPDATE_DISCONNECTED=ON -DVC_MARCH_NATIVE=OFF -DVC_PROFILE_COMPILE=OFF \
  -DVC_QUICKBUILD_OPT_LEVEL=1 -DVC_RUN_RENDER_BENCHMARKS=OFF -DVC_TESTING=OFF -DVC_USE_CCACHE=OFF \
  -DVC_USE_PCH=OFF -DVC_USE_SCCACHE=OFF -DVC_USE_SYSTEM_LIBBACKTRACE=ON -DVC_WARNINGS=OFF -DVC_WERROR=OFF
nice -n 10 cmake --build $B --target vc_render_tifxyz -j $JOBS
$B/bin/vc_render_tifxyz --help | head -1   # expected: vc_render_tifxyz: Render volume data using segmentation surfaces
sha256sum $B/bin/vc_render_tifxyz           # differs between builds (see PINS.csv); the rendered output is what was compared
