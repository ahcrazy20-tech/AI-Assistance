#!/usr/bin/env python3
"""Validate the AI Hub model catalog.

Why this exists
---------------
The app died because hardcoded model IDs silently went stale: Groq shut down
llama-3.3-70b-versatile on 2026-08-16, DeepSeek retired deepseek-chat on
2026-07-24, Z.AI dropped glm-4-flash, Cerebras removed llama-3.3-70b. Every one
of those was still a default in three separate places:

  1. remote_models.json          (fetched at runtime from GitHub raw)
  2. ProviderID.defaultModel     (compiled into the binary)
  3. RemoteModelConfigService.fallbackJSON (compiled in, used when offline)

This script cross-checks all three against a single deprecation table so a stale
ID can never ship again unnoticed.

Run:  python3 tools/validate_catalog.py
Exit: 0 = clean, 1 = problems found.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWIFT = ROOT / "GeneratedApp" / "Sources" / "AIHubApp.swift"
CATALOG = ROOT / "remote_models.json"

# Model IDs confirmed dead EVERYWHERE, against provider deprecation tables
# (verified 2026-09-10). Mirrors the "deprecated" map in remote_models.json.
DEPRECATED: dict[str, str] = {
    # Z.AI — glm-4.x flash family retired
    "glm-4-flash": "glm-4.7-flash",
    "glm-4v-flash": "glm-4.6v-flash",
    "glm-4-air": "glm-4.5-air",
    "glm-4-plus": "glm-4.7",
    # Gemini — 1.5 line retired
    "gemini-1.5-pro": "gemini-2.5-flash",
    "gemini-1.5-flash": "gemini-2.5-flash-lite",
    # DeepSeek — retired 2026-07-24 15:59 UTC
    "deepseek-chat": "deepseek-v4-flash",
    "deepseek-reasoner": "deepseek-v4-flash",
    "deepseek-coder": "deepseek-v4-flash",
    "deepseek-v3": "deepseek-v4-flash",
    # Groq — kimi 0905 checkpoint pulled
    "moonshotai/kimi-k2-instruct-0905": "moonshotai/kimi-k2-instruct",
    # Stale Anthropic / OpenAI / Google IDs
    "anthropic/claude-3.5-sonnet": "anthropic/claude-sonnet-4.5",
    "anthropic/claude-3-5-sonnet-20241022": "anthropic/claude-sonnet-4.5",
    "anthropic/claude-3-5-haiku-20241022": "anthropic/claude-haiku-4.5",
    "claude-3-5-sonnet-20241022": "anthropic/claude-sonnet-4.5",
    "claude-3-5-haiku-20241022": "anthropic/claude-haiku-4.5",
    "gpt-4o": "openai/gpt-5.6-luna",
    "google/gemini-2.0-flash": "google/gemini-2.5-flash",
    "xai/grok-3": "xai/grok-4",
    # Never existed as a callable model
    "openrouter/free": "nvidia/nemotron-3-ultra-550b-a55b:free",
    # NVIDIA NIM — 3.1 line aging out
    "meta/llama-3.1-70b-instruct": "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-405b-instruct": "meta/llama-3.3-70b-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct": "nvidia/nemotron-3-super-120b-a12b",
    # Cloudflare Workers AI — superseded checkpoints
    "@cf/google/gemma-3-12b-it": "@cf/google/gemma-4-26b-a4b-it",
    "@cf/qwen/qwq-32b": "@cf/qwen/qwen3-30b-a3b-fp8",
}

# IDs that are dead on ONE provider but may still resolve elsewhere, so they are
# only condemned inside that provider's catalog. Mirrors "retiredModels" in
# remote_models.json.
DEPRECATED_BY_PROVIDER: dict[str, dict[str, str]] = {
    # Groq — shutdown 2026-08-16 / 2026-07-17 / 2026-03-09
    "groq": {
        "llama-3.3-70b-versatile": "qwen/qwen3.6-27b",
        "llama-3.1-8b-instant": "openai/gpt-oss-20b",
        "qwen/qwen3-32b": "openai/gpt-oss-120b",
        "meta-llama/llama-4-scout-17b-16e-instruct": "openai/gpt-oss-120b",
        "meta-llama/llama-4-maverick-17b-128e-instruct": "openai/gpt-oss-120b",
        "allam-2-7b-instruct": "qwen/qwen3.6-27b",
        "meta-llama/llama-guard-4-12b": "openai/gpt-oss-safeguard-20b",
    },
    # Cerebras — llama-3.3-70b removed from the catalog
    "cerebras": {
        "llama-3.3-70b": "gpt-oss-120b",
        "llama3.1-70b-specdec": "llama3.1-70b",  # Cerebras still lists llama3.1-70b as online
    },
    # SambaNova — dropped from the free catalog
    "sambaNova": {
        "Qwen3-32B": "gpt-oss-120b",
        "DeepSeek-R1": "DeepSeek-V3.2",
        "Llama-4-Maverick-17B-128E-Instruct": "gpt-oss-120b",
    },
    # OpenRouter — rotated off the :free roster
    "openRouter": {
        "google/gemini-2.0-flash-exp:free": "google/gemma-4-31b-it:free",
        "qwen/qwen-2.5-72b-instruct:free": "qwen/qwen3-coder:free",
        "mistralai/mistral-7b-instruct:free": "mistralai/mistral-nemo",
    },
    # Vercel AI Gateway — naming traps / stale IDs
    "vercel": {
        "openai/gpt-4o-mini": "openai/gpt-5.6-luna",
        "meta/llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct",
    },
}


def dead_replacement(model: str, provider: str | None) -> str | None:
    """Return the replacement for a dead ID, or None if the ID is still live."""
    if model in DEPRECATED:
        return DEPRECATED[model]
    if provider and model in DEPRECATED_BY_PROVIDER.get(provider, {}):
        return DEPRECATED_BY_PROVIDER[provider][model]
    return None


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def parse_provider_cases(swift: str) -> set[str]:
    """Read the ProviderID enum declaration and return its raw values."""
    match = re.search(r"enum ProviderID:[^\n]*\{\s*\n\s*case ([^\n]+)", swift)
    if not match:
        raise SystemExit("FATAL: could not locate `enum ProviderID` in the Swift source")
    return {c.strip() for c in match.group(1).split(",") if c.strip()}


def parse_swift_defaults(swift: str) -> dict[str, str]:
    """Read ProviderID.defaultModel — the compiled-in default per provider."""
    block = re.search(r"var defaultModel: String \{(.*?)\n    \}", swift, re.S)
    if not block:
        raise SystemExit("FATAL: could not locate ProviderID.defaultModel")
    return dict(
        (m.group(1), m.group(2))
        for m in re.finditer(r'case \.(\w+): return "([^"]*)"', block.group(1))
    )


def parse_settings_defaults(swift: str) -> dict[str, str]:
    """Read the AppSettings.init UserDefaults fallbacks — what a fresh install uses."""
    init = re.search(r"\n    init\(\) \{\n        let store = UserDefaults\.standard(.*?)\n    \}\n", swift, re.S)
    if not init:
        raise SystemExit("FATAL: could not locate AppSettings.init")
    return dict(
        (m.group(1), m.group(2))
        for m in re.finditer(r'store\.string\(forKey: "(\w+)"\) \?\? "([^"]*)"', init.group(1))
    )


# UserDefaults key -> provider. The keys are irregular (siliconModel, nvidiaNIMModel),
# so scoping per-provider deprecations needs an explicit map.
SETTINGS_KEY_PROVIDER = {
    "geminiModel": "gemini",
    "groqModel": "groq",
    "zaiModel": "zai",
    "zaiVisionModel": "zai",
    "mistralModel": "mistral",
    "cloudflareModel": "cloudflare",
    "cloudflareVisionModel": "cloudflare",
    "cloudflareImageModel": "cloudflare",
    "vercelModel": "vercel",
    "sambaNovaModel": "sambaNova",
    "openRouterModel": "openRouter",
    "siliconModel": "siliconFlow",
    "cerebrasModel": "cerebras",
    "deepseekModel": "deepseek",
    "nvidiaNIMModel": "nvidiaNIM",
    "antigravityModel": "antigravity",
    "customModel": "custom",
}


def parse_embedded_fallback(swift: str) -> dict:
    """Read RemoteModelConfigService.fallbackJSON — used when GitHub raw is unreachable."""
    block = re.search(r'private let fallbackJSON = """(.*?)"""', swift, re.S)
    if not block:
        raise SystemExit("FATAL: could not locate RemoteModelConfigService.fallbackJSON")
    return json.loads(block.group(1))


def check_no_deprecated(ids: list[str], where: str, report: Report, provider: str | None = None) -> None:
    for model in ids:
        replacement = dead_replacement(model, provider)
        if replacement is not None:
            scope = "globally" if model in DEPRECATED else f"on {provider}"
            report.error(f"{where}: '{model}' is dead {scope} -> use '{replacement}'")


def check_generated_blocks(report: Report) -> None:
    """The compiled-in copies must match remote_models.json exactly."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "sync_fallback_json.py"), "--check"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip().replace("\n", " | ")
        report.error(f"compiled-in catalog is out of sync with remote_models.json: {detail}")


def main() -> int:
    report = Report()
    swift = SWIFT.read_text(encoding="utf-8")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    provider_cases = parse_provider_cases(swift)
    swift_defaults = parse_swift_defaults(swift)
    settings_defaults = parse_settings_defaults(swift)
    embedded = parse_embedded_fallback(swift)

    print(f"ProviderID cases in Swift : {len(provider_cases)}")
    print(f"Catalog providers         : {len(catalog['providers'])}")
    print(f"Known-dead model IDs      : {len(DEPRECATED)}")
    print()

    # 1. Catalog keys must be real ProviderID raw values, or the app can never read them.
    for key in catalog["providers"]:
        if key not in provider_cases:
            report.error(f"remote_models.json: provider '{key}' has no ProviderID case in Swift")

    # 2. The catalog's own deprecation map must agree with this script's table.
    for model, replacement in catalog.get("deprecated", {}).items():
        if model not in DEPRECATED:
            report.warn(f"remote_models.json deprecates '{model}' but validate_catalog.py does not track it")
        elif DEPRECATED[model] != replacement:
            report.error(
                f"replacement mismatch for '{model}': catalog says '{replacement}', "
                f"validator says '{DEPRECATED[model]}'"
            )
    for model in DEPRECATED:
        if model not in catalog.get("deprecated", {}):
            report.error(f"validator tracks globally-dead ID '{model}' but remote_models.json omits it")

    for provider, table in DEPRECATED_BY_PROVIDER.items():
        declared = catalog["providers"].get(provider, {}).get("retiredModels", {})
        for model, replacement in table.items():
            if model not in declared:
                report.error(f"remote_models.json[{provider}] must declare retiredModels['{model}']")
            elif declared[model] != replacement:
                report.error(
                    f"replacement mismatch for {provider} '{model}': catalog says "
                    f"'{declared[model]}', validator says '{replacement}'"
                )
        for model in declared:
            if model not in table:
                report.error(f"remote_models.json[{provider}] retires '{model}' but the validator does not track it")

    # 3. Per-provider structural checks.
    for name, cfg in catalog["providers"].items():
        where = f"remote_models.json[{name}]"
        recommended = cfg.get("recommendedModels", [])
        default = cfg.get("defaultModel", "")
        chain = cfg.get("fallbackChain", [])

        if cfg.get("status") == "retired":
            if recommended or default or chain:
                report.error(f"{where}: retired provider must not advertise models")
            continue

        if not recommended:
            report.error(f"{where}: recommendedModels is empty")
        if default and default not in recommended:
            report.error(f"{where}: defaultModel '{default}' is not in recommendedModels")
        if chain and default and chain[0] != default:
            report.error(f"{where}: fallbackChain[0]='{chain[0]}' must equal defaultModel '{default}'")
        if not chain:
            report.error(f"{where}: fallbackChain is empty — a 404 has nowhere to go")

        check_no_deprecated(recommended, f"{where}.recommendedModels", report, name)
        check_no_deprecated([default] if default else [], f"{where}.defaultModel", report, name)
        check_no_deprecated(chain, f"{where}.fallbackChain", report, name)

        for model in chain:
            if model not in recommended:
                report.warn(f"{where}: fallback '{model}' is not in recommendedModels (picker won't show it)")

    # 4. Compiled-in defaults must not be dead either — these ship in the binary.
    for provider, model in swift_defaults.items():
        if model:
            check_no_deprecated([model], f"Swift ProviderID.defaultModel[.{provider}]", report, provider)

    # 5. A fresh install's UserDefaults fallbacks.
    for key, model in settings_defaults.items():
        if model:
            check_no_deprecated(
                [model], f"Swift AppSettings.init['{key}']", report, SETTINGS_KEY_PROVIDER.get(key)
            )

    # 6. The offline fallback JSON — the silent killer: it is used exactly when
    #    the network is bad, which is also when a stale model can't be corrected.
    for name, cfg in embedded.get("providers", {}).items():
        where = f"Swift fallbackJSON[{name}]"
        check_no_deprecated(cfg.get("recommendedModels", []), f"{where}.recommendedModels", report, name)
        if cfg.get("defaultModel"):
            check_no_deprecated([cfg["defaultModel"]], f"{where}.defaultModel", report, name)

    # 7. Every non-retired provider needs a Swift default that matches the catalog,
    #    otherwise a user who never fetched the remote config gets a different model
    #    than the one that was verified.
    for name, cfg in catalog["providers"].items():
        if cfg.get("status") == "retired":
            continue
        expected = cfg.get("defaultModel", "")
        actual = swift_defaults.get(name)
        if actual is None:
            report.error(f"Swift ProviderID.defaultModel has no case for '{name}'")
        elif expected and actual != expected:
            report.error(
                f"drift for '{name}': Swift default '{actual}' != catalog default '{expected}'"
            )

    # 8. The two compiled-in copies (fallbackJSON, ModelCatalogDefaults) are
    #    generated from the JSON; confirm nobody hand-edited them.
    check_generated_blocks(report)

    for warning in report.warnings:
        print(f"WARN  {warning}")
    for error in report.errors:
        print(f"ERROR {error}")

    print()
    if report.errors:
        print(f"FAILED — {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
        return 1
    print(f"OK — catalog is consistent, no dead model IDs ({len(report.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

