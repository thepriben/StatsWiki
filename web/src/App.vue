<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import {
  fmtViews,
  loadRanking,
  loadManifest,
  pad,
  titleText,
  url,
  wikiUrl,
  wikidataUrl,
  yesterday,
} from './lib.js';

const loading = ref(true);
const error = ref('');
const data = ref(null);
const manifest = ref(null);

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
  const end = yesterday().year;
  return Array.from({ length: end - 2014 }, (_, i) => 2015 + i);
});

const heading = computed(() => data.value?.period || 'StatsWiki');
const lines = computed(() => data.value?.lines || []);
const subnav = computed(() =>
  (data.value?.nav || []).map((item) => ({ label: item.label, href: url(item.path) }))
);

onMounted(async () => {
  manifest.value = await loadManifest().catch(() => null);
  fetchData();
});

watch(route, fetchData);
</script>

<template>
  <div class="page">
    <header>
      <a :href="url()" class="brand">StatsWiki</a>
      <span class="tagline">
        English Wikipedia pageviews since July 2015
        <template v-if="manifest?.end"> · data through {{ manifest.end }}</template>
      </span>
      <nav class="toolbar">
        <a :href="url('alltime')">All time</a>
        <a :href="url(`${yesterday().year}/${pad(yesterday().month)}/${pad(yesterday().day)}`)">Yesterday</a>
        <select v-model="selYear">
          <option value="">Year</option>
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
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
      <section v-if="route.kind === 'home'" class="hero">
        <h1>Most-viewed Wikipedia articles</h1>
        <p>Daily, monthly, yearly and all-time rankings.</p>
        <p>
          <a :href="url('alltime')">All-time top 50</a>
          ·
          <a :href="url(`${yesterday().year}/${pad(yesterday().month)}/${pad(yesterday().day)}`)">Yesterday</a>
        </p>
      </section>

      <template v-else>
        <h1>{{ heading }}</h1>
        <nav v-if="subnav.length" class="subnav">
          <a v-for="item in subnav" :key="item.href" :href="item.href">{{ item.label }}</a>
        </nav>
        <p v-if="loading">Loading…</p>
        <p v-else-if="error" class="error">{{ error }}</p>
        <table v-else-if="lines.length">
          <thead>
            <tr><th>#</th><th>Article</th><th class="num">Views</th></tr>
          </thead>
          <tbody>
            <tr v-for="line in lines" :key="line.title">
              <td>{{ line.rank }}</td>
              <td>
                <a :href="wikiUrl(line.title)">{{ line.label || titleText(line) }}</a>
                <span v-if="line.description" class="desc">{{ line.description }}</span>
                <a v-if="wikidataUrl(line.qid)" class="qid" :href="wikidataUrl(line.qid)">{{ line.qid }}</a>
                <img v-if="line.image" class="thumb" :src="line.image" :alt="line.label" loading="lazy" />
              </td>
              <td class="num">{{ fmtViews(line.views) }}</td>
            </tr>
          </tbody>
        </table>
      </template>
    </main>

    <footer><a href="https://twitter.com/StatsWiki">@StatsWiki</a></footer>
  </div>
</template>
