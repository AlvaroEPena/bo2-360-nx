{name}
{rule}

This kit builds bo2-360-nx, Call of Duty: Black Ops II for the Nintendo Switch and for Windows, from your own copy of
the game. It contains no game data. Everything it makes from your files stays on your PC.


What you need
-------------
Your game files:
  - Your Xbox 360 copy of Black Ops II: the disc image (.iso) or the folder extracted from it.
  - Title Update 18 (the package tu00000002_00000000). Required.
  - Your DLC packages, if you have them (optional).

A Windows PC with 16 GB of memory or more (32 GB is comfortable), about 30 GB free (less when the kit is on the same
drive as your game files), and these free tools:
  - Python 3.11 or later (python.org; while installing, tick "Add python.exe to PATH")
  - Git for Windows (git-scm.com; the build uses its bash)
  - Kitware CMake 3.25 or later (cmake.org) and Ninja (winget install Ninja-build.Ninja)
  - the Microsoft Visual C++ Redistributable (x64)
  - for the Switch: devkitPro (devkitpro.org) with the switch-dev group, switch-zlib and switch-libexpat
  - for Windows: LLVM 20 or later (winget install LLVM.LLVM) and Visual Studio's "Desktop development with C++"
    build tools

To play: a Switch that runs homebrew (custom firmware such as Atmosphere), and/or a Windows PC with a GPU that has
Vulkan 1.3.


Building
--------
1. Put your game files in the Game Files folder. Any layout works: the kit looks through every subfolder.
2. Double-click "Build bo2-360-nx.bat".
3. It lists what it found. Without Title Update 18 it stops and says so. Without DLC it asks whether to go on.
4. Choose the systems (Switch, Windows or both) and the game modes (any of Zombies, Multiplayer and Campaign). Only
   the files and shader libraries of the modes you choose are made.
5. It checks the tools above, says what is missing if anything is, and asks before it starts.

The first build takes a while: about half an hour for Zombies on one system on a 16-thread PC, more for each extra
mode and system. If it stops (or you close it), double-click the .bat again: it carries on where it stopped. The log
of every step is in build\work\logs.

With 16 GB of memory, start it from a command prompt in this folder with less parallel work:
    "Build bo2-360-nx.bat" --low-memory


What it makes
-------------
  build\switch\bo2zm\       copy this folder into the switch folder on your SD card (sdmc:/switch/bo2zm/), then
                            start bo2zm from the Homebrew Menu opened through a game (hold R while starting one) or
                            from a forwarder, so the game gets the console's full memory
  build\windows\bo2zm\      the complete Windows game, ready to play; start it with the bo2-360-nx shortcut in
                            build\windows (its README.txt lists the settings you can add to the shortcut)
  build\work\               the build's own files: keep them for a quicker rebuild, delete them when you are done

Each output folder has a short README.txt. The Windows folder plays System Link and internet games with Switch and
Windows players as it is.

Zombies and Multiplayer are one program (bo2zm), Campaign is another (bo2cp); a build with only some modes can
switch only to those in the game's menus.


Only the game files
-------------------
"Extract game files.bat" looks through the Game Files folder the same way, asks for the modes, and writes only their
game files to build\game-files\bo2zm, without building anything. Use it to add a mode's files or your DLC to an
install you already have: its README.txt says where to copy them.


Bots
----
Zombies lobbies can fill empty slots with bots when bo2zm_bots.gscpack sits next to the game. The bots pack is a
separate download, not part of this kit: put the file in Game Files and the build copies it into both output folders.


Credits and licences
--------------------
bo2-360-nx is free software under the GPL-3.0 (LICENSE). The upstream projects it builds on are listed in
THIRD_PARTY_NOTICES.md.

Disc images are read by the kit itself (tools/install/xiso.py); no other extractor is needed.
