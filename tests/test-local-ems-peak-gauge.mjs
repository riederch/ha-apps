// SPDX-License-Identifier: GPL-3.0-or-later
import test from "node:test";
import assert from "node:assert/strict";
import {
  makePeakGaugeModel, formatKw, formatRemaining, arcPath, needleTip,
} from "../custom_components/local_ems/frontend/peak-gauge-model.mjs";

const sample = {
  ems_peak_gauge_version: 1,
  ems_peak_summary: {
    valid: true,
    quality: "ok",
    quarter_average_kw: 8,
    forecast_kw: 8.7,
    committed_kw: 3.2,
    energy_kwh: 0.8,
    warning_kw: 9,
    limit_kw: 10,
    quarter_start: "2026-11-02T17:45:00+00:00",
    quarter_end: "2026-11-02T18:00:00+00:00",
    quarter_remaining_seconds: 540,
  },
};

test("actual elapsed-quarter mean and forecast stay separate", () => {
  const result = makePeakGaugeModel(sample);
  assert.equal(result.averageKw, 8);
  assert.equal(result.forecastKw, 8.7);
  assert.equal(result.committedKw, 3.2);
  assert.equal(result.energyKwh, 0.8);
  assert.equal(result.warningKw, 9);
  assert.equal(result.limitKw, 10);
  assert.equal(result.scaleMax, 12);
  assert.equal(result.severity, "ok");
  assert.equal(result.needleFraction, 2 / 3);
  assert.equal(result.remainingSeconds, 540);
});

test("gauge severity uses forecast even if current average is low", () => {
  const warning = makePeakGaugeModel({
    ems_peak_summary: { ...sample.ems_peak_summary, forecast_kw: 9.5 },
  });
  assert.equal(warning.severity, "warning");
  const limit = makePeakGaugeModel({
    ems_peak_summary: { ...sample.ems_peak_summary, forecast_kw: 10.8 },
  });
  assert.equal(limit.severity, "limit");
  assert.equal(limit.averageKw, 8);
});

test("stale meter never shows a false zero or previous actual average", () => {
  const stale = makePeakGaugeModel({
    ems_peak_summary: { ...sample.ems_peak_summary, valid: false,
      quality: "stale", quarter_average_kw: 8, forecast_kw: 8.7 },
  });
  assert.equal(stale.averageKw, null);
  assert.equal(stale.forecastKw, null);
  assert.equal(stale.severity, "invalid");
  assert.equal(stale.needleFraction, null);
  assert.equal(formatKw(stale.averageKw), "—");
});

test("zero elapsed duration is undefined, not fabricated zero", () => {
  const first = makePeakGaugeModel({
    ems_peak_summary: {
      ...sample.ems_peak_summary, quarter_average_kw: null,
      energy_kwh: 0, quarter_remaining_seconds: 900,
    },
  });
  assert.equal(first.averageKw, null);
  assert.equal(first.needleFraction, null);
});

test("actual 0kW after meter reports is a valid needle at zero", () => {
  const zero = makePeakGaugeModel({
    ems_peak_summary: {
      ...sample.ems_peak_summary, quarter_average_kw: 0, forecast_kw: 0,
    },
  });
  assert.equal(zero.averageKw, 0);
  assert.equal(zero.needleFraction, 0);
  assert.equal(zero.severity, "ok");
});

test("over-limit value remains truthful even when pointer reaches scale end", () => {
  const result = makePeakGaugeModel({
    ems_peak_summary: {
      ...sample.ems_peak_summary, quarter_average_kw: 15.2, forecast_kw: 16,
    },
  });
  assert.equal(result.averageKw, 15.2);
  assert.equal(result.scaleMax, 12);
  assert.equal(result.needleFraction, 1);
  assert.equal(result.severity, "limit");
  assert.equal(formatKw(result.averageKw, "de-AT"), "15,2 kW");
});

test("invalid threshold configuration cannot yield a false green status", () => {
  const result = makePeakGaugeModel({
    ems_peak_summary: {
      ...sample.ems_peak_summary, warning_kw: 12, limit_kw: 10,
    },
  });
  assert.equal(result.warningKw, null);
  assert.equal(result.limitKw, null);
  assert.equal(result.severity, "unknown");
});

test("non-numeric and missing readings remain missing", () => {
  const m = makePeakGaugeModel({
    ems_peak_summary: {
      ...sample.ems_peak_summary, quarter_average_kw: "unavailable",
      forecast_kw: "NaN", committed_kw: Infinity,
    },
  });
  assert.equal(m.averageKw, null);
  assert.equal(m.forecastKw, null);
  assert.equal(m.committedKw, null);
  assert.equal(m.severity, "unknown");
});

test("semicircular arc segments have non-overlapping bounds", () => {
  const green = arcPath(0, 9, 12);
  const yellow = arcPath(9, 10, 12);
  const red = arcPath(10, 12, 12);
  assert.match(green, /^M /);
  assert.match(yellow, /^M /);
  assert.match(red, /^M /);
  assert.equal(arcPath(1, 1, 12), "");
  assert.equal(arcPath(0, 1, 0), "");
  const zero = needleTip(0);
  const max = needleTip(1);
  assert.ok(zero.x < 160);
  assert.ok(max.x > 160);
  assert.equal(needleTip(null), null);
});

test("locale and time labels are legible", () => {
  assert.equal(formatRemaining(540), "09:00");
  assert.equal(formatRemaining(900), "15:00");
  assert.equal(formatRemaining(null), "—");
  assert.equal(formatKw(8.05, "de-AT"), "8,1 kW");
});

test("the gauge card ships in the same JS resource as Local EMS Flow", async () => {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { resolve } = await import("node:path");
  const directory = fileURLToPath(new URL(".", import.meta.url));
  const path = resolve(directory,
    "../custom_components/local_ems/frontend/local-ems-flow-card.mjs");
  const code = readFileSync(path, "utf8");
  assert.match(code, /import "\.\/local-ems-peak-gauge-card\.mjs"/);
  const resource = readFileSync(resolve(directory,
    "../custom_components/local_ems/frontend/local-ems-peak-gauge-card.mjs"),
  "utf8");
  assert.match(resource, /local-ems-peak-gauge-card/);
  assert.match(resource, /columns: 6/);
  assert.match(resource, /ems_peak_gauge_version/);
});

test("backend has an always-available gauge anchor even during failures", async () => {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { resolve } = await import("node:path");
  const directory = fileURLToPath(new URL(".", import.meta.url));
  const code = readFileSync(resolve(directory,
    "../custom_components/local_ems/sensor.py"), "utf8");
  assert.match(code, /if self\.key == "quality":/);
  assert.match(code, /"ems_peak_gauge_version"/);
  assert.match(code, /"ems_peak_summary"/);
});
