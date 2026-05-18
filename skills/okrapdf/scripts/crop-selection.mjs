#!/usr/bin/env node
import { execFile } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

function parseArgs(argv) {
  const options = {
    host: process.env.OKRA_BRIDGE_HOST || '127.0.0.1',
    port: Number(process.env.OKRA_BRIDGE_PORT || '7373'),
    out: '',
    padding: 20,
    scale: 2,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--host') options.host = argv[++i];
    else if (arg === '--port') options.port = Number(argv[++i]);
    else if (arg === '--out') options.out = argv[++i];
    else if (arg === '--padding') options.padding = Number(argv[++i]);
    else if (arg === '--scale') options.scale = Number(argv[++i]);
    else if (arg === '--help' || arg === '-h') {
      process.stdout.write([
        'Usage: node scripts/crop-selection.mjs [--out /tmp/selection.png]',
        '',
        'Reads the current OkraPDF bridge selection, fetches the selected page image,',
        'crops the selected bbox, and prints JSON with the crop path.',
        '',
        'Options:',
        '  --host <host>       Bridge host (default: 127.0.0.1)',
        '  --port <port>       Bridge port (default: 7373)',
        '  --out <path>        Crop output path',
        '  --padding <px>      Pixel padding around bbox (default: 20)',
        '  --scale <number>    Output resize multiplier (default: 2)',
        '',
      ].join('\n'));
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!Number.isFinite(options.port) || options.port < 1) {
    throw new Error('--port must be a positive number');
  }
  if (!Number.isFinite(options.padding) || options.padding < 0) {
    throw new Error('--padding must be a non-negative number');
  }
  if (!Number.isFinite(options.scale) || options.scale <= 0) {
    throw new Error('--scale must be a positive number');
  }

  return options;
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!response.ok) {
    throw new Error(`GET ${url} failed: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

async function fetchBytes(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`GET ${url} failed: ${response.status} ${await response.text()}`);
  }
  return Buffer.from(await response.arrayBuffer());
}

async function imageSize(path) {
  const { stdout } = await execFileAsync('magick', ['identify', '-format', '%w %h', path]);
  const [width, height] = stdout.trim().split(/\s+/).map(Number);
  if (!Number.isFinite(width) || !Number.isFinite(height)) {
    throw new Error(`Could not read image size for ${path}`);
  }
  return { width, height };
}

function pixelCrop(selection, image, padding) {
  if (!selection.bbox) {
    throw new Error('Current selection does not include a bbox');
  }

  const left = Math.max(0, Math.floor(selection.bbox.x * image.width) - padding);
  const top = Math.max(0, Math.floor(selection.bbox.y * image.height) - padding);
  const right = Math.min(image.width, Math.ceil((selection.bbox.x + selection.bbox.width) * image.width) + padding);
  const bottom = Math.min(image.height, Math.ceil((selection.bbox.y + selection.bbox.height) * image.height) + padding);
  const width = Math.max(1, right - left);
  const height = Math.max(1, bottom - top);

  return { x: left, y: top, width, height };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const baseUrl = `http://${options.host}:${options.port}`;
  const selection = await fetchJson(`${baseUrl}/selection`);
  const workDir = join(tmpdir(), 'okrapdf-selection');
  await mkdir(workDir, { recursive: true });

  const pageImagePath = join(workDir, `${selection.docId}-page-${selection.page}.png`);
  const cropPath = resolve(
    options.out || join(workDir, `${selection.docId}-page-${selection.page}-selection.png`),
  );

  const pageImage = await fetchBytes(
    `${baseUrl}/viewer/doc/${encodeURIComponent(selection.docId)}/pages/${selection.page}/image`,
  );
  await writeFile(pageImagePath, pageImage);

  const image = await imageSize(pageImagePath);
  const crop = pixelCrop(selection, image, options.padding);
  await execFileAsync('magick', [
    pageImagePath,
    '-crop',
    `${crop.width}x${crop.height}+${crop.x}+${crop.y}`,
    '+repage',
    '-resize',
    `${Math.round(options.scale * 100)}%`,
    cropPath,
  ]);

  process.stdout.write(JSON.stringify({
    selection,
    pageImagePath,
    cropPath,
    image,
    crop,
  }, null, 2));
  process.stdout.write('\n');
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
});
