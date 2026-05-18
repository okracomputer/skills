# OkraPDF CLI Reference

Use JSON output for agent workflows.

## Auth

```bash
okra auth status
okra auth login
```

## Upload

```bash
okra upload ./report.pdf --json
```

Returns a document id such as `doc-...`.

## Codex Panel Bridge

```bash
okra bridge serve
```

The bridge binds to `127.0.0.1:7373`, serves the local viewer, proxies document page/status data with the CLI API key, and exposes the active PDF selection.

Open:

```text
http://127.0.0.1:7373/viewer?doc=<docId>
```

Drag on a PDF page. The page will show "Selection synced to Codex bridge" when the bbox is posted.

## Selection

```bash
okra select --json
```

Returns:

```json
{
  "docId": "doc-...",
  "page": 1,
  "nodeId": "local-viewer-p1",
  "bbox": { "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.1 },
  "selectedAt": "2026-05-18T12:00:00.000Z",
  "source": "http://127.0.0.1:7373"
}
```

## Crop The Current Selection

When the user highlights a region, crop the actual pixels before answering:

```bash
node <skill-dir>/scripts/crop-selection.mjs --out /tmp/okra-selection.png
```

Then inspect the crop image and use that as the source of truth.

The helper requires ImageMagick's `magick` command. If it is unavailable, manually fetch the page image and crop with any available image tool:

```bash
curl -fsS -o /tmp/okra-page.png \
  "http://127.0.0.1:7373/viewer/doc/<docId>/pages/<page>/image"
```

Convert normalized bbox values to pixels using the page image width and height:

```text
x_px = bbox.x * image_width
y_px = bbox.y * image_height
w_px = bbox.width * image_width
h_px = bbox.height * image_height
```

## Ask About The Current Selection

```bash
okra ask "What is in the selected region?" --selection --json
```

## Extract From The Current Selection

```bash
okra extract --selection --schema ./schema.json --json
```

Inline schema is allowed:

```bash
okra extract --selection \
  --schema '{"type":"object","properties":{"total":{"type":"string"}}}' \
  --json
```

## Hosted Embed Fallback

```text
https://app.okrapdf.com/documents?document=<docId>&view=review&embed=codex
```

Use the local viewer when auth in the Codex browser is awkward. Use the hosted embed when the user is already signed in.
