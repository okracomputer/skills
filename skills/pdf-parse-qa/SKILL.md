---
name: pdf-parse-qa
description: Block-by-block A/B testing for PDF / VLM document parsers. Bring your own PDF and your own parser (HuggingFace Qwen2.5-VL, Gemini Flash, Mistral OCR, Reducto, LlamaParse, Azure Document Intelligence, AWS Textract, Unstructured, MinerU, Docling — or anything that emits text+bbox), run them through the same hosted validator UI, vote pass/partial/fail on every block with `↑↓ 1/2/3`, export JSON, compare per-label pass-rates. Triggered by "compare PDF parsers", "pick a VLM for PDFs", "bake-off Reducto vs LlamaParse", "evaluate Qwen2.5-VL on documents", "ParseBench-style accuracy QA", "which OCR is best for my docs". No SaaS account required — adapters produce a tiny JSON file, the hosted widget at embed.okrapdf.com renders it. Inspired by Label Studio + Daloopa + Adobe Acrobat "Find Suspects" review queues.
---

# pdf-parse-qa

A structured way to A/B test PDF parsers — VLMs, OCRs, layout APIs, anything that takes a PDF page and returns text + bounding boxes. You bring the parsers (HuggingFace models, vendor APIs, local libs), the skill brings the validator UI, the data contract, and adapter examples.

## Why this exists

Picking a PDF parser is a benchmark problem disguised as a procurement problem. Vendor demos pick the easy pages. Per-block accuracy varies wildly by **label** (a parser may nail Title and Section-header but butcher Table or Picture). A summary "F1 score" hides that.

This skill gives you the per-block, per-label, source-anchored audit that vendor benchmarks don't.

## Workflow

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────┐
│ your PDF    │ →  │ your parser      │ →  │ blocks.json     │ →  │ validator UI │
│ (CORS host) │    │ (one of adapters)│    │ (this contract) │    │ (vote ↑↓123) │
└─────────────┘    └──────────────────┘    └─────────────────┘    └──────────────┘
                                                                          ↓
                                                                  verdicts.json
                                                                  → spreadsheet / Langfuse
```

1. **Host the PDF** somewhere CORS-open from `embed.okrapdf.com` (GitHub raw, R2, S3 with CORS, gist).
2. **Run a parser adapter** (`adapters/*.py`) to produce `blocks.json` matching the data contract below. Host it the same way.
3. **Open the validator** with both URLs as query params:
   ```
   https://embed.okrapdf.com/e/af8cc13f3d270c4b32f9245a?pdfUrl=<YOUR_PDF>&dataUrl=<YOUR_BLOCKS>&docTitle=Apple%2010-K%20(reducto)
   ```
4. **Vote**: click a row or use `↑↓` to navigate, `1/2/3` to score pass/partial/fail, `0` clears. Bias toward `pass`; mark only deviations. Bbox cross-highlights on the canvas as you go.
5. **Copy verdicts as JSON** when done. Paste into a sheet keyed by `(parser, label) → pass-rate`. That's the bake-off currency.

## Data contract

Adapters MUST emit JSON in this shape. Coordinates are **0–1 normalized** (origin = top-left), so they survive any PDF render scale.

```json
{
  "pages": [
    {
      "page_number": 1,
      "blocks": [
        {
          "label": "Title",
          "value": "Form 10-K",
          "bbox": { "x": 0.10, "y": 0.05, "w": 0.80, "h": 0.03 }
        },
        {
          "label": "Table",
          "value": "Title of each class | Name of each exchange ...",
          "bbox": { "x": 0.08, "y": 0.32, "w": 0.84, "h": 0.18 }
        }
      ]
    },
    { "page_number": 2, "blocks": [ ... ] }
  ]
}
```

Required: `pages[].page_number`, `pages[].blocks[].bbox.{x,y,w,h}`.
Recommended: `pages[].blocks[].label`, `pages[].blocks[].value`.

A starter file lives at [`examples/sample-blocks.json`](examples/sample-blocks.json) — sanity-test the widget before writing an adapter.

## Validator URL

```
https://embed.okrapdf.com/e/af8cc13f3d270c4b32f9245a
  ?pdfUrl=<CORS-open PDF URL>
  &dataUrl=<CORS-open blocks.json URL>
  &docTitle=<display title, URL-encoded>
  &scale=1.5   (optional, default 1.5 — pdf.js render scale)
```

Verdicts persist in `sessionStorage` keyed by `dataUrl`, so refreshing the tab won't lose your work.

## Adapters

Reference scripts in `adapters/`. Each one: takes a PDF file path, writes `blocks.json` in the contract above. ~30–80 lines. Add your own — PRs welcome.

| File | Parser | Auth | Notes |
|---|---|---|---|
| `adapters/gemini-flash.py` | Google Gemini 3 Flash (Thinking) | `GEMINI_API_KEY` | Uses the ParseBench prompt; native `[y_min, x_min, y_max, x_max]` bbox order normalized to `{x,y,w,h}` |
| `adapters/qwen2-vl-hf.py` | HuggingFace `Qwen/Qwen2.5-VL-7B-Instruct` | none (local) | Local GPU; ~8GB VRAM @ fp16. Latest open-weights VL model. |
| `adapters/reducto.py` | Reducto `/parse` | `REDUCTO_API_KEY` | One of the strongest commercial table extractors as of 2026. |
| `adapters/llamaparse.py` | LlamaIndex LlamaParse (Premium / Agentic modes) | `LLAMA_CLOUD_API_KEY` | Stalwart; agentic mode handles charts. |
| `adapters/azure-di.py` | Azure Document Intelligence (prebuilt-layout) | `AZURE_DI_ENDPOINT`, `AZURE_DI_KEY` | Enterprise default; strong layout, weaker on free-form OCR. |
| `adapters/okra.py` | OkraPDF facets (any of 14: gemini-3-flash-minimal, reducto-parse, llamaparse-premium, mistral-ocr, mineru, unstructured, chandra-ocr, ...) | `OKRA_API_KEY` | One adapter, 14 parsers — useful if you already have an OkraPDF account. |

### Adapters worth adding (PRs welcome)

- **Mistral OCR** — `mistral-ocr-latest` is fast and cheap; good Mistral-vs-Gemini cost angle
- **AWS Textract** — `analyze_document` with `FORMS|TABLES|LAYOUT`
- **Google Document AI** — layout parser processor
- **MinerU** — local Python, strong on academic layout
- **Docling** — IBM open-source, fast on scientific PDFs
- **Unstructured** — `unstructured.partition.pdf` with `hi_res`
- **Chandra OCR** — emerging open-source OCR

## Bake-off recipe

Same PDF, N parsers. Each adapter writes `blocks-<parser>.json`. Host all of them. Open one validator tab per parser. Score each. Aggregate by `(parser, label) → pass-rate`. That's a buyer-grade comparison your CFO can read.

```bash
# Same source PDF, four parsers in parallel
PDF=https://raw.githubusercontent.com/you/repo/main/test.pdf

python adapters/gemini-flash.py test.pdf > blocks-gemini.json
python adapters/reducto.py     test.pdf > blocks-reducto.json
python adapters/llamaparse.py  test.pdf > blocks-llamaparse.json
python adapters/qwen2-vl-hf.py test.pdf > blocks-qwen25vl.json

# Upload to gist / R2 / S3 (CORS open) — then:
for P in gemini reducto llamaparse qwen25vl; do
  echo "https://embed.okrapdf.com/e/af8cc13f3d270c4b32f9245a?pdfUrl=$PDF&dataUrl=https://.../blocks-$P.json&docTitle=$P"
done
```

Open each URL in a tab, score every page, copy verdicts, paste into:

| parser | Title pass | Table pass | Picture pass | Section-header pass | overall |
|---|---|---|---|---|---|
| gemini | 19/20 | 8/12 | 4/4 | 22/22 | 53/58 (91%) |
| reducto | 18/20 | 11/12 | 3/4 | 22/22 | 54/58 (93%) |
| ... |

## Verdict export shape

`Copy verdicts as JSON` → clipboard:

```json
{
  "source": { "dataUrl": "https://.../blocks-reducto.json", "pdfUrl": "https://.../test.pdf" },
  "docTitle": "Apple 10-K (reducto)",
  "verdicts": [
    { "page": 1, "blockIndex": 0, "verdict": "pass" },
    { "page": 1, "blockIndex": 7, "verdict": "fail" },
    { "page": 2, "blockIndex": 3, "verdict": "partial" }
  ],
  "capturedAt": "2026-05-18T05:40:52Z"
}
```

When run against an OkraPDF facet (no `dataUrl`), `source` becomes `{ "docId": "...", "facet": "..." }` instead. Same shape, different provenance.

## Keyboard

| Key | Action |
|---|---|
| `↑` / `k` | previous block |
| `↓` / `j` | next block |
| `1` | mark pass |
| `2` | mark partial |
| `3` | mark fail |
| `0` | clear verdict |
| Click row | focus block |
| Click bbox | focus row |
| `Show source` | re-scroll + flash the focused block |

## Hosting tips (CORS-open URLs)

The widget runs in the browser at `embed.okrapdf.com` and `fetch`es your URLs cross-origin. They must respond with `Access-Control-Allow-Origin: *` (or include `embed.okrapdf.com`).

| Host | Works out-of-the-box | Notes |
|---|---|---|
| GitHub raw (`raw.githubusercontent.com`) | ✅ | Use for small JSON + sample PDFs in your repo |
| GitHub gist (`gist.githubusercontent.com/.../raw/...`) | ✅ | Best for one-off blocks.json — `gh gist create blocks.json --public` |
| Cloudflare R2 with public bucket + CORS | ✅ | Best for many large PDFs |
| AWS S3 with CORS policy `AllowedOrigin: *` | ✅ | Add `<CORSRule>` to bucket |
| Vercel/Netlify static | ✅ | Default headers are CORS-open |
| **Local file://** | ❌ | Browser blocks cross-origin file:// — host even short-lived runs via `python -m http.server` + a tunnel |

For private PDFs you don't want to host: see *Standalone mode* below.

## Standalone mode (no embed.okrapdf.com)

The widget is a single HTML file. Clone the repo's parent (this skill ships SKILL.md only; the widget source lives at [`okrapdf/manual-app`](https://github.com/okrapdf/manual-app) under `embeds/parse-validator/`) and open `dist/index.html` directly. Same `?pdfUrl=&dataUrl=` params work. Use this for confidential PDFs that can't leave your machine.

## See also

- **OkraPDF facets** (`okra-curl` skill in this repo) — if you want a hosted parser store rather than running 6 SDKs yourself, OkraPDF's `/v1/documents/{id}/facets/{name}/run` exposes 14 parsers behind one API. Use the `adapters/okra.py` adapter then.
- **Label Studio** — heavier, server-installed, supports per-cell table validation. Better when you're building a ground-truth dataset.
- **Daloopa** — commercial, finance-vertical, similar UX inspired this widget.
- **ParseBench** (arXiv 2604.08538) — the benchmark this skill operationalizes.

## License

MIT. Adapter scripts are reference implementations; PRs welcome at [okrapdf/skills](https://github.com/okrapdf/skills).
