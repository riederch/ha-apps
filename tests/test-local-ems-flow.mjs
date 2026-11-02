// SPDX-License-Identifier: GPL-3.0-or-later
import test from "node:test";
import assert from "node:assert/strict";

import {
  toWatts, toPercent, toHertz, buildFlowModel, formatWatts,
} from "../custom_components/local_ems/frontend/flow-model.mjs";

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

test("native card preserves the circular four-node layout", async () => {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { dirname, resolve } = await import("node:path");
  const root = dirname(fileURLToPath(import.meta.url));
  const card = readFileSync(resolve(root,
    "../custom_components/local_ems/frontend/local-ems-flow-card.mjs"), "utf8");
  for (const role of ["solar", "grid", "home", "battery"]) {
    assert.match(card, new RegExp('class="node ' + role + '"'));
  }
  assert.match(card, /border-radius:50%/);
  assert.match(card, /<path class="dots"/);
  assert.match(card, /energy\/get_prefs/);
  assert.doesNotMatch(card, /power-flow-card-plus\.js/);
});
