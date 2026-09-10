#!/usr/bin/env python3
"""Regenerate the compiled-in fallbackJSON literal inside AIHubApp.swift from
remote_models.json.

RemoteModelConfigService ships an embedded copy of the catalog so the app still
has good model IDs when it cannot reach GitHub raw. That copy is exactly what
rotted last time: the app fell back to llama-3.3-70b-versatile and glm-4-flash,
both already shut down. Hand-editing two copies is how that happened, so this
script makes the Swift literal a build artifact of the JSON instead.

Run:  python3 tools/sync_fallback_json.py          # rewrite the literal
      python3 tools/sync_fallback_json.py --check  # verify only, exit 1 on drift
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWIFT = ROOT / "GeneratedApp" / "Sources" / "AIHubApp.swift"
CATALOG = ROOT / "remote_models.json"

# Fields RemoteProviderConfig actually decodes. Keep in sync with the struct.
PROVIDER_FIELDS = (
    "recommendedModels", "defaultModel", "notes", "fallbackChain", "retiredModels",
    "free", "requiresCard", "status", "contextTokens", "vision",
    "visionModel", "imageModel", "baseURL", "modelsEndpoint", "signupURL",
)

LITERAL_RE = re.compile(r'(private let fallbackJSON = """)(.*?)(""")', re.S)
DEFAULTS_RE = re.compile(
    r"(/// MARK: MODEL_CATALOG_DEFAULTS_BEGIN\n)(.*?)(\n/// MARK: MODEL_CATALOG_DEFAULTS_END)",
    re.S,
)


def swift_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def swift_dict(table: dict[str, str], indent: str) -> str:
    if not table:
        return "[:]"
    rows = ",\n".join(f"{indent}    {swift_string(k)}: {swift_string(v)}" for k, v in sorted(table.items()))
    return f"[\n{rows}\n{indent}]"


def swift_string_array(values: list[str], indent: str) -> str:
    if not values:
        return "[]"
    rows = ",\n".join(f"{indent}    {swift_string(v)}" for v in values)
    return f"[\n{rows}\n{indent}]"


def build_defaults() -> str:
    """Emit the compiled-in deprecation tables / fallback chains as Swift."""
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    retired = {
        name: cfg["retiredModels"]
        for name, cfg in catalog["providers"].items()
        if cfg.get("retiredModels")
    }
    chains = {
        name: cfg["fallbackChain"]
        for name, cfg in catalog["providers"].items()
        if cfg.get("fallbackChain")
    }

    lines = ["enum ModelCatalogDefaults {"]

    lines.append("    static let globalDeprecated: [String: String] = "
                 + swift_dict(catalog.get("deprecated", {}), "    "))

    if retired:
        inner = []
        for name in sorted(retired):
            inner.append(f"        {swift_string(name)}: " + swift_dict(retired[name], "        "))
        lines.append("    static let retiredByProvider: [String: [String: String]] = [\n"
                     + ",\n".join(inner) + "\n    ]")
    else:
        lines.append("    static let retiredByProvider: [String: [String: String]] = [:]")

    if chains:
        inner = []
        for name in sorted(chains):
            inner.append(f"        {swift_string(name)}: " + swift_string_array(chains[name], "        "))
        lines.append("    static let chains: [String: [String]] = [\n" + ",\n".join(inner) + "\n    ]")
    else:
        lines.append("    static let chains: [String: [String]] = [:]")

    lines.append("}")
    return "\n".join(lines)


def build_literal() -> str:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    providers = {}
    for name, cfg in catalog["providers"].items():
        providers[name] = {k: cfg[k] for k in PROVIDER_FIELDS if k in cfg}

    payload = {
        "version": catalog["version"],
        "updatedAt": catalog["updatedAt"],
        "providers": providers,
    }
    if "deprecated" in catalog:
        payload["deprecated"] = catalog["deprecated"]
    if "providerOrder" in catalog:
        payload["providerOrder"] = catalog["providerOrder"]

    # 6-space base indent matches the surrounding Swift property body.
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    indented = "\n".join(("    " + line) if line else line for line in body.split("\n"))
    return "\n" + indented + "\n    "


def sync_block(text: str, pattern: re.Pattern, generated: str, label: str,
               check_only: bool) -> tuple[str, bool, bool]:
    """Replace one generated region. Returns (text, changed, ok)."""
    match = pattern.search(text)
    if not match:
        print(f"FATAL: could not find the {label} region", file=sys.stderr)
        return text, False, False
    if match.group(2) == generated:
        print(f"{label} is in sync with remote_models.json")
        return text, False, True
    if check_only:
        print(f"DRIFT: the compiled-in {label} differs from remote_models.json.", file=sys.stderr)
        return text, False, False
    updated = text[: match.start(2)] + generated + text[match.end(2):]
    print(f"{label} regenerated from remote_models.json")
    return updated, True, True


def main() -> int:
    check_only = "--check" in sys.argv
    text = SWIFT.read_text(encoding="utf-8")

    text, changed_json, ok_json = sync_block(
        text, LITERAL_RE, build_literal(), "fallbackJSON", check_only
    )
    text, changed_defaults, ok_defaults = sync_block(
        text, DEFAULTS_RE, "\n" + build_defaults() + "\n", "ModelCatalogDefaults", check_only
    )

    if not (ok_json and ok_defaults):
        if check_only:
            print("Run: python3 tools/sync_fallback_json.py", file=sys.stderr)
        return 1

    if changed_json or changed_defaults:
        SWIFT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
