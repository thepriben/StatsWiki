<script setup>
import { fmtViews, statsUrl, titleText, wikiUrl, wikidataUrl } from './lib.js';

defineProps({
  lines: { type: Array, required: true },
  compact: { type: Boolean, default: false },
});

const emit = defineEmits(['open-qid']);

function openQid(e, qid) {
  const path = statsUrl(qid);
  if (!path) return;
  e.preventDefault();
  emit('open-qid', `q/${qid}`);
}
</script>

<template>
  <table :class="{ compact }">
    <thead>
      <tr><th>#</th><th>Article</th><th class="num">Views</th></tr>
    </thead>
    <tbody>
      <tr v-for="line in lines" :key="line.title">
        <td>{{ line.rank }}</td>
        <td>
          <a :href="wikiUrl(line.title)" class="link">{{ line.label || titleText(line) }}</a>
          <a
            v-if="wikidataUrl(line.qid)"
            class="qid"
            :href="statsUrl(line.qid) || wikidataUrl(line.qid)"
            @click="openQid($event, line.qid)"
          >{{ line.qid }}</a>
          <template v-if="!compact">
            <span v-if="line.description" class="desc">{{ line.description }}</span>
            <img v-if="line.image" class="thumb" :src="line.image" :alt="line.label" loading="lazy" decoding="async" />
          </template>
        </td>
        <td class="num">{{ fmtViews(line.views) }}</td>
      </tr>
    </tbody>
  </table>
</template>
