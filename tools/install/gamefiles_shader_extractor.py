"""The game files and shader extractor: prepares your own game files and shader libraries for the prebuilt bo2-360-nx.

The release's prebuilt programs (bo2zm.nro and bo2cp.nro for the Switch, bo2zm.exe and bo2cp.exe for Windows) still
need two things only your own copy of the game can give them: the game files and the shader libraries. This tool makes
those two and nothing else, so it needs no compiler, only Python and the host tools it ships with.

Its "Extract game files and shaders.bat" runs it (through extractor.py at the tool's root). It:

  1. looks through the Game Files folder for the game (a disc image or the folder extracted from one), Title Update 18
     (required) and the DLC (optional), exactly as the build kit does (game_files.py);
  2. asks what to make: the game files, the shaders, or both;
  3. asks for the modes: any of Zombies, Multiplayer and Campaign;
  4. writes output/README.txt and output/bo2zm/:

       game/, update/, user/0000000000000000/   the chosen modes' game files, Title Update 18 and the DLC
       bo2zm_shaders.spvpack and .spvidx        the shaders of Zombies and/or Multiplayer (one library serves both)
       bo2cp_shaders.spvpack and .spvidx        the campaign's shaders

The work is the build kit's own (bo2zm_install.Installer, which this tool subclasses): the same steps lay out the
files, decrypt the two programs and check they are TU18's (the fastfiles' key is rebuilt from them), build each shader
library and its index. The steps record their progress in work/state.json, so a run that stopped carries on where it
stopped, and a run with other choices redoes only what they change. The tool ships only what those steps need:
SOURCE_FILES below (in source/) and HOST_TOOLS (in runtime/host).

Options, for a run without questions (all three must be given):
  --make files|shaders|both   --modes zm,mp,cp   --dlc yes|no   [--game-files FOLDER] [--out FOLDER] [--work FOLDER]
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bo2zm_install  # noqa: E402
import game_files  # noqa: E402
from bo2zm_install import Step, fail, link_or_copy  # noqa: E402
from game_files import ask_choices, ask_yes_no, describe, say  # noqa: E402

NAME = bo2zm_install.NAME
# The scripts and files of the source tree the steps use, relative to its root. tools/install/make_extractor.py packs
# exactly these.
SOURCE_FILES = (
    "tools/install/gamefiles_shader_extractor.py",
    "tools/install/bo2zm_install.py",
    "tools/install/game_files.py",
    "tools/install/xiso.py",
    "tools/install_dlc.py",
    "tools/inspect/stfs_extract.py",
    "tools/inspect/ff_shaders.py",
    "tools/xenosrecomp/translator/shader_common.h",
)
# The prebuilt host tools of the runtime package the shader steps run: the decrypter and its runtime library, the
# shader translator and packer, and the shader compiler with its validator.
HOST_TOOLS = ("xexdump.exe", "rexruntime.dll", "bo2zm_hlsl.exe", "bo2zm_pack.exe", "dxc.exe", "dxcompiler.dll",
              "spirv-val.exe")
MAKE = [("files", "Game files"), ("shaders", "Shaders"), ("both", "Both")]
MAKE_TEXT = {"files": "the game files", "shaders": "the shaders", "both": "the game files and the shaders"}
PROGRAMS = (("bo2zm", ("zm", "mp")), ("bo2cp", ("cp",)))

README = """{name}: your game files and shaders
{rule}

The bo2zm folder here was made from your own copy of the game, for {modes}. It holds:

{contents}

Switch
------
1. Put your SD card in your PC.
2. Copy this bo2zm folder into the switch folder on the SD card.
3. There is already a bo2zm folder there, the one with bo2zm.nro from the release (and bo2cp.nro for Campaign).
   When Windows asks, say yes to merge the folders. Merging only adds files and replaces the ones with the same name:
   it deletes nothing, so your saves stay.

When you are done, the SD card looks like this:

  sdmc:/switch/bo2zm/
      bo2zm.nro                  from the release: Zombies and Multiplayer
      bo2zm.toml                 from the release: its settings
      bo2cp.nro                  from the release: Campaign
      bo2cp.toml                 from the release: its settings
      bo2zm_shaders.spvpack      from this tool: the shaders of Zombies and Multiplayer
      bo2zm_shaders.spvidx       from this tool: their index
      bo2cp_shaders.spvpack      from this tool: the shaders of Campaign
      bo2cp_shaders.spvidx       from this tool: their index
      game/                      from this tool: the game files
      update/                    from this tool: Title Update 18
      user/
          0000000000000000/      from this tool: your DLC

You only need the bo2zm files to play Zombies or Multiplayer, and the bo2cp files to play Campaign.

Windows
-------
The same files go in the same places, next to bo2zm.exe (and bo2cp.exe) instead of bo2zm.nro: copy what is inside this
bo2zm folder into the folder that has bo2zm.exe, and merge.

To add another mode later, run the tool again and choose it: it makes everything for the modes you choose then.

These are your own game files. Keep them for yourself.
"""


def stop(text):
    say()
    say("Stopped: " + text)
    return 1


def remove(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.lexists(path):
        os.remove(path)


class Extractor(bo2zm_install.Installer):
    """The kit's build with only the steps that make game files and shader libraries, and an output step of its own."""

    def __init__(self, args, make):
        super().__init__(args)
        self.files = make in ("files", "both")
        self.shaders = make in ("shaders", "both")

    def steps(self):
        main, cp = self.main_program, self.campaign
        zm_mp = " and ".join(game_files.MODES[m] for m in ("zm", "mp") if m in self.modes)
        shaders = lambda: self.shaders  # noqa: E731
        all_steps = [
            Step("source", "copy the tool's scripts into the work folder", self.step_source, (), shaders),
            Step("game", "lay out the game files, Title Update 18 and the DLC", self.step_game),
            Step("decrypt", "decrypt the game's programs and check they are TU18's", self.step_decrypt,
                 ("source", "game"), shaders),
            Step("shaders", f"build the shader library of {zm_mp}", self.step_shaders, ("game", "decrypt"),
                 lambda: self.shaders and main()),
            Step("shaders-campaign", "build the campaign's shader library", self.step_shaders_campaign,
                 ("game", "decrypt"), lambda: self.shaders and cp()),
            Step("output", "put together the output folder", self.step_output,
                 ("game", "shaders", "shaders-campaign")),
        ]
        return [s for s in all_steps if s.when()]

    def check_tools(self):
        """Only the shader steps run tools: the host tools and the scripts they need."""
        problems = []
        if not self.shaders:
            return problems
        for name in HOST_TOOLS:
            if not os.path.isfile(os.path.join(self.host(), name)):
                problems.append(f"the tool's runtime folder lacks {name} (runtime/host): unpack the tool again")
        for rel in SOURCE_FILES:
            if not os.path.isfile(os.path.join(self.source, *rel.split("/"))):
                problems.append(f"the tool lacks {rel} (in source/): unpack the tool again")
        if not problems:
            r = subprocess.run([os.path.join(self.host(), "xexdump.exe")], capture_output=True)
            if r.returncode in (0xC0000135, -1073741515):
                problems.append("the tool's programs cannot start: install the Microsoft Visual C++ Redistributable "
                                "(x64)")
        return problems

    def check(self):
        problems = self.check_tools() + self.find_inputs()
        if problems:
            fail("it cannot start:\n" + "\n".join("  - " + p for p in problems))
        # The game files are hard links when they are on the same drive as the work folder. The shader build needs
        # a few gigabytes more for the decompressed zones and the compiled shaders while it runs.
        need = game_files.estimate(self.game, self.modes, self.found) * (0 if self.same_drive() else 1)
        need += 8e9 if self.shaders else 0
        free = game_files.free_space(self.work)
        if free < need:
            say(f"  warning: {game_files.gb(free)} free in {self.work}, about {game_files.gb(need)} needed")

    def step_source(self, run):
        # Only the scripts the shader steps run, so the work folder holds its own copy as the kit's does.
        for rel in SOURCE_FILES:
            link_or_copy(os.path.join(self.source, *rel.split("/")), os.path.join(self.src, *rel.split("/")))
        say(f"  {len(SOURCE_FILES)} files")

    def step_output(self, run):
        dst = os.path.join(self.out, "bo2zm")
        os.makedirs(dst, exist_ok=True)
        user = os.path.join(dst, "user")
        dlc = os.path.join(user, "0000000000000000")
        if self.files:
            self.lay_out_game(dst)
        else:
            for name in ("game", "update"):
                remove(os.path.join(dst, name))
            remove(dlc)
        if os.path.isdir(dlc) and not self.tree(dlc):
            remove(dlc)
        if os.path.isdir(user) and not os.listdir(user):
            os.rmdir(user)
        for program, modes in PROGRAMS:
            pack = os.path.join(dst, f"{program}_shaders.spvpack")
            index = os.path.join(dst, f"{program}_shaders.spvidx")
            if self.shaders and set(modes) & set(self.modes):
                self.lay_out_shaders(run, program, dst)
                if not os.path.isfile(index):
                    fail(f"the index of {os.path.basename(pack)} was not made: see {run.log_path}")
                say(f"  {os.path.basename(pack)}: {os.path.getsize(pack) / 1e6:.0f} MB, with its index")
            else:
                remove(pack)
                remove(index)
        with open(os.path.join(self.out, "README.txt"), "w", encoding="utf-8", newline="\r\n") as f:
            f.write(self.readme(dst))
        say(f"  {dst}")

    def readme(self, dst):
        lines = []
        if self.files:
            lines += ["  game/                       the game files", "  update/                     Title Update 18"]
            if os.path.isdir(os.path.join(dst, "user", "0000000000000000")):
                lines.append("  user/0000000000000000/      your DLC")
        if self.shaders:
            for program, modes in PROGRAMS:
                chosen = [game_files.MODES[m] for m in modes if m in self.modes]
                if chosen:
                    lines.append(f"  {program}_shaders.spvpack       the shaders of {' and '.join(chosen)}")
                    lines.append(f"  {program}_shaders.spvidx        their index")
        title = f"{NAME}: your game files and shaders"
        return README.format(name=NAME, rule="=" * len(title), modes=self.modes_text(),
                             contents="\n".join(lines))

    def modes_text(self):
        names = [game_files.MODES[m] for m in self.modes]
        return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]

    def report(self):
        say(f"  Everything is in {self.out}: its README.txt says where to copy the bo2zm folder.")
        say(f"  The work folder ({self.work}) holds the tool's own files. Keep it for a quicker run with other")
        say("  choices, or delete it: the output folder does not need it.")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--tool", required=True, help="the tool's folder (with Game Files, runtime and source)")
    p.add_argument("--game-files")
    p.add_argument("--out")
    p.add_argument("--work")
    p.add_argument("--make", choices=[k for k, _ in MAKE])
    p.add_argument("--modes")
    p.add_argument("--dlc", choices=("yes", "no"))
    args = p.parse_args(argv)
    tool = os.path.abspath(args.tool)
    game_dir = os.path.abspath(args.game_files or os.path.join(tool, "Game Files"))
    out = os.path.abspath(args.out or os.path.join(tool, "output"))
    work = os.path.abspath(args.work or os.path.join(tool, "work"))

    title = f"{NAME}: game files and shader extractor"
    say(title)
    say("=" * len(title))
    say()
    say("Step 1: looking at your game files")
    say(f"  in {game_dir}")
    os.makedirs(game_dir, exist_ok=True)
    found = game_files.scan(game_dir, skip=[out, work], progress=lambda m: say("  " + m))
    say()
    describe(found)
    say()
    game, problem = game_files.choose_game(found)
    if problem:
        return stop(problem + ".")
    if not found.tu18:
        return stop(f"Title Update 18 was not found, and it is required. Put the TU18 package ({game_files.TU18_NAME}) "
                    "in the Game Files folder and run this again.")
    if len([g for g in found.games if g.xex_ok]) > 1:
        say(f"More than one copy of the game was found; using the {game.label()}.")
    packages = found.dlc
    if not packages or args.dlc == "no":
        if args.dlc == "no" or (args.dlc is None and ask_yes_no("Continue without DLC?")):
            packages = []
        else:
            return stop("put your DLC packages in the Game Files folder and run this again.")

    if args.make:
        make = args.make
    else:
        say()
        say("Step 2: what do you want to make?")
        picked = ask_choices("Type a number", MAKE)
        make = picked[0] if len(picked) == 1 else "both"
    if args.modes:
        modes = bo2zm_install.parse_list(args.modes, tuple(game_files.MODES), {"all": list(game_files.MODES)})
    else:
        say()
        say("Step 3: which game modes? Zombies and Multiplayer share one shader library, Campaign has its own; only "
            "the files and shaders of the modes you choose are made.")
        modes = ask_choices("Type the numbers", list(game_files.MODES.items()))

    say()
    say("Making:")
    say(f"  what:   {MAKE_TEXT[make]}")
    say(f"  modes:  {', '.join(game_files.MODES[m] for m in modes)}")
    relevant = [p.display_name for p in packages if p.has_id and p.modes & set(modes)]
    say(f"  DLC:    {', '.join(relevant) if relevant else 'none'}")
    say(f"  output: {out}")
    if make != "files":
        say("The shaders take a while on a fast PC: about 10 minutes for Zombies and Multiplayer (more with the DLC) "
            "and about 20 minutes for Campaign.")
        say("If it stops, run the tool again: it carries on where it stopped.")
    say()
    build_args = bo2zm_install.parser().parse_args(
        ["--out", out, "--work", work, "--game-files", game_dir, "--kit", tool, "--modes", ",".join(modes)]
        + (["--no-dlc"] if not packages else []))
    inst = Extractor(build_args, make)
    inst.use(found, packages)
    inst.state["game_files"] = [game_dir]
    inst.state.setdefault("steps", {}).pop("output", None)  # cheap, and always made to match this run's choices
    try:
        inst.run()
    except bo2zm_install.BuildError as e:
        return stop(str(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
