# SPDX-License-Identifier: GPL-3.0-or-later
"""Constants for Local EMS."""
DOMAIN = "local_ems"

CONF_SOURCE = "source"
CONF_LIMIT_KW = "limit_kw"
CONF_WARNING_KW = "warning_kw"
CONF_STALE_SECONDS = "stale_seconds"

DEFAULT_SOURCE = "sensor.kng_p_in"
DEFAULT_LIMIT_KW = 10.0
DEFAULT_WARNING_KW = 9.0
DEFAULT_STALE_SECONDS = 180

SENSOR_DESCRIPTIONS = (
    ("energy_kwh", "Current quarter imported energy", "kWh"),
    ("quarter_average_kw", "Quarter actual average demand", "kW"),
    ("committed_kw", "Quarter committed demand", "kW"),
    ("forecast_kw", "Quarter demand forecast", "kW"),
    ("remaining_budget_kwh", "Remaining import budget", "kWh"),
    ("allowed_remaining_kw", "Permitted average import until quarter end", "kW"),
    ("minutes_to_limit", "Minutes until limit", "min"),
    ("trend_kw", "Recent import trend", "kW"),
    ("quality", "Measurement quality", None),
)

# Registry: one HA config entry owns the complete EMS device catalogue.
CONF_CONSUMERS = "consumers"
CONF_WALLBOXES = "wallboxes"
CONF_ENERGY_SOURCES = "energy_sources"

CONSUMER_KIND = "consumer_type"
CONSUMER_SWITCH = "switch_entity"
CONSUMER_RATED_POWER = "rated_power_w"
CONSUMER_MEASURED_POWER = "power_sensor"
CONSUMER_PRIORITY = "priority"
CONSUMER_MIN_ON = "min_on_seconds"
CONSUMER_MIN_OFF = "min_off_seconds"
CONSUMER_SURPLUS_MARGIN = "surplus_margin_w"
CONSUMER_ENABLED = "enabled"

WALLBOX_CHARGE_SWITCH = "charge_enable_switch"
WALLBOX_CHARGE_POWER = "charge_power_sensor"
WALLBOX_CURRENT_LIMIT = "current_limit_number"
WALLBOX_CONNECTED = "connected_binary_sensor"
WALLBOX_PHASE_COUNT = "phase_count"
WALLBOX_MAX_CURRENT = "max_current_a"

ENERGY_SOURCE_KEYS = (
    "grid_power_sensor",
    "pv_power_sensor",
    "house_power_sensor",
    "battery_power_sensor",
    "battery_soc_sensor",
    "grid_frequency_sensor",
)

GRID_POWER_INVERT = "grid_power_invert"
BATTERY_POWER_INVERT = "battery_power_invert"

CATALOG_SENSORS = (
    ("consumers_count", "Registered flexible consumers", None),
    ("consumers_on", "Active flexible consumers", None),
    ("consumers_unknown", "Unavailable flexible consumers", None),
    ("consumer_power_kw_estimated", "Estimated flexible consumption", "kW"),
    ("wallboxes_count", "Registered wallboxes", None),
)

# Generic grid/EPS/meter/operating-mode safety. All sources optional until
# configured. There is no manufacturer or inverter register dependency.
CONF_GRID_SAFETY = "grid_safety"
CONF_EMS_ENABLED = "ems_enabled"

GRID_STATE_ENTITY = "grid_state_entity"
GRID_ON_VALUES = "grid_on_values"
GRID_EPS_VALUES = "grid_eps_values"
GRID_CONTACT_ENTITY = "grid_contact_entity"
GRID_CONTACT_ON_IS_PRESENT = "grid_contact_on_is_present"
METER_HEARTBEAT_ENTITY = "meter_heartbeat_entity"
METER_TIMEOUT_SECONDS = "meter_timeout_seconds"
MODE_ENTITY = "operating_mode_entity"
MODE_ALLOWED_VALUES = "mode_allowed_values"
GRID_RECOVERY_SECONDS = "grid_recovery_seconds"

DEFAULT_METER_TIMEOUT_SECONDS = 10
DEFAULT_GRID_RECOVERY_SECONDS = 120
