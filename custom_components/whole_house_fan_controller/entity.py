"""Shared entity helpers for QuietCool Shelly House Fan Controller."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import WholeHouseFanController
from .const import DOMAIN


class WholeHouseFanBaseEntity(Entity):
    """Base entity for all QuietCool Shelly House Fan Controller entities."""

    _attr_has_entity_name = True

    def __init__(self, controller: WholeHouseFanController, entry: ConfigEntry) -> None:
        self.controller = controller
        self.entry = entry
        self._remove_listener: Callable[[], None] | None = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=controller.name,
            manufacturer="QuietCool Shelly House Fan Controller",
            model="Relay-backed virtual fan",
        )

    async def async_added_to_hass(self) -> None:
        """Register for controller updates."""
        self._remove_listener = self.controller.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister controller updates."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
