#!/usr/bin/env bash
# Builds a static libzstd.a for the Switch and installs it into the Mesa SDK
# folder: the ReXGlue SDK's Switch link line (rexglue_switch.cmake, rex::nvk)
# links "zstd", and devkitPro has no switch-zstd package.
# Run after tools/build_mesa.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${ZSTD_DIR:-$(bash "$ROOT/tools/data_dir.sh")/zstd}"
# CMake, Ninja, devkitPro and the Mesa SDK (MESA_SDK), from tools/toolchain.sh.
. "$ROOT/tools/toolchain.sh"

[ -d "$SRC" ] || git clone --depth 1 -b v1.5.7 https://github.com/facebook/zstd.git "$SRC"

# The cross toolchain file limits program lookups to the target sysroot, so
# CMake would not find Ninja on PATH: it is named explicitly (NINJA_EXE).
cmake -S "$SRC/build/cmake" -B "$SRC/out-switch" -G Ninja "-DCMAKE_MAKE_PROGRAM=$NINJA_EXE" \
  -DCMAKE_TOOLCHAIN_FILE="$ROOT/tools/switch/cmake/switch-devkitA64.cmake" \
  -DCMAKE_BUILD_TYPE=Release \
  -DZSTD_BUILD_SHARED=OFF -DZSTD_BUILD_STATIC=ON \
  -DZSTD_BUILD_PROGRAMS=OFF -DZSTD_BUILD_TESTS=OFF \
  -DZSTD_MULTITHREAD_SUPPORT=OFF -DZSTD_LEGACY_SUPPORT=OFF
cmake --build "$SRC/out-switch" --target libzstd_static

cp "$SRC/out-switch/lib/libzstd.a" "$MESA_SDK/lib/libzstd.a"
cp "$SRC/lib/zstd.h" "$SRC/lib/zstd_errors.h" "$SRC/lib/zdict.h" "$MESA_SDK/include/"
ls -la "$MESA_SDK/lib/libzstd.a"
