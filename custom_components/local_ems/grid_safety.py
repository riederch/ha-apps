# SPDX-License-Identifier: GPL-3.0-or-later
"""Vendor-agnostic grid safety interlock for the Local EMS.

This module only classifies inputs and recommends safety actions. It must not
execute any service call, switch a relay, or control a charger.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .const import (
    CONF_EMS_ENABLED,
    CONF_GRID_SAFETY,
    DEFAULT_GRID_RECOVERY_SECONDS,
    DEFAULT_METER_TIMEOUT_SECONDS,
    GRID_CONTACT_ENTITY,
    GRID_CONTACT_ON_IS_PRESENT,
    GRID_EPS_VALUES,
    GRID_ON_VALUES,
    GRID_RECOVERY_SECONDS,
    GRID_STATE_ENTITY,
    METER_HEARTBEAT_ENTITY,
    METER_TIMEOUT_SECONDS,
    MODE_ALLOWED_VALUES,
    MODE_ENTITY,
)

UNKNOWN_VALUES = frozenset({"", "unknown", "unavailable", "none"})


@dataclass(frozen=True)
class GridSafetyResult:
    """An auditable, read-only result for the central EMS gate."""

    grid_state: str
    safety_reason: str
    grid_confirmed: bool
    eps_detected: bool | None
    meter_heartbeat_ok: bool | None
    meter_age_seconds: float | None
    mode_allowed: bool | None
    control_allowed: bool
    load_shed_requested: bool
    recovery_remaining_seconds: int
    enabled: bool


def parse_values(raw: str | list[str] | tuple[str, ...] | None) -> set[str]:
    """Normalize exact HA states. Never use substring matching."""
    if raw is None:
        return set()
    if isinstance(raw, (list, tuple)):
        parts = [piece for value in raw for piece in str(value).split(",")]
    else:
        parts = str(raw).replace("\n", ",").split(",")
    return {str(part).strip().casefold() for part in parts if str(part).strip()}


def validate_safety_config(config: Mapping[str, Any]) -> dict[str, str]:
    """Check configured state mappings before accepting the UI form."""
    errors: dict[str, str] = {}
    inverter = str(config.get(GRID_STATE_ENTITY) or "")
    contact = str(config.get(GRID_CONTACT_ENTITY) or "")
    if not inverter and not contact:
        # Partial configuration is okay, but the core will stay fail-closed.
        return errors
    grid_values = parse_values(config.get(GRID_ON_VALUES))
    eps_values = parse_values(config.get(GRID_EPS_VALUES))
    if inverter and not grid_values:
        errors[GRID_ON_VALUES] = "grid_values_required"
    if inverter and grid_values & eps_values:
        errors[GRID_EPS_VALUES] = "overlapping_grid_values"
    if config.get(MODE_ENTITY) and not parse_values(config.get(MODE_ALLOWED_VALUES)):
        errors[MODE_ALLOWED_VALUES] = "mode_values_required"
    return errors


def _read_state(resolve: Callable[[str], Any], entity: str | None) -> str | None:
    if not entity:
        return None
    state = resolve(entity)
    if state is None:
        return None
    value = str(state.state).strip().casefold()
    return value if value not in UNKNOWN_VALUES else None


def _meter_health(
    config: Mapping[str, Any], resolve: Callable[[str], Any], now: datetime
) -> tuple[bool | None, float | None]:
    entity = config.get(METER_HEARTBEAT_ENTITY)
    if not entity:
        return None, None
    state = resolve(str(entity))
    if state is None or str(state.state).strip().casefold() in UNKNOWN_VALUES:
        return False, None
    # last_updated can remain unchanged for hours with 0 W import, while
    # last_reported advances for repeated HA state reports.
    last_reported = getattr(state, "last_reported", None)
    if last_reported is None:
        return False, None
    try:
        age = (now.astimezone(UTC) - last_reported.astimezone(UTC)).total_seconds()
    except (TypeError, ValueError, AttributeError):
        return False, None
    if age < -2:
        return False, None
    age = max(0.0, age)
    timeout = int(config.get(METER_TIMEOUT_SECONDS, DEFAULT_METER_TIMEOUT_SECONDS))
    return age <= timeout, round(age, 2)


def evaluate_grid_safety(
    options: Mapping[str, Any],
    resolve: Callable[[str], Any],
    now: datetime,
    safe_since: datetime | None = None,
) -> tuple[GridSafetyResult, datetime | None]:
    """Classify signals and apply a stable-on-grid recovery delay.

    A meter heartbeat alone cannot prove that the public grid is present.
    A configured inverter mode is a permission gate, never a grid sensor.
    An unconfigured or ambiguous grid never grants control permission.
    """
    config = options.get(CONF_GRID_SAFETY) or {}
    enabled = bool(options.get(CONF_EMS_ENABLED, False))
    inverter_entity = config.get(GRID_STATE_ENTITY)
    contact_entity = config.get(GRID_CONTACT_ENTITY)
    mode_entity = config.get(MODE_ENTITY)

    inverter_state = _read_state(resolve, inverter_entity)
    contact_state = _read_state(resolve, contact_entity)
    mode_state = _read_state(resolve, mode_entity)

    on_values = parse_values(config.get(GRID_ON_VALUES))
    eps_values = parse_values(config.get(GRID_EPS_VALUES))
    allowed_modes = parse_values(config.get(MODE_ALLOWED_VALUES))

    recognized_eps = bool(inverter_state and inverter_state in eps_values)
    recognized_grid = bool(inverter_state and inverter_state in on_values)
    recognized_contact = None
    if contact_entity:
        on_means_present = bool(config.get(GRID_CONTACT_ON_IS_PRESENT, True))
        if contact_state in {"on", "off"}:
            recognized_contact = (
                (contact_state == "on") == on_means_present
            )

    meter_ok, meter_age = _meter_health(config, resolve, now)

    if not inverter_entity and not contact_entity:
        state, reason = "unconfigured", "no_grid_source"
    elif recognized_eps:
        state, reason = "eps", "inverter_eps"
    elif recognized_contact is False:
        state, reason = "grid_lost", "grid_contact_lost"
    elif inverter_entity and not recognized_grid:
        state, reason = "unknown", (
            "inverter_state_unavailable"
            if inverter_state is None else "inverter_state_unrecognized"
        )
    elif contact_entity and recognized_contact is None:
        state, reason = "unknown", "grid_contact_unavailable"
    elif recognized_grid or recognized_contact is True:
        state, reason = "on_grid", "grid_confirmed"
    else:
        state, reason = "unknown", "no_confirmed_grid"

    if state == "on_grid" and meter_ok is False:
        state, reason = "suspect", (
            "meter_heartbeat_stale" if meter_age is not None
            else "meter_heartbeat_unavailable"
        )

    if not mode_entity:
        mode_allowed: bool | None = None
        mode_ok = True
    else:
        mode_allowed = bool(mode_state and mode_state in allowed_modes)
        mode_ok = mode_allowed

    raw_grid_confirmed = state == "on_grid"
    qualifies = raw_grid_confirmed and mode_ok and enabled
    remaining = 0

    if qualifies:
        since = safe_since if safe_since and safe_since <= now else now
        recovery = int(config.get(GRID_RECOVERY_SECONDS, DEFAULT_GRID_RECOVERY_SECONDS))
        remaining = max(0, recovery - int((now - since).total_seconds()))
        if remaining > 0:
            state, reason = "recovering", "recovery_wait"
        control_allowed = remaining == 0
        safe_since = since
    else:
        safe_since = None
        control_allowed = False
        if raw_grid_confirmed and not mode_ok:
            reason = "operating_mode_blocked"
        elif raw_grid_confirmed and not enabled:
            reason = "ems_disabled"

    # This is a diagnostic *request*, not a switched load. Only a later,
    # separately tested actuator module may dispatch actual off commands.
    load_shed_requested = enabled and not control_allowed
    return (
        GridSafetyResult(
            grid_state=state,
            safety_reason=reason,
            grid_confirmed=raw_grid_confirmed,
            eps_detected=recognized_eps if inverter_entity else None,
            meter_heartbeat_ok=meter_ok,
            meter_age_seconds=meter_age,
            mode_allowed=mode_allowed,
            control_allowed=control_allowed,
            load_shed_requested=load_shed_requested,
            recovery_remaining_seconds=remaining,
            enabled=enabled,
        ),
        safe_since,
    )
