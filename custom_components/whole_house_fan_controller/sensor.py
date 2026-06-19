"""Sensor platform for QuietCool Shelly House Fan Controller."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import WholeHouseFanController
from .const import DOMAIN
from .entity import WholeHouseFanBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    controller: WholeHouseFanController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            WholeHouseFanTimerRemainingSensor(controller, entry),
            WholeHouseFanTimerFinishesAtSensor(controller, entry),
        ]
    )


class WholeHouseFanTimerRemainingSensor(WholeHouseFanBaseEntity, SensorEntity):
    """Timer remaining sensor."""

    _attr_translation_key = "timer_remaining"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-sand"

    def __init__(self, controller: WholeHouseFanController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_timer_remaining"

    @property
    def native_value(self) -> int | None:
        """Return remaining minutes."""
        return self.controller.remaining_minutes


class WholeHouseFanTimerFinishesAtSensor(WholeHouseFanBaseEntity, SensorEntity):
    """Timer finish time sensor."""

    _attr_translation_key = "timer_finishes_at"
    _attr_icon = "mdi:timer-check-outline"

    def __init__(self, controller: WholeHouseFanController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_timer_finishes_at"

    @property
    def native_value(self) -> str | None:
        """Return timer finish time as a local clock time."""
        finish_time = self.controller.finish_time
        if finish_time is None:
            return None

        return _format_time(dt_util.as_local(finish_time))


def _format_time(value: datetime) -> str:
    """Format a time without a leading zero."""
    formatted = value.strftime("%I:%M %p")
    return formatted.removeprefix("0")
