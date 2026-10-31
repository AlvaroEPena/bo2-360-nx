"""Starts the bo2-360-nx build kit ("Build bo2-360-nx.bat" runs this). Options: source/tools/install/kit_build.py."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if sys.version_info < (3, 11):
    sys.exit(f"Python 3.11 or later is needed (this is {sys.version.split()[0]}): python.org")
sys.path.insert(0, os.path.join(HERE, "source", "tools", "install"))
import kit_build  # noqa: E402

try:
    sys.exit(kit_build.main(sys.argv[1:] + ["--kit", HERE]))
except KeyboardInterrupt:
    print("\nStopped. Run the kit again to carry on where it stopped.")
    sys.exit(1)
