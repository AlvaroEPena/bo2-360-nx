"""Starts the bo2-360-nx game files and shader extractor ("Extract game files and shaders.bat" runs this). Options:
source/tools/install/gamefiles_shader_extractor.py."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if sys.version_info < (3, 8):
    sys.exit(f"Python 3.8 or later is needed (this is {sys.version.split()[0]}): python.org")
sys.path.insert(0, os.path.join(HERE, "source", "tools", "install"))
import gamefiles_shader_extractor  # noqa: E402

try:
    sys.exit(gamefiles_shader_extractor.main(sys.argv[1:] + ["--tool", HERE]))
except KeyboardInterrupt:
    print("\nStopped. Run it again to carry on where it stopped.")
    sys.exit(1)
