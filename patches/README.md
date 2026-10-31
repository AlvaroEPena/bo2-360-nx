# patches

## mesa-bo2zm.patch

This project's changes to the Vulkan driver: Mesa's NVK with its NAK compiler, built for Horizon by
[mesa-switch](https://github.com/danfromtico/mesa-switch) (commit `1a8c1a66d6f`) and linked into the NRO.
`tools/build_mesa.sh` clones that commit, applies the patch and builds it. To change it, edit the Mesa checkout
(`mesa/` in the data folder by default) and write it back with `git -C <checkout> diff > patches/mesa-bo2zm.patch`.

| Area | Files | Change |
|---|---|---|
| Build | `build-switch.sh`, `build-unified.sh`, bindgen and rustc wrappers, `meson.build` | Builds from MSYS2 on Windows for devkitA64 |
| Pipeline binds | `src/vulkan/runtime/vk_graphics_state.*`, `vk_pipeline.*` | Fingerprints per state group; a bind copies only the groups that differ |
| Copies | `nvk_cmd_meta.c` | Image-to-image copies on the copy engine; the app picks the upload path; uploads ordered against draws |
| Texture memory | `nvk_device_memory.*`, `nvk_image.c` | Kind views: one GPU range per memory block and kind, shared by its tiled images |
| Descriptors | `nvk_cmd_buffer.*`, `nvk_cmd_draw.c`, `nvk_descriptor_*` | Set 4 by differences, cached constant buffer groups, a leaked push descriptor set freed |
| Measurement | `nvk_cmd_buffer.*`, `nvk_cmd_draw.c`, `nvk_queue.c` | Counters and timings for the renderer's reports |
| Shader compiler | `src/nouveau/compiler/nak/*`, `nak_nir.c` | Corrections for the Switch's Maxwell GPU (SM50) |
| Horizon | `src/nouveau/horizon/*`, `nvkmd/switch/*` | Device and memory handling |

Changes are marked `BO2ZM` in the code. This project's changes are GPL-3.0 under the top-level
[`LICENSE`](../LICENSE); Mesa and the upstream changes the patch carries keep their own licenses (MIT), as listed in
[`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).
