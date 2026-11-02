# What was left out, and why

From the carry reports. Nothing here has been checked in the game.

## Blocks left out

| Reason | Blocks |
|---|---|
| Signs need a text-editing block entity (canvas, hanging, wall) | 72 |
| Feast blocks (servings taken with a bowl): Horizon's templates have no such behaviour | 22 |
| Model files absent from the source repository | 2 |
| No template fits: tatami mats (3), rope, skillet, rich-soil compost, tomato vine variants, Expanded Delight pieces | about 12 |

## Items and behaviour approximated

- **Knives** (5) are plain iron swords: no tool abilities, no cutting-board role. The cutting board needs no knife.
- **Nourishment and Comfort effects** exist as mob effects but do nothing: Horizon's mod effects have no behaviour yet.
- **Stove** is declared as a furnace-template block: it smelts like a furnace. It is not FD's stove.
- **Cutting-board chances**: results with a chance below 100% (47 across the mods) are dropped, so bonus drops are missing.
- **Ingredients using NeoForge's `difference`** (3) are approximated by their base ingredient.
- **Pies** are cake-template blocks with a `facing` property.

## Recipes skipped

| Reason | Count |
|---|---|
| Integration with Create, Immersive Engineering and others (no such mods in Horizon) | 37 |
| Expanded Delight `juicing` | 5 |
| Result is a block or item that was left out | about 10 |
| Recipes with no certain result (FD salvaging etc.) | 11 |
| Gated on other mods (No Man's Land, vanilla crates) | 6 |

## Not attempted

- **World generation** (wild crops, structures, villager trades, mobs such as Expanded's): a malformed worldgen file can stop
  the whole content load, so it is left for a later pass. Wild crops therefore do not generate.
- **Advancements, enchantments, damage types**, JEI/EMI/Create integrations.
- **Brewin' And Chewin'** (removed for now; its keg needs fluids) and **Fruits, Coffee, Cocktails, Cultural and Gensokyo Delight** (left out by decision).
- **Storage Delight's per-block container sizes** and its cabinet screens: all its blocks are plain barrels.
- **Skillet and campfire cooking on a stove**, **the picnic basket's behaviour**, **canvas rugs and signs**.
