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

import {
  energyPowerMappings,
  powerFromMappings,
  primaryEntity,
  percentageFromMappings,
} from "./energy-preferences.mjs";

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

/**
 * Conservative *minimum* allocations for direct energy-flow links.
 * A power-flow display cannot identify the physical source of charging or
 * export from bus totals alone. So a link animates only if part of the transfer
 * is forced by conservation of energy, even under the most conservative
 * allocation of the competing source.
 *
 * grid -> battery: charging beyond all available PV must use imported power.
 * solar -> grid: export beyond all battery discharge must involve PV.
 * solar -> battery: charging beyond the available grid import must use PV.
 * A dedicated PV -> battery power sensor does not exist, so this is only a
 * lower bound, not an exact physical attribution.
 * Direct-route inference requires valid PV, grid and battery power values
 * and an available grid. During EPS, a generator may be an unmetered source,
 * so the conservative estimate is zero rather than inventing an origin.
 * The result is not a per-path meter and must never be used for actuation.
 */
export function inferDirectFlows({ gridW, solarW, batteryW, gridState, gridContact }) {
  const gridUnavailable = gridState === "eps" || gridState === "grid_lost" ||
    gridContact === false;
  const complete = [gridW, solarW, batteryW].every(Number.isFinite) &&
    solarW >= 0;
  if (gridUnavailable || !complete) {
    return { gridToBatteryW: 0, solarToGridW: 0, solarToBatteryW: 0 };
  }
  const importW = Math.max(0, gridW);
  const exportW = Math.max(0, -gridW);
  const chargeW = Math.max(0, -batteryW);
  const dischargeW = Math.max(0, batteryW);
  return {
    gridToBatteryW: Math.min(importW, Math.max(0, chargeW - solarW)),
    solarToGridW: Math.min(solarW, Math.max(0, exportW - dischargeW)),
    solarToBatteryW: Math.min(solarW, Math.max(0, chargeW - importW)),
  };
}

export function buildFlowModel(states, attributes, preferences = null, options = {}) {
  const attrs = attributes ?? {};
  const explicit = attrs.source_entities ?? {};
  const mappings = energyPowerMappings(preferences);
  // Energy Dashboard is authoritative by default, unless deliberately
  // overridden by source_mode: ems in this card's config.
  const preferEnergy = options.source_mode !== "ems";
  const sourceEntities = {};

  function power(role, mappedName, invert = false) {
    const mappingList = mappings[role];
    const entity = explicit[mappedName];
    const hasEnergy = mappingList.length > 0;
    const useEnergy = (preferEnergy && hasEnergy) || (!entity && hasEnergy);
    if (useEnergy) {
      sourceEntities[role] = primaryEntity(mappingList);
      return powerFromMappings(
        mappingList,
        (id) => toWatts(states, id),
        (id) => !!states?.[id],
      );
    }
    sourceEntities[role] = entity || null;
    return toWatts(states, entity, invert);
  }

  const gridW = power("grid", "grid", !!attrs.invert_grid_power);
  const pvValue = power("solar", "solar");
  const solarW = pvValue === null || pvValue < 0 ? null : pvValue;
  const batteryW = power("battery", "battery", !!attrs.invert_battery_power);
  const houseValue = power("home", "home");
  const houseW = houseValue === null || houseValue < 0 ? null : houseValue;
  const hasEnergySoc = mappings.soc.length > 0;
  const useEnergySoc = (preferEnergy && hasEnergySoc) ||
    (!explicit.battery_soc && hasEnergySoc);
  const batterySoc = useEnergySoc
    ? percentageFromMappings(mappings.soc, (id) => toPercent(states, id))
    : toPercent(states, explicit.battery_soc);
  sourceEntities.battery_soc = useEnergySoc
    ? mappings.soc[0]?.entity || null : explicit.battery_soc || null;
  const frequency = toHertz(states, explicit.grid_frequency);
  const inverterState = rawState(states, explicit.inverter_state);
  sourceEntities.grid_frequency = explicit.grid_frequency || null;
  sourceEntities.grid_contact = explicit.grid_contact || null;
  sourceEntities.inverter_state = explicit.inverter_state || null;

  let gridContact = null;
  const contactRaw = rawState(states, explicit.grid_contact);
  if (contactRaw === "on" || contactRaw === "off") {
    gridContact = (contactRaw === "on") === !!attrs.grid_contact_on_is_present;
  }

  const safety = String(attrs.grid_state || "unconfigured");
  const status = [
    "on_grid", "eps", "grid_lost", "suspect", "recovering",
    "unknown", "unconfigured",
  ].includes(safety) ? safety : "unknown";

  const isEnergyMapped = ["grid", "solar", "home", "battery"].some(
    (key) => mappings[key].length > 0
  );

  return {
    sources: sourceEntities, gridW, solarW, batteryW, houseW,
    batterySoc, frequency, inverterState, gridContact,
    directFlows: inferDirectFlows({
      gridW, solarW, batteryW, gridState: status, gridContact,
    }),
    gridState: status,
    safetyReason: attrs.grid_safety_reason || null,
    controlAllowed: attrs.control_allowed === true,
    sourcesConfigured: !!(
      isEnergyMapped ||
      ["grid", "solar", "home", "battery"].some((key) => explicit[key])
    ),
    sourceMode: preferEnergy && isEnergyMapped ? "energy" : "ems",
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
