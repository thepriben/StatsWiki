<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { CHART_COLORS, loadArticleCatalog, searchCatalog } from './lib.js';

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  min: { type: Number, default: 2 },
});

const emit = defineEmits(['update:modelValue']);

const catalog = ref([]);
const catalogError = ref('');
const query = ref('');
const open = ref(false);
const activeIdx = ref(0);
const inputRef = ref(null);

function chipColor(i) {
  return CHART_COLORS[i % CHART_COLORS.length];
}

onMounted(async () => {
  try {
    catalog.value = await loadArticleCatalog();
  } catch {
    catalogError.value = 'Catalog unavailable — type a QID manually (e.g. Q22686).';
  }
});

const suggestions = computed(() => {
  const q = query.value.trim();
  if (!q) return [];
  const exclude = props.modelValue.map((m) => m.qid);
  const hits = searchCatalog(catalog.value, q, { limit: 8, exclude });

  if (/^Q\d+$/i.test(q) && !exclude.includes(q.toUpperCase())) {
    const exact = q.toUpperCase();
    if (!hits.some((h) => h.qid === exact)) {
      hits.unshift({ qid: exact, label: exact, article: '', score: 95 });
    }
  }

  return hits.slice(0, 8);
});

function addItem(item) {
  if (props.modelValue.some((m) => m.qid === item.qid)) return;
  emit('update:modelValue', [
    ...props.modelValue,
    { qid: item.qid, label: item.label },
  ]);
  query.value = '';
  open.value = false;
  activeIdx.value = 0;
  inputRef.value?.focus();
}

function removeItem(qid) {
  emit('update:modelValue', props.modelValue.filter((m) => m.qid !== qid));
}

function onInput() {
  open.value = query.value.trim().length > 0;
  activeIdx.value = 0;
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

watch(query, onInput);
</script>

<template>
  <div class="qid-picker">
    <label class="field">
      <span>Articles in this race</span>
      <p v-if="catalogError" class="hint">{{ catalogError }}</p>

      <ul v-if="modelValue.length" class="qid-chips" aria-label="Selected articles">
        <li v-for="(m, i) in modelValue" :key="m.qid" class="qid-chip">
          <span class="qid-chip-color" :style="{ background: chipColor(i) }" aria-hidden="true" />
          <span class="qid-chip-label">{{ m.label }}</span>
          <span class="qid-chip-id">{{ m.qid }}</span>
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
          @focus="open = query.trim().length > 0"
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
            <strong>{{ item.label }}</strong>
            <span class="qid-suggestion-meta">{{ item.qid }}</span>
          </li>
        </ul>
      </div>

      <p class="hint qid-picker-hint">
        {{ modelValue.length }} selected · need at least {{ min }}
      </p>
    </label>
  </div>
</template>
