#!/usr/bin/env node
// S.5.34: build plugins/okrapdf, the plugin folder for Anthropic's plugin directory.
// The directory blocks an npx range (okrapdf@^0.18.0), so the server and the skill name
// one exact okrapdf version. The folder holds only the offline okrapdf skill: the
// API-key skills stay at the repository root.
// Usage: node scripts/build-claude-plugin.mjs <okrapdf version>, then raise "version" in
// plugins/okrapdf/.claude-plugin/plugin.json and run `claude plugin validate plugins/okrapdf`.
import { mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const version = process.argv[2];
if (!/^\d+\.\d+\.\d+$/.test(version ?? '')) {
  console.error('Usage: node scripts/build-claude-plugin.mjs <okrapdf version, such as 0.18.0>');
  process.exit(1);
}

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = join(root, 'skills', 'okrapdf');
const plugin = join(root, 'plugins', 'okrapdf');
const skill = join(plugin, 'skills', 'okrapdf');

const pin = (text) =>
  text
    .replace(/^allowed-tools: .*$/m, `allowed-tools: Bash(npx okrapdf@${version} *), Bash(curl -s http://127.0.0.1*)`)
    .replaceAll(/npx okrapdf(@latest)?(?=[\s`])/g, `npx okrapdf@${version}`)
    // The cloud CLI needs an account and downloads @okrapdf/cli at run time: not part of an offline listing.
    .replace(/\n## Cloud commands\n[\s\S]*?(?=\n## )/, '');

await rm(skill, { recursive: true, force: true });
await mkdir(join(skill, 'references'), { recursive: true });
await writeFile(join(skill, 'SKILL.md'), pin(await readFile(join(source, 'SKILL.md'), 'utf8')));
for (const file of await readdir(join(source, 'references'))) {
  const text = await readFile(join(source, 'references', file), 'utf8');
  await writeFile(join(skill, 'references', file), pin(text));
}

const server = { type: 'stdio', command: 'npx', args: ['-y', `okrapdf@${version}`, 'mcp'] };
await writeFile(join(plugin, '.mcp.json'), `${JSON.stringify({ mcpServers: { 'okrapdf-parser': server } }, null, 2)}\n`);

const readme = join(plugin, 'README.md');
await writeFile(readme, (await readFile(readme, 'utf8')).replaceAll(/okrapdf@\d+\.\d+\.\d+/g, `okrapdf@${version}`));
console.log(`plugins/okrapdf now runs okrapdf@${version}.`);
