#!/usr/bin/env python3
"""Carries a Java Farmer's Delight-family mod's SOURCE resources into a Horizon content mod (`.hmod` folder).

Why a script: Horizon's own `horizon-port-pack carry` reads a jar and, without the Java "oracle", turns every item into a
stick. This reads the mod's source repository instead, so it can also read food values and item registrations from the
Java code. The output goes in `mods/<id>/`; nothing is written outside it.

    python3 tools/carry.py --src ~/src/mods/FarmersDelight --id farmersdelight --out mods/farmersdelight

Everything it cannot carry is listed in `<out>/CARRY-REPORT.md`. NOTHING it makes has been run in Horizon.
Licence: the source mods are MIT; their LICENSE is copied into the output (`LICENSE-<id>`).
"""
import argparse
import json
import re
import shutil
import sys
from collections import Counter, OrderedDict
from pathlib import Path

# ---------------------------------------------------------------------------------------------------------------------
# Blocks: a vanilla template guessed from the blockstate's properties (the table is Horizon's `horizon-port-pack`).
# ---------------------------------------------------------------------------------------------------------------------
TEMPLATES = [
    ("", "minecraft:stone"), ("axis", "minecraft:oak_log"), ("type,waterlogged", "minecraft:oak_slab"),
    ("facing,half,shape,waterlogged", "minecraft:oak_stairs"), ("facing,half,hinge,open,powered", "minecraft:oak_door"),
    ("facing,half,open,powered,waterlogged", "minecraft:oak_trapdoor"),
    ("east,north,south,waterlogged,west", "minecraft:oak_fence"),
    ("east,north,south,up,waterlogged,west", "minecraft:cobblestone_wall"),
    ("facing,in_wall,open,powered", "minecraft:oak_fence_gate"), ("face,facing,powered", "minecraft:oak_button"),
    ("powered", "minecraft:oak_pressure_plate"), ("facing", "minecraft:carved_pumpkin"),
    ("facing,lit", "minecraft:furnace"), ("lit", "minecraft:redstone_lamp"), ("waterlogged", "minecraft:chain"),
    ("age", "minecraft:wheat"), ("distance,persistent,waterlogged", "minecraft:oak_leaves"),
    ("stage", "minecraft:oak_sapling"),
]
# Crops by how many growth stages their blockstate has (age 0..N).
CROP_BY_MAX_AGE = {3: "minecraft:beetroots", 7: "minecraft:wheat"}

# The machines Cookpot provides for Farmer's Delight (see docs/FEATURES.md). Their blocks use the furnace as template
# because it has a block entity and a horizontal `facing`.
INCLUDED = {"farmersdelight", "expandeddelight", "corn_delight", "brewinandchewin", "rusticdelight"}
MACHINE_BLOCKS = {"cooking_pot": "farmersdelight:cooking_pot", "cutting_board": "farmersdelight:cutting_board"}


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def jdump(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def props_of(blockstate):
    names = set()
    for key in blockstate.get("variants", {}):
        for kv in key.split(","):
            if "=" in kv:
                names.add(kv.split("=")[0])

    def walk(w):
        if isinstance(w, dict):
            for k, v in w.items():
                if k in ("AND", "OR"):
                    for x in v:
                        walk(x)
                else:
                    names.add(k)

    for part in blockstate.get("multipart", []):
        walk(part.get("when", {}))
    return names


def values_of(blockstate, prop):
    vals = set()
    for key in blockstate.get("variants", {}):
        for kv in key.split(","):
            if kv.startswith(prop + "="):
                vals.add(kv.split("=", 1)[1])
    return vals


def enum_prop(bs, prop):
    vals = sorted(values_of(bs, prop))
    if set(vals) <= {"true", "false"}:
        return {"type": "boolean"}
    return {"type": "enum", "values": vals}


def decide(name, bs):
    """(template, extra state properties) for a block, or (None, reason) when it is left out."""
    props = props_of(bs)
    if "sign" in name:
        return None, "signs need a text-editing block entity"
    if name.endswith("_cabinet") or name.endswith("_basket") or name == "rice_bale":
        return "minecraft:barrel", {}
    if props == {"half"}:
        return "minecraft:tall_grass", {}
    if props == {"facing"}:
        return "minecraft:glazed_terracotta", {}
    if props == {"moisture"}:
        return "minecraft:farmland", {}
    if "servings" in props:
        return None, "feast blocks (servings taken with a bowl) need behaviour Horizon's templates lack"
    if props == {"bites", "facing"}:
        return "minecraft:cake", {"facing": enum_prop(bs, "facing")}
    if "age" in props and props - {"age", "half"}:
        ages = [int(a) for a in values_of(bs, "age") if a.isdigit()]
        base = CROP_BY_MAX_AGE.get(max(ages)) if ages else None
        extra = props - {"age"}
        if base and not (extra & {"half"}):
            return base, {k: enum_prop(bs, k) for k in sorted(extra)}
    t = guess_template(name, bs)
    if t is None:
        return None, "no template for properties [%s]" % ", ".join(sorted(props))
    return t, {}


def augment_facing(bs):
    """A horizontal-only blockstate gets the up and down facings a barrel can have."""
    vs = bs.get("variants", {})
    for key, v in list(vs.items()):
        if "facing=north" in key:
            for face, x in (("up", 270), ("down", 90)):
                vs[key.replace("facing=north", f"facing={face}")] = dict(v, x=x)
    return bs


def guess_template(name, bs):
    props = props_of(bs)
    if "age" in props:
        ages = [int(a) for a in values_of(bs, "age") if a.isdigit()]
        if ages and max(ages) in CROP_BY_MAX_AGE and props <= {"age", "half"}:
            return CROP_BY_MAX_AGE[max(ages)]
    best = None
    for key, template in TEMPLATES:
        have = {p for p in key.split(",") if p}
        if props <= have:
            hint = not name.endswith("_" + template.rsplit("_", 1)[-1])
            score = (len(have) - len(props), hint)
            if best is None or score < best[0]:
                best = (score, template)
    return best[1] if best else None


# ---------------------------------------------------------------------------------------------------------------------
# Items: read from the Java registrations and food values.
# ---------------------------------------------------------------------------------------------------------------------
def parse_foods(java_text, consts):
    foods = {}
    for m in re.finditer(r"public static final FoodProperties (\w+)\s*=(.*?);\s*(?=\n\s*(?:public|//|/\*|\}|$))", java_text, re.S):
        foods[m.group(1)] = body_to_food(m.group(2), consts)
    return foods


def body_to_food(body, consts):
    if True:
        nut = re.search(r"\.nutrition\((\d+)\)", body)
        sat = re.search(r"\.saturationModifier\(([\d.]+)[fF]?\)", body)
        food = {"nutrition": int(nut.group(1)) if nut else 0}
        food["saturation"] = round(food["nutrition"] * float(sat.group(1)) * 2, 3) if sat else 0.0
        if "alwaysEdible()" in body:
            food["can_always_eat"] = True
        effects = []
        for e in re.finditer(r"\.effect\(\s*\(\)\s*->\s*(.*?),\s*([\d.]+)[fF]?\s*\)", body, re.S):
            expr, chance = e.group(1), float(e.group(2))
            inst = re.search(r"MobEffects\.(\w+)\s*,\s*([\w.]+)\s*(?:,\s*(\d+))?", expr)
            mod = re.search(r"(nourishment|comfort)\(\s*(\w+|\d+)\s*\)", expr)
            if inst:
                effects.append({"id": "minecraft:" + inst.group(1).lower(), "duration": consts.get(inst.group(2), int(inst.group(2)) if inst.group(2).isdigit() else 600),
                                "amplifier": int(inst.group(3) or 0), "chance": chance})
            elif mod:
                d = mod.group(2)
                effects.append({"id": "farmersdelight:" + mod.group(1), "duration": consts.get(d, int(d) if d.isdigit() else 3600), "amplifier": 0, "chance": chance})
        return {"food": food, "fast": ".fast()" in body, "effects": effects}


def consumable(entry, drink):
    c = {"consume_seconds": 0.8 if entry["fast"] else 1.6, "animation": "drink" if drink else "eat",
         "sound": "minecraft:entity.generic.drink" if drink else "minecraft:entity.generic.eat"}
    by_chance = OrderedDict()
    for e in entry["effects"]:
        by_chance.setdefault(e["chance"], []).append({"id": e["id"], "duration": e["duration"], "amplifier": e["amplifier"]})
    if by_chance:
        c["on_consume_effects"] = [{"type": "minecraft:apply_effects", "effects": fx, "probability": ch} for ch, fx in by_chance.items()]
    return c


def parse_items(java_text):
    """Item registrations by statement: the first lower-case string literal is the item's name. Works for field
    initialisers, `register("name", ...)` calls and `Registry.register(..., asResource("name"), item)` alike."""
    items = OrderedDict()
    for stmt in java_text.split(";"):
        names = re.findall(r'"([a-z][a-z0-9_]*)"', stmt)
        if not names or "FoodProperties" in stmt and "static final FoodProperties" in stmt:
            continue
        if not re.search(r"\b(new \w*Item|register\w*\(|Items?\.|Item\()", stmt):
            continue
        name = names[0]
        if name in items:
            continue
        food = re.search(r"\b(?:FoodValues|\w*Foods?|\w*FoodProperties)\.(\w+)", stmt)
        inline = stmt[stmt.index("nutrition("):] if "nutrition(" in stmt and not food else None
        stack = re.search(r"stacksTo\((\d+)\)", stmt)
        items[name] = {
            "tab": "idden" not in stmt.split("(")[0], "food": food.group(1) if food else None, "inline": inline,
            "stack": int(stack.group(1)) if stack else None,
            "bowl": "bowlFoodItem" in stmt or "BOWL" in stmt and "craftRemainder" in stmt,
            "drink": "drinkItem" in stmt or "DrinkableItem" in stmt,
            "knife": "knifeItem" in stmt or "KnifeItem" in stmt,
            "block_item": "BlockItem(" in stmt or "ModBlocks." in stmt or "Blocks." in stmt,
            "expr": " ".join(stmt.split())[:160],
        }
    return items


# ---------------------------------------------------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------------------------------------------------
def ingredient(v):
    """A 1.21.1 ingredient as 26.3's, or None when it has no such form."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict) and len(v) == 1:
        if "item" in v:
            return v["item"]
        if "tag" in v:
            return "#" + v["tag"]
        return None
    if isinstance(v, list):
        ids = []
        for x in v:
            if not (isinstance(x, dict) and len(x) == 1 and "item" in x):
                return None
            ids.append(x["item"])
        return ids[0] if len(ids) == 1 else ids
    return None


def upgrade_vanilla(recipe):
    out = json.loads(json.dumps(recipe))
    for key in list(out.get("key", {})):
        n = ingredient(out["key"][key])
        if n is None:
            return None
        out["key"][key] = n
    if "ingredients" in out:
        new = [ingredient(x) for x in out["ingredients"]]
        if None in new:
            return None
        out["ingredients"] = new
    for f in ("ingredient", "base", "addition", "template"):
        if f in out:
            n = ingredient(out[f])
            if n is None:
                return None
            out[f] = n
    return out


def simple_ingredient(v, rep=None):
    """A Cookpot-readable ingredient: NeoForge's `difference` becomes its base (an approximation), `compound` its parts."""
    if isinstance(v, dict) and v.get("type") == "neoforge:difference":
        if rep is not None:
            rep["unsupported"]["ingredient 'difference' approximated by its base"] += 1
        return simple_ingredient(v["base"], rep)
    if isinstance(v, dict) and v.get("type") == "neoforge:compound":
        v = v.get("children", [])
    if isinstance(v, list):
        out = []
        for x in v:
            x = simple_ingredient(x, rep)
            if isinstance(x, dict) and len(x) == 1 and "item" in x:
                out.append(x["item"])
            elif isinstance(x, dict) and len(x) == 1 and "tag" in x:
                out.append("#" + x["tag"])
            elif isinstance(x, (str, list)):
                out += x if isinstance(x, list) else [x]
        return out
    return v


def result_stack(v):
    """A farmersdelight result entry as a Cookpot result, and its chance (1.0 when none)."""
    chance = 1.0
    if isinstance(v, dict):
        chance = float(v.get("chance", 1.0))
        v = v.get("item", v)
    if isinstance(v, dict):
        rid = v.get("id") or v.get("item")
        return {"id": rid, "count": int(v.get("count", 1))}, chance
    return {"id": v, "count": 1}, chance


# ---------------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="a source mod repository")
    ap.add_argument("--id", required=True, help="the mod id (its resource namespace)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--registry", default=None, help="Java file with the item registrations (default: found by name)")
    args = ap.parse_args()
    src, mid, out = Path(args.src), args.id, Path(args.out)
    base = src / "common" if (src / "common/src").exists() else src
    roots = [r for r in (base / "src/main/resources", base / "src/generated/resources") if r.exists()]
    java_root = base / "src/main/java"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rep = {"copied": 0, "unsupported": Counter(), "notes": [], "blocks": {}, "blocks_unknown": {}, "items": 0,
           "recipes": Counter(), "recipes_skipped": []}

    # ---- locate the Java sources
    java_files = [p for p in java_root.rglob("*.java") if "compat" not in p.as_posix().lower()]
    regs = [Path(args.registry)] if args.registry else [p for p in java_files if re.search(r"Item", p.name) and p.name.endswith(("Items.java", "ItemRegistry.java", "Registry.java")) and "Block" not in p.name]
    items = OrderedDict()
    for reg in regs:
        items.update(parse_items(reg.read_text(encoding="utf-8")))
    consts = {}
    foods = {}
    for foods_file in [p for p in java_files if "FoodProperties" in p.read_text(encoding="utf-8", errors="ignore")]:
        text = foods_file.read_text(encoding="utf-8")
        for m in re.finditer(r"int (\w+_DURATION)\s*=\s*(\d+)", text):
            consts[m.group(1)] = int(m.group(2))
        foods.update(parse_foods(text, consts))

    # ---- merged resource view: relative path -> file (generated wins over main only when main lacks it)
    files = {}
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file():
                files.setdefault(p.relative_to(root).as_posix(), p)

    def copy(rel, dest=None):
        d = out / (dest or rel)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(files[rel], d)
        rep["copied"] += 1

    # ---- assets: models, textures, blockstates, particles, sounds, English text
    skip_dirs = ("/jei/", "/emi/")
    for rel in sorted(files):
        if not rel.startswith(f"assets/{mid}/"):
            continue
        sub = rel[len(f"assets/{mid}/"):]
        if sub.startswith("lang/") and sub != "lang/en_us.json":
            continue
        if any(s in rel for s in skip_dirs):
            continue
        if sub.startswith("items/"):
            continue
        copy(rel)

    # ---- blocks
    blockstates = {Path(r).stem: jload(p) for r, p in files.items() if r.startswith(f"assets/{mid}/blockstates/")}
    block_names = set(blockstates)
    blocks_out = {}
    for name, bs in sorted(blockstates.items()):
        if mid == "farmersdelight" and name in MACHINE_BLOCKS:
            decl = {"template": "minecraft:furnace", "item": True,
                    "state_properties": ({"support": {"type": "enum", "values": ["none", "tray", "handle"]}} if name == "cooking_pot" else {}),
                    "components": {"minecraft:max_stack_size": 1} if name == "cooking_pot" else {}}
            decl = {k: v for k, v in decl.items() if v != {}}
            blocks_out[name] = decl
            rep["blocks"][name] = "minecraft:furnace (Cookpot machine)"
            continue
        t, extra = decide(name, bs)
        if t is None:
            rep["blocks_unknown"][name] = extra
            continue
        decl = {"template": t, "item": True}
        if extra:
            decl["state_properties"] = extra
        blocks_out[name] = decl
        rep["blocks"][name] = t
    for name, decl in blocks_out.items():
        jdump(out / f"data/{mid}/horizon/block/{name}.json", decl)
    # Cabinets become barrels, which can face up and down.
    for name in blocks_out:
        if name.endswith("_cabinet"):
            p = out / f"assets/{mid}/blockstates/{name}.json"
            jdump(p, augment_facing(jload(p)))
    # Assets of blocks that were left out are not shipped.
    for name in block_names - set(blocks_out):
        for sub in (f"assets/{mid}/blockstates/{name}.json",):
            (out / sub).unlink(missing_ok=True)

    # ---- loot tables of declared blocks (copied as they are: UNVERIFIED against 26.3; custom functions are skipped)
    for rel in sorted(files):
        m = re.match(rf"data/{mid}/loot_tables?/blocks/(.+)\.json$", rel)
        if not m or m.group(1) not in blocks_out:
            continue
        text = files[rel].read_text(encoding="utf-8")
        if f'"{mid}:' in text and re.search(rf'"(function|condition|type)":\s*"{mid}:', text):
            rep["unsupported"]["loot tables using the mod's own functions or conditions skipped"] += 1
            continue
        copy(rel, f"data/{mid}/loot_table/blocks/{m.group(1)}.json")

    # ---- items (those that are not a block's item)
    item_models = {Path(r).stem for r in files if r.startswith(f"assets/{mid}/models/item/")}
    declared_items = {}
    for name, it in items.items():
        if name in blocks_out or name in block_names:
            continue
        if it["block_item"] and name not in item_models:
            rep["unsupported"]["item for a block that was left out"] += 1
            continue
        comps = {}
        template = "minecraft:stick"
        if it.get("inline") and not it["food"]:
            foods[f"@{name}"] = body_to_food(it["inline"], consts)
            it["food"] = f"@{name}"
        if it["food"] and it["food"] in foods:
            f = foods[it["food"]]
            template = "minecraft:bread"
            comps["minecraft:food"] = f["food"]
            comps["minecraft:consumable"] = consumable(f, it["drink"])
            if it["bowl"]:
                comps["minecraft:use_remainder"] = {"id": "minecraft:bowl"}
            elif it["drink"]:
                comps["minecraft:use_remainder"] = {"id": "minecraft:glass_bottle"}
        elif it["knife"]:
            template = "minecraft:iron_sword"
            rep["unsupported"]["knife stats (a plain iron sword stands in)"] += 1
        if it["stack"]:
            comps["minecraft:max_stack_size"] = it["stack"]
        decl = {"template": template}
        if comps:
            decl["components"] = comps
        if it["bowl"]:
            decl["crafting_remainder"] = "minecraft:bowl"
        elif it["drink"] and "minecraft:food" not in comps:
            decl["crafting_remainder"] = "minecraft:glass_bottle"
        declared_items[name] = decl
        jdump(out / f"data/{mid}/horizon/item/{name}.json", decl)
        rep["items"] += 1
    # models of items nobody registered in Java code that have a model and no block: sticks, so nothing is missing
    # item model definitions (1.21.4 moved item models behind items/<name>.json)
    for name in sorted(set(declared_items) | set(blocks_out)):
        if name in item_models:
            jdump(out / f"assets/{mid}/items/{name}.json", {"model": {"type": "minecraft:model", "model": f"{mid}:item/{name}"}})

    # ---- mob effects the foods use (no behaviour yet: Horizon's mob effects do nothing on their own)
    used_effects = {e["id"].split(":")[1] for f in foods.values() for e in f["effects"] if e["id"].startswith(mid + ":")}
    for eff in sorted(used_effects):
        jdump(out / f"data/{mid}/horizon/mob_effect/{eff}.json", {"category": "beneficial", "color": 14390528})
        rep["unsupported"][f"effect {eff} has no behaviour in Horizon"] += 1

    # ---- creative tab, in the mod's own order
    tab = [f"{mid}:{n}" for n, it in items.items() if it["tab"] and (n in declared_items or n in blocks_out)]
    for n in sorted(blocks_out):
        if f"{mid}:{n}" not in tab:
            tab.append(f"{mid}:{n}")
    icon = f"{mid}:cooking_pot" if "cooking_pot" in blocks_out else (tab[0] if tab else "minecraft:stick")
    if not tab:
        jdump(out / f"data/{mid}/horizon/creative_tab/{mid}.json", {"title": mid, "icon": "minecraft:stick", "items": []})
    jdump(out / f"data/{mid}/horizon/creative_tab/{mid}.json", {"title": f"itemGroup.{mid}", "icon": icon, "items": tab})
    lang_path = out / f"assets/{mid}/lang/en_us.json"
    lang = jload(lang_path) if lang_path.exists() else {}
    lang.setdefault(f"itemGroup.{mid}", "Farmer's Delight" if mid == "farmersdelight" else mid)
    jdump(lang_path, lang)

    # ---- tags
    for rel in sorted(files):
        m = re.match(r"data/(%s|c|minecraft)/tags/" % re.escape(mid), rel)
        if m:
            copy(rel)

    # ---- recipes
    machine_slots = {"cooking_pot": 0, "cutting_board": 0}
    cut_outputs = 0
    for rel in sorted(files):
        m = re.match(rf"data/{mid}/recipes?/(.+)\.json$", rel)
        if not m:
            continue
        name = m.group(1)
        if name.startswith("integration/") or "/integration/" in name:
            rep["recipes_skipped"].append(f"{name}: integration with another mod")
            continue
        r = jload(files[rel])
        kind = r.get("type", "")
        if "neoforge:conditions" in r:
            keep = []
            for c in r["neoforge:conditions"]:
                if c.get("type", "").endswith(":config_boolean"):
                    continue  # the mod's own on/off settings: everything is on (Delightful's settings menu decides later)
                if c.get("type") == "neoforge:mod_loaded" and c.get("modid") in INCLUDED:
                    continue
                keep.append(c)
            if keep:
                rep["recipes_skipped"].append(f"{name}: needs {keep[0].get('type')} {keep[0].get('modid', keep[0].get('settingId', ''))}")
                continue
            r = {k: v for k, v in r.items() if k != "neoforge:conditions"}
        dest = out / f"data/{mid}/recipe/{name}.json"
        res = r.get("result")
        rid = res.get("id") if isinstance(res, dict) else (res if isinstance(res, str) else None)
        if rid and rid.startswith(mid + ":") and rid.split(":", 1)[1] not in set(blocks_out) | set(declared_items):
            rep["recipes_skipped"].append(f"{name}: makes {rid}, which is left out")
            continue
        if kind.startswith("minecraft:"):
            new = upgrade_vanilla(r)
            if new is None:
                rep["recipes_skipped"].append(f"{name}: ingredient has no 26.3 form")
                continue
            jdump(dest, new)
            rep["recipes"]["vanilla"] += 1
        elif kind == "farmersdelight:cooking":
            ins = [simple_ingredient(x, rep) for x in r.get("ingredients", [])]
            rec = {"type": "cookpot:recipe", "machine": "farmersdelight:cooking_pot", "inputs": ins,
                   "results": [result_stack(r["result"])[0]], "experience": r.get("experience", 0.0),
                   "time": r.get("cookingtime", 200)}
            if r.get("container"):
                c = r["container"]
                rec["container"] = c.get("id") or c.get("item") if isinstance(c, dict) else c
            jdump(dest, rec)
            rep["recipes"]["cooking pot"] += 1
        elif kind == "farmersdelight:cutting":
            ing = [simple_ingredient(x, rep) for x in r.get("ingredients", [])]
            results, dropped = [], 0
            for x in r.get("result", []):
                stack, chance = result_stack(x)
                if chance >= 1.0:
                    results.append(stack)
                else:
                    dropped += 1
            if not ing or not results:
                rep["recipes_skipped"].append(f"{name}: no certain result")
                continue
            if dropped:
                rep["unsupported"]["cutting chances below 100% dropped"] += dropped
            cut_outputs = max(cut_outputs, len(results))
            jdump(dest, {"type": "cookpot:recipe", "machine": "farmersdelight:cutting_board", "inputs": ing[:1], "results": results})
            rep["recipes"]["cutting board"] += 1
        else:
            rep["recipes_skipped"].append(f"{name}: type {kind} is not supported")

    # ---- machines (Cookpot)
    if mid == "farmersdelight" and "cooking_pot" in blocks_out:
        slots = [{"id": f"in{i}", "role": "input", "pos": [30 + 18 * (i % 3), 17 + 18 * (i // 3)]} for i in range(6)]
        slots += [{"id": "bowl", "role": "container", "pos": [92, 55]}, {"id": "out", "role": "output", "pos": [124, 26]}]
        jdump(out / f"data/{mid}/recipe/cooking_pot.json", {
            "type": "cookpot:machine", "block": f"{mid}:cooking_pot", "menu": f"{mid}:cooking_pot", "data_slots": 4,
            "heat": {"offset": [0, -1, 0], "sources": [
                "minecraft:campfire[lit=true]", "minecraft:soul_campfire[lit=true]", "minecraft:furnace[lit=true]",
                "minecraft:blast_furnace[lit=true]", "minecraft:smoker[lit=true]", "#%s:heat_sources" % mid]},
            "process": {"default_time": 200},
            "sounds": {"working": {"id": "minecraft:block.campfire.crackle", "interval": 40, "volume": 0.5},
                       "done": "minecraft:entity.experience_orb.pickup"},
            "gui": {"size": [176, 166], "texture": f"{mid}:gui/cooking_pot", "slots": slots,
                    "progress": {"pos": [89, 30], "size": [24, 6]}}})
        jdump(out / f"data/{mid}/horizon/menu/cooking_pot.json", {"slots": 8, "data_slots": 4, "results": [7]})
    if mid == "farmersdelight" and "cutting_board" in blocks_out:
        n = max(cut_outputs, 1)
        slots = [{"id": "in", "role": "input", "pos": [44, 35]}] + [
            {"id": f"out{i}", "role": "output", "pos": [98 + 18 * (i % 3), 26 + 18 * (i // 3)]} for i in range(n)]
        jdump(out / f"data/{mid}/recipe/cutting_board.json", {
            "type": "cookpot:machine", "block": f"{mid}:cutting_board", "menu": f"{mid}:cutting_board", "data_slots": 0,
            "mode": "instant", "sounds": {"done": "minecraft:block.wood.hit"}, "gui": {"slots": slots}})
        jdump(out / f"data/{mid}/horizon/menu/cutting_board.json", {"slots": 1 + n, "data_slots": 0, "results": list(range(1, 1 + n))})

    # ---- manifest, licence, credits
    (out / "horizon-mod.toml").write_text(
        f'id = "{mid}"\nname = "{mid} (Delightful carry)"\nversion = "0.1.0"\n'
        f'description = "Carried from {mid}\'s MIT-licensed source by Delightful\'s tools/carry.py. Not run in Horizon yet."\n'
        'authors = ["Delightful"]\napi = "0.2"\nside = "both"\ncapabilities = ["registries"]\n', encoding="utf-8")
    lic = next((src / n for n in ("LICENSE", "LICENSE.txt", "LICENSE.md") if (src / n).exists()), None)
    if lic:
        shutil.copyfile(lic, out / f"LICENSE-{mid}")

    # ---- report
    lines = [f"# Carry report: {mid}", "", "NOTHING here has been run in Horizon.", "",
             f"- files copied: {rep['copied']}", f"- blocks declared: {len(rep['blocks'])}, left out: {len(rep['blocks_unknown'])}",
             f"- items declared: {rep['items']}", f"- recipes: {dict(rep['recipes'])}",
             f"- recipes skipped: {len(rep['recipes_skipped'])}", "", "## Not carried or approximated"]
    lines += [f"- {k}: {v}" for k, v in sorted(rep["unsupported"].items())] or ["- (none)"]
    lines += ["", "## Blocks left out"] + ([f"- {k}: {v}" for k, v in sorted(rep["blocks_unknown"].items())] or ["- (none)"])
    lines += ["", "## Recipes skipped"] + ([f"- {x}" for x in rep["recipes_skipped"]] or ["- (none)"])
    lines += ["", "## Block templates", ""] + [f"- {k}: {v}" for k, v in sorted(rep["blocks"].items())]
    (out / "CARRY-REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:14]))


if __name__ == "__main__":
    sys.exit(main())
