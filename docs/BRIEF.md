# Delightful: project brief

*Improved from the user's first prompt (2 Nov 2026). Items marked **[open]** need a decision before building.*

## Goal

Delightful is a Farmer's Delight-style food and farming mod for Horizon, built as **content (`.hmod`, no Rust)** on top of
[Cookpot](https://github.com/realblobii/cookpot) (the crafting-machine library), (each add-on its own mod). It reproduces the content of Farmer's Delight and its add-ons (`docs/SOURCES.md`) as
closely as Horizon allows.

## Scope

**Included mods** (1:1 where possible): Farmer's Delight, Rustic Delight, Expanded Delight,
Corn Delight, Crate Delight, Dumpling Delight, Storage Delight.

**Left out (decided 2 Nov 2026):** Fruits Delight, Gensokyo Delight ~ Youkais' Feasts, Coffee Delight, Cocktails Delight
and Cultural Delights. Their licences are All Rights Reserved, custom, or unknown, so their assets cannot be reused. They
may be revisited if their authors give written permission. (Cocktails Delight also needs Brewin' And Chewin'.)

**Rule for gaps:** anything Horizon or Cookpot cannot do is **removed**, and listed in `docs/UNSUPPORTED.md` with the
reason (so the list is reviewed, not silent).

## Decisions made

1. **Each add-on is a separate mod**, toggled in Options > Mods (decided 2 Nov 2026).
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

## Add-on toggles

**Decided 2 Nov 2026:** no settings menu. Each add-on is its own `.hmod`, switched on or off in Options > Mods. (An earlier plan, a native settings page, was dropped.)

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

First increment generated: see [FEATURES.md](FEATURES.md) and [UNSUPPORTED.md](UNSUPPORTED.md). Brewin' And Chewin' is removed for now.

## Next steps (original plan)

1. (Done: no settings menu; add-ons are separate mods.)
2. Research pass: what each source mod contains (blocks, items, machines, entities, worldgen) and what Horizon supports.
   Output: `docs/FEATURES.md` (what we build) and `docs/UNSUPPORTED.md` (what we drop).
3. Cookpot changes (see above), tested by the user.
4. Build Farmer's Delight first, then each add-on in order.
