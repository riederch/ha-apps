"""Pure, testable quarter-hour demand calculations for Local EMS.

No Home Assistant state history is stored here. Samples come from HA Recorder
at startup and from HA state events during operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

QUARTER = timedelta(minutes=15)
MAX_BOUNDARY_GAP = timedelta(minutes=3)
MIN_TREND_SPAN = timedelta(seconds=15)


@dataclass(frozen=True)
class Sample:
    timestamp: datetime
    energy_kwh: float


@dataclass(frozen=True)
class PeakReading:
    valid: bool
    quality: str
    energy_kwh: float | None = None
    committed_kw: float | None = None
    forecast_kw: float | None = None
    remaining_budget_kwh: float | None = None
    allowed_remaining_kw: float | None = None
    minutes_to_limit: float | None = None
    trend_kw: float | None = None


def quarter_start_utc(now: datetime, timezone_name: str) -> datetime:
    """Use local clock quarters, including both occurrences of a DST hour."""
    local = now.astimezone(ZoneInfo(timezone_name))
    start = local.replace(minute=(local.minute // 15) * 15, second=0, microsecond=0)
    return start.astimezone(UTC)


def _invalid(reason: str) -> PeakReading:
    return PeakReading(valid=False, quality=reason)


def _baseline(samples: list[Sample], start: datetime) -> tuple[float | None, str]:
    before = next((s for s in reversed(samples) if s.timestamp <= start), None)
    after = next((s for s in samples if s.timestamp >= start), None)
    if before is None or after is None:
        return None, "missing_boundary"
    if before.timestamp == start:
        return before.energy_kwh, "exact"
    if after.timestamp == start:
        return after.energy_kwh, "exact"
    gap = after.timestamp - before.timestamp
    if gap <= timedelta(0) or gap > MAX_BOUNDARY_GAP:
        return None, "boundary_gap"
    fraction = (start - before.timestamp).total_seconds() / gap.total_seconds()
    return before.energy_kwh + (after.energy_kwh - before.energy_kwh) * fraction, "estimated_boundary"


def calculate_peak(
    samples: list[Sample],
    now: datetime,
    quarter_start: datetime,
    warning_kw: float,
    limit_kw: float,
    stale_after: timedelta,
) -> PeakReading:
    """Calculate quarter demand and projection from an import-only energy counter.

    A forecast may use extrapolation, but committed_kw never includes projected
    energy. Never silently assume a missing quarter baseline is zero.
    """
    if limit_kw <= 0 or not 0 < warning_kw < limit_kw:
        return _invalid("invalid_configuration")
    if not samples:
        return _invalid("missing_source")
    readings = sorted((s for s in samples if s.timestamp <= now), key=lambda s: s.timestamp)
    if not readings:
        return _invalid("missing_source")

    newest = readings[-1]
    if newest.timestamp < quarter_start:
        return _invalid("waiting_for_sample")
    if now - newest.timestamp > stale_after:
        return _invalid("stale")

    baseline, boundary_quality = _baseline(readings, quarter_start)
    if baseline is None:
        return _invalid(boundary_quality)

    previous_value = None
    for sample in readings:
        if previous_value is not None and sample.energy_kwh < previous_value - 1e-6:
            return _invalid("counter_reset")
        previous_value = sample.energy_kwh

    energy = newest.energy_kwh - baseline
    if energy < -1e-6:
        return _invalid("counter_reset")
    energy = max(0.0, energy)

    elapsed_hours = (newest.timestamp - quarter_start).total_seconds() / 3600.0
    in_quarter = [s for s in readings if quarter_start <= s.timestamp <= newest.timestamp]
    target = newest.timestamp - timedelta(seconds=60)
    candidate = next((s for s in reversed(in_quarter) if s.timestamp <= target), None)
    if candidate is None and in_quarter:
        candidate = in_quarter[0]

    if candidate is not None and newest.timestamp - candidate.timestamp >= MIN_TREND_SPAN:
        hours = (newest.timestamp - candidate.timestamp).total_seconds() / 3600.0
        trend_kw = max(0.0, (newest.energy_kwh - candidate.energy_kwh) / hours)
    elif elapsed_hours >= MIN_TREND_SPAN.total_seconds() / 3600:
        trend_kw = energy / elapsed_hours
    else:
        trend_kw = 0.0

    end = quarter_start + QUARTER
    remaining_hours_since_reading = max(0.0, (end - newest.timestamp).total_seconds() / 3600)
    remaining_hours_since_now = max(0.0, (end - now).total_seconds() / 3600)
    budget_kwh = limit_kw * 0.25
    committed_kw = energy * 4.0
    forecast_kw = max(committed_kw, 4.0 * (energy + trend_kw * remaining_hours_since_reading))
    left_kwh = max(0.0, budget_kwh - energy)
    allowed_kw = left_kwh / remaining_hours_since_now if remaining_hours_since_now > 0 else 0.0
    minutes_to_limit = None
    if energy >= budget_kwh:
        minutes_to_limit = 0.0
    elif trend_kw > 0:
        candidate_minutes = (budget_kwh - energy) / trend_kw * 60.0
        candidate_minutes -= (now - newest.timestamp).total_seconds() / 60.0
        if 0 <= candidate_minutes <= remaining_hours_since_now * 60:
            minutes_to_limit = candidate_minutes

    return PeakReading(
        valid=True,
        quality=boundary_quality if boundary_quality != "exact" else "ok",
        energy_kwh=round(energy, 5),
        committed_kw=round(committed_kw, 4),
        forecast_kw=round(forecast_kw, 4),
        remaining_budget_kwh=round(left_kwh, 5),
        allowed_remaining_kw=round(allowed_kw, 4),
        minutes_to_limit=round(minutes_to_limit, 2) if minutes_to_limit is not None else None,
        trend_kw=round(trend_kw, 4),
    )
