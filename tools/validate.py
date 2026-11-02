#!/usr/bin/env python3
"""Checks a carried content mod for the mistakes a script can see: JSON that does not parse, blockstates naming models that
are missing, models naming missing parents or textures, creative-tab and menu/machine mismatches.
It cannot know what Horizon accepts; only running the game does that.  Usage: validate.py mods/<id>"""
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
mid = json.loads(json.dumps({}))  # placeholder to keep the namespace logic simple
mid = re.search(r'^id = "(\w+)"', (root / "horizon-mod.toml").read_text(), re.M).group(1)
errors, warns = [], []

def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"{p.relative_to(root)}: {e}")

for p in root.rglob("*.json"):
    load(p)
a = root / "assets" / mid

def model_path(ref):
    ns, _, path = ref.partition(":") if ":" in ref else ("minecraft", "", ref)
    return ns, path

roots = [root] + [p for p in root.parent.iterdir() if p.is_dir() and p != root]  # sibling mods count

def exists_model(ref):
    ns, path = model_path(ref)
    return ns == "minecraft" or any((r / "assets" / ns / "models" / f"{path}.json").exists() for r in roots)

def exists_tex(ref):
    ns, path = model_path(ref)
    return ns == "minecraft" or any((r / "assets" / ns / "textures" / f"{path}.png").exists() for r in roots)

for p in (a / "blockstates").glob("*.json") if (a / "blockstates").exists() else []:
    d = load(p) or {}
    refs = []
    for v in d.get("variants", {}).values():
        refs += [x["model"] for x in (v if isinstance(v, list) else [v])]
    for part in d.get("multipart", []):
        ap = part.get("apply", {})
        refs += [x["model"] for x in (ap if isinstance(ap, list) else [ap])]
    for r in refs:
        if not exists_model(r):
            errors.append(f"blockstate {p.stem}: model {r} is missing")
for p in (a / "models").rglob("*.json") if (a / "models").exists() else []:
    d = load(p) or {}
    if "parent" in d and not exists_model(d["parent"]):
        errors.append(f"model {p.relative_to(a)}: parent {d['parent']} is missing")
    for k, t in (d.get("textures") or {}).items():
        if isinstance(t, str) and not t.startswith("#") and not exists_tex(t):
            errors.append(f"model {p.relative_to(a)}: texture {t} is missing")
for p in (a / "items").glob("*.json") if (a / "items").exists() else []:
    d = load(p) or {}
    m = d.get("model", {}).get("model")
    if m and not exists_model(m):
        errors.append(f"item {p.stem}: model {m} is missing")
declared = {p.stem for k in ("block", "item") for p in (root / "data" / mid / "horizon" / k).glob("*.json")}
for p in (root / "data" / mid / "horizon" / "creative_tab").glob("*.json"):
    for it in (load(p) or {}).get("items", []):
        if it.split(":")[1] not in declared:
            warns.append(f"creative tab lists {it}, which is not declared (the game leaves it out)")
menus = {p.stem: load(p) for p in (root / "data" / mid / "horizon" / "menu").glob("*.json")}
for p in (root / "data" / mid / "recipe").glob("*.json"):
    d = load(p) or {}
    if d.get("type") == "cookpot:machine":
        n = len(d["gui"]["slots"])
        m = menus.get(d["menu"].split(":")[1])
        if not m or m["slots"] != n:
            errors.append(f"machine {p.stem}: menu has {m and m['slots']} slots, the machine has {n}")
for p in (root / "data" / mid / "recipe").rglob("*.json"):
    d = load(p) or {}
    r = d.get("result")
    rid = r.get("id") if isinstance(r, dict) else r if isinstance(r, str) else None
    if rid and rid.startswith(mid + ":") and rid.split(":")[1] not in declared:
        errors.append(f"recipe {p.relative_to(root)}: makes undeclared {rid}")
print(f"{len(errors)} errors, {len(warns)} warnings")
for e in errors[:60]:
    print("ERROR", e)
for w in warns[:20]:
    print("warn", w)
sys.exit(1 if errors else 0)
