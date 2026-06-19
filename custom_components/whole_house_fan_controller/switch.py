"""Switch platform for QuietCool Shelly House Fan Controller."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up switch entity."""
    controller: WholeHouseFanController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WholeHouseFanTimedRunSwitch(controller, entry)])


class WholeHouseFanTimedRunSwitch(WholeHouseFanBaseEntity, SwitchEntity):
    """Timed run switch entity."""

    _attr_translation_key = "timed_run"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, controller: WholeHouseFanController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_timed_run"

    @property
    def is_on(self) -> bool:
        """Return whether the timed run is active."""
        return self.controller.timer_active

    async def async_turn_on(self, **kwargs) -> None:
        """Start the timed run."""
        await self.controller.async_start_timer()

    async def async_turn_off(self, **kwargs) -> None:
        """Stop the timed run and turn the fan off."""
        await self.controller.async_stop_timer()
