const BASE = import.meta.env.BASE_URL;

export const pad = (n) => String(n).padStart(2, '0');

export function url(path = '') {
  const p = path.startsWith('/') ? path.slice(1) : path;
  return `${BASE}${p}`;
}

export function dataPath({ year, month, day, alltime }) {
  if (alltime) return 'alltime.json';
  if (year && month && day) return `day/${year}/${pad(month)}/${pad(day)}.json`;
  if (year && month) return `month/${year}/${pad(month)}.json`;
  if (year) return `year/${year}.json`;
  return null;
}

export async function loadRanking(params) {
  const path = dataPath(params);
  if (!path) throw new Error('Invalid period');
  const res = await fetch(url(`data/${path}`));
  if (!res.ok) throw new Error(`Not found: ${path}`);
  return res.json();
}

export async function loadManifest() {
  const res = await fetch(url('data/manifest.json'));
  if (!res.ok) throw new Error('No manifest');
  return res.json();
}

export function yesterday() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return { year: d.getFullYear(), month: d.getMonth() + 1, day: d.getDate() };
}

export function fmtViews(n) {
  return typeof n === 'number' ? n.toLocaleString('en-US') : n;
}

export function titleText(line) {
  return line.title.replace(/_/g, ' ');
}

export function wikiUrl(title) {
  return `https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g, '_'))}`;
}

export function wikidataUrl(qid) {
  return /^Q\d+$/.test(qid) ? `https://www.wikidata.org/wiki/${qid}` : null;
}
