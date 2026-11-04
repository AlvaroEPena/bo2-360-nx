# GSC Loader: script mods

The GSC Loader runs compiled **T6 Xbox 360 server GSC** objects, the format console mod menus ship in, in Zombies and
Multiplayer. Bring every script a mod needs. Source text, PC/Plutonium bytecode, `.gscr` containers and native
executables cannot be loaded as they are. The loader checks metadata and paths; it does not sandbox what a script
does or guarantee that every feature of a mod works.

## Zombies bots

The Zombies LOCAL lobby starts with **BOT COUNT: OFF**. Choose bots for that
lobby before starting the match. Humans and bots share four slots: one human
allows three bots, two humans allow two, three humans allow one, and four humans
disable bots. Joining humans reduce the choice automatically.

A System Link host gets the same row in its Zombies lobby. Players on other
consoles take slots like local ones, and the bots run on the host. Consoles that
join have no bot row.

Bots are independent of **Extras > Script Loader**: keep a compatible mod menu
selected and choose the bot count in the lobby. An optional `bo2zm_bots.gscpack`
file beside the NRO or PC executable supplies the compiled bot scripts. Without the bot pack, the row shows **NOT INSTALLED** and cannot be changed.
A script conflict is explained by a short hint; the bot component is refused
while the selected menu remains available. Switching the count to
OFF stops loading the bot component on the next match.

The reviewed standalone bot package migrates automatically to this setting.
Other script selections are preserved. Common bot
logic runs on Zombies maps, with additional Origins logic loaded only on Origins.
Map-specific navigation, objectives and mod interactions still require testing.

## Install a mod

1. Put the compiled scripts in `scripts/MyMod/` beside the NRO or PC executable.
   Each mod gets its own folder and a required `mod.ini`. Folder names use letters,
   digits, underscores, dashes and dots; spaces are unsupported.
2. Choose one of the configurations below. Flat and nested layouts both work.
3. Open **Extras > Script Loader**, refresh the list and select the mod.
4. Choose **Check Scripts** to validate it and view each source file's exact
   replacement target. **Setup Issues** explains folders that could not be listed.
5. Choose **Load Selected + Restart** to apply it. This ends an active match.

### Use embedded names

When the compiled objects already contain their correct full replacement paths,
use this for Zombies:

```ini
mode=zombies
names=internal
```

Use `mode=multiplayer` for MP. Omitting `names` also selects `internal`.
A stored `maps/mp/gametypes_zm/_clientids.gsc` remains exactly that path.
The files themselves may be flat or nested; their disk names do not change targets.
Gr3Zz uses this configuration.

### Use the supplied folder structure

For objects with generic internal names, preserve the known game hierarchy:

```text
scripts/MyMod/
    mod.ini
    maps/mp/_development_dvars.gsc
    common_scripts/helper.gsc
```

```ini
mode=multiplayer
names=files
base=/
```

With `base=/`, every file must supply its complete game path through the folder
structure. `/` means the game script root, not the SD card root. The supported
paths start with `maps/mp/` or `common_scripts/`. A flat filename alone is invalid
with this base. For Jiggy's flat `_development_dvars.gsc` and `_ambientpackage.gsc`,
use `base=maps/mp` instead.

### Use flat files with a known target folder

For a generic `_clientids.gsc` known to replace Zombies' gametype script:

```ini
mode=zombies
names=files
base=maps/mp/gametypes_zm
```

The flat file now targets `maps/mp/gametypes_zm/_clientids.gsc`. The base can also
be `common_scripts` or a subfolder of either supported root. **`base` is required
with `names=files`** and is rejected with internal naming. There is no implicit
base. Every recursive `.gsc` file is resolved as `base + relative path`; `/` simply
keeps the relative path. Nested folders extend the chosen base:

```text
base=maps/mp/gametypes_zm
_clientids.gsc       -> maps/mp/gametypes_zm/_clientids.gsc
helpers/example.gsc -> maps/mp/gametypes_zm/helpers/example.gsc
```

Do not repeat a complete game path underneath a non-root base: it would be
prefixed too. Use `base=/` when mixing full `maps/mp/...` and
`common_scripts/...` trees. Only `.gsc` files are loaded; other files are ignored
by the runtime. These are in-memory asset overrides, not edits to original game
files. A script still needs to be requested by the game or imported by another
script; placing it in a folder does not automatically execute it.

The loader does not guess the intended target from a generic name. Check the
mod's instructions, source or supplied hierarchy before choosing filename routing.
Supported roots are currently `maps/mp/` and `common_scripts/`; Campaign loading
is not implemented. `mode=campaign` is reserved and those mods remain unavailable.

INI keys can be ordered freely, with whitespace around `=`. Mode/naming values
are case-insensitive. Blank lines, full-line `#` or `;` comments, an optional
`[mod]` section and a UTF-8 BOM are accepted. Metadata is limited to 1024 bytes;
duplicate/unknown keys, unsafe paths and unsupported sections are rejected.

## Inspect internal names on PC

From the project folder:

```text
python -I tools/inspect/gsc_names.py "C:\Mods\MyMod"
python -I tools/inspect/gsc_names.py --config zombies "C:\Mods\MyMod"
```

The tool reads individual files or folders and prints embedded names. `--config`
prints advisory INI text only when names are unique and non-generic; it writes
nothing. Generic Studio names need explicit targets. BE/LE output describes
header byte order and does not identify Xbox versus PS3 origin or prove compatibility.

## Standalone startup scripts

A mod that adds its own modules can declare one startup script:

```ini
mode=zombies
names=internal
entry=maps/mp/port_mods/mymod/bootstrap.gsc
```

The entry must be included in the mod and export a unique public zero-argument
`main`, `init`, or both. The server loads its dependencies before linking, then starts `main`
and `init` in that order after stock server script startup, once per map load.
Functions run as script threads and may wait normally. This does not discover
all files automatically or add Plutonium-specific natives. Replacement-only
mods do not need `entry`; their stock entry points keep working as before.
Entry `main`/`init` exports must not also carry the engine's autoexec flag.

Map-specific mods declare their allowed maps explicitly:

```ini
maps=zm_tomb
```

Use up to 16 comma-separated map names. The loader checks this before linking
any mod dependencies. Other maps run stock scripts while the selection stays
saved; the Script Loader shows that the mod is inactive there. Omitting `maps`
keeps normal all-map behavior. A script-level map check alone runs too late to
protect dependencies that are unavailable on another map.

A mod with common logic and map-specific add-ons can choose a different startup
module before dependency linking:

```ini
entry=maps/mp/mods/common_start.gsc
map_entries=zm_tomb:maps/mp/mods/origins_start.gsc
```

The default entry runs on other maps; the Origins entry runs on `zm_tomb` and can
include the common logic plus its add-ons. Every listed entry must be contained
and validated. Up to 16 unique map overrides are supported. This chooses startup
dependencies, independently of the optional whole-mod `maps` restriction.

An adapted mod can also declare one zero-argument stock function replacement:

```ini
replace=maps/mp/stock.gsc::function=>maps/mp/port_mods/mymod/logic.gsc::function
```

This requires `entry`. The source must be a stock script outside the mod, and
the target must be a unique public zero-argument export in a contained module.
The loader redirects a private copy before linking; original game assets stay
unchanged. This supports explicit adapted contracts rather than arbitrary
Plutonium `replacefunc` calls. Parameters and multiple replacements are unsupported.

## Local split-screen menus

A mod loads once for the map. It must create menu state and input handlers for
each player itself; the loader does not repeat its startup or bypass verification
and host-only access rules. Some menus already support this, while others need
changes to their source.

Supported menu-owned 2D HUDs fit their local split-screen viewport automatically,
in a Local game and in a System Link game, on the host and on the consoles that
joined it. A joining console runs no scripts of its own: the host tells it, over
the side socket (UDP 31002), which HUD element slots hold a menu element, and it
fits only an element that is still exactly that one.
Text and menu materials scale together; the original script objects remain
unchanged. Stock HUDs and world, shared, 3D or unrecognized asynchronous HUDs keep
their existing rendering. If ownership or provenance is ambiguous, fitting is
disabled for that owner rather than mixing scaled materials with unscaled text.
This does not guarantee compatibility with every compiled menu.

Set `bo2zm_mod_hud_fit=false` in the launch TOML and restart to disable fitting.
The normal setting defaults to `true`; diagnostic HUD tracing remains off.

## Loading and unloading

Selections are separate: `script_mod` for Zombies and `script_mod_mp` for MP in
`user/bo2zm_settings.txt`. A saved choice, including disabled, overrides the
initial `bo2zm_gsc_mod` or `bo2mp_gsc_mod` TOML setting. Script roots default to
`scripts/` beside the executable; `bo2zm_gsc_mods_root` can override that location.

Checking only previews paths; it does not inject, enable or restart anything.
Loading/unloading restarts the current mode to clear linked objects, threads,
HUD and effects. Unload keeps the files. Campaign's manager controls the next
Zombies selection; it does not execute Campaign scripts.

Without an explicit `entry`, scripts still need a game-called entry point:
a stock replacement or one of its imports must actually be requested.
Readable source needs compilation for T6 Xbox 360, for example:

```text
gsc-tool -m comp -g t6 -s xb2 -i server source
```

Limits are 32 scripts, 1 MiB each and 4 MiB per mod. Animation-tree, relocation
and profiling records are unsupported. Older objects with omitted code sizes
need `bo2zm_gsc_legacy_sizes=true`; only the writable working copy is repaired.
That option also permits the exact immutable header-magic literal (as a field
name, string or export name) that some older compilers point at. Other header
offsets remain rejected. Literal strings
are bounded to 16 KiB; names retain narrower bounds.

BO2 patches scripts while linking. Each server load gets a fresh writable copy;
previous generations remain until exit, capped at 16 MiB and 64 loads. Reaching
either cap selects stock scripts until restart rather than reclaiming objects
that the VM might still reference.
