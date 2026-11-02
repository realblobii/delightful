#!/usr/bin/env python3
"""Zips each folder in mods/ into dist/<id>-<version>.hmod (the reports stay out of the archive)."""
import re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "dist"
out.mkdir(exist_ok=True)
for d in sorted(p for p in (ROOT / "mods").iterdir() if p.is_dir()):
    toml = (d / "horizon-mod.toml").read_text()
    mid = re.search(r'^id = "(\w+)"', toml, re.M).group(1)
    ver = re.search(r'^version = "([^"]+)"', toml, re.M).group(1)
    target = out / f"{mid}-{ver}.hmod"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(d.rglob("*")):
            if f.is_file() and f.name not in ("CARRY-REPORT.md", "PRUNE-REPORT.md"):
                info = zipfile.ZipInfo(f.relative_to(d).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, f.read_bytes())
    print(target.name, round(target.stat().st_size / 1e6, 1), "MB")
