"""Local EMS sensor platform."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CATALOG_SENSORS, DOMAIN, SENSOR_DESCRIPTIONS
from .coordinator import LocalEMSCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            *(LocalEMSSensor(coordinator, entry, key, label, unit)
              for key, label, unit in SENSOR_DESCRIPTIONS),
            *(LocalEMSCatalogSensor(coordinator, entry, key, label, unit)
              for key, label, unit in CATALOG_SENSORS),
        ]
    )


class LocalEMSSensor(CoordinatorEntity[LocalEMSCoordinator], SensorEntity):
    """A computed, HA-recorded peak monitor value."""
# SPDX-License-Identifier: GPL-3.0-or-later

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, coordinator: LocalEMSCoordinator, entry: ConfigEntry,
        key: str, label: str, unit: str | None
    ) -> None:
        super().__init__(coordinator)
        self.key = key
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Local EMS",
            manufacturer="Local EMS",
            model="Peak Monitor 0.1",
        )
        if unit:
            self._attr_native_unit_of_measurement = unit
        if key.endswith("_kw"):
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key.endswith("_kwh"):
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key == "minutes_to_limit":
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def available(self) -> bool:
        return self.key == "quality" or bool(self.coordinator.data.get("valid"))

    @property
    def native_value(self):
        return self.coordinator.data.get(self.key)

    @property
    def extra_state_attributes(self):
        return {
            "source_entity": self.coordinator.source,
            "quarter_start": self.coordinator.data.get("quarter_start"),
        }


class LocalEMSCatalogSensor(CoordinatorEntity[LocalEMSCoordinator], SensorEntity):
    """Current HA-managed device registry overview; no duplicate consumption log."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, coordinator: LocalEMSCoordinator, entry: ConfigEntry,
        key: str, label: str, unit: str | None
    ) -> None:
        super().__init__(coordinator)
        self.key = key
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Local EMS",
            manufacturer="Local EMS",
            model="Modular EMS",
        )
        if unit:
            self._attr_native_unit_of_measurement = unit
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get(self.key, 0)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if self.key == "consumers_count":
            return {"consumers": data.get("catalog_consumers", []),
                    "control_mode": "monitor_only"}
        if self.key == "wallboxes_count":
            return {"wallboxes": data.get("catalog_wallboxes", []),
                    "control_mode": "monitor_only"}
        if self.key == "consumer_power_kw_estimated":
            return {"calculation": "measured when available, otherwise rated power",
                    "control_mode": "monitor_only"}
        return {}
