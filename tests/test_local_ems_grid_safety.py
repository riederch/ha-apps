# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail-closed grid interlock tests; no Home Assistant installation required."""
import sys
import unittest
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path
from types import ModuleType, SimpleNamespace

p = Path(__file__).resolve().parents[1] / "custom_components" / "local_ems"
pkg = ModuleType("local_ems")
pkg.__path__ = [str(p)]
sys.modules.setdefault("local_ems", pkg)

grid = import_module("local_ems.grid_safety")
c = import_module("local_ems.const")

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def state(value, age=0, with_report=True):
    return SimpleNamespace(
        state=value,
        last_reported=NOW - timedelta(seconds=age) if with_report else None,
        last_updated=NOW - timedelta(hours=9),
    )


def safety(status=True, meter=True, mode=True, contact=False, enabled=True):
    config = {
        c.GRID_ON_VALUES: "2, On Grid",
        c.GRID_EPS_VALUES: "3, EPS",
        c.METER_TIMEOUT_SECONDS: 10,
        c.MODE_ALLOWED_VALUES: "Self Consumption, Eigenverbrauch",
        c.GRID_RECOVERY_SECONDS: 120,
    }
    if status:
        config[c.GRID_STATE_ENTITY] = "sensor.inverter_state"
    if meter:
        config[c.METER_HEARTBEAT_ENTITY] = "sensor.grid_meter"
    if mode:
        config[c.MODE_ENTITY] = "select.inverter_mode"
    if contact:
        config[c.GRID_CONTACT_ENTITY] = "binary_sensor.grid_contact"
    return {c.CONF_GRID_SAFETY: config, c.CONF_EMS_ENABLED: enabled}


def valid_states():
    return {
        "sensor.inverter_state": state("2"),
        "sensor.grid_meter": state("123456", age=1),
        "select.inverter_mode": state("Self Consumption"),
        "binary_sensor.grid_contact": state("on"),
    }


def run(options=None, states=None, seconds_since_good=None):
    opts = safety() if options is None else options
    states = valid_states() if states is None else states
    since = NOW - timedelta(seconds=seconds_since_good) if seconds_since_good is not None else None
    return grid.evaluate_grid_safety(opts, states.get, NOW, since)


class GridSafetyTests(unittest.TestCase):
    def test_healthy_requires_stabilization(self):
        result, since = run()
        self.assertEqual(result.grid_state, "recovering")
        self.assertFalse(result.control_allowed)
        self.assertEqual(result.recovery_remaining_seconds, 120)
        self.assertEqual(since, NOW)
        stable, _ = run(seconds_since_good=120)
        self.assertTrue(stable.control_allowed)
        self.assertEqual(stable.grid_state, "on_grid")
        self.assertFalse(stable.load_shed_requested)

    def test_eps_drops_permission_immediately_even_with_meter(self):
        st = valid_states()
        st["sensor.inverter_state"] = state("3")
        result, since = run(states=st, seconds_since_good=300)
        self.assertEqual(result.grid_state, "eps")
        self.assertTrue(result.eps_detected)
        self.assertFalse(result.control_allowed)
        self.assertTrue(result.load_shed_requested)
        self.assertIsNone(since)

    def test_meter_stale_is_suspect_not_proof_of_eps(self):
        st = valid_states()
        st["sensor.grid_meter"] = state("123456", age=11)
        result, _ = run(states=st, seconds_since_good=300)
        self.assertEqual(result.grid_state, "suspect")
        self.assertEqual(result.safety_reason, "meter_heartbeat_stale")
        self.assertFalse(result.eps_detected)
        self.assertFalse(result.control_allowed)

    def test_unchanged_meter_value_still_healthy(self):
        st = valid_states()
        st["sensor.grid_meter"] = state("123456", age=1)
        self.assertTrue(run(states=st, seconds_since_good=200)[0].meter_heartbeat_ok)

    def test_meter_without_last_reported_is_not_assumed_fresh(self):
        st = valid_states()
        st["sensor.grid_meter"] = state("123456", with_report=False)
        self.assertEqual(run(states=st)[0].grid_state, "suspect")

    def test_meter_alone_cannot_prove_grid(self):
        options = safety(status=False, mode=False)
        result, _ = run(options=options)
        self.assertEqual(result.grid_state, "unconfigured")
        self.assertFalse(result.control_allowed)

    def test_allowed_operating_mode_and_wrong_mode(self):
        st = valid_states()
        st["select.inverter_mode"] = state("Time of Use")
        result, _ = run(states=st, seconds_since_good=500)
        self.assertEqual(result.grid_state, "on_grid")
        self.assertFalse(result.control_allowed)
        self.assertFalse(result.mode_allowed)
        self.assertEqual(result.safety_reason, "operating_mode_blocked")

    def test_mode_is_optional_for_other_inverters(self):
        opts = safety(mode=False)
        result, _ = run(options=opts, seconds_since_good=500)
        self.assertEqual(result.grid_state, "on_grid")
        self.assertIsNone(result.mode_allowed)
        self.assertTrue(result.control_allowed)

    def test_offline_mode_blocks(self):
        st = valid_states()
        st["select.inverter_mode"] = state("unavailable")
        self.assertFalse(run(states=st, seconds_since_good=500)[0].control_allowed)

    def test_missing_state_is_unknown(self):
        st = valid_states()
        del st["sensor.inverter_state"]
        result, _ = run(states=st)
        self.assertEqual(result.grid_state, "unknown")
        self.assertTrue(result.load_shed_requested)

    def test_binary_contact_without_inverter(self):
        opts = safety(status=False, mode=False, contact=True)
        r, _ = run(options=opts, seconds_since_good=200)
        self.assertTrue(r.control_allowed)
        states = valid_states()
        states["binary_sensor.grid_contact"] = state("off")
        r, _ = run(options=opts, states=states, seconds_since_good=200)
        self.assertEqual(r.grid_state, "grid_lost")
        self.assertFalse(r.control_allowed)

    def test_off_contact_overrules_inverter_on_grid(self):
        opts = safety(contact=True)
        states = valid_states()
        states["binary_sensor.grid_contact"] = state("off")
        r, _ = run(options=opts, states=states, seconds_since_good=500)
        self.assertEqual(r.grid_state, "grid_lost")

    def test_no_monitor_sources_fail_closed(self):
        result, _ = run(options={c.CONF_EMS_ENABLED: True})
        self.assertEqual(result.grid_state, "unconfigured")
        self.assertFalse(result.control_allowed)

    def test_disabled_ems_has_no_load_shed_request(self):
        result, _ = run(options=safety(enabled=False), seconds_since_good=999)
        self.assertFalse(result.control_allowed)
        self.assertFalse(result.load_shed_requested)

    def test_values_are_casefolded_exact_match(self):
        self.assertEqual(
            grid.parse_values(" Self Consumption, EIGENVERBRAUCH "),
            {"self consumption", "eigenverbrauch"},
        )
        opts = safety()
        states = valid_states()
        states["sensor.inverter_state"] = state("20")
        result, _ = run(options=opts, states=states)
        self.assertEqual(result.grid_state, "unknown")

    def test_overlapping_state_mapping_rejected(self):
        self.assertEqual(
            grid.validate_safety_config({
                c.GRID_STATE_ENTITY: "sensor.mode",
                c.GRID_ON_VALUES: "EPS, Grid",
                c.GRID_EPS_VALUES: "eps",
            }),
            {c.GRID_EPS_VALUES: "overlapping_grid_values"},
        )

    def test_mode_without_allowlist_rejected(self):
        self.assertEqual(
            grid.validate_safety_config({
                c.GRID_CONTACT_ENTITY: "binary_sensor.netz",
                c.MODE_ENTITY: "select.mode",
                c.MODE_ALLOWED_VALUES: "",
            }),
            {c.MODE_ALLOWED_VALUES: "mode_values_required"},
        )

    def test_grid_values_needed_for_inverter_source(self):
        self.assertEqual(
            grid.validate_safety_config({
                c.GRID_STATE_ENTITY: "sensor.mode",
                c.GRID_ON_VALUES: "",
            }),
            {c.GRID_ON_VALUES: "grid_values_required"},
        )

    def test_recovery_time_resets_after_eps(self):
        good, since = run(seconds_since_good=180)
        self.assertTrue(good.control_allowed)
        values = valid_states()
        values["sensor.inverter_state"] = state("EPS")
        _, after = run(states=values, seconds_since_good=180)
        self.assertIsNone(after)
        r, new_since = grid.evaluate_grid_safety(safety(), valid_states().get, NOW, after)
        self.assertFalse(r.control_allowed)
        self.assertEqual(new_since, NOW)


if __name__ == "__main__":
    unittest.main()
