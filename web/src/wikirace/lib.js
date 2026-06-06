import { loadQidStats, url, pad } from '../lib.js';

const PV_API =
  'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents';

export const MAX_RACE_MEMBERS = 10;
export const MAX_RANGE_DAYS = 365;
/** Wikimedia per-article daily pageviews API backfill starts here. */
export const PAGE_VIEWS_MIN_DATE = '2015-07-01';
const RACE_LOAD_LIMIT = 6;
const RACE_LOAD_WINDOW_MS = 60_000;

export const WINDOW_PRESETS = [
  { id: '30d', label: '1 month', days: 30 },
  { id: '90d', label: '3 months', days: 90 },
  { id: '6m', label: '6 months', days: 180 },
  { id: '1y', label: '1 year', days: 365 },
];

let groupsCache = null;
let catalogCache = null;
const pvCache = new Map();
const raceLoadTimestamps = [];

/** Soft rate limit — max race loads per minute in this browser tab. */
export function allowRaceLoad() {
  const now = Date.now();
  while (raceLoadTimestamps.length && now - raceLoadTimestamps[0] > RACE_LOAD_WINDOW_MS) {
    raceLoadTimestamps.shift();
  }
  if (raceLoadTimestamps.length >= RACE_LOAD_LIMIT) return false;
  raceLoadTimestamps.push(now);
  return true;
}

export function clearGroupsCache() {
  groupsCache = null;
}

export async function loadArticleCatalog() {
  if (catalogCache) return catalogCache;
  const res = await fetch(url('wikirace/catalog.json'));
  if (!res.ok) throw new Error('Could not load article catalog');
  const data = await res.json();
  catalogCache = data.items || [];
  return catalogCache;
}

/** @returns {{ qid, label, article, score }[]} */
export function searchCatalog(catalog, query, { limit = 8, exclude = [] } = {}) {
  const q = query.trim().toLowerCase();
  if (!q || !catalog?.length) return [];

  const excluded = new Set(exclude);
  const scored = [];

  for (const item of catalog) {
    if (excluded.has(item.qid)) continue;
    const label = item.label.toLowerCase();
    const qid = item.qid.toLowerCase();
    const article = (item.article || '').toLowerCase().replace(/_/g, ' ');

    let score = 0;
    if (qid === q) score = 100;
    else if (qid.startsWith(q)) score = 90;
    else if (label === q) score = 85;
    else if (label.startsWith(q)) score = 80;
    else if (label.includes(q)) score = 60;
    else if (article.includes(q)) score = 40;
    else continue;

    scored.push({ ...item, score });
  }

  return scored
    .sort((a, b) => b.score - a.score || a.label.localeCompare(b.label))
    .slice(0, limit);
}

export function catalogLookup(catalog, qid) {
  return catalog.find((item) => item.qid === qid) ?? null;
}

const WD_API = 'https://www.wikidata.org/w/api.php';

/** Wikidata entity search — English Wikipedia articles only. */
export async function searchWikidata(query, { limit = 8, exclude = [] } = {}) {
  const q = query.trim();
  if (q.length < 2) return [];

  const excluded = new Set(exclude);
  const searchParams = new URLSearchParams({
    action: 'wbsearchentities',
    search: q,
    language: 'en',
    format: 'json',
    origin: '*',
    limit: String(Math.min(limit * 3, 20)),
  });

  const searchRes = await fetch(`${WD_API}?${searchParams}`);
  if (!searchRes.ok) return [];
  const searchData = await searchRes.json();
  const hits = (searchData.search || []).filter(
    (h) => /^Q\d+$/.test(h.id) && !excluded.has(h.id),
  );
  if (!hits.length) return [];

  const entityParams = new URLSearchParams({
    action: 'wbgetentities',
    ids: hits.map((h) => h.id).join('|'),
    props: 'labels|sitelinks|descriptions',
    languages: 'en',
    sitefilter: 'enwiki',
    format: 'json',
    origin: '*',
  });
  const entityRes = await fetch(`${WD_API}?${entityParams}`);
  if (!entityRes.ok) return [];
  const entityData = await entityRes.json();
  const entities = entityData.entities || {};

  const items = [];
  for (const hit of hits) {
    const entity = entities[hit.id];
    const enwiki = entity?.sitelinks?.enwiki?.title;
    if (!enwiki) continue;
    items.push({
      qid: hit.id,
      label: entity.labels?.en?.value || hit.label || hit.id,
      article: enwiki.replace(/ /g, '_'),
      description: entity.descriptions?.en?.value || hit.description || '',
      source: 'wikidata',
    });
    if (items.length >= limit) break;
  }
  return items;
}

/** Catalog hits first, then Wikidata — deduped by QID. */
export function mergeSearchResults(catalogHits, wikidataHits, limit = 8) {
  const seen = new Set();
  const out = [];
  for (const item of catalogHits) {
    if (seen.has(item.qid)) continue;
    seen.add(item.qid);
    out.push({ ...item, source: item.source || 'catalog' });
    if (out.length >= limit) return out;
  }
  for (const item of wikidataHits) {
    if (seen.has(item.qid)) continue;
    seen.add(item.qid);
    out.push(item);
    if (out.length >= limit) return out;
  }
  return out;
}

export function wikiraceUrl(parts = []) {
  const segs = ['wikirace', ...parts.filter(Boolean)];
  return url(segs.join('/'));
}

function isValidQid(s) {
  return /^Q\d+$/.test(s);
}

function isQidSegment(s) {
  return s.split('+').every(isValidQid);
}

export function parseIsoDate(s) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  const [y, m, d] = s.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  if (dt.getFullYear() !== y || dt.getMonth() !== m - 1 || dt.getDate() !== d) return null;
  return dt;
}

export function formatIso(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function yesterday() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return formatIso(d);
}

export function subtractDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() - n);
  return d;
}

export function daysBetween(start, end) {
  const a = parseIsoDate(start);
  const b = parseIsoDate(end);
  return Math.round((b - a) / 86400000) + 1;
}

/** Parse /wikirace/help or /wikirace/{QIDs}/{start}/{end} */
export function parseWikiracePath(segments) {
  if (!segments.length) {
    return { kind: 'home' };
  }

  if (segments[0] === 'help') {
    return { kind: 'help' };
  }

  const [qidSeg, startSeg, endSeg] = segments;

  if (!qidSeg || !isQidSegment(qidSeg)) {
    return { kind: 'invalid' };
  }

  const qids = qidSeg.split('+').filter(isValidQid);
  if (qids.length < 2) {
    return { kind: 'invalid' };
  }
  if (qids.length > MAX_RACE_MEMBERS) {
    return { kind: 'invalid', reason: 'too_many', count: qids.length };
  }

  const start = parseIsoDate(startSeg);
  const end = parseIsoDate(endSeg);
  if (!start || !end || start > end) {
    return { kind: 'invalid' };
  }
  const span = daysBetween(formatIso(start), formatIso(end));
  if (span > MAX_RANGE_DAYS) {
    return { kind: 'invalid', reason: 'range_too_long', days: span };
  }

  return {
    kind: 'race',
    qids,
    start: formatIso(start),
    end: formatIso(end),
  };
}

export function buildRacePath({ qids, start, end }) {
  if (!qids?.length || qids.length < 2 || qids.length > MAX_RACE_MEMBERS || !start || !end) {
    return 'wikirace';
  }
  return `wikirace/${qids.join('+')}/${start}/${end}`;
}

export function windowRange({ days, end }) {
  const endDate = parseIsoDate(end) || parseIsoDate(yesterday());
  const startDate = subtractDays(endDate, days - 1);
  return { start: formatIso(startDate), end: formatIso(endDate) };
}

/** Last day of the race window: day before event, or yesterday. */
export function resolveEndDate(group) {
  const yest = parseIsoDate(yesterday());
  if (!group?.eventDate) return yest;

  const ev = parseIsoDate(group.eventDate);
  if (!ev || ev > yest) return yest;

  return subtractDays(ev, 1);
}

export function clampToYesterday(end) {
  const y = yesterday();
  const endDt = parseIsoDate(end);
  const yestDt = parseIsoDate(y);
  if (!endDt || !yestDt || endDt > yestDt) return y;
  return end;
}

export function clampPageviewsStart(start) {
  const min = parseIsoDate(PAGE_VIEWS_MIN_DATE);
  const s = parseIsoDate(start);
  if (!s || !min || s >= min) return start;
  return PAGE_VIEWS_MIN_DATE;
}

export function resolveDateRange(route) {
  const end = route.end;
  const dataEnd = clampToYesterday(end);
  const fetchStart = clampPageviewsStart(route.start);
  return {
    start: route.start,
    end,
    dataEnd,
    fetchStart,
    windowDays: daysBetween(route.start, end),
    days: daysBetween(fetchStart, dataEnd),
    futureEnd: end !== dataEnd,
    clippedStart: fetchStart !== route.start,
  };
}

export async function loadGroups() {
  if (groupsCache) return groupsCache;
  const res = await fetch(url('wikirace/groups.json'));
  if (!res.ok) throw new Error('Could not load wikirace groups');
  const data = await res.json();
  groupsCache = data.groups || [];
  return groupsCache;
}

export function findGroupByQids(groups, qids) {
  const key = [...qids].sort().join('+');
  return (
    groups.find((g) => [...g.members.map((m) => m.qid)].sort().join('+') === key) ?? null
  );
}

async function fetchQidMeta(qid) {
  // No custom headers — avoids CORS preflight (Wikidata allows origin *)
  const res = await fetch(`https://www.wikidata.org/wiki/Special:EntityData/${qid}.json`);
  if (!res.ok) return null;
  const data = await res.json();
  const entity = data.entities?.[qid];
  if (!entity) return null;
  const label = entity.labels?.en?.value || qid;
  const enwiki = entity.sitelinks?.enwiki?.title;
  return {
    label,
    title: enwiki || null,
  };
}

async function resolveMember(qid, memberDef = null) {
  if (memberDef?.article) {
    return {
      qid,
      label: memberDef.label || qid,
      title: memberDef.article,
      image: '',
    };
  }

  const stats = await loadQidStats(qid).catch(() => null);
  if (stats?.title) {
    return {
      qid,
      label: memberDef?.label || stats.label || qid,
      title: stats.title,
      image: stats.image || '',
    };
  }

  const remote = await fetchQidMeta(qid);
  return {
    qid,
    label: memberDef?.label || remote?.label || qid,
    title: remote?.title || null,
    image: '',
  };
}

export async function resolveMembers(qids, group) {
  const byQid = group
    ? Object.fromEntries(group.members.map((m) => [m.qid, m]))
    : {};
  return Promise.all(qids.map((qid) => resolveMember(qid, byQid[qid] || null)));
}

function parsePvDay(timestamp) {
  // API returns YYYYMMDDHH — e.g. "2024050900" → "2024-05-09"
  return `${timestamp.slice(0, 4)}-${timestamp.slice(4, 6)}-${timestamp.slice(6, 8)}`;
}

function pvArticlePath(article) {
  return encodeURIComponent(article.replace(/_/g, ' '));
}

/** Split [start, end] into monthly chunks for smaller API requests. */
function monthChunks(start, end) {
  const chunks = [];
  let cur = parseIsoDate(start);
  const last = parseIsoDate(end);
  const yest = parseIsoDate(yesterday());
  if (!cur || !last) return chunks;

  while (cur <= last) {
    if (yest && cur > yest) break;
    const chunkStart = new Date(cur);
    const chunkEnd = new Date(cur.getFullYear(), cur.getMonth() + 1, 0);
    if (chunkEnd > last) chunkEnd.setTime(last.getTime());
    if (yest && chunkEnd > yest) chunkEnd.setTime(yest.getTime());
    chunks.push({ start: formatIso(chunkStart), end: formatIso(chunkEnd) });
    cur = new Date(cur.getFullYear(), cur.getMonth() + 1, 1);
  }
  return chunks;
}

async function fetchDailyViewsChunk(article, start, end) {
  const s = start.replace(/-/g, '') + '00';
  const e = end.replace(/-/g, '') + '00';
  const path = pvArticlePath(article);
  // Simple GET, no custom headers — custom headers trigger CORS preflight (405 on Wikimedia)
  const res = await fetch(`${PV_API}/${path}/daily/${s}/${e}`);
  if (!res.ok) throw new Error(`Pageviews HTTP ${res.status} for ${article}`);
  const data = await res.json();
  const map = new Map();
  for (const item of data.items || []) {
    map.set(parsePvDay(item.timestamp), item.views);
  }
  return map;
}

export async function fetchDailyViews(article, start, end) {
  const fetchStart = clampPageviewsStart(start);
  const dataEnd = clampToYesterday(end);
  const cacheKey = `${article}|${fetchStart}|${dataEnd}`;
  if (pvCache.has(cacheKey)) {
    return new Map(pvCache.get(cacheKey));
  }

  const chunks = monthChunks(fetchStart, dataEnd);
  const map = new Map();
  for (const chunk of chunks) {
    const partial = await fetchDailyViewsChunk(article, chunk.start, chunk.end);
    for (const [day, views] of partial) map.set(day, views);
  }
  pvCache.set(cacheKey, [...map.entries()]);
  return map;
}

export function enumerateDays(start, end) {
  const days = [];
  const d = parseIsoDate(start);
  const last = parseIsoDate(end);
  while (d <= last) {
    days.push(formatIso(d));
    d.setDate(d.getDate() + 1);
  }
  return days;
}

export function buildSeries(member, viewMap, days) {
  const points = days.map((day) => ({
    day,
    views: viewMap.get(day) ?? 0,
  }));
  const total = points.reduce((s, p) => s + p.views, 0);
  return { ...member, points, total };
}

export function racePercentages(series) {
  const grand = series.reduce((s, m) => s + m.total, 0);
  if (!grand) return series.map((m) => ({ ...m, racePct: 0 }));
  return series
    .map((m) => ({ ...m, racePct: (100 * m.total) / grand }))
    .sort((a, b) => b.racePct - a.racePct);
}

// Neutral palette — no red/blue pairing (US party connotation)
export const CHART_COLORS = [
  '#0d9488', // teal
  '#d97706', // amber
  '#7c3aed', // violet
  '#059669', // emerald
  '#c026d3', // fuchsia
  '#ea580c', // orange
  '#6366f1', // indigo
  '#84cc16', // lime
];
