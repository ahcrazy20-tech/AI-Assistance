# Free Modules — verified 2026-09-10

Every entry below was checked against the provider's own docs, deprecation table,
or a live catalog on **2026-09-10**. "Wired" means the app already has it as a
`ProviderID` with a working base URL, default model, and fallback chain.

**Confidence** = how solid the verification is:
- **live** — read directly from the provider's own machine-readable catalog or docs today
- **docs** — provider deprecation/pricing page, dated within the last ~6 weeks
- **agg** — third-party aggregator only; re-verify in-app before depending on it

---

## Tier 1 — wired into the app, genuinely free, no card

| Module | Base URL | Free models to use | Limits | Conf |
|---|---|---|---|---|
| **APInex** ⭐ new | `https://api.apinex.bond/v1` | `free/gemini-3.8-flash`, `free/qwen-3.8-max`, `free/glm-5.3-flash`, `free/gpt-5.6-luna`, `free/deepseek-v4-flash-0731`, `free/gemini-3.1-pro`, `free/deepseek-v4-pro-0813`, `free/muse-spark-1.3` | all 1M context; prepaid balance only for non-`free/` IDs | live |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta` | `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3-flash-preview`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-3.1-flash-lite` | 10–15 RPM, ~1,500 RPD; native vision + PDF + 1M ctx | docs |
| **Groq** | `https://api.groq.com/openai/v1` | `qwen/qwen3.6-27b`, `openai/gpt-oss-120b`, `minimaxai/minimax-m2.7`, `moonshotai/kimi-k2-instruct`, `openai/gpt-oss-20b`, `groq/compound` | 30 RPM, 1,000 RPD per model | docs |
| **Z.AI (Zhipu)** | `https://api.z.ai/api/paas/v4` | `glm-4.7-flash` (203K), `glm-4.5-flash`, `glm-4.6v-flash` (vision) | only these three are $0 | docs |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `nvidia/nemotron-3-ultra-550b-a55b:free` (1M), `inclusionai/ling-3.0-flash:free`, `qwen/qwen3-coder:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `google/gemma-4-31b-it:free`, `poolside/laguna-s-2.1:free`, `cohere/north-mini-code:free`, `openai/gpt-oss-20b:free` | 20 RPM, 50 RPD (1,000 RPD after a one-time $10 top-up). Roster rotates. | docs |
| **Cloudflare Workers AI** | `https://api.cloudflare.com/client/v4/accounts/{id}/ai/v1` | `@cf/zai-org/glm-4.7-flash`, `@cf/openai/gpt-oss-120b`, `@cf/meta/llama-4-scout-17b-16e-instruct`, `@cf/google/gemma-4-26b-a4b-it`, `@cf/qwen/qwen3-30b-a3b-fp8`, `@cf/moonshotai/kimi-k2.6` | 10,000 Neurons/day shared | docs |
| **SambaNova Cloud** | `https://api.sambanova.ai/v1` | `Meta-Llama-3.3-70B-Instruct`, `gpt-oss-120b`, `DeepSeek-V3.2`, `DeepSeek-V3.1`, `gemma-4-31B-it`, `MiniMax-M2.7` | ~200K tokens/day per model | docs |
| **Mistral La Plateforme** | `https://api.mistral.ai/v1` | `mistral-small-latest`, `mistral-medium-2508`, `devstral-small`, `magistral-small`, `codestral-latest`, `mistral-large-latest` | free "Experiment" tier ~1B tok/month but ~1 req/sec — phone verification | docs |
| **NVIDIA NIM** | `https://integrate.api.nvidia.com/v1` | `meta/llama-3.3-70b-instruct`, `nvidia/nemotron-3-super-120b-a12b`, `deepseek-ai/deepseek-r1`, `moonshotai/kimi-k2-instruct` | 1,000 free credits, ~40 RPM | agg |
| **SiliconFlow** | `https://api.siliconflow.com/v1` | `Qwen/Qwen3-8B`, `Qwen/Qwen2.5-7B-Instruct`, `meta-llama/Meta-Llama-3.1-8B-Instruct` | small checkpoints are the reliably free ones | agg |

## Tier 2 — wired, but not actually free

| Module | Reality as of 2026-09-10 |
|---|---|
| **Cerebras** | The no-card free tier **ended August 2026**. New accounts need a payment method and get $5 of credit expiring in 30 days. Models: `gpt-oss-120b`, `qwen-3-235b-a22b-instruct-2507`, `zai-glm-4.7`, `llama3.1-8b`, `qwen-3-32b`. `llama-3.3-70b` is gone. |
| **DeepSeek** | Not free, but the cheapest strong option. Only `deepseek-v4-flash` and `deepseek-v4-pro` answer — `deepseek-chat`/`deepseek-reasoner` were retired 2026-07-24 15:59 UTC. 1M context. |
| **Vercel AI Gateway** | $5/month renewing credit, zero token markup. Current IDs: `anthropic/claude-sonnet-4.5`, `anthropic/claude-haiku-4.5`, `openai/gpt-5.6-luna`, `google/gemini-3-flash`. `anthropic/claude-3.5-sonnet` no longer resolves. |
| **Google Antigravity** | **Retired from the app.** It has no public inference API; the old config POSTed Claude IDs to the Gemini endpoint and always 404'd. |

## Tier 3 — free modules NOT yet wired, worth adding next

Found while searching; each needs an in-app check before it is trusted.

| Module | Why it is interesting | Free allowance | Conf |
|---|---|---|---|
| **GitHub Models** | GPT-4o / GPT-4.1 / o3 / Grok-3 class models on a GitHub token you may already have | 50–150 req/day, 10–15 RPM | agg |
| **Cohere** | Command R+ and Embed 4; good for the Knowledge/RAG tab | 1,000 calls/month (non-commercial) | agg |
| **HuggingFace Inference** | 300+ community models, one key | small monthly credits | agg |
| **xAI** | Grok 4 / Grok 4.1 Fast | $25 signup credit, not a standing tier | agg |
| **AI21 Labs** | Jamba Large/Mini, 200 RPM | $10 credit / 3 months | agg |
| **Fireworks AI** | Llama 3.1 405B, DeepSeek R1 | 10 RPM free, limited without a card | agg |
| **Scaleway** | Devstral 2 123B, Qwen3.5 400B VLM, Mistral Large 675B | EU-hosted free tier | agg |
| **Pollinations** (images) | `gen.pollinations.ai` now needs a key, but `GET https://image.pollinations.ai/prompt/{prompt}` is still anonymous | ~1 request / 15 s, may watermark | docs |

---

## What changed in the app to go with this list

1. **`remote_models.json` v3.0** — the runtime catalog. Installed apps fetch it
   from GitHub raw, so pushing it to `main` repairs existing installs with no new
   IPA. It now carries `fallbackChain`, `retiredModels`, and `free`/`requiresCard`/
   `status` per provider, plus a top-level `deprecated` map.
2. **`ModelCatalog` self-healing** — a retired ID is rewritten to its replacement
   before the request, and a model-not-found response walks to the next model in
   the chain. Both the Gemini and OpenAI transports do this.
3. **`tools/validate_catalog.py`** — fails the build if any dead ID appears in the
   catalog, the compiled defaults, or the offline fallback JSON.
4. **`tools/sync_fallback_json.py`** — regenerates the two compiled-in copies from
   the JSON so they cannot drift.

## Adding a provider

1. Add the case to `ProviderID` and every exhaustive switch
   (`tools/validate_catalog.py` reports any you miss).
2. Add `baseURL(for:)`, a default model, and an entry in `remote_models.json`
   with a `fallbackChain`.
3. Run `python3 tools/sync_fallback_json.py && python3 tools/validate_catalog.py`.
4. `ProviderLiveModuleStore` discovers its models automatically.
