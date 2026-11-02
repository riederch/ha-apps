# SPDX-License-Identifier: GPL-3.0-or-later
"""Persistent, read-only EMS device catalogue.

Device definitions live exclusively in HA's config entry options. The registry
contains mappings and planning parameters, not measured time series.
"""
from __future__ import annotations

from math import isfinite
from typing import Any, Callable
from uuid import uuid4

from .const import (
    CONF_CONSUMERS,
    CONF_ENERGY_SOURCES,
    CONF_WALLBOXES,
    CONSUMER_SWITCH,
    CONSUMER_RATED_POWER,
    CONSUMER_MEASURED_POWER,
    WALLBOX_CHARGE_SWITCH,
    WALLBOX_CHARGE_POWER,
    WALLBOX_CURRENT_LIMIT,
    WALLBOX_CONNECTED,
)

CATALOG_KEYS = (CONF_CONSUMERS, CONF_WALLBOXES)
ENTITY_FIELDS = {
    CONF_CONSUMERS: {
        CONSUMER_SWITCH: "switch",
        CONSUMER_MEASURED_POWER: "sensor",
    },
    CONF_WALLBOXES: {
        WALLBOX_CHARGE_SWITCH: "switch",
        WALLBOX_CHARGE_POWER: "sensor",
        WALLBOX_CURRENT_LIMIT: "number",
        WALLBOX_CONNECTED: "binary_sensor",
    },
}
UNIQUE_ENTITY_FIELDS = {
    CONF_CONSUMERS: (CONSUMER_SWITCH,),
    CONF_WALLBOXES: (WALLBOX_CHARGE_SWITCH, WALLBOX_CHARGE_POWER),
}


def _validate(item: dict[str, Any], kind: str) -> None:
    if kind not in CATALOG_KEYS:
        raise ValueError("invalid_collection")
    if not str(item.get("name", "")).strip():
        raise ValueError("name_required")
    for field, domain in ENTITY_FIELDS[kind].items():
        value = item.get(field)
        if value and not str(value).startswith(f"{domain}."):
            raise ValueError("invalid_entity_domain")
    if kind == CONF_CONSUMERS:
        if not item.get(CONSUMER_SWITCH):
            raise ValueError("switch_required")
        value = float(item.get(CONSUMER_RATED_POWER, 0))
        if not isfinite(value) or not 1 <= value <= 50000:
            raise ValueError("power_required")
    else:
        if not any(item.get(field) for field in ENTITY_FIELDS[kind]):
            raise ValueError("wallbox_entity_required")
        if int(item.get("phase_count", 3)) not in (1, 3):
            raise ValueError("invalid_phase_count")


def save_item(
    options: dict[str, Any], kind: str, item: dict[str, Any],
    item_id: str | None = None, id_factory: Callable[[], str] | None = None
) -> dict[str, Any]:
    """Add or replace one entry, preserving its stable id and other options."""
    _validate(item, kind)
    current = list(options.get(kind, []))
    if item_id is not None and not any(row.get("id") == item_id for row in current):
        raise ValueError("unknown_item")
    new_id = item_id or (id_factory or (lambda: uuid4().hex))()
    if any(row.get("id") == new_id and row.get("id") != item_id for row in current):
        raise ValueError("duplicate_id")
    for row in current:
        if row.get("id") == item_id:
            continue
        for key in UNIQUE_ENTITY_FIELDS[kind]:
            if item.get(key) and row.get(key) == item[key]:
                raise ValueError("duplicate_entity")
    normalized = {**item, "id": new_id, "name": str(item["name"]).strip()}
    updated = [
        normalized if row.get("id") == item_id else dict(row)
        for row in current
    ] if item_id else current + [normalized]
    result = dict(options)
    result[kind] = updated
    return result


def remove_item(options: dict[str, Any], kind: str, item_id: str) -> dict[str, Any]:
    if kind not in CATALOG_KEYS:
        raise ValueError("invalid_collection")
    current = list(options.get(kind, []))
    updated = [row for row in current if row.get("id") != item_id]
    if len(updated) == len(current):
        raise ValueError("unknown_item")
    result = dict(options)
    result[kind] = updated
    return result


def set_sources(options: dict[str, Any], data: dict[str, str]) -> dict[str, Any]:
    result = dict(options)
    from .const import ENERGY_SOURCE_KEYS

    result[CONF_ENERGY_SOURCES] = {
        k: v for k, v in data.items()
        if k in ENERGY_SOURCE_KEYS and v and str(v).startswith("sensor.")
    }
    return result


def _state_of(resolve: Callable[[str], Any], entity_id: str | None) -> str:
    if not entity_id:
        return "unconfigured"
    state = resolve(entity_id)
    return str(state.state) if state is not None else "unavailable"


def _power_w(resolve: Callable[[str], Any], entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    state = resolve(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        return None
    try:
        value = float(state.state)
    except (ValueError, TypeError):
        return None
    if not isfinite(value) or value < 0:
        return None
    unit = state.attributes.get("unit_of_measurement")
    if unit == "W":
        return value
    if unit == "kW":
        return value * 1000
    return None


def catalog_snapshot(
    options: dict[str, Any], resolve: Callable[[str], Any]
) -> dict[str, Any]:
    """Summarize registered loads without issuing any HA service calls."""
    consumers: list[dict[str, Any]] = []
    active = unknown = 0
    power_w = 0.0
    for item in options.get(CONF_CONSUMERS, []):
        state = _state_of(resolve, item.get(CONSUMER_SWITCH))
        if state == "on":
            active += 1
            measured_w = _power_w(resolve, item.get(CONSUMER_MEASURED_POWER))
            power_w += (measured_w if measured_w is not None
                        else float(item[CONSUMER_RATED_POWER]))
        elif state not in ("off",):
            unknown += 1
        consumers.append({
            "id": item["id"],
            "name": item["name"],
            "type": item.get("consumer_type"),
            "switch_entity": item[CONSUMER_SWITCH],
            "switch_state": state,
            "rated_power_w": item[CONSUMER_RATED_POWER],
            "priority": item.get("priority", 50),
            "enabled": item.get("enabled", True),
        })
    wallboxes: list[dict[str, Any]] = []
    for item in options.get(CONF_WALLBOXES, []):
        wallboxes.append({
            "id": item["id"], "name": item["name"],
            "charge_enable_switch": item.get(WALLBOX_CHARGE_SWITCH),
            "charge_enable_state": _state_of(resolve, item.get(WALLBOX_CHARGE_SWITCH)),
            "charge_power_sensor": item.get(WALLBOX_CHARGE_POWER),
            "charge_power_w": _power_w(resolve, item.get(WALLBOX_CHARGE_POWER)),
            "vehicle_connected_state": _state_of(resolve, item.get(WALLBOX_CONNECTED)),
            "priority": item.get("priority", 50),
            "enabled": item.get("enabled", True),
        })
    return {
        "consumers_count": len(consumers),
        "consumers_on": active,
        "consumers_unknown": unknown,
        "consumer_power_kw_estimated": round(power_w / 1000, 3),
        "wallboxes_count": len(wallboxes),
        "catalog_consumers": consumers,
        "catalog_wallboxes": wallboxes,
        "catalog_sources": dict(options.get(CONF_ENERGY_SOURCES, {})),
    }
