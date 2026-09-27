/** Generate workflow 5's configured held-out permutation-importance figure. */

import fs from "node:fs";
import path from "node:path";
import {
  getArgs,
  getFigureSettings,
  line,
  loadWorkflowConfig,
  number,
  readCsv,
  resolvePath,
  svgDocument,
  xmlEscape,
} from "../common/figure_utils.mjs";

function featureImportanceFigure(rows, outputDirectory, config, figure) {
  const settings = config.figures;
  const plot = settings.importance_plot;
  const importance = rows
    .map((row) => ({
      feature: row.feature,
      mean: number(row.mean_mae_increase_vehicles_per_hour, "mean_mae_increase_vehicles_per_hour"),
      sd: number(row.std_mae_increase_vehicles_per_hour, "std_mae_increase_vehicles_per_hour"),
    }))
    .sort((first, second) => second.mean - first.mean)
    .slice(0, config.interpretation.top_n)
    .reverse();
  const left = plot.left;
  const right = figure.width - plot.right_padding;
  const top = plot.top;
  const bottom = figure.height - plot.bottom_padding;
  const low = Math.min(0, ...importance.map((entry) => entry.mean - entry.sd));
  const high = Math.max(0, ...importance.map((entry) => entry.mean + entry.sd));
  const span = Math.max(plot.minimum_span, high - low);
  const xFor = (value) => left + ((value - low) / span) * (right - left);
  const rowHeight = (bottom - top) / importance.length;
  let body = "";
  for (let tick = 0; tick <= settings.axis_intervals; tick += 1) {
    const value = low + (span * tick) / settings.axis_intervals;
    const x = left + ((right - left) * tick) / settings.axis_intervals;
    body += line(x, top, x, bottom, "grid");
    body += `<text class="label" x="${x}" y="${bottom + plot.tick_label_offset}">${value.toFixed(plot.tick_decimal_places)}</text>`;
  }
  const zeroX = xFor(0);
  body += line(zeroX, top, zeroX, bottom, "tick", `stroke-width="${plot.zero_line_width}" stroke="${figure.colors.ink}"`);
  importance.forEach((entry, index) => {
    const centerY = top + rowHeight * (index + 0.5);
    const barHeight = rowHeight * plot.bar_height_fraction;
    const valueX = xFor(entry.mean);
    body += `<text class="small" x="${left - plot.label_gap}" y="${centerY + plot.feature_label_baseline_offset}">${xmlEscape(entry.feature)}</text>`;
    body += `<rect x="${Math.min(zeroX, valueX)}" y="${centerY - barHeight / 2}" width="${Math.max(plot.minimum_bar_width, Math.abs(valueX - zeroX))}" height="${barHeight}" fill="${figure.colors.orange}"/>`;
    const lowX = xFor(Math.max(low, entry.mean - entry.sd));
    const highX = xFor(Math.min(high, entry.mean + entry.sd));
    body += line(lowX, centerY, highX, centerY, "tick", `stroke-width="${plot.error_line_width}" stroke="${figure.colors.ink}"`);
    body += line(lowX, centerY - plot.error_cap_height / 2, lowX, centerY + plot.error_cap_height / 2, "tick", `stroke="${figure.colors.ink}"`);
    body += line(highX, centerY - plot.error_cap_height / 2, highX, centerY + plot.error_cap_height / 2, "tick", `stroke="${figure.colors.ink}"`);
  });
  body += line(left, top, left, bottom);
  body += line(left, bottom, right, bottom);
  body += `<text class="label" x="${(left + right) / 2}" y="${figure.height - plot.x_label_bottom_padding}">${xmlEscape(plot.x_label)}</text>`;
  body += `<text class="label" transform="translate(${plot.y_label_x} ${(top + bottom) / 2}) rotate(-90)">${xmlEscape(plot.y_label)}</text>`;
  fs.writeFileSync(
    path.join(outputDirectory, config.outputs.figure_filename),
    svgDocument(plot.title, body, figure),
    "utf-8",
  );
}

function main() {
  const args = getArgs(process.argv.slice(2), ["work_space"]);
  const workspace = path.resolve(args.work_space);
  const configPath = args.config_path ?? "config/workflow_5_model_interpretation/config.json";
  const config = loadWorkflowConfig(workspace, configPath, {
    data_path: args.data_path,
    output_path: args.output_path,
  });
  const figure = getFigureSettings(config, "figures");
  const outputRoot = resolvePath(workspace, config.output_path);
  const outputDirectory = path.join(outputRoot, config.outputs.directory);
  const importancePath = path.join(outputDirectory, config.outputs.importance_filename);
  const importanceRows = readCsv(importancePath);
  featureImportanceFigure(importanceRows, outputDirectory, config, figure);
  console.log(`Saved permutation-importance SVG under ${outputDirectory}`);
}

try {
  main();
} catch (error) {
  console.error(`Workflow 5 figure generation failed: ${error.message}`);
  process.exitCode = 1;
}
