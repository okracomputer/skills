---
name: okrapdf
description: Use OkraPDF as a Codex-native interactive PDF panel. Trigger when the user wants to open a PDF in OkraPDF inside Codex, inspect the current PDF selection, extract or ask about a selected table/region/text span, or reproduce the MagicPath-style "select in the web app, act from the agent" workflow with `okra bridge serve`, `okra select`, `okra ask --selection`, and `okra extract --selection`.
metadata:
  author: OkraPDF
  source: https://github.com/okrapdf/skills
allowed-tools: Bash(okra *), Bash(npx okrapdf *), Bash(npm install -g okrapdf)
user-invocable: true
---

# OkraPDF Codex Panel

Use this skill when the user is looking at a PDF in OkraPDF and wants the agent to act on the selected page region, table, block, or text.

This is the MagicPath pattern for PDFs:

1. `okra bridge serve` starts a loopback viewer and selection bridge.
2. OkraPDF runs in the agent IDE browser pane at `http://127.0.0.1:7373/viewer?doc=<docId>`.
3. The user drags on the PDF page; the viewer shows "Selection synced to Codex bridge."
4. The agent reads that state with `okra select --json`.
5. For visual grounding, the agent crops the actual selected pixels and inspects the crop.
6. The agent returns JSON, or runs `okra ask --selection` / `okra extract --selection` when document reasoning or typed extraction is needed.

For command details, see `references/cli-reference.md`.

## Interaction Model

Treat the bridge selection as a visual pointer, not as a final answer. A bbox may point at logos, a chart, a table, a paragraph, or whitespace. When the user asks "what is this?", "give me JSON", "extract this", or otherwise refers to a highlighted region, do this in order:

1. Read the active selection with `okra select --json`.
2. Crop the selected pixels from the page image.
3. Inspect the crop visually.
4. Return JSON grounded in what is visible in the crop.
5. Use `okra ask --selection` or `okra extract --selection` only after the crop confirms the selected region and when semantic document context is useful.

Do not rely on `okra ask --selection` alone to identify the selected region; it can answer from nearby document context. The crop is the source of truth for "what did the user highlight?"

## First Step

Check the CLI and auth state:

```bash
okra auth status
```

If `okra` is missing, install it:

```bash
npm install -g okrapdf
```

If auth is missing, run:

```bash
okra auth login
```

## Start The Local PDF Panel

Start the bridge in a background terminal/session:

```bash
okra bridge serve
```

The bridge listens only on `127.0.0.1:7373`. It serves a local viewer, proxies OkraPDF page/status data with the CLI's API key server-side, accepts local selection posts, and exposes the latest selection at `GET /selection`.

Do not expose the bridge through a tunnel or bind it to a public interface.

Then open the local viewer in the IDE/browser pane:

```text
http://127.0.0.1:7373/viewer?doc=<docId>
```

The user should drag on a PDF page to select a bbox before selection-aware commands are run. When the selection is accepted, the viewer displays "Selection synced to Codex bridge."

## Hosted Fallback

For an existing OkraPDF document id:

```text
https://app.okrapdf.com/documents?document=<docId>&view=review&embed=codex
```

Open that URL in the IDE/browser pane. The user should select a PDF bbox, table, or text block in the review surface before selection-aware commands are run.

If the user has a local PDF instead of a document id:

```bash
okra upload ./report.pdf --json
```

Then open the returned document id with the embed URL above.

## Read Current Selection

Before acting on phrases like "this table", "the selected section", "that number", or "extract this", read the active selection:

```bash
okra select --json
```

Expected shape:

```json
{
  "docId": "doc-abc123",
  "page": 2,
  "nodeId": "node-42",
  "bbox": { "x": 0.12, "y": 0.34, "width": 0.52, "height": 0.18 },
  "text": "Selected text or table payload",
  "selectedAt": "2026-05-18T12:00:00.000Z",
  "source": "https://app.okrapdf.com"
}
```

If no selection is available, tell the user to click a region in the OkraPDF panel, then retry `okra select --json`.

If the user says "this", "that", "the highlighted region", "the selected table", or similar, do not ask them to paste coordinates. Run `okra select --json` first and use the returned `docId`, page, and bbox.

## Crop The Selected Pixels

Preferred helper:

```bash
node <skill-dir>/scripts/crop-selection.mjs --out /tmp/okra-selection.png
```

Then inspect `/tmp/okra-selection.png` with the agent's image viewer and answer from that visual crop.

The helper prints JSON like:

```json
{
  "selection": { "docId": "doc-...", "page": 1, "bbox": { "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.1 } },
  "cropPath": "/tmp/okra-selection.png",
  "crop": { "x": 108, "y": 320, "width": 420, "height": 180 }
}
```

If the helper is unavailable, reproduce the same logic manually: fetch the current page image from `http://127.0.0.1:7373/viewer/doc/<docId>/pages/<page>/image`, convert the normalized bbox to pixels, crop it, inspect the image, then answer.

## Ask About The Selection

Use this for natural-language questions about the selected region:

```bash
okra ask "What is this table saying?" --selection --json
```

For streaming text:

```bash
okra ask "Summarize the selected section." --selection --stream
```

The CLI reads the selected `docId`, page, node id, bbox, and text from the bridge and appends them as explicit context to the document question.

## Extract The Selection

Use this when the user wants JSON, CSV-ready fields, line items, table rows, or a typed answer from the selected region:

```bash
okra extract --selection --schema ./schema.json --json
```

Inline schema is also allowed:

```bash
okra extract --selection \
  --schema '{"type":"object","properties":{"rows":{"type":"array","items":{"type":"object"}}}}' \
  --json
```

Prefer a narrow schema that matches the user's requested output. Keep the user-facing answer focused on the returned JSON or the saved output file.

## Common Flows

### "Extract this table as JSON"

```bash
okra select --json
node <skill-dir>/scripts/crop-selection.mjs --out /tmp/okra-selection.png
```

Inspect the crop. If it is a table, return JSON directly from the visible rows/columns, or run `okra extract --selection --schema ./table.schema.json --json` after the crop confirms the target region.

### "What does this highlighted paragraph mean?"

```bash
okra select --json
node <skill-dir>/scripts/crop-selection.mjs --out /tmp/okra-selection.png
okra ask "Explain the selected paragraph in plain English." --selection
```

### "Upload this PDF and let me select from it"

```bash
okra upload ./report.pdf --json
```

Open:

```text
http://127.0.0.1:7373/viewer?doc=<docId>
```

Then:

```bash
okra select --json
```

## Rules

- Use `okra select --json` whenever the user refers to "this", "that", "selected", "highlighted", or a visible PDF region.
- For "what do you see?", "give me JSON", and visual disambiguation, crop and inspect the selected pixels before using document Q&A.
- Prefer `okra ask --selection` for explanation, verification, summarization, and QA.
- Prefer `okra extract --selection --schema ...` for structured output.
- Do not guess a document id if the bridge selection has one.
- Do not run `okra bridge serve` bound to anything other than loopback.
- If the bridge is not running, start it or tell the user exactly which command to run.
- If the selected text is empty but bbox/page is present, proceed; OkraPDF can still answer from page and bbox context.
- This skill is for the interactive Codex-native panel. For raw HTTP recipes, use `okra-curl`; for generated PDFs, use `okra-create`; for parser bake-offs, use `pdf-parse-qa`.
