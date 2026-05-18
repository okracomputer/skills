"""Gemini 3 Flash adapter — page-by-page ParseBench prompt, emits the pdf-parse-qa data contract.

Usage:
    GEMINI_API_KEY=... python adapters/gemini-flash.py path/to/doc.pdf > blocks-gemini.json

Output: { "pages": [{ "page_number": N, "blocks": [...] }] } on stdout.

Costs: ~$0.005/page at gemini-3-flash-preview pricing (2026-05). 160-page doc ≈ $0.80.
Bbox order: Gemini emits [y_min, x_min, y_max, x_max] normalized 0–1000; we convert to {x, y, w, h} 0–1.
"""

import base64, json, os, re, sys
import fitz  # PyMuPDF
import requests

PDF = sys.argv[1]
KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-3-flash-preview"

SYSTEM = "You are a document parser. Your task is to convert document images to clean, well-structured markdown."
USER = """Convert this page to clean markdown.

Rules:
- Preserve document structure and reading order.
- Tables → HTML <table> with colspan/rowspan for merged cells.
- Charts → HTML table with flat combined column headers.
- Images / figures → bracketed description, e.g. [bar chart of revenue by year].
- Wrap every layout region in <div data-bbox="[y_min, x_min, y_max, x_max]" data-label="LABEL">CONTENT</div>.
  - data-bbox uses Gemini-native order [y_min, x_min, y_max, x_max], normalized 0–1000.
  - data-label ∈ {Title, Section-header, Page-header, Page-footer, Text, List-item, Table, Picture, Caption, Code}.
- Every visible region must be wrapped. Do not emit content outside a wrapping div.
"""

REGION_RE = re.compile(
    r'<div\s+data-bbox="\[(?P<y0>[\d.]+),\s*(?P<x0>[\d.]+),\s*(?P<y1>[\d.]+),\s*(?P<x1>[\d.]+)\]"\s+data-label="(?P<label>[^"]+)"\s*>(?P<value>.*?)</div>',
    re.DOTALL,
)


def parse_page(pdf_path: str, page_num: int) -> dict:
    doc = fitz.open(pdf_path)
    pix = doc[page_num - 1].get_pixmap(dpi=200)
    img_b64 = base64.b64encode(pix.tobytes("png")).decode()
    doc.close()

    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"role": "user", "parts": [
                {"inlineData": {"mimeType": "image/png", "data": img_b64}},
                {"text": USER},
            ]}],
            "generationConfig": {"temperature": 0.0, "thinkingConfig": {"thinkingLevel": "low"}, "maxOutputTokens": 8192},
        },
        timeout=180,
    )
    r.raise_for_status()
    cand = r.json()["candidates"][0]
    md = "".join(p.get("text", "") for p in cand["content"]["parts"])

    blocks = []
    for m in REGION_RE.finditer(md):
        y0, x0, y1, x1 = float(m["y0"]) / 1000, float(m["x0"]) / 1000, float(m["y1"]) / 1000, float(m["x1"]) / 1000
        blocks.append({
            "label": m["label"],
            "value": re.sub(r"\s+", " ", m["value"]).strip()[:500],
            "bbox": {"x": x0, "y": y0, "w": max(0.001, x1 - x0), "h": max(0.001, y1 - y0)},
        })
    return {"page_number": page_num, "blocks": blocks}


def main():
    doc = fitz.open(PDF)
    n_pages = len(doc)
    doc.close()
    print(f"parsing {n_pages} pages with {MODEL}…", file=sys.stderr)
    pages = []
    for p in range(1, n_pages + 1):
        try:
            page = parse_page(PDF, p)
            print(f"  page {p}/{n_pages}: {len(page['blocks'])} blocks", file=sys.stderr)
            pages.append(page)
        except Exception as e:
            print(f"  page {p} FAILED: {e}", file=sys.stderr)
    json.dump({"pages": pages}, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
