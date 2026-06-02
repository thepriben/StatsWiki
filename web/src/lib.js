const BASE = import.meta.env.BASE_URL;
const cache = new Map();

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
  if (cache.has(path)) return cache.get(path);
  const res = await fetch(url(`data/${path}`));
  if (!res.ok) throw new Error(`Not found: ${path}`);
  const data = await res.json();
  cache.set(path, data);
  return data;
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

function dayTitle({ year, month, day }) {
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function monthTitle(year, month) {
  return new Date(year, month - 1, 1).toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  });
}

export async function loadHomeRankings() {
  const y = yesterday();
  const { year: monthYear, month } = currentMonthYear();
  const year = currentYear();

  const sections = [
    {
      id: 'day',
      title: 'Yesterday',
      subtitle: dayTitle(y),
      morePath: `${y.year}/${pad(y.month)}/${pad(y.day)}`,
      params: { year: y.year, month: y.month, day: y.day },
    },
    {
      id: 'month',
      title: 'This month',
      subtitle: monthTitle(monthYear, month),
      morePath: `${monthYear}/${pad(month)}`,
      params: { year: monthYear, month },
    },
    {
      id: 'year',
      title: 'This year',
      subtitle: String(year),
      morePath: String(year),
      params: { year },
    },
  ];

  return Promise.all(
    sections.map(async (section) => {
      try {
        const data = await loadRanking(section.params);
        return {
          ...section,
          period: data.period,
          lines: data.lines,
          error: null,
        };
      } catch {
        return {
          ...section,
          period: section.subtitle,
          lines: [],
          error: 'No data yet.',
        };
      }
    })
  );
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
