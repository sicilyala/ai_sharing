/** Generate workflow 4's configured observed-versus-predicted figures. */

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
  xmlEscape,
  yAxis,
} from "../common/figure_utils.mjs";

function predictionFigures(rows, outputDirectory, config, figure) {
  const settings = config.figures;
  const actual = rows.map((row) => number(row.observed_traffic_volume, "observed_traffic_volume"));
  const predicted = rows.map((row) => number(row.predicted_traffic_volume, "predicted_traffic_volume"));
  const upper = niceMaximum(Math.max(...actual, ...predicted), settings.axis_intervals);
  const scatter = settings.scatter_plot;
  const left = scatter.left;
  const right = figure.width - scatter.right_padding;
  const top = scatter.top;
  const bottom = figure.height - scatter.bottom_padding;
  const plotWidth = right - left;
  const plotHeight = bottom - top;
  let body = "";
  for (let tick = 0; tick <= settings.axis_intervals; tick += 1) {
    const value = (upper * tick) / settings.axis_intervals;
    const x = left + (plotWidth * tick) / settings.axis_intervals;
    const y = bottom - (plotHeight * tick) / settings.axis_intervals;
    body += line(left, y, right, y, "grid");
    body += line(x, top, x, bottom, "grid");
    body += `<text class="label" x="${x}" y="${bottom + scatter.tick_label_offset}">${formatNumber(value)}</text>`;
    body += `<text class="small" x="${left - scatter.tick_label_gap}" y="${y + scatter.tick_text_baseline_offset}">${formatNumber(value)}</text>`;
  }
  body += line(left, top, left, bottom);
  body += line(left, bottom, right, bottom);
  body += line(left, bottom, right, top, "tick", `stroke-dasharray="${scatter.reference_dash}" stroke="${figure.colors.red}"`);
  const pointStep = Math.max(1, Math.ceil(rows.length / settings.max_scatter_points));
  for (let index = 0; index < rows.length; index += pointStep) {
    const x = left + (plotWidth * actual[index]) / upper;
    const y = bottom - (plotHeight * predicted[index]) / upper;
    body += `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="${scatter.point_radius}" fill="${figure.colors.blue}" fill-opacity="${scatter.point_opacity}"/>`;
  }
  body += `<text class="label" x="${(left + right) / 2}" y="${figure.height - scatter.x_label_bottom_padding}">${xmlEscape(scatter.x_label)}</text>`;
  body += `<text class="label" transform="translate(${scatter.y_label_x} ${(top + bottom) / 2}) rotate(-90)">${xmlEscape(scatter.y_label)}</text>`;
  fs.writeFileSync(
    path.join(outputDirectory, settings.scatter_filename),
    svgDocument(scatter.title, body, figure),
    "utf-8",
  );

  const timeSeries = settings.time_series_plot;
  const timeLeft = timeSeries.left;
  const timeRight = figure.width - timeSeries.right_padding;
  const timeTop = timeSeries.top;
  const timeBottom = figure.height - timeSeries.bottom_padding;
  const timeMaximum = niceMaximum(Math.max(...actual, ...predicted), settings.axis_intervals);
  let timeBody = yAxis({
    left: timeLeft,
    top: timeTop,
    bottom: timeBottom,
    maximum: timeMaximum,
    intervals: settings.axis_intervals,
    rightPadding: timeSeries.right_padding,
    xLabelBottomPadding: timeSeries.x_label_bottom_padding,
    yLabelX: timeSeries.y_label_x,
    tickLabelGap: timeSeries.tick_label_gap,
    tickTextBaselineOffset: timeSeries.tick_text_baseline_offset,
    xLabel: timeSeries.x_label,
    yLabel: timeSeries.y_label,
    figure,
  });
  const actualPoints = [];
  const predictedPoints = [];
  rows.forEach((row, index) => {
    const x = timeLeft + ((timeRight - timeLeft) * index) / Math.max(1, rows.length - 1);
    const actualY = timeBottom - ((timeBottom - timeTop) * actual[index]) / timeMaximum;
    const predictedY = timeBottom - ((timeBottom - timeTop) * predicted[index]) / timeMaximum;
    actualPoints.push(`${x.toFixed(2)},${actualY.toFixed(2)}`);
    predictedPoints.push(`${x.toFixed(2)},${predictedY.toFixed(2)}`);
  });
  timeBody += `<polyline points="${actualPoints.join(" ")}" fill="none" stroke="${figure.colors.blue}" stroke-width="${timeSeries.line_width}"/>`;
  timeBody += `<polyline points="${predictedPoints.join(" ")}" fill="none" stroke="${figure.colors.orange}" stroke-width="${timeSeries.line_width}"/>`;
  const legendY = timeTop + timeSeries.legend_top_padding;
  const observedLegendX = timeRight - timeSeries.observed_legend_right_offset;
  const predictedLegendX = timeRight - timeSeries.predicted_legend_right_offset;
  timeBody += `<line x1="${observedLegendX}" y1="${legendY}" x2="${observedLegendX + timeSeries.legend_line_length}" y2="${legendY}" stroke="${figure.colors.blue}" stroke-width="${timeSeries.legend_line_width}"/>`;
  timeBody += `<text x="${observedLegendX + timeSeries.legend_label_gap}" y="${legendY + timeSeries.legend_text_baseline_offset}">${xmlEscape(timeSeries.observed_label)}</text>`;
  timeBody += `<line x1="${predictedLegendX}" y1="${legendY}" x2="${predictedLegendX + timeSeries.legend_line_length}" y2="${legendY}" stroke="${figure.colors.orange}" stroke-width="${timeSeries.legend_line_width}"/>`;
  timeBody += `<text x="${predictedLegendX + timeSeries.legend_label_gap}" y="${legendY + timeSeries.legend_text_baseline_offset}">${xmlEscape(timeSeries.predicted_label)}</text>`;
  timeBody += `<text x="${timeLeft}" y="${timeBottom + timeSeries.date_label_bottom_padding}">${timeSeries.start_label} ${xmlEscape(rows[0][config.dataset.date_column])}</text>`;
  timeBody += `<text x="${timeRight}" y="${timeBottom + timeSeries.date_label_bottom_padding}" text-anchor="end">${timeSeries.end_label} ${xmlEscape(rows.at(-1)[config.dataset.date_column])}</text>`;
  fs.writeFileSync(
    path.join(outputDirectory, settings.time_series_filename),
    svgDocument(timeSeries.title, timeBody, figure),
    "utf-8",
  );
}

function main() {
  const args = getArgs(process.argv.slice(2), ["work_space"]);
  const workspace = path.resolve(args.work_space);
  const configPath = args.config_path ?? "config/workflow_4_model_training/config.json";
  const config = loadWorkflowConfig(workspace, configPath, {
    data_path: args.data_path,
    output_path: args.output_path,
  });
  const figure = getFigureSettings(config, "figures");
  const outputRoot = resolvePath(workspace, config.output_path);
  const outputDirectory = path.join(outputRoot, config.outputs.directory);
  const predictionsPath = path.join(outputDirectory, config.outputs.predictions_filename);
  const rows = readCsv(predictionsPath);
  predictionFigures(rows, outputDirectory, config, figure);
  const metricsPath = path.join(outputDirectory, config.outputs.metrics_filename);
  const metrics = JSON.parse(fs.readFileSync(metricsPath, "utf-8"));
  metrics.artifacts = [
    ...new Set([
      ...(metrics.artifacts ?? []),
      path.join(outputDirectory, config.figures.scatter_filename),
      path.join(outputDirectory, config.figures.time_series_filename),
    ]),
  ];
  fs.writeFileSync(metricsPath, `${JSON.stringify(metrics, null, 2)}\n`, "utf-8");
  console.log(`Saved two prediction SVG figures under ${outputDirectory}`);
}

try {
  main();
} catch (error) {
  console.error(`Workflow 4 figure generation failed: ${error.message}`);
  process.exitCode = 1;
}
