"""Editable peak limits, stored as Home Assistant config-entry options."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_LIMIT_KW,
    CONF_WARNING_KW,
    DEFAULT_LIMIT_KW,
    DEFAULT_WARNING_KW,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            LocalEMSNumber(hass, entry, CONF_LIMIT_KW, "Demand limit"),
            LocalEMSNumber(hass, entry, CONF_WARNING_KW, "Warning threshold"),
        ]
    )


class LocalEMSNumber(NumberEntity):
    """A configured limit; not a command to control electrical equipment."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_native_min_value = 0.1
    _attr_native_max_value = 100.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "kW"
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, key: str, label: str):
        self.hass = hass
        self.entry = entry
        self.key = key
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Local EMS",
            manufacturer="Local EMS",
            model="Peak Monitor 0.1",
        )

    @property
    def native_value(self) -> float:
        default = DEFAULT_LIMIT_KW if self.key == CONF_LIMIT_KW else DEFAULT_WARNING_KW
        return float(self.entry.options.get(self.key, default))

    async def async_set_native_value(self, value: float) -> None:
        options = dict(self.entry.options)
        options[self.key] = float(value)
        current_limit = float(options.get(CONF_LIMIT_KW, DEFAULT_LIMIT_KW))
        current_warning = float(options.get(CONF_WARNING_KW, DEFAULT_WARNING_KW))
        if self.key == CONF_LIMIT_KW and current_warning >= current_limit:
            options[CONF_WARNING_KW] = round(current_limit * 0.9, 2)
        elif self.key == CONF_WARNING_KW and current_warning >= current_limit:
            raise ValueError("The warning threshold must be below the demand limit")
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self.hass.data[DOMAIN][self.entry.entry_id].refresh_configuration()
        self.async_write_ha_state()
