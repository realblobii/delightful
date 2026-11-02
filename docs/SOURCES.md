# Source mods

**Decision (2 Nov 2026): rows marked LEFT OUT are not used** (restricted or unknown licence). The mods Delightful is modelled on, with where their source lives and what licence they state. **Licences decide what
we may reuse** (textures, models, sounds, lang, recipes). Read `docs/BRIEF.md` for the policy.

Verified means a page for that project said so while this list was made (2 Nov 2026). Licences and repos can change;
**open the repo's `LICENSE` file before copying anything**, and check for a separate asset licence in its README.

| # | Mod | Repo | Stated licence | Status |
|---|---|---|---|---|
| 1 | Farmer's Delight | https://github.com/vectorwing/FarmersDelight (Fabric port: https://github.com/MehVahdJukaar/FarmersDelight) | MIT (repo licence) | Repo and code licence verified. **Asset licence not checked**: read the repo's LICENSE and README. |
| 2 | Brewin' And Chewin' **(REMOVED FOR NOW)** | https://github.com/ChefsDelights/BrewinAndChewin | MIT | Repo found. MIT is from a port's permission note, not from the repo's LICENSE: confirm. |
| 3 | Rustic Delight | https://github.com/PhantomWing/RusticDelight | MIT | Repo found. MIT is from a port's note: confirm. |
| 4 | Expanded Delight | https://github.com/ianm1647/expandeddelight | MIT | Verified (Modrinth page). |
| 5 | Corn Delight | https://github.com/0999312/Corn-Delight | MIT | Verified (Modrinth page). A separate Fabric edition exists (also listed MIT). |
| 6 | Fruits Delight **(LEFT OUT)** | not found | unknown | **Repo and licence unverified.** CurseForge page: https://www.curseforge.com/minecraft/mc-mods/fruits-delight |
| 7 | Crate Delight | https://github.com/axperty/cratedelight | MIT (LICENSE file, Axperty) | Verified. Used: branch 26.2-neoforge. |
| 8 | Dumpling Delight | https://github.com/Joshcraft2002/Dumplings-Delight-Rewrapped (a port of the 1.16.5 original by FoggyHillside) | MIT (LICENSE file, FoggyHillside) | Verified. The port is what we use. |
| 9 | Gensokyo Delight ~ Youkais' Feasts **(LEFT OUT)** | not found | unknown | **Assumed to be what "Genskoyo Delight" means: confirm.** https://www.curseforge.com/minecraft/mc-mods/gensokyo-delight-youkais-feasts |
| 10 | Coffee Delight **(LEFT OUT)** | not found | custom "Pineapple License" | **Custom licence: read it before any reuse.** https://www.curseforge.com/minecraft/mc-mods/coffee-delight |
| 11 | Cocktails Delight **(LEFT OUT)** | https://github.com/DraconicArcher/CocktailsDelight (inferred from a wiki link) | **All Rights Reserved** (Modrinth) | Do not reuse assets without the author's permission. |
| 12 | Cultural Delights **(LEFT OUT)** | https://github.com/Baisylia/Cultural-Delights-1.19.2 | **All Rights Reserved** (Modrinth) | Do not reuse assets without permission. A Fabric port lists MIT but is a different upload: do not rely on it. |
| 13 | Storage Delight | https://github.com/axperty/storagedelight | MIT (LICENSE file, Axperty) | Verified. Used: branch 1.21.11-neoforge. |

"Corn Delight" was listed twice in the request; it appears once here.

## Related

- Delight Lib (a library by the Crate/Storage Delight author): https://modrinth.com/mod/delight-lib

## Added 2 Nov 2026: Display Delight and Pumpkin Pie Delight

| Mod | Finding |
|---|---|
| Display Delight (3D placeable foods) | **https://github.com/jkvin114/display-delight-neoforge** (supplied by the user, 2 Nov 2026). Its LICENSE file: main project **LGPL-3.0** (code, 5 model modifications, other models) plus a third-party notice: 5 models derived from Pder's *Farmers 3D*, **MIT**. **Carried** for the foods Delightful has (Farmer's, Corn and Expanded Delight and 5 vanilla foods): 104 blocks. The 278 blocks for other mods are not carried. Its Java code is not used; Roast provides the behaviour. The files stay LGPL (see CREDITS.md). |
| Pumpkin Pie Delight | **LGPL-3.0-only**, no repository found. **Redundant**: Farmer's Delight (1.3) already makes pumpkin pie placeable and sliceable, and Delightful's pumpkin pie is a Roast cake with knife slicing. Nothing copied. |
| "Display Delight compatibility from the other mods" | Rustic Delight's `coaster` models are made for Brewin' And Chewin's coaster block (left out). Not carried. Roast's display plate shows those foods as items instead. |
