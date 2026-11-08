// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Bridges Local EMS/HA Energy Dashboard sources to the unmodified upstream
 * Power Flow Card Plus energy-routing solver and renderer.
 *
 * This is a UI adapter: synthetic sensor states are never registered in HA,
 * never recorded, and never used for control, load shedding or EPS safety.
 */
import { buildFlowModel } from "./flow-model.mjs";

export const VIRTUAL = Object.freeze({
  grid: "sensor.local_ems_ui_pfcp_grid",
  solar: "sensor.local_ems_ui_pfcp_solar",
  battery: "sensor.local_ems_ui_pfcp_battery",
  home: "sensor.local_ems_ui_pfcp_home",
  soc: "sensor.local_ems_ui_pfcp_soc",
  outage: "binary_sensor.local_ems_ui_pfcp_outage",
});

export const UPSTREAM_ELEMENT = "local-ems-pfcp-upstream";
export const LOCAL_CARD_TYPE = "custom:local-ems-flow-card";
export const UPSTREAM_CARD_TYPE = "custom:local-ems-pfcp-upstream";

function virtualState(id, value, unit, source = null) {
  const available = Number.isFinite(value);
  return {
    entity_id: id,
    state: available ? String(value) : "unavailable",
    attributes: {
      friendly_name: id.replace("sensor.local_ems_ui_pfcp_", "Local EMS "),
      unit_of_measurement: unit,
      ...(unit === "W" ? { device_class: "power" } : {}),
      ...(unit === "%" ? { device_class: "battery" } : {}),
    },
    last_changed: source?.last_changed ?? "",
    last_updated: source?.last_updated ?? "",
    context: source?.context ?? { id: "", parent_id: null, user_id: null },
  };
}

function originalOptions(config) {
  // Forward the original card's complete set of advanced options rather than
  // reimplementing its rendering/editing/flow algorithm in Local EMS.
  const { type, entity, source_mode, use_measured_home, entities, ...rest } = config;
  return rest;
}

/** Pure conversion of existing HA source mapping and EMS safety metadata. */
export function buildUpstreamBridge(hass, metadataAttributes, energyPreferences, localConfig = {}) {
  const config = localConfig ?? {};
  if (config.entities) {
    // Full upstream YAML is supported as-is, with only the Lovelace type
    // rewritten to point at the separately namespaced vendored element.
    return {
      config: {
        ...originalOptions(config),
        entities: config.entities,
        type: UPSTREAM_CARD_TYPE,
      },
      hass,
      sourceMap: {},
      model: null,
      sourceMode: "manual",
    };
  }

  const model = buildFlowModel(
    hass?.states ?? {}, metadataAttributes ?? {}, energyPreferences, config
  );
  const sourceMap = {};
  const states = {};
  const entities = {};
  const sources = model.sources ?? {};

  const setPower = (role, pfcpValue, originalId) => {
    if (!originalId) return;
    const id = VIRTUAL[role];
    states[id] = virtualState(id, pfcpValue, "W", hass?.states?.[originalId]);
    sourceMap[id] = originalId;
    entities[role] = { entity: id };
  };

  // Power Flow Card Plus native signs: Grid +import/-export and Battery
  // +charge/-discharge. Local EMS uses the opposite battery convention.
  const outage = model.gridState === "eps" ||
    model.gridState === "grid_lost" || model.gridContact === false;
  setPower("grid", outage ? 0 : model.gridW, sources.grid);
  setPower("solar", model.solarW, sources.solar);
  setPower("battery", model.batteryW === null ? null : -model.batteryW, sources.battery);

  if (entities.battery) {
    states[VIRTUAL.soc] = virtualState(
      VIRTUAL.soc, model.batterySoc, "%", hass?.states?.[sources.battery_soc]
    );
    if (sources.battery_soc) sourceMap[VIRTUAL.soc] = sources.battery_soc;
    entities.battery.state_of_charge = VIRTUAL.soc;
  }

  if (entities.grid) {
    states[VIRTUAL.outage] = {
      entity_id: VIRTUAL.outage,
      state: outage ? "on" : "off",
      attributes: { friendly_name: "Local EMS Grid Power Outage" },
      last_changed: "", last_updated: "",
      context: { id: "", parent_id: null, user_id: null },
    };
    entities.grid.power_outage = {
      entity: VIRTUAL.outage, state_alert: "on",
    };
  }

  // PFCP defaults to the original, source-derived house-flow calculation.
  // Optional measured house override is explicit and never silently inferred.
  if (config.use_measured_home === true && sources.home) {
    setPower("home", model.houseW, sources.home);
    entities.home.override_state = true;
  }

  if (!entities.grid && !entities.solar && !entities.battery) return null;

  const originalConfig = {
    ...originalOptions(config),
    type: UPSTREAM_CARD_TYPE,
    entities,
  };
  if (originalConfig.title === undefined) originalConfig.title = "Energiefluss";

  // The synthetic display sensors are only visible to this card, not HA.
  // Inheriting from hass keeps the WebSocket, localization and formatter
  // methods/properties of the normal Home Assistant frontend object intact.
  const displayHass = Object.create(hass);
  displayHass.states = { ...hass.states, ...states };

  return { config: originalConfig, hass: displayHass, sourceMap, model,
    sourceMode: model.sourceMode };
}
