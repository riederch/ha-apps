# SPDX-License-Identifier: GPL-3.0-or-later
"""Local EMS: read-only demand monitoring and future energy modules."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import LocalEMSCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = LocalEMSCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    success = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if success:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return success
