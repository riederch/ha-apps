# SPDX-License-Identifier: GPL-3.0-or-later
"""UI-driven Local EMS setup and registry administration, without YAML."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CONSUMERS,
    CONF_ENERGY_SOURCES,
    CONF_LIMIT_KW,
    CONF_SOURCE,
    CONF_STALE_SECONDS,
    CONF_WALLBOXES,
    CONF_WARNING_KW,
    CONSUMER_ENABLED,
    CONSUMER_KIND,
    CONSUMER_MEASURED_POWER,
    CONSUMER_MIN_OFF,
    CONSUMER_MIN_ON,
    CONSUMER_PRIORITY,
    CONSUMER_RATED_POWER,
    CONSUMER_SURPLUS_MARGIN,
    CONSUMER_SWITCH,
    DEFAULT_LIMIT_KW,
    DEFAULT_SOURCE,
    DEFAULT_STALE_SECONDS,
    DEFAULT_WARNING_KW,
    DOMAIN,
    ENERGY_SOURCE_KEYS,
    GRID_POWER_INVERT,
    BATTERY_POWER_INVERT,
    CONF_GRID_SAFETY,
    CONF_EMS_ENABLED,
    GRID_STATE_ENTITY,
    GRID_ON_VALUES,
    GRID_EPS_VALUES,
    GRID_CONTACT_ENTITY,
    GRID_CONTACT_ON_IS_PRESENT,
    METER_HEARTBEAT_ENTITY,
    METER_TIMEOUT_SECONDS,
    MODE_ENTITY,
    MODE_ALLOWED_VALUES,
    GRID_RECOVERY_SECONDS,
    DEFAULT_METER_TIMEOUT_SECONDS,
    DEFAULT_GRID_RECOVERY_SECONDS,
    WALLBOX_CHARGE_POWER,
    WALLBOX_CHARGE_SWITCH,
    WALLBOX_CONNECTED,
    WALLBOX_CURRENT_LIMIT,
    WALLBOX_MAX_CURRENT,
    WALLBOX_PHASE_COUNT,
)
from .devices import remove_item, save_item, set_sources
from .grid_safety import validate_safety_config
from .source_filters import entity_selector_filter, incompatible_selected_units


def _energy_form(source: str, limit: float, warning: float, stale: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SOURCE, default=source): _filtered_entity(
                CONF_SOURCE, "sensor"
            ),
            vol.Required(CONF_LIMIT_KW, default=limit): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=100)
            ),
            vol.Required(CONF_WARNING_KW, default=warning): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=100)
            ),
            vol.Required(CONF_STALE_SECONDS, default=stale): vol.All(
                vol.Coerce(int), vol.Range(min=30, max=3600)
            ),
        }
    )


def _validate_source(hass, user_input: dict) -> dict[str, str]:
    state = hass.states.get(user_input[CONF_SOURCE])
    if state is None:
        return {"base": "source_missing"}
    if state.attributes.get("unit_of_measurement") not in {"Wh", "kWh"}:
        return {"base": "source_unit"}
    try:
        float(state.state)
    except (ValueError, TypeError):
        return {"base": "source_unavailable"}
    if user_input[CONF_WARNING_KW] >= user_input[CONF_LIMIT_KW]:
        return {"base": "warning_above_limit"}
    return {}


def _filtered_entity(field: str, entity_domain: str) -> selector.EntitySelector:
    """Filter the dropdown by domain and physical measurement unit."""
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=entity_selector_filter(field, entity_domain)
        )
    )


def _optional_entity(name: str, entity_domain: str, item: dict) -> tuple:
    """Return an optional HA entity selector with the saved value preselected."""
    value = item.get(name)
    # suggested_value is visible but, unlike default, can be cleared in the UI.
    marker = (
        vol.Optional(name, description={"suggested_value": value})
        if value else vol.Optional(name)
    )
    return marker, _filtered_entity(name, entity_domain)


def _multi_entity_selector(domains: list[str]) -> selector.EntitySelector:
    """Select status entities independently of any inverter manufacturer."""
    return selector.EntitySelector(selector.EntitySelectorConfig(
        filter={"domain": domains}
    ))


def _optional_status_entity(name: str, current: dict, domains: list[str]) -> tuple:
    value = current.get(name)
    key = (
        vol.Optional(name, description={"suggested_value": value})
        if value else vol.Optional(name)
    )
    return key, _multi_entity_selector(domains)


def _grid_safety_form(current: dict, enabled: bool) -> vol.Schema:
    """Safety inputs are selectable HA entities plus user-defined raw states."""
    fields: dict = {
        vol.Required(
            CONF_EMS_ENABLED, default=enabled
        ): selector.BooleanSelector(),
        vol.Required(
            GRID_ON_VALUES, default=current.get(GRID_ON_VALUES, "")
        ): vol.All(str, vol.Length(max=255)),
        vol.Required(
            GRID_EPS_VALUES, default=current.get(GRID_EPS_VALUES, "")
        ): vol.All(str, vol.Length(max=255)),
        vol.Required(
            MODE_ALLOWED_VALUES, default=current.get(MODE_ALLOWED_VALUES, "")
        ): vol.All(str, vol.Length(max=255)),
        vol.Required(
            METER_TIMEOUT_SECONDS,
            default=current.get(METER_TIMEOUT_SECONDS, DEFAULT_METER_TIMEOUT_SECONDS)
        ): vol.All(vol.Coerce(int), vol.Range(min=3, max=600)),
        vol.Required(
            GRID_RECOVERY_SECONDS,
            default=current.get(GRID_RECOVERY_SECONDS, DEFAULT_GRID_RECOVERY_SECONDS)
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=3600)),
        vol.Required(
            GRID_CONTACT_ON_IS_PRESENT,
            default=current.get(GRID_CONTACT_ON_IS_PRESENT, True)
        ): selector.BooleanSelector(),
    }
    for key, domains in (
        (GRID_STATE_ENTITY, ["sensor", "select", "input_select"]),
        (GRID_CONTACT_ENTITY, ["binary_sensor"]),
        (METER_HEARTBEAT_ENTITY, ["sensor", "binary_sensor"]),
        (MODE_ENTITY, ["sensor", "select", "input_select"]),
    ):
        marker, entity_selector = _optional_status_entity(key, current, domains)
        fields[marker] = entity_selector
    return vol.Schema(fields)


def _consumer_form(item: dict) -> vol.Schema:
    schema: dict = {
        vol.Required("name", default=item.get("name", "")): vol.All(
            str, vol.Length(min=1, max=80)
        ),
        vol.Required(CONSUMER_KIND, default=item.get(CONSUMER_KIND, "heating_rod")):
            vol.In({
                "heating_rod": "Heizstab",
                "fan_heater": "Heizlüfter",
                "other": "Sonstiger Verbraucher",
            }),
        (vol.Required(CONSUMER_SWITCH, default=item[CONSUMER_SWITCH])
         if item.get(CONSUMER_SWITCH) else vol.Required(CONSUMER_SWITCH)):
            _filtered_entity(CONSUMER_SWITCH, "switch"),
        vol.Required(CONSUMER_RATED_POWER, default=item.get(CONSUMER_RATED_POWER, 2000)):
            vol.All(vol.Coerce(float), vol.Range(min=1, max=50000)),
        vol.Required(CONSUMER_PRIORITY, default=item.get(CONSUMER_PRIORITY, 50)):
            vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Required(CONSUMER_MIN_ON, default=item.get(CONSUMER_MIN_ON, 300)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=86400)),
        vol.Required(CONSUMER_MIN_OFF, default=item.get(CONSUMER_MIN_OFF, 300)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=86400)),
        vol.Required(CONSUMER_SURPLUS_MARGIN,
                     default=item.get(CONSUMER_SURPLUS_MARGIN, 200)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=5000)),
        vol.Required(CONSUMER_ENABLED, default=item.get(CONSUMER_ENABLED, True)):
            selector.BooleanSelector(),
    }
    schema.update([_optional_entity(CONSUMER_MEASURED_POWER, "sensor", item)])
    return vol.Schema(schema)


def _wallbox_form(item: dict) -> vol.Schema:
    schema: dict = {
        vol.Required("name", default=item.get("name", "")): vol.All(
            str, vol.Length(min=1, max=80)
        ),
        vol.Required(CONSUMER_PRIORITY, default=item.get(CONSUMER_PRIORITY, 20)):
            vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Required(WALLBOX_PHASE_COUNT,
                     default=str(item.get(WALLBOX_PHASE_COUNT, 3))):
            vol.In({"1": "Einphasig", "3": "Dreiphasig"}),
        vol.Required(WALLBOX_MAX_CURRENT,
                     default=item.get(WALLBOX_MAX_CURRENT, 16)):
            vol.All(vol.Coerce(int), vol.Range(min=6, max=80)),
        vol.Required(CONSUMER_ENABLED,
                     default=item.get(CONSUMER_ENABLED, True)):
            selector.BooleanSelector(),
    }
    for key, domain in (
        (WALLBOX_CHARGE_POWER, "sensor"),
        (WALLBOX_CHARGE_SWITCH, "switch"),
        (WALLBOX_CURRENT_LIMIT, "number"),
        (WALLBOX_CONNECTED, "binary_sensor"),
    ):
        schema.update([_optional_entity(key, domain, item)])
    return vol.Schema(schema)


def _sources_form(current: dict) -> vol.Schema:
    fields = dict(
        _optional_entity(key, "sensor", current)
        for key in ENERGY_SOURCE_KEYS
    )
    fields.update({
        vol.Required(GRID_POWER_INVERT, default=current.get(GRID_POWER_INVERT, False)):
            selector.BooleanSelector(),
        vol.Required(BATTERY_POWER_INVERT, default=current.get(BATTERY_POWER_INVERT, False)):
            selector.BooleanSelector(),
    })
    return vol.Schema(fields)


def _choose_item(items: list[dict]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("item_id"): vol.In(
                {
                    item["id"]: f"{item['name']} ({item.get(CONSUMER_SWITCH) or item.get(WALLBOX_CHARGE_POWER) or item.get(WALLBOX_CHARGE_SWITCH) or item['id']})"
                    for item in items
                }
            )
        }
    )


class LocalEMSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initialize the core. All new devices are managed in its options menu."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            errors = _validate_source(self.hass, user_input)
            if not errors:
                await self.async_set_unique_id(user_input[CONF_SOURCE])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Local EMS",
                    data={CONF_SOURCE: user_input[CONF_SOURCE]},
                    options={
                        CONF_LIMIT_KW: user_input[CONF_LIMIT_KW],
                        CONF_WARNING_KW: user_input[CONF_WARNING_KW],
                        CONF_STALE_SECONDS: user_input[CONF_STALE_SECONDS],
                        CONF_CONSUMERS: [],
                        CONF_WALLBOXES: [],
                        CONF_ENERGY_SOURCES: {},
                        CONF_GRID_SAFETY: {},
                        CONF_EMS_ENABLED: False,
                    },
                )
        return self.async_show_form(
            step_id="user",
            data_schema=_energy_form(
                DEFAULT_SOURCE, DEFAULT_LIMIT_KW, DEFAULT_WARNING_KW,
                DEFAULT_STALE_SECONDS,
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LocalEMSOptionsFlow()


class LocalEMSOptionsFlow(config_entries.OptionsFlow):
    """Add, update and remove consumers / wallboxes in the HA configuration UI."""

    def __init__(self) -> None:
        self._selected_id: str | None = None

    def _items(self, category: str) -> list[dict]:
        return list(self.config_entry.options.get(category, []))

    def _finish(self, options: dict) -> dict:
        return self.async_create_entry(title="", data=options)

    def _save_item(
        self, kind: str, user_input: dict, selected_id: str | None = None
    ) -> dict:
        payload = dict(user_input)
        if kind == CONF_WALLBOXES:
            payload[WALLBOX_PHASE_COUNT] = int(payload[WALLBOX_PHASE_COUNT])
        if incompatible_selected_units(payload, self.hass.states.get):
            raise ValueError("unit_mismatch")
        try:
            options = save_item(dict(self.config_entry.options), kind, payload, selected_id)
        except ValueError as err:
            raise ValueError(str(err)) from err
        return self._finish(options)

    async def async_step_init(self, user_input: dict | None = None):
        choices = [
            "peak_settings", "energy_sources", "grid_safety",
            "add_consumer", "add_wallbox"
        ]
        if self._items(CONF_CONSUMERS):
            choices += ["edit_consumer", "remove_consumer"]
        if self._items(CONF_WALLBOXES):
            choices += ["edit_wallbox", "remove_wallbox"]
        return self.async_show_menu(step_id="init", menu_options=choices)

    async def async_step_grid_safety(self, user_input: dict | None = None):
        """Map grid, heartbeat and operating-mode signals through the HA UI."""
        errors = {}
        if user_input is not None:
            values = dict(user_input)
            enabled = bool(values.pop(CONF_EMS_ENABLED, False))
            errors = validate_safety_config(values)
            if not errors:
                options = dict(self.config_entry.options)
                options[CONF_GRID_SAFETY] = values
                options[CONF_EMS_ENABLED] = enabled
                return self._finish(options)
        return self.async_show_form(
            step_id="grid_safety",
            data_schema=_grid_safety_form(
                dict(self.config_entry.options.get(CONF_GRID_SAFETY, {})),
                bool(self.config_entry.options.get(CONF_EMS_ENABLED, False)),
            ),
            errors=errors,
        )

    async def async_step_peak_settings(self, user_input: dict | None = None):
        opts = self.config_entry.options
        errors = {}
        if user_input is not None:
            data = {**user_input, CONF_SOURCE: self.config_entry.data[CONF_SOURCE]}
            errors = _validate_source(self.hass, data)
            if not errors:
                updated = dict(opts)
                updated.update(user_input)
                return self._finish(updated)
        return self.async_show_form(
            step_id="peak_settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LIMIT_KW, default=opts.get(CONF_LIMIT_KW, DEFAULT_LIMIT_KW)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100)),
                    vol.Required(
                        CONF_WARNING_KW,
                        default=opts.get(CONF_WARNING_KW, DEFAULT_WARNING_KW),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100)),
                    vol.Required(
                        CONF_STALE_SECONDS,
                        default=opts.get(CONF_STALE_SECONDS, DEFAULT_STALE_SECONDS),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                }
            ),
            errors=errors,
        )

    async def async_step_energy_sources(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            errors = incompatible_selected_units(user_input, self.hass.states.get)
            if not errors:
                return self._finish(
                    set_sources(dict(self.config_entry.options), user_input)
                )
        return self.async_show_form(
            step_id="energy_sources",
            data_schema=_sources_form(
                dict(self.config_entry.options.get(CONF_ENERGY_SOURCES, {}))
            ),
            errors=errors,
        )

    async def async_step_add_consumer(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            try:
                return self._save_item(CONF_CONSUMERS, user_input)
            except ValueError as err:
                errors = {"base": str(err)}
        return self.async_show_form(
            step_id="add_consumer", data_schema=_consumer_form({}), errors=errors
        )

    async def async_step_edit_consumer(self, user_input: dict | None = None):
        items = self._items(CONF_CONSUMERS)
        if user_input is not None:
            self._selected_id = user_input["item_id"]
            return await self.async_step_consumer_details()
        return self.async_show_form(
            step_id="edit_consumer", data_schema=_choose_item(items)
        )

    async def async_step_consumer_details(self, user_input: dict | None = None):
        current = next(
            (r for r in self._items(CONF_CONSUMERS) if r["id"] == self._selected_id),
            None,
        )
        if current is None:
            return self.async_abort(reason="item_not_found")
        errors = {}
        if user_input is not None:
            try:
                return self._save_item(CONF_CONSUMERS, user_input, self._selected_id)
            except ValueError as err:
                errors = {"base": str(err)}
        return self.async_show_form(
            step_id="consumer_details", data_schema=_consumer_form(current),
            errors=errors,
        )

    async def async_step_remove_consumer(self, user_input: dict | None = None):
        if user_input is not None:
            self._selected_id = user_input["item_id"]
            return await self.async_step_confirm_remove_consumer()
        return self.async_show_form(
            step_id="remove_consumer",
            data_schema=_choose_item(self._items(CONF_CONSUMERS)),
        )

    async def async_step_confirm_remove_consumer(
        self, user_input: dict | None = None
    ):
        if user_input is not None:
            try:
                updated = remove_item(
                    dict(self.config_entry.options), CONF_CONSUMERS,
                    self._selected_id,
                )
            except ValueError:
                return self.async_abort(reason="item_not_found")
            return self._finish(updated)
        return self.async_show_form(
            step_id="confirm_remove_consumer", data_schema=vol.Schema({})
        )

    async def async_step_add_wallbox(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            try:
                return self._save_item(CONF_WALLBOXES, user_input)
            except ValueError as err:
                errors = {"base": str(err)}
        return self.async_show_form(
            step_id="add_wallbox", data_schema=_wallbox_form({}), errors=errors
        )

    async def async_step_edit_wallbox(self, user_input: dict | None = None):
        if user_input is not None:
            self._selected_id = user_input["item_id"]
            return await self.async_step_wallbox_details()
        return self.async_show_form(
            step_id="edit_wallbox",
            data_schema=_choose_item(self._items(CONF_WALLBOXES)),
        )

    async def async_step_wallbox_details(self, user_input: dict | None = None):
        current = next(
            (r for r in self._items(CONF_WALLBOXES) if r["id"] == self._selected_id),
            None,
        )
        if current is None:
            return self.async_abort(reason="item_not_found")
        errors = {}
        if user_input is not None:
            try:
                return self._save_item(CONF_WALLBOXES, user_input, self._selected_id)
            except ValueError as err:
                errors = {"base": str(err)}
        return self.async_show_form(
            step_id="wallbox_details", data_schema=_wallbox_form(current),
            errors=errors,
        )

    async def async_step_remove_wallbox(self, user_input: dict | None = None):
        if user_input is not None:
            self._selected_id = user_input["item_id"]
            return await self.async_step_confirm_remove_wallbox()
        return self.async_show_form(
            step_id="remove_wallbox",
            data_schema=_choose_item(self._items(CONF_WALLBOXES)),
        )

    async def async_step_confirm_remove_wallbox(self, user_input: dict | None = None):
        if user_input is not None:
            try:
                updated = remove_item(
                    dict(self.config_entry.options), CONF_WALLBOXES,
                    self._selected_id,
                )
            except ValueError:
                return self.async_abort(reason="item_not_found")
            return self._finish(updated)
        return self.async_show_form(
            step_id="confirm_remove_wallbox", data_schema=vol.Schema({})
        )
