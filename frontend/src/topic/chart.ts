/**
 * The Topic detail page's engagement chart, behind a small interface of our own
 * (CLAUDE.md §8), as the dot plot's is: ECharts draws it, and tests swap this module for a
 * stand-in.
 */
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

import type { DayRange } from "../explore/range";
import type { EngagementSeries } from "./engagement";

echarts.use([
  LineChart,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  TooltipComponent,
  CanvasRenderer,
]);

export type EngagementPicture = { series: EngagementSeries; range: DayRange };

export type EngagementChart = {
  show: (picture: EngagementPicture) => void;
  resize: () => void;
  dispose: () => void;
};

/** Checked for colour-blind separation and contrast on both the light and dark pages. */
export const SERIES_COLOURS = {
  posts: "#0d9488",
  comments: "#d97706",
  upvotes: "#3b82f6",
  people: "#db2777",
};
const MUTED_INK = "#64748b"; // axis labels and legend text, readable in both themes
const RANGE_SHADE = "rgba(100, 116, 139, 0.15)";
const AREA_OPACITY = 0.55;
const LINE_WIDTH = 2;

export function createEngagementChart(element: HTMLElement): EngagementChart {
  const chart = echarts.init(element);
  return {
    show: (picture) => chart.setOption(optionFor(picture), { notMerge: true }),
    resize: () => chart.resize(),
    dispose: () => chart.dispose(),
  };
}

function optionFor({ series, range }: EngagementPicture) {
  return {
    grid: { left: 40, right: 12, top: 36, bottom: 28 },
    legend: { top: 0, textStyle: { color: MUTED_INK } },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: series.days, axisLabel: { color: MUTED_INK } },
    yAxis: { type: "value", axisLabel: { color: MUTED_INK }, splitLine: { show: false } },
    series: [
      { ...stackedArea("Posts", series.posts, SERIES_COLOURS.posts), markArea: shaded(range) },
      stackedArea("Comments", series.comments, SERIES_COLOURS.comments),
      stackedArea("Upvotes", series.upvotes, SERIES_COLOURS.upvotes),
      {
        name: "People",
        type: "line",
        data: series.people,
        showSymbol: false,
        lineStyle: { width: LINE_WIDTH, color: SERIES_COLOURS.people },
        itemStyle: { color: SERIES_COLOURS.people },
      },
    ],
  };
}

function stackedArea(name: string, data: number[], colour: string) {
  return {
    name,
    type: "line",
    stack: "engagement",
    data,
    showSymbol: false,
    lineStyle: { width: 0 },
    areaStyle: { color: colour, opacity: AREA_OPACITY },
    itemStyle: { color: colour },
  };
}

/** The range chosen on Explore, shaded behind the areas. */
function shaded(range: DayRange) {
  return {
    silent: true,
    itemStyle: { color: RANGE_SHADE },
    data: [[{ xAxis: range.start }, { xAxis: range.end }]],
  };
}
