<script setup>
import { computed, ref, watch } from 'vue';
import { SITE_URL, fmtViews, statsUrl, url } from '../lib.js';
import HelpPage from './HelpPage.vue';
import MultiLineChart from './MultiLineChart.vue';
import QidPicker from './QidPicker.vue';
import {
  WINDOW_PRESETS,
  buildRacePath,
  buildSeries,
  catalogLookup,
  enumerateDays,
  fetchDailyViews,
  findGroupByQids,
  loadArticleCatalog,
  loadGroups,
  racePercentages,
  formatIso,
  resolveDateRange,
  resolveEndDate,
  resolveMembers,
  windowRange,
  yesterday,
  CHART_COLORS,
} from './lib.js';

const props = defineProps({
  route: { type: Object, required: true },
});

const emit = defineEmits(['navigate']);

const groups = ref([]);
const loading = ref(false);
const error = ref('');
const raceSeries = ref([]);
const range = ref({ start: '', end: '', days: null });
const activeGroup = ref(null);

const builderMembers = ref([]);
const builderStart = ref('');
const builderEnd = ref('');
const builderWindow = ref('6m');
const canCompare = computed(() => builderMembers.value.length >= 2);

const isHome = computed(() => props.route.kind === 'home');
const isHelp = computed(() => props.route.kind === 'help');
const isInvalid = computed(() => props.route.kind === 'invalid');

const title = computed(() => {
  if (isHome.value || isInvalid.value) return 'Wikirace';
  if (activeGroup.value) return activeGroup.value.label;
  const n = raceSeries.value.length;
  if (n) return `Wikirace · ${n} articles`;
  return 'Wikirace';
});

const windowLabel = computed(() => {
  if (!range.value.start || !range.value.end) return '';
  return `${range.value.start} → ${range.value.end}`;
});

const dataThroughNote = computed(() => {
  if (!range.value.futureEnd || !range.value.dataEnd) return '';
  return `Pageviews through ${range.value.dataEnd} (URL end date is still in the future)`;
});

const ranked = computed(() => racePercentages(raceSeries.value));

const activeWindowId = computed(() => {
  const span = range.value.windowDays ?? range.value.days;
  if (!span) return null;
  const preset = WINDOW_PRESETS.find((p) => p.days === span);
  return preset?.id || null;
});

const shareUrl = computed(() => {
  if (isHome.value || isInvalid.value) return url('wikirace');
  const path = buildRacePath({
    qids: props.route.qids,
    start: props.route.start,
    end: props.route.end,
  });
  if (typeof window !== 'undefined') return `${window.location.origin}${url(path)}`;
  return `${SITE_URL}${url(path)}`;
});

function joinQidsForDisplay(qids) {
  return qids.join('+\u200b');
}

const breadcrumbLabel = computed(() => {
  if (activeGroup.value) return activeGroup.value.label;
  if (props.route.qids?.length) return joinQidsForDisplay(props.route.qids);
  return 'race';
});

const shareUrlDisplay = computed(() => shareUrl.value.replace(/\+/g, '+\u200b'));

async function loadCatalog() {
  try {
    groups.value = await loadGroups();
  } catch {
    groups.value = [];
  }
}

async function loadRace() {
  if (isHome.value || isHelp.value || isInvalid.value) {
    raceSeries.value = [];
    activeGroup.value = null;
    if (isInvalid.value) error.value = 'Invalid URL — use /wikirace/Q1+Q2/YYYY-MM-DD/YYYY-MM-DD';
    return;
  }

  loading.value = true;
  error.value = '';
  raceSeries.value = [];

  try {
    const catalog = groups.value.length ? groups.value : await loadGroups();
    groups.value = catalog;

    const qids = props.route.qids || [];
    const group = findGroupByQids(catalog, qids);
    const dateRange = resolveDateRange(props.route);

    range.value = dateRange;
    activeGroup.value = group;

    const members = await resolveMembers(qids, group);
    const missing = members.filter((m) => !m.title);
    if (missing.length) {
      throw new Error(`Could not resolve Wikipedia title for: ${missing.map((m) => m.label).join(', ')}`);
    }

    const days = enumerateDays(dateRange.start, dateRange.dataEnd);
    const results = [];
    for (const member of members) {
      try {
        const viewMap = await fetchDailyViews(member.title, dateRange.start, dateRange.end);
        results.push(buildSeries(member, viewMap, days));
      } catch (err) {
        throw new Error(`${member.label}: ${err.message || 'fetch failed'}`);
      }
    }

    raceSeries.value = results;
    if (!results.some((r) => r.total > 0)) {
      error.value = 'No pageview data for this period.';
    }
  } catch (e) {
    error.value = e.message || 'Could not load wikirace.';
  } finally {
    loading.value = false;
  }
}

function go(path) {
  emit('navigate', path);
}

function openGroup(g) {
  fillBuilderFromGroup(g);
  const qids = g.members.map((m) => m.qid);
  const { start, end } = g.defaultRange;
  go(buildRacePath({ qids, start, end }));
}

function resolveBuilderDates() {
  if (builderStart.value && builderEnd.value) {
    return { start: builderStart.value, end: builderEnd.value };
  }
  const preset = WINDOW_PRESETS.find((p) => p.id === builderWindow.value) || WINDOW_PRESETS[2];
  return windowRange({ days: preset.days, end: yesterday() });
}

function applyBuilder() {
  const qids = builderMembers.value.map((m) => m.qid);
  if (qids.length < 2) return;

  const { start, end } = resolveBuilderDates();
  go(buildRacePath({ qids, start, end }));
}

function applyBuilderWindow() {
  const { start, end } = resolveBuilderDates();
  builderStart.value = start;
  builderEnd.value = end;
}

const shareCopied = ref(false);

function copyShareUrl() {
  navigator.clipboard?.writeText(shareUrl.value);
  shareCopied.value = true;
  setTimeout(() => { shareCopied.value = false; }, 2000);
}

function setWindow(windowId) {
  const preset = WINDOW_PRESETS.find((p) => p.id === windowId);
  if (!preset || !props.route.qids?.length) return;

  const endIso = activeGroup.value
    ? formatIso(resolveEndDate(activeGroup.value))
    : props.route.end;

  const { start, end } = windowRange({ days: preset.days, end: endIso });
  go(buildRacePath({ qids: props.route.qids, start, end }));
}

async function syncBuilderFromRoute() {
  if (props.route.kind !== 'race') return;
  builderStart.value = props.route.start;
  builderEnd.value = props.route.end;

  const catalog = await loadArticleCatalog().catch(() => []);
  builderMembers.value = props.route.qids.map((qid) => {
    const hit = catalogLookup(catalog, qid);
    return { qid, label: hit?.label || qid };
  });
}

function fillBuilderFromGroup(g) {
  builderMembers.value = g.members.map((m) => ({ qid: m.qid, label: m.label }));
  builderStart.value = g.defaultRange.start;
  builderEnd.value = g.defaultRange.end;
}

watch(() => props.route, () => {
  syncBuilderFromRoute();
  loadRace();
}, { immediate: true, deep: true });

watch(builderWindow, () => {
  if (isHome.value && !builderStart.value && !builderEnd.value) {
    applyBuilderWindow();
  }
});

loadCatalog();
applyBuilderWindow();
</script>

<template>
  <HelpPage v-if="isHelp" @navigate="go" />

  <section v-else class="wikirace-page">
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="#" @click.prevent="go('')">StatsWiki</a>
      <span class="crumb-sep">/</span>
      <a v-if="!isHome" href="#" @click.prevent="go('wikirace')">Wikirace</a>
      <span v-else class="crumb-current">Wikirace</span>
      <template v-if="!isHome && !isInvalid">
        <span class="crumb-sep">/</span>
        <span class="crumb-current">{{ breadcrumbLabel }}</span>
      </template>
    </nav>

    <header class="wikirace-head">
      <div>
        <h1>{{ title }}</h1>
        <p v-if="!isHome && !isInvalid && windowLabel" class="wikirace-period">{{ windowLabel }}</p>
        <p v-if="!isHome && !isInvalid && dataThroughNote" class="wikirace-data-note">{{ dataThroughNote }}</p>
        <p v-if="!isHome && !isInvalid && ranked.length" class="wikirace-metric-note">
          Race% = area under the curve — each article’s share of combined daily pageviews.
        </p>
        <p v-else-if="isHome" class="wikirace-tagline">
          Compare Wikipedia attention. Race% is area under the curve, as a share of the group.
        </p>
      </div>
      <div class="wikirace-head-links">
        <a href="#" class="wikirace-home-link" @click.prevent="go('wikirace/help')">Help</a>
        <a v-if="!isHome" href="#" class="wikirace-home-link" @click.prevent="go('wikirace')">New race</a>
      </div>
    </header>

    <div v-if="isHome" class="wikirace-home">
      <p class="wikirace-intro">
        Compare Wikipedia pageviews for any group of articles over a date range.
        <a href="#" @click.prevent="go('wikirace/help')">Read the help guide →</a>
      </p>

      <section class="wikirace-panel">
        <h2>Build a race</h2>
        <p class="hint">Search the StatsWiki catalog, add at least two articles, set a date range.</p>
        <div class="wikirace-form">
          <QidPicker v-model="builderMembers" :min="2" />
          <div class="field-row">
            <label class="field">
              <span>Quick window</span>
              <select v-model="builderWindow" @change="applyBuilderWindow">
                <option v-for="p in WINDOW_PRESETS" :key="p.id" :value="p.id">{{ p.label }}</option>
              </select>
            </label>
            <label class="field">
              <span>Start</span>
              <input v-model="builderStart" type="date" :max="builderEnd || yesterday()" />
            </label>
            <label class="field">
              <span>End</span>
              <input v-model="builderEnd" type="date" :min="builderStart" :max="yesterday()" />
            </label>
          </div>
          <button type="button" class="btn-primary" :disabled="!canCompare" @click="applyBuilder">Compare →</button>
        </div>
      </section>

      <section class="wikirace-panel">
        <h2>Preset groups</h2>
        <div class="group-grid">
          <button
            v-for="g in groups"
            :key="g.slug"
            type="button"
            class="group-card"
            @click="openGroup(g)"
          >
            <span class="group-cat">{{ g.category }}</span>
            <strong>{{ g.label }}</strong>
            <span class="group-meta">{{ joinQidsForDisplay(g.members.map((m) => m.qid)) }}</span>
            <span class="group-meta">{{ g.defaultRange.start }} → {{ g.defaultRange.end }}</span>
          </button>
        </div>
      </section>

    </div>

    <template v-else-if="isInvalid">
      <p class="error">{{ error }}</p>
      <p class="hint">Example: <a href="#" @click.prevent="go('wikirace/Q22686+Q10853588/2024-05-09/2024-11-04')">2024 US President</a></p>
    </template>

    <template v-else>
      <div v-if="!loading && raceSeries.length" class="wikirace-toolbar">
        <span class="toolbar-label">Resize</span>
        <button
          v-for="p in WINDOW_PRESETS"
          :key="p.id"
          type="button"
          :class="{ active: activeWindowId === p.id }"
          @click="setWindow(p.id)"
        >{{ p.label }}</button>
      </div>

      <p v-if="loading" class="status">Loading pageviews…</p>
      <p v-else-if="error" class="error">{{ error }}</p>

      <template v-else-if="ranked.length">
        <MultiLineChart :series="ranked" />

        <p class="race-metric-key">
          <strong>Race%</strong> is <strong>area under the curve</strong>: the sum of daily pageviews for each
          article over this period, as a percentage of the group total. The shaded bands on the chart correspond
          to these shares — a larger filled area means a higher Race%.
        </p>

        <table class="race-table">
          <caption class="race-table-caption">
            Ranked by Race% (area under the curve). Views = sum of daily pageviews in the period.
          </caption>
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Article</th>
              <th scope="col" class="num">Views</th>
              <th scope="col" class="num" title="Area under the curve as % of group total">Race%</th>
              <th scope="col">Share</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in ranked" :key="row.qid">
              <td class="rank">{{ i + 1 }}</td>
              <td>
                <a
                  v-if="statsUrl(row.qid)"
                  href="#"
                  class="race-name"
                  @click.prevent="go(`q/${row.qid}`)"
                >{{ row.label }}</a>
                <span v-else class="race-name">{{ row.label }}</span>
              </td>
              <td class="num">{{ fmtViews(row.total) }}</td>
              <td class="num"><strong>{{ row.racePct.toFixed(1) }}%</strong></td>
              <td>
                <div class="race-bar-track">
                  <div
                    class="race-bar-fill"
                    :style="{ width: row.racePct + '%', background: CHART_COLORS[i % CHART_COLORS.length] }"
                  />
                </div>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="2">Group total</td>
              <td class="num">{{ fmtViews(ranked.reduce((s, r) => s + r.total, 0)) }}</td>
              <td class="num">100%</td>
              <td />
            </tr>
          </tfoot>
        </table>

        <div class="share-hint">
          <span class="share-hint-label">Share this race:</span>
          <a href="#" class="share-link" @click.prevent="copyShareUrl">{{ shareCopied ? 'Copied!' : shareUrlDisplay }}</a>
        </div>
      </template>
    </template>
  </section>
</template>
