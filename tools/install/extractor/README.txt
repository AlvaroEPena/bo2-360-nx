{name}
{rule}

This tool prepares what the prebuilt bo2-360-nx programs need from your own copy of Black Ops II: the game files and
the shader libraries. Use it when you downloaded the release's bo2zm.nro (and bo2cp.nro) or bo2zm.exe (and bo2cp.exe)
and do not want to build the game yourself. It contains no game data, and everything it makes stays on your PC.


What you need
-------------
  - Your Xbox 360 copy of Black Ops II: the disc image (.iso) or the folder extracted from it.
  - Title Update 18 (the package tu00000002_00000000). Required.
  - Your DLC packages, if you have them (optional).
  - A Windows PC with Python 3.8 or later (python.org; while installing, tick "Add python.exe to PATH") and the
    Microsoft Visual C++ Redistributable (x64).
  - Free space: about as much as the game files of your modes (much less when this tool is on the same drive as
    your game files), plus about 8 GB while the shaders are made.


How to use it
-------------
1. Put your game files in the Game Files folder. Any layout works: the tool looks through every subfolder.
2. Double-click "Extract game files and shaders.bat".
3. It lists what it found. Without Title Update 18 it stops and says so. Without DLC it asks whether to go on.
4. Choose what to make: the game files, the shaders, or both.
5. Choose the game modes: any of Zombies, Multiplayer and Campaign. Only the files and shaders of those modes are
   made. Zombies and Multiplayer share one shader library (bo2zm_shaders), Campaign has its own (bo2cp_shaders).

The game files take a few minutes. The shaders take longer on a 16-thread PC: about 10 minutes for Zombies and
Multiplayer, about 20 minutes with all their DLC, and about 20 minutes for Campaign. If it stops (or you close it), double-click
the .bat again: it carries on where it stopped. The log of every step is in work\logs.


What it makes
-------------
  output\bo2zm\        the files to copy next to the release's programs
  output\README.txt    where to copy them, with a picture of the finished folder

Switch: copy output\bo2zm into the switch folder on your SD card and merge it with the bo2zm folder from the
release (sdmc:/switch/bo2zm/). Windows: copy what is inside output\bo2zm into the folder with bo2zm.exe.

The work folder holds the tool's own files: keep it for a quicker run with other choices, or delete it.


Credits and licences
--------------------
bo2-360-nx is free software under the GPL-3.0 (LICENSE). The upstream projects it builds on are listed in
THIRD_PARTY_NOTICES.md; the shader compiler's licence is in runtime\licenses.
