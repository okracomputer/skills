# OkraPDF Agent Skills

Agent skills for working with PDFs. Most are bound to the [OkraPDF API](https://api.okrapdf.com); **[pdf-parse-qa](skills/pdf-parse-qa/) is vendor-neutral** (bring your own parser - HuggingFace VLMs, Reducto, LlamaParse, Azure DI, anything).

Run this to open a local PDF parser dashboard. It needs no account:

```bash
npx okrapdf report.pdf
```

This repo is also packaged as an okraPDF Codex plugin:

- `npx skills add okrapdf/skills --skill okrapdf` for the skill-first install.
- `codex plugin marketplace add okrapdf/skills` for Codex plugin discovery once you want the plugin surface.
- Claude Code-compatible metadata is included under `.claude-plugin/`.

## Skills

| JTBD | Skill | API key needed | What it teaches |
|------|-------|---|-----------------|
| Parse a PDF locally, side by side with hover source mapping | [okrapdf](skills/okrapdf/) | **none** — local models or your own key | `npx okrapdf` serves a dashboard on localhost: PDF and parsed blocks with two-way hover, local model detection (Ollama, LM Studio, vLLM, llama.cpp, MLX, Jan), your own API keys, and ParseBench scoring with the official evaluator. |
| Get a completion endpoint on a PDF, fast | [okra-curl](skills/okra-curl/) | OkraPDF | `curl` cookbook for `POST /v1/documents` → OpenAI-compatible `POST /document/{id}/chat/completions`, structured extraction with `response_format`, exports, page images. The fastest path from "I have a PDF" to "I have an API." |
| Generate a designed PDF from an agent | [okra-create](skills/okra-create/) | OkraPDF | `POST /render` (baked design system) + `POST /browser/html-to-pdf` (custom HTML cover) + `POST /codemode/run` (composed). One Worker, three modes. |
| Turn a collection into a navigable wiki | [okra-wiki](skills/okra-wiki/) | OkraPDF | Collection export → per-doc synthesis → static site. Built on `GET /v1/collections/{id}/export`, `POST /v1/sandbox/run`, and the per-document chat-completion endpoint. |
| A/B test PDF parsers (Reducto vs LlamaParse vs Qwen2.5-VL vs Gemini Flash vs …) | [pdf-parse-qa](skills/pdf-parse-qa/) | **none** — BYO parser | Hosted block-by-block validator. Adapters for HuggingFace VLMs, Gemini, Reducto, OkraPDF facets. Vote ↑↓ 1/2/3, export verdict JSON, compare per-label pass-rates. |

## Install

```bash
# All
npx skills add okrapdf/skills --all

# Just one
npx skills add okrapdf/skills --skill okrapdf
npx skills add okrapdf/skills --skill okra-curl
npx skills add okrapdf/skills --skill okra-create
npx skills add okrapdf/skills --skill okra-wiki
npx skills add okrapdf/skills --skill pdf-parse-qa

# For a specific agent (Claude Code, Cursor, OpenCode...)
npx skills add okrapdf/skills -a claude-code -g
```

Codex plugin marketplace install:

```bash
codex plugin marketplace add okrapdf/skills
```

Then open the Codex plugin directory and install **OkraPDF** from the OkraPDF marketplace. For local development:

```bash
codex plugin marketplace add /Users/steventsao_personal/dev/okrapdf-skills
```

## Quick start

For the OkraPDF-bound skills:
1. Get an API key at [okrapdf.com](https://okrapdf.com)
2. `export OKRA_API_KEY=okra_...`
3. Pick a JTBD above; the SKILL.md has copy-pasteable curl examples.

For the local dashboard, install the skill and tell your agent to open a PDF:

```bash
npx skills add okrapdf/skills --skill okrapdf
```

## Links

- [Documentation](https://docs.okrapdf.com)
- [API Reference](https://api.okrapdf.com)
- [SDK](https://github.com/okrapdf/sdk)
