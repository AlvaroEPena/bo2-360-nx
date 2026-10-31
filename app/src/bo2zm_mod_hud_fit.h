// Optional client script HUD fitting. Server sources and the elements stay
// unchanged: a mod element is drawn with its view's screen placement replaced.
#pragma once
#include <cstdint>
#include <rex/ppc.h>

namespace bo2zm::mod_hud_fit {
void BeginEpoch();
// Normal server script startup completed. View observations must be freshly
// published after this boundary before a replicated copy can be fitted.
void EndMapLoad();
constexpr bool IsCopySite(uint32_t lr) {
  return lr == 0x8232CDB0 || lr == 0x8232CE8C ||
         lr == 0x8232CF68 || lr == 0x8232D044;
}
// This full playerstate copy tail-calls the shared CRT without changing LR.
constexpr bool IsUnknownPsCopySite(uint32_t lr) { return lr == 0x82439010; }
constexpr bool IsBulkPsCopySite(uint32_t lr) { return lr == 0x8230369C; }
// Diagnostic metadata publication precedes the destination becoming visible.
// Never changes either copy buffer or the guest register context.
void BeforeCopy(const PPCContext& ctx, uint8_t* base);
// Called after the existing CRT copy. Must not modify registers or invoke guest
// code; unrelated copies leave through the inexpensive caller guard.
void AfterCopy(const PPCContext& ctx, uint8_t* base);
}
