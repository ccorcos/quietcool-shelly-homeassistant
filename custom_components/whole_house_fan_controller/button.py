"""Button platform for QuietCool Shelly Whole House Fan Controller."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up button entity."""
    controller: WholeHouseFanController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WholeHouseFanStartTimerButton(controller, entry)])


class WholeHouseFanStartTimerButton(WholeHouseFanBaseEntity, ButtonEntity):
    """Start timer button entity."""

    _attr_translation_key = "start_timer"
    _attr_icon = "mdi:timer-play-outline"

    def __init__(self, controller: WholeHouseFanController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_start_timer"

    async def async_press(self) -> None:
        """Start the run timer."""
        await self.controller.async_start_timer()
