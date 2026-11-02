"""Read Home Assistant Recorder and live entity updates, then publish forecasts."""
from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
import logging

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, EventStateReportedData, HomeAssistant, State
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_state_report_event,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LIMIT_KW,
    CONF_SOURCE,
    CONF_STALE_SECONDS,
    CONF_WARNING_KW,
    DEFAULT_LIMIT_KW,
    DEFAULT_STALE_SECONDS,
    DEFAULT_WARNING_KW,
    DOMAIN,
)
from .peak import Sample, calculate_peak, quarter_start_utc
from .grid_safety import evaluate_grid_safety
from .const import (
    CONF_GRID_SAFETY,
    GRID_STATE_ENTITY,
    GRID_CONTACT_ENTITY,
    MODE_ENTITY,
)
from .devices import catalog_snapshot

_LOGGER = logging.getLogger(__name__)


class LocalEMSCoordinator(DataUpdateCoordinator[dict]):
    """One short-lived sample buffer, rehydrated from Recorder each quarter."""
# SPDX-License-Identifier: GPL-3.0-or-later

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name="Local EMS")
        self.entry = entry
        self.source = entry.data[CONF_SOURCE]
        self.samples: list[Sample] = []
        self._quarter: datetime | None = None
        self._source_ok = False
        self._unsubs: list = []
        self.data = {"valid": False, "quality": "starting"}
        self._grid_good_since: datetime | None = None
        self._grid_watch_signature: tuple[str, ...] = ()
        self._grid_watch_unsub = None

    def _to_sample(self, state: State | None, timestamp: datetime | None = None) -> Sample | None:
        if state is None or state.state in ("unknown", "unavailable", ""):
            return None
        source_state = self.hass.states.get(self.source)
        unit = (
            state.attributes.get("unit_of_measurement")
            or (source_state.attributes.get("unit_of_measurement") if source_state else None)
        )
        if unit not in ("Wh", "kWh"):
            return None
        try:
            amount = float(state.state)
        except (TypeError, ValueError):
            return None
        if not (0 <= amount < float("inf")):
            return None
        return Sample(
            timestamp=(timestamp or state.last_updated).astimezone(UTC),
            energy_kwh=amount / 1000 if unit == "Wh" else amount,
        )

    def _append(self, sample: Sample | None) -> None:
        if sample is None:
            return
        if self.samples and sample.timestamp == self.samples[-1].timestamp:
            self.samples[-1] = sample
        else:
            self.samples.append(sample)
            self.samples.sort(key=lambda x: x.timestamp)
        # We only need observations from the quarter and the final one before it.
        if self._quarter is not None:
            old = [s for s in self.samples if s.timestamp < self._quarter]
            keep_before = old[-1:] if old else []
            self.samples = keep_before + [
                s for s in self.samples if s.timestamp >= self._quarter
            ]

    async def _reload_history(self) -> None:
        now = dt_util.utcnow()
        self._quarter = quarter_start_utc(now, self.hass.config.time_zone)
        try:
            recorded = await get_instance(self.hass).async_add_executor_job(
                get_significant_states,
                self.hass,
                self._quarter,
                now,
                [self.source],
                None,
                True,   # include last state before the quarter
                True,   # significant changes only
                False,  # full State objects
                False,  # include attributes for source unit verification
            )
            history = recorded.get(self.source, [])
            self.samples = []
            for state in history:
                self._append(self._to_sample(state))
        except Exception:
            _LOGGER.exception("Cannot recover %s from Home Assistant Recorder", self.source)
            self.samples = []
        # Include the freshest live state, which may not yet have been committed.
        live_state = self.hass.states.get(self.source)
        self._source_ok = self._to_sample(live_state) is not None
        self._append(self._to_sample(live_state, live_state.last_reported if live_state else None))

    def _publish(self) -> None:
        # Safety and registry remain visible even while the peak meter fails.
        catalog = catalog_snapshot(self.entry.options, self.hass.states.get)
        now = dt_util.utcnow()
        safety, self._grid_good_since = evaluate_grid_safety(
            self.entry.options, self.hass.states.get, now,
            self._grid_good_since,
        )
        catalog.update(asdict(safety))
        quarter = quarter_start_utc(now, self.hass.config.time_zone)
        if self._quarter != quarter:
            self.async_set_updated_data({**catalog, "valid": False, "quality": "quarter_rollover"})
            return
        if not self._source_ok:
            self.async_set_updated_data({**catalog, "valid": False, "quality": "source_unavailable"})
            return
        options = self.entry.options
        warning = float(options.get(CONF_WARNING_KW, DEFAULT_WARNING_KW))
        limit = float(options.get(CONF_LIMIT_KW, DEFAULT_LIMIT_KW))
        stale = int(options.get(CONF_STALE_SECONDS, DEFAULT_STALE_SECONDS))
        result = calculate_peak(
            self.samples,
            now,
            quarter,
            warning_kw=warning,
            limit_kw=limit,
            stale_after=timedelta(seconds=stale),
        )
        snapshot = asdict(result)
        snapshot.update(catalog)
        snapshot.update(
            {
                "quarter_start": quarter.isoformat(),
                "quarter_end": (quarter + timedelta(minutes=15)).isoformat(),
                "quarter_remaining_seconds": max(
                    0, int(((quarter + timedelta(minutes=15)) - now).total_seconds())
                ),
                "source": self.source,
                "limit_kw": limit,
                "warning_kw": warning,
                "warning": result.valid
                and result.forecast_kw is not None
                and result.forecast_kw >= warning,
                "limit_reached": result.valid
                and result.committed_kw is not None
                and result.committed_kw >= limit,
            }
        )
        self.async_set_updated_data(snapshot)

    def _update_grid_watch(self) -> None:
        """Follow whichever vendor-neutral sources the user has configured."""
        options = self.entry.options.get(CONF_GRID_SAFETY, {})
        entities = tuple(sorted(set(
            value for key in (
                GRID_STATE_ENTITY, GRID_CONTACT_ENTITY, MODE_ENTITY
            )
            if isinstance((value := options.get(key)), str) and value
        )))
        if entities == self._grid_watch_signature:
            return
        if self._grid_watch_unsub is not None:
            self._grid_watch_unsub()
            self._grid_watch_unsub = None
        self._grid_watch_signature = entities
        self._grid_good_since = None
        if entities:
            self._grid_watch_unsub = async_track_state_change_event(
                self.hass, list(entities), self._on_grid_changed
            )

    async def _on_grid_changed(self, _event: Event[EventStateChangedData]) -> None:
        self._publish()

    async def async_start(self) -> None:
        self._update_grid_watch()
        self._unsubs.append(
            async_track_state_change_event(
                self.hass, [self.source], self._on_source_changed
            )
        )
        self._unsubs.append(
            async_track_state_report_event(
                self.hass, [self.source], self._on_source_reported
            )
        )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._on_timer, timedelta(seconds=2))
        )
        await self._reload_history()
        self._publish()

    async def _on_source_changed(self, event: Event[EventStateChangedData]) -> None:
        new_state = event.data.get("new_state")
        sample = self._to_sample(new_state)
        self._source_ok = sample is not None
        if sample is not None:
            self._append(sample)
        now = dt_util.utcnow()
        if quarter_start_utc(now, self.hass.config.time_zone) != self._quarter:
            await self._reload_history()
        self._publish()

    async def _on_source_reported(self, event: Event[EventStateReportedData]) -> None:
        """A heartbeat with unchanged energy still counts as a fresh observation."""
        sample = self._to_sample(event.data["new_state"], event.data["last_reported"])
        self._source_ok = sample is not None
        if sample is not None:
            self._append(sample)
        if quarter_start_utc(dt_util.utcnow(), self.hass.config.time_zone) != self._quarter:
            await self._reload_history()
        self._publish()

    async def _on_timer(self, _now: datetime) -> None:
        now = dt_util.utcnow()
        if quarter_start_utc(now, self.hass.config.time_zone) != self._quarter:
            await self._reload_history()
        self._publish()

    async def async_shutdown(self) -> None:
        if self._grid_watch_unsub is not None:
            self._grid_watch_unsub()
            self._grid_watch_unsub = None
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    def refresh_configuration(self) -> None:
        """Re-subscribe to changed input entities and recalculate permissions."""
        self._update_grid_watch()
        # Always re-arm a full recovery period after a config edit.
        self._grid_good_since = None
        self._publish()
