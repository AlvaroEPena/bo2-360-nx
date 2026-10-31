#!/usr/bin/env bash
# Prints the data folder every script and tool shares: the game files, the consoles' delivery state, PGO profiles, logs and
# icons. It is $BO2_DATA when that is set, else the path written in bo2_data.txt at the repository's root (one line,
# git-ignored, so each machine keeps its own), else the data/ folder at the root (also git-ignored).
#
#   DATA="$(bash tools/data_dir.sh)"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -n "${BO2_DATA:-}" ]; then
  echo "$BO2_DATA"
elif [ -s "$ROOT/bo2_data.txt" ]; then
  tr -d '\r\n' < "$ROOT/bo2_data.txt"
  echo
else
  echo "$ROOT/data"
fi
