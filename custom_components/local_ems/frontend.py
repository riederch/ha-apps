# SPDX-License-Identifier: GPL-3.0-or-later
"""Serve the bundled Lovelace card without depending on a second HACS project."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
STATIC_URL = "/local_ems"
CARD_PATH = "/local_ems/local-ems-flow-card.mjs"
CARD_VERSION = "0.4.0b1"
CARD_RESOURCE_URL = f"{CARD_PATH}?v={CARD_VERSION}"
_REGISTERED_KEY = "_flow_frontend_registered"


async def async_register_flow_card(hass: HomeAssistant) -> None:
    """Serve JS files; register Lovelace module in storage mode if safe.

    We explicitly load the existing resource collection before modifying it.
    Some HA versions lazily load their Lovelace resources, so calling
    async_create_item before async_load would erase existing resources.
    Card registration failure is nonfatal for the core integration.
    """
    data = hass.data.setdefault(DOMAIN, {})
    if data.get(_REGISTERED_KEY):
        return

    frontend_path = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(frontend_path), cache_headers=False)]
        )
    except Exception:
        _LOGGER.exception(
            "Local EMS card could not be served; backend remains usable"
        )
        return
    data[_REGISTERED_KEY] = True

    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        _LOGGER.info(
            "No Lovelace resource store; add %s manually as a module",
            CARD_RESOURCE_URL,
        )
        return

    if getattr(lovelace, "resource_mode", None) != "storage":
        _LOGGER.info(
            "Lovelace resources are managed in YAML; add %s as a module",
            CARD_RESOURCE_URL,
        )
        return

    resources = getattr(lovelace, "resources", None)
    if resources is None:
        return

    try:
        # Guard against HA installations with lazily loaded resource stores.
        if not getattr(resources, "loaded", False):
            await resources.async_load()

        for item in resources.async_items():
            url = item.get("url", "")
            if url.split("?", 1)[0] == CARD_PATH:
                if url != CARD_RESOURCE_URL or item.get("res_type") != "module":
                    await resources.async_update_item(
                        item["id"],
                        {"url": CARD_RESOURCE_URL, "res_type": "module"},
                    )
                return

        await resources.async_create_item(
            {"url": CARD_RESOURCE_URL, "res_type": "module"}
        )
        _LOGGER.info("Local EMS flow card registered as a Lovelace module")
    except Exception:
        _LOGGER.warning(
            "Could not register the Local EMS card automatically. "
            "Add %s in Dashboard resources as a JavaScript module.",
            CARD_RESOURCE_URL,
            exc_info=True,
        )
