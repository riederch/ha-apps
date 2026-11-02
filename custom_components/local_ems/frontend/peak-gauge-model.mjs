// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Compact, vendor-neutral 15-minute demand gauge model.
 * Reads the already-computed HA Local EMS peak-quality sensor attributes.
 * Never estimates energy from instantaneous power or relies on wall-clock
 * time for the E/t average.
 */
export function nonnegative(value) {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) && n >= 0 ? n : null;
}

export function makePeakGaugeModel(attributes) {
  const raw = attributes?.ems_peak_summary ?? {};
  const quality = String(raw.quality ?? "unknown");
  const valid = raw.valid === true;
  const avg = valid ? nonnegative(raw.quarter_average_kw) : null;
  const forecast = valid ? nonnegative(raw.forecast_kw) : null;
  const committed = valid ? nonnegative(raw.committed_kw) : null;
  const energy = valid ? nonnegative(raw.energy_kwh) : null;
  const limit = nonnegative(raw.limit_kw);
  const warning = nonnegative(raw.warning_kw);
  const remaining = nonnegative(raw.quarter_remaining_seconds);

  const thresholdsValid = limit !== null && limit > 0 &&
    warning !== null && warning > 0 && warning < limit;
  const scaleMax = thresholdsValid ? limit * 1.2 : 12;
  const reference = forecast ?? avg;
  let severity = "unknown";
  if (!valid) severity = "invalid";
  else if (reference !== null && thresholdsValid) {
    severity = reference >= limit ? "limit" :
      reference >= warning ? "warning" : "ok";
  }
  return {
    valid, quality,
    averageKw: avg,
    forecastKw: forecast,
    committedKw: committed,
    energyKwh: energy,
    warningKw: thresholdsValid ? warning : null,
    limitKw: thresholdsValid ? limit : null,
    scaleMax,
    remainingSeconds: remaining,
    quarterStart: raw.quarter_start || null,
    quarterEnd: raw.quarter_end || null,
    severity,
    // The needle never exceeds the graphic. The text retains the true value.
    needleFraction: avg === null ? null : Math.min(1, avg / scaleMax),
  };
}

export function formatKw(value, locale = "de-AT") {
  if (value === null || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value) + " kW";
}

export function formatRemaining(seconds, locale = "de-AT") {
  if (seconds === null || !Number.isFinite(seconds)) return "—";
  const rounded = Math.max(0, Math.ceil(seconds));
  const m = Math.floor(rounded / 60);
  const s = rounded % 60;
  // Prefer a stable MM:SS rendering regardless of the browser's locale.
  return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
}

function polar(fraction, radius) {
  const theta = Math.PI * (1 - fraction);
  return {
    x: 160 + radius * Math.cos(theta),
    y: 150 - radius * Math.sin(theta),
  };
}

export function arcPath(startValue, endValue, maxValue) {
  if (!Number.isFinite(maxValue) || maxValue <= 0) return "";
  const start = Math.max(0, Math.min(1, startValue / maxValue));
  const end = Math.max(0, Math.min(1, endValue / maxValue));
  if (end - start <= 0.000001) return "";
  const p1 = polar(start, 112);
  const p2 = polar(end, 112);
  return [
    "M", p1.x.toFixed(2), p1.y.toFixed(2),
    "A", 112, 112, 0, end - start > 0.5 ? 1 : 0, 1,
    p2.x.toFixed(2), p2.y.toFixed(2),
  ].join(" ");
}

export function needleTip(fraction) {
  if (fraction === null || !Number.isFinite(fraction)) return null;
  return polar(Math.max(0, Math.min(1, fraction)), 87);
}
