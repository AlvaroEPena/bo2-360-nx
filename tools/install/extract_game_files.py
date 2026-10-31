"""The kit's game files extractor: lays out your own game files for bo2-360-nx without building anything.

The kit's "Extract game files.bat" runs it (through extract.py at the kit's root). It looks through the kit's Game
Files folder exactly as the build does, asks which game modes you want, and writes only those modes' files:

  build/game-files/bo2zm/game/      the disc's files, plus Title Update 18's executable patches
  build/game-files/bo2zm/update/    the rest of Title Update 18
  build/game-files/bo2zm/user/0000000000000000/   your DLC

That bo2zm folder merges into an existing install: sdmc:/switch/bo2zm/ on a Switch, or the folder with bo2zm.exe on
Windows. Use it to add modes or DLC to a console without building again, or to move your files to another SD card.

Options, for a run without questions: --modes zm,mp,cp  --dlc yes|no  [--game-files FOLDER] [--out FOLDER]
"""
import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bo2zm_install  # noqa: E402
import game_files  # noqa: E402
from game_files import ask_choices, ask_yes_no, describe, say  # noqa: E402

NAME = bo2zm_install.NAME
README = """{name}: your game files
==========================

The bo2zm folder here holds the game files of the modes you chose ({modes}):

  bo2zm\\game\\      the disc's files and Title Update 18's executable patches
  bo2zm\\update\\    the rest of Title Update 18
  bo2zm\\user\\      your DLC

Switch: copy the bo2zm folder into the switch folder on your SD card and let it merge with the bo2zm folder already
there (sdmc:/switch/bo2zm/).
Windows: copy what is inside bo2zm into the folder that holds bo2zm.exe and let it merge.

Merging adds and replaces game files only: saves and settings in user\\ are not touched. These are your own game
files: keep them for yourself.
"""


def stop(text):
    say()
    say("Stopped: " + text)
    return 1


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--kit", required=True)
    p.add_argument("--game-files")
    p.add_argument("--out")
    p.add_argument("--modes")
    p.add_argument("--dlc", choices=("yes", "no"))
    args = p.parse_args(argv)
    kit = os.path.abspath(args.kit)
    game_dir = os.path.abspath(args.game_files or os.path.join(kit, "Game Files"))
    build = os.path.abspath(args.out or os.path.join(kit, "build"))
    out = os.path.join(build, "game-files")

    say(f"{NAME}: game files extractor")
    say("=" * (len(NAME) + 22))
    say()
    say("Step 1: looking at your game files")
    say(f"  in {game_dir}")
    os.makedirs(game_dir, exist_ok=True)
    found = game_files.scan(game_dir, skip=[build], progress=lambda m: say("  " + m))
    say()
    describe(found)
    say()
    game, problem = game_files.choose_game(found)
    if problem:
        return stop(problem + ".")
    if not found.tu18:
        return stop(f"Title Update 18 was not found, and it is required. Put the TU18 package ({game_files.TU18_NAME}) "
                    "in the Game Files folder and run this again.")
    packages = found.dlc
    if not packages or args.dlc == "no":
        if args.dlc == "no" or (args.dlc is None and ask_yes_no("Continue without DLC?")):
            packages = []
        else:
            return stop("put your DLC packages in the Game Files folder and run this again.")
    if args.modes:
        modes = bo2zm_install.parse_list(args.modes, tuple(game_files.MODES), {"all": list(game_files.MODES)})
    else:
        say("Step 2: which game modes do you want the files of?")
        modes = ask_choices("Type the numbers", list(game_files.MODES.items()))
    need = game_files.estimate(game, modes, found)
    say()
    say(f"Step 3: writing the files of {', '.join(game_files.MODES[m] for m in modes)} (about {game_files.gb(need)})")
    free = game_files.free_space(build)
    if free < need:
        say(f"  warning: only {game_files.gb(free)} free there; files on the same drive as Game Files are hard links "
            "and take no extra space")
    work = bo2zm_install.work_folder(os.path.join(build, "work"))
    data = os.path.join(work, "data")
    log = os.path.join(work, "logs", "extract.log")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    try:
        installed = game_files.prepare(found, game, modes, packages, data, os.path.join(work, "game-work"), log)
    except (RuntimeError, OSError) as e:
        return stop(str(e))
    dst = os.path.join(out, "bo2zm")
    say("  putting the bo2zm folder together")
    for name in ("game", "update"):
        game_files.sync_folder(bo2zm_install.Installer.tree(os.path.join(data, name)), os.path.join(dst, name))
    dlc = bo2zm_install.Installer.tree(os.path.join(data, "content", "0000000000000000"))
    user = os.path.join(dst, "user", "0000000000000000")
    if dlc:
        game_files.sync_folder(dlc, user)
    elif os.path.isdir(user):
        shutil.rmtree(user)
    with open(os.path.join(out, "README.txt"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(README.format(name=NAME, modes=", ".join(game_files.MODES[m] for m in modes)))
    say()
    say(f"Done: {dst}")
    if installed:
        say("  DLC: " + ", ".join(p.display_name for p in installed))
    say("  Its README.txt says where to copy it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
