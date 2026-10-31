// Force-included after pch_min.h: XenosRecomp's assert() throws instead of
// aborting, so one bad shader is reported in translate.tsv and the run goes on
// (a failed assert on Windows also opens a dialog box).
#pragma once
#include <stdexcept>
#undef assert
#define assert(expr) ((expr) ? (void)0 : throw std::runtime_error("assert failed: " #expr))
