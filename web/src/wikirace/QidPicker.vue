<script setup>
import { onMounted, ref, watch } from 'vue';
import { wikiUrl, wikidataUrl } from '../lib.js';
import {
  CHART_COLORS,
  catalogLookup,
  loadArticleCatalog,
  mergeSearchResults,
  searchCatalog,
  searchWikidata,
} from './lib.js';

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  min: { type: Number, default: 2 },
  max: { type: Number, default: 10 },
});

const emit = defineEmits(['update:modelValue']);

const catalog = ref([]);
const catalogError = ref('');
const query = ref('');
const open = ref(false);
const activeIdx = ref(0);
const inputRef = ref(null);
const suggestions = ref([]);
const searching = ref(false);
let searchSeq = 0;
let debounceTimer = null;

function chipColor(i) {
  return CHART_COLORS[i % CHART_COLORS.length];
}

function chipArticle(member) {
  if (member.article) return member.article;
  const hit = catalogLookup(catalog.value, member.qid);
  return hit?.article || '';
}

onMounted(async () => {
  try {
    catalog.value = await loadArticleCatalog();
  } catch {
    catalogError.value = 'Local catalog unavailable — Wikidata search still works, or type a QID.';
  }
});

function exactQidSuggestion(q, exclude) {
  if (!/^Q\d+$/i.test(q)) return null;
  const exact = q.toUpperCase();
  if (exclude.includes(exact)) return null;
  return { qid: exact, label: exact, article: '', source: 'qid' };
}

async function runSearch(q) {
  const seq = ++searchSeq;
  const exclude = props.modelValue.map((m) => m.qid);
  const catalogHits = searchCatalog(catalog.value, q, { limit: 8, exclude });

  let merged = catalogHits;
  if (q.length >= 2 && catalogHits.length < 8) {
    searching.value = true;
    try {
      const wdHits = await searchWikidata(q, { limit: 8 - catalogHits.length, exclude });
      if (seq !== searchSeq) return;
      merged = mergeSearchResults(catalogHits, wdHits, 8);
    } catch {
      if (seq !== searchSeq) return;
      merged = catalogHits;
    } finally {
      if (seq === searchSeq) searching.value = false;
    }
  }

  if (seq !== searchSeq) return;
  const exact = exactQidSuggestion(q, exclude);
  if (exact && !merged.some((h) => h.qid === exact.qid)) {
    merged = [exact, ...merged].slice(0, 8);
  }
  suggestions.value = merged;
}

function scheduleSearch() {
  const q = query.value.trim();
  clearTimeout(debounceTimer);
  if (!q) {
    searchSeq += 1;
    searching.value = false;
    suggestions.value = [];
    open.value = false;
    return;
  }
  open.value = true;
  activeIdx.value = 0;
  debounceTimer = setTimeout(() => runSearch(q), 280);
}

const atMax = () => props.modelValue.length >= props.max;

function addItem(item) {
  if (atMax() || props.modelValue.some((m) => m.qid === item.qid)) return;
  emit('update:modelValue', [
    ...props.modelValue,
    { qid: item.qid, label: item.label, article: item.article || '' },
  ]);
  query.value = '';
  suggestions.value = [];
  open.value = false;
  activeIdx.value = 0;
  inputRef.value?.focus();
}

function removeItem(qid) {
  emit('update:modelValue', props.modelValue.filter((m) => m.qid !== qid));
}

function onKeydown(e) {
  if (!open.value || !suggestions.value.length) {
    if (e.key === 'Enter' && /^Q\d+$/i.test(query.value.trim())) {
      e.preventDefault();
      addItem({ qid: query.value.trim().toUpperCase(), label: query.value.trim().toUpperCase() });
    }
    return;
  }

  if (e.key === 'ArrowDown') {
    e.preventDefault();
    activeIdx.value = (activeIdx.value + 1) % suggestions.value.length;
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    activeIdx.value = (activeIdx.value - 1 + suggestions.value.length) % suggestions.value.length;
  } else if (e.key === 'Enter') {
    e.preventDefault();
    addItem(suggestions.value[activeIdx.value]);
  } else if (e.key === 'Escape') {
    open.value = false;
  }
}

function onBlur() {
  setTimeout(() => { open.value = false; }, 150);
}

watch(query, scheduleSearch);
</script>

<template>
  <div class="qid-picker">
    <label class="field">
      <span>Articles in this race</span>
      <p v-if="catalogError" class="hint">{{ catalogError }}</p>

      <ul v-if="modelValue.length" class="qid-chips" aria-label="Selected articles">
        <li v-for="(m, i) in modelValue" :key="m.qid" class="qid-chip">
          <span class="qid-chip-color" :style="{ background: chipColor(i) }" aria-hidden="true" />
          <a
            v-if="chipArticle(m)"
            :href="wikiUrl(chipArticle(m))"
            class="qid-chip-label race-name"
            target="_blank"
            rel="noopener noreferrer"
            @click.stop
          >{{ m.label }}</a>
          <span v-else class="qid-chip-label">{{ m.label }}</span>
          <a
            v-if="wikidataUrl(m.qid)"
            :href="wikidataUrl(m.qid)"
            class="race-ext-link"
            target="_blank"
            rel="noopener noreferrer"
            :aria-label="`Wikidata: ${m.qid}`"
            @click.stop
          >{{ m.qid }} ↗</a>
          <button type="button" class="qid-chip-remove" :aria-label="`Remove ${m.label}`" @click="removeItem(m.qid)">×</button>
        </li>
      </ul>

      <div class="qid-search-wrap">
        <input
          ref="inputRef"
          v-model="query"
          type="search"
          class="qid-search"
          placeholder="Search by name or QID…"
          autocomplete="off"
          spellcheck="false"
          :disabled="atMax()"
          @focus="scheduleSearch"
          @blur="onBlur"
          @keydown="onKeydown"
        />
        <ul v-if="open && suggestions.length" class="qid-suggestions" role="listbox">
          <li
            v-for="(item, i) in suggestions"
            :key="item.qid"
            role="option"
            :aria-selected="i === activeIdx"
            :class="{ active: i === activeIdx }"
            @mousedown.prevent="addItem(item)"
          >
            <div class="qid-suggestion-main">
              <strong>{{ item.label }}</strong>
              <span class="qid-suggestion-meta">{{ item.qid }}</span>
            </div>
            <span v-if="item.description" class="qid-suggestion-desc">{{ item.description }}</span>
          </li>
        </ul>
      </div>

      <p class="hint qid-picker-hint">
        {{ modelValue.length }} selected · min {{ min }} · max {{ max }}
        <span v-if="atMax()"> · group full</span>
        <span v-else-if="searching"> · searching Wikidata…</span>
      </p>
    </label>
  </div>
</template>
