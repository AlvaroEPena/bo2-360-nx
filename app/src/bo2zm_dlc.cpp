// DLC map packs: no NEW badge on the Zombies globe.
//
// The globe and start-location menus (Lua in the title update's patch_ui_zm.ff: SeenStartMap, SeenStartLocation,
// SeenGameModeMap, SawGameModeMap in SelectStartLocZombie) keep one bit per map, start location and mode in the
// profile setting unlock_crumbs_zm, and draw a NEW icon for every combination whose bit is clear; opening one sets its
// bit. Installed DLC maps (tools/install_dlc.py) therefore all start as NEW. Measured on the PC: with the setting at
// 16777215 (24 bits set) no map on the globe shows NEW, so every combination's bit is below bit 24.
//
// The profile setter behind the game's "setprofile" console command does nothing until that controller's profile is
// loaded: it first checks a byte at 0x836BAE58 + 2000 + controller * 2008 (one 2008-byte block per controller). So the
// per-frame hook watches that byte and, each time a profile finishes loading, runs "setprofile unlock_crumbs_zm
// 16777215" for that controller with the game's own text runner.

#include "bo2zm_dlc.h"

#include <cstring>

#include <rex/cvar.h>
#include <rex/logging.h>

#include "bo2zm_autoexec.h"

REXCVAR_DEFINE_BOOL(bo2zm_dlc_maps_seen, true, "BO2",
                    "Marks every Zombies map, start location and mode as already seen in each profile when it loads, "
                    "so installed DLC maps show no NEW badge on the globe");

namespace {

constexpr uint32_t kProfileBlocks = 0x836BAE58;
constexpr uint32_t kProfileBlockSize = 2008;
constexpr uint32_t kProfileLoaded = 2000;  // byte: the profile of that controller is loaded
constexpr int kControllers = 4;
constexpr const char* kAllSeen = "setprofile unlock_crumbs_zm 16777215";

bool g_applied[kControllers] = {};

}  // namespace

void bo2zm::dlc::EveryFrame(PPCContext& ctx, uint8_t* base) {
  if (!REXCVAR_GET(bo2zm_dlc_maps_seen)) [[unlikely]] {
    return;
  }
  for (int controller = 0; controller < kControllers; ++controller) {
    const bool loaded =
        base[kProfileBlocks + uint32_t(controller) * kProfileBlockSize + kProfileLoaded] != 0;
    if (!loaded) {
      g_applied[controller] = false;  // signed out or not loaded yet: apply again on the next load
      continue;
    }
    if (g_applied[controller]) [[likely]] {
      continue;
    }
    g_applied[controller] = true;
    REXLOG_INFO("[dlc] profile of controller {} loaded: every Zombies map marked as seen (no NEW badges)", controller);
    bo2zm::autoexec::ExecuteCommands(ctx, base, kAllSeen, controller);
  }
}
