#!/bin/sh
# Starts bo2zm from its folder with the native Vulkan renderer. Extra arguments go to the game
# (e.g. ./bo2zm.sh --fullscreen=false). See README.txt for what goes next to this script.
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here" || exit 1

missing=""
[ -f game/default_mp.xex ] || missing="$missing game/default_mp.xex"
[ -d update ] || missing="$missing update/"
[ -f bo2zm_shaders.spvpack ] || missing="$missing bo2zm_shaders.spvpack"
if [ -n "$missing" ]; then
  echo "bo2zm: missing next to this script:$missing (see README.txt)" >&2
  exit 1
fi
if ! ldconfig -p 2>/dev/null | grep -q 'libvulkan\.so\.1'; then
  echo "bo2zm: libvulkan.so.1 not found: install your distribution's Vulkan loader (e.g. libvulkan1) and driver" >&2
fi

# An option the game is given twice makes it ignore all of them, so the defaults below only apply when the command
# line does not set them itself.
renderer="--bo2zm_renderer=native"
own_user=""
for a in "$@"; do
  case "$a" in
    --bo2zm_renderer=*) renderer="" ;;
    --user_data_root=*) own_user=1 ;;
  esac
done
# Saves, the profile, caches and the DLC packs (user/0000000000000000/): a user/ folder next to this script when there
# is one, as on the Switch; otherwise $XDG_DATA_HOME/bo2zm (usually ~/.local/share/bo2zm).
if [ -d user ] && [ -z "$own_user" ]; then
  set -- "--user_data_root=$here/user" "$@"
fi
exec ./bo2zm $renderer "$@"
