// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Read-only adapter for Home Assistant Energy dashboard preferences.
 * No Home Assistant-specific dependency is imported in the bundled card.
 * Supports one or multiple grid / solar / battery / home sources and all
 * documented Energy power_config variants.
 */

const ROLES = new Set(["grid", "solar", "home", "battery"]);

function nonempty(value) {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function mappingFor(source) {
  const p = source.power_config || {};
  const helper = nonempty(source.stat_rate);
  const direct = nonempty(p.stat_rate);
  const inverted = nonempty(p.stat_rate_inverted);
  const from = nonempty(p.stat_rate_from);
  const to = nonempty(p.stat_rate_to);
  if (from || to) {
    // The HA-generated helper is preferable; split sensors are a fallback.
    return { helper, from, to, kind: "split" };
  }
  if (inverted) {
    return { helper, inverted, kind: "inverted" };
  }
  if (direct || helper) {
    return { direct: direct || helper, kind: "direct" };
  }
  return null;
}

export function energyPowerMappings(prefs) {
  const result = { grid: [], solar: [], home: [], battery: [], soc: [] };
  const entries = Array.isArray(prefs?.energy_sources) ? prefs.energy_sources : [];
  for (const source of entries) {
    if (!source || !ROLES.has(source.type)) continue;
    const mapping = mappingFor(source);
    if (mapping) result[source.type].push(mapping);
    if (source.type === "battery") {
      const soc = nonempty(source.stat_soc);
      if (soc) {
        const capacity = Number(source.capacity);
        result.soc.push({
          entity: soc,
          weight: Number.isFinite(capacity) && capacity > 0 ? capacity : 1,
        });
      }
    }
  }
  return result;
}

export function primaryEntity(mappings) {
  if (!Array.isArray(mappings) || !mappings.length) return null;
  const first = mappings[0];
  return first.helper || first.direct || first.inverted || first.from || first.to || null;
}

/**
 * The caller supplies a watts reader. A missing required sensor is unknown,
 * never zero. A generated helper is preferred when present; if it is not
 * in hass.states, split and inverse settings are evaluated independently.
 */
export function powerFromMappings(mappings, readWatts, isPresent) {
  if (!Array.isArray(mappings) || mappings.length === 0) return null;
  let sum = 0;
  for (const m of mappings) {
    let value = null;
    if (m.helper && isPresent(m.helper)) {
      value = readWatts(m.helper);
    } else if (m.kind === "split") {
      if (!m.from && !m.to) return null;
      const from = m.from ? readWatts(m.from) : 0;
      const to = m.to ? readWatts(m.to) : 0;
      if (from === null || to === null || from < 0 || to < 0) return null;
      value = from - to;
    } else if (m.kind === "inverted") {
      const source = readWatts(m.inverted);
      value = source === null ? null : -source;
    } else {
      value = readWatts(m.direct);
    }
    if (value === null || !Number.isFinite(value)) return null;
    sum += value;
  }
  return sum;
}

export function percentageFromMappings(mappings, readPercent) {
  if (!Array.isArray(mappings) || !mappings.length) return null;
  let total = 0;
  let weight = 0;
  for (const item of mappings) {
    const value = readPercent(item.entity);
    if (value === null) return null;
    total += value * item.weight;
    weight += item.weight;
  }
  return weight ? total / weight : null;
}
