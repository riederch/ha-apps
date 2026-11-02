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

from .const import (
    BATTERY_POWER_INVERT,
    CATALOG_SENSORS,
    CONF_ENERGY_SOURCES,
    CONF_GRID_SAFETY,
    CONF_LIMIT_KW,
    CONF_WARNING_KW,
    DEFAULT_LIMIT_KW,
    DEFAULT_WARNING_KW,
    DOMAIN,
    ENERGY_SOURCE_KEYS,
    GRID_CONTACT_ENTITY,
    GRID_CONTACT_ON_IS_PRESENT,
    GRID_POWER_INVERT,
    GRID_STATE_ENTITY,
    SENSOR_DESCRIPTIONS,
)
from .coordinator import LocalEMSCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            LocalEMSEnergyFlowSource(coordinator, entry),
            *(LocalEMSGridSafetySensor(coordinator, entry, key, name, unit)
              for key, name, unit in (
                  ("grid_state", "Grid safety state", None),
                  ("safety_reason", "Grid safety reason", None),
                  ("recovery_remaining_seconds", "Grid recovery remaining", "s"),
                  ("meter_age_seconds", "Grid meter heartbeat age", "s"),
              )),
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
        data = self.coordinator.data
        attributes = {
            "source_entity": self.coordinator.source,
            "quarter_start": data.get("quarter_start"),
        }
        if self.key == "quality":
            # Stable, always-available card discovery source. The UI reads
            # these existing coordinator values and does not poll HA history
            # or invent a second measurement interval.
            options = self.coordinator.entry.options
            attributes["ems_peak_gauge_version"] = 1
            attributes["ems_peak_summary"] = {
                "valid": bool(data.get("valid", False)),
                "quality": data.get("quality", "starting"),
                "quarter_average_kw": data.get("quarter_average_kw"),
                "forecast_kw": data.get("forecast_kw"),
                "committed_kw": data.get("committed_kw"),
                "energy_kwh": data.get("energy_kwh"),
                "warning_kw": data.get(
                    "warning_kw", float(options.get(CONF_WARNING_KW, DEFAULT_WARNING_KW))
                ),
                "limit_kw": data.get(
                    "limit_kw", float(options.get(CONF_LIMIT_KW, DEFAULT_LIMIT_KW))
                ),
                "quarter_start": data.get("quarter_start"),
                "quarter_end": data.get("quarter_end"),
                "quarter_remaining_seconds": data.get("quarter_remaining_seconds"),
            }
        return attributes


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


class LocalEMSGridSafetySensor(CoordinatorEntity[LocalEMSCoordinator], SensorEntity):
    """Vendor-neutral electrical grid and EMS interlock status."""

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
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def available(self) -> bool:
        return self.key not in ("meter_age_seconds",) or (
            self.coordinator.data.get(self.key) is not None
        )

    @property
    def native_value(self):
        return self.coordinator.data.get(self.key)

    @property
    def extra_state_attributes(self):
        options = self.coordinator.entry.options.get("grid_safety", {})
        return {
            "safety_policy": "fail_closed",
            "actuator_mode": "monitor_only",
            "grid_state_source": options.get("grid_state_entity"),
            "grid_contact_source": options.get("grid_contact_entity"),
            "heartbeat_source": options.get("meter_heartbeat_entity"),
            "operating_mode_source": options.get("operating_mode_entity"),
        }


class LocalEMSEnergyFlowSource(CoordinatorEntity[LocalEMSCoordinator], SensorEntity):
    """One metadata-only source for Local EMS frontend cards.

    No power readings are copied into the recorder. The bundled JS card reads
    live source entities from hass.states and uses this sensor for mapping,
    polarity and the safety state. Existing Home Assistant integrations remain
    the authoritative source of all energy/consumption history.
    """

    _attr_has_entity_name = True
    _attr_name = "Energy flow"
    _attr_should_poll = False

    def __init__(self, coordinator: LocalEMSCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_energy_flow"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Local EMS",
            manufacturer="Local EMS",
            model="Modular EMS",
        )

    @property
    def native_value(self) -> str:
        sources = self.coordinator.entry.options.get(CONF_ENERGY_SOURCES, {})
        return "configured" if any(sources.get(k) for k in ENERGY_SOURCE_KEYS) \
            else "not_configured"

    @property
    def extra_state_attributes(self) -> dict:
        sources = self.coordinator.entry.options.get(CONF_ENERGY_SOURCES, {})
        safety = self.coordinator.entry.options.get(CONF_GRID_SAFETY, {})
        return {
            "ems_flow_version": 1,
            "source_entities": {
                "grid": sources.get("grid_power_sensor"),
                "solar": sources.get("pv_power_sensor"),
                "home": sources.get("house_power_sensor"),
                "battery": sources.get("battery_power_sensor"),
                "battery_soc": sources.get("battery_soc_sensor"),
                "grid_frequency": sources.get("grid_frequency_sensor"),
                "grid_contact": safety.get(GRID_CONTACT_ENTITY),
                "inverter_state": safety.get(GRID_STATE_ENTITY),
            },
            "invert_grid_power": bool(sources.get(GRID_POWER_INVERT, False)),
            "invert_battery_power": bool(sources.get(BATTERY_POWER_INVERT, False)),
            "grid_contact_on_is_present": bool(
                safety.get(GRID_CONTACT_ON_IS_PRESENT, True)
            ),
            "grid_state": self.coordinator.data.get("grid_state", "unconfigured"),
            "grid_safety_reason": self.coordinator.data.get("safety_reason"),
            "control_allowed": bool(
                self.coordinator.data.get("control_allowed", False)
            ),
            "read_only": True,
        }
