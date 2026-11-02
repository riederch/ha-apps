"""UI setup and options for Local EMS. No configuration.yaml required."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_LIMIT_KW,
    CONF_SOURCE,
    CONF_STALE_SECONDS,
    CONF_WARNING_KW,
    DEFAULT_LIMIT_KW,
    DEFAULT_SOURCE,
    DEFAULT_STALE_SECONDS,
    DEFAULT_WARNING_KW,
    DOMAIN,
)


def _form(source: str, limit: float, warning: float, stale: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SOURCE, default=source): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
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


def _validate(hass, user_input: dict) -> dict[str, str]:
    source = user_input[CONF_SOURCE]
    state = hass.states.get(source)
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


class LocalEMSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up a single or multiple monitoring installations."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            errors = _validate(self.hass, user_input)
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
                    },
                )
        return self.async_show_form(
            step_id="user",
            data_schema=_form(
                DEFAULT_SOURCE,
                DEFAULT_LIMIT_KW,
                DEFAULT_WARNING_KW,
                DEFAULT_STALE_SECONDS,
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LocalEMSOptionsFlow()


class LocalEMSOptionsFlow(config_entries.OptionsFlow):
    """Configure thresholds and timeout without YAML."""

    async def async_step_init(self, user_input: dict | None = None):
        entry = self.config_entry
        options = entry.options
        source = entry.data[CONF_SOURCE]
        errors = {}
        if user_input is not None:
            user_input[CONF_SOURCE] = source
            errors = _validate(self.hass, user_input)
            if not errors:
                user_input.pop(CONF_SOURCE, None)
                return self.async_create_entry(title="", data=user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LIMIT_KW, default=options.get(CONF_LIMIT_KW, DEFAULT_LIMIT_KW)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100)),
                vol.Required(
                    CONF_WARNING_KW,
                    default=options.get(CONF_WARNING_KW, DEFAULT_WARNING_KW),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100)),
                vol.Required(
                    CONF_STALE_SECONDS,
                    default=options.get(CONF_STALE_SECONDS, DEFAULT_STALE_SECONDS),
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
