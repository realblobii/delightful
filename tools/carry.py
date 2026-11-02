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
INCLUDED = {"farmersdelight", "expandeddelight", "corn_delight", "rusticdelight", "cratedelight", "storagedelight", "dumplings_delight"}
MACHINE_BLOCKS = {"cooking_pot": "farmersdelight:cooking_pot", "cutting_board": "farmersdelight:cutting_board"}


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


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


SPECIAL = {}  # block name -> {"kind": "feast"|"pie", ...} read from the Java registrations


def parse_special_blocks(java_files):
    """Feast and pie blocks from the Java block registrations: their serving or slice item and whether a feast leaves a dish."""
    feast_classes = {"FeastBlock", "RotatedFeastBlock"}
    texts = {p: p.read_text(encoding="utf-8", errors="ignore") for p in java_files}
    for t in texts.values():
        for m in re.finditer(r"class (\w+) extends (?:Rotated)?FeastBlock", t):
            feast_classes.add(m.group(1))
    # A feast subclass may name its serving in its own constructor: `super(properties, Items.X, true)`.
    class_info = {}
    for t in texts.values():
        for m in re.finditer(r"class (\w+) extends (?:Rotated)?FeastBlock", t):
            sup = re.search(r"super\(([^;]*?)\);", t[m.end():], re.S)
            if sup:
                item = re.search(r"\b[A-Za-z]*(?:Items?|Registry)\.([A-Z][A-Z0-9_]+)", sup.group(1))
                if item:
                    flag = re.search(r"\b(true|false)\b", sup.group(1)[item.end():])
                    class_info[m.group(1)] = {"kind": "feast", "serving": item.group(1).lower(), "leftovers": (flag.group(1) == "true") if flag else True}
    out = {}
    for t in texts.values():
        for stmt in t.split(";"):
            m = re.search(r'"([a-z][a-z0-9_]*)"\s*,\s*\(\)\s*->\s*new (\w+)\(', stmt)
            if not m:
                continue
            name, cls = m.group(1), m.group(2)
            item = re.search(r"\b[A-Za-z]*(?:Items?|Registry)\.([A-Z][A-Z0-9_]+)", stmt)
            if cls in class_info and not item:
                out[name] = dict(class_info[cls])
            elif cls in feast_classes and item:
                after = stmt[item.end():]
                flag = re.search(r"\b(true|false)\b", after)
                out[name] = {"kind": "feast", "serving": item.group(1).lower(), "leftovers": (flag.group(1) == "true") if flag else True}
            elif cls == "PieBlock" and item:
                out[name] = {"kind": "pie", "slice": item.group(1).lower()}
    return out


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
    if name.endswith("_cabinet") or name.endswith("_basket") or name == "rice_bale" or props == {"facing", "open"}:
        return "minecraft:barrel", {}
    if props == {"half"}:
        return "minecraft:tall_grass", {}
    if props == {"facing"}:
        return "minecraft:glazed_terracotta", {}
    if props == {"moisture"}:
        return "minecraft:farmland", {}
    sp = SPECIAL.get(name)
    if sp and sp["kind"] == "feast" and props <= {"facing", "servings"} and "servings" in props:
        extra = {"servings": enum_prop(bs, "servings")}
        return ("minecraft:glazed_terracotta" if "facing" in props else "minecraft:stone"), extra
    if sp and sp["kind"] == "pie" and props <= {"bites", "facing"} and "bites" in props:
        return ("minecraft:glazed_terracotta" if "facing" in props else "minecraft:stone"), {"bites": enum_prop(bs, "bites")}
    if "servings" in props:
        return None, "a feast block this tool could not read the serving item of"
    if props == {"bites", "facing"}:
        return None, "a pie block this tool could not read the slice item of"
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
# Java field names of effects that 26.3 ids spell differently.
EFFECT_IDS = {"movement_speed": "speed", "movement_slowdown": "slowness", "dig_speed": "haste", "dig_slowdown": "mining_fatigue",
              "confusion": "nausea", "jump": "jump_boost", "damage_boost": "strength", "damage_resistance": "resistance",
              "heal": "instant_health", "harm": "instant_damage"}


def effect_id(java_name):
    n = java_name.lower()
    return "minecraft:" + EFFECT_IDS.get(n, n)


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
                effects.append({"id": effect_id(inst.group(1)), "duration": consts.get(inst.group(2), int(inst.group(2)) if inst.group(2).isdigit() else 600),
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


# Expanded Delight builds foods with helper functions (EDItems.stewItem and so on); each adds fixed effects.
HELPER_EFFECTS = {"stewItem": ("farmersdelight:comfort", 2400), "mealItem": ("farmersdelight:nourishment", 3600),
                  "saladItem": ("minecraft:regeneration", 100), "jellyItem": (None, 400), "drinkItem": (None, 200),
                  "pieSliceItem": ("minecraft:speed", 600)}


def HELPER_FOODS(m):
    """A builder body (as body_to_food reads it) for `foodItem(n, s)`, `stewItem(n, s)`, `drinkItem(n, s, EFFECT)` ..."""
    kind, n, sat, eff = m.group(1), m.group(2), m.group(3), m.group(4)
    body = f".nutrition({n}).saturationModifier({sat})"
    fx, ticks = HELPER_EFFECTS.get(kind, (None, 0))
    if kind in ("drinkItem", "jellyItem") and eff:
        fx = "minecraft:" + eff.lower()
    if kind == "pieSliceItem":
        body += ".fast()"
    if fx:
        ns, nm = fx.split(":")
        if ns == "minecraft":
            body += f".effect(() -> new MobEffectInstance(MobEffects.{nm.upper()}, {ticks}, 0), 1.0f)"
        else:
            body += f".effect(() -> ModEffects.{nm}({ticks}), 1.0f)"
    return body


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
        food = re.search(r"\b(?:\w*FoodValues|\w*Foods?|\w*FoodProperties)\.(\w+)", stmt)
        inline = stmt[stmt.index("nutrition("):] if "nutrition(" in stmt and not food else None
        helper = re.search(r"\b(foodItem|stewItem|mealItem|saladItem|pieSliceItem|drinkItem|jellyItem)\(\s*(\d+)\s*,\s*([\d.]+)[fF]?\s*(?:,\s*(?:MobEffects\.)?(\w+))?\s*\)", stmt)
        calories = re.search(r"amountAndCalories\(\s*(\d+)\s*,\s*([\d.]+)[fF]?\s*\)", stmt)
        if helper and not inline:
            inline, food = HELPER_FOODS(helper), None
        elif calories and not inline:
            inline, food = f".nutrition({calories.group(1)}).saturationModifier({calories.group(2)})", None
        stack = re.search(r"stacksTo\((\d+)\)", stmt)
        items[name] = {
            "tab": "idden" not in stmt.split("(")[0], "food": food.group(1) if food else None, "inline": inline,
            "stack": int(stack.group(1)) if stack else (16 if helper and helper.group(1) in ("stewItem", "mealItem", "saladItem", "drinkItem", "jellyItem") else None),
            "bowl": "bowlFoodItem" in stmt or "BOWL" in stmt and "craftRemainder" in stmt
                    or bool(helper and helper.group(1) in ("stewItem", "mealItem", "saladItem")),
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
# Wild crops: the mods' own worldgen types (`farmersdelight:wild_crop`, a random patch) are Java code, so they are rewritten as
# plain 26.3 features: a `simple_block` placed by a count of attempts, an offset and a ground test. NOT TESTED in Horizon.
# ---------------------------------------------------------------------------------------------------------------------
BIOME_TAGS = {  # NeoForge convention tags Horizon does not have, as vanilla biome lists (a rough mapping)
    "is_hot/overworld": ["minecraft:desert", "minecraft:savanna", "minecraft:savanna_plateau", "minecraft:badlands", "minecraft:eroded_badlands", "minecraft:wooded_badlands", "minecraft:jungle", "minecraft:sparse_jungle", "minecraft:bamboo_jungle"],
    "is_wet/overworld": ["minecraft:swamp", "minecraft:mangrove_swamp", "minecraft:jungle", "minecraft:bamboo_jungle", "minecraft:river", "minecraft:beach"],
    "is_mushroom": ["minecraft:mushroom_fields"], "is_desert": ["minecraft:desert"],
    "is_jungle": ["minecraft:jungle", "minecraft:sparse_jungle", "minecraft:bamboo_jungle"],
    "is_plains": ["minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow"],
    "is_savanna": ["minecraft:savanna", "minecraft:savanna_plateau", "minecraft:windswept_savanna"],
    "is_swamp": ["minecraft:swamp", "minecraft:mangrove_swamp"],
    "is_ocean": ["minecraft:ocean", "minecraft:deep_ocean", "minecraft:cold_ocean", "minecraft:deep_cold_ocean", "minecraft:lukewarm_ocean", "minecraft:deep_lukewarm_ocean", "minecraft:warm_ocean"],
    "is_forest": ["minecraft:forest", "minecraft:flower_forest", "minecraft:birch_forest", "minecraft:old_growth_birch_forest", "minecraft:dark_forest"],
}


def carry_worldgen(files, mid, blocks_out, out, rep):
    def load(prefix):
        return {Path(r).stem: (jload(p), r) for r, p in files.items() if re.match(rf"data/{mid}/{prefix}/[^/]+\.json$", r)}
    configured, placed, mods = load("worldgen/configured_feature"), load("worldgen/placed_feature"), load("neoforge/biome_modifier")
    made, skipped = {}, Counter()
    for name, (c, _) in configured.items():
        t, conf = c.get("type", ""), c.get("config", {})
        primary = conf.get("primary_feature") if t.endswith(":wild_crop") else conf.get("feature") if t == "minecraft:random_patch" else None
        if not primary:
            skipped[f"configured feature type {t}"] += 1
            continue
        feat = primary.get("feature", {})
        tp = (feat.get("config") or {}).get("to_place", {})
        state = tp.get("state") if isinstance(tp, dict) and "state" in tp else tp
        block = state.get("Name") if isinstance(state, dict) else None
        if feat.get("type") != "minecraft:simple_block" or not block or not block.startswith(mid + ":") or block.split(":")[1] not in blocks_out:
            skipped["wild crop whose block is not carried or is not a simple block"] += 1
            continue
        predicate = next((m["predicate"] for m in primary.get("placement", []) if m.get("type") == "minecraft:block_predicate_filter"), None)
        if predicate is None:
            skipped["wild crop without a ground test"] += 1
            continue
        made[name] = {"block": block, "predicate": predicate, "tries": int(conf.get("tries", 32)),
                      "xz": int(conf.get("xz_spread", 6)), "y": int(conf.get("y_spread", 3))}
    wild_features = set()
    for pname, (pf, _) in placed.items():
        ref = pf.get("feature")
        if not (isinstance(ref, str) and ref.startswith(mid + ":") and ref.split(":")[1] in made):
            skipped["placed feature of something not carried"] += 1
            continue
        info = made[ref.split(":")[1]]
        keep = []
        for m in pf.get("placement", []):
            t = m.get("type", "")
            if t in ("minecraft:rarity_filter", "minecraft:in_square", "minecraft:heightmap"):
                keep.append(m)
            elif t.endswith("configurable_rarity_filter"):
                keep.append({"type": "minecraft:rarity_filter", "chance": 30})
        keep += [
            {"type": "minecraft:count", "count": info["tries"]},
            {"type": "minecraft:offset", "x": {"type": "minecraft:uniform", "min_inclusive": -info["xz"], "max_inclusive": info["xz"]},
             "y": {"type": "minecraft:uniform", "min_inclusive": -info["y"], "max_inclusive": info["y"]},
             "z": {"type": "minecraft:uniform", "min_inclusive": -info["xz"], "max_inclusive": info["xz"]}},
            {"type": "minecraft:block_predicate_filter", "predicate": info["predicate"]},
            {"type": "minecraft:biome"},
        ]
        jdump(out / f"data/{mid}/worldgen/configured_feature/{ref.split(':')[1]}.json", {"type": "minecraft:simple_block", "to_place": {"Name": info["block"]}})
        jdump(out / f"data/{mid}/worldgen/placed_feature/{pname}.json", {"feature": ref, "placement": keep})
        wild_features.add(f"{mid}:{pname}")
    used_tags = set()
    for mname, (m, _) in mods.items():
        feats = m.get("features")
        feats = [feats] if isinstance(feats, str) else (feats or [])
        biomes = m.get("allowed_biomes") or m.get("biomes")
        if not feats or not all(f in wild_features for f in feats) or not biomes:
            skipped["biome modifier for something not carried"] += 1
            continue
        if m.get("type") not in ("neoforge:add_features", f"{mid}:add_features_by_filter", "farmersdelight:add_features_by_filter"):
            skipped[f"biome modifier type {m.get('type')}"] += 1
            continue
        if isinstance(biomes, str) and biomes.startswith("#c:"):
            used_tags.add(biomes[3:])
        jdump(out / f"data/{mid}/neoforge/biome_modifier/{mname}.json",
              {"type": "neoforge:add_features", "biomes": biomes, "features": feats, "step": m.get("step", "vegetal_decoration")})
    for tag in sorted(used_tags):
        if tag in BIOME_TAGS:
            jdump(out / f"data/c/tags/worldgen/biome/{tag}.json", {"values": BIOME_TAGS[tag]})
        else:
            rep["unsupported"][f"biome tag c:{tag} has no mapping, so its modifier does nothing"] += 1
    for k, v in skipped.items():
        rep["unsupported"][f"worldgen: {k}"] += v
    rep["wild_features"] = len(wild_features)


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
    SPECIAL.clear()
    SPECIAL.update(parse_special_blocks(java_files))
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
        data = files[rel].read_bytes()
        if rel.endswith(".json") and data.startswith(b"\xef\xbb\xbf"):
            data = data[3:]  # a byte-order mark would stop some JSON readers
        d.write_bytes(data)
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
    for name, decl in blocks_out.items():
        if decl["template"] == "minecraft:barrel":
            p = out / f"assets/{mid}/blockstates/{name}.json"
            bs = jload(p)
            if "facing=north" in "".join(bs.get("variants", {})) and not values_of(bs, "facing") & {"up", "down"}:
                jdump(p, augment_facing(bs))
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
        elif it["drink"]:
            template = "minecraft:bread"
            comps["minecraft:food"] = {"nutrition": 0, "saturation": 0.0, "can_always_eat": True}
            comps["minecraft:consumable"] = consumable({"fast": False, "effects": []}, True)
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

    # ---- Roast definitions for feasts and pies (the Roast mod provides the behaviour)
    roast_defs = 0
    for name, decl in blocks_out.items():
        sp = SPECIAL.get(name)
        ps = (decl.get("state_properties") or {})
        if not sp:
            continue
        bs = blockstates[name]
        if sp["kind"] == "feast" and "servings" in ps:
            top = max(int(v) for v in values_of(bs, "servings") if v.isdigit())
            serving_decl = declared_items.get(sp["serving"], {})
            container = serving_decl.get("crafting_remainder")
            d = {"type": "roast:feast", "block": f"{mid}:{name}", "max": top, "serving": f"{mid}:{sp['serving']}",
                 "on_empty": "keep" if sp["leftovers"] else "break", "sound": "minecraft:block.wood.break"}
            if container:
                d["container"] = container
            jdump(out / f"data/{mid}/recipe/roast_{name}.json", d)
            roast_defs += 1
            decl["default_state"] = {"servings": str(top)}
        elif sp["kind"] == "pie" and "bites" in ps:
            top = max(int(v) for v in values_of(bs, "bites") if v.isdigit())
            slice_item = sp["slice"]
            fd = (foods.get(items.get(slice_item, {}).get("food") or "", {}) or {}).get("food", {"nutrition": 3, "saturation": 0.3})
            d = {"type": "roast:cake", "block": f"{mid}:{name}", "max": top, "nutrition": fd.get("nutrition", 3),
                 "saturation": fd.get("saturation", 0.3), "slice_tool": "#c:tools/knife", "slice_item": f"{mid}:{slice_item}"}
            jdump(out / f"data/{mid}/recipe/roast_{name}.json", d)
            roast_defs += 1
            decl["default_state"] = {"bites": "0"}
    for name, decl in blocks_out.items():
        jdump(out / f"data/{mid}/horizon/block/{name}.json", decl)
    rep["roast_defs"] = roast_defs

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

    # ---- wild crops (worldgen)
    carry_worldgen(files, mid, blocks_out, out, rep)
    rep["unsupported"]["villager trades: Horizon has no hook or data format for them"] += 0

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
             f"- items declared: {rep['items']}", f"- wild-crop features: {rep.get('wild_features', 0)}", f"- Roast feast and pie definitions: {rep.get('roast_defs', 0)}", f"- recipes: {dict(rep['recipes'])}",
             f"- recipes skipped: {len(rep['recipes_skipped'])}", "", "## Not carried or approximated"]
    lines += [f"- {k}: {v}" for k, v in sorted(rep["unsupported"].items())] or ["- (none)"]
    lines += ["", "## Blocks left out"] + ([f"- {k}: {v}" for k, v in sorted(rep["blocks_unknown"].items())] or ["- (none)"])
    lines += ["", "## Recipes skipped"] + ([f"- {x}" for x in rep["recipes_skipped"]] or ["- (none)"])
    lines += ["", "## Block templates", ""] + [f"- {k}: {v}" for k, v in sorted(rep["blocks"].items())]
    (out / "CARRY-REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:14]))


if __name__ == "__main__":
    sys.exit(main())
