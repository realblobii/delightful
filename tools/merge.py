#!/usr/bin/env python3
"""Merges the per-source content mods in `work/` (made by carry.py + prune.py) into ONE content mod, `mods/delightful/`.

* Every `<source>:name` becomes `delightful:name`. Two sources that declare the same name are one thing (the first in
  PRIORITY wins; its assets and loot table are kept).
* Machine files keep their top-level place (`recipe/cooking_pot.json`) so the machine ids are `delightful:cooking_pot` and
  `delightful:cutting_board`; all other recipes go under `recipe/<source>/...`.
* Duplicate recipes (same type, same inputs, same results) are dropped, first in PRIORITY wins.
* Tags of the same name are merged. One creative tab.
Run: python3 tools/merge.py   (reads work/, writes mods/delightful/ and a MERGE-REPORT.md)
"""
import hashlib, json, re, shutil, sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK, OUT = ROOT / "work", ROOT / "mods" / "delightful"
PRIORITY = ["farmersdelight", "rusticdelight", "expandeddelight", "corn_delight", "dumplings_delight", "cratedelight", "storagedelight"]
NAME = "delightful"
WORLDGEN = True   # False leaves out the wild-crop worldgen files (a bad one can stop all content from loading)
MACHINE_FILES = {"cooking_pot", "cutting_board"}
# Things that are the same under two names: (source, name) -> the name that stays. The source's own declaration, assets and
# loot table are dropped and every reference to it points at the kept one.
ALIASES = {
    "chinese_cabbages": "cabbages", "chinese_cabbage_crate": "cabbage_crate", "chinese_cabbage_leaf": "cabbage_leaf",
    "chinese_cabbage_seeds": "cabbage_seeds", "chinese_cabbage": "cabbage",
}
alias_re = re.compile(r"(?<=[:/])(%s)(?![a-z0-9_])" % "|".join(sorted(map(re.escape, ALIASES), key=len, reverse=True)))


def jl(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def jd(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


srcs = [s for s in PRIORITY if (WORK / s).exists()]
ref_re = re.compile(r"(?<![A-Za-z0-9_.])(%s):" % "|".join(map(re.escape, srcs)))


def rw(text):
    return alias_re.sub(lambda m: ALIASES[m.group(1)], ref_re.sub(NAME + ":", text))


def rw_key(k):
    for s in srcs:
        k = re.sub(rf"^(block|item|effect|entity|itemGroup|fluid|tag\.item|tag\.block|container|advancements?)\.{s}(\.|$)", rf"\1.{NAME}\2", k)
        if k.startswith(s + "."):
            k = NAME + k[len(s):]
    return k


if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rep = {"dupes": [], "recipes_dup": [], "conflicts": [], "tags": 0, "files": 0}

# ---- declared names: the first source in PRIORITY keeps a name
declared = {"block": {}, "item": {}}
for s in srcs:
    for kind in declared:
        for p in sorted((WORK / s / "data" / s / "horizon" / kind).glob("*.json")) if (WORK / s / "data" / s / "horizon" / kind).exists() else []:
            n = p.stem
            if n in ALIASES:
                rep["dupes"].append(f"{s}:{n} ({kind}) is the same as {ALIASES[n]}")
                continue
            owner = declared["block"].get(n) or declared["item"].get(n)
            if owner and owner != s:
                rep["dupes"].append(f"{s}:{n} ({kind}) merged into {owner}:{n}")
                continue
            declared[kind][n] = s
dupe_by_src = defaultdict(set)
for line in rep["dupes"]:
    who, rest = line.split(" ", 1)
    s, n = who.split(":")
    dupe_by_src[s].add(n)

seen_asset = {}      # rest path -> (source, sha)
tabs = OrderedDict()
tags = defaultdict(list)
lang = OrderedDict()
sounds = OrderedDict()
recipe_sigs = {}


def sha(b):
    return hashlib.sha1(b).hexdigest()


def sig(r):
    r = json.loads(json.dumps(r))
    for k in ("group", "category", "recipe_book_tab", "experience", "cookingtime", "time"):
        r.pop(k, None)
    for k in ("ingredients", "inputs"):
        if isinstance(r.get(k), list):
            r[k] = sorted(json.dumps(x, sort_keys=True) for x in r[k])
    return json.dumps(r, sort_keys=True)


for s in srcs:
    root = WORK / s
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel in ("CARRY-REPORT.md", "PRUNE-REPORT.md", "horizon-mod.toml") or rel.startswith(("LICENSE", "NOTICE")):
            continue
        data = p.read_bytes()
        m = re.match(r"assets/%s/(.+)$" % re.escape(s), rel)
        if m:
            rest = m.group(1)
            name = Path(rest).stem
            # declared-duplicate block/item assets are not copied again
            if name in dupe_by_src[s] or any(name.startswith(a) for a in ALIASES if s == "dumplings_delight"):
                continue
            if rest == f"lang/en_us.json":
                for k, v in jl(p).items():
                    if s == "dumplings_delight" and k.rsplit(".", 1)[-1] in ALIASES:
                        continue  # text of a name that is now another item
                    lang.setdefault(rw_key(k), rw(v) if isinstance(v, str) else v)
                continue
            if rest == "sounds.json":
                for k, v in jl(p).items():
                    sounds.setdefault(k, json.loads(rw(json.dumps(v))))
                continue
            dest = OUT / "assets" / NAME / rest
            if rest.endswith(".json"):
                data = rw(data.decode("utf-8-sig")).encode("utf-8")
            h = sha(data)
            if rest in seen_asset:
                if seen_asset[rest][1] != h:
                    rep["conflicts"].append(f"assets/{rest}: {s} differs from {seen_asset[rest][0]} (kept {seen_asset[rest][0]}'s)")
                continue
            seen_asset[rest] = (s, h)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            rep["files"] += 1
            continue
        m = re.match(r"data/%s/horizon/(block|item)/(.+)$" % re.escape(s), rel)
        if m:
            if m.group(2)[:-5] in dupe_by_src[s]:
                continue
            d = OUT / "data" / NAME / "horizon" / m.group(1) / m.group(2)
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_bytes(rw(data.decode("utf-8")).encode("utf-8"))
            continue
        m = re.match(r"data/%s/horizon/creative_tab/.+$" % re.escape(s), rel)
        if m:
            for it in jl(p)["items"]:
                tabs.setdefault(rw(it), None)
            continue
        m = re.match(r"data/%s/horizon/(menu|mob_effect)/(.+)$" % re.escape(s), rel)
        if m:
            d = OUT / "data" / NAME / "horizon" / m.group(1) / m.group(2)
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_bytes(rw(data.decode("utf-8")).encode("utf-8"))
            continue
        m = re.match(r"data/%s/loot_table/(.+)$" % re.escape(s), rel)
        if m:
            if Path(m.group(1)).stem in dupe_by_src[s]:
                continue
            d = OUT / "data" / NAME / "loot_table" / m.group(1)
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_bytes(rw(data.decode("utf-8")).encode("utf-8"))
            continue
        m = re.match(r"data/%s/(worldgen|neoforge)/(.+)$" % re.escape(s), rel)
        if m and not WORLDGEN:
            continue
        if m:
            d = OUT / "data" / NAME / m.group(1) / m.group(2)
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_bytes(rw(data.decode("utf-8")).encode("utf-8"))
            rep["worldgen"] = rep.get("worldgen", 0) + 1
            continue
        m = re.match(r"data/(%s|c|minecraft)/tags/(.+)$" % re.escape(s), rel)
        if m:
            ns = NAME if m.group(1) == s else m.group(1)
            rest_tag = alias_re.sub(lambda mm: ALIASES[mm.group(1)], "/" + m.group(2))[1:]
            for v in jl(p).get("values", []):
                tags[(ns, rest_tag)].append(json.loads(rw(json.dumps(v))))
            continue
        m = re.match(r"data/%s/recipe/(.+)\.json$" % re.escape(s), rel)
        if m:
            r = json.loads(rw(data.decode("utf-8")))
            sg = sig(r)
            if sg in recipe_sigs:
                rep["recipes_dup"].append(f"{s}:{m.group(1)} duplicates {recipe_sigs[sg]}")
                continue
            top = m.group(1) in MACHINE_FILES and s == "farmersdelight" or r.get("type") == "cookpot:machine"
            path = f"{m.group(1)}.json" if top else f"{s}/{m.group(1)}.json"
            recipe_sigs[sg] = f"{s}:{m.group(1)}"
            jd(OUT / "data" / NAME / "recipe" / path, r)
            continue
        rep["conflicts"].append(f"unhandled file kept out: {rel}")

# tags (merged, de-duplicated, order kept)
for (ns, rest), vals in sorted(tags.items()):
    uniq = []
    for v in vals:
        if v not in uniq:
            uniq.append(v)
    jd(OUT / "data" / ns / "tags" / rest, {"values": uniq})
    rep["tags"] += 1
# one creative tab, one lang file, one sounds file
tab_items = [i for i in tabs if i.split(":", 1)[1] in set(declared["block"]) | set(declared["item"])]
jd(OUT / "data" / NAME / "horizon" / "creative_tab" / f"{NAME}.json", {"title": f"itemGroup.{NAME}", "icon": f"{NAME}:cooking_pot", "items": tab_items})
lang[f"itemGroup.{NAME}"] = "Delightful"
jd(OUT / "assets" / NAME / "lang" / "en_us.json", lang)
if sounds:
    jd(OUT / "assets" / NAME / "sounds.json", sounds)
(OUT / "horizon-mod.toml").write_text(
    f'id = "{NAME}"\nname = "Delightful"\nversion = "0.2.0"\n'
    'description = "Farmer\'s Delight and six add-ons merged into one mod. Generated by tools/merge.py. Not run in Horizon yet."\n'
    'authors = ["Delightful"]\napi = "0.2"\nside = "both"\ncapabilities = ["registries"]\n', encoding="utf-8")
(OUT / "licenses").mkdir()
for f in sorted((ROOT / "licenses").glob("*")):
    shutil.copyfile(f, OUT / "licenses" / f.name)
lines = [f"# Merge report", "", f"- sources: {', '.join(srcs)}", f"- blocks: {len(declared['block'])}, items: {len(declared['item'])}",
         f"- asset files: {rep['files']}", f"- tags merged: {rep['tags']}", f"- worldgen files: {rep.get('worldgen', 0)}", f"- recipes kept: {len(recipe_sigs)}",
         f"- duplicate recipes removed: {len(rep['recipes_dup'])}", f"- same-name items/blocks merged: {len(rep['dupes'])}",
         f"- asset path conflicts: {len([c for c in rep['conflicts'] if c.startswith('assets')])}", "", "## Merged names"]
lines += [f"- {x}" for x in rep["dupes"]] or ["- (none)"]
lines += ["", "## Duplicate recipes removed"] + [f"- {x}" for x in rep["recipes_dup"]] or ["- (none)"]
lines += ["", "## Conflicts"] + [f"- {x}" for x in rep["conflicts"]] or ["- (none)"]
(OUT / "MERGE-REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:12]))
