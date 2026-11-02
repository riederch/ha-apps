# SPDX-License-Identifier: GPL-3.0-or-later
"""Enable/disable future EMS regulation; no physical loads are operated."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_EMS_ENABLED, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([LocalEMSEnableSwitch(hass, entry)])


class LocalEMSEnableSwitch(SwitchEntity):
    """Only arm the safety decision state. Not an actuator."""

    _attr_has_entity_name = True
    _attr_name = "EMS regulation enabled (monitor only)"
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ems_regulation_enabled"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Local EMS",
            manufacturer="Local EMS",
            model="Modular EMS",
        )

    @property
    def is_on(self) -> bool:
        return bool(self.entry.options.get(CONF_EMS_ENABLED, False))

    async def _set_enabled(self, value: bool) -> None:
        options = dict(self.entry.options)
        options[CONF_EMS_ENABLED] = value
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_enabled(False)

    @property
    def extra_state_attributes(self):
        return {
            "actuator_mode": "monitor_only",
            "note": "Does not switch physical loads in this beta",
        }
