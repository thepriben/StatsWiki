<script setup>
import { onMounted, ref } from 'vue';
import { url } from '../lib.js';

const emit = defineEmits(['navigate']);

const help = ref(null);
const loading = ref(true);
const error = ref('');

function go(path) {
  emit('navigate', path);
}

function onHelpClick(e) {
  const a = e.target.closest('a');
  if (!a) return;
  const href = a.getAttribute('href');
  if (href?.startsWith('/') && !href.startsWith('//')) {
    e.preventDefault();
    go(href.replace(/^\//, ''));
  }
}

onMounted(async () => {
  try {
    const res = await fetch(url('wikirace/help.json'));
    if (!res.ok) throw new Error('Help not found');
    help.value = await res.json();
  } catch {
    error.value = 'Could not load help. Run npm run build:help in web/.';
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <article class="wikirace-help-page">
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="#" @click.prevent="go('')">StatsWiki</a>
      <span class="crumb-sep">/</span>
      <a href="#" @click.prevent="go('wikirace')">Wikirace</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-current">Help</span>
    </nav>

    <p v-if="loading" class="status">Loading help…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <template v-else-if="help">
      <p v-if="help.updated" class="help-meta">Updated {{ help.updated }}</p>
      <div class="help-prose" v-html="help.html" @click="onHelpClick" />
      <p class="help-back">
        <a href="#" @click.prevent="go('wikirace')">← Back to Wikirace</a>
      </p>
    </template>
  </article>
</template>
