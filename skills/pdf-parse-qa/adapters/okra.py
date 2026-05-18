"""OkraPDF facet adapter — pulls any of 14 parser facets and reshapes into the contract.

Usage:
    OKRA_API_KEY=... python adapters/okra.py <docId> [facet=gemini-3-flash-minimal] > blocks-okra.json

Use this when you already have an OkraPDF account and want to A/B test their hosted
parsers without running them yourself. The same `docId` can be run through multiple
facets in one account — each `facet` argument here produces a separate blocks file.

Available facets (2026-05): gemini-3-flash-minimal, reducto-parse, reducto-agentic,
llamaparse-fast, llamaparse-premium, llamaparse-agentic, mistral-ocr, mistral-ocr-annotated,
unstructured, mineru, chandra-ocr, chandra-ocr-raw, vlm-parsebench, azure-di-layout,
google-document-ai-ocr, textlayer.

If the facet hasn't been run on the doc yet, this script triggers it and polls. That can
take 10+ minutes and cost real $ on a long PDF — set FACET_AUTORUN=0 to disable.
"""

import json, os, sys, time
import requests

DOC = sys.argv[1]
FACET = sys.argv[2] if len(sys.argv) > 2 else "gemini-3-flash-minimal"
KEY = os.environ["OKRA_API_KEY"]
AUTORUN = os.environ.get("FACET_AUTORUN", "1") == "1"
API = "https://api.okrapdf.com"


def facet_status() -> dict:
    r = requests.get(f"{API}/document/{DOC}/facets", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
    r.raise_for_status()
    for f in r.json().get("facets", []):
        if f["facet"] == FACET:
            return f
    raise RuntimeError(f"facet {FACET} not found on {DOC}")


def wait_for_complete():
    while True:
        s = facet_status()
        if s["phase"] == "complete":
            return s
        if s["phase"] == "error":
            raise RuntimeError(f"facet errored: {s.get('error')}")
        print(f"  facet phase={s['phase']} pages={s.get('pages_completed', 0)}/{s.get('pages_total', '?')}", file=sys.stderr)
        time.sleep(15)


def kickoff():
    print(f"triggering facet run {FACET}…", file=sys.stderr)
    requests.post(f"{API}/document/{DOC}/facets/{FACET}/run", headers={"Authorization": f"Bearer {KEY}"}, timeout=30).raise_for_status()


def fetch_pages(n_pages: int) -> dict:
    pages = []
    for p in range(1, n_pages + 1):
        r = requests.get(f"{API}/v1/documents/{DOC}/facets/{FACET}/pages?from={p}&to={p}", timeout=60)
        if not r.ok:
            continue
        for page in r.json().get("pages", []):
            payload = json.loads(page.get("payload_json") or "{}")
            blocks = [b for b in payload.get("blocks", []) if b.get("bbox")]
            pages.append({
                "page_number": page.get("page_number", p),
                "blocks": [{"label": b.get("label", "Text"), "value": (b.get("value") or "")[:500], "bbox": b["bbox"]} for b in blocks],
            })
    return {"pages": pages}


def main():
    s = facet_status()
    if s["phase"] != "complete":
        if AUTORUN:
            kickoff()
            s = wait_for_complete()
        else:
            print(f"facet phase={s['phase']}; set FACET_AUTORUN=1 to trigger", file=sys.stderr)
            sys.exit(1)
    n_pages = s.get("pages_total") or s.get("pages_completed") or 0
    print(f"facet complete · {n_pages} pages · {s.get('anchors', 0)} blocks", file=sys.stderr)
    out = fetch_pages(n_pages)
    json.dump(out, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
