<script setup>
import { computed } from 'vue';
import { fmtViews } from './lib.js';

const props = defineProps({
  points: { type: Array, required: true },
  height: { type: Number, default: 160 },
});

const width = 720;

const layout = computed(() => {
  const pts = props.points;
  if (!pts.length) return null;
  const maxV = Math.max(...pts.map((p) => p.views), 1);
  const pad = { t: 8, r: 8, b: 28, l: 52 };
  const innerW = width - pad.l - pad.r;
  const innerH = props.height - pad.t - pad.b;
  const coords = pts.map((p, i) => ({
    x: pad.l + (pts.length === 1 ? innerW / 2 : (i / (pts.length - 1)) * innerW),
    y: pad.t + innerH - (p.views / maxV) * innerH,
    ...p,
  }));
  const line = coords.map((c) => `${c.x},${c.y}`).join(' ');
  const area = `${coords[0].x},${pad.t + innerH} ${line} ${coords.at(-1).x},${pad.t + innerH}`;
  return { coords, line, area, maxV, pad, innerH };
});
</script>

<template>
  <div v-if="layout" class="chart-wrap">
    <svg :viewBox="`0 0 ${width} ${height}`" class="chart" role="img" :aria-label="`Views chart, ${points.length} points`">
      <line
        :x1="layout.pad.l" :y1="layout.pad.t + layout.innerH"
        :x2="width - layout.pad.r" :y2="layout.pad.t + layout.innerH"
        class="axis"
      />
      <polygon :points="layout.area" class="area" />
      <polyline :points="layout.line" class="line" fill="none" />
      <circle
        v-for="(c, i) in layout.coords"
        :key="i"
        :cx="c.x" :cy="c.y" r="3"
        class="dot"
      >
        <title>{{ c.period }}: {{ fmtViews(c.views) }}</title>
      </circle>
    </svg>
    <div class="chart-labels">
      <span>{{ points[0]?.period }}</span>
      <span>{{ points.at(-1)?.period }}</span>
    </div>
  </div>
  <p v-else class="empty">No chart data.</p>
</template>
