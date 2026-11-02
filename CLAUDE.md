# Delightful: guidance for Claude

Delightful is a Farmer's Delight-style food and farming mod for Horizon. It is a **content mod (`.hmod`), no Rust**.
Its crafting machines are data files for **Cookpot** (`https://github.com/realblobii/cookpot`, a library native mod).

## Current state: wait for the feature list

The repo holds instructions only. **Do not add blocks, items, recipes, art, or a mod manifest until the user has
given the feature list** and said to start. When they do, restate the list back as a checklist and build in small
steps. If asked to "start" without a list, ask for it.

Decisions already made (do not re-ask):
- Content mod with no code. If something truly needs code, stop and say what hook or Cookpot feature is missing.
- Machines (cooking pot, cutting board and so on) are **Cookpot machine files**, and recipes are **Cookpot recipe
  files** (`cookpot:machine`, `cookpot:recipe`). Delightful's machine ids are public API for add-ons: once chosen, do not
  rename them.
- Prefer **tags** for heat sources, fuels and ingredient categories so other mods can extend them.
- Singleplayer first.

## Originality (important)

Delightful is "like Farmer's Delight", not a copy of it.
- Do **not** copy Farmer's Delight's textures, models, sounds, lang text, code or data files, and do not download them.
- Draw original textures; use original sounds or vanilla sound events; write original names and descriptions.
- Mechanics and ideas (a cooking pot, a cutting board, crops that grow in a field) are fine to reimplement in our own way.
- Keep a short `CREDITS.md` once there is anything to credit.

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
