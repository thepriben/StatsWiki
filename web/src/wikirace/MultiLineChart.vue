<script setup>
import { computed } from 'vue';
import { fmtViews } from '../lib.js';
import { CHART_COLORS } from './lib.js';

const props = defineProps({
  series: { type: Array, required: true },
  height: { type: Number, default: 220 },
});

const width = 720;

const layout = computed(() => {
  const items = props.series.filter((s) => s.points?.length);
  if (!items.length) return null;

  const days = items[0].points.map((p) => p.day);
  const maxV = Math.max(1, ...items.flatMap((s) => s.points.map((p) => p.views)));
  const pad = { t: 12, r: 12, b: 32, l: 56 };
  const innerW = width - pad.l - pad.r;
  const innerH = props.height - pad.t - pad.b;

  const lines = items.map((s, si) => {
    const coords = s.points.map((p, i) => ({
      x: pad.l + (days.length === 1 ? innerW / 2 : (i / (days.length - 1)) * innerW),
      y: pad.t + innerH - (p.views / maxV) * innerH,
      ...p,
    }));
    const line = coords.map((c) => `${c.x},${c.y}`).join(' ');
    const area = `${coords[0].x},${pad.t + innerH} ${line} ${coords.at(-1).x},${pad.t + innerH}`;
    return { ...s, coords, line, area, color: CHART_COLORS[si % CHART_COLORS.length] };
  });

  return { lines, days, maxV, pad, innerH };
});
</script>

<template>
  <div v-if="layout" class="multi-chart-wrap">
    <svg
      :viewBox="`0 0 ${width} ${height}`"
      class="multi-chart"
      role="img"
      aria-label="Daily pageviews; shaded area under each curve matches Race percent"
    >
      <line
        :x1="layout.pad.l"
        :y1="layout.pad.t + layout.innerH"
        :x2="width - layout.pad.r"
        :y2="layout.pad.t + layout.innerH"
        class="axis"
      />
      <g v-for="(s, i) in layout.lines" :key="s.qid || i">
        <polygon :points="s.area" class="area" :style="{ fill: s.color + '18' }" />
        <polyline :points="s.line" class="line" fill="none" :style="{ stroke: s.color }" />
      </g>
      <text
        :x="layout.pad.l - 6"
        :y="layout.pad.t + 4"
        class="y-label"
        text-anchor="end"
      >{{ fmtViews(layout.maxV) }}</text>
    </svg>
    <div class="chart-labels">
      <span>{{ layout.days[0] }}</span>
      <span>{{ layout.days.at(-1) }}</span>
    </div>
    <ul class="chart-legend">
      <li v-for="(s, i) in layout.lines" :key="s.qid || i">
        <span class="legend-swatch" :style="{ background: s.color }" />
        {{ s.label }}
      </li>
    </ul>
  </div>
  <p v-else class="empty">No chart data.</p>
</template>
