#pragma once

#include <filesystem>

namespace bo2cp {

void ApplyPendingRelaunch(const std::filesystem::path& user_dir);
void StartWatchdog(const std::filesystem::path& logs_dir);

// Worker-safe request only. Pump RestartForScriptChanges from main EveryFrame.
void RequestRestart();
// Handles a queued request on the main thread through the existing relaunch path.
// Returns false when idle or if preserving launch data failed; success exits.
bool RestartForScriptChanges();

}  // namespace bo2cp
