#!/usr/bin/env bash
# Builds the Mesa/NVK Vulkan driver for the Switch (static libvulkan.a SDK):
# danfromtico/mesa-switch at 1a8c1a66d6f (the official base) plus this project's
# changes in patches/mesa-bo2zm.patch.
#
# Needs:
#   - MSYS2 at C:\msys64 with the clang64 packages (clang, llvm, lld,
#     spirv-llvm-translator, libclc, spirv-tools/headers, meson, ninja, python
#     + mako/yaml/packaging, pkgconf, cmake, cbindgen, rust-bindgen) and
#     bison, flex, git
#   - a junction C:\msys64\opt\devkitpro -> C:\devkitPro (the build files
#     hard-code that path), devkitA64 + libnx + switch-zlib + switch-libexpat
#   - rustup toolchain stable-x86_64-pc-windows-gnu with target
#     aarch64-unknown-linux-gnu
#
# Run from Git Bash: tools/build_mesa.sh   (writes $MESA_DIR/mesa-unified-install,
# default mesa/ in the data folder, tools/data_dir.sh; the path must have no spaces)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Outside the project: its path must not contain spaces (the bindgen wrapper
# passes clang flags through an environment variable split on spaces).
MESA="${MESA_DIR:-$(bash "$ROOT/tools/data_dir.sh")/mesa}"
. "$ROOT/tools/toolchain.sh"  # BO2_MSYS2_DIR
PATCH="$ROOT/patches/mesa-bo2zm.patch"

if [ ! -d "$MESA" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/danfromtico/mesa-switch.git "$MESA"
  git -C "$MESA" -c core.symlinks=false checkout 1a8c1a66d6f
fi
if git -C "$MESA" apply --check "$PATCH" 2>/dev/null; then
  git -C "$MESA" apply "$PATCH"
elif ! git -C "$MESA" apply --check -R "$PATCH" 2>/dev/null; then
  echo "patches/mesa-bo2zm.patch neither applies nor is already applied to $MESA" >&2
  exit 1
fi

MESA_W="$(cygpath -u "$MESA")"
RUSTC_W="$(cygpath -u "$USERPROFILE")/.cargo/bin/rustc.exe"

# build-unified.sh only runs inside an MSYS2 shell (MSYSTEM set).
# --resume: continue an interrupted build (ninja + install) instead of
# build-unified.sh, which wipes builddir-unified on every run.
INNER="./build-unified.sh"
if [ "${1:-}" = "--resume" ]; then
  INNER="ninja -C builddir-unified && meson install -C builddir-unified --destdir \"\$PWD/mesa-unified-install\" --only-changed"
fi

# USERPROFILE must be passed through: the MSYS2 login shell drops it, and
# Windows Python (which runs Meson) only finds the home folder through it
# ("Could not determine home directory" in Meson's cmake lookups).
"$BO2_MSYS2_DIR/usr/bin/env" MSYSTEM=CLANG64 CHERE_INVOKING=1 \
  USERPROFILE="$(cygpath -w "$USERPROFILE")" \
  DEVKITPRO=/opt/devkitpro \
  MESA_SWITCH_RUST_TARGET=aarch64-unknown-linux-gnu \
  ALLOW_DIRTY=1 \
  NATIVE_FILE="$(cygpath -m "$ROOT/tools/mesa/switch_native_tools_msys2.txt")" \
  RUSTUP_TOOLCHAIN=stable-x86_64-pc-windows-gnu \
  RUSTUP_HOME="$(cygpath -m "$USERPROFILE")/.rustup" \
  CARGO_HOME="$(cygpath -m "$USERPROFILE")/.cargo" \
  MESA_SWITCH_RUSTC="$RUSTC_W" \
  MESA_SWITCH_NATIVE_RUSTC="$RUSTC_W" \
  MESA_SWITCH_BINDGEN=/clang64/bin/bindgen.exe \
  "$BO2_MSYS2_DIR/usr/bin/bash.exe" -lc "cd '$MESA_W' && $INNER"

echo
echo "Vulkan SDK: $MESA/mesa-unified-install/opt/devkitpro/portlibs/switch"
find "$MESA/mesa-unified-install" -name "libvulkan.a" -exec ls -la {} \;
