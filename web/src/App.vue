<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import RankingTable from './RankingTable.vue';
import {
  currentYear,
  loadHomeRankings,
  loadRanking,
  pad,
  url,
  yesterday,
} from './lib.js';

const loading = ref(true);
const error = ref('');
const data = ref(null);
const homeSections = ref([]);

const route = ref(parseRoute(window.location.pathname));

function parseRoute(pathname) {
  const base = '/StatsWiki'.replace(/\/$/, '');
  const path = pathname.replace(base, '').replace(/\/$/, '') || '/';
  if (path === '/' || path === '') return { kind: 'home' };
  if (path === '/alltime') return { kind: 'alltime', alltime: true };
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

function goDate() {
  if (!selYear.value) return;
  let path = String(selYear.value);
  if (selMonth.value) path += `/${pad(selMonth.value)}`;
  if (selDay.value) path += `/${pad(selDay.value)}`;
  window.location.href = url(path);
}

const selYear = ref('');
const selMonth = ref('');
const selDay = ref('');

const years = computed(() => {
  const end = currentYear();
  return Array.from({ length: end - 2014 }, (_, i) => 2015 + i);
});

const heading = computed(() => data.value?.period || 'StatsWiki');
const lines = computed(() => data.value?.lines || []);
const subnav = computed(() =>
  (data.value?.nav || []).map((item) => ({ label: item.label, href: url(item.path) }))
);

const y = yesterday();

onMounted(() => {
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
        <a :href="url()" class="brand">StatsWiki</a>
        <span class="tagline">English Wikipedia · pageview rankings since July 2015</span>
      </div>
      <nav class="toolbar">
        <a :href="url()">Home</a>
        <a :href="url('alltime')">All time</a>
        <a :href="url(`${y.year}/${pad(y.month)}/${pad(y.day)}`)">Yesterday</a>
        <select v-model="selYear">
          <option value="">Year</option>
          <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
        </select>
        <select v-model="selMonth">
          <option value="">Month</option>
          <option v-for="m in 12" :key="m" :value="m">{{ m }}</option>
        </select>
        <select v-model="selDay">
          <option value="">Day</option>
          <option v-for="d in 31" :key="d" :value="d">{{ d }}</option>
        </select>
        <button type="button" @click="goDate">Go</button>
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
              <a v-if="section.lines.length" :href="url(section.morePath)" class="more">Full page →</a>
            </header>
            <p v-if="section.error" class="empty">{{ section.error }}</p>
            <RankingTable v-else :lines="section.lines" compact />
          </article>
        </div>
      </section>

      <template v-else>
        <h1>{{ heading }}</h1>
        <nav v-if="subnav.length" class="subnav">
          <a v-for="item in subnav" :key="item.href" :href="item.href">{{ item.label }}</a>
        </nav>
        <p v-if="loading" class="status">Loading…</p>
        <p v-else-if="error" class="error">{{ error }}</p>
        <RankingTable v-else-if="lines.length" :lines="lines" />
      </template>
    </main>
  </div>
</template>
