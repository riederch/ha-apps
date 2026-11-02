# SPDX-License-Identifier: GPL-3.0-or-later
"""Check that Local EMS entity dropdowns select only suitable units."""
import sys
import unittest
from importlib import import_module
from pathlib import Path
from types import ModuleType, SimpleNamespace

pkg_path = Path(__file__).resolve().parents[1] / "custom_components" / "local_ems"
pkg = ModuleType("local_ems")
pkg.__path__ = [str(pkg_path)]
sys.modules.setdefault("local_ems", pkg)

filters = import_module("local_ems.source_filters")
constants = import_module("local_ems.const")


def state_with_unit(unit):
    return SimpleNamespace(attributes={"unit_of_measurement": unit})


class LocalEMSUnitFilterTests(unittest.TestCase):
    def test_grid_import_counter_only_wh_kwh(self):
        result = filters.entity_selector_filter(constants.CONF_SOURCE, "sensor")
        self.assertEqual(result, {
            "domain": "sensor", "unit_of_measurement": ["Wh", "kWh"]
        })

    def test_all_power_fields_only_w_or_kw(self):
        keys = [
            "grid_power_sensor", "pv_power_sensor", "house_power_sensor",
            "battery_power_sensor", constants.CONSUMER_MEASURED_POWER,
            constants.WALLBOX_CHARGE_POWER,
        ]
        for key in keys:
            with self.subTest(field=key):
                self.assertEqual(
                    filters.entity_selector_filter(key, "sensor"),
                    {"domain": "sensor", "unit_of_measurement": ["W", "kW"]},
                )

    def test_battery_soc_only_percent(self):
        self.assertEqual(
            filters.entity_selector_filter("battery_soc_sensor", "sensor"),
            {"domain": "sensor", "unit_of_measurement": ["%"]},
        )

    def test_wallbox_current_limit_only_amperes(self):
        self.assertEqual(
            filters.entity_selector_filter(
                constants.WALLBOX_CURRENT_LIMIT, "number"
            ),
            {"domain": "number", "unit_of_measurement": ["A"]},
        )

    def test_switch_selectors_still_use_domain(self):
        self.assertEqual(
            filters.entity_selector_filter(constants.CONSUMER_SWITCH, "switch"),
            {"domain": "switch"},
        )

    def test_validation_accepts_compatible_units(self):
        states = {
            "sensor.import": state_with_unit("Wh"),
            "sensor.pv": state_with_unit("kW"),
            "sensor.soc": state_with_unit("%"),
            "sensor.consumer": state_with_unit("W"),
            "number.wallbox_current": state_with_unit("A"),
        }
        data = {
            constants.CONF_SOURCE: "sensor.import",
            "pv_power_sensor": "sensor.pv",
            "battery_soc_sensor": "sensor.soc",
            constants.CONSUMER_MEASURED_POWER: "sensor.consumer",
            constants.WALLBOX_CURRENT_LIMIT: "number.wallbox_current",
        }
        self.assertEqual(
            filters.incompatible_selected_units(data, states.get), {}
        )

    def test_validation_rejects_wrong_units(self):
        states = {
            "sensor.bad_energy": state_with_unit("W"),
            "sensor.bad_power": state_with_unit("kWh"),
            "sensor.bad_soc": state_with_unit("°C"),
            "number.bad_current": state_with_unit("kW"),
        }
        data = {
            constants.CONF_SOURCE: "sensor.bad_energy",
            "pv_power_sensor": "sensor.bad_power",
            "battery_soc_sensor": "sensor.bad_soc",
            constants.WALLBOX_CURRENT_LIMIT: "number.bad_current",
        }
        self.assertEqual(
            filters.incompatible_selected_units(data, states.get),
            {key: "unit_mismatch" for key in data},
        )

    def test_offline_entity_does_not_invalidate_existing_mapping(self):
        self.assertEqual(
            filters.incompatible_selected_units(
                {"grid_power_sensor": "sensor.offline"}, lambda _: None
            ),
            {},
        )

    def test_incompatible_number_without_unit_is_detected(self):
        states = {"sensor.power": state_with_unit(None)}
        self.assertEqual(
            filters.incompatible_selected_units(
                {"grid_power_sensor": "sensor.power"}, states.get
            ),
            {"grid_power_sensor": "unit_mismatch"},
        )


if __name__ == "__main__":
    unittest.main()
