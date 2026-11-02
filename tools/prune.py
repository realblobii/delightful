#!/usr/bin/env python3
"""Removes the blocks (and what depends on them) whose models or textures cannot be found, across all carried mods in
`mods/`: the game would draw them as missing models. Writes `PRUNE-REPORT.md` into each mod. Run after carry.py."""
import json, re, sys
from pathlib import Path

MODS = Path(sys.argv[1] if len(sys.argv) > 1 else "mods")
mods = {}
for d in sorted(p for p in MODS.iterdir() if p.is_dir()):
    mid = re.search(r'^id = "(\w+)"', (d / "horizon-mod.toml").read_text(), re.M).group(1)
    mods[mid] = d

def jl(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def find(kind, ref, ext):
    ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)
    if ns == "minecraft":
        return True
    d = mods.get(ns)
    return bool(d and (d / "assets" / ns / kind / f"{path}{ext}").exists())

def model_ok(ref, seen=None):
    seen = seen or set()
    if ref in seen:
        return True
    seen.add(ref)
    ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)
    if ns == "minecraft":
        return True
    if not find("models", ref, ".json"):
        return False
    m = jl(mods[ns] / "assets" / ns / "models" / f"{path}.json") or {}
    if "parent" in m and not model_ok(m["parent"], seen):
        return False
    for t in (m.get("textures") or {}).values():
        if isinstance(t, str) and not t.startswith("#") and not find("textures", t, ".png"):
            return False
    return True

def block_models(bs):
    refs = []
    for v in bs.get("variants", {}).values():
        refs += [x["model"] for x in (v if isinstance(v, list) else [v])]
    for part in bs.get("multipart", []):
        ap = part.get("apply", {})
        refs += [x["model"] for x in (ap if isinstance(ap, list) else [ap])]
    return refs

for mid, d in mods.items():
    removed = {}
    for p in sorted((d / "data" / mid / "horizon" / "block").glob("*.json")):
        n = p.stem
        bs = jl(d / "assets" / mid / "blockstates" / f"{n}.json")
        refs = block_models(bs) if bs else []
        bad = [r for r in refs if not model_ok(r)]
        if not bs or bad:
            removed[n] = f"model chain broken: {bad[0] if bad else 'no blockstate'}"
    for n, why in removed.items():
        for rel in (f"data/{mid}/horizon/block/{n}.json", f"assets/{mid}/blockstates/{n}.json", f"assets/{mid}/items/{n}.json",
                    f"data/{mid}/loot_table/blocks/{n}.json"):
            (d / rel).unlink(missing_ok=True)
    gone = set(removed)
    # creative tab
    for p in (d / "data" / mid / "horizon" / "creative_tab").glob("*.json"):
        t = jl(p)
        t["items"] = [i for i in t["items"] if i.split(":", 1)[1] not in gone]
        p.write_text(json.dumps(t, indent=2) + "\n", encoding="utf-8")
    # recipes making a removed block
    dropped = []
    for p in list((d / "data" / mid / "recipe").rglob("*.json")):
        r = jl(p) or {}
        res = r.get("result")
        rid = res.get("id") if isinstance(res, dict) else res if isinstance(res, str) else None
        ids = [rid] + [x.get("id") for x in r.get("results", []) if isinstance(x, dict)]
        if any(i and i.startswith(mid + ":") and i.split(":", 1)[1] in gone for i in ids):
            p.unlink()
            dropped.append(p.relative_to(d / "data" / mid / "recipe").as_posix())
    lines = [f"# Prune report: {mid}", "", f"- blocks removed: {len(removed)}", f"- recipes removed: {len(dropped)}", "", "## Blocks"]
    lines += [f"- {k}: {v}" for k, v in sorted(removed.items())] or ["- (none)"]
    (d / "PRUNE-REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{mid}: removed {len(removed)} blocks, {len(dropped)} recipes")
