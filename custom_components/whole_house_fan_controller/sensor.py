"""Sensor platform for QuietCool Shelly Whole House Fan Controller."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
    """Timer finish timestamp sensor."""

    _attr_translation_key = "timer_finishes_at"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:timer-check-outline"

    def __init__(self, controller: WholeHouseFanController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_timer_finishes_at"

    @property
    def native_value(self) -> datetime | None:
        """Return timer finish timestamp."""
        return self.controller.finish_time
