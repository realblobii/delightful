# Delightful: project brief

*Improved from the user's first prompt (2 Nov 2026). Items marked **[open]** need a decision before building.*

## Goal

Delightful is a Farmer's Delight-style food and farming mod for Horizon, built as **content (`.hmod`, no Rust)** on top of
[Cookpot](https://github.com/realblobii/cookpot) (the crafting-machine library), plus **one small native mod for the
settings menu** (see "Settings"). It reproduces the content of Farmer's Delight and 7 add-ons (`docs/SOURCES.md`) as
closely as Horizon allows.

## Scope

**Included mods** (1:1 where possible): Farmer's Delight, Brewin' And Chewin', Rustic Delight, Expanded Delight,
Corn Delight, Crate Delight, Dumpling Delight, Storage Delight.

**Left out (decided 2 Nov 2026):** Fruits Delight, Gensokyo Delight ~ Youkais' Feasts, Coffee Delight, Cocktails Delight
and Cultural Delights. Their licences are All Rights Reserved, custom, or unknown, so their assets cannot be reused. They
may be revisited if their authors give written permission. (Cocktails Delight also needs Brewin' And Chewin'.)

**Rule for gaps:** anything Horizon or Cookpot cannot do is **removed**, and listed in `docs/UNSUPPORTED.md` with the
reason (so the list is reviewed, not silent).

## Decisions made

1. **Each add-on is toggleable, all on by default**, from a **real settings menu** (decided 2 Nov 2026): see "Settings".
2. **Heat:** the cooking pot (and other heated machines) are heated by a **lit campfire or lit furnace** below them, using
   Cookpot's heat-from-block rule (`heat.sources`, default offset directly below).
3. **Cabinets, drawers, crates, shelves** are **custom chests** (container blocks with a vanilla menu), not Cookpot machines.
4. **Cutting board** is a **Cookpot machine with a screen** (an `instant` machine), not the original place-and-click board.
   **No knife is needed** (decided 2 Nov 2026: the knife requirement is dropped).
5. Machines are Cookpot machine files; recipes are Cookpot recipe files. Machine ids are public API once chosen.

## Assets and licences

The aim is to use the real textures, models and sounds from the source mods, so licences decide what is allowed
(`docs/SOURCES.md`).

- **Included mods are MIT-licensed** (some unconfirmed): reuse is permitted if the licence text and copyright notice are
  kept. Delightful carries a `CREDITS.md` and the licence texts, and every reused file's origin is recorded.
- **Confirm before copying:** for each mod, open its repo's `LICENSE` and README (an asset licence may differ from the code
  licence). Repos still to be found: Crate Delight, Storage Delight, Dumpling Delight (the Rewrapped port and the
  original). Farmer's Delight's asset licence is unchecked.
- The five left-out mods are not touched.

## Settings (add-on toggles)

**Decided: a real settings menu.** A content mod has no code, so this is a **native mod** (`delightful_settings`, in this
repo) with its own screen, a saved setting per add-on, and all add-ons **on by default**. It would use the native hooks
Cookpot already relies on, plus the screen and settings hooks (`native_screen`, `native_set_setting`).

**[open] research first:** a disabled add-on has to disappear (its items, blocks, recipes, machines, creative-tab entries).
Content is read once at game start, and nothing checked so far shows a way to switch content off at runtime. The research
pass must find one, and if there isn't, tell the user before building. Fallbacks to put to the user then:
(a) the setting takes effect after a restart and the native mod filters recipes/items it can reach, or
(b) one `.hmod` per add-on toggled in Options > Mods.

## Cookpot changes this needs

- Possibly **fluids** for Brewin' And Chewin's keg (Horizon has a fluid container hook; not yet used by Cookpot).
- Cabinet-style storage needs no Cookpot change.
- Machines from toggled-off add-ons must be skippable: Cookpot would need a way to ignore a machine or recipe when its add-on
  is off (for example a condition on the file). **[open]**

## Practical limits

- Nothing built so far (Cookpot or Delightful) has been run in the game.
- Source mods target Minecraft 1.20.1 or 1.21.1; Horizon is a rewrite of 26.3. Block, item, model and loot formats must be
  checked against Horizon's source, and some features (mobs, world generation, custom entities, villager trades) may not
  be possible. Those go in `docs/UNSUPPORTED.md` after research.
- Getting the assets means reading each mod's repo or jar. The development container can reach GitHub but not most other
  sites, so jars from CurseForge or Modrinth may need to be supplied by the user.

## Status (2 Nov 2026)

Research and a first increment are done: see [FEATURES.md](FEATURES.md), [UNSUPPORTED.md](UNSUPPORTED.md) and [SETTINGS.md](SETTINGS.md). The toggle decision became: OFF removes the add-on's items from inventories and does not unload content; hiding from the creative menu is not possible with Horizon's current hooks.

## Next steps (original plan)

1. Research the settings menu and how a disabled add-on can be hidden (see "Settings").
2. Research pass: what each source mod contains (blocks, items, machines, entities, worldgen) and what Horizon supports.
   Output: `docs/FEATURES.md` (what we build) and `docs/UNSUPPORTED.md` (what we drop).
3. Cookpot changes (see above), tested by the user.
4. Build Farmer's Delight first, then each add-on in order.
