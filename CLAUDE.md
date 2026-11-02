# Delightful: guidance for Claude

Delightful is a Farmer's Delight-style food and farming mod for Horizon. It is a **content mod (`.hmod`), no Rust**.
Its crafting machines are data files for **Cookpot** (`https://github.com/realblobii/cookpot`, a library native mod).

## Current state: wait for the feature list

The repo holds a brief and instructions only. **Do not add blocks, items, recipes, art, or a mod manifest until the research pass in
`docs/BRIEF.md` ("Next steps") is done and the user has said to start.** When they do, restate the list back as a checklist and build in small
steps. If asked to "start" without a list, ask for it.

Decisions already made (do not re-ask):
- The content is data only (no Rust). The one exception is the settings-menu native mod. If anything else needs code, stop and say what hook or Cookpot feature is missing.
- Machines (cooking pot, cutting board and so on) are **Cookpot machine files**, and recipes are **Cookpot recipe
  files** (`cookpot:machine`, `cookpot:recipe`). Delightful's machine ids are public API for add-ons: once chosen, do not
  rename them.
- Prefer **tags** for heat sources, fuels and ingredient categories so other mods can extend them.
- Singleplayer first.
- Scope: Farmer's Delight plus 7 add-ons. **Left out:** Fruits Delight, Gensokyo Delight, Coffee Delight, Cocktails Delight,
  Cultural Delights (restricted or unknown licences). See `docs/BRIEF.md` and `docs/SOURCES.md`.
- Add-ons are toggled from a real settings menu (a small native mod, all on by default). Research how disabled content can be
  hidden before building it, and tell the user if it can't be done. Features Horizon or Cookpot cannot do are removed and listed
  in `docs/UNSUPPORTED.md`. Cabinets and storage are custom chests, not machines. The cutting board is a Cookpot machine
  with a screen and a knife as non-consumed "fuel". Pots are heated by a lit campfire or furnace below.

## Assets and licences (important)

The user wants a near 1:1 clone that uses the source mods' real textures, models and sounds. That is only allowed where
each mod's licence permits it. **Read `docs/BRIEF.md` and `docs/SOURCES.md` first.**
- Before copying anything from a mod, open its repo's `LICENSE` (and README) and confirm the licence. Do not trust the
  table in `docs/SOURCES.md` alone: some entries are unverified.
- MIT and similar: reuse is fine if the licence text and copyright notice are kept. Record each reused asset's origin in
  `CREDITS.md` and ship the licence texts.
- **All Rights Reserved, custom, or unknown licence** (Cocktails Delight, Cultural Delights, Coffee Delight, Fruits Delight,
  Gensokyo Delight): these are **left out**. Do not copy their assets, code or data without the author's written permission.
- Never copy assets by downloading from sites that forbid it, and do not rely on memory for a licence.

## Read first

Before writing any machine or recipe, read Cookpot's docs from its repository, starting at `docs/README.md`
(Quickstart, Authoring reference, Add-ons, Examples). Cookpot's formats changed during development and its docs are the
source of truth. Nothing in Cookpot has been run in the game yet; say so whenever a feature depends on it.

## Horizon rules (carried over)

- Horizon is unofficial and moves fast. Look up block, item and manifest formats in the Horizon source at the commit
  Cookpot pins (`compatibility.json` in the Cookpot repo), not from memory. Docs: `docs/mods.md` in
  `https://github.com/horizon-rust/horizon`.
- When docs and source disagree, the source at the pinned commit wins.
- Never claim something works unless it was run in the game. State what is untested.
- Content is read once at game start: JSON changes need a game restart, not a rebuild.
- Block templates for machines must have a block entity (barrel, chest, furnace).

## Working with the user

- The user tests in the game and reports back with screenshots and logs (`logs/latest.log`, search for `cookpot`).
- Keep each iteration small. Report outcomes plainly: built / not built, tested / untested.
- Do not publish, release or contact external services without asking. Do not push to `main` without being asked.
- Keep docs current as features land: a feature list in `README.md`, and notes for add-on authors on any ids they can rely on.
