<script setup>
import { computed, onMounted, ref, watch } from 'vue';
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
    loading.value = false;
    data.value = null;
    error.value = '';
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

function goDate() {
  if (!selYear.value) return;
  let path = String(selYear.value);
  if (selMonth.value) path += `/${pad(selMonth.value)}`;
  if (selDay.value) path += `/${pad(selDay.value)}`;
  go(path);
}

function onLinkClick(e, path) {
  e.preventDefault();
  go(path);
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

watch(route, fetchData);
</script>

<template>
  <div class="page">
    <header>
      <div class="header-top">
        <a href="#" class="brand" @click.prevent="go('')">StatsWiki</a>
        <span class="tagline">English Wikipedia · pageview rankings since July 2015</span>
      </div>
      <nav class="toolbar" aria-label="Browse by date">
        <a href="#" class="nav-link" @click.prevent="go('')">Home</a>
        <a href="#" class="nav-link" @click.prevent="go('alltime')">All time</a>
        <label class="picker">
          <span class="picker-label">Year</span>
          <select v-model="selYear">
            <option value="">—</option>
            <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
          </select>
        </label>
        <label class="picker">
          <span class="picker-label">Month</span>
          <select v-model="selMonth">
            <option value="">—</option>
            <option v-for="(name, i) in MONTHS" :key="name" :value="i + 1">{{ name }}</option>
          </select>
        </label>
        <label class="picker">
          <span class="picker-label">Day</span>
          <select v-model="selDay">
            <option value="">—</option>
            <option v-for="d in daysInMonth" :key="d" :value="d">{{ d }}</option>
          </select>
        </label>
        <button type="button" class="btn-go" @click="goDate">Go</button>
      </nav>
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
            <RankingTable v-else :lines="section.lines" compact />
          </article>
        </div>
      </section>

      <section v-else-if="route.kind === 'qid'" class="qid-page">
        <h1>{{ route.qid }}</h1>
        <p class="status">
          Article view over time — coming soon.
          <span class="hint">Plot daily / monthly / yearly pageviews for this Wikidata item, then compare several QIDs on a date range.</span>
        </p>
        <p><a :href="`https://www.wikidata.org/wiki/${route.qid}`" class="link">Open on Wikidata ↗</a></p>
      </section>

      <template v-else>
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
  </div>
</template>
