"""The build kit's front end: asks a few questions in the console and builds the game.

The kit's "Build bo2-360-nx.bat" runs it (through install.py at the kit's root). It looks through the kit's Game
Files folder for the game, Title Update 18 and the DLC, asks which systems and game modes to build, checks the PC's
tools, then hands over to bo2zm_install.py, which does the work in build/work and writes the finished game to
build/switch and build/windows. The answers are remembered in build/choices.json, so running it again (for example
after it stopped) offers to carry on with the same choices.

Options, for a run without questions (all of them must be given):
  --targets switch,windows   --modes zm,mp,cp   --dlc yes|no   [--yes]   and any option of bo2zm_install.py
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bo2zm_install  # noqa: E402
import game_files  # noqa: E402
from game_files import ask_choices, ask_yes_no, describe, say  # noqa: E402

NAME = bo2zm_install.NAME
TARGETS = [("switch", "Nintendo Switch"), ("windows", "Windows")]
MODES = [(k, v) for k, v in game_files.MODES.items()]


def stop(text):
    say()
    say("Stopped: " + text)
    return 1


def load_choices(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--kit", required=True)
    p.add_argument("--game-files")
    p.add_argument("--out")
    p.add_argument("--targets")
    p.add_argument("--modes")
    p.add_argument("--dlc", choices=("yes", "no"))
    p.add_argument("--yes", action="store_true", help="start without asking")
    args, rest = p.parse_known_args(argv)
    kit = os.path.abspath(args.kit)
    game_dir = os.path.abspath(args.game_files or os.path.join(kit, "Game Files"))
    out = os.path.abspath(args.out or os.path.join(kit, "build"))
    choices_path = os.path.join(out, "choices.json")

    say(f"{NAME}: build kit")
    say("=" * (len(NAME) + 11))
    say()
    say("Step 1: looking at your game files")
    say(f"  in {game_dir}")
    if not os.path.isdir(game_dir):
        os.makedirs(game_dir, exist_ok=True)
    found = game_files.scan(game_dir, skip=[out], progress=lambda m: say("  " + m))
    say()
    describe(found)
    say()
    game, problem = game_files.choose_game(found)
    if problem:
        return stop(problem + ".")
    if not found.tu18:
        return stop(f"Title Update 18 was not found, and it is required. Put the TU18 package ({game_files.TU18_NAME}) "
                    "in the Game Files folder and run the kit again.")
    if len([g for g in found.games if g.xex_ok]) > 1:
        say(f"More than one copy of the game was found; using the {game.label()}.")
    packages = found.dlc
    if not packages or args.dlc == "no":
        if args.dlc == "no" or (args.dlc is None and ask_yes_no("Continue without DLC?")):
            packages = []
        else:
            return stop("put your DLC packages in the Game Files folder and run the kit again.")

    last = load_choices(choices_path)
    targets = bo2zm_install.parse_list(args.targets, ("switch", "windows"), {"all": ["switch", "windows"]}) \
        if args.targets else None
    modes = bo2zm_install.parse_list(args.modes, tuple(game_files.MODES), {"all": list(game_files.MODES)}) \
        if args.modes else None
    if last and not (targets or modes):
        say()
        say("Last time you chose: " + ", ".join(dict(TARGETS)[t] for t in last["targets"]) + "; "
            + ", ".join(game_files.MODES[m] for m in last["modes"]) + ".")
        if ask_yes_no("Build the same again?", default=True):
            targets, modes = last["targets"], last["modes"]
    if not targets:
        say()
        say("Step 2: which systems should the game be built for?")
        targets = ask_choices("Type the numbers", TARGETS, default=last and last.get("targets"))
    if not modes:
        say()
        say("Step 3: which game modes? Zombies and Multiplayer are one program, Campaign is another; only the files "
            "and shaders of the modes you choose are built.")
        modes = ask_choices("Type the numbers", MODES, default=last and last.get("modes"))
    os.makedirs(out, exist_ok=True)
    with open(choices_path, "w", encoding="utf-8") as f:
        json.dump({"targets": targets, "modes": modes}, f)

    say()
    say("Step 4: checking the tools on this PC")
    build_args = bo2zm_install.parser().parse_args(
        ["--out", out, "--game-files", game_dir, "--kit", kit, "--target", ",".join(targets),
         "--modes", ",".join(modes)] + (["--no-dlc"] if not packages else []) + rest)
    inst = bo2zm_install.Installer(build_args)
    inst.use(found, packages)
    problems = inst.check_tools() + inst.find_inputs()
    if problems:
        return stop("this PC is missing what the build needs (the kit's README.txt lists it all):\n"
                    + "\n".join("  - " + p for p in problems))
    say("  everything is there")
    need = game_files.estimate(game, modes, found)
    say()
    say("Ready to build:")
    say(f"  for:        {', '.join(dict(TARGETS)[t] for t in targets)}")
    say(f"  modes:      {', '.join(game_files.MODES[m] for m in modes)}")
    relevant = [p.display_name for p in packages if p.has_id and p.modes & set(modes)]
    say(f"  DLC:        {', '.join(relevant) if relevant else 'none'}")
    if "zm" in modes:
        say(f"  bots:       {'bo2zm_bots.gscpack' if inst.bots_pack else 'none (optional; see README.txt)'}")
    say(f"  game files: about {game_files.gb(need)} for these modes")
    say(f"  output:     {out}")
    if inst.work != os.path.join(out, "work"):
        say(f"  work folder: {inst.work} (the build tools need a path without spaces)")
    say("The first build takes a while (half an hour or more on a fast PC; longer with every mode and both systems).")
    say("If it stops, run the kit again: it carries on where it stopped.")
    if not args.yes and not ask_yes_no("Start the build?", default=True):
        return stop("nothing was built.")
    say()
    inst.state["game_files"] = [game_dir]
    try:
        inst.run()
    except bo2zm_install.BuildError as e:
        return stop(str(e))
    say()
    say(f"Everything is in {out}. Each folder there has a README.txt with what to do next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
