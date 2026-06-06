<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import QidPage from './QidPage.vue';
import RankingTable from './RankingTable.vue';
import {
  MONTHS,
  currentYear,
  loadHomeRankings,
  loadManifest,
  loadRanking,
  navigate,
  pad,
  parseIsoDate,
  BSKY_URL,
  REPO_URL,
  VERSION,
  X_URL,
  yesterday,
} from './lib.js';

const loading = ref(true);
const error = ref('');
const data = ref(null);
const homeSections = ref([]);
const manifest = ref(null);

const route = ref(parseRoute(window.location.pathname));

function parseRoute(pathname) {
  const base = '/StatsWiki'.replace(/\/$/, '');
  let path = pathname.replace(base, '').replace(/\/$/, '') || '/';
  if (path === '/' || path === '') return { kind: 'home' };
  if (path === '/alltime') return { kind: 'alltime', alltime: true };
  const qMatch = path.match(/^\/q\/(Q\d+)$/);
  if (qMatch) return { kind: 'qid', qid: qMatch[1] };
  const parts = path.split('/').filter(Boolean);
  const [y, m, d] = parts.map(Number);
  if (parts.length === 1 && y >= 2015) return { kind: 'year', year: y };
  if (parts.length === 2 && y >= 2015 && m >= 1 && m <= 12) return { kind: 'month', year: y, month: m };
  if (parts.length === 3 && y >= 2015 && m >= 1 && m <= 12 && d >= 1 && d <= 31) {
    return { kind: 'day', year: y, month: m, day: d };
  }
  return { kind: 'home' };
}

async function fetchData() {
  if (route.value.kind === 'home') {
    loading.value = true;
    error.value = '';
    try {
      homeSections.value = await loadHomeRankings();
    } catch {
      homeSections.value = [];
      error.value = 'Could not load rankings.';
    } finally {
      loading.value = false;
    }
    data.value = null;
    return;
  }

  if (route.value.kind === 'qid') {
    data.value = null;
    error.value = '';
    loading.value = false;
    return;
  }

  loading.value = true;
  error.value = '';
  try {
    data.value = await loadRanking(route.value);
  } catch {
    data.value = null;
    error.value = 'No data for this period.';
  } finally {
    loading.value = false;
  }
}

function go(path) {
  navigate(path);
}

function pickerPath() {
  if (!selYear.value) return '';
  let path = String(selYear.value);
  if (selMonth.value) path += `/${pad(selMonth.value)}`;
  if (selDay.value) path += `/${pad(selDay.value)}`;
  return path;
}

function routePath() {
  const r = route.value;
  if (r.kind === 'year') return String(r.year);
  if (r.kind === 'month') return `${r.year}/${pad(r.month)}`;
  if (r.kind === 'day') return `${r.year}/${pad(r.month)}/${pad(r.day)}`;
  return '';
}

function syncPickersFromRoute() {
  const r = route.value;
  if (r.kind === 'year' || r.kind === 'month' || r.kind === 'day') {
    selYear.value = r.year;
    selMonth.value = r.kind === 'year' ? '' : r.month;
    selDay.value = r.kind === 'day' ? r.day : '';
  }
}

function goDate() {
  const path = pickerPath();
  if (path && path !== routePath()) go(path);
}

const selYear = ref('');
const selMonth = ref('');
const selDay = ref('');

const years = computed(() => {
  const end = manifest.value?.end
    ? parseIsoDate(manifest.value.end)?.year
    : currentYear();
  const startYear = 2015;
  const hi = end || currentYear();
  return Array.from({ length: hi - startYear + 1 }, (_, i) => hi - i);
});

const daysInMonth = computed(() => {
  if (!selYear.value || !selMonth.value) return 31;
  return new Date(Number(selYear.value), Number(selMonth.value), 0).getDate();
});

const isHome = computed(() => route.value.kind === 'home');
const isAlltime = computed(() => route.value.kind === 'alltime');

const breadcrumb = computed(() => {
  const r = route.value;
  const crumbs = [{ label: 'StatsWiki', path: '' }];
  if (r.kind === 'alltime') return [...crumbs, { label: 'All time', path: null }];
  if (r.kind === 'year') return [...crumbs, { label: String(r.year), path: null }];
  if (r.kind === 'month') {
    return [...crumbs, { label: String(r.year), path: String(r.year) }, { label: MONTHS[r.month - 1], path: null }];
  }
  if (r.kind === 'day') {
    return [
      ...crumbs,
      { label: String(r.year), path: String(r.year) },
      { label: MONTHS[r.month - 1], path: `${r.year}/${pad(r.month)}` },
      { label: String(r.day), path: null },
    ];
  }
  if (r.kind === 'qid') return [...crumbs, { label: r.qid, path: null }];
  return crumbs;
});

const tagline = 'English Wikipedia · pageview rankings since July 2015';

const heading = computed(() => data.value?.period || 'StatsWiki');
const lines = computed(() => data.value?.lines || []);
const subnav = computed(() =>
  (data.value?.nav || []).map((item) => ({ label: item.label, path: item.path }))
);

onMounted(async () => {
  manifest.value = await loadManifest().catch(() => null);
  const end = parseIsoDate(manifest.value?.end);
  if (end) {
    selYear.value = end.year;
    selMonth.value = end.month;
    selDay.value = end.day;
  }
  fetchData();
  window.addEventListener('popstate', () => {
    route.value = parseRoute(window.location.pathname);
  });
});

watch(route, () => {
  syncPickersFromRoute();
  fetchData();
});

watch(selYear, (y) => {
  if (!y) {
    selMonth.value = '';
    selDay.value = '';
  }
});

watch(selMonth, (m) => {
  if (!m) selDay.value = '';
});
</script>

<template>
  <div class="page">
    <header class="site-header">
      <div class="header-inner">
        <div class="header-brand">
          <a
            href="#"
            class="brand-title"
            :class="{ 'brand-title--active': isHome }"
            @click.prevent="go('')"
          >StatsWiki</a>
          <p class="brand-tagline">{{ tagline }} · {{ VERSION }}</p>
        </div>

        <nav class="header-nav" aria-label="Main">
          <a
            href="#"
            class="nav-alltime"
            :class="{ 'nav-alltime--active': isAlltime }"
            @click.prevent="go('alltime')"
          >All time</a>
          <div class="header-social">
            <a
              :href="REPO_URL"
              class="icon-btn"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub repository"
            >
              <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
                <path fill="currentColor" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.17 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.001 10.001 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"/>
              </svg>
            </a>
            <a
              :href="BSKY_URL"
              class="icon-btn icon-btn--bsky"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Bluesky"
            >
              <svg viewBox="0 0 568 501" aria-hidden="true">
                <path fill="currentColor" d="M123.121 33.664c65.486 40.932 135.009 118.342 160.919 151.43 25.91-33.088 95.433-110.498 160.919-151.43C510.387-.334 568-20.92 568 35.44c0 11.403-6.581 95.562-10.435 109.335-13.385 47.759-62.16 59.863-105.618 52.385 75.223 12.803 94.283 55.17 52.919 97.7-78.24 80.322-112.335-20.253-121.047-45.888-1.631-4.735-2.415-6.953-2.473-6.4-.058-.553-.842 1.665-2.473 6.4-8.712 25.635-42.807 126.208-121.047 45.888-41.364-42.53-22.304-84.897 52.919-97.7-43.458 7.478-94.233-4.626-105.618-52.385C6.581 131.002 0 46.843 0 35.44 0-20.92 57.613-.334 123.121 33.664z"/>
              </svg>
            </a>
            <a
              :href="X_URL"
              class="icon-btn icon-btn--x"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="X"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path fill="currentColor" d="M14.4 10.6 22.9 1h-2l-7.4 8.3L7.6 1H1l8.9 12.7L1 23h2l7.8-8.6L17 23h6.5l-9.1-12.4Zm-2.8 3.1-.9-1.2L3.6 2.5h3l5.8 8.2.9 1.2 7.5 9.7h-3l-6.2-7.9Z"/>
              </svg>
            </a>
          </div>
        </nav>

        <div class="header-date" aria-label="Choose a date">
          <select v-model="selYear" class="date-select" aria-label="Year" @change="goDate">
            <option value="">Year</option>
            <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
          </select>
          <span class="date-sep" aria-hidden="true">/</span>
          <select
            v-model="selMonth"
            class="date-select"
            aria-label="Month"
            :disabled="!selYear"
            @change="goDate"
          >
            <option value="">Month</option>
            <option v-for="(name, i) in MONTHS" :key="name" :value="i + 1">{{ name }}</option>
          </select>
          <span class="date-sep" aria-hidden="true">/</span>
          <select
            v-model="selDay"
            class="date-select"
            aria-label="Day"
            :disabled="!selMonth"
            @change="goDate"
          >
            <option value="">Day</option>
            <option v-for="d in daysInMonth" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
      </div>
    </header>

    <main>
      <section v-if="route.kind === 'home'" class="home">
        <h1>Top 50 most-read articles</h1>
        <p v-if="loading" class="status">Loading…</p>
        <p v-else-if="error" class="error">{{ error }}</p>
        <div v-else class="home-sections">
          <article v-for="section in homeSections" :key="section.id" class="home-block">
            <header class="home-block-head">
              <div>
                <h2>{{ section.title }}</h2>
                <p class="home-period">{{ section.period }}</p>
              </div>
              <a
                v-if="section.lines.length && section.morePath"
                href="#"
                class="more"
                @click.prevent="go(section.morePath)"
              >Full page →</a>
            </header>
            <p v-if="section.error" class="empty">{{ section.error }}</p>
            <RankingTable v-else :lines="section.lines" compact @open-qid="go" />
          </article>
        </div>
      </section>

      <QidPage v-else-if="route.kind === 'qid'" :qid="route.qid" />

      <template v-else>
        <nav v-if="breadcrumb.length > 1" class="breadcrumb" aria-label="Breadcrumb">
          <template v-for="(crumb, i) in breadcrumb" :key="i">
            <a v-if="crumb.path !== null" href="#" @click.prevent="go(crumb.path)">{{ crumb.label }}</a>
            <span v-else class="crumb-current">{{ crumb.label }}</span>
            <span v-if="i < breadcrumb.length - 1" class="crumb-sep">/</span>
          </template>
        </nav>
        <h1>{{ heading }}</h1>
        <nav v-if="subnav.length" class="subnav">
          <a
            v-for="item in subnav"
            :key="item.path"
            href="#"
            @click.prevent="go(item.path)"
          >{{ item.label }}</a>
        </nav>
        <p v-if="loading" class="status">Loading…</p>
        <p v-else-if="error" class="error">{{ error }}</p>
        <RankingTable v-else-if="lines.length" :lines="lines" @open-qid="go" />
      </template>
    </main>

    <footer class="site-footer">
      <a :href="REPO_URL" class="repo-link" target="_blank" rel="noopener noreferrer">GitHub repository</a>
    </footer>
  </div>
</template>
