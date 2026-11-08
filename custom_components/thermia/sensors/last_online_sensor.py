"""Thermia Last Online Sensor integration."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from ..const import MDI_CLOUD_CLOCK_OUTLINE_ICON
from ..coordinator import ThermiaDataUpdateCoordinator
from .generic_sensor import ThermiaGenericSensor


class ThermiaLastOnlineSensor(ThermiaGenericSensor):
    """Timestamp of when the heat pump was last seen online by Thermia Online.

    Unlike other sensors, this one stays available while the heat pump is
    reported offline, so it shows when the cloud last heard from it.
    """

    def __init__(self, coordinator: ThermiaDataUpdateCoordinator, idx: int):
        super().__init__(
            coordinator,
            idx,
            "is_online",
            "Last Online",
            MDI_CLOUD_CLOCK_OUTLINE_ICON,
            EntityCategory.DIAGNOSTIC,
            SensorDeviceClass.TIMESTAMP,
            None,
            "last_online",
            None,
        )

    @property
    def available(self):
        """Return True if the last online timestamp is known."""
        return super(ThermiaGenericSensor, self).available and self.native_value is not None

    @property
    def native_value(self) -> datetime | None:
        """Return the last online timestamp.

        The API returns naive ISO strings: `last_online_utc` (from the
        installations list) is UTC, while `last_online` (from the installation
        details) is in the installation's local time zone. Older library
        versions only expose the latter, so fall back to it and assume the
        Home Assistant time zone.
        """
        heat_pump = self.coordinator.data.heat_pumps[self.idx]

        value = getattr(heat_pump, "last_online_utc", None)
        tz = timezone.utc
        if not value:
            value = heat_pump.last_online
            tz = dt_util.DEFAULT_TIME_ZONE
        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)

        return parsed
