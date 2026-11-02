# What was left out, and why

From the carry reports. Nothing here has been checked in the game.

## Blocks left out

| Reason | Blocks |
|---|---|
| Signs need a text-editing block entity (canvas, hanging, wall) | 72 |
| Feast blocks this tool could not read a serving item from (Rustic pancakes, Corn's popcorn box, dumpling medley) | 9 |
| Model files absent from the source repository | 2 |
| No template fits: tatami mats (3), rope, skillet, rich-soil compost, tomato vine variants, Expanded Delight pieces | about 12 |

## Items and behaviour approximated

- **Knives** (5) are plain iron swords: no tool abilities, no cutting-board role. The cutting board needs no knife.
- **Nourishment and Comfort effects** exist as mob effects but do nothing: Horizon's mod effects have no behaviour yet.
- **Stove** is declared as a furnace-template block: it smelts like a furnace. It is not FD's stove.
- **Cutting-board chances**: results with a chance below 100% (47 across the mods) are dropped, so bonus drops are missing.
- **Ingredients using NeoForge's `difference`** (3) are approximated by their base ingredient.
- **Display Delight:** 104 foods carried (the foods of mods Delightful has); its blocks for 16 other mods are not. Not done: the support table under non-sturdy tops (the `support` property stays false), hiding a plate with an axe, silk-touch drops of the block, particles, wandering-trader sales, and facing the placed food toward the player (it always faces north).

## Recipes skipped

| Reason | Count |
|---|---|
| Integration with Create, Immersive Engineering and others (no such mods in Horizon) | 37 |
| Expanded Delight `juicing` | 5 |
| Result is a block or item that was left out | about 10 |
| Recipes with no certain result (FD salvaging etc.) | 11 |
| Gated on other mods (No Man's Land, vanilla crates) | 6 |

## Not attempted

- **World generation, partly:** wild crops now generate (see below). **Not generated:** wild rice (a custom feature), Expanded Delight's
  cinnamon trees and salt ore, structures and villager houses, and any wild crop whose block was left out.

- **Advancements, enchantments, damage types**, JEI/EMI/Create integrations.
- **Storage Delight's per-block container sizes** and its cabinet screens: all its blocks are plain barrels.
- **Skillet and campfire cooking on a stove**, **the picnic basket's behaviour**, **canvas rugs and signs**.

## Wild crops (untested)

15 wild-crop features generate (cabbages, carrots, onions, potatoes, tomatoes, beetroots, coffee, cotton, corn, peanuts, asparagus,
chili pepper, sweet potato, cranberries, and one more). The originals use Java-coded feature types, so `tools/carry.py` rewrites
each as plain 26.3 data: a `simple_block` placed by a count of attempts, a random offset and the original's ground test, added
to biomes by a `neoforge:add_features` modifier. NeoForge's `c:is_*` biome tags are replaced by my own lists of vanilla biomes
(`BIOME_TAGS` in the script; approximate). Rarity for Rustic Delight's configurable features is fixed at 1 in 30.

**If the game starts with "content mods not loaded" in the log**, a worldgen file is malformed: delete `data/delightful/worldgen/`
and `data/delightful/neoforge/` from the mod (or run `tools/merge.py` after setting `WORLDGEN = False` there) and send me the log line.
Placement may also fail silently if a block's template refuses to survive on the ground (a template-guess problem).

## Villager trades: not possible (no hook)

The mods add trades in Java code. Horizon's content format has no villager-trade data and the 108 native hooks include none for
trades (checked in `native-hooks.json` at the pinned commit). Adding them needs a new hook from the Horizon project. Not done.

## Foods with behaviour in Java code

Foods are read from the Java food definitions (nutrition, saturation, effects, bowl or bottle left behind). Items whose extra
behaviour lives in Java code are plain foods here: hot cocoa (cures a harmful effect), melon juice and milk bottle (always edible, no
nutrition or effect). Expanded Delight's helper foods (stews, meals, salads, drinks, jellies, pie slices) get the helper's fixed effect.
