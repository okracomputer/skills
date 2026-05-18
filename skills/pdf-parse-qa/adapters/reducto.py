"""Reducto /parse adapter — uploads PDF, polls, transforms into pdf-parse-qa data contract.

Usage:
    REDUCTO_API_KEY=... python adapters/reducto.py path/to/doc.pdf > blocks-reducto.json

Reducto returns absolute pixel bboxes plus the rendered page dimensions per page; we
normalize against those so the widget can place overlays on any render scale.

Pricing: ~$0.005/page for /parse (2026-05 list price). Layout + table extraction.
"""

import json, os, sys, time
import requests

PDF = sys.argv[1]
KEY = os.environ["REDUCTO_API_KEY"]
BASE = "https://platform.reducto.ai"

# Map Reducto block_type → our canonical labels (close-enough mapping).
LABEL_MAP = {
    "Title": "Title", "Section Header": "Section-header", "Page Header": "Page-header",
    "Page Footer": "Page-footer", "Text": "Text", "List Item": "List-item",
    "Table": "Table", "Figure": "Picture", "Caption": "Caption", "Code": "Code",
}


def upload(pdf_path: str) -> str:
    with open(pdf_path, "rb") as f:
        r = requests.post(f"{BASE}/upload", headers={"Authorization": f"Bearer {KEY}"}, files={"file": f}, timeout=120)
    r.raise_for_status()
    return r.json()["file_id"]


def parse(file_id: str) -> dict:
    r = requests.post(
        f"{BASE}/parse",
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json={"document_url": f"jobid://{file_id}", "options": {"extraction_mode": "ocr", "chunking": {"chunk_mode": "page"}}},
        timeout=600,
    )
    r.raise_for_status()
    job = r.json()
    job_id = job.get("job_id") or job.get("id")
    # poll
    while True:
        s = requests.get(f"{BASE}/job/{job_id}", headers={"Authorization": f"Bearer {KEY}"}, timeout=30).json()
        if s["status"] == "Completed":
            return s["result"]
        if s["status"] in ("Failed", "Error"):
            raise RuntimeError(f"reducto parse failed: {s}")
        time.sleep(2)


def to_contract(result: dict) -> dict:
    pages = []
    for ch in result.get("chunks", []):
        # Reducto's per-page blocks live under chunk.blocks with absolute pixel coords.
        for block in ch.get("blocks", []):
            pass  # handled below
        page_num = ch.get("page", 1)
        # page render dims (used to normalize) — Reducto sometimes returns under chunk.metadata.
        meta = ch.get("metadata", {})
        W, H = meta.get("page_width", 1000), meta.get("page_height", 1000)
        bs = []
        for b in ch.get("blocks", []):
            bbox = b.get("bbox") or b.get("boundingBox") or {}
            x0, y0 = bbox.get("left", 0), bbox.get("top", 0)
            x1, y1 = bbox.get("right", x0), bbox.get("bottom", y0)
            bs.append({
                "label": LABEL_MAP.get(b.get("type", "Text"), "Text"),
                "value": (b.get("content") or "").strip()[:500],
                "bbox": {"x": x0 / W, "y": y0 / H, "w": max(0.001, (x1 - x0) / W), "h": max(0.001, (y1 - y0) / H)},
            })
        pages.append({"page_number": page_num, "blocks": bs})
    return {"pages": pages}


def main():
    print("uploading…", file=sys.stderr)
    fid = upload(PDF)
    print(f"parsing (file_id={fid})…", file=sys.stderr)
    result = parse(fid)
    out = to_contract(result)
    print(f"got {sum(len(p['blocks']) for p in out['pages'])} blocks across {len(out['pages'])} pages", file=sys.stderr)
    json.dump(out, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
