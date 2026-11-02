# SPDX-License-Identifier: GPL-3.0-or-later
"""Home Assistant entity selector metadata for Local EMS.

Only compatible units are offered in the UI, even when a sensor has no
device_class assigned. The filter is kept in one place so the initial
setup and later options dialogs cannot drift apart.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .const import (
    CONF_SOURCE,
    CONSUMER_MEASURED_POWER,
    ENERGY_SOURCE_KEYS,
    WALLBOX_CHARGE_POWER,
    WALLBOX_CURRENT_LIMIT,
)

ENERGY_UNITS = ("Wh", "kWh")
POWER_UNITS = ("W", "kW")
PERCENT_UNITS = ("%",)
FREQUENCY_UNITS = ("Hz",)
CURRENT_UNITS = ("A",)

# HA's entity selector supports filter.unit_of_measurement since the
# modern entity-filter schema. This is a presentation filter, not an
# automatic unit converter.
FIELD_UNITS: dict[str, tuple[str, ...]] = {
    CONF_SOURCE: ENERGY_UNITS,
    CONSUMER_MEASURED_POWER: POWER_UNITS,
    WALLBOX_CHARGE_POWER: POWER_UNITS,
    WALLBOX_CURRENT_LIMIT: CURRENT_UNITS,
    **{
        field: (
            PERCENT_UNITS if field == "battery_soc_sensor"
            else FREQUENCY_UNITS if field == "grid_frequency_sensor"
            else POWER_UNITS
        )
        for field in ENERGY_SOURCE_KEYS
    },
}


def entity_selector_filter(field: str, entity_domain: str) -> dict[str, Any]:
    """Return a HA frontend-compatible EntitySelector 'filter' specification."""
    result: dict[str, Any] = {"domain": entity_domain}
    if units := FIELD_UNITS.get(field):
        result["unit_of_measurement"] = list(units)
    return result


def incompatible_selected_units(
    selections: Mapping[str, Any],
    get_state: Callable[[str], Any],
) -> dict[str, str]:
    """Validate already selected entities against live HA metadata.

    The frontend filters the available choices; this further checks submitted
    values. Missing states (e.g. offline devices) are not rejected solely for
    being offline, but a known incompatible unit is never silently accepted.
    """
    errors: dict[str, str] = {}
    for field, allowed_units in FIELD_UNITS.items():
        entity_id = selections.get(field)
        if not isinstance(entity_id, str) or not entity_id:
            continue
        state = get_state(entity_id)
        if state is None:
            continue
        unit = state.attributes.get("unit_of_measurement")
        if unit not in allowed_units:
            errors[field] = "unit_mismatch"
    return errors
