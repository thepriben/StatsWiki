<script setup>
import { fmtViews, titleText, wikiUrl, wikidataUrl } from './lib.js';

defineProps({
  lines: { type: Array, required: true },
  compact: { type: Boolean, default: false },
});
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
          <a :href="wikiUrl(line.title)">{{ line.label || titleText(line) }}</a>
          <template v-if="!compact">
            <span v-if="line.description" class="desc">{{ line.description }}</span>
            <a v-if="wikidataUrl(line.qid)" class="qid" :href="wikidataUrl(line.qid)">{{ line.qid }}</a>
            <img v-if="line.image" class="thumb" :src="line.image" :alt="line.label" loading="lazy" decoding="async" />
          </template>
        </td>
        <td class="num">{{ fmtViews(line.views) }}</td>
      </tr>
    </tbody>
  </table>
</template>
