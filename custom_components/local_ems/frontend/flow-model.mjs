// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Vendor-neutral power-flow model for Local EMS.
 *
 * Source entity IDs and polarity are supplied by the EMS integration.
 * The browser reads HA live state; it never maintains a second archive.
 *
 * Sign conventions:
 *  - Grid: positive = import, negative = export.
 *  - Battery: positive = discharge, negative = charging.
 *  - PV and house load: nonnegative.
 */

const UNKNOWN = new Set(["unknown", "unavailable", "none", ""]);

function numericState(states, entityId, allowedUnits) {
  if (!entityId || !states || !states[entityId]) return null;
  const record = states[entityId];
  const raw = String(record.state ?? "").trim().toLowerCase();
  if (UNKNOWN.has(raw)) return null;
  const unit = record.attributes?.unit_of_measurement;
  if (!allowedUnits.includes(unit)) return null;
  const number = Number(record.state);
  return Number.isFinite(number) ? { value: number, unit } : null;
}

export function toWatts(states, entityId, invert = false) {
  const val = numericState(states, entityId, ["W", "kW"]);
  if (!val) return null;
  return (invert ? -1 : 1) * val.value * (val.unit === "kW" ? 1000 : 1);
}

export function toPercent(states, entityId) {
  const val = numericState(states, entityId, ["%"]);
  return val && val.value >= 0 && val.value <= 100 ? val.value : null;
}

export function toHertz(states, entityId) {
  const val = numericState(states, entityId, ["Hz"]);
  return val && val.value >= 0 ? val.value : null;
}

function rawState(states, entityId) {
  if (!entityId || !states?.[entityId]) return null;
  const raw = String(states[entityId].state ?? "").trim();
  return UNKNOWN.has(raw.toLowerCase()) ? null : raw;
}

export function buildFlowModel(states, attributes) {
  const attrs = attributes ?? {};
  const sources = attrs.source_entities ?? {};

  const gridW = toWatts(states, sources.grid, !!attrs.invert_grid_power);
  const pvValue = toWatts(states, sources.solar);
  const solarW = pvValue === null ? null : Math.max(0, pvValue);
  const batteryW = toWatts(states, sources.battery, !!attrs.invert_battery_power);
  const houseValue = toWatts(states, sources.home);
  const houseW = houseValue === null ? null : Math.max(0, houseValue);
  const batterySoc = toPercent(states, sources.battery_soc);
  const frequency = toHertz(states, sources.grid_frequency);
  const inverterState = rawState(states, sources.inverter_state);

  let gridContact = null;
  const contactRaw = rawState(states, sources.grid_contact);
  if (contactRaw === "on" || contactRaw === "off") {
    gridContact = (contactRaw === "on") === !!attrs.grid_contact_on_is_present;
  }

  const safety = String(attrs.grid_state || "unconfigured");
  const status = [
    "on_grid", "eps", "grid_lost", "suspect", "recovering",
    "unknown", "unconfigured",
  ].includes(safety) ? safety : "unknown";

  return {
    sources, gridW, solarW, batteryW, houseW,
    batterySoc, frequency, inverterState, gridContact,
    gridState: status,
    safetyReason: attrs.grid_safety_reason || null,
    controlAllowed: attrs.control_allowed === true,
    directions: {
      grid: gridW === null ? null : (
        Math.abs(gridW) < 5 ? "idle" : gridW > 0 ? "import" : "export"
      ),
      battery: batteryW === null ? null : (
        Math.abs(batteryW) < 5 ? "idle" : batteryW > 0 ? "discharge" : "charge"
      ),
      solar: solarW === null ? null : (solarW >= 5 ? "production" : "idle"),
    },
  };
}

export function formatWatts(watts, locale = "de-AT") {
  if (watts === null || !Number.isFinite(watts)) return "—";
  const magnitude = Math.abs(watts);
  if (magnitude >= 1000) {
    return new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(magnitude / 1000) + " kW";
  }
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(magnitude) + " W";
}
