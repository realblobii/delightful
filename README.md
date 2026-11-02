# Delightful

A food and farming mod for the [Horizon](https://github.com/horizon-rust/horizon) Minecraft client, in the spirit of Farmer's Delight:
a cooking pot, a cutting board, crops you grow and find wild, feasts, pies, placeable dishes and plenty of storage.

It merges [Farmer's Delight](https://github.com/vectorwing/FarmersDelight) with Rustic, Expanded, Corn, Crate, Storage and Dumplings
Delight into one mod, and adds Display Delight's placeable 3D foods. Similar items are combined (one cabbage, not two), and
there are no duplicate recipes. See [Credits](CREDITS.md) for the authors.

## What you get

- **475 blocks, 312 items and about 1,000 recipes** in one creative tab.
- **Cooking pot** and **cutting board** (Cookpot machines). Light a campfire or furnace under the pot to heat it.
- **Feasts and pies** you serve from and eat in bites (Roast), and **104 foods you can set down as 3D dishes** (sneak + right-click).
- **Crops and wild plants** that grow in the world, with crates for storing harvests.
- **Cabinets, drawers and shelves** for storage.

## Install

Delightful needs two library mods, installed as Horizon native mods, plus the content mod itself:

1. [Cookpot](https://github.com/realblobii/cookpot): the machines.
2. [Roast](https://github.com/realblobii/roast): feasts, pies, plates and placeable food.
3. `delightful-0.2.0.hmod`, built from this repo (see below), in your Horizon mods.

> **Status: untested.** Nothing here has been run in Horizon yet, so expect rough edges. Please report problems with your
> `logs/latest.log` (search for `cookpot` and `roast`).

## Documentation

- [What's in the mod](docs/FEATURES.md)
- [What isn't (and why)](docs/UNSUPPORTED.md)
- [Source mods and licences](docs/SOURCES.md) and [Credits](CREDITS.md)

## Building the mod

The mod is generated from the source mods' repositories with the scripts in `tools/` (`carry.py`, `prune.py`, `merge.py`,
`package_mods.py`); the generated mod is in `mods/delightful/`. Do not edit it by hand, change the tools and regenerate. Rebuild
steps are at the end of [docs/FEATURES.md](docs/FEATURES.md).

## For add-on authors

`delightful:cooking_pot` and `delightful:cutting_board` are stable machine ids: other mods can add recipes to them with
[Cookpot add-ons](https://github.com/realblobii/cookpot/blob/main/docs/ADDONS.md).

## Licence

MIT, except the files carried from Display Delight, which are LGPL-3.0. See [Credits](CREDITS.md) and `licenses/`.
