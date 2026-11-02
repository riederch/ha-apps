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
    ("committed_kw", "Quarter committed demand", "kW"),
    ("forecast_kw", "Quarter demand forecast", "kW"),
    ("remaining_budget_kwh", "Remaining import budget", "kWh"),
    ("allowed_remaining_kw", "Permitted average import until quarter end", "kW"),
    ("minutes_to_limit", "Minutes until limit", "min"),
    ("trend_kw", "Recent import trend", "kW"),
    ("quality", "Measurement quality", None),
)
