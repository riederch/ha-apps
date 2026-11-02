# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for the HA options catalogue; no Home Assistant installation needed."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from importlib import import_module
from types import ModuleType

pkg_path = Path(__file__).resolve().parents[1] / "custom_components" / "local_ems"
pkg = ModuleType("local_ems")
pkg.__path__ = [str(pkg_path)]
sys.modules.setdefault("local_ems", pkg)

devices = import_module("local_ems.devices")
constants = import_module("local_ems.const")
save_item = devices.save_item
remove_item = devices.remove_item
set_sources = devices.set_sources
catalog_snapshot = devices.catalog_snapshot
CONF_CONSUMERS = constants.CONF_CONSUMERS
CONF_WALLBOXES = constants.CONF_WALLBOXES
CONF_ENERGY_SOURCES = constants.CONF_ENERGY_SOURCES


def consumer(entity, name="Heizstab", watts=3000):
    return {
        "name": name, "consumer_type": "heating_rod", "switch_entity": entity,
        "rated_power_w": watts, "priority": 10,
        "min_on_seconds": 300, "min_off_seconds": 300,
        "surplus_margin_w": 200, "enabled": True,
    }


def wallbox(name="go-e", switch="switch.goe_enable"):
    return {
        "name": name, "charge_enable_switch": switch,
        "priority": 20, "phase_count": 3, "max_current_a": 16, "enabled": True,
    }


def fake(state, unit=None):
    return SimpleNamespace(
        state=state, attributes={"unit_of_measurement": unit}
    )


class LocalEMSCatalogTests(unittest.TestCase):
    def test_many_independent_consumers(self):
        initial = {"limit_kw": 10, "warning_kw": 9}
        one = save_item(initial, CONF_CONSUMERS, consumer("switch.heater_1"), id_factory=lambda: "a")
        two = save_item(one, CONF_CONSUMERS,
                        consumer("switch.heater_2", name="Heizlüfter", watts=2200),
                        id_factory=lambda: "b")
        self.assertEqual([v["id"] for v in two[CONF_CONSUMERS]], ["a", "b"])
        self.assertEqual(two["limit_kw"], 10)
        self.assertNotIn(CONF_CONSUMERS, initial)

    def test_duplicate_switch_is_rejected(self):
        one = save_item({}, CONF_CONSUMERS, consumer("switch.same"), id_factory=lambda: "a")
        with self.assertRaisesRegex(ValueError, "duplicate_entity"):
            save_item(one, CONF_CONSUMERS, consumer("switch.same"))

    def test_edit_preserves_id_and_rest_of_list(self):
        one = save_item({}, CONF_CONSUMERS, consumer("switch.a"), id_factory=lambda: "a")
        two = save_item(one, CONF_CONSUMERS, consumer("switch.b"), id_factory=lambda: "b")
        changed = save_item(two, CONF_CONSUMERS,
                            consumer("switch.a", name="Neue Bezeichnung"),
                            item_id="a")
        self.assertEqual(len(changed[CONF_CONSUMERS]), 2)
        self.assertEqual(changed[CONF_CONSUMERS][0]["id"], "a")
        self.assertEqual(changed[CONF_CONSUMERS][0]["name"], "Neue Bezeichnung")
        self.assertEqual(changed[CONF_CONSUMERS][1], two[CONF_CONSUMERS][1])

    def test_remove_keeps_others_and_never_switches_devices(self):
        options = save_item({}, CONF_CONSUMERS,
                            consumer("switch.a"), id_factory=lambda: "a")
        options = save_item(options, CONF_CONSUMERS,
                            consumer("switch.b"), id_factory=lambda: "b")
        pruned = remove_item(options, CONF_CONSUMERS, "a")
        self.assertEqual(len(pruned[CONF_CONSUMERS]), 1)
        self.assertEqual(pruned[CONF_CONSUMERS][0]["id"], "b")
        self.assertEqual(len(options[CONF_CONSUMERS]), 2)

    def test_wallbox_requires_entity_and_can_be_registered(self):
        with self.assertRaisesRegex(ValueError, "wallbox_entity_required"):
            save_item({}, CONF_WALLBOXES, {
                "name": "Empty wallbox", "phase_count": 3
            })
        options = save_item({}, CONF_WALLBOXES, wallbox(), id_factory=lambda: "goe")
        self.assertEqual(options[CONF_WALLBOXES][0]["id"], "goe")

    def test_wallbox_duplicate_rejected(self):
        options = save_item({}, CONF_WALLBOXES, wallbox(), id_factory=lambda: "a")
        with self.assertRaisesRegex(ValueError, "duplicate_entity"):
            save_item(options, CONF_WALLBOXES, wallbox(name="Other"))

    def test_wallbox_switch_cannot_be_registered_as_heater(self):
        options = save_item({}, CONF_WALLBOXES,
                            wallbox(switch="switch.shared"), id_factory=lambda: "w")
        with self.assertRaisesRegex(ValueError, "duplicate_entity"):
            save_item(options, CONF_CONSUMERS, consumer("switch.shared"))
        options = save_item({}, CONF_CONSUMERS,
                            consumer("switch.shared"), id_factory=lambda: "h")
        with self.assertRaisesRegex(ValueError, "duplicate_entity"):
            save_item(options, CONF_WALLBOXES,
                      wallbox(switch="switch.shared"))

    def test_wrong_domain_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_entity_domain"):
            save_item({}, CONF_CONSUMERS, consumer("light.foo"))

    def test_invalid_power_rejected(self):
        with self.assertRaisesRegex(ValueError, "power_required"):
            save_item({}, CONF_CONSUMERS, consumer("switch.a", watts=0))

    def test_energy_sources_keep_existing_registry(self):
        options = save_item({"limit_kw": 10}, CONF_CONSUMERS,
                            consumer("switch.a"), id_factory=lambda: "a")
        updated = set_sources(options, {
            "grid_power_sensor": "sensor.netz_kng",
            "battery_soc_sensor": "",
            "pv_power_sensor": "sensor.pv_power",
        })
        self.assertEqual(updated[CONF_ENERGY_SOURCES], {
            "grid_power_sensor": "sensor.netz_kng",
            "pv_power_sensor": "sensor.pv_power",
        })
        self.assertEqual(updated[CONF_CONSUMERS], options[CONF_CONSUMERS])

    def test_energy_sources_store_sign_inversions_and_frequency(self):
        updated = set_sources({}, {
            "grid_power_sensor": "sensor.kng_p",
            "pv_power_sensor": "sensor.pv",
            "grid_frequency_sensor": "sensor.grid_hz",
            "battery_power_invert": True,
            "grid_power_invert": False,
        })
        result = updated[CONF_ENERGY_SOURCES]
        self.assertEqual(result["grid_frequency_sensor"], "sensor.grid_hz")
        self.assertTrue(result["battery_power_invert"])
        self.assertFalse(result["grid_power_invert"])
        # The flag is optional for older callers, keeping API backward-compatible.
        old = set_sources({}, {"grid_power_sensor": "sensor.kng_p"})
        self.assertNotIn("battery_power_invert", old[CONF_ENERGY_SOURCES])

    def test_live_state_summary_falls_back_to_rated_power(self):
        options = save_item({}, CONF_CONSUMERS,
                            consumer("switch.a", watts=3000),
                            id_factory=lambda: "a")
        options = save_item(options, CONF_CONSUMERS,
                            consumer("switch.b", watts=2000),
                            id_factory=lambda: "b")
        states = {"switch.a": fake("on"), "switch.b": fake("off")}
        snap = catalog_snapshot(options, states.get)
        self.assertEqual(snap["consumers_on"], 1)
        self.assertEqual(snap["consumers_count"], 2)
        self.assertEqual(snap["consumer_power_kw_estimated"], 3)

    def test_sensor_power_preferred_to_nominal(self):
        item = consumer("switch.a", watts=3000)
        item["power_sensor"] = "sensor.load_a"
        options = save_item({}, CONF_CONSUMERS, item, id_factory=lambda: "a")
        states = {"switch.a": fake("on"), "sensor.load_a": fake("1.4", "kW")}
        snap = catalog_snapshot(options, states.get)
        self.assertEqual(snap["consumer_power_kw_estimated"], 1.4)

    def test_unavailable_switch_not_treated_as_off(self):
        options = save_item({}, CONF_CONSUMERS,
                            consumer("switch.a"), id_factory=lambda: "a")
        snap = catalog_snapshot(options, {}.get)
        self.assertEqual(snap["consumers_unknown"], 1)
        self.assertEqual(snap["consumers_on"], 0)
        self.assertIsNone(snap["consumer_power_kw_estimated"])


if __name__ == "__main__":
    unittest.main()
