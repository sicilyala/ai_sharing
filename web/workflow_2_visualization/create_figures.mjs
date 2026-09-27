/** Generate workflow 2's configured traffic-volume summary figures. */

import fs from "node:fs";
import path from "node:path";
import {
  formatNumber,
  getArgs,
  getFigureSettings,
  line,
  loadWorkflowConfig,
  niceMaximum,
  number,
  readCsv,
  resolvePath,
  svgDocument,
  timestampParts,
  xmlEscape,
  yAxis,
} from "../common/figure_utils.mjs";

function averageTrafficByHour(rows, outputDirectory, dataset, visualization, figure) {
  const settings = visualization.hour_plot;
  const totals = Array.from({ length: settings.group_count }, () => ({ sum: 0, count: 0 }));
  for (const row of rows) {
    const { hour } = timestampParts(row[dataset.date_column]);
    const entry = totals[hour];
    entry.sum += number(row[dataset.target_column], dataset.target_column);
    entry.count += 1;
  }
  const means = totals.map((entry) => entry.sum / entry.count);
  const maximum = niceMaximum(Math.max(...means), visualization.axis_intervals);
  const right = figure.width - settings.right_padding;
  const bottom = settings.bottom;
  const chartWidth = right - settings.left;
  let body = yAxis({
    left: settings.left,
    top: settings.top,
    bottom,
    maximum,
    intervals: visualization.axis_intervals,
    rightPadding: settings.right_padding,
    xLabelBottomPadding: visualization.axis_label_layout.x_label_bottom_padding,
    yLabelX: visualization.axis_label_layout.y_label_x,
    tickLabelGap: visualization.axis_label_layout.tick_label_gap,
    tickTextBaselineOffset: visualization.axis_label_layout.tick_text_baseline_offset,
    xLabel: settings.x_label,
    yLabel: settings.y_label,
    figure,
  });
  const points = means
    .map((value, index) => {
      const x = settings.left + (chartWidth * index) / Math.max(1, means.length - 1);
      const y = bottom - ((bottom - settings.top) * value) / maximum;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
  body += `<polyline points="${points}" fill="none" stroke="${figure.colors.blue}" stroke-width="${settings.line_width}"/>`;
  for (let hour = 0; hour < settings.group_count; hour += settings.tick_interval) {
    const x = settings.left + (chartWidth * hour) / Math.max(1, settings.group_count - 1);
    body += line(x, bottom, x, bottom + 7, "tick");
    body += `<text class="label" x="${x}" y="${bottom + settings.tick_label_offset}">${hour}</text>`;
  }
  fs.writeFileSync(
    path.join(outputDirectory, settings.output_filename),
    svgDocument(settings.title, body, figure),
    "utf-8",
  );
}

function averageTrafficByWeekday(rows, outputDirectory, dataset, visualization, figure) {
  const settings = visualization.weekday_plot;
  const weekdayNames = visualization.weekday_names;
  const totals = Array.from({ length: weekdayNames.length }, () => ({ sum: 0, count: 0 }));
  for (const row of rows) {
    const { weekday } = timestampParts(row[dataset.date_column]);
    const entry = totals[weekday];
    entry.sum += number(row[dataset.target_column], dataset.target_column);
    entry.count += 1;
  }
  const means = totals.map((entry) => entry.sum / entry.count);
  const maximum = niceMaximum(Math.max(...means), visualization.axis_intervals);
  const right = figure.width - settings.right_padding;
  const bottom = settings.bottom;
  const plotWidth = right - settings.left;
  let body = yAxis({
    left: settings.left,
    top: settings.top,
    bottom,
    maximum,
    intervals: visualization.axis_intervals,
    rightPadding: settings.right_padding,
    xLabelBottomPadding: visualization.axis_label_layout.x_label_bottom_padding,
    yLabelX: visualization.axis_label_layout.y_label_x,
    tickLabelGap: visualization.axis_label_layout.tick_label_gap,
    tickTextBaselineOffset: visualization.axis_label_layout.tick_text_baseline_offset,
    xLabel: settings.x_label,
    yLabel: settings.y_label,
    figure,
  });
  means.forEach((value, index) => {
    const center = settings.left + (plotWidth * (index + 0.5)) / means.length;
    const barHeight = ((bottom - settings.top) * value) / maximum;
    body += `<rect x="${center - settings.bar_width / 2}" y="${bottom - barHeight}" width="${settings.bar_width}" height="${barHeight}" fill="${figure.colors.blue}"/>`;
    body += `<text class="label" x="${center}" y="${bottom + settings.tick_label_offset}">${xmlEscape(weekdayNames[index])}</text>`;
  });
  fs.writeFileSync(
    path.join(outputDirectory, settings.output_filename),
    svgDocument(settings.title, body, figure),
    "utf-8",
  );
}

function averageTrafficByWeather(rows, outputDirectory, dataset, visualization, figure) {
  const settings = visualization.weather_plot;
  const groups = new Map();
  for (const row of rows) {
    const category = row[dataset.weather_column] || settings.blank_category_label;
    const group = groups.get(category) ?? { sum: 0, count: 0 };
    group.sum += number(row[dataset.target_column], dataset.target_column);
    group.count += 1;
    groups.set(category, group);
  }
  const weather = [...groups.entries()]
    .map(([category, value]) => ({ category, mean: value.sum / value.count, count: value.count }))
    .sort((first, second) => first.mean - second.mean);
  const left = settings.left;
  const right = figure.width - settings.right_padding;
  const top = settings.top;
  const bottom = figure.height - settings.bottom_padding;
  const maximum = niceMaximum(Math.max(...weather.map((entry) => entry.mean)), visualization.axis_intervals);
  const rowHeight = (bottom - top) / weather.length;
  let body = "";
  for (let tick = 0; tick <= visualization.axis_intervals; tick += 1) {
    const value = (maximum * tick) / visualization.axis_intervals;
    const x = left + ((right - left) * tick) / visualization.axis_intervals;
    body += line(x, top, x, bottom, "grid");
    body += `<text class="label" x="${x}" y="${bottom + settings.tick_label_offset}">${formatNumber(value)}</text>`;
  }
  weather.forEach((entry, index) => {
    const y = top + rowHeight * index + rowHeight * settings.bar_vertical_offset_fraction;
    const height = rowHeight * settings.bar_height_fraction;
    const width = ((right - left) * entry.mean) / maximum;
    body += `<text class="small" x="${left - settings.label_gap}" y="${y + height * settings.label_vertical_offset_fraction}">${xmlEscape(entry.category)} (n=${entry.count.toLocaleString("en-US")})</text>`;
    body += `<rect x="${left}" y="${y}" width="${width}" height="${height}" fill="${figure.colors.green}"/>`;
  });
  body += line(left, top, left, bottom);
  body += line(left, bottom, right, bottom);
  body += `<text class="label" x="${(left + right) / 2}" y="${figure.height - settings.x_label_bottom_padding}">${xmlEscape(settings.x_label)}</text>`;
  body += `<text class="label" transform="translate(${settings.y_label_x} ${(top + bottom) / 2}) rotate(-90)">${xmlEscape(settings.y_label)}</text>`;
  fs.writeFileSync(
    path.join(outputDirectory, settings.output_filename),
    svgDocument(settings.title, body, figure),
    "utf-8",
  );
}

function main() {
  const args = getArgs(process.argv.slice(2), ["work_space"]);
  const workspace = path.resolve(args.work_space);
  const configPath = args.config_path ?? "config/workflow_2_visualization/config.json";
  const config = loadWorkflowConfig(workspace, configPath, {
    data_path: args.data_path,
    output_path: args.output_path,
  });
  const dataset = config.dataset;
  const visualization = config.visualization;
  const figure = getFigureSettings(config, "visualization");
  const dataDirectory = resolvePath(workspace, config.data_path);
  const outputRoot = resolvePath(workspace, config.output_path);
  const rawPath = path.join(dataDirectory, dataset.filename);
  if (!fs.existsSync(rawPath)) throw new Error(`Raw dataset not found: ${rawPath}`);
  const rows = readCsv(rawPath);
  const outputDirectory = path.join(outputRoot, visualization.output_directory);
  fs.mkdirSync(outputDirectory, { recursive: true });
  averageTrafficByHour(rows, outputDirectory, dataset, visualization, figure);
  averageTrafficByWeekday(rows, outputDirectory, dataset, visualization, figure);
  averageTrafficByWeather(rows, outputDirectory, dataset, visualization, figure);
  console.log(`Saved three SVG figures under ${outputDirectory}`);
}

try {
  main();
} catch (error) {
  console.error(`Workflow 2 figure generation failed: ${error.message}`);
  process.exitCode = 1;
}
