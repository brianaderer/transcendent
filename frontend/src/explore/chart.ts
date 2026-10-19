/**
 * The dot plot's chart, behind a small interface of our own (CLAUDE.md §8): ECharts draws a
 * few thousand points on a canvas, and tests swap this module for a stand-in.
 */
import { ScatterChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([ScatterChart, GridComponent, TooltipComponent, CanvasRenderer]);

export type Dot = {
  id: string;
  x: number;
  y: number;
  colour: string;
  faded: boolean; // another topic is highlighted
  card: string; // the hover card, already escaped HTML
  link: string;
};

export type Scatter = { show: (dots: Dot[]) => void; resize: () => void; dispose: () => void };

const GLIDE_MS = 900;
const DOT_SIZE = 6;
const FADED_OPACITY = 0.12;
const SHOWN_OPACITY = 0.85;
const CARD_WIDTH_PX = 320;

export function createScatter(element: HTMLElement, open: (link: string) => void): Scatter {
  const chart = echarts.init(element);
  chart.on("click", (event) => open((event.data as Dot).link));
  return {
    show: (dots) => chart.setOption(optionFor(dots), { replaceMerge: ["series"] }),
    resize: () => chart.resize(),
    dispose: () => chart.dispose(),
  };
}

function optionFor(dots: Dot[]) {
  return {
    animationDurationUpdate: GLIDE_MS,
    animationEasingUpdate: "cubicInOut" as const,
    grid: { left: 8, right: 8, top: 8, bottom: 8 },
    xAxis: { show: false, scale: true },
    yAxis: { show: false, scale: true },
    tooltip: {
      trigger: "item",
      formatter: (item: { data: Dot }) => item.data.card,
      extraCssText: `max-width: ${CARD_WIDTH_PX}px; white-space: normal;`,
    },
    series: [
      {
        id: "posts",
        type: "scatter",
        symbolSize: DOT_SIZE,
        data: dots.map((dot) => ({
          ...dot,
          value: [dot.x, dot.y],
          itemStyle: { color: dot.colour, opacity: dot.faded ? FADED_OPACITY : SHOWN_OPACITY },
        })),
      },
    ],
  };
}
