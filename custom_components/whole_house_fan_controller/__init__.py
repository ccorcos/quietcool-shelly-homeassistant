"""QuietCool Shelly House Fan Controller integration."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_ON, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEFAULT_RUN_HOURS,
    CONF_MAX_RUN_HOURS,
    CONF_MIN_RUN_HOURS,
    CONF_POWER_SWITCH,
    CONF_RUN_HOURS_STEP,
    CONF_SPEED_MAP,
    CONF_SPEED_RELAY_A,
    CONF_SPEED_RELAY_B,
    DEFAULT_MAX_RUN_HOURS,
    DEFAULT_MIN_RUN_HOURS,
    DEFAULT_RUN_HOURS,
    DEFAULT_RUN_HOURS_STEP,
    DEFAULT_SPEED_MAP,
    DOMAIN,
    PRESET_LOW,
    PRESET_MODES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.FAN,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
]


UpdateCallback = Callable[[], None]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration domain."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_lovelace_card(hass)
    return True


async def _async_register_lovelace_card(hass: HomeAssistant) -> None:
    """Register the bundled Lovelace card as a static file."""
    from homeassistant.components.http import StaticPathConfig

    card_path = Path(__file__).parent / "www" / "quietcool-house-fan-card.js"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                f"/{DOMAIN}/quietcool-house-fan-card.js",
                str(card_path),
                False,
            )
        ]
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a QuietCool Shelly House Fan Controller config entry."""
    controller = WholeHouseFanController(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller

    remove_state_listener = async_track_state_change_event(
        hass,
        [controller.power_switch_entity, controller.relay_a_entity, controller.relay_b_entity],
        controller.async_entity_state_changed,
    )
    entry.async_on_unload(remove_state_listener)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        controller: WholeHouseFanController | None = hass.data[DOMAIN].pop(entry.entry_id, None)
        if controller is not None:
            controller.cancel_timer(turn_off=False)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry after options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class WholeHouseFanController:
    """Runtime controller shared by the fan, number, button, and sensor entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._lock = asyncio.Lock()
        self._listeners: list[UpdateCallback] = []
        self._cancel_timer_callback: Callable[[], None] | None = None
        self.finish_time: datetime | None = None
        self.current_preset = self.options.get("current_preset", PRESET_LOW)
        if self.current_preset not in PRESET_MODES:
            self.current_preset = PRESET_LOW
        self.run_hours = float(self.options.get(CONF_DEFAULT_RUN_HOURS, DEFAULT_RUN_HOURS))

    @property
    def options(self) -> dict[str, Any]:
        """Return merged entry data and options."""
        return {**self.entry.data, **self.entry.options}

    @property
    def name(self) -> str:
        """Return configured name."""
        return self.options[CONF_NAME]

    @property
    def power_switch_entity(self) -> str:
        """Return master power switch entity ID."""
        return self.options[CONF_POWER_SWITCH]

    @property
    def relay_a_entity(self) -> str:
        """Return speed relay A switch entity ID."""
        return self.options[CONF_SPEED_RELAY_A]

    @property
    def relay_b_entity(self) -> str:
        """Return speed relay B switch entity ID."""
        return self.options[CONF_SPEED_RELAY_B]

    @property
    def speed_map(self) -> dict[str, dict[str, bool]]:
        """Return speed relay truth table."""
        return self.options.get(CONF_SPEED_MAP, DEFAULT_SPEED_MAP)

    @property
    def min_run_hours(self) -> float:
        """Return minimum timer hours."""
        return float(self.options.get(CONF_MIN_RUN_HOURS, DEFAULT_MIN_RUN_HOURS))

    @property
    def max_run_hours(self) -> float:
        """Return maximum timer hours."""
        return float(self.options.get(CONF_MAX_RUN_HOURS, DEFAULT_MAX_RUN_HOURS))

    @property
    def run_hours_step(self) -> float:
        """Return timer number step."""
        return float(self.options.get(CONF_RUN_HOURS_STEP, DEFAULT_RUN_HOURS_STEP))

    @property
    def is_on(self) -> bool:
        """Return whether the master power switch is currently on."""
        state = self.hass.states.get(self.power_switch_entity)
        return state is not None and state.state == STATE_ON

    @property
    def timer_active(self) -> bool:
        """Return whether a run timer is active."""
        return self.finish_time is not None and self.finish_time > dt_util.utcnow()

    @property
    def remaining_minutes(self) -> int | None:
        """Return remaining timer minutes, rounded up."""
        if not self.timer_active or self.finish_time is None:
            return None
        remaining = self.finish_time - dt_util.utcnow()
        return max(0, int((remaining.total_seconds() + 59) // 60))

    @callback
    def async_add_listener(self, listener: UpdateCallback) -> Callable[[], None]:
        """Register an entity update listener."""
        self._listeners.append(listener)

        @callback
        def remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove_listener

    @callback
    def async_update_listeners(self) -> None:
        """Notify entities to write their state."""
        for listener in list(self._listeners):
            listener()

    @callback
    def async_entity_state_changed(self, event) -> None:
        """Handle source switch state changes."""
        self.async_update_listeners()

    async def async_turn_on(self, preset_mode: str | None = None) -> None:
        """Apply speed selection and turn master power on."""
        async with self._lock:
            if preset_mode is not None:
                self._validate_preset(preset_mode)
                self.current_preset = preset_mode
            await self._apply_speed_relays(self.current_preset)
            await self._set_switch(self.power_switch_entity, True)
            self.async_update_listeners()

    async def async_turn_off(self, *, cancel_timer: bool = True) -> None:
        """Turn master power off and optionally cancel the timer."""
        async with self._lock:
            if cancel_timer:
                self.cancel_timer(turn_off=False)
            await self._set_switch(self.power_switch_entity, False)
            self.async_update_listeners()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set selected speed."""
        self._validate_preset(preset_mode)
        async with self._lock:
            self.current_preset = preset_mode
            await self._apply_speed_relays(preset_mode)
            self.async_update_listeners()

    async def async_set_run_hours(self, value: float) -> None:
        """Set timer run hours."""
        value = min(max(float(value), self.min_run_hours), self.max_run_hours)
        self.run_hours = value
        self.async_update_listeners()

    async def async_start_timer(self, hours: float | None = None) -> None:
        """Turn on the fan and start/restart the run timer."""
        hours = self.run_hours if hours is None else float(hours)
        hours = min(max(hours, self.min_run_hours), self.max_run_hours)
        await self.async_turn_on()
        self.cancel_timer(turn_off=False)
        self.finish_time = dt_util.utcnow() + timedelta(hours=hours)
        self._cancel_timer_callback = async_call_later(
            self.hass,
            hours * 3600,
            self._async_timer_finished,
        )
        self.async_update_listeners()

    async def async_stop_timer(self) -> None:
        """Cancel the run timer and turn the fan off."""
        self.cancel_timer(turn_off=False)
        await self.async_turn_off(cancel_timer=False)

    @callback
    def cancel_timer(self, *, turn_off: bool) -> None:
        """Cancel any active timer."""
        if self._cancel_timer_callback is not None:
            self._cancel_timer_callback()
            self._cancel_timer_callback = None
        self.finish_time = None
        self.async_update_listeners()
        if turn_off:
            self.hass.async_create_task(self.async_turn_off(cancel_timer=False))

    @callback
    def _async_timer_finished(self, _now) -> None:
        """Handle timer expiration."""
        self._cancel_timer_callback = None
        self.finish_time = None
        self.hass.async_create_task(self.async_turn_off(cancel_timer=False))
        self.async_update_listeners()

    async def _apply_speed_relays(self, preset_mode: str) -> None:
        """Apply speed relay state."""
        relay_state = self.speed_map[preset_mode]
        await self._set_switch(self.relay_a_entity, bool(relay_state["relay_a"]))
        await self._set_switch(self.relay_b_entity, bool(relay_state["relay_b"]))

    async def _set_switch(self, entity_id: str, turn_on: bool) -> None:
        """Call switch turn_on/turn_off and fail loudly on service errors."""
        service = "turn_on" if turn_on else "turn_off"
        state = self.hass.states.get(entity_id)
        if state is None:
            raise HomeAssistantError(f"Switch entity {entity_id} does not exist")
        await self.hass.services.async_call(
            "switch",
            service,
            {"entity_id": entity_id},
            blocking=True,
        )

    def _validate_preset(self, preset_mode: str) -> None:
        """Validate speed preset."""
        if preset_mode not in PRESET_MODES:
            raise HomeAssistantError(f"Invalid fan preset mode: {preset_mode}")
