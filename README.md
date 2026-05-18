# OkraPDF Agent Skills

Agent skills for working with PDFs. Most are bound to the [OkraPDF API](https://api.okrapdf.com); **[pdf-parse-qa](skills/pdf-parse-qa/) is vendor-neutral** (bring your own parser - HuggingFace VLMs, Reducto, LlamaParse, Azure DI, anything).

This repo is also packaged as an OkraPDF Codex plugin, using the same MagicPath-style shape:

- `npx skills add okrapdf/skills --skill okrapdf` for the skill-first install.
- `codex plugin marketplace add okrapdf/skills` for Codex plugin discovery once you want the plugin surface.
- Claude Code-compatible metadata is included under `.claude-plugin/`.

## Skills

| JTBD | Skill | API key needed | What it teaches |
|------|-------|---|-----------------|
| Use OkraPDF as a Codex-native interactive PDF panel | [okrapdf](skills/okrapdf/) | OkraPDF | MagicPath-style agent IDE loop: run `okra bridge serve`, open `http://127.0.0.1:7373/viewer?doc=<docId>`, read `okra select`, crop the selected pixels, then return JSON or run `okra ask/extract --selection`. |
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

For the Codex-native PDF panel, install `okrapdf`, then use:

```bash
npx skills add okrapdf/skills --skill okrapdf
okra bridge serve
```

Open `http://127.0.0.1:7373/viewer?doc=<docId>`, drag-select a region, and ask your agent about "this selection." The viewer shows "Selection synced to Codex bridge" when `okra select --json` can read it.

For visual questions or JSON from a highlight, the `okrapdf` skill tells the agent to crop the actual selected pixels first:

```bash
node <skill-dir>/scripts/crop-selection.mjs --out /tmp/okra-selection.png
```

That crop is the source of truth for what the user highlighted.

For `pdf-parse-qa`: no signup needed. Open the [skill's SKILL.md](skills/pdf-parse-qa/SKILL.md) and follow the workflow with whichever parser(s) you're evaluating.

## Links

- [Documentation](https://docs.okrapdf.com)
- [API Reference](https://api.okrapdf.com)
- [SDK](https://github.com/okrapdf/sdk)
