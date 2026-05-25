#!/usr/bin/env python3
"""Print install-time dependency hints for this skill."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
MANIFEST = SKILL_DIR / "dependencies.json"


PACKAGE_IMPORTS = {
    "beautifulsoup4": "bs4",
    "lxml": "lxml",
    "playwright": "playwright",
    "requests": "requests",
}


PLUGIN_HINT_PATHS = {
    "Browser": [".codex/plugins/cache/openai-bundled/browser"],
    "Chrome": [".codex/plugins/cache/openai-bundled/chrome"],
    "Computer Use": [".codex/plugins/cache/openai-primary-runtime/computer-use", ".codex/plugins/cache/openai-bundled/computer-use"],
    "Spreadsheets": [".codex/plugins/cache/openai-primary-runtime/spreadsheets"],
    "Documents": [".codex/plugins/cache/openai-primary-runtime/documents"],
}


def import_available(package_name: str) -> bool:
    module_name = PACKAGE_IMPORTS.get(package_name, package_name)
    return importlib.util.find_spec(module_name) is not None


def plugin_hint_available(name: str) -> bool:
    home = Path.home()
    for relative in PLUGIN_HINT_PATHS.get(name, []):
        if (home / relative).exists():
            return True
    return False


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    print(f"Skill: {manifest['skill']}")
    print("\nPython packages:")
    missing_packages = []
    for package in manifest["python"]["packages"]:
        ok = import_available(package)
        print(f"- [{'OK' if ok else 'MISSING'}] {package}")
        if not ok:
            missing_packages.append(package)

    if missing_packages:
        print("\nInstall missing packages:")
        print("python3 -m pip install -r requirements.txt")
        if "playwright" in missing_packages:
            print("python3 -m playwright install chromium")

    print("\nRecommended plugins/connectors:")
    for plugin in manifest["plugins"]:
        status = "FOUND" if plugin_hint_available(plugin["name"]) else "CHECK"
        required = "required" if plugin.get("required") else "recommended"
        print(f"- [{status}] {plugin['name']} ({required}): {plugin['reason']}")

    print("\nIf a plugin is marked CHECK, install/enable it in Codex before relying on the related workflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
