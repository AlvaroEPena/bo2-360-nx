"""Starts the bo2-360-nx game files extractor ("Extract game files.bat" runs this). Options:
source/tools/install/extract_game_files.py."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "source", "tools", "install"))
import extract_game_files  # noqa: E402

try:
    sys.exit(extract_game_files.main(sys.argv[1:] + ["--kit", HERE]))
except KeyboardInterrupt:
    print("\nStopped. Run it again to carry on where it stopped.")
    sys.exit(1)
