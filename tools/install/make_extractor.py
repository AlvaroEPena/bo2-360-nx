"""Makes the game files and shader extractor: one "bo2-360-nx-gamefiles-shader-extractor.zip" for players who use the
release's prebuilt programs and only need their own game files and shader libraries.

The tool is one folder:
  Extract game files and shaders.bat   double-click: scans Game Files, asks what to make and for which modes
  extractor.py                         what the .bat starts (source/tools/install/gamefiles_shader_extractor.py)
  README.txt                           what the tool needs and does (tools/install/extractor/README.txt)
  Game Files/                          where the player puts the game, Title Update 18 and the DLC
  LICENSE, THIRD_PARTY_NOTICES.md
  source/                              only the scripts the tool runs (SOURCE_FILES of gamefiles_shader_extractor.py),
                                       taken from the public source tree (--source, an export of main)
  runtime/host/                        only the host tools it runs (HOST_TOOLS), from the runtime package
                                       (tools/install/make_runtime.py), with the shader compiler's licence

It needs no Switch driver and no compiler. Nothing is published: the zip is only written to disk.

usage: python -I tools/install/make_extractor.py --runtime <runtime package> [--source <public tree>] [--name "<name>"]
                                                 [--out <folder>] [--folder-only]

  --source       the public source tree the scripts are taken from (default C:/dev/bo2-360-nx, the export)
  --name         the tool's name: its folder and its zip (default bo2-360-nx-gamefiles-shader-extractor)
  --out          where the zip goes (default: release/ in the data folder, tools/data_dir.sh)
  --folder-only  write the tool's folder without zipping it (for testing it as a player would unpack it)
"""
import argparse
import ast
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_kit  # noqa: E402
from make_kit import ROOT, inside, say, text_file, zip_folder  # noqa: E402

TEMPLATE = os.path.join(HERE, "extractor")
DEFAULT_NAME = "bo2-360-nx-gamefiles-shader-extractor"
BAT = "Extract game files and shaders.bat"
# The licences of the prebuilt parts the tool ships (dxc and spirv-val come from the Vulkan SDK).
RUNTIME_LICENSES = ("vulkan-sdk-LICENSE.txt",)


def lists(tree):
    """SOURCE_FILES and HOST_TOOLS as the tree's own extractor names them, so the zip matches the script it ships.
    They are read from the script's text, without importing it."""
    path = os.path.join(tree, "tools", "install", "gamefiles_shader_extractor.py")
    if not os.path.isfile(path):
        sys.exit(f"{tree} has no tools/install/gamefiles_shader_extractor.py (export main first)")
    names = {}
    for node in ast.parse(open(path, encoding="utf-8").read(), path).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("SOURCE_FILES", "HOST_TOOLS"):
                    names[target.id] = ast.literal_eval(node.value)
    return names["SOURCE_FILES"], names["HOST_TOOLS"]


def make_extractor(name, runtime, out, folder_only, tree):
    source_files, host_tools = lists(tree)
    folder = os.path.join(out, name)
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder)
    say(f"== {name}")
    for rel in source_files:
        src = os.path.join(tree, *rel.split("/"))
        if not os.path.isfile(src):
            sys.exit(f"{tree} lacks {rel}")
        dst = os.path.join(folder, "source", *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    say(f"  source: {len(source_files)} files")
    for n in host_tools:
        src = os.path.join(runtime, "host", n)
        if not os.path.isfile(src):
            sys.exit(f"the runtime package lacks host/{n}: make it with make_runtime.py")
        os.makedirs(os.path.join(folder, "runtime", "host"), exist_ok=True)
        shutil.copy2(src, os.path.join(folder, "runtime", "host", n))
    for n in RUNTIME_LICENSES:
        src = os.path.join(runtime, "licenses", n)
        if not os.path.isfile(src):
            sys.exit(f"the runtime package lacks licenses/{n}")
        os.makedirs(os.path.join(folder, "runtime", "licenses"), exist_ok=True)
        shutil.copy2(src, os.path.join(folder, "runtime", "licenses", n))
    say(f"  runtime: {len(host_tools)} host tools")
    for f in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(os.path.join(tree, f), folder)
    for f in (BAT, "extractor.py"):
        shutil.copy2(os.path.join(TEMPLATE, f), folder)
    title = "bo2-360-nx: game files and shader extractor"
    text_file(os.path.join(TEMPLATE, "README.txt"), os.path.join(folder, "README.txt"), name=title,
              rule="=" * len(title))
    text_file(os.path.join(TEMPLATE, "Game Files", "Put your game files here.txt"),
              os.path.join(folder, "Game Files", "Put your game files here.txt"))
    if folder_only:
        say(f"  {folder}")
        return folder
    return zip_folder(folder)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--runtime", required=True)
    p.add_argument("--source", default=make_kit.DEFAULT_SOURCE)
    p.add_argument("--name", default=DEFAULT_NAME)
    p.add_argument("--out")
    p.add_argument("--folder-only", action="store_true")
    args = p.parse_args()
    data = os.path.abspath(make_kit.data_dir())
    out = os.path.abspath(args.out or os.path.join(data, "release"))
    if inside(out, ROOT) and not inside(out, data):  # the data folder is git-ignored, even inside the checkout
        sys.exit("the tool must be written outside the repository or in its data folder")
    os.makedirs(out, exist_ok=True)
    make_extractor(args.name, os.path.abspath(args.runtime), out, args.folder_only, os.path.abspath(args.source))


if __name__ == "__main__":
    main()
