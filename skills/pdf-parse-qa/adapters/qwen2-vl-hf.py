"""Qwen2.5-VL-7B (HuggingFace) adapter — local GPU, no API.

Usage:
    pip install transformers accelerate qwen-vl-utils[decord] pymupdf
    python adapters/qwen2-vl-hf.py path/to/doc.pdf > blocks-qwen25vl.json

Hardware: ~8GB VRAM at fp16 (fits on RTX 2070 Super, 3060 12GB, 4060 Ti 16GB, etc.).
Costs: $0 marginal. Slower than API parsers — expect 5–15s/page on consumer GPU.
Quality: as of 2026, Qwen2.5-VL-7B is the strongest open-weights VL model for documents and
charts; the 72B variant is even stronger if you have the VRAM.

Bbox: Qwen emits absolute pixel coords in the rendered image; we normalize against image size.
"""

import base64, json, re, sys
import fitz  # PyMuPDF
import torch
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

PDF = sys.argv[1]
MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"
DPI = 200

PROMPT = """Detect every layout region on this document page. For each region output one line:

LABEL | x0,y0,x1,y1 | CONTENT

Where:
- LABEL ∈ {Title, Section-header, Page-header, Page-footer, Text, List-item, Table, Picture, Caption, Code}
- x0,y0,x1,y1 are pixel coords of the bbox in the input image
- CONTENT is the text content (markdown for tables, "[chart of …]" for figures)

Output every region in reading order. No commentary."""

LINE_RE = re.compile(r"^([\w\-]+)\s*\|\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\|\s*(.*)$")


def load_model():
    print("loading Qwen2.5-VL-7B…", file=sys.stderr)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID, torch_dtype=torch.float16, device_map="auto"
    )
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    return model, processor


def parse_page(model, processor, pdf_path: str, page_num: int) -> dict:
    doc = fitz.open(pdf_path)
    pix = doc[page_num - 1].get_pixmap(dpi=DPI)
    doc.close()
    img = Image.open(__import__("io").BytesIO(pix.tobytes("png"))).convert("RGB")
    W, H = img.size

    messages = [{"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": PROMPT}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[img], padding=True, return_tensors="pt").to(model.device)
    out_ids = model.generate(**inputs, max_new_tokens=2048, do_sample=False)
    out = processor.batch_decode(out_ids[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]

    blocks = []
    for line in out.splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        label, x0, y0, x1, y1, content = m.groups()
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        blocks.append({
            "label": label,
            "value": content.strip()[:500],
            "bbox": {"x": x0 / W, "y": y0 / H, "w": max(0.001, (x1 - x0) / W), "h": max(0.001, (y1 - y0) / H)},
        })
    return {"page_number": page_num, "blocks": blocks}


def main():
    doc = fitz.open(PDF)
    n_pages = len(doc)
    doc.close()
    model, processor = load_model()
    pages = []
    for p in range(1, n_pages + 1):
        page = parse_page(model, processor, PDF, p)
        print(f"  page {p}/{n_pages}: {len(page['blocks'])} blocks", file=sys.stderr)
        pages.append(page)
    json.dump({"pages": pages}, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
