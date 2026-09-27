/** Shared CSV, path, and SVG helpers for workflow figure generation. */

import fs from "node:fs";
import path from "node:path";

const FONT = "Times New Roman, serif";

export function getArgs(argv, requiredOptions = ["work_space", "config_path"]) {
  const args = {};
  const supported = ["--work_space", "--config_path", "--data_path", "--output_path"];
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key.startsWith("--") || value === undefined || value.startsWith("--")) {
      throw new Error(`Expected a named option and value near: ${key ?? "<end>"}`);
    }
    if (!supported.includes(key)) throw new Error(`Unsupported argument: ${key}`);
    args[key.slice(2)] = value;
    index += 1;
  }
  for (const key of requiredOptions) {
    if (!args[key]) throw new Error(`Missing required option --${key}`);
  }
  return args;
}

export function resolvePath(workspace, value) {
  return path.resolve(path.isAbsolute(value) ? value : path.join(workspace, value));
}

export function loadWorkflowConfig(workspace, configPath, overrides = {}) {
  const resolvedPath = resolvePath(workspace, configPath);
  const config = JSON.parse(fs.readFileSync(resolvedPath, "utf-8"));
  if (config === null || Array.isArray(config) || typeof config !== "object") {
    throw new Error(`Workflow config must contain a JSON object: ${resolvedPath}`);
  }
  for (const [key, value] of Object.entries(overrides)) {
    if (value !== undefined && value !== null) config[key] = value;
  }
  return config;
}

export function getFigureSettings(config, section) {
  const figure = section === "visualization" ? config.visualization?.figure : config.figures?.figure;
  if (!figure || !Number.isFinite(figure.width) || !Number.isFinite(figure.height)) {
    throw new Error(`Config section ${section} must define figure width and height.`);
  }
  if (!figure.colors || typeof figure.colors !== "object") {
    throw new Error(`Config section ${section} must define figure colors.`);
  }
  return figure;
}

export function parseCsv(text) {
  const records = [];
  let record = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        field += character;
      }
    } else if (character === '"' && field.length === 0) {
      quoted = true;
    } else if (character === ",") {
      record.push(field);
      field = "";
    } else if (character === "\n") {
      record.push(field.replace(/\r$/, ""));
      records.push(record);
      record = [];
      field = "";
    } else {
      field += character;
    }
  }
  if (field.length > 0 || record.length > 0) {
    record.push(field.replace(/\r$/, ""));
    records.push(record);
  }
  if (records.length === 0) throw new Error("CSV file is empty.");
  const headers = records.shift().map((header) => header.replace(/^\uFEFF/, ""));
  return records
    .filter((row) => row.some((value) => value.length > 0))
    .map((row) => Object.fromEntries(headers.map((header, index) => [header, row[index] ?? ""])));
}

export function readCsv(filePath) {
  return parseCsv(fs.readFileSync(filePath, "utf-8"));
}

export function number(value, fieldName) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    throw new Error(`Column ${fieldName} contains a non-numeric or non-finite value: ${value}`);
  }
  return parsed;
}

export function timestampParts(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):\d{2}:\d{2}$/.exec(value);
  if (!match) throw new Error(`Invalid date_time value: ${value}`);
  const [, year, month, day, hour] = match;
  const weekday = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day))).getUTCDay();
  return { hour: Number(hour), weekday: (weekday + 6) % 7 };
}

export function xmlEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export function svgDocument(title, body, figure) {
  const { width, height, colors } = figure;
  const fontFamily = figure.font_family ?? FONT;
  const fontSize = figure.font_size ?? 10;
  const physicalWidth = figure.width_in ?? width / 120;
  const physicalHeight = figure.height_in ?? height / 120;
  const gridWidth = figure.grid_line_width ?? 1;
  const axisWidth = figure.axis_line_width ?? 1.4;
  const tickWidth = figure.tick_line_width ?? 1;
  return `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="${physicalWidth}in" height="${physicalHeight}in" viewBox="0 0 ${width} ${height}" role="img" aria-label="${xmlEscape(title)}">\n<style>text{font-family:${fontFamily};font-size:${fontSize}pt;fill:${colors.ink}}.title{font-weight:bold}.grid{stroke:${colors.grid};stroke-width:${gridWidth}}.axis{stroke:${colors.ink};stroke-width:${axisWidth}}.tick{stroke:${colors.ink};stroke-width:${tickWidth}}.label{text-anchor:middle}.small{text-anchor:end}</style>\n<text class="title label" x="${width / 2}" y="${figure.title_y ?? 35}">${xmlEscape(title)}</text>\n${body}\n</svg>\n`;
}

export function niceMaximum(value, intervals = 5) {
  if (value <= 0) return 1;
  const rawStep = value / intervals;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  const step = (normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10) * magnitude;
  return Math.ceil(value / step) * step;
}

export function formatNumber(value) {
  return Math.round(value).toLocaleString("en-US");
}

export function line(x1, y1, x2, y2, className = "axis", extra = "") {
  return `<line class="${className}" x1="${x1.toFixed(2)}" y1="${y1.toFixed(2)}" x2="${x2.toFixed(2)}" y2="${y2.toFixed(2)}" ${extra}/>`;
}

export function yAxis({
  left,
  top,
  bottom,
  maximum,
  intervals,
  xLabel,
  yLabel,
  rightPadding,
  xLabelBottomPadding,
  yLabelX,
  tickLabelGap,
  tickTextBaselineOffset,
  figure,
}) {
  const { width, height } = figure;
  const right = width - rightPadding;
  let svg = "";
  for (let index = 0; index <= intervals; index += 1) {
    const value = (maximum * index) / intervals;
    const y = bottom - ((bottom - top) * index) / intervals;
    svg += line(left, y, right, y, "grid");
    svg += `<text class="small" x="${left - tickLabelGap}" y="${y + tickTextBaselineOffset}">${formatNumber(value)}</text>`;
  }
  svg += line(left, top, left, bottom);
  svg += line(left, bottom, right, bottom);
  svg += `<text class="label" x="${(left + right) / 2}" y="${height - xLabelBottomPadding}">${xmlEscape(xLabel)}</text>`;
  svg += `<text class="label" transform="translate(${yLabelX} ${(top + bottom) / 2}) rotate(-90)">${xmlEscape(yLabel)}</text>`;
  return svg;
}
