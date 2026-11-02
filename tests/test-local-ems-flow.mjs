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
