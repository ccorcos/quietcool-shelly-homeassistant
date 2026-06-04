"""Number platform for Whole House Fan Controller."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up number entity."""
    controller: WholeHouseFanController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WholeHouseFanRunHoursNumber(controller, entry)])


class WholeHouseFanRunHoursNumber(WholeHouseFanBaseEntity, NumberEntity):
    """Timer run-hours number entity."""

    _attr_translation_key = "run_hours"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_mode = NumberMode.BOX

    def __init__(self, controller: WholeHouseFanController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_run_hours"

    @property
    def native_value(self) -> float:
        """Return selected run hours."""
        return self.controller.run_hours

    @property
    def native_min_value(self) -> float:
        """Return minimum run hours."""
        return self.controller.min_run_hours

    @property
    def native_max_value(self) -> float:
        """Return maximum run hours."""
        return self.controller.max_run_hours

    @property
    def native_step(self) -> float:
        """Return run hours step."""
        return self.controller.run_hours_step

    async def async_set_native_value(self, value: float) -> None:
        """Set selected run hours."""
        await self.controller.async_set_run_hours(value)
