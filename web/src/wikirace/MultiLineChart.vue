<script setup>
import { computed, ref } from 'vue';
import { fmtViews } from '../lib.js';
import { CHART_COLORS } from './lib.js';

const props = defineProps({
  series: { type: Array, required: true },
  height: { type: Number, default: 240 },
});

const mode = ref('stacked');

const width = 720;

function alignToDays(items) {
  const days = [...new Set(items.flatMap((s) => s.points.map((p) => p.day)))].sort();
  return items.map((s, si) => {
    const byDay = new Map(s.points.map((p) => [p.day, p.views]));
    return {
      ...s,
      color: CHART_COLORS[si % CHART_COLORS.length],
      points: days.map((day) => ({ day, views: byDay.get(day) ?? 0 })),
    };
  });
}

function yScale(v, maxV, pad, innerH) {
  return pad.t + innerH - (v / maxV) * innerH;
}

const layout = computed(() => {
  const items = alignToDays(props.series.filter((s) => s.points?.length));
  if (!items.length) return null;

  const days = items[0].points.map((p) => p.day);
  const pad = { t: 14, r: 12, b: 32, l: 56 };
  const innerW = width - pad.l - pad.r;
  const innerH = props.height - pad.t - pad.b;
  const xAt = (i) => pad.l + (days.length === 1 ? innerW / 2 : (i / (days.length - 1)) * innerW);

  if (mode.value === 'stacked') {
    const stackItems = [...items].sort((a, b) => (a.total ?? 0) - (b.total ?? 0));
    const dailyTotals = days.map((_, i) =>
      items.reduce((s, item) => s + item.points[i].views, 0),
    );
    const maxV = Math.max(1, ...dailyTotals);
    const cumul = Array(days.length).fill(0);

    const layers = stackItems.map((s) => {
      const bands = s.points.map((p, i) => {
        const bottom = cumul[i];
        cumul[i] += p.views;
        return { x: xAt(i), day: p.day, views: p.views, bottom, top: cumul[i] };
      });
      const topCoords = bands.map((b) => ({
        x: b.x,
        y: yScale(b.top, maxV, pad, innerH),
      }));
      const bottomCoords = bands
        .map((b) => ({ x: b.x, y: yScale(b.bottom, maxV, pad, innerH) }))
        .reverse();
      const area = [...topCoords, ...bottomCoords].map((c) => `${c.x},${c.y}`).join(' ');
      const line = topCoords.map((c) => `${c.x},${c.y}`).join(' ');
      return { ...s, bands, area, line };
    });

    const gridLines = [0.25, 0.5, 0.75].map((f) => ({
      y: yScale(maxV * f, maxV, pad, innerH),
      label: fmtViews(Math.round(maxV * f)),
    }));

    return {
      mode: 'stacked',
      layers,
      legendLines: items,
      days,
      maxV,
      pad,
      innerH,
      gridLines,
      baselineY: pad.t + innerH,
    };
  }

  const maxV = Math.max(1, ...items.flatMap((s) => s.points.map((p) => p.views)));
  const lines = items.map((s) => {
    const coords = s.points.map((p, i) => ({
      x: xAt(i),
      y: yScale(p.views, maxV, pad, innerH),
      ...p,
    }));
    const line = coords.map((c) => `${c.x},${c.y}`).join(' ');
    const area = `${coords[0].x},${pad.t + innerH} ${line} ${coords.at(-1).x},${pad.t + innerH}`;
    return { ...s, coords, line, area };
  });

  const drawLines = [...lines].sort((a, b) => (a.total ?? 0) - (b.total ?? 0));

  return {
    mode: 'overlay',
    drawLines,
    legendLines: lines,
    days,
    maxV,
    pad,
    innerH,
    baselineY: pad.t + innerH,
  };
});

const periodCaption = computed(() => {
  if (!layout.value) return '';
  const { days } = layout.value;
  const range = `${days[0]} → ${days.at(-1)}`;
  return mode.value === 'stacked'
    ? `${range} · stacked daily share (band area = Race%)`
    : `${range} · daily views per article (shared scale)`;
});

const ariaLabel = computed(() =>
  mode.value === 'stacked'
    ? 'Stacked daily pageview share; each band area matches Race percent'
    : 'Daily pageviews per article on a shared scale',
);
</script>

<template>
  <div v-if="layout" class="multi-chart-wrap">
    <div class="chart-toolbar chart-mode-toolbar" role="tablist" aria-label="Chart mode">
      <button
        type="button"
        role="tab"
        :class="{ active: mode === 'stacked' }"
        :aria-selected="mode === 'stacked'"
        @click="mode = 'stacked'"
      >Stacked share</button>
      <button
        type="button"
        role="tab"
        :class="{ active: mode === 'overlay' }"
        :aria-selected="mode === 'overlay'"
        @click="mode = 'overlay'"
      >Daily compare</button>
    </div>

    <svg
      :viewBox="`0 0 ${width} ${height}`"
      class="multi-chart"
      role="img"
      :aria-label="ariaLabel"
    >
      <template v-if="layout.mode === 'stacked'">
        <line
          v-for="(g, gi) in layout.gridLines"
          :key="'g' + gi"
          :x1="layout.pad.l"
          :y1="g.y"
          :x2="width - layout.pad.r"
          :y2="g.y"
          class="grid-line"
        />
        <text
          v-for="(g, gi) in layout.gridLines"
          :key="'gl' + gi"
          :x="layout.pad.l - 6"
          :y="g.y + 3"
          class="y-label"
          text-anchor="end"
        >{{ g.label }}</text>
        <line
          :x1="layout.pad.l"
          :y1="layout.baselineY"
          :x2="width - layout.pad.r"
          :y2="layout.baselineY"
          class="axis"
        />
        <g v-for="(layer, i) in layout.layers" :key="layer.qid || i">
          <polygon :points="layer.area" class="stack-area" :style="{ fill: layer.color + '52' }" />
          <polyline :points="layer.line" class="stack-edge" fill="none" :style="{ stroke: layer.color }" />
        </g>
        <text
          :x="layout.pad.l - 6"
          :y="layout.pad.t + 4"
          class="y-label"
          text-anchor="end"
        >{{ fmtViews(layout.maxV) }}</text>
        <text
          :x="layout.pad.l - 6"
          :y="layout.baselineY"
          class="y-label"
          text-anchor="end"
        >0</text>
      </template>

      <template v-else>
        <line
          :x1="layout.pad.l"
          :y1="layout.baselineY"
          :x2="width - layout.pad.r"
          :y2="layout.baselineY"
          class="axis"
        />
        <g v-for="(s, i) in layout.drawLines" :key="s.qid || i">
          <polygon :points="s.area" class="area" :style="{ fill: s.color + '18' }" />
          <polyline :points="s.line" class="line" fill="none" :style="{ stroke: s.color }" />
        </g>
        <text
          :x="layout.pad.l - 6"
          :y="layout.pad.t + 4"
          class="y-label"
          text-anchor="end"
        >{{ fmtViews(layout.maxV) }}</text>
        <text
          :x="layout.pad.l - 6"
          :y="layout.baselineY"
          class="y-label"
          text-anchor="end"
        >0</text>
      </template>
    </svg>

    <p class="chart-period">{{ periodCaption }}</p>
    <div class="chart-labels">
      <span>{{ layout.days[0] }}</span>
      <span>{{ layout.days.at(-1) }}</span>
    </div>
    <ul class="chart-legend">
      <li v-for="(s, i) in layout.legendLines" :key="s.qid || i">
        <span class="legend-swatch" :style="{ background: s.color }" />
        {{ s.label }}
        <span v-if="s.racePct != null" class="legend-pct">{{ s.racePct.toFixed(1) }}%</span>
      </li>
    </ul>
  </div>
  <p v-else class="empty">No chart data.</p>
</template>
