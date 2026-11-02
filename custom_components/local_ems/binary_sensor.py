"""Warnings and data health for Local EMS."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LocalEMSCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LocalEMSBinarySensor(coordinator, entry, key, label)
        for key, label in (
            ("valid", "Measurement valid"),
            ("warning", "Demand warning"),
            ("limit_reached", "Demand limit reached"),
        )
    )


class LocalEMSBinarySensor(
    CoordinatorEntity[LocalEMSCoordinator], BinarySensorEntity
):
    """Boolean monitor states, with unavailable warnings on invalid data."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, coordinator: LocalEMSCoordinator, entry: ConfigEntry,
        key: str, label: str
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
        if key == "valid":
            self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def available(self) -> bool:
        return self.key == "valid" or bool(self.coordinator.data.get("valid"))

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get(self.key))
