# Add-on settings: what OFF does

Options > Mods > **Delightful settings** has one button per add-on (Brewin' And Chewin', Rustic Delight, Expanded Delight,
Corn Delight), ON by default. The base mod (Farmer's Delight) has no switch. Settings are saved under
`horizon-mods/.horizon-mod-data/delightful_settings/`.

**Decided:** OFF must not unload anything. The add-on's blocks, items and recipes stay loaded, so worlds keep working.

**What Horizon allows (checked in the source at the pinned commit):** there is no hook that edits the creative inventory, and
no hook that gates a crafting recipe at run time. So OFF does only this:

- **Items of an OFF add-on are removed from player inventories as they are carried** (`native_inventory_tick` and
  `native_carried_stack`). That makes them unobtainable in survival and in creative: anything crafted, picked up or taken
  from the creative menu disappears on the next tick.
- **Placed blocks, existing world content and recipes are untouched.**

**What OFF does not do (a Horizon limitation):**
- The add-on's items still **show in the creative menu**. Taking one removes it again.
- Its recipes still appear in the recipe book and the crafting grid still produces the item (which then disappears).
- **Items already in inventories or chests**: inventory items vanish when the add-on is turned off; items in chests stay.

If hiding from the creative menu is essential, Horizon needs a new hook for it. Tell me and I will describe what to ask the
Horizon project for.
