// SPDX-License-Identifier: GPL-3.0-or-later
import test from "node:test";
import assert from "node:assert/strict";

import {
  toWatts, toPercent, toHertz, buildFlowModel, inferDirectFlows, formatWatts,
} from "../custom_components/local_ems/frontend/flow-model.mjs";

import {
  buildUpstreamBridge, VIRTUAL, UPSTREAM_ELEMENT, UPSTREAM_CARD_TYPE,
} from "../custom_components/local_ems/frontend/pfcp-adapter.mjs";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const mk = (value, unit) => ({
  state: String(value),
  attributes: { unit_of_measurement: unit },
});
const sources = {
  grid: "sensor.kng_p",
  solar: "sensor.pv",
  home: "sensor.house",
  battery: "sensor.battery",
  battery_soc: "sensor.soc",
  grid_frequency: "sensor.frequency",
  grid_contact: "binary_sensor.grid",
  inverter_state: "sensor.inverter_status",
};
const attributes = {
  ems_flow_version: 1,
  source_entities: sources,
  invert_grid_power: false,
  invert_battery_power: true,
  grid_contact_on_is_present: true,
  grid_state: "on_grid",
  grid_safety_reason: "grid_confirmed",
  control_allowed: true,
};

function sample() {
  return {
    "sensor.kng_p": mk(-307, "W"),
    "sensor.pv": mk(8.2, "kW"),
    "sensor.house": mk(3.5, "kW"),
    "sensor.battery": mk(-1400, "W"),
    "sensor.soc": mk(64.5, "%"),
    "sensor.frequency": mk(49.98, "Hz"),
    "binary_sensor.grid": { state: "on", attributes: {} },
    "sensor.inverter_status": { state: "On Grid", attributes: {} },
  };
}

test("normalizes watts, kilowatts and signs", () => {
  const model = buildFlowModel(sample(), attributes);
  assert.equal(model.gridW, -307);
  assert.equal(model.solarW, 8200);
  assert.equal(model.houseW, 3500);
  assert.equal(model.batteryW, 1400);
  assert.equal(model.batterySoc, 64.5);
  assert.equal(model.frequency, 49.98);
  assert.equal(model.gridContact, true);
  assert.equal(model.gridState, "on_grid");
  assert.equal(model.inverterState, "On Grid");
  assert.equal(model.directions.grid, "export");
  assert.equal(model.directions.battery, "discharge");
  assert.equal(model.directions.solar, "production");
});

test("battery mode is the inverse of charge power", () => {
  const states = sample();
  states["sensor.battery"] = mk(1200, "W");
  const model = buildFlowModel(states, attributes);
  assert.equal(model.batteryW, -1200);
  assert.equal(model.directions.battery, "charge");
});

test("positive grid is import and negative grid is export", () => {
  const states = sample();
  states["sensor.kng_p"] = mk(500, "W");
  assert.equal(buildFlowModel(states, attributes).directions.grid, "import");
  states["sensor.kng_p"] = mk(-500, "W");
  assert.equal(buildFlowModel(states, attributes).directions.grid, "export");
});

test("grid inversion supports other manufacturers", () => {
  const states = sample();
  const model = buildFlowModel(states, {
    ...attributes, invert_grid_power: true,
  });
  assert.equal(model.gridW, 307);
  assert.equal(model.directions.grid, "import");
});

test("a missing entity must never be displayed as zero power", () => {
  const states = sample();
  delete states["sensor.pv"];
  const model = buildFlowModel(states, attributes);
  assert.equal(model.solarW, null);
  assert.equal(model.directions.solar, null);
  assert.equal(formatWatts(model.solarW), "—");
});

test("rejects wrong units, unavailable and NaN values", () => {
  const states = {
    "sensor.bad_unit": mk(11, "kWh"),
    "sensor.bad_value": mk("unavailable", "W"),
    "sensor.nan": mk("NaN", "kW"),
  };
  assert.equal(toWatts(states, "sensor.bad_unit"), null);
  assert.equal(toWatts(states, "sensor.bad_value"), null);
  assert.equal(toWatts(states, "sensor.nan"), null);
  assert.equal(toPercent(states, "sensor.bad_unit"), null);
  assert.equal(toHertz(states, "sensor.bad_unit"), null);
});

test("zero readings show no moving direction", () => {
  const states = sample();
  states["sensor.kng_p"] = mk(0, "W");
  states["sensor.battery"] = mk(0, "W");
  states["sensor.pv"] = mk(0, "W");
  const flow = buildFlowModel(states, attributes);
  assert.equal(flow.directions.grid, "idle");
  assert.equal(flow.directions.battery, "idle");
  assert.equal(flow.directions.solar, "idle");
});

test("does not confuse grid outage and unconfigured grid monitoring", () => {
  const states = sample();
  const eps = buildFlowModel(states, { ...attributes, grid_state: "eps" });
  assert.equal(eps.gridState, "eps");
  const unknown = buildFlowModel(states, {
    ...attributes, grid_state: "unconfigured",
  });
  assert.equal(unknown.gridState, "unconfigured");
});

test("home uses the configured measured consumption, never a guessed balance", () => {
  const states = sample();
  states["sensor.house"] = mk("unavailable", "kW");
  const model = buildFlowModel(states, attributes);
  assert.equal(model.houseW, null);
});

test("display formatting works at zero and in kW", () => {
  assert.match(formatWatts(0, "de-AT"), /0 W/);
  assert.match(formatWatts(2340, "de-AT"), /2,3 kW/);
  assert.match(formatWatts(-560, "de-AT"), /560 W/);
});


test("Energy dashboard power data is preferred over EMS manual mapping", () => {
  const energy = { energy_sources: [
    { type: "grid", stat_rate: "sensor.energy_grid" },
    { type: "solar", stat_rate: "sensor.energy_solar" },
    { type: "home", stat_rate: "sensor.energy_home" },
    { type: "battery", stat_rate: "sensor.energy_battery", stat_soc: "sensor.energy_soc" },
  ] };
  const states = {
    ...sample(),
    "sensor.energy_grid": mk(0.5, "kW"),
    "sensor.energy_solar": mk(5, "kW"),
    "sensor.energy_home": mk(2000, "W"),
    "sensor.energy_battery": mk(-700, "W"),
    "sensor.energy_soc": mk(81, "%"),
  };
  const model = buildFlowModel(states, attributes, energy);
  assert.equal(model.sourceMode, "energy");
  assert.equal(model.gridW, 500);
  assert.equal(model.solarW, 5000);
  assert.equal(model.homeW, undefined);
  assert.equal(model.houseW, 2000);
  assert.equal(model.batteryW, -700);
  assert.equal(model.batterySoc, 81);
  assert.equal(model.sources.grid, "sensor.energy_grid");
  assert.equal(model.directions.battery, "charge");
});

test("manual source_mode overrides configured Energy dashboard power", () => {
  const energy = { energy_sources: [
    { type: "grid", stat_rate: "sensor.energy_grid" }
  ] };
  const states = { ...sample(), "sensor.energy_grid": mk(3000, "W") };
  const model = buildFlowModel(states, attributes, energy, { source_mode: "ems" });
  assert.equal(model.gridW, -307);
  assert.equal(model.sourceMode, "ems");
  assert.equal(model.sources.grid, "sensor.kng_p");
});

test("split import/export sensor configuration yields signed grid power", () => {
  const energy = { energy_sources: [
    { type: "grid", stat_rate: "sensor.grid_helper",
      power_config: {
        stat_rate_from: "sensor.import",
        stat_rate_to: "sensor.export",
      },
    },
  ] };
  const states = {
    ...sample(),
    "sensor.import": mk(1.1, "kW"),
    "sensor.export": mk(300, "W"),
  };
  const model = buildFlowModel(states, attributes, energy);
  assert.equal(model.gridW, 800);
  assert.equal(model.directions.grid, "import");
  states["sensor.grid_helper"] = mk(-1500, "W");
  assert.equal(buildFlowModel(states, attributes, energy).gridW, -1500);
});

test("inverted energy dashboard power_config works without generated helper", () => {
  const energy = { energy_sources: [
    { type: "battery", stat_rate: "sensor.battery_helper",
      power_config: { stat_rate_inverted: "sensor.battery_raw" },
      stat_soc: "sensor.energy_soc",
    },
  ] };
  const states = {
    ...sample(),
    "sensor.battery_raw": mk(2, "kW"),
    "sensor.energy_soc": mk(55, "%"),
  };
  const model = buildFlowModel(states, attributes, energy);
  assert.equal(model.batteryW, -2000);
  assert.equal(model.batterySoc, 55);
});

test("multiple photovoltaic sources aggregate; any missing source stays unknown", () => {
  const energy = { energy_sources: [
    { type: "solar", stat_rate: "sensor.solar_1" },
    { type: "solar", stat_rate: "sensor.solar_2" },
  ] };
  const states = {
    ...sample(),
    "sensor.solar_1": mk(1000, "W"),
    "sensor.solar_2": mk(1.5, "kW"),
  };
  assert.equal(buildFlowModel(states, attributes, energy).solarW, 2500);
  delete states["sensor.solar_2"];
  assert.equal(buildFlowModel(states, attributes, energy).solarW, null);
});

test("weighted battery SOC for multiple storages matches configured capacity", () => {
  const energy = { energy_sources: [
    { type: "battery", stat_rate: "sensor.b1", stat_soc: "sensor.soc1", capacity: 10 },
    { type: "battery", stat_rate: "sensor.b2", stat_soc: "sensor.soc2", capacity: 30 },
  ] };
  const states = {
    ...sample(),
    "sensor.b1": mk(500, "W"),
    "sensor.b2": mk(-250, "W"),
    "sensor.soc1": mk(20, "%"),
    "sensor.soc2": mk(80, "%"),
  };
  const model = buildFlowModel(states, attributes, energy);
  assert.equal(model.batteryW, 250);
  assert.equal(model.batterySoc, 65);
});

test("Energy kWh-only preferences never fake instantaneous watts", () => {
  const energy = { energy_sources: [
    { type: "grid", stat_energy_from: "sensor.total_import",
      stat_energy_to: "sensor.total_export" },
    { type: "solar", stat_energy_from: "sensor.total_solar" },
  ] };
  const model = buildFlowModel(sample(), attributes, energy);
  assert.equal(model.gridW, -307);
  assert.equal(model.solarW, 8200);
  assert.equal(model.sourceMode, "ems");
});

test("the card occupies a full 12-column Sections dashboard by default", async () => {
  // The component's layout API is pure; no browser or Home Assistant
  // connection is required to inspect it.
  globalThis.HTMLElement ??= class {};
  const { LocalEMSFlowCard } = await import(
    "../custom_components/local_ems/frontend/local-ems-flow-card.mjs"
  );
  const grid = LocalEMSFlowCard.prototype.getGridOptions();
  assert.deepEqual(grid, {
    columns: 12,
    min_columns: 6,
    max_columns: 12,
    rows: "auto",
  });
});

test("solar-to-grid animates only unavoidable PV export", () => {
  const routes = inferDirectFlows({
    gridW: -1800, solarW: 3300, batteryW: -600,
    gridState: "on_grid", gridContact: true,
  });
  assert.equal(routes.solarToGridW, 1800);
  assert.equal(routes.gridToBatteryW, 0);
  assert.equal(routes.solarToBatteryW, 600);
});

test("grid-to-battery shows unavoidable grid charging when PV is insufficient", () => {
  const routes = inferDirectFlows({
    gridW: 2300, solarW: 500, batteryW: -2000,
    gridState: "on_grid", gridContact: true,
  });
  assert.equal(routes.gridToBatteryW, 1500);
  assert.equal(routes.solarToGridW, 0);
  assert.equal(routes.solarToBatteryW, 0);
});

test("solar can cover battery charging: do not claim grid-to-battery transfer", () => {
  const routes = inferDirectFlows({
    gridW: 1200, solarW: 2800, batteryW: -1000,
    gridState: "on_grid", gridContact: true,
  });
  assert.equal(routes.gridToBatteryW, 0);
  assert.equal(routes.solarToBatteryW, 0);
});

test("battery discharge could cause all export: do not claim solar-to-grid transfer", () => {
  const routes = inferDirectFlows({
    gridW: -1800, solarW: 900, batteryW: 2200,
    gridState: "on_grid", gridContact: true,
  });
  assert.equal(routes.solarToGridW, 0);
});

test("mixed PV/battery grid export only assigns the guaranteed PV share", () => {
  const routes = inferDirectFlows({
    gridW: -3500, solarW: 3000, batteryW: 1800,
    gridState: "on_grid", gridContact: null,
  });
  assert.equal(routes.solarToGridW, 1700);
});

test("PV to battery shows guaranteed PV share beyond maximum grid import", () => {
  const model = inferDirectFlows({
    gridW: 700, solarW: 3200, batteryW: -2400,
    gridState: "on_grid", gridContact: true,
  });
  assert.equal(model.solarToBatteryW, 1700);
  assert.equal(model.gridToBatteryW, 0);
  assert.equal(model.solarToGridW, 0);
});

test("PV to battery during export includes the measured charging power", () => {
  const model = inferDirectFlows({
    gridW: -1400, solarW: 3200, batteryW: -1100,
    gridState: "on_grid", gridContact: true,
  });
  assert.equal(model.solarToBatteryW, 1100);
  assert.equal(model.solarToGridW, 1400);
});

test("PV to battery does not invent charging from PV without production", () => {
  for (const { gridW, solarW, batteryW } of [
    { gridW: 1200, solarW: 0, batteryW: -600 },
    { gridW: -300, solarW: 1600, batteryW: 550 },
    { gridW: 1800, solarW: 200, batteryW: -800 },
  ]) {
    const routes = inferDirectFlows({
      gridW, solarW, batteryW, gridState: "on_grid", gridContact: true,
    });
    assert.equal(routes.solarToBatteryW, 0);
  }
});

test("EPS or a missing grid suppresses all conservatively inferred paths", () => {
  for (const state of ["eps", "grid_lost"]) {
    assert.deepEqual(inferDirectFlows({
      gridW: -2000, solarW: 3000, batteryW: -1000,
      gridState: state, gridContact: null,
    }), { gridToBatteryW: 0, solarToGridW: 0, solarToBatteryW: 0 });
  }
  assert.deepEqual(inferDirectFlows({
    gridW: 2300, solarW: 300, batteryW: -2000,
    gridState: "on_grid", gridContact: false,
  }), { gridToBatteryW: 0, solarToGridW: 0, solarToBatteryW: 0 });
});

test("unknown sensor data never creates fictitious direct power flows", () => {
  for (const missing of ["gridW", "solarW", "batteryW"]) {
    const config = {
      gridW: -2500, solarW: 3000, batteryW: -500,
      gridState: "on_grid", gridContact: true,
    };
    config[missing] = null;
    assert.deepEqual(inferDirectFlows(config), {
      gridToBatteryW: 0, solarToGridW: 0, solarToBatteryW: 0,
    }, missing);
  }
});

test("model includes vendor-neutral inferred direct routes", () => {
  const states = sample();
  states["sensor.kng_p"] = mk(2400, "W");
  states["sensor.pv"] = mk(500, "W");
  states["sensor.battery"] = mk(2000, "W"); // inverter sign, inverted to -2000
  const chargeModel = buildFlowModel(states, attributes);
  assert.equal(chargeModel.directFlows.gridToBatteryW, 1500);
  assert.equal(chargeModel.directFlows.solarToGridW, 0);
  assert.equal(chargeModel.directFlows.solarToBatteryW, 0);
  states["sensor.kng_p"] = mk(-2700, "W");
  states["sensor.pv"] = mk(3500, "W");
  states["sensor.battery"] = mk(300, "W"); // inverted to charging
  const exportModel = buildFlowModel(states, attributes);
  assert.equal(exportModel.directFlows.solarToGridW, 2700);
  assert.equal(exportModel.directFlows.gridToBatteryW, 0);
  assert.equal(exportModel.directFlows.solarToBatteryW, 300);
});



function bridge(config = {}, states = sample(), attrs = attributes, energy = null) {
  return buildUpstreamBridge({ states, language: "de", connection: {} },
    attrs, energy, config);
}

test("PFCP adapter uses original bidirectional power signs, not the local EMS scheme", () => {
  const b = bridge();
  assert.equal(b.config.type, UPSTREAM_CARD_TYPE);
  assert.equal(b.config.entities.grid.entity, VIRTUAL.grid);
  assert.equal(b.config.entities.battery.entity, VIRTUAL.battery);
  assert.equal(b.config.entities.solar.entity, VIRTUAL.solar);
  assert.equal(b.hass.states[VIRTUAL.grid].state, "-307");
  assert.equal(b.hass.states[VIRTUAL.solar].state, "8200");
  // Local EMS + = discharge; original PFCP - = discharge.
  assert.equal(b.hass.states[VIRTUAL.battery].state, "-1400");
  assert.equal(b.hass.states[VIRTUAL.soc].state, "64.5");
  assert.equal(b.hass.states[VIRTUAL.grid].attributes.unit_of_measurement, "W");
  assert.equal(b.config.title, "Energiefluss");
  assert.equal(b.config.entities.home, undefined);
  assert.equal(b.sourceMap[VIRTUAL.grid], "sensor.kng_p");
});

test("PFCP battery charging, grid import and grid export use native directions", () => {
  const states = sample();
  states["sensor.kng_p"] = mk(2500, "W");
  states["sensor.battery"] = mk(1900, "W");
  const b = bridge({}, states);
  assert.equal(b.hass.states[VIRTUAL.grid].state, "2500");
  assert.equal(b.hass.states[VIRTUAL.battery].state, "1900");
  states["sensor.kng_p"] = mk(-800, "W");
  const c = bridge({}, states);
  assert.equal(c.hass.states[VIRTUAL.grid].state, "-800");
});

test("missing PV readings remain unavailable, not artificial zero production", () => {
  const states = sample();
  delete states["sensor.pv"];
  const b = bridge({}, states);
  assert.equal(b.hass.states[VIRTUAL.solar].state, "unavailable");
  assert.equal(b.config.entities.solar.entity, VIRTUAL.solar);
});

test("EPS outage is forwarded to original PFCP power_outage semantics", () => {
  const b = bridge({}, sample(), { ...attributes, grid_state: "eps" });
  assert.equal(b.hass.states[VIRTUAL.grid].state, "0");
  assert.equal(b.hass.states[VIRTUAL.outage].state, "on");
  assert.equal(b.config.entities.grid.power_outage.entity, VIRTUAL.outage);
  assert.equal(b.config.entities.grid.power_outage.state_alert, "on");
  assert.equal(b.hass.states[VIRTUAL.solar].state, "8200");
  const noGrid = bridge({}, sample(), { ...attributes, grid_state: "grid_lost" });
  assert.equal(noGrid.hass.states[VIRTUAL.outage].state, "on");
});

test("unknown grid status never fabricates a power outage", () => {
  const b = bridge({}, sample(), { ...attributes, grid_state: "unconfigured" });
  assert.equal(b.hass.states[VIRTUAL.outage].state, "off");
});

test("real measured home override is opt-in, original computed home is default", () => {
  assert.equal(bridge().config.entities.home, undefined);
  const b = bridge({ use_measured_home: true });
  assert.equal(b.config.entities.home.entity, VIRTUAL.home);
  assert.equal(b.config.entities.home.override_state, true);
  assert.equal(b.hass.states[VIRTUAL.home].state, "3500");
  assert.equal(b.sourceMap[VIRTUAL.home], "sensor.house");
});

test("original PFCP YAML is forwarded without losing upstream layout settings", () => {
  const hass = { states: sample() };
  const b = buildUpstreamBridge(hass, null, null, {
    type: "custom:local-ems-flow-card",
    entities: { battery: { entity: "sensor.battery", invert_state: true } },
    title: "Originalkarte",
    max_expected_power: 17000, flow_rate_model: "new",
  });
  assert.equal(b.config.type, UPSTREAM_CARD_TYPE);
  assert.equal(b.config.entities.battery.invert_state, true);
  assert.equal(b.config.max_expected_power, 17000);
  assert.equal(b.config.title, "Originalkarte");
  assert.equal(b.hass, hass);
  assert.deepEqual(b.sourceMap, {});
});

test("EMS settings override energy dashboard mappings only with source_mode ems", () => {
  const energy = { energy_sources: [
    { type: "grid", stat_rate: "sensor.energy_grid" },
    { type: "battery", stat_rate: "sensor.energy_battery" },
  ] };
  const states = { ...sample(),
    "sensor.energy_grid": mk(3, "kW"),
    "sensor.energy_battery": mk(-500, "W"),
  };
  assert.equal(bridge({}, states, attributes, energy).hass.states[VIRTUAL.grid].state,
    "3000");
  const mapped = bridge({}, states, attributes, energy);
  assert.equal(mapped.hass.states[VIRTUAL.battery].state, "500");
  const own = bridge({ source_mode: "ems" }, states, attributes, energy);
  assert.equal(own.hass.states[VIRTUAL.grid].state, "-307");
  assert.equal(own.hass.states[VIRTUAL.battery].state, "-1400");
});

test("no power sources do not produce an invalid original card config", () => {
  const b = buildUpstreamBridge({ states: {} }, {}, null, {});
  assert.equal(b, null);
});

test("bundled original PFCP is pinned, namespaced and licensed", () => {
  const root = fileURLToPath(new URL(".", import.meta.url));
  const base = "../custom_components/local_ems/frontend/";
  const js = readFileSync(resolve(root, base +
    "vendor/power-flow-card-plus-v0.4.0-beta.1.mjs"), "utf8");
  const license = readFileSync(resolve(root, base + "vendor/LICENSE-PFCP"), "utf8");
  assert.match(js, /Power Flow Card Plus original distribution: v0\.4\.0-beta\.1/);
  assert.ok(js.includes('Ca("local-ems-pfcp-upstream")'));
  assert.ok(js.includes('Ca("local-ems-pfcp-upstream-editor")'));
  assert.ok(!js.includes('Ca("power-flow-card-plus")'));
  assert.match(js, /export\{[A-Za-z_$]+ as PowerFlowCardPlus\}/);
  assert.match(license, /MIT License/);
  assert.match(license, /Copyright \(c\) 2023-2026 flixlix/);
  assert.equal(UPSTREAM_ELEMENT, "local-ems-pfcp-upstream");
});

test("wrapper serves original renderer and solver, not a custom SVG clone", () => {
  const root = fileURLToPath(new URL(".", import.meta.url));
  const base = "../custom_components/local_ems/frontend/";
  const js = readFileSync(resolve(root, base + "local-ems-flow-card.mjs"), "utf8");
  const backend = readFileSync(resolve(root, "../custom_components/local_ems/frontend.py"), "utf8");
  const manifest = JSON.parse(readFileSync(resolve(root,
    "../custom_components/local_ems/manifest.json"), "utf8"));
  assert.ok(js.includes('power-flow-card-plus-v0.4.0-beta.1.mjs?v=' + manifest.version));
  assert.ok(js.includes('pfcp-adapter.mjs?v=' + manifest.version));
  assert.ok(backend.includes('CARD_VERSION = "' + manifest.version + '"'));
  assert.ok(js.includes("Original.getConfigElement()"));
  assert.ok(!js.includes('const PATHS = {'));
  assert.ok(!js.includes('"solar-grid":'));
});


test("current original bundle 0.4.0-beta.1 preserves upstream provenance", () => {
  const root = fileURLToPath(new URL(".", import.meta.url));
  const path = "../custom_components/local_ems/frontend/vendor/";
  const js = readFileSync(resolve(root, path +
    "power-flow-card-plus-v0.4.0-beta.1.mjs"), "utf8");
  assert.ok(js.includes("d9f3a9255776b3e1a270bf72b2c8039e22047104"));
  assert.ok(js.includes('version:"0.4.0-beta.1"'));
  assert.ok(js.includes("https://github.com/flixlix/power-flow-card-plus/releases/"));
  assert.ok(js.includes('Ca("local-ems-pfcp-upstream")'));
  assert.ok(js.includes('Ca("local-ems-pfcp-upstream-editor")'));
  assert.ok(!js.includes('Ca("power-flow-card-plus")'));
  assert.ok(!js.includes('Ca("power-flow-card-plus-editor")'));
  assert.ok(js.includes('querySelector("#local-ems-pfcp-upstream")'));
});
