"""Fan platform for QuietCool Shelly Whole House Fan Controller."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WholeHouseFanController
from .const import DOMAIN, PRESET_HIGH, PRESET_LOW, PRESET_MEDIUM, PRESET_MODES
from .entity import WholeHouseFanBaseEntity

PERCENTAGE_TO_PRESET = {
    PRESET_LOW: 33,
    PRESET_MEDIUM: 66,
    PRESET_HIGH: 100,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up fan entity."""
    controller: WholeHouseFanController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WholeHouseFanEntity(controller, entry)])


class WholeHouseFanEntity(WholeHouseFanBaseEntity, FanEntity):
    """Virtual whole house fan entity backed by three switch entities."""

    _attr_supported_features = FanEntityFeature.PRESET_MODE | FanEntityFeature.SET_SPEED
    _attr_preset_modes = PRESET_MODES
    _attr_speed_count = 3

    def __init__(self, controller: WholeHouseFanController, entry: ConfigEntry) -> None:
        super().__init__(controller, entry)
        self._attr_unique_id = f"{entry.entry_id}_fan"
        self._attr_name = None

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on."""
        return self.controller.is_on

    @property
    def preset_mode(self) -> str:
        """Return current preset mode."""
        return self.controller.current_preset

    @property
    def percentage(self) -> int:
        """Return fan speed percentage."""
        if not self.is_on:
            return 0
        return PERCENTAGE_TO_PRESET[self.controller.current_preset]

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn fan on."""
        if preset_mode is None and percentage is not None:
            preset_mode = _percentage_to_preset(percentage)
        await self.controller.async_turn_on(preset_mode=preset_mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn fan off."""
        await self.controller.async_turn_off()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set fan preset mode."""
        await self.controller.async_set_preset_mode(preset_mode)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan percentage."""
        if percentage <= 0:
            await self.controller.async_turn_off()
            return
        await self.controller.async_set_preset_mode(_percentage_to_preset(percentage))
        if not self.controller.is_on:
            await self.controller.async_turn_on()


def _percentage_to_preset(percentage: int) -> str:
    """Map Home Assistant percentage speed to preset."""
    if percentage <= 33:
        return PRESET_LOW
    if percentage <= 66:
        return PRESET_MEDIUM
    return PRESET_HIGH
