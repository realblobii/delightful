# Delightful: project brief

*Improved from the user's first prompt (2 Nov 2026). Items marked **[open]** need a decision before building.*

## Goal

Delightful is a Farmer's Delight-style food and farming mod for Horizon, built as **content mods (`.hmod`, no Rust)** on
top of [Cookpot](https://github.com/realblobii/cookpot) (the crafting-machine library). It reproduces the content of
Farmer's Delight and 12 add-ons (`docs/SOURCES.md`) as closely as Horizon allows.

## Scope

**Included mods** (all 1:1 where possible): Farmer's Delight, Brewin' And Chewin', Rustic Delight, Expanded Delight,
Corn Delight, Fruits Delight, Crate Delight, Dumpling Delight, Gensokyo Delight ~ Youkais' Feasts, Coffee Delight,
Cocktails Delight, Cultural Delights, Storage Delight.

**Rule for gaps:** anything Horizon or Cookpot cannot do is **removed**, and listed in `docs/UNSUPPORTED.md` with the
reason (so the list is reviewed, not silent).

## Decisions made

1. **Each add-on is toggleable, all on by default.** **[open]** how: see "Settings" below.
2. **Heat:** the cooking pot (and other heated machines) are heated by a **lit campfire or lit furnace** below them, using
   Cookpot's heat-from-block rule (`heat.sources`, default offset directly below).
3. **Cabinets, drawers, crates, shelves** are **custom chests** (container blocks with a vanilla menu), not Cookpot machines.
4. **Cutting board** is a **Cookpot machine with a screen**, not the original place-and-click board. A **knife is its
   infinite "fuel"**: it must be present but is not used up. **[open]** needs a small Cookpot change: see below.
5. Machines are Cookpot machine files; recipes are Cookpot recipe files. Machine ids are public API once chosen.

## Assets and licences **[open]**

The request is to use the real textures, models and sounds from the source mods. Whether that is allowed depends on each
mod's licence (`docs/SOURCES.md`):

- **MIT or similar (most of them):** reuse is permitted if the licence text and copyright notice are kept. Delightful must
  carry a `CREDITS.md` and the licence texts. Still check each repo for a separate asset licence.
- **All Rights Reserved (Cocktails Delight, Cultural Delights) and unknown (Fruits Delight, Gensokyo Delight, Coffee
  Delight's custom licence):** the assets cannot be copied without the author's permission.

Proposed policy, **pending the user's decision**: reuse from MIT-licensed mods with attribution; for the others, either get
written permission, draw original art with the same design, or leave the content out.

## Settings (add-on toggles) **[open]**

A content mod has no code, so it cannot draw a settings screen on its own. Two options:

- **A. One `.hmod` per add-on** (a `delightful` core plus `delightful_brewin`, `delightful_corn`, ...). The existing
  Options > Mods list already enables and disables each, with everything enabled by default. No new code.
- **B. A real settings menu** (a native mod with its own screen and saved settings) that hides or disables an add-on's
  recipes, items and machines at runtime. More code, and it needs a way to switch content off that has not been checked.

## Cookpot changes this needs

- **Non-consumed tool slot** (for the knife): a slot role whose item must be present but is not used up, optionally taking
  durability damage. Cookpot's fuel slot consumes its item today.
- Possibly **fluids** for Brewin' And Chewin's keg (Horizon has a fluid container hook; not yet used by Cookpot).
- Cabinet-style storage needs no Cookpot change.

## Practical limits

- Nothing built so far (Cookpot or Delightful) has been run in the game.
- Source mods target Minecraft 1.20.1 or 1.21.1; Horizon is a rewrite of 26.3. Block, item, model and loot formats must be
  checked against Horizon's source, and some features (mobs, world generation, custom entities, villager trades) may not
  be possible. Those go in `docs/UNSUPPORTED.md` after research.
- Getting the assets means reading each mod's repo or jar. The development container can reach GitHub but not most other
  sites, so jars from CurseForge or Modrinth may need to be supplied by the user.

## Next steps

1. User answers the [open] items.
2. Research pass: what each source mod contains (blocks, items, machines, entities, worldgen) and what Horizon supports.
   Output: `docs/FEATURES.md` (what we build) and `docs/UNSUPPORTED.md` (what we drop).
3. Cookpot changes (tool slot), tested by the user.
4. Build Farmer's Delight first, then each add-on in order.
