const BASE = import.meta.env.BASE_URL;
const cache = new Map();

export const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export const pad = (n) => String(n).padStart(2, '0');

export function url(path = '') {
  const p = path.startsWith('/') ? path.slice(1) : path;
  return `${BASE}${p}`;
}

/** In-app navigation (GitHub Pages SPA). */
export function navigate(path = '') {
  history.pushState(null, '', url(path));
  window.dispatchEvent(new PopStateEvent('popstate'));
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
  if (cache.has(path)) return cache.get(path);
  const res = await fetch(url(`data/${path}`));
  if (!res.ok) throw new Error(`Not found: ${path}`);
  const data = await res.json();
  cache.set(path, data);
  return data;
}

export async function tryLoadRanking(params) {
  try {
    return await loadRanking(params);
  } catch {
    return null;
  }
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

export function currentMonthYear() {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() + 1 };
}

export function currentYear() {
  return new Date().getFullYear();
}

export function parseIsoDate(iso) {
  if (!iso) return null;
  const [y, m, d] = iso.split('-').map(Number);
  return { year: y, month: m, day: d };
}

function dayTitle({ year, month, day }) {
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function monthTitle(year, month) {
  return `${MONTHS[month - 1]} ${year}`;
}

export async function loadHomeRankings() {
  const manifest = await loadManifest().catch(() => ({}));
  const latest = parseIsoDate(manifest.end);
  const y = yesterday();
  const { year: cy, month: cm } = currentMonthYear();
  const year = currentYear();

  const dayCandidates = [
    { params: { year: y.year, month: y.month, day: y.day }, label: 'Yesterday' },
  ];
  if (latest && (latest.year !== y.year || latest.month !== y.month || latest.day !== y.day)) {
    dayCandidates.push({
      params: { year: latest.year, month: latest.month, day: latest.day },
      label: 'Latest day',
    });
  }

  const monthCandidates = [
    { params: { year: cy, month: cm }, label: 'This month' },
  ];
  if (latest && (latest.year !== cy || latest.month !== cm)) {
    monthCandidates.push({
      params: { year: latest.year, month: latest.month },
      label: 'Latest month',
    });
  }

  const yearCandidates = [
    { params: { year }, label: 'This year' },
  ];
  if (latest && latest.year !== year) {
    yearCandidates.push({ params: { year: latest.year }, label: 'Latest year' });
  }

  async function pick(id, candidates, subtitleFn) {
    for (const c of candidates) {
      const data = await tryLoadRanking(c.params);
      if (data?.lines?.length) {
        const { year: yr, month: mo, day: da } = c.params;
        let morePath = String(yr);
        if (mo) morePath += `/${pad(mo)}`;
        if (da) morePath += `/${pad(da)}`;
        return {
          id,
          title: c.label,
          period: data.period,
          subtitle: subtitleFn(c.params),
          morePath,
          params: c.params,
          lines: data.lines,
          error: null,
        };
      }
    }
    const fallback = candidates[0];
    return {
      id,
      title: fallback.label,
      period: subtitleFn(fallback.params),
      subtitle: subtitleFn(fallback.params),
      morePath: '',
      params: fallback.params,
      lines: [],
      error: 'No data yet.',
    };
  }

  return Promise.all([
    pick('day', dayCandidates, dayTitle),
    pick('month', monthCandidates, (p) => monthTitle(p.year, p.month)),
    pick('year', yearCandidates, (p) => String(p.year)),
  ]);
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

export function statsUrl(qid) {
  return /^Q\d+$/.test(qid) ? url(`q/${qid}`) : null;
}
