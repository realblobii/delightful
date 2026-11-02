# Source mods

The eight projects Delightful's content is carried from, with the repository, branch and commit used, and the licence found in
the repository itself (checked 2 Nov 2026 by reading each `LICENSE` file). `tools/carry.py` and `tools/carry_dd.py` read them;
the licence texts are in `licenses/` and every reuse is credited in [CREDITS.md](../CREDITS.md). Licences can change: open the
repo's `LICENSE` again before copying anything new.

| Mod | Repository | Branch / commit | Licence |
|---|---|---|---|
| Farmer's Delight | https://github.com/vectorwing/FarmersDelight | `1.21` / `dd8b9b0` | MIT, Copyright (c) 2020 vectorwing |
| Rustic Delight | https://github.com/PhantomWing/RusticDelight | `version/1.21` / `50d95de` | MIT, Copyright (c) 2025 PhantomWing |
| Expanded Delight | https://github.com/ianm1647/expandeddelight | `1.21-neo` / `ea82640` | MIT, declared in `gradle.properties`; the repo has no LICENSE file, so the standard MIT text is shipped as `licenses/NOTICE-expandeddelight.txt` |
| Corn Delight | https://github.com/0999312/Corn-Delight | `1.21` / `ab03743` | MIT, Copyright (c) 2022 Zheng Syameimaru |
| Crate Delight | https://github.com/axperty/cratedelight | `26.2-neoforge` / `0b67360` | MIT, Copyright (c) 2024 Axperty |
| Storage Delight | https://github.com/axperty/storagedelight | `1.21.11-neoforge` / `6969cdc` | MIT, Copyright (c) 2024 Axperty |
| Dumplings Delight Rewrapped (a port of the 1.16.5 mod by FoggyHillside) | https://github.com/Joshcraft2002/Dumplings-Delight-Rewrapped | `main` / `c72f089` | MIT, Copyright (c) 2023 FoggyHillside |
| Display Delight | https://github.com/jkvin114/display-delight-neoforge | `main` / `8e1a7c1` | **LGPL-3.0**, plus a notice that 5 models derive from Pder's *Farmers 3D* (MIT). The files carried from it stay LGPL (see CREDITS.md) |

## How each is used

- The first seven are carried whole: blocks, items, models, textures, sounds, lang, recipes, tags and wild-crop worldgen, merged into
  the one `delightful` mod by `tools/merge.py`. Similar items are merged and duplicate recipes removed.
- Display Delight: only the 104 placeable foods for the foods Delightful has (Farmer's, Corn and Expanded Delight and 5 vanilla foods).
  Its Java code is not used; Roast provides the behaviour.
