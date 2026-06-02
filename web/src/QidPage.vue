<script setup>
import { computed, ref, watch } from 'vue';
import LineChart from './LineChart.vue';
import { commonsFileUrl, fmtViews, loadQidStats, wikidataUrl, wikiUrl } from './lib.js';

const props = defineProps({
  qid: { type: String, required: true },
});

const loading = ref(true);
const error = ref('');
const stats = ref(null);
const mode = ref('monthly');

async function load() {
  loading.value = true;
  error.value = '';
  try {
    stats.value = await loadQidStats(props.qid);
  } catch {
    stats.value = null;
    error.value = 'No pageview data for this item yet.';
  } finally {
    loading.value = false;
  }
}

watch(() => props.qid, load, { immediate: true });

const points = computed(() => {
  if (!stats.value) return [];
  return stats.value[mode.value] || [];
});

const peak = computed(() => {
  if (!points.value.length) return null;
  return points.value.reduce((a, b) => (b.views > a.views ? b : a));
});
</script>

<template>
  <section class="qid-page">
    <p v-if="loading" class="status">Loading…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <template v-else-if="stats">
      <div class="qid-head">
        <a
          v-if="stats.image && commonsFileUrl(stats.image)"
          :href="commonsFileUrl(stats.image)"
          class="qid-image-link"
          target="_blank"
          rel="noopener noreferrer"
          title="Image on Wikimedia Commons"
        >
          <img :src="stats.image" :alt="stats.label" class="qid-image" />
        </a>
        <img
          v-else-if="stats.image"
          :src="stats.image"
          :alt="stats.label"
          class="qid-image"
        />
        <div>
          <h1>{{ stats.label }}</h1>
          <p class="qid-meta">
            <a :href="wikiUrl(stats.title)" class="link" target="_blank" rel="noopener">Wikipedia ↗</a>
            <span class="sep">·</span>
            <a :href="wikidataUrl(stats.qid)" class="link" target="_blank" rel="noopener">{{ stats.qid }} ↗</a>
          </p>
          <p v-if="stats.description" class="qid-desc">{{ stats.description }}</p>
          <p class="qid-total">{{ fmtViews(stats.total) }} total views in dataset</p>
        </div>
      </div>

      <div class="chart-toolbar">
        <button type="button" :class="{ active: mode === 'monthly' }" @click="mode = 'monthly'">Monthly</button>
        <button type="button" :class="{ active: mode === 'yearly' }" @click="mode = 'yearly'">Yearly</button>
      </div>

      <LineChart :points="points" />

      <p v-if="peak" class="peak">
        Peak {{ mode === 'monthly' ? 'month' : 'year' }}:
        <strong>{{ peak.period }}</strong> — {{ fmtViews(peak.views) }} views
      </p>

    </template>
  </section>
</template>
