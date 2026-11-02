#!/usr/bin/env python3
"""Carries Display Delight's placeable food blocks into `work/displaydelight/`, for the foods Delightful has.

Display Delight (https://github.com/jkvin114/display-delight-neoforge) is LGPL-3.0 with five MIT-licensed models derived from Pder's
"Farmers 3D" pack. Its block `X` shows the food `X` (prefixes: none = Farmer's Delight, `cd_` Corn, `ed_` Expanded; `plated_` a stackable
plate of finger foods, `small_plated_` a slice on a small plate). Here each becomes a block `placed_<name>` with a Roast `placeable`
definition and a loot table that drops the food back. Models and textures are moved under `dd/` so they cannot clash with ours.

    python3 tools/carry_dd.py --src ../src/mods/dd        (after tools/carry.py has filled work/)
NOTHING it makes has been run in Horizon.
"""
import argparse, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = "displaydelight"
OTHER_MODS = ("df_", "pd_", "od_", "ad_", "ctd_", "lm_", "fd_", "bnc_", "acd_", "erd_", "edd_", "mnd_", "nd_", "crd_", "abd_", "fr_", "md_")
VANILLA = {"mushroom_stew", "rabbit_stew", "beetroot_soup", "pumpkin_pie", "cookie"}
ALIASES = {"chinese_cabbages": "cabbages", "chinese_cabbage_crate": "cabbage_crate", "chinese_cabbage_leaf": "cabbage_leaf",
           "chinese_cabbage_seeds": "cabbage_seeds", "chinese_cabbage": "cabbage"}


def jl(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def jd(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def when_props(bs):
    """Property name -> set of values the blockstate's multipart conditions mention."""
    found = {}

    def walk(w):
        if isinstance(w, dict):
            for k, v in w.items():
                if k in ("AND", "OR"):
                    for x in v:
                        walk(x)
                else:
                    found.setdefault(k, set()).update(str(v).split("|"))

    for part in bs.get("multipart", []):
        walk(part.get("when", {}))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    args = ap.parse_args()
    src = Path(args.src)
    res = src / "src/main/resources"
    out = ROOT / "work" / ID
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    ours = set()
    for d in (ROOT / "work").iterdir():
        if d.name == ID or not d.is_dir():
            continue
        for kind in ("item", "block"):
            ours |= {p.stem for p in (d / "data" / d.name / "horizon" / kind).glob("*.json")} if (d / "data" / d.name / "horizon" / kind).exists() else set()
    ours = {ALIASES.get(n, n) for n in ours} | set(ours)

    # stem -> (kind, item)
    chosen = {}
    for f in sorted((res / "assets/displaydelight/blockstates").glob("*.json")):
        s = f.stem
        cp = next((c for c in ("cd_", "ed_") if s.startswith(c)), "")
        if not cp and any(s.startswith(o) for o in OTHER_MODS):
            continue
        r = s[len(cp):]
        kind, item = ("small", r[13:]) if r.startswith("small_plated_") else ("plated", r[7:]) if r.startswith("plated_") else ("direct", r)
        if item in ("plate", "small_plate") or item.endswith("showcase") or item in ("bowl", "food_plate", "small_food_plate"):
            continue
        if item in ours:
            target = f"delightful:{item}"
        elif cp == "" and item in VANILLA:
            target = f"minecraft:{item}"
        else:
            continue
        rank = {"plated": 0, "small": 1, "direct": 2}
        old = chosen.get(target)
        if old is None or rank[kind] < rank[old[0]]:
            chosen[target] = (kind, s)

    models_done, textures_done = set(), set()
    notes = {"blocks": 0, "models": 0, "textures": 0, "skipped": []}

    def move_model(ref):
        """Copies a displaydelight model (and what it needs) under dd/ and returns its new id."""
        ns, _, path = ref.partition(":")
        if ns != ID:
            return ref
        new = re.sub(r"^block/", "block/dd/", path) if path.startswith("block/") else re.sub(r"^item/", "item/dd/", path)
        if ref in models_done:
            return f"{ID}:{new}"
        models_done.add(ref)
        mf = res / "assets" / ID / "models" / f"{path}.json"
        if not mf.exists():
            return f"{ID}:{new}"
        m = jl(mf)
        if "parent" in m:
            m["parent"] = move_model(m["parent"])
        for k, t in list((m.get("textures") or {}).items()):
            if isinstance(t, str) and not t.startswith("#"):
                m["textures"][k] = move_texture(t)
        jd(out / "assets" / ID / "models" / f"{new}.json", m)
        notes["models"] += 1
        return f"{ID}:{new}"

    def move_texture(ref):
        ns, _, path = ref.partition(":")
        if ns != ID:
            return ref
        new = re.sub(r"^(block|item)/", lambda m: f"{m.group(1)}/dd/", path)
        if ref not in textures_done:
            textures_done.add(ref)
            tf = res / "assets" / ID / "textures" / f"{path}.png"
            if tf.exists():
                d = out / "assets" / ID / "textures" / f"{new}.png"
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(tf, d)
                notes["textures"] += 1
                mc = tf.with_suffix(".png.mcmeta")
                if mc.exists():
                    shutil.copyfile(mc, d.with_suffix(".png.mcmeta"))
        return f"{ID}:{new}"

    for target, (kind, stem) in sorted(chosen.items()):
        bs = jl(res / "assets/displaydelight/blockstates" / f"{stem}.json")
        pv = when_props(bs)
        if set(pv) - {"facing", "support", "stacks"}:
            notes["skipped"].append(f"{stem}: unknown property {sorted(set(pv) - {'facing', 'support', 'stacks'})}")
            continue
        name = f"placed_{stem}"
        sp = {}
        if "facing" in pv or "facing=" in "".join(bs.get("variants", {})):
            sp["facing"] = {"type": "enum", "values": ["north", "south", "east", "west"]}
        sp["support"] = {"type": "boolean"}
        top = 1
        if "stacks" in pv:
            top = max(int(v) for v in pv["stacks"] if v.isdigit())
            sp["stacks"] = {"type": "enum", "values": [str(i) for i in range(1, top + 1)]}
        decl = {"template": "minecraft:white_carpet", "item": False, "state_properties": sp}
        decl["default_state"] = {"stacks": "1"} if "stacks" in sp else {}
        if not decl["default_state"]:
            del decl["default_state"]
        jd(out / f"data/{ID}/horizon/block/{name}.json", decl)
        # blockstate with moved models
        def fix(x):
            if isinstance(x, dict) and "model" in x:
                x = dict(x, model=move_model(x["model"]))
            return x
        if "multipart" in bs:
            for part in bs["multipart"]:
                ap_ = part.get("apply")
                part["apply"] = [fix(a) for a in ap_] if isinstance(ap_, list) else fix(ap_)
        jd(out / f"assets/{ID}/blockstates/{name}.json", bs)
        # Roast definition
        jd(out / f"data/{ID}/recipe/{name}.json", {
            "type": "roast:placeable", "item": target, "block": f"{ID}:{name}", "top_only": True, "sneak_to_place": True,
            "take": True, "stack_max": top, "stack_property": "stacks", "sound": "minecraft:block.wool.place"})
        # loot: the food comes back (all stacked items)
        if top > 1:
            entries = [{"type": "minecraft:item", "name": target,
                        "conditions": [{"condition": "minecraft:block_state_property", "block": f"{ID}:{name}", "properties": {"stacks": str(n)}}],
                        "functions": [{"function": "minecraft:set_count", "count": n}]} for n in range(top, 0, -1)]
            pool = {"rolls": 1, "entries": [{"type": "minecraft:alternatives", "children": entries}]}
        else:
            pool = {"rolls": 1, "entries": [{"type": "minecraft:item", "name": target}]}
        jd(out / f"data/{ID}/loot_table/blocks/{name}.json", {"type": "minecraft:block", "pools": [pool]})
        notes["blocks"] += 1

    # manifest and licence
    (out / "horizon-mod.toml").write_text(f'id = "{ID}"\nname = "Display Delight (carried)"\nversion = "0.1.0"\napi = "0.2"\nside = "both"\ncapabilities = ["registries"]\n', encoding="utf-8")
    lines = ["# Carry report: displaydelight", "", "NOTHING here has been run in Horizon.", "",
             f"- placeable foods carried: {notes['blocks']}", f"- models: {notes['models']}, textures: {notes['textures']}",
             f"- skipped: {len(notes['skipped'])}", ""] + [f"- {x}" for x in notes["skipped"]]
    (out / "CARRY-REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:8]))


if __name__ == "__main__":
    sys.exit(main())
