#!/usr/bin/env node
/**
 * Build Wikirace public help from docs/wikirace-help.md
 * Output: web/public/wikirace/help.json
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { marked } from 'marked';

const root = join(fileURLToPath(dirname(import.meta.url)), '../..');
const src = join(root, 'docs/wikirace-help.md');
const outDir = join(root, 'web/public/wikirace');
const out = join(outDir, 'help.json');

marked.setOptions({ gfm: true, breaks: false });

const md = readFileSync(src, 'utf8');
const html = marked.parse(md);

const titleMatch = md.match(/^#\s+(.+)$/m);
const payload = {
  title: titleMatch?.[1]?.trim() || 'Wikirace Help',
  source: 'docs/wikirace-help.md',
  updated: new Date().toISOString().slice(0, 10),
  html,
};

mkdirSync(outDir, { recursive: true });
writeFileSync(out, `${JSON.stringify(payload, null, 2)}\n`);
console.log(`Wikirace help → ${out}`);
