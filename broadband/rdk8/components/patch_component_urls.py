#!/usr/bin/env python3
"""
patch_component_urls.py
Run from broadband/rdk8/components/

Updates the `url` field in every *-components.json to point to the exact
release tag or commit derived from component-versions.json.
"""

import json, re, sys
from pathlib import Path


def versioned_url(base_url: str, version_str: str) -> str:
    """Return base_url enriched with the most-specific ref we can derive."""
    if not version_str or not base_url.startswith("https://github.com"):
        return base_url  # Gerrit or unknown host — leave alone

    base_url = base_url.rstrip("/")

    # Primary part = everything before the first parenthetical sub-repo note
    # e.g. "1.2.9 (rdm-agent: develop / rev:d5e73722)" → "1.2.9"
    # e.g. "develop / rev:4bc32193 (rdk-wps-monitor: ...)" → "develop / rev:4bc32193"
    primary = version_str.split("(")[0].strip()

    # Semver / explicit tag: "1.4.3", "v1.6.0", "2.11.0", "v0.5.0" …
    if re.match(r"^v?\d+\.\d+", primary):
        return f"{base_url}/releases/tag/{primary}"

    # Branch + commit: "develop / rev:f203bb73", "main / rev:8b6d5211" …
    m = re.search(r"rev:([0-9a-f]+)", primary)
    if m:
        return f"{base_url}/commit/{m.group(1)}"

    # Branch only ("main", "develop") — nothing specific to pin
    return base_url


def main():
    here = Path(__file__).parent
    versions_path = here / "component-versions.json"

    if not versions_path.exists():
        sys.exit(f"ERROR: {versions_path} not found")

    versions: dict = json.loads(versions_path.read_text())

    component_files = sorted(here.glob("*-components.json"))
    if not component_files:
        sys.exit("No *-components.json files found.")

    for cf in component_files:
        data = json.loads(cf.read_text())
        changed = 0
        for comp in data.get("components", []):
            ver = versions.get(comp.get("name", ""))
            if ver and comp.get("url"):
                new_url = versioned_url(comp["url"], ver)
                if new_url != comp["url"]:
                    comp["url"] = new_url
                    changed += 1
        cf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"{cf.name}: {changed} URL(s) updated")

    print("Done.")


if __name__ == "__main__":
    main()
